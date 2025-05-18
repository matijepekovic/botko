"""
Main application module for the LinkedIn Bot desktop application.
"""

import sys
import os
import argparse
from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime

# For local imports, use relative imports
from .main_window import MainWindow
from ..core.scheduler import scheduler

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='LinkedIn Bot Desktop Application')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()

def main():
    """Main entry point for the desktop application."""
    args = parse_arguments()
    
    # Create the application
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("LinkedIn Bot")
    app.setOrganizationName("LinkedInBot")
    app.setOrganizationDomain("linkedinbot.app")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Load settings
    settings = QtCore.QSettings()
    
    # Create the main window
    main_window = MainWindow(debug_mode=args.debug)
    main_window.show()
    
    # Start the scheduler in a background thread
    scheduler.start_scheduler()
    
    # Execute the application
    result = app.exec_()
    
    # Stop the scheduler when the application exits
    scheduler.stop_scheduler()
    
    return result

if __name__ == "__main__":
    sys.exit(main())