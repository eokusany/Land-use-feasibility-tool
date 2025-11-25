#!/usr/bin/env python3
"""
Alberta Land Use Feasibility Tool - Main Runner
Run this file to start the web application
"""

import os
from app import app

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('reports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the application
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )
