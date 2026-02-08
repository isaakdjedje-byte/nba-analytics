#!/usr/bin/env python3
"""
Complete setup for Windows Hadoop/Spark compatibility
Downloads winutils.exe AND hadoop.dll for Delta Lake tests
"""
import os
import sys
import urllib.request
from pathlib import Path

def download_file(url, dest):
    """Download a file if it doesn't exist"""
    if not os.path.exists(dest):
        print(f"Downloading {os.path.basename(dest)}...")
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"  [OK] Downloaded to {dest}")
            return True
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            return False
    else:
        print(f"  [OK] {os.path.basename(dest)} already exists")
        return True

def setup_windows_hadoop():
    """Download and setup all required files for Windows Hadoop"""
    
    print("="*60)
    print("Complete Windows Hadoop Setup")
    print("="*60)
    
    # Create directories
    hadoop_home = os.path.join(os.getcwd(), 'tmp', 'hadoop')
    bin_dir = os.path.join(hadoop_home, 'bin')
    os.makedirs(bin_dir, exist_ok=True)
    
    # Files to download
    files_to_download = [
        # winutils.exe
        ("https://raw.githubusercontent.com/steveloughran/winutils/master/hadoop-3.0.0/bin/winutils.exe",
         os.path.join(bin_dir, 'winutils.exe')),
        
        # hadoop.dll (alternative sources)
        ("https://github.com/cdarlint/winutils/raw/master/hadoop-3.2.1/bin/hadoop.dll",
         os.path.join(bin_dir, 'hadoop.dll')),
        
        # hdfs.dll
        ("https://github.com/cdarlint/winutils/raw/master/hadoop-3.2.1/bin/hdfs.dll",
         os.path.join(bin_dir, 'hdfs.dll')),
    ]
    
    # Download all files
    success_count = 0
    for url, dest in files_to_download:
        if download_file(url, dest):
            success_count += 1
    
    print(f"\nDownloaded {success_count}/{len(files_to_download)} files")
    
    # Set environment variables
    os.environ['HADOOP_HOME'] = hadoop_home
    os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
    os.environ['SPARK_LOCAL_DIRS'] = os.path.join(os.getcwd(), 'tmp', 'spark')
    os.environ['HADOOP_OPTS'] = '-Djava.library.path=' + bin_dir
    
    # Create required directories
    os.makedirs(os.environ['SPARK_LOCAL_DIRS'], exist_ok=True)
    os.makedirs(os.path.join(hadoop_home, 'data', 'hdfs'), exist_ok=True)
    
    print("\nEnvironment variables set:")
    print(f"  HADOOP_HOME={hadoop_home}")
    print(f"  PATH includes {bin_dir}")
    
    print("\n" + "="*60)
    print("Setup complete! You can now run the tests.")
    print("="*60)
    
    return success_count == len(files_to_download)

if __name__ == "__main__":
    if sys.platform == 'win32':
        success = setup_windows_hadoop()
        sys.exit(0 if success else 1)
    else:
        print("This script is only needed on Windows")
        sys.exit(0)
