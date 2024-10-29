from flask import Flask, render_template, request, send_file, flash
from werkzeug.utils import secure_filename
import os
import tempfile
from datetime import datetime
import csv
import io

# Import our calendar generator
from calendargen.generator import generate_calendar

app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')
app.secret_key = 'your-secret-key-here'  # Required for flash messages

# Configuration
ALLOWED_EXTENSIONS = {'csv'}
TEMP_DIR = tempfile.gettempdir()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_csv_from_text(csv_text):
    """Save CSV text to a temporary file and return the path"""
    if not csv_text.strip():
        return None
        
    try:
        # Validate CSV format
        csv_file = io.StringIO(csv_text)
        reader = csv.DictReader(csv_file)
        
        # Check if CSV has required headers
        required_headers = {'date', 'event'}
        headers = set(reader.fieldnames) if reader.fieldnames else set()
        if not required_headers.issubset(headers):
            raise ValueError("CSV must contain 'date' and 'event' columns")
        
        # Save to temporary file
        temp_path = os.path.join(TEMP_DIR, f'calendar_events_{datetime.now().timestamp()}.csv')
        with open(temp_path, 'w', newline='') as f:
            f.write(csv_text)
        
        return temp_path
    except Exception as e:
        flash(f'Error in CSV format: {str(e)}')
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        year = int(request.form.get('year', datetime.now().year))
        csv_path = None
        
        # Check for CSV file upload
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            if file and allowed_file(file.filename):
                csv_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
                file.save(csv_path)
        
        # Check for pasted CSV if no file was uploaded
        elif csv_text := request.form.get('csv_text'):
            csv_path = save_csv_from_text(csv_text)
        
        # Generate PDF calendar
        pdf_filename = f'calendar_{year}.pdf'
        pdf_path = os.path.join(TEMP_DIR, pdf_filename)
        
        # Get styling options from form
        styling = {
            'header_size': int(request.form.get('header_size', 24)),
            'event_size': int(request.form.get('event_size', 10)),
            'color_scheme': request.form.get('color_scheme', 'minimal'),
            'cell_padding': float(request.form.get('cell_padding', 3)),
            'grid_width': float(request.form.get('grid_width', 0.5)),
            'corner_radius': float(request.form.get('corner_radius', 2)),
            'orientation': request.form.get('orientation', 'P'),
            'paper_size': request.form.get('paper_size', 'A4'),
            'weekstart': request.form.get('weekstart', '0'),
            'holidays': request.form.get('holidays', 'none'),
            'show_weekends': request.form.get('show_weekends') == 'on',
            'compact_mode': request.form.get('compact_mode') == 'true'
        }
        
        try:
            generate_calendar(year, csv_path if csv_path else None, pdf_path, styling)
            
            # Clean up the temporary CSV file
            if csv_path:
                os.remove(csv_path)
            
            # Send the PDF file to the user
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=pdf_filename,
                mimetype='application/pdf'
            )
        
        except Exception as e:
            flash(f'Error generating calendar: {str(e)}')
            return render_template('index.html', current_year=datetime.now().year)
    
    # GET request
    return render_template('index.html', current_year=datetime.now().year)

if __name__ == '__main__':
    app.run(debug=True)