 #!/bin/bash

# Function to activate virtual environment
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "Virtual environment not found"
        exit 1
    fi
}

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating new virtual environment..."
    python -m venv venv
    activate_venv
    xcode-select --install || true  # Install command line tools if needed
    pip install watchdog
    pip install -r requirements.txt
else
    activate_venv
fi

echo "Starting application in virtual environment..."
python run.py