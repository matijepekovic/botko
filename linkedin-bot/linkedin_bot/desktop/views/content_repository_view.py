"""
Content repository view for the LinkedIn Bot desktop application.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime

from ...services.content_service import ContentService

class ContentRepositoryView(QtWidgets.QWidget):
    """View for managing the content repository."""
    
    def __init__(self, parent=None):
        """Initialize the content repository view."""
        super().__init__(parent)
        
        self.parent = parent
        self.init_ui()
        
        # Refresh the view initially
        self.refresh()
    
    def init_ui(self):
        """Initialize the UI components."""
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title and actions bar
        title_layout = QtWidgets.QHBoxLayout()
        
        # Title
        title_label = QtWidgets.QLabel("Content Repository")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        # Spacer
        title_layout.addStretch()
        
        # Add Content button
        add_button = QtWidgets.QPushButton("Add New Content")
        add_button.clicked.connect(self.show_add_content_dialog)
        title_layout.addWidget(add_button)
        
        # Import CSV button
        import_button = QtWidgets.QPushButton("Import from CSV")
        import_button.clicked.connect(self.import_csv)
        title_layout.addWidget(import_button)
        
        # Reset All button
        reset_button = QtWidgets.QPushButton("Reset All Content")
        reset_button.clicked.connect(self.reset_all_content)
        title_layout.addWidget(reset_button)
        
        # Refresh button
        refresh_button = QtWidgets.QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        title_layout.addWidget(refresh_button)
        
        layout.addLayout(title_layout)
        
        # Content table
        self.content_table = QtWidgets.QTableWidget()
        self.content_table.setColumnCount(5)
        self.content_table.setHorizontalHeaderLabels(["ID", "Content", "Category", "Status", "Actions"])
        
        # Set column stretching
        header = self.content_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        
        layout.addWidget(self.content_table)
    
    def refresh(self):
        """Refresh the content repository data."""
        try:
            # Get content
            content = ContentService.get_all_content()
            
            # Update table
            self.content_table.setRowCount(len(content))
            
            for i, item in enumerate(content):
                # ID
                id_item = QtWidgets.QTableWidgetItem(str(item['id']))
                id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.content_table.setItem(i, 0, id_item)
                
                # Content (truncate if too long)
                content_text = item['text']
                if len(content_text) > 100:
                    content_text = content_text[:97] + "..."
                
                content_item = QtWidgets.QTableWidgetItem(content_text)
                content_item.setFlags(content_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.content_table.setItem(i, 1, content_item)
                
                # Category
                category_item = QtWidgets.QTableWidgetItem(item['category'])
                category_item.setFlags(category_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.content_table.setItem(i, 2, category_item)
                
                # Status
                status_text = "Used" if item['is_used'] else "Available"
                status_item = QtWidgets.QTableWidgetItem(status_text)
                status_item.setFlags(status_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.content_table.setItem(i, 3, status_item)
                
                # Actions
                actions_widget = QtWidgets.QWidget()
                actions_layout = QtWidgets.QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                if item['is_used']:
                    reset_button = QtWidgets.QPushButton("Reset")
                    reset_button.setProperty("content_id", item['id'])
                    reset_button.clicked.connect(self.reset_content)
                    actions_layout.addWidget(reset_button)
                
                self.content_table.setCellWidget(i, 4, actions_widget)
            
        except Exception as e:
            print(f"Error refreshing content repository: {str(e)}")
            if self.parent:
                self.parent.show_error("Refresh Error", f"Error refreshing content repository: {str(e)}")
    
    def show_add_content_dialog(self):
        """Show dialog for adding new content."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Content to Repository")
        dialog.setMinimumWidth(500)
        
        # Dialog layout
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Content field
        layout.addWidget(QtWidgets.QLabel("Post Content:"))
        content_edit = QtWidgets.QTextEdit()
        content_edit.setMinimumHeight(150)
        layout.addWidget(content_edit)
        
        # Category field
        category_layout = QtWidgets.QHBoxLayout()
        category_layout.addWidget(QtWidgets.QLabel("Category (Optional):"))
        category_edit = QtWidgets.QLineEdit()
        category_layout.addWidget(category_edit)
        
        layout.addLayout(category_layout)
        
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
            category = category_edit.text() or None
            
            if not post_text:
                if self.parent:
                    self.parent.show_error("Validation Error", "Content cannot be empty")
                return
            
            try:
                content_id = ContentService.add_content(post_text, category)
                if self.parent:
                    self.parent.show_message("Success", f"Content added with ID: {content_id}")
                self.refresh()
            except Exception as e:
                print(f"Error adding content: {str(e)}")
                if self.parent:
                    self.parent.show_error("Add Error", f"Error adding content: {str(e)}")
    
    def import_csv(self):
        """Import content from a CSV file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Content", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                count = ContentService.import_from_csv(file_path)
                if self.parent:
                    self.parent.show_message("Import Complete", f"Successfully imported {count} content items")
                self.refresh()
            except Exception as e:
                print(f"Error importing CSV: {str(e)}")
                if self.parent:
                    self.parent.show_error("Import Error", f"Error importing CSV: {str(e)}")
    
    def reset_content(self):
        """Reset a content item for reuse."""
        button = self.sender()
        if button:
            content_id = button.property("content_id")
            
            try:
                success = ContentService.reset_content(content_id)
                if success:
                    if self.parent:
                        self.parent.show_message("Success", f"Content {content_id} reset for reuse")
                    self.refresh()
                else:
                    if self.parent:
                        self.parent.show_error("Reset Error", f"Failed to reset content {content_id}")
            except Exception as e:
                print(f"Error resetting content: {str(e)}")
                if self.parent:
                    self.parent.show_error("Reset Error", f"Error resetting content: {str(e)}")
    
    def reset_all_content(self):
        """Reset all content for reuse."""
        # Confirm reset
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to reset all content for reuse?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if confirm == QtWidgets.QMessageBox.Yes:
            try:
                success = ContentService.reset_content()
                if success:
                    if self.parent:
                        self.parent.show_message("Success", "All content reset for reuse")
                    self.refresh()
                else:
                    if self.parent:
                        self.parent.show_error("Reset Error", "Failed to reset content")
            except Exception as e:
                print(f"Error resetting all content: {str(e)}")
                if self.parent:
                    self.parent.show_error("Reset Error", f"Error resetting all content: {str(e)}")