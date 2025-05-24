import pandas as pd
import requests
from datetime import datetime
import json
import sys
from config import API_BASE_URL
from core.codelist_utils import map_theme_to_code, map_license_to_code, map_access_rights_to_code

def create_language_object(text, lang="de"):
    return {lang: text}

def create_uri_label_object(uri, label=None):
    obj = {"uri": uri}
    if label:
        obj["label"] = create_language_object(label)
    return obj

def safe_get(row, key, default=None):
    if isinstance(row, dict):
        return row.get(key, default)
    elif isinstance(row, pd.Series):
        return row[key] if key in row and pd.notna(row[key]) else default
    else:
        try:
            val = getattr(row, key, default)
            return val if pd.notna(val) else default
        except:
            return default

def process_keywords(row):
    keywords = []
    for i in range(1, 4):
        key = f'keywords_{i}'
        value = safe_get(row, key)
        if pd.notna(value):
            keywords.append(create_language_object(value))
    return keywords

def process_distribution(row, index):
    access_key = f'distribution_accessUrl_{index}'
    download_key = f'distribution_downloadUrl_{index}'
    license_key = f'distribution_license_label_{index}'
    
    access_url = safe_get(row, access_key)
    download_url = safe_get(row, download_key)
    
    if pd.isna(access_url) and pd.isna(download_url):
        return None

    distribution = {}
    
    if pd.notna(access_url) and pd.notna(download_url):
        url_to_use = access_url
        distribution["accessUrl"] = create_uri_label_object(url_to_use)
        distribution["downloadUrl"] = create_uri_label_object(url_to_use)
    elif pd.notna(access_url):
        distribution["accessUrl"] = create_uri_label_object(access_url)
        distribution["downloadUrl"] = create_uri_label_object(access_url)
    elif pd.notna(download_url):
        distribution["accessUrl"] = create_uri_label_object(download_url)
        distribution["downloadUrl"] = create_uri_label_object(download_url)
    
    license_value = safe_get(row, license_key)
    if pd.notna(license_value):
        license_code = map_license_to_code(license_value)
        if license_code:
            distribution["license"] = {"code": license_code}

    distribution['title'] = {'de': 'Datenexport'}
    distribution['description'] = {'de': 'Export der Daten'}

    return distribution

def create_dataset_payload(row, publisher_identifier=None):
    access_rights_value = safe_get(row, 'accessRights')
    access_rights_code = map_access_rights_to_code(access_rights_value)
    
    payload = {
        "data": {
            "title": create_language_object(row['title']),
            "description": create_language_object(row['description']),
            "identifiers": [row['identificator']],
            "publisher": {"identifier": publisher_identifier or ""},
            "accessRights": {"code": access_rights_code or "PUBLIC"},
            "issued": row['issued'].isoformat() if pd.notna(row['issued']) else None,
            "modified": row['modified'].isoformat() if pd.notna(row['modified']) else None,
        }
    }

    keywords = process_keywords(row)
    if keywords:
        payload["data"]["keywords"] = keywords

    contact_fn = safe_get(row, 'contactPoints_fn')
    contact_email = safe_get(row, 'contactPoints_hasEmail')
    contact_phone = safe_get(row, 'contactPoints_hasTelephone')
    
    if pd.notna(contact_fn) or pd.notna(contact_email):
        contact_point = {
            "kind": "Organization"
        }
        
        if publisher_identifier:
            contact_point["fn"] = create_language_object(publisher_identifier)
        
        if pd.notna(contact_fn):
            contact_point["hasAddress"] = create_language_object(contact_fn)
            
        if pd.notna(contact_email):
            contact_point["hasEmail"] = contact_email
        if pd.notna(contact_phone):
            contact_point["hasTelephone"] = contact_phone
        payload["data"]["contactPoints"] = [contact_point]

    theme_value = safe_get(row, 'themes_label')
    if pd.notna(theme_value):
        theme_code = map_theme_to_code(theme_value)
        if theme_code:
            payload["data"]["themes"] = [{"code": theme_code}]

    spatial_value = safe_get(row, 'spatial')
    if pd.notna(spatial_value):
        payload["data"]["spatial"] = [spatial_value]

    temp_start = safe_get(row, 'temporalCoverage_start')
    temp_end = safe_get(row, 'temporalCoverage_end')
    
    if pd.notna(temp_start) or pd.notna(temp_end):
        coverage = {}
        if pd.notna(temp_start):
            coverage["start"] = temp_start.isoformat()
        if pd.notna(temp_end):
            coverage["end"] = temp_end.isoformat()
        payload["data"]["temporalCoverage"] = [coverage]

    distributions = []
    for i in range(1, 4):
        dist = process_distribution(row, i)
        if dist:
            distributions.append(dist)
    
    if distributions:
        payload["data"]["distributions"] = distributions

    return payload

def submit_to_api(payload, api_token):
    headers = {
        "Authorization": api_token,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/datasets",
        headers=headers,
        json=payload
    )
    
    if response.status_code not in (200, 201):
        raise Exception(f"API submission failed: {response.status_code} - {response.text}")
    
    return response.text.strip('"')

def main(template_path, api_token=None, organization_id=None, publisher_identifier=None):
    # Remove the default template path fallback since we always provide a path
    if not api_token:
        print("Error: No API token provided")
        sys.exit(1)
    
    if not publisher_identifier:
        print("Error: No publisher identifier provided")
        sys.exit(1)
    
    try:
        df = pd.read_excel(template_path, header=0)
        df = df.dropna(subset=['title', 'description'], how='all')
        
        for col in ['title', 'description', 'identificator']:
            if col in df.columns:
                df = df[df[col] != col]
        
        actual_rows = len(df)
        print(f"Successfully loaded {actual_rows} valid entries from {template_path}")
        
        if actual_rows == 0:
            print("Warning: No valid data rows found in the Excel file")
            return {
                'success_count': 0,
                'error_count': 0,
                'total_count': 0,
                'message': "No valid data rows found in the Excel file"
            }
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        sys.exit(1)
    
    success_count = 0
    error_count = 0
    successful_datasets = []
    
    print("\nStarting dataset import...\n")
    
    for idx, row in df.iterrows():
        title_value = safe_get(row, 'title')
        if pd.isna(title_value) or not title_value:
            continue
            
        identificator = safe_get(row, 'identificator', f'Dataset_{idx}')
        print(f"Processing dataset {idx + 1}: {identificator}")
        
        try:
            payload = create_dataset_payload(row, publisher_identifier)
            dataset_id = submit_to_api(payload, api_token)
            success_count += 1
            
            successful_datasets.append({
                'id': dataset_id,
                'title': title_value,
                'identifier': identificator
            })
            print(f"✓ Success - Dataset ID: {dataset_id}\n")
            
        except Exception as e:
            error_count += 1
            print(f"✗ Error: {str(e)}\n")
    
    print("=== Import Summary ===")
    print(f"Total processed: {success_count + error_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {error_count}")
    
    return {
        'successful_datasets': successful_datasets,
        'success_count': success_count,
        'error_count': error_count,
        'total_count': success_count + error_count
    }