"""
Play functionality - opens generated report files.
Uses Python standard library only.
"""

import sys
import subprocess
import os
from pathlib import Path


def play_file(file_path: str) -> bool:
    """
    Open a generated report file in the appropriate application.
    
    Args:
        file_path: Path to the file to open
        
    Returns:
        True if successful, False otherwise
    """
    if not file_path:
        print("Error: No file specified for --play")
        return False
    
    # Check if file exists
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    # Determine file type and open appropriately
    try:
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', file_path], check=True)
        elif sys.platform == 'win32':  # Windows
            os.startfile(file_path)
        else:  # Linux and other Unix-like systems
            subprocess.run(['xdg-open', file_path], check=True)
        
        print(f"✓ Opened {file_path}")
        return True
        
    except subprocess.CalledProcessError:
        print(f"Error: Failed to open {file_path}")
        print("Try opening the file manually")
        return False
    except FileNotFoundError:
        if sys.platform == 'linux':
            print("Error: xdg-open not found. Please install xdg-utils or open the file manually")
        else:
            print(f"Error: Could not find application to open {file_path}")
        return False
    except Exception as e:
        print(f"Error opening file: {e}")
        return False
