import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# First verify we can import the core package
from src.calendargen import CalendarGenerator, generate_calendar, __version__

# Then import the webapp - now at correct path
from src.webapp.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4321))
    app.run(host='0.0.0.0', port=port, debug=True)