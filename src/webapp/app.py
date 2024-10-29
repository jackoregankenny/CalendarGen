import os
from flask import Flask, render_template, request, send_file, flash
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime
import csv
import io
from calendargen.generator import generate_calendar

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configuration
ALLOWED_EXTENSIONS = {'csv'}
TEMP_DIR = tempfile.gettempdir()

# Cleanup function for temporary files
def cleanup_temp_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health')
def health_check():
    """Health check endpoint for Koyeb"""
    return {'status': 'healthy'}, 200

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        year = int(request.form.get('year', datetime.now().year))
        csv_path = None
        pdf_path = None
        
        try:
            # Handle file upload or CSV text
            if 'file' in request.files and request.files['file'].filename:
                file = request.files['file']
                if file and allowed_file(file.filename):
                    csv_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
                    file.save(csv_path)
            elif csv_text := request.form.get('csv_text'):
                csv_path = os.path.join(TEMP_DIR, f'calendar_events_{datetime.now().timestamp()}.csv')
                with open(csv_path, 'w', newline='') as f:
                    f.write(csv_text)

            # Generate PDF
            pdf_filename = f'calendar_{year}.pdf'
            pdf_path = os.path.join(TEMP_DIR, pdf_filename)
            
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

            generate_calendar(year, csv_path, pdf_path, styling)

            # Clean up CSV file immediately
            if csv_path:
                cleanup_temp_file(csv_path)

            # Send PDF and clean up
            response = send_file(
                pdf_path,
                as_attachment=True,
                download_name=pdf_filename,
                mimetype='application/pdf'
            )
            
            @response.call_on_close
            def cleanup():
                cleanup_temp_file(pdf_path)

            return response

        except Exception as e:
            # Clean up files in case of error
            if csv_path:
                cleanup_temp_file(csv_path)
            if pdf_path:
                cleanup_temp_file(pdf_path)
            flash(f'Error generating calendar: {str(e)}')
            return render_template('index.html', current_year=datetime.now().year)

    return render_template('index.html', current_year=datetime.now().year)

if __name__ == '__main__':
    # This block will only run for direct Python execution
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)