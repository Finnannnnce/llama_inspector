#!/usr/bin/env python3
import subprocess
import os
from dotenv import load_dotenv
import socket
import threading
import time

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def terminate_process(process):
    """Safely terminate a process"""
    if process and process.poll() is None:
        process.terminate()
        process.wait(timeout=5)

def monitor_processes(processes):
    """Monitor processes and exit if any of them dies"""
    while all(p.poll() is None for p in processes):
        time.sleep(1)
    for p in processes:
        terminate_process(p)

def main():
    # Load environment variables
    load_dotenv()
    
    # Check if ports are available
    if is_port_in_use(8000):
        print("Error: Port 8000 is already in use")
        return

    api_process = None
    streamlit_process = None
    
    try:
        # Start FastAPI server
        api_process = subprocess.Popen([
            "uvicorn",
            "src.api.app:app",
            "--host", "0.0.0.0",
            "--port", "8000", 
            "--log-level", "info"
        ])

        # Start Streamlit server
        streamlit_process = subprocess.Popen([
            "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.baseUrlPath", ""
        ])

        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(
            target=monitor_processes, 
            args=([api_process, streamlit_process],))
        monitor_thread.start()

    except KeyboardInterrupt:
        print("\nShutting down servers...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if api_process:
            terminate_process(api_process)
        if streamlit_process:
            terminate_process(streamlit_process)

if __name__ == "__main__":
    main()