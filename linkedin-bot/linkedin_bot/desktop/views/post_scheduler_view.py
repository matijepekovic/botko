"""
Post scheduler view for the LinkedIn Bot desktop application.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime, timedelta

from ...services.post_service import PostService

class PostSchedulerView(QtWidgets.QWidget):
    """View for scheduling and managing posts."""
    
    def __init__(self, parent=None):
        """Initialize the post scheduler view."""
        super().__init__(parent)
        
        self.parent = parent
        self.init_ui()
        
        # Refresh the view initially
        self.refresh()
        
        # Set up refresh timer
        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        """Initialize the UI components."""
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title and actions bar
        title_layout = QtWidgets.QHBoxLayout()
        
        # Title
        title_label = QtWidgets.QLabel("Scheduled Posts")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        # Spacer
        title_layout.addStretch()
        
        # Add Post button
        add_button = QtWidgets.QPushButton("Schedule New Post")
        add_button.clicked.connect(self.show_add_post_dialog)
        title_layout.addWidget(add_button)
        
        # Refresh button
        refresh_button = QtWidgets.QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        title_layout.addWidget(refresh_button)
        
        layout.addLayout(title_layout)
        
        # Scheduled posts table
        self.posts_table = QtWidgets.QTableWidget()
        self.posts_table.setColumnCount(5)
        self.posts_table.setHorizontalHeaderLabels(["ID", "Content", "Scheduled Time", "Status", "Actions"])
        
        # Set column stretching
        header = self.posts_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        
        layout.addWidget(self.posts_table)
    
    def refresh(self):
        """Refresh the post schedule data."""
        try:
            # Get posts
            posts = PostService.get_all_posts()
            
            # Update table
            self.posts_table.setRowCount(len(posts))
            
            for i, post in enumerate(posts):
                # ID
                id_item = QtWidgets.QTableWidgetItem(str(post['id']))
                id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.posts_table.setItem(i, 0, id_item)
                
                # Content (truncate if too long)
                content = post['text']
                if len(content) > 100:
                    content = content[:97] + "..."
                
                content_item = QtWidgets.QTableWidgetItem(content)
                content_item.setFlags(content_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.posts_table.setItem(i, 1, content_item)
                
                # Scheduled time
                time_item = QtWidgets.QTableWidgetItem(post['scheduled_time'])
                time_item.setFlags(time_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.posts_table.setItem(i, 2, time_item)
                
                # Status
                status_item = QtWidgets.QTableWidgetItem(post['status'].capitalize())
                status_item.setFlags(status_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.posts_table.setItem(i, 3, status_item)
                
                # Actions - only allow delete for pending posts
                actions_widget = QtWidgets.QWidget()
                actions_layout = QtWidgets.QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                if post['status'] == 'pending':
                    delete_button = QtWidgets.QPushButton("Delete")
                    delete_button.setProperty("post_id", post['id'])
                    delete_button.clicked.connect(self.delete_post)
                    actions_layout.addWidget(delete_button)
                
                self.posts_table.setCellWidget(i, 4, actions_widget)
            
            self.posts_table.sortItems(2)  # Sort by scheduled time
            
        except Exception as e:
            print(f"Error refreshing post schedule: {str(e)}")
            if self.parent:
                self.parent.show_error("Refresh Error", f"Error refreshing post schedule: {str(e)}")
    
    def show_add_post_dialog(self):
        """Show dialog for adding a new scheduled post."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Schedule New Post")
        dialog.setMinimumWidth(500)
        
        # Dialog layout
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Content field
        layout.addWidget(QtWidgets.QLabel("Post Content:"))
        content_edit = QtWidgets.QTextEdit()
        content_edit.setMinimumHeight(150)
        layout.addWidget(content_edit)
        
        # Date and time fields
        date_time_layout = QtWidgets.QHBoxLayout()
        
        # Date picker
        date_time_layout.addWidget(QtWidgets.QLabel("Date:"))
        date_edit = QtWidgets.QDateEdit(QtCore.QDate.currentDate().addDays(1))
        date_edit.setCalendarPopup(True)
        date_time_layout.addWidget(date_edit)
        
        # Time picker
        date_time_layout.addWidget(QtWidgets.QLabel("Time:"))
        time_edit = QtWidgets.QTimeEdit(QtCore.QTime(12, 0))
        date_time_layout.addWidget(time_edit)
        
        layout.addLayout(date_time_layout)
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Show dialog
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            post_text = content_edit.toPlainText()
            schedule_date = date_edit.date().toString("yyyy-MM-dd")
            schedule_time = time_edit.time().toString("HH:mm")
            
            if not post_text:
                if self.parent:
                    self.parent.show_error("Validation Error", "Post content cannot be empty")
                return
            
            try:
                post_id = PostService.add_post(post_text, schedule_date, schedule_time)
                if self.parent:
                    self.parent.show_message("Success", f"Post scheduled with ID: {post_id}")
                self.refresh()
            except Exception as e:
                print(f"Error scheduling post: {str(e)}")
                if self.parent:
                    self.parent.show_error("Schedule Error", f"Error scheduling post: {str(e)}")
    
    def delete_post(self):
        """Delete a scheduled post."""
        button = self.sender()
        if button:
            post_id = button.property("post_id")
            
            # Confirm deletion
            confirm = QtWidgets.QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete post {post_id}?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if confirm == QtWidgets.QMessageBox.Yes:
                try:
                    success = PostService.delete_post(post_id)
                    if success:
                        if self.parent:
                            self.parent.show_message("Success", f"Post {post_id} deleted")
                        self.refresh()
                    else:
                        if self.parent:
                            self.parent.show_error("Delete Error", f"Failed to delete post {post_id}")
                except Exception as e:
                    print(f"Error deleting post: {str(e)}")
                    if self.parent:
                        self.parent.show_error("Delete Error", f"Error deleting post: {str(e)}")