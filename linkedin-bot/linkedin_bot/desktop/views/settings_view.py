"""
Settings view for the LinkedIn Bot desktop application.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
import os
import webbrowser

from ...services.auth_service import AuthService

class SettingsView(QtWidgets.QWidget):
    """View for configuring application settings."""
    
    def __init__(self, parent=None):
        """Initialize the settings view."""
        super().__init__(parent)
        
        self.parent = parent
        self.init_ui()
        
        # Load settings
        self.load_settings()
    
    def init_ui(self):
        """Initialize the UI components."""
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title_label = QtWidgets.QLabel("Settings")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Create tab widget for different settings categories
        tab_widget = QtWidgets.QTabWidget()
        
        # LinkedIn API tab
        linkedin_tab = QtWidgets.QWidget()
        linkedin_layout = QtWidgets.QVBoxLayout(linkedin_tab)
        
        # LinkedIn API credentials section
        linkedin_group = QtWidgets.QGroupBox("LinkedIn API Credentials")
        linkedin_settings_layout = QtWidgets.QFormLayout(linkedin_group)
        
        # Client ID field
        self.client_id_edit = QtWidgets.QLineEdit()
        linkedin_settings_layout.addRow("Client ID:", self.client_id_edit)
        
        # Client Secret field
        self.client_secret_edit = QtWidgets.QLineEdit()
        self.client_secret_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        linkedin_settings_layout.addRow("Client Secret:", self.client_secret_edit)
        
        # Status label
        self.linkedin_status_label = QtWidgets.QLabel("Status: Not Configured")
        linkedin_settings_layout.addRow("", self.linkedin_status_label)
        
        # Save LinkedIn credentials button
        save_linkedin_button = QtWidgets.QPushButton("Save Credentials")
        save_linkedin_button.clicked.connect(self.save_linkedin_credentials)
        linkedin_settings_layout.addRow("", save_linkedin_button)
        
        linkedin_layout.addWidget(linkedin_group)
        
        # LinkedIn Authentication section
        linkedin_auth_group = QtWidgets.QGroupBox("LinkedIn Authentication")
        linkedin_auth_layout = QtWidgets.QVBoxLayout(linkedin_auth_group)
        
        # Authentication status
        self.auth_status_label = QtWidgets.QLabel("Status: Not Authenticated")
        linkedin_auth_layout.addWidget(self.auth_status_label)
        
        # Authentication button
        self.auth_button = QtWidgets.QPushButton("Authenticate with LinkedIn")
        self.auth_button.clicked.connect(self.authenticate_linkedin)
        linkedin_auth_layout.addWidget(self.auth_button)
        
        # OAuth code field
        oauth_layout = QtWidgets.QHBoxLayout()
        oauth_layout.addWidget(QtWidgets.QLabel("OAuth Code:"))
        self.oauth_code_edit = QtWidgets.QLineEdit()
        oauth_layout.addWidget(self.oauth_code_edit)
        
        # Submit code button
        self.submit_code_button = QtWidgets.QPushButton("Submit Code")
        self.submit_code_button.clicked.connect(self.submit_oauth_code)
        oauth_layout.addWidget(self.submit_code_button)
        
        linkedin_auth_layout.addLayout(oauth_layout)
        
        # Instructions
        instructions_label = QtWidgets.QLabel(
            "1. Click 'Authenticate with LinkedIn' to open the authorization page in your browser\n"
            "2. Log in to LinkedIn if necessary and authorize the app\n"
            "3. Copy the code from the redirect URL ('code' parameter)\n"
            "4. Paste the code above and click 'Submit Code'"
        )
        instructions_label.setWordWrap(True)
        linkedin_auth_layout.addWidget(instructions_label)
        
        linkedin_layout.addWidget(linkedin_auth_group)
        
        # Add spacer at the bottom
        linkedin_layout.addStretch()
        
        # AI Providers tab
        ai_tab = QtWidgets.QWidget()
        ai_layout = QtWidgets.QVBoxLayout(ai_tab)
        
        # OpenAI section
        openai_group = QtWidgets.QGroupBox("OpenAI")
        openai_layout = QtWidgets.QFormLayout(openai_group)
        
        # API Key field
        self.openai_key_edit = QtWidgets.QLineEdit()
        self.openai_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        openai_layout.addRow("API Key:", self.openai_key_edit)
        
        # Status label
        self.openai_status_label = QtWidgets.QLabel("Status: Not Configured")
        openai_layout.addRow("", self.openai_status_label)
        
        # Save button
        save_openai_button = QtWidgets.QPushButton("Save API Key")
        save_openai_button.clicked.connect(self.save_openai_key)
        openai_layout.addRow("", save_openai_button)
        
        ai_layout.addWidget(openai_group)
        
        # Gemini section
        gemini_group = QtWidgets.QGroupBox("Google Gemini")
        gemini_layout = QtWidgets.QFormLayout(gemini_group)
        
        # API Key field
        self.gemini_key_edit = QtWidgets.QLineEdit()
        self.gemini_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        gemini_layout.addRow("API Key:", self.gemini_key_edit)
        
        # Status label
        self.gemini_status_label = QtWidgets.QLabel("Status: Not Configured")
        gemini_layout.addRow("", self.gemini_status_label)
        
        # Save button
        save_gemini_button = QtWidgets.QPushButton("Save API Key")
        save_gemini_button.clicked.connect(self.save_gemini_key)
        gemini_layout.addRow("", save_gemini_button)
        
        ai_layout.addWidget(gemini_group)
        
        # Claude section
        claude_group = QtWidgets.QGroupBox("Anthropic Claude")
        claude_layout = QtWidgets.QFormLayout(claude_group)
        
        # API Key field
        self.claude_key_edit = QtWidgets.QLineEdit()
        self.claude_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        claude_layout.addRow("API Key:", self.claude_key_edit)
        
        # Status label
        self.claude_status_label = QtWidgets.QLabel("Status: Not Configured")
        claude_layout.addRow("", self.claude_status_label)
        
        # Save button
        save_claude_button = QtWidgets.QPushButton("Save API Key")
        save_claude_button.clicked.connect(self.save_claude_key)
        claude_layout.addRow("", save_claude_button)
        
        ai_layout.addWidget(claude_group)
        
        # Add spacer at the bottom
        ai_layout.addStretch()
        
        # Add tabs to tab widget
        tab_widget.addTab(linkedin_tab, "LinkedIn API")
        tab_widget.addTab(ai_tab, "AI Providers")
        
        layout.addWidget(tab_widget)
    
    def load_settings(self):
        """Load saved settings and update UI."""
        # Check LinkedIn configuration
        self.update_linkedin_status()
        
        # Check AI provider configuration
        self.update_ai_provider_status("openai", self.openai_status_label)
        self.update_ai_provider_status("gemini", self.gemini_status_label)
        self.update_ai_provider_status("claude", self.claude_status_label)
    
    def update_linkedin_status(self):
        """Update LinkedIn configuration and authentication status."""
        # Check if LinkedIn credentials are configured
        if AuthService.is_linkedin_configured():
            self.linkedin_status_label.setText("Status: Configured")
            
            # Check if LinkedIn is authenticated
            if AuthService.is_linkedin_authenticated():
                self.auth_status_label.setText("Status: Authenticated")
                self.auth_button.setEnabled(False)
                self.oauth_code_edit.setEnabled(False)
                self.submit_code_button.setEnabled(False)
            else:
                self.auth_status_label.setText("Status: Not Authenticated")
                self.auth_button.setEnabled(True)
                self.oauth_code_edit.setEnabled(True)
                self.submit_code_button.setEnabled(True)
        else:
            self.linkedin_status_label.setText("Status: Not Configured")
            self.auth_status_label.setText("Status: Not Authenticated")
            self.auth_button.setEnabled(False)
            self.oauth_code_edit.setEnabled(False)
            self.submit_code_button.setEnabled(False)
    
    def update_ai_provider_status(self, provider_name, status_label):
        """Update AI provider configuration status."""
        if AuthService.is_ai_provider_configured(provider_name):
            status_label.setText("Status: Configured")
        else:
            status_label.setText("Status: Not Configured")
    
    def save_linkedin_credentials(self):
        """Save LinkedIn API credentials."""
        client_id = self.client_id_edit.text()
        client_secret = self.client_secret_edit.text()
        
        if not client_id or not client_secret:
            if self.parent:
                self.parent.show_error("Validation Error", "Client ID and Client Secret are required")
            return
        
        try:
            AuthService.set_linkedin_credentials(client_id, client_secret)
            
            if self.parent:
                self.parent.show_message("Success", "LinkedIn API credentials saved")
            
            # Update status
            self.update_linkedin_status()
        except Exception as e:
            print(f"Error saving LinkedIn credentials: {str(e)}")
            if self.parent:
                self.parent.show_error("Save Error", f"Error saving LinkedIn credentials: {str(e)}")
    
    def authenticate_linkedin(self):
        """Start the LinkedIn authentication flow."""
        try:
            auth_url = AuthService.start_linkedin_auth_flow()
            
            # Open the browser
            webbrowser.open(auth_url)
            
            if self.parent:
                self.parent.show_message(
                    "Authentication Started",
                    "The LinkedIn authorization page has been opened in your browser.\n\n"
                    "After authorizing, you'll be redirected to a URL containing a 'code' parameter.\n"
                    "Copy this code and paste it in the OAuth Code field, then click 'Submit Code'."
                )
        except Exception as e:
            print(f"Error starting LinkedIn authentication: {str(e)}")
            if self.parent:
                self.parent.show_error("Authentication Error", f"Error starting LinkedIn authentication: {str(e)}")
    
    def submit_oauth_code(self):
        """Submit the OAuth code to complete authentication."""
        auth_code = self.oauth_code_edit.text()
        
        if not auth_code:
            if self.parent:
                self.parent.show_error("Validation Error", "OAuth Code is required")
            return
        
        try:
            access_token = AuthService.complete_linkedin_auth_flow(auth_code)
            
            if self.parent:
                self.parent.show_message(
                    "Authentication Complete",
                    "LinkedIn authentication completed successfully.\n\n"
                    "You are now authenticated with LinkedIn."
                )
            
            # Update status
            self.update_linkedin_status()
        except Exception as e:
            print(f"Error completing LinkedIn authentication: {str(e)}")
            if self.parent:
                self.parent.show_error("Authentication Error", f"Error completing LinkedIn authentication: {str(e)}")
    
    def save_openai_key(self):
        """Save OpenAI API key."""
        api_key = self.openai_key_edit.text()
        
        if not api_key:
            if self.parent:
                self.parent.show_error("Validation Error", "API Key is required")
            return
        
        try:
            AuthService.set_ai_provider_key("openai", api_key)
            
            if self.parent:
                self.parent.show_message("Success", "OpenAI API key saved")
            
            # Update status
            self.update_ai_provider_status("openai", self.openai_status_label)
        except Exception as e:
            print(f"Error saving OpenAI API key: {str(e)}")
            if self.parent:
                self.parent.show_error("Save Error", f"Error saving OpenAI API key: {str(e)}")
    
    def save_gemini_key(self):
        """Save Google Gemini API key."""
        api_key = self.gemini_key_edit.text()
        
        if not api_key:
            if self.parent:
                self.parent.show_error("Validation Error", "API Key is required")
            return
        
        try:
            AuthService.set_ai_provider_key("gemini", api_key)
            
            if self.parent:
                self.parent.show_message("Success", "Google Gemini API key saved")
            
            # Update status
            self.update_ai_provider_status("gemini", self.gemini_status_label)
        except Exception as e:
            print(f"Error saving Google Gemini API key: {str(e)}")
            if self.parent:
                self.parent.show_error("Save Error", f"Error saving Google Gemini API key: {str(e)}")
    
    def save_claude_key(self):
        """Save Anthropic Claude API key."""
        api_key = self.claude_key_edit.text()
        
        if not api_key:
            if self.parent:
                self.parent.show_error("Validation Error", "API Key is required")
            return
        
        try:
            AuthService.set_ai_provider_key("claude", api_key)
            
            if self.parent:
                self.parent.show_message("Success", "Anthropic Claude API key saved")
            
            # Update status
            self.update_ai_provider_status("claude", self.claude_status_label)
        except Exception as e:
            print(f"Error saving Anthropic Claude API key: {str(e)}")
            if self.parent:
                self.parent.show_error("Save Error", f"Error saving Anthropic Claude API key: {str(e)}")