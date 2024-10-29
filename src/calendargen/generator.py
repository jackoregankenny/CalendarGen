from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, LETTER, LEGAL
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas
import calendar as cal
import csv
from datetime import datetime, date
from .holidays import get_holidays

# Modern color schemes
COLOR_SCHEMES = {
    'minimal': {
        'header_bg': '#FFFFFF',
        'header_text': '#1A1A1A',
        'grid': '#E5E5E5',
        'weekend_bg': '#F8F8F8',
        'today_bg': '#F5F5F5',
        'holiday_text': '#FF5A5F',
        'event_text': '#4A4A4A',
        'day_number': '#1A1A1A',
    },
    'dark': {
        'header_bg': '#2D2D2D',
        'header_text': '#FFFFFF',
        'grid': '#404040',
        'weekend_bg': '#333333',
        'today_bg': '#383838',
        'holiday_text': '#FF5A5F',
        'event_text': '#E0E0E0',
        'day_number': '#FFFFFF',
    },
    'ocean': {
        'header_bg': '#F8FDFF',
        'header_text': '#2C5282',
        'grid': '#E6F0F5',
        'weekend_bg': '#F0F9FF',
        'today_bg': '#EBF8FF',
        'holiday_text': '#3182CE',
        'event_text': '#4A5568',
        'day_number': '#2D3748',
    }
}

