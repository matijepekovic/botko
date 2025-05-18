"""
Campaign view for the LinkedIn Bot desktop application.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime

from ...services.campaign_service import CampaignService
from ...services.auth_service import AuthService

class CampaignView(QtWidgets.QWidget):
    """View for managing LinkedIn post campaigns."""
    
    def __init__(self, parent=None):
        """Initialize the campaign view."""
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
        title_label = QtWidgets.QLabel("Campaigns")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        # Spacer
        title_layout.addStretch()
        
        # Create Campaign button
        create_button = QtWidgets.QPushButton("Create New Campaign")
        create_button.clicked.connect(self.show_create_campaign_dialog)
        title_layout.addWidget(create_button)
        
        # Refresh button
        refresh_button = QtWidgets.QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        title_layout.addWidget(refresh_button)
        
        layout.addLayout(title_layout)
        
        # Campaigns table
        self.campaigns_table = QtWidgets.QTableWidget()
        self.campaigns_table.setColumnCount(7)
        self.campaigns_table.setHorizontalHeaderLabels([
            "ID", "Name", "Category", "Posts/Day", 
            "Duration", "Status", "Actions"
        ])
        
        # Set column stretching
        header = self.campaigns_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
        
        layout.addWidget(self.campaigns_table)
        
        # Campaign details section
        self.details_group = QtWidgets.QGroupBox("Campaign Details")
        self.details_group.setVisible(False)
        details_layout = QtWidgets.QVBoxLayout(self.details_group)
        
        # Campaign info
        info_layout = QtWidgets.QFormLayout()
        self.campaign_name_label = QtWidgets.QLabel()
        info_layout.addRow("Name:", self.campaign_name_label)
        
        self.campaign_category_label = QtWidgets.QLabel()
        info_layout.addRow("Category:", self.campaign_category_label)
        
        self.campaign_posts_label = QtWidgets.QLabel()
        info_layout.addRow("Posts per day:", self.campaign_posts_label)
        
        self.campaign_duration_label = QtWidgets.QLabel()
        info_layout.addRow("Duration:", self.campaign_duration_label)
        
        self.campaign_dates_label = QtWidgets.QLabel()
        info_layout.addRow("Date range:", self.campaign_dates_label)
        
        self.campaign_review_label = QtWidgets.QLabel()
        info_layout.addRow("Review required:", self.campaign_review_label)
        
        details_layout.addLayout(info_layout)
        
        # Campaign progress
        progress_layout = QtWidgets.QFormLayout()
        self.campaign_topics_label = QtWidgets.QLabel()
        progress_layout.addRow("Topics:", self.campaign_topics_label)
        
        self.campaign_content_label = QtWidgets.QLabel()
        progress_layout.addRow("Generated content:", self.campaign_content_label)
        
        self.campaign_scheduled_label = QtWidgets.QLabel()
        progress_layout.addRow("Scheduled posts:", self.campaign_scheduled_label)
        
        details_layout.addLayout(progress_layout)
        
        # Campaign actions
        actions_layout = QtWidgets.QHBoxLayout()
        
        self.generate_topics_button = QtWidgets.QPushButton("Generate Topics")
        self.generate_topics_button.clicked.connect(self.show_generate_topics_dialog)
        actions_layout.addWidget(self.generate_topics_button)
        
        self.view_topics_button = QtWidgets.QPushButton("View Topics")
        self.view_topics_button.clicked.connect(self.show_topics_dialog)
        actions_layout.addWidget(self.view_topics_button)
        
        self.generate_content_button = QtWidgets.QPushButton("Generate Content")
        self.generate_content_button.clicked.connect(self.show_generate_content_dialog)
        actions_layout.addWidget(self.generate_content_button)
        
        self.view_content_button = QtWidgets.QPushButton("View Content")
        self.view_content_button.clicked.connect(self.show_content_dialog)
        actions_layout.addWidget(self.view_content_button)
        
        self.schedule_button = QtWidgets.QPushButton("Schedule Posts")
        self.schedule_button.clicked.connect(self.schedule_campaign_posts)
        actions_layout.addWidget(self.schedule_button)
        
        details_layout.addLayout(actions_layout)
        
        # Delete campaign
        delete_layout = QtWidgets.QHBoxLayout()
        delete_layout.addStretch()
        
        self.delete_campaign_button = QtWidgets.QPushButton("Delete Campaign")
        self.delete_campaign_button.clicked.connect(self.delete_campaign)
        delete_layout.addWidget(self.delete_campaign_button)
        
        details_layout.addLayout(delete_layout)
        
        layout.addWidget(self.details_group)
    
    def refresh(self):
        """Refresh the campaigns data."""
        try:
            # Get campaigns
            campaigns = CampaignService.get_all_campaigns()
            
            # Update table
            self.campaigns_table.setRowCount(len(campaigns))
            
            for i, campaign in enumerate(campaigns):
                # ID
                id_item = QtWidgets.QTableWidgetItem(str(campaign['id']))
                id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.campaigns_table.setItem(i, 0, id_item)
                
                # Name
                name_item = QtWidgets.QTableWidgetItem(campaign['name'])
                name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.campaigns_table.setItem(i, 1, name_item)
                
                # Category
                category_item = QtWidgets.QTableWidgetItem(campaign['category'])
                category_item.setFlags(category_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.campaigns_table.setItem(i, 2, category_item)
                
                # Posts per day
                posts_item = QtWidgets.QTableWidgetItem(str(campaign['posts_per_day']))
                posts_item.setFlags(posts_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.campaigns_table.setItem(i, 3, posts_item)
                
                # Duration
                duration_item = QtWidgets.QTableWidgetItem(f"{campaign['duration_days']} days")
                duration_item.setFlags(duration_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.campaigns_table.setItem(i, 4, duration_item)
                
                # Status
                status_item = QtWidgets.QTableWidgetItem(campaign['status'].capitalize())
                status_item.setFlags(status_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.campaigns_table.setItem(i, 5, status_item)
                
                # Actions
                actions_widget = QtWidgets.QWidget()
                actions_layout = QtWidgets.QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                view_button = QtWidgets.QPushButton("View")
                view_button.setProperty("campaign_id", campaign['id'])
                view_button.clicked.connect(self.view_campaign_details)
                actions_layout.addWidget(view_button)
                
                self.campaigns_table.setCellWidget(i, 6, actions_widget)
            
        except Exception as e:
            print(f"Error refreshing campaigns: {str(e)}")
            if self.parent:
                self.parent.show_error("Refresh Error", f"Error refreshing campaigns: {str(e)}")
    
    def view_campaign_details(self):
        """View details for a campaign."""
        button = self.sender()
        if button:
            campaign_id = button.property("campaign_id")
            
            try:
                campaign = CampaignService.get_campaign(campaign_id)
                
                if campaign:
                    # Store campaign ID for actions
                    self.current_campaign_id = campaign_id
                    
                    # Update labels
                    self.campaign_name_label.setText(campaign['name'])
                    self.campaign_category_label.setText(campaign['category'])
                    self.campaign_posts_label.setText(str(campaign['posts_per_day']))
                    self.campaign_duration_label.setText(f"{campaign['duration_days']} days")
                    self.campaign_dates_label.setText(f"{campaign['start_date']} to {campaign['end_date']}")
                    self.campaign_review_label.setText("Yes" if campaign['requires_review'] else "No")
                    
                    # Progress
                    self.campaign_topics_label.setText(f"{campaign['topic_count']} ({campaign['unused_topic_count']} unused)")
                    
                    # Enable/disable buttons based on campaign state
                    self.view_topics_button.setEnabled(campaign['topic_count'] > 0)
                    self.generate_content_button.setEnabled(campaign['unused_topic_count'] > 0)
                    self.view_content_button.setEnabled(True)
                    self.schedule_button.setEnabled(True)
                    
                    # Show details
                    self.details_group.setVisible(True)
                else:
                    self.details_group.setVisible(False)
                    if self.parent:
                        self.parent.show_error("Campaign Error", "Campaign not found")
            except Exception as e:
                print(f"Error getting campaign details: {str(e)}")
                if self.parent:
                    self.parent.show_error("View Error", f"Error getting campaign details: {str(e)}")
    
    def show_create_campaign_dialog(self):
        """Show dialog for creating a new campaign."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Create New Campaign")
        dialog.setMinimumWidth(500)
        
        # Dialog layout
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Name field
        layout.addWidget(QtWidgets.QLabel("Campaign Name:"))
        name_edit = QtWidgets.QLineEdit()
        layout.addWidget(name_edit)
        
        # Category field
        layout.addWidget(QtWidgets.QLabel("Campaign Category:"))
        category_edit = QtWidgets.QLineEdit()
        category_edit.setText("Home Sales Consultations")
        layout.addWidget(category_edit)
        
        # Posts per day field
        layout.addWidget(QtWidgets.QLabel("Posts Per Day:"))
        posts_combo = QtWidgets.QComboBox()
        posts_combo.addItems(["1", "2", "3", "5"])
        layout.addWidget(posts_combo)
        
        # Duration field
        layout.addWidget(QtWidgets.QLabel("Campaign Duration (days):"))
        duration_spin = QtWidgets.QSpinBox()
        duration_spin.setMinimum(1)
        duration_spin.setMaximum(365)
        duration_spin.setValue(30)
        layout.addWidget(duration_spin)
        
        # Review checkbox
        review_check = QtWidgets.QCheckBox("Require review for all posts")
        layout.addWidget(review_check)
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Show dialog
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            name = name_edit.text()
            category = category_edit.text()
            posts_per_day = int(posts_combo.currentText())
            duration_days = duration_spin.value()
            requires_review = review_check.isChecked()
            
            if not name or not category:
                if self.parent:
                    self.parent.show_error("Validation Error", "Name and category are required")
                return
            
            try:
                campaign_id = CampaignService.create_campaign(
                    name=name,
                    category=category,
                    posts_per_day=posts_per_day,
                    duration_days=duration_days,
                    requires_review=requires_review
                )
                
                if self.parent:
                    self.parent.show_message("Success", f"Campaign '{name}' created with ID: {campaign_id}")
                
                self.refresh()
                
                # Show the campaign details
                for i in range(self.campaigns_table.rowCount()):
                    if self.campaigns_table.item(i, 0).text() == str(campaign_id):
                        view_button = self.campaigns_table.cellWidget(i, 6).findChild(QtWidgets.QPushButton)
                        if view_button:
                            view_button.click()
                            break
            except Exception as e:
                print(f"Error creating campaign: {str(e)}")
                if self.parent:
                    self.parent.show_error("Create Error", f"Error creating campaign: {str(e)}")
    
    def show_generate_topics_dialog(self):
        """Show dialog for generating campaign topics."""
        if not hasattr(self, 'current_campaign_id'):
            if self.parent:
                self.parent.show_error("Selection Error", "No campaign selected")
            return
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Generate Topics")
        dialog.setMinimumWidth(500)
        
        # Dialog layout
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # AI Provider field
        layout.addWidget(QtWidgets.QLabel("AI Provider:"))
        provider_combo = QtWidgets.QComboBox()
        provider_combo.addItems(["openai", "gemini", "claude"])
        layout.addWidget(provider_combo)
        
        # API Key field
        layout.addWidget(QtWidgets.QLabel("AI API Key:"))
        api_key_edit = QtWidgets.QLineEdit()
        api_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(api_key_edit)
        
        # Check if API key is already stored
        def update_stored_key():
            provider = provider_combo.currentText()
            key = AuthService.get_ai_provider_key(provider)
            if key:
                api_key_edit.setPlaceholderText("API key is already stored (leave empty to use stored key)")
            else:
                api_key_edit.setPlaceholderText("")
        
        update_stored_key()
        provider_combo.currentTextChanged.connect(update_stored_key)
        
        # Number of topics field
        layout.addWidget(QtWidgets.QLabel("Number of Topics:"))
        topics_spin = QtWidgets.QSpinBox()
        topics_spin.setMinimum(5)
        topics_spin.setMaximum(30)
        topics_spin.setValue(15)
        layout.addWidget(topics_spin)
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Show dialog
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            provider_name = provider_combo.currentText()
            api_key = api_key_edit.text()
            num_topics = topics_spin.value()
            
            # If API key provided, save it
            if api_key:
                AuthService.set_ai_provider_key(provider_name, api_key)
            else:
                # Check if we have a stored key
                api_key = AuthService.get_ai_provider_key(provider_name)
                if not api_key:
                    if self.parent:
                        self.parent.show_error("API Key Error", "No API key provided or stored")
                    return
            
            try:
                # Show progress dialog
                progress_dialog = QtWidgets.QProgressDialog("Generating topics...", "Cancel", 0, 0, self)
                progress_dialog.setWindowTitle("Generating Topics")
                progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
                progress_dialog.setMinimumDuration(0)
                progress_dialog.setValue(0)
                progress_dialog.setAutoClose(False)
                progress_dialog.setAutoReset(False)
                progress_dialog.show()
                
                # Process events to show dialog
                QtWidgets.QApplication.processEvents()
                
                # Generate topics
                count = CampaignService.generate_topics(
                    campaign_id=self.current_campaign_id,
                    num_topics=num_topics,
                    api_key=api_key,
                    provider_name=provider_name
                )
                
                # Close progress dialog
                progress_dialog.close()
                
                if self.parent:
                    self.parent.show_message("Success", f"Generated {count} topics")
                
                # Refresh campaign details
                self.view_campaign_details()
            except Exception as e:
                # Close progress dialog
                progress_dialog.close()
                
                print(f"Error generating topics: {str(e)}")
                if self.parent:
                    self.parent.show_error("Generate Error", f"Error generating topics: {str(e)}")
    
    def show_topics_dialog(self):
        """Show dialog for viewing and managing campaign topics."""
        if not hasattr(self, 'current_campaign_id'):
            if self.parent:
                self.parent.show_error("Selection Error", "No campaign selected")
            return
        
        try:
            topics = CampaignService.get_campaign_topics(self.current_campaign_id)
            
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Campaign Topics")
            dialog.setMinimumWidth(600)
            dialog.setMinimumHeight(400)
            
            # Dialog layout
            layout = QtWidgets.QVBoxLayout(dialog)
            
            # Topics table
            topics_table = QtWidgets.QTableWidget()
            topics_table.setColumnCount(4)
            topics_table.setHorizontalHeaderLabels(["ID", "Topic", "Status", "Actions"])
            
            # Set column stretching
            header = topics_table.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
            
            # Fill topics
            topics_table.setRowCount(len(topics))
            
            for i, topic in enumerate(topics):
                # ID
                id_item = QtWidgets.QTableWidgetItem(str(topic['id']))
                id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemIsEditable)
                topics_table.setItem(i, 0, id_item)
                
                # Topic
                topic_item = QtWidgets.QTableWidgetItem(topic['text'])
                topic_item.setFlags(topic_item.flags() & ~QtCore.Qt.ItemIsEditable)
                topics_table.setItem(i, 1, topic_item)
                
                # Status
                status_text = "Used" if topic['is_used'] else "Available"
                status_item = QtWidgets.QTableWidgetItem(status_text)
                status_item.setFlags(status_item.flags() & ~QtCore.Qt.ItemIsEditable)
                topics_table.setItem(i, 2, status_item)
                
                # Actions
                actions_widget = QtWidgets.QWidget()
                actions_layout = QtWidgets.QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                edit_button = QtWidgets.QPushButton("Edit")
                edit_button.setProperty("topic_id", topic['id'])
                edit_button.setProperty("topic_text", topic['text'])
                edit_button.clicked.connect(lambda checked, dialog=dialog: self.edit_topic(dialog))
                actions_layout.addWidget(edit_button)
                
                delete_button = QtWidgets.QPushButton("Delete")
                delete_button.setProperty("topic_id", topic['id'])
                delete_button.clicked.connect(lambda checked, dialog=dialog: self.delete_topic(dialog))
                actions_layout.addWidget(delete_button)
                
                topics_table.setCellWidget(i, 3, actions_widget)
            
            layout.addWidget(topics_table)
            
            # Buttons
            button_layout = QtWidgets.QHBoxLayout()
            
            delete_all_button = QtWidgets.QPushButton("Delete All Topics")
            delete_all_button.clicked.connect(lambda: self.delete_all_topics(dialog))
            button_layout.addWidget(delete_all_button)
            
            button_layout.addStretch()
            
            close_button = QtWidgets.QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            button_layout.addWidget(close_button)
            
            layout.addLayout(button_layout)
            
            # Show dialog
            dialog.exec_()
        except Exception as e:
            print(f"Error showing topics: {str(e)}")
            if self.parent:
                self.parent.show_error("Topics Error", f"Error showing topics: {str(e)}")
    
    def edit_topic(self, parent_dialog):
        """Edit a campaign topic."""
        button = self.sender()
        if button:
            topic_id = button.property("topic_id")
            topic_text = button.property("topic_text")
            
            dialog = QtWidgets.QDialog(parent_dialog)
            dialog.setWindowTitle("Edit Topic")
            dialog.setMinimumWidth(400)
            
            # Dialog layout
            layout = QtWidgets.QVBoxLayout(dialog)
            
            # Topic field
            layout.addWidget(QtWidgets.QLabel("Topic:"))
            topic_edit = QtWidgets.QLineEdit(topic_text)
            layout.addWidget(topic_edit)
            
            # Buttons
            buttons = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            # Show dialog
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                new_text = topic_edit.text()
                
                if not new_text:
                    if self.parent:
                        self.parent.show_error("Validation Error", "Topic cannot be empty")
                    return
                
                try:
                    success = CampaignService.update_topic(topic_id, new_text)
                    
                    if success:
                        # Update the topic in the table
                        for i in range(parent_dialog.findChild(QtWidgets.QTableWidget).rowCount()):
                            if parent_dialog.findChild(QtWidgets.QTableWidget).item(i, 0).text() == str(topic_id):
                                parent_dialog.findChild(QtWidgets.QTableWidget).item(i, 1).setText(new_text)
                                # Update the property for future edits
                                edit_button = parent_dialog.findChild(QtWidgets.QTableWidget).cellWidget(i, 3).findChild(QtWidgets.QPushButton, "", 
                                                                                                                       QtCore.Qt.FindChildrenRecursively)
                                if edit_button:
                                    edit_button.setProperty("topic_text", new_text)
                                break
                    else:
                        if self.parent:
                            self.parent.show_error("Update Error", f"Failed to update topic {topic_id}")
                except Exception as e:
                    print(f"Error updating topic: {str(e)}")
                    if self.parent:
                        self.parent.show_error("Update Error", f"Error updating topic: {str(e)}")
    
    def delete_topic(self, parent_dialog):
        """Delete a campaign topic."""
        button = self.sender()
        if button:
            topic_id = button.property("topic_id")
            
            # Confirm deletion
            confirm = QtWidgets.QMessageBox.question(
                parent_dialog,
                "Confirm Deletion",
                f"Are you sure you want to delete topic {topic_id}?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if confirm == QtWidgets.QMessageBox.Yes:
                try:
                    success = CampaignService.delete_topic(topic_id)
                    
                    if success:
                        # Remove the row from the table
                        table = parent_dialog.findChild(QtWidgets.QTableWidget)
                        for i in range(table.rowCount()):
                            if table.item(i, 0).text() == str(topic_id):
                                table.removeRow(i)
                                break
                        
                        # Refresh campaign details
                        self.view_campaign_details()
                    else:
                        if self.parent:
                            self.parent.show_error("Delete Error", f"Failed to delete topic {topic_id}")
                except Exception as e:
                    print(f"Error deleting topic: {str(e)}")
                    if self.parent:
                        self.parent.show_error("Delete Error", f"Error deleting topic: {str(e)}")
    
    def delete_all_topics(self, parent_dialog):
        """Delete all topics for a campaign."""
        if not hasattr(self, 'current_campaign_id'):
            if self.parent:
                self.parent.show_error("Selection Error", "No campaign selected")
            return
        
        # Confirm deletion
        confirm = QtWidgets.QMessageBox.question(
            parent_dialog,
            "Confirm Deletion",
            "Are you sure you want to delete ALL topics for this campaign?\nThis cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if confirm == QtWidgets.QMessageBox.Yes:
            try:
                count = CampaignService.delete_all_topics(self.current_campaign_id)
                
                if count > 0:
                    # Clear the table
                    table = parent_dialog.findChild(QtWidgets.QTableWidget)
                    table.setRowCount(0)
                    
                    # Refresh campaign details
                    self.view_campaign_details()
                    
                    # Close the dialog
                    parent_dialog.accept()
                    
                    if self.parent:
                        self.parent.show_message("Success", f"Deleted {count} topics")
                else:
                    if self.parent:
                        self.parent.show_message("Info", "No topics to delete")
            except Exception as e:
                print(f"Error deleting all topics: {str(e)}")
                if self.parent:
                    self.parent.show_error("Delete Error", f"Error deleting topics: {str(e)}")
    
    def show_generate_content_dialog(self):
        """Show dialog for generating content for campaign topics."""
        if not hasattr(self, 'current_campaign_id'):
            if self.parent:
                self.parent.show_error("Selection Error", "No campaign selected")
            return
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Generate Content")
        dialog.setMinimumWidth(500)
        
        # Dialog layout
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # AI Provider field
        layout.addWidget(QtWidgets.QLabel("AI Provider:"))
        provider_combo = QtWidgets.QComboBox()
        provider_combo.addItems(["openai", "gemini", "claude"])
        layout.addWidget(provider_combo)
        
        # API Key field
        layout.addWidget(QtWidgets.QLabel("AI API Key:"))
        api_key_edit = QtWidgets.QLineEdit()
        api_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(api_key_edit)
        
        # Check if API key is already stored
        def update_stored_key():
            provider = provider_combo.currentText()
            key = AuthService.get_ai_provider_key(provider)
            if key:
                api_key_edit.setPlaceholderText("API key is already stored (leave empty to use stored key)")
            else:
                api_key_edit.setPlaceholderText("")
        
        update_stored_key()
        provider_combo.currentTextChanged.connect(update_stored_key)
        
        # Information
        info_label = QtWidgets.QLabel("This will generate content for all unused topics in the campaign.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Show dialog
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            provider_name = provider_combo.currentText()
            api_key = api_key_edit.text()
            
            # If API key provided, save it
            if api_key:
                AuthService.set_ai_provider_key(provider_name, api_key)
            else:
                # Check if we have a stored key
                api_key = AuthService.get_ai_provider_key(provider_name)
                if not api_key:
                    if self.parent:
                        self.parent.show_error("API Key Error", "No API key provided or stored")
                    return
            
            try:
                # Show progress dialog
                progress_dialog = QtWidgets.QProgressDialog("Generating content...", "Cancel", 0, 0, self)
                progress_dialog.setWindowTitle("Generating Content")
                progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
                progress_dialog.setMinimumDuration(0)
                progress_dialog.setValue(0)
                progress_dialog.setAutoClose(False)
                progress_dialog.setAutoReset(False)
                progress_dialog.show()
                
                # Process events to show dialog
                QtWidgets.QApplication.processEvents()
                
                # Generate content
                count = CampaignService.generate_content(
                    campaign_id=self.current_campaign_id,
                    api_key=api_key,
                    provider_name=provider_name
                )
                
                # Close progress dialog
                progress_dialog.close()
                
                if self.parent:
                    self.parent.show_message("Success", f"Generated content for {count} topics")
                
                # Refresh campaign details
                self.view_campaign_details()
            except Exception as e:
                # Close progress dialog
                progress_dialog.close()
                
                print(f"Error generating content: {str(e)}")
                if self.parent:
                    self.parent.show_error("Generate Error", f"Error generating content: {str(e)}")
    
    def show_content_dialog(self):
        """Show dialog for viewing campaign content."""
        if not hasattr(self, 'current_campaign_id'):
            if self.parent:
                self.parent.show_error("Selection Error", "No campaign selected")
            return
        
        try:
            content = CampaignService.get_campaign_content(self.current_campaign_id)
            
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Campaign Content")
            dialog.setMinimumWidth(800)
            dialog.setMinimumHeight(600)
            
            # Dialog layout
            layout = QtWidgets.QVBoxLayout(dialog)
            
            # Content list
            content_list = QtWidgets.QListWidget()
            content_list.setWordWrap(True)
            
            for item in content:
                list_item = QtWidgets.QListWidgetItem(f"[{'Used' if item['is_used'] else 'Available'}] {item['topic']}")
                list_item.setData(QtCore.Qt.UserRole, item)
                content_list.addItem(list_item)
            
            layout.addWidget(content_list)
            
            # Content preview
            preview_group = QtWidgets.QGroupBox("Content Preview")
            preview_layout = QtWidgets.QVBoxLayout(preview_group)
            
            content_preview = QtWidgets.QTextEdit()
            content_preview.setReadOnly(True)
            preview_layout.addWidget(content_preview)
            
            layout.addWidget(preview_group)
            
            # Show content when item selected
            def show_content():
                selected_items = content_list.selectedItems()
                if selected_items:
                    item_data = selected_items[0].data(QtCore.Qt.UserRole)
                    content_preview.setText(item_data['text'])
            
            content_list.itemSelectionChanged.connect(show_content)
            
            # Buttons
            button_layout = QtWidgets.QHBoxLayout()
            
            button_layout.addStretch()
            
            close_button = QtWidgets.QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            button_layout.addWidget(close_button)
            
            layout.addLayout(button_layout)
            
            # Show dialog
            dialog.exec_()
        except Exception as e:
            print(f"Error showing content: {str(e)}")
            if self.parent:
                self.parent.show_error("Content Error", f"Error showing content: {str(e)}")
    
    def schedule_campaign_posts(self):
        """Schedule posts for a campaign."""
        if not hasattr(self, 'current_campaign_id'):
            if self.parent:
                self.parent.show_error("Selection Error", "No campaign selected")
            return
        
        # Confirm scheduling
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Confirm Scheduling",
            "Are you sure you want to schedule posts for this campaign?\n\nThis will:\n"
            "- Take content from your campaign repository\n"
            "- Automatically distribute posts according to campaign settings\n"
            "- Schedule posts during business hours on weekdays\n"
            "- Avoid scheduling posts in the past",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if confirm == QtWidgets.QMessageBox.Yes:
            try:
                # Show progress dialog
                progress_dialog = QtWidgets.QProgressDialog("Scheduling posts...", "Cancel", 0, 0, self)
                progress_dialog.setWindowTitle("Scheduling Posts")
                progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
                progress_dialog.setMinimumDuration(0)
                progress_dialog.setValue(0)
                progress_dialog.setAutoClose(False)
                progress_dialog.setAutoReset(False)
                progress_dialog.show()
                
                # Process events to show dialog
                QtWidgets.QApplication.processEvents()
                
                # Schedule posts
                count = CampaignService.schedule_campaign_posts(self.current_campaign_id)
                
                # Close progress dialog
                progress_dialog.close()
                
                if self.parent:
                    self.parent.show_message("Success", f"Scheduled {count} posts")
                
                # Refresh campaign details
                self.view_campaign_details()
            except Exception as e:
                # Close progress dialog
                progress_dialog.close()
                
                print(f"Error scheduling posts: {str(e)}")
                if self.parent:
                    self.parent.show_error("Schedule Error", f"Error scheduling posts: {str(e)}")
    
    def delete_campaign(self):
        """Delete a campaign and its related data."""
        if not hasattr(self, 'current_campaign_id'):
            if self.parent:
                self.parent.show_error("Selection Error", "No campaign selected")
            return
        
        # Confirm deletion
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Confirm Deletion",
            "WARNING: Are you sure you want to delete this campaign?\n\n"
            "This will permanently delete all topics, content, and settings associated with this campaign.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if confirm == QtWidgets.QMessageBox.Yes:
            try:
                success = CampaignService.delete_campaign(self.current_campaign_id)
                
                if success:
                    if self.parent:
                        self.parent.show_message("Success", "Campaign deleted successfully")
                    
                    # Hide details
                    self.details_group.setVisible(False)
                    
                    # Clear current campaign
                    if hasattr(self, 'current_campaign_id'):
                        delattr(self, 'current_campaign_id')
                    
                    # Refresh campaigns list
                    self.refresh()
                else:
                    if self.parent:
                        self.parent.show_error("Delete Error", "Failed to delete campaign")
            except Exception as e:
                print(f"Error deleting campaign: {str(e)}")
                if self.parent:
                    self.parent.show_error("Delete Error", f"Error deleting campaign: {str(e)}")