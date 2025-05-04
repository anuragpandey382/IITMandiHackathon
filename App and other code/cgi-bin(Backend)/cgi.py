#!/usr/bin/env python3

import cgi
import cgitb
import json
import os
import traceback

# Enable debugging for detailed tracebacks
cgitb.enable()

# Directory where files will be saved (writable directory)
UPLOAD_DIR = '/tmp/uploads'

try:
    # Create with full permissions to avoid permission issues
    os.makedirs(UPLOAD_DIR, mode=0o777, exist_ok=True)
    if not os.access(UPLOAD_DIR, os.W_OK):
        raise PermissionError(f"Upload directory '{UPLOAD_DIR}' is not writable.")

    # Parse incoming form data
    form = cgi.FieldStorage()
    file_field = form['audio_file'] if 'audio_file' in form else None

    saved = False
    filename = None
    filepath = None

    if file_field is not None and getattr(file_field, 'filename', None):
        filename = os.path.basename(file_field.filename)
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(file_field.file.read())
        saved = True

    # List directory contents for debugging
    dir_contents = os.listdir(UPLOAD_DIR)

    # Build response
    if saved:
        payload = {
            "status": "success",
            "filename": filename,
            "path": filepath
        }
    else:
        payload = {
            "status": "error",
            "message": "No file uploaded or filename missing"
        }

    response = {
        "payload": payload,
        "debug": {
            "upload_dir": UPLOAD_DIR,
            "dir_contents": dir_contents
        }
    }

    print("Content-Type: application/json")
    print()
    print(json.dumps(response))

except Exception as e:
    print("Content-Type: application/json")
    print()
    error_response = {
        "error": str(e),
        "trace": traceback.format_exc().splitlines(),
        "upload_dir": UPLOAD_DIR,
        # safe dir list
        "dir_contents": os.listdir(UPLOAD_DIR) if os.path.isdir(UPLOAD_DIR) else []
    }
    print(json.dumps(error_response))
