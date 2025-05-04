#!/usr/bin/env python3

import cgi
import cgitb
import json
import os

# Enable debugging
cgitb.enable()

# Create instance of FieldStorage
form = cgi.FieldStorage()

# Attempt to retrieve the uploaded audio file; expecting field name 'audio_file'
file_field = form['audio_file'] if 'audio_file' in form else None

# Optionally save the file to a temporary location
if file_field and file_field.filename:
    # Sanitize filename
    filename = os.path.basename(file_field.filename)
    upload_dir = './tmp'
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(file_field.file.read())
    # You now have the file saved at `filepath`

# Prepare JSON response
response = {
    "payload": {}
}

# Output HTTP header and JSON
print("Content-Type: application/json")
print()
print(json.dumps(response))
