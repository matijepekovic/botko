"""
Dashboard view for the LinkedIn Bot desktop application.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, QDateTime

from ...services.post_service import PostService

class DashboardView(QWidget):
    """Dashboard view showing recent posts and status."""
    
    def __init__(self, parent=None):
        """Initialize the dashboard view."""
        super().__init__(parent)
        
        self.init_ui()
        
        # Refresh the view initially
        self.refresh()
        
        # Set up refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        """Initialize the UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Dashboard")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Stats section
        stats_layout = QHBoxLayout()
        
        # Pending posts
        self.pending_posts_label = QLabel("Pending: 0")
        stats_layout.addWidget(self.pending_posts_label)
        
        # Published posts
        self.published_posts_label = QLabel("Published: 0")
        stats_layout.addWidget(self.published_posts_label)
        
        # Failed posts
        self.failed_posts_label = QLabel("Failed: 0")
        stats_layout.addWidget(self.failed_posts_label)
        
        # Spacer
        stats_layout.addStretch()
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        stats_layout.addWidget(refresh_button)
        
        layout.addLayout(stats_layout)
        
        # Recent posts table
        self.posts_table = QTableWidget()
        self.posts_table.setColumnCount(4)
        self.posts_table.setHorizontalHeaderLabels(["ID", "Content", "Scheduled Time", "Status"])
        
        # Set column stretching
        header = self.posts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.posts_table)
    
    def refresh(self):
        """Refresh the dashboard data."""
        try:
            # Get posts
            posts = PostService.get_all_posts()
            
            # Update stats
            pending_count = sum(1 for post in posts if post['status'] == 'pending')
            published_count = sum(1 for post in posts if post['status'] == 'published')
            failed_count = sum(1 for post in posts if post['status'] == 'failed')
            
            self.pending_posts_label.setText(f"Pending: {pending_count}")
            self.published_posts_label.setText(f"Published: {published_count}")
            self.failed_posts_label.setText(f"Failed: {failed_count}")
            
            # Update table
            self.posts_table.setRowCount(len(posts))
            
            for i, post in enumerate(posts):
                # ID
                id_item = QTableWidgetItem(str(post['id']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                self.posts_table.setItem(i, 0, id_item)
                
                # Content (truncate if too long)
                content = post['text']
                if len(content) > 100:
                    content = content[:97] + "..."
                
                content_item = QTableWidgetItem(content)
                content_item.setFlags(content_item.flags() & ~Qt.ItemIsEditable)
                self.posts_table.setItem(i, 1, content_item)
                
                # Scheduled time
                time_item = QTableWidgetItem(post['scheduled_time'])
                time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
                self.posts_table.setItem(i, 2, time_item)
                
                # Status
                status_item = QTableWidgetItem(post['status'].capitalize())
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                self.posts_table.setItem(i, 3, status_item)
            
            self.posts_table.sortItems(2)  # Sort by scheduled time
            
        except Exception as e:
            print(f"Error refreshing dashboard: {str(e)}")