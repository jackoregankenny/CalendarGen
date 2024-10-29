import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from webapp.app import app

if __name__ == '__main__':
    # Allow external access and set port explicitly
    app.run(
        host='0.0.0.0',  # Allow external access
        port=4321,       # Specify port
        debug=True       # Keep debug mode for development
    )