#!/usr/bin/env python3
"""
Simple packaging script for Dify plugin
Creates a .difypkg file (which is essentially a zip file)
"""

import os
import zipfile
import json

def create_package():
    # Read manifest to get plugin name
    with open('manifest.yaml', 'r') as f:
        # Simple parsing to get name
        for line in f:
            if 'name:' in line:
                plugin_name = line.split(':')[1].strip().strip('"').strip("'")
                break
    
    package_name = f"{plugin_name}.difypkg"
    
    # Files and directories to include
    include_items = [
        'manifest.yaml',
        'provider/',
        'tools/',
        '_assets/',
        'requirements.txt',
        'main.py',
        'PRIVACY.md',
        '.env.example'
    ]
    
    # Files to exclude
    exclude_patterns = [
        '__pycache__',
        '.pyc',
        '.env',
        '.git',
        '.DS_Store'
    ]
    
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in include_items:
            if os.path.isfile(item):
                zipf.write(item)
            elif os.path.isdir(item):
                for root, dirs, files in os.walk(item):
                    # Remove excluded directories
                    dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                    
                    for file in files:
                        if not any(pattern in file for pattern in exclude_patterns):
                            file_path = os.path.join(root, file)
                            zipf.write(file_path)
    
    print(f"✅ Plugin packaged successfully: {package_name}")
    print(f"📦 Package size: {os.path.getsize(package_name) / 1024:.2f} KB")

if __name__ == "__main__":
    create_package()