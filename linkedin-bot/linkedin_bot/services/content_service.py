"""
Content service that manages the content repository.
"""

import os
import csv
from typing import List, Dict, Any, Optional, Tuple
import tempfile

from ..core.database import db
from ..core.scheduler import scheduler

class ContentService:
    """Service for managing the content repository."""
    
    @staticmethod
    def add_content(post_text: str, category: Optional[str] = None) -> int:
        """
        Add content to the repository.
        
        Args:
            post_text: The content to add
            category: Optional category for grouping content
            
        Returns:
            ID of the new content
        """
        return scheduler.add_content(post_text, category)
    
    @staticmethod
    def get_all_content() -> List[Dict[str, Any]]:
        """
        Get all content from the repository.
        
        Returns:
            List of content dictionaries
        """
        content = scheduler.get_content_repository()
        
        # Format content for display
        formatted_content = []
        for item in content:
            formatted_content.append({
                'id': item['id'],
                'text': item['post_text'],
                'category': item['category'] or "None",
                'is_used': bool(item['is_used']),
                'created_at': item['created_at']
            })
        
        return formatted_content
    
    @staticmethod
    def get_content(content_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific content item.
        
        Args:
            content_id: ID of the content to retrieve
            
        Returns:
            Content dictionary or None if not found
        """
        items = db.select(
            table='content_repository',
            where='id = ?',
            where_params=(content_id,),
            limit=1
        )
        
        if not items:
            return None
        
        item = items[0]
        
        return {
            'id': item['id'],
            'text': item['post_text'],
            'category': item['category'],
            'is_used': bool(item['is_used']),
            'created_at': item['created_at']
        }
    
    @staticmethod
    def reset_content(content_id: Optional[int] = None) -> bool:
        """
        Reset content usage status.
        
        Args:
            content_id: Optional ID of specific content to reset, or None for all
            
        Returns:
            Boolean indicating success
        """
        scheduler.reset_content_usage(content_id)
        return True
    
    @staticmethod
    def import_from_csv(file_path: str) -> int:
        """
        Import content from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Number of imported items
        """
        count = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            header = next(csv_reader, None)  # Skip header row if it exists
            
            for row in csv_reader:
                if len(row) >= 1:
                    post_text = row[0]
                    category = row[1] if len(row) >= 2 else None
                    
                    ContentService.add_content(post_text, category)
                    count += 1
        
        return count
    
    @staticmethod
    def export_to_csv(file_path: str) -> int:
        """
        Export content repository to a CSV file.
        
        Args:
            file_path: Path to save the CSV file
            
        Returns:
            Number of exported items
        """
        content = ContentService.get_all_content()
        
        with open(file_path, 'w', encoding='utf-8', newline='') as file:
            csv_writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
            
            # Write header row
            csv_writer.writerow(['PostContent', 'Category', 'IsUsed', 'CreatedAt'])
            
            # Write content rows
            for item in content:
                csv_writer.writerow([
                    item['text'],
                    item['category'],
                    '1' if item['is_used'] else '0',
                    item['created_at']
                ])
        
        return len(content)
    
    @staticmethod
    def import_from_uploaded_file(file_data: bytes) -> int:
        """
        Import content from uploaded file data.
        
        Args:
            file_data: Raw file data
            
        Returns:
            Number of imported items
        """
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_data)
        
        try:
            # Import from the temporary file
            count = ContentService.import_from_csv(temp_path)
            return count
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @staticmethod
    def get_categories() -> List[str]:
        """
        Get all unique categories from the content repository.
        
        Returns:
            List of category strings
        """
        result = db.execute(
            "SELECT DISTINCT category FROM content_repository WHERE category IS NOT NULL"
        )
        
        categories = [row['category'] for row in result.fetchall()]
        return categories