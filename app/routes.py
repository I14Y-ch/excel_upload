import os
import uuid
import jwt
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename

from config import ALLOWED_EXTENSIONS, JWT_DECODE_OPTIONS
from core import import_datasets

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_jwt_token(token):
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        
        decoded = jwt.decode(token, options=JWT_DECODE_OPTIONS)
        
        agencies = decoded.get('agencies', [])
        if not agencies:
            raise ValueError("Keine Organisationen im Token gefunden")
        
        first_agency = agencies[0]
        if '\\' in first_agency:
            parts = first_agency.split('\\')
            org_id = parts[0]
            publisher_name = parts[1] if len(parts) > 1 else org_id
        else:
            org_id = first_agency
            publisher_name = first_agency
        
        return {
            'organization_id': org_id,
            'publisher_name': publisher_name,
            'user_email': decoded.get('email', ''),
            'user_name': f"{decoded.get('given_name', '')} {decoded.get('family_name', '')}".strip(),
            'agencies': agencies
        }
    except jwt.ExpiredSignatureError:
        raise ValueError("Token ist abgelaufen")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Ungültiger Token: {str(e)}")
    except Exception as e:
        raise ValueError(f"Fehler beim Parsen des Tokens: {str(e)}")

def generate_i14y_links(result):
    links = []
    
    if result and isinstance(result, dict) and 'successful_datasets' in result:
        successful_datasets = result['successful_datasets']
        
        for dataset in successful_datasets:
            if isinstance(dataset, dict) and 'id' in dataset:
                dataset_id = dataset['id']
                title = dataset.get('title', 'Dataset')
                
                if dataset_id and dataset_id != 'N/A':
                    link = f"https://input.i14y.admin.ch/catalog/datasets/{dataset_id}/"
                    links.append({
                        'id': dataset_id,
                        'title': title,
                        'link': link
                    })
    
    return links

def delete_uploaded_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Warning: Failed to delete temporary file {filepath}: {str(e)}")

def register_routes(app):
    # Use system temp directory or create uploads in a location we know is writable
    import tempfile
    upload_folder = os.environ.get('UPLOAD_FOLDER', 
                                  os.path.join(tempfile.gettempdir(), 'i14y_uploads'))
    
    # Make sure the directory exists and is writable
    os.makedirs(upload_folder, exist_ok=True)
    
    # Test if directory is writable
    try:
        test_file = os.path.join(upload_folder, 'test_write.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"Successfully confirmed upload directory is writable: {upload_folder}")
    except Exception as e:
        print(f"WARNING: Upload directory may not be writable: {upload_folder}, Error: {e}")
        # Fall back to /tmp which should always be writable
        upload_folder = os.path.join('/tmp', 'i14y_uploads')
        os.makedirs(upload_folder, exist_ok=True)
        print(f"Using fallback upload directory: {upload_folder}")
    
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            flash('Keine Datei ausgewählt')
            return redirect(request.url)
        
        file = request.files['file']
        access_token = request.form.get('access_token', '').strip()
        
        if file.filename == '':
            flash('Keine Datei ausgewählt')
            return redirect(url_for('index'))
        
        if not access_token:
            flash('Zugriffstoken ist erforderlich')
            return redirect(url_for('index'))
        
        try:
            org_info = parse_jwt_token(access_token)
        except ValueError as e:
            flash(f'Token-Fehler: {str(e)}')
            return redirect(url_for('index'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(upload_folder, unique_filename)
            
            # Double-check directory exists before saving
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            file.save(filepath)
            
            try:
                # Process file synchronously
                result = import_datasets.main(
                    template_path=filepath,
                    api_token=f"Bearer {access_token}" if not access_token.startswith('Bearer ') else access_token,
                    organization_id=org_info['organization_id'],
                    publisher_identifier=org_info['publisher_name']
                )
                
                # Generate links
                i14y_links = generate_i14y_links(result)
                
                # Store results in session for display
                if result:
                    success_count = result.get('success_count', 0)
                    error_count = result.get('error_count', 0)
                    
                    session['import_result'] = {
                        'org_info': org_info,
                        'success_count': success_count,
                        'error_count': error_count,
                        'i14y_links': i14y_links,
                        'message': f'Import abgeschlossen: {success_count} erfolgreich, {error_count} fehlgeschlagen'
                    }
                    
                    if error_count > 0 and success_count > 0:
                        status = 'completed_with_errors'
                    elif error_count > 0 and success_count == 0:
                        status = 'error'
                    else:
                        status = 'completed'
                        
                    session['import_status'] = status
                
            except Exception as e:
                import traceback
                session['import_result'] = {
                    'org_info': org_info,
                    'message': f'Fehler beim Import: {str(e)}',
                    'error_details': traceback.format_exc()[:500]  # Limit error length
                }
                session['import_status'] = 'error'
            
            finally:
                # Clean up the file
                delete_uploaded_file(filepath)
            
            # Redirect to results page
            return redirect(url_for('results'))
        else:
            flash('Nur Excel-Dateien (.xlsx) sind erlaubt')
            return redirect(url_for('index'))

    @app.route('/results')
    def results():
        # Show results from session
        if 'import_result' not in session:
            flash('Keine Import-Ergebnisse gefunden')
            return redirect(url_for('index'))
            
        return render_template('results.html', 
                              result=session['import_result'],
                              status=session.get('import_status', 'unknown'))