class DynamicCalendarGenerator:
    def __init__(self, styling=None):
        self.styling = styling or {}
        self.recurring_events = {}
        self.specific_events = {}
        
        # Get color scheme
        scheme_name = self.styling.get('color_scheme', 'minimal')
        self.colors = COLOR_SCHEMES[scheme_name]
        
        # Set paper size with margins
        paper_size = self.styling.get('paper_size', 'A4').upper()
        self.page_size = {
            'A4': A4,
            'LETTER': LETTER,
            'LEGAL': LEGAL
        }.get(paper_size, A4)
        
        # Set orientation
        if self.styling.get('orientation', 'P').upper() == 'L':
            self.page_size = self.page_size[1], self.page_size[0]
        
        # Modern styling options
        self.cell_padding = float(self.styling.get('cell_padding', 3)) * mm
        self.grid_width = float(self.styling.get('grid_width', 0.5))  # Thinner lines for modern look
        self.corner_radius = float(self.styling.get('corner_radius', 2))  # Rounded corners (in points)
        self.show_weekends = self.styling.get('show_weekends', True)  # Different styling for weekends
        self.compact_mode = self.styling.get('compact_mode', False)  # More compact layout
        
        # Set week start (0 = Monday, 6 = Sunday)
        week_start = int(self.styling.get('weekstart', 0))
        cal.setfirstweekday(week_start)
        
        self.year = None
        self.holidays = {}
        
        # Initialize styles
        self.setup_styles()

    def setup_styles(self, header_size=24, event_size=10):
        """Setup styles with given font sizes and modern aesthetic"""
        self.styles = getSampleStyleSheet()
        
        # Modern header style
        self.styles.add(ParagraphStyle(
            name='MonthHeader',
            fontSize=header_size,
            alignment=1,
            spaceAfter=15,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor(self.colors['header_text']),
            leading=header_size * 1.2
        ))
        
        # Clean event text style
        self.styles.add(ParagraphStyle(
            name='EventText',
            fontSize=event_size,
            fontName='Helvetica',
            textColor=colors.HexColor(self.colors['event_text']),
            leading=event_size * 1.3,
            spaceBefore=2,
            spaceAfter=2
        ))
        
        # Day number style
        self.styles.add(ParagraphStyle(
            name='DayNumber',
            fontSize=event_size * 1.2,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor(self.colors['day_number']),
            alignment=0  # Left align
        ))

    def _get_weekend_style(self, day_of_week):
        """Get special styling for weekends"""
        if not self.show_weekends:
            return []
            
        is_weekend = day_of_week in [5, 6]  # Saturday or Sunday
        if is_weekend:
            return [
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(self.colors['weekend_bg'])),
            ]
        return []

    def calculate_optimal_sizes(self, year, month, available_height):
        """Calculate optimal font sizes to fit content on one page"""
        # Start with maximum sizes
        max_header = int(self.styling.get('header_size', 24))
        max_event = int(self.styling.get('event_size', 10))
        
        # Get number of weeks in this month
        num_weeks = len(cal.monthcalendar(year, month))
        
        # Calculate maximum events per day for this month
        max_events_per_day = 0
        for day in range(1, 32):
            try:
                current_date = date(year, month, day)
            except ValueError:
                break
                
            events_count = 0
            # Count specific events
            if current_date in self.specific_events:
                events_count += len(self.specific_events[current_date])
            
            # Count recurring events
            if month in self.recurring_events and day in self.recurring_events[month]:
                events_count += len(self.recurring_events[month][day])
            
            # Count holiday
            if current_date in self.holidays:
                events_count += 1
            
            max_events_per_day = max(max_events_per_day, events_count)

        # Calculate cell height available for events
        cell_height = available_height / (num_weeks + 1)  # +1 for header row
        
        # Adjust sizes iteratively
        while max_header > 12 and max_event > 6:
            test_height = (
                max_header +  # Header height
                (max_event * 1.2 * min(max_events_per_day, 3))  # Event text height (with leading)
            )
            
            if test_height <= cell_height * 0.9:  # Leave 10% margin
                break
                
            # Reduce sizes proportionally
            max_header -= 1
            max_event = max(6, max_event - 0.5)
        
        return int(max_header), int(max_event)

    def load_events(self, csv_file):
        """Load events from CSV file"""
        if not csv_file:
            return
            
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                event = {
                    'description': row['event'],
                    'type': row.get('type', 'other')
                }
                
                date_str = row['date'].strip()
                if len(date_str) == 5:  # MM-DD format
                    month, day = map(int, date_str.split('-'))
                    if month not in self.recurring_events:
                        self.recurring_events[month] = {}
                    if day not in self.recurring_events[month]:
                        self.recurring_events[month][day] = []
                    self.recurring_events[month][day].append(event)
                else:  # YYYY-MM-DD format
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    if date not in self.specific_events:
                        self.specific_events[date] = []
                    self.specific_events[date].append(event)

    def create_month_table(self, year, month, header_size, event_size):
        """Create month table with modern styling"""
        self.setup_styles(header_size, event_size)
        
        # Get calendar data and create basic structure
        cal_matrix = cal.monthcalendar(year, month)
        headers = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if cal.firstweekday() == 6:
            headers = headers[-1:] + headers[:-1]
        
        # Modern table style
        base_style = [
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors['header_bg'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(self.colors['header_text'])),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), event_size * 1.1),
            ('BOTTOMPADDING', (0, 0), (-1, 0), self.cell_padding * 1.5),
            
            # Grid styling
            ('GRID', (0, 0), (-1, -1), self.grid_width, colors.HexColor(self.colors['grid'])),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Cell padding
            ('LEFTPADDING', (0, 0), (-1, -1), self.cell_padding),
            ('RIGHTPADDING', (0, 0), (-1, -1), self.cell_padding),
            ('TOPPADDING', (0, 0), (-1, -1), self.cell_padding),
            ('BOTTOMPADDING', (0, 0), (-1, -1), self.cell_padding),
        ]
        
        # Add rounded corners if specified
        if self.corner_radius > 0:
            base_style.extend([
                ('ROUNDEDCORNERS', [self.corner_radius]),
            ])

        # Format calendar data
        table_data = [headers]
        for week in cal_matrix:
            row_data = []
            for day in week:
                if day == 0:
                    cell_content = ''
                else:
                    cell_content = [Paragraph(f"<b>{day}</b>", self.styles['DayNumber'])]
                    
                    # Collect all events for this day
                    events = []
                    current_date = date(year, month, day)
                    
                    # Add specific events
                    if current_date in self.specific_events:
                        events.extend(self.specific_events[current_date])
                    
                    # Add recurring events
                    if month in self.recurring_events and day in self.recurring_events[month]:
                        events.extend(self.recurring_events[month][day])
                    
                    # Add holiday
                    if current_date in self.holidays:
                        events.append({
                            'description': self.holidays[current_date],
                            'type': 'holiday'
                        })
                    
                    # Add events to cell (limited to 3)
                    for event in events[:3]:
                        style = self.styles['EventText']
                        if event['type'] == 'holiday':
                            style = ParagraphStyle(
                                'HolidayStyle',
                                parent=self.styles['EventText'],
                                textColor=colors.HexColor(self.colors['holiday_text'])
                            )
                        event_text = Paragraph(event['description'], style)
                        cell_content.append(event_text)
                
                row_data.append(cell_content if isinstance(cell_content, list) else '')
            table_data.append(row_data)
        
        # Calculate row heights based on compact mode
        row_factor = 0.8 if self.compact_mode else 1.0
        num_weeks = len(cal_matrix)
        available_height = self.page_size[1] - 80*mm
        row_height = (available_height / num_weeks) * row_factor
        row_heights = [12*mm] + [row_height] * num_weeks

        return table_data, TableStyle(base_style), row_heights

    def generate_calendar(self, year, output_file):
        self.year = year
        
        # Load holidays if specified
        holiday_country = self.styling.get('holidays')
        if holiday_country and holiday_country != 'none':
            self.holidays = get_holidays(year, holiday_country)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_file,
            pagesize=self.page_size,
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        # Calculate available height for the table
        available_height = self.page_size[1] - (doc.topMargin + doc.bottomMargin + 30*mm)
        
        story = []
        for month in range(1, 13):
            # Calculate optimal font sizes for this month
            header_size, event_size = self.calculate_optimal_sizes(year, month, available_height)
            
            # Add month header
            month_name = cal.month_name[month]
            story.append(Paragraph(
                f"{month_name} {year}",
                ParagraphStyle(
                    'MonthHeader',
                    fontSize=header_size,
                    alignment=1,
                    spaceAfter=20
                )
            ))
            
            # Create month table with calculated sizes
            table_data, style, row_heights = self.create_month_table(year, month, header_size, event_size)
            
            # Calculate table width
            available_width = self.page_size[0] - (doc.leftMargin + doc.rightMargin)
            col_width = available_width / 7
            
            table = Table(table_data, colWidths=[col_width]*7, rowHeights=row_heights)
            table.setStyle(style)
            
            story.append(table)
            
            if month < 12:
                story.append(PageBreak())
        
        # Build the document
        doc.build(story)

def generate_calendar(year, csv_file, output_file, styling=None):
    """Generate a calendar PDF with dynamic sizing"""
    calendar_gen = DynamicCalendarGenerator(styling)
    if csv_file:
        calendar_gen.load_events(csv_file)
    calendar_gen.generate_calendar(year, output_file)