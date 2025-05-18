"""
Main window for the LinkedIn Bot desktop application.
"""

import os
import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime
from .views.dashboard_view import DashboardView
from .views.post_scheduler_view import PostSchedulerView
from .views.content_repository_view import ContentRepositoryView
from .views.campaign_view import CampaignView
from .views.settings_view import SettingsView

# Import views - we'll only import DashboardView for now 
# since that's the only one we've implemented
from .views.dashboard_view import DashboardView

class MainWindow(QtWidgets.QMainWindow):
    """Main window for the LinkedIn Bot desktop application."""
    
    def __init__(self, debug_mode=False):
        """
        Initialize the main window.
        
        Args:
            debug_mode: Whether to enable debug features
        """
        super().__init__()
        
        self.debug_mode = debug_mode
        self.setWindowTitle("LinkedIn Bot")
        self.setMinimumSize(1024, 768)
        
        # Initialize components
        self._create_menu()
        self._create_toolbar()
        self._create_statusbar()
        self._create_tabs()
        
        # Set up auto-refresh timer
        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_views)
        self.refresh_timer.start(60000)  # Refresh every minute
    
    def _create_menu(self):
        """Create the main menu."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        # Export action
        export_action = QtWidgets.QAction("&Export Content Repository...", self)
        export_action.setStatusTip("Export content repository to CSV")
        export_action.triggered.connect(self.export_content)
        file_menu.addAction(export_action)
        
        # Import action
        import_action = QtWidgets.QAction("&Import Content...", self)
        import_action.setStatusTip("Import content from CSV")
        import_action.triggered.connect(self.import_content)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Settings action
        settings_action = QtWidgets.QAction("&Settings", self)
        settings_action.setStatusTip("Configure application settings")
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QtWidgets.QAction("E&xit", self)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        # About action
        about_action = QtWidgets.QAction("&About", self)
        about_action.setStatusTip("Show the application's About box")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _create_toolbar(self):
        """Create the main toolbar."""
        self.toolbar = QtWidgets.QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QtCore.QSize(24, 24))
        self.addToolBar(self.toolbar)
        
        # Refresh action
        refresh_action = QtWidgets.QAction("Refresh", self)
        refresh_action.setStatusTip("Refresh all data")
        refresh_action.triggered.connect(self.refresh_views)
        self.toolbar.addAction(refresh_action)
        
        self.toolbar.addSeparator()
        
        # Add post action
        add_post_action = QtWidgets.QAction("New Post", self)
        add_post_action.setStatusTip("Schedule a new post")
        add_post_action.triggered.connect(self.add_new_post)
        self.toolbar.addAction(add_post_action)
        
        # Add content action
        add_content_action = QtWidgets.QAction("Add Content", self)
        add_content_action.setStatusTip("Add new content to repository")
        add_content_action.triggered.connect(self.add_new_content)
        self.toolbar.addAction(add_content_action)
        
        # New campaign action
        new_campaign_action = QtWidgets.QAction("New Campaign", self)
        new_campaign_action.setStatusTip("Create a new campaign")
        new_campaign_action.triggered.connect(self.create_new_campaign)
        self.toolbar.addAction(new_campaign_action)
    
    def _create_statusbar(self):
        """Create the status bar."""
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Status message
        self.status_label = QtWidgets.QLabel("LinkedIn Bot Ready")
        self.statusBar.addWidget(self.status_label)
    
    def _create_tabs(self):
        """Create the main tab widget and its tabs."""
        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Dashboard tab
        self.dashboard_view = DashboardView(self)
        self.tabs.addTab(self.dashboard_view, "Dashboard")
        
     

def _create_tabs(self):
    """Create the main tab widget and its tabs."""
    self.tabs = QtWidgets.QTabWidget()
    self.setCentralWidget(self.tabs)
    
    # Dashboard tab
    self.dashboard_view = DashboardView(self)
    self.tabs.addTab(self.dashboard_view, "Dashboard")
    
    # Post Scheduler tab
    from .views.post_scheduler_view import PostSchedulerView
    self.post_scheduler_view = PostSchedulerView(self)
    self.tabs.addTab(self.post_scheduler_view, "Scheduled Posts")
    
    # Content Repository tab
    from .views.content_repository_view import ContentRepositoryView
    self.content_repository_view = ContentRepositoryView(self)
    self.tabs.addTab(self.content_repository_view, "Content Repository")
    
        
         # Campaigns tab
    self.campaign_view = CampaignView(self)
    self.tabs.addTab(self.campaign_view, "Campaigns")
    
    # Settings tab
    self.settings_view = SettingsView(self)
    self.tabs.addTab(self.settings_view, "Settings")
    
    def show_message(self, title, message, icon=QtWidgets.QMessageBox.Information):
        """
        Show a message box to the user.
        
        Args:
            title: Title of the message box
            message: Message to display
            icon: Icon to show (default: Information)
        """
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()
    
    def show_error(self, title, message):
        """
        Show an error message box to the user.
        
        Args:
            title: Title of the message box
            message: Error message to display
        """
        self.show_message(title, message, QtWidgets.QMessageBox.Critical)
    
    def refresh_views(self):
        """Refresh all tab views."""
        current_index = self.tabs.currentIndex()
        current_widget = self.tabs.widget(current_index)
        
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
        
        self.status_label.setText(f"Data refreshed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def export_content(self):
        """Export content repository to a CSV file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Content Repository", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                from ..services.content_service import ContentService
                count = ContentService.export_to_csv(file_path)
                self.show_message("Export Complete", f"Successfully exported {count} content items to {file_path}")
            except Exception as e:
                self.show_error("Export Error", f"Error exporting content: {str(e)}")
    
    def import_content(self):
        """Import content from a CSV file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Content", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                from ..services.content_service import ContentService
                count = ContentService.import_from_csv(file_path)
                self.show_message("Import Complete", f"Successfully imported {count} content items")
                
                # Refresh content repository view if it exists
                if hasattr(self, 'content_repository_view'):
                    self.content_repository_view.refresh()
            except Exception as e:
                self.show_error("Import Error", f"Error importing content: {str(e)}")
    
    def open_settings(self):
        """Open the settings tab."""
        # If we have a settings tab, switch to it, otherwise show a message
        if hasattr(self, 'settings_view'):
            self.tabs.setCurrentWidget(self.settings_view)
        else:
            self.show_message("Settings", "Settings tab is not yet implemented.")
    
    def show_about(self):
        """Show the about dialog."""
        QtWidgets.QMessageBox.about(
            self,
            "About LinkedIn Bot",
            """<b>LinkedIn Bot</b> v1.0
            <p>Desktop application for automating LinkedIn posts.
            <p>Copyright &copy; 2025"""
        )
    
    def add_new_post(self):
        """Switch to post scheduler tab and show add dialog."""
        # If we have a post scheduler tab, switch to it and show dialog
        if hasattr(self, 'post_scheduler_view'):
            self.tabs.setCurrentWidget(self.post_scheduler_view)
            self.post_scheduler_view.show_add_post_dialog()
        else:
            self.show_message("Add Post", "Post scheduler tab is not yet implemented.")
    
    def add_new_content(self):
        """Switch to content repository tab and show add dialog."""
        # If we have a content repository tab, switch to it and show dialog
        if hasattr(self, 'content_repository_view'):
            self.tabs.setCurrentWidget(self.content_repository_view)
            self.content_repository_view.show_add_content_dialog()
        else:
            self.show_message("Add Content", "Content repository tab is not yet implemented.")
    
    def create_new_campaign(self):
        """Switch to campaigns tab and show create campaign dialog."""
        # If we have a campaigns tab, switch to it and show dialog
        if hasattr(self, 'campaign_view'):
            self.tabs.setCurrentWidget(self.campaign_view)
            self.campaign_view.show_create_campaign_dialog()
        else:
            self.show_message("Create Campaign", "Campaigns tab is not yet implemented.")