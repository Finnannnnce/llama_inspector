 #!/bin/bash

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    python -m venv venv
    source venv/bin/activate
    xcode-select --install || true  # Install command line tools if needed
    pip install watchdog
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the application
python run.py