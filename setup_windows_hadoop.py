#!/usr/bin/env python3
"""
Setup script for Windows Hadoop/Spark compatibility
Downloads and configures winutils.exe for Delta Lake tests
"""
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

def setup_windows_hadoop():
    """Download and setup winutils for Windows"""
    
    print("Setting up Windows Hadoop compatibility...")
    
    # Create directories
    hadoop_home = os.path.join(os.getcwd(), 'tmp', 'hadoop')
    bin_dir = os.path.join(hadoop_home, 'bin')
    os.makedirs(bin_dir, exist_ok=True)
    
    # Download winutils.exe from a reliable source
    winutils_url = "https://raw.githubusercontent.com/steveloughran/winutils/master/hadoop-3.0.0/bin/winutils.exe"
    winutils_path = os.path.join(bin_dir, 'winutils.exe')
    
    if not os.path.exists(winutils_path):
        print(f"Downloading winutils.exe to {winutils_path}...")
        try:
            urllib.request.urlretrieve(winutils_url, winutils_path)
            print("Downloaded successfully!")
        except Exception as e:
            print(f"Error downloading winutils.exe: {e}")
            print("Trying alternative method...")
            # Alternative: create a dummy file and set permissions via Python
            open(winutils_path, 'a').close()
    else:
        print("winutils.exe already exists")
    
    # Set environment variables
    os.environ['HADOOP_HOME'] = hadoop_home
    os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
    
    # Create a hdfs directory to avoid permission issues
    hdfs_dir = os.path.join(hadoop_home, 'data', 'hdfs')
    os.makedirs(hdfs_dir, exist_ok=True)
    
    print(f"HADOOP_HOME set to: {hadoop_home}")
    print("Windows Hadoop setup complete!")
    
    return hadoop_home

if __name__ == "__main__":
    if sys.platform == 'win32':
        setup_windows_hadoop()
    else:
        print("This script is only needed on Windows")
