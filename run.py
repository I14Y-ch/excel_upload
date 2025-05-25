from flask import Flask
from config import FLASK_SECRET_KEY, MAX_CONTENT_LENGTH
import os
import tempfile

# Define the necessary folders
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')

# Define upload folder using environment variable or temp directory
upload_folder = os.environ.get('UPLOAD_FOLDER', 
                              os.path.join(tempfile.gettempdir(), 'i14y_uploads'))
os.makedirs(upload_folder, exist_ok=True)

# Create the Flask app
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Configure the app
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = upload_folder

# Register routes
from app.routes import register_routes
register_routes(app)

if __name__ == '__main__':
    # Use PORT environment variable if available (for Digital Ocean)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)