#!/bin/bash
echo "Running script.sh"

echo "Creating virtual environment"
python3 -m venv venv
source venv/bin/activate

echo "Installing requirements"
apt-get install poppler-utils
pip install -r requirements.txt

echo "Running app.py"
python3 app.py