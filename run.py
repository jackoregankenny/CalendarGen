import os
import sys

# Get the absolute path of the project root
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from calendargen.webapp.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4321))
    app.run(host='0.0.0.0', port=port, debug=True)