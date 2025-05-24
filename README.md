# I14Y Dataset Import Tool

## Metadata Import Made Easy

Streamline your dataset management workflow! This tool enables efficient bulk importation of dataset metadata into Switzerland's I14Y platform.

## Deployment on Digital Ocean App Platform

### Prerequisites
1. A GitHub account with this repository pushed to it
2. A Digital Ocean account

### Steps
1. Create a new app on Digital Ocean App Platform
2. Connect your GitHub repository
3. Configure environment variables:
   - `FLASK_SECRET_KEY`: A secure random string for session encryption

### Local Development
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python run.py`

## Usage
1. Access the web interface
2. Paste your I14Y access token
3. Upload your Excel file with dataset information
4. View the import results
