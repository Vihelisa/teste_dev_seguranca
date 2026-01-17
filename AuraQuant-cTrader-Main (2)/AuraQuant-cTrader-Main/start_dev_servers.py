
#!/usr/bin/env python3
import os
import sys
import threading
import subprocess
import time

def run_django():
    """Run Django development server"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

def run_frontend():
    """Run React development server"""
    os.chdir('frontend')
    subprocess.run(['npm', 'run', 'dev'], check=True)

if __name__ == '__main__':
    # Start Django server in a thread
    django_thread = threading.Thread(target=run_django)
    django_thread.daemon = True
    django_thread.start()
    
    print("Django server starting on http://0.0.0.0:8000")
    time.sleep(3)
    
    print("Starting React frontend on http://0.0.0.0:5173")
    run_frontend()
