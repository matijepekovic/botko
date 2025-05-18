"""
Post service that provides business logic for managing posts.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from ..core.database import db
from ..core.scheduler import scheduler

class PostService:
    """Service for managing posts."""
    
    @staticmethod
    def add_post(post_text: str, schedule_date: str, schedule_time: str) -> int:
        """
        Add a new post to be scheduled.
        
        Args:
            post_text: Content of the post
            schedule_date: Date in YYYY-MM-DD format
            schedule_time: Time in HH:MM format
            
        Returns:
            ID of the scheduled post
        """
        # Combine date and time into ISO format
        schedule_datetime = datetime.fromisoformat(f"{schedule_date} {schedule_time}")
        schedule_iso = schedule_datetime.isoformat()
        
        # Add post to scheduler
        post_id = scheduler.add_post(post_text, schedule_iso)
        return post_id
    
    @staticmethod
    def get_all_posts() -> List[Dict[str, Any]]:
        """
        Get all scheduled posts.
        
        Returns:
            List of post dictionaries
        """
        posts = scheduler.get_all_scheduled_posts()
        
        # Format the posts for display
        formatted_posts = []
        for post in posts:
            # Convert ISO time to a more readable format
            try:
                schedule_datetime = datetime.fromisoformat(post['schedule_time'])
                formatted_time = schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = post['schedule_time']
                
            formatted_posts.append({
                'id': post['id'],
                'text': post['post_text'],
                'scheduled_time': formatted_time,
                'status': post['status'],
                'created_at': post['created_at'],
                'needs_review': bool(post.get('needs_review', 0)),
                'reviewed': bool(post.get('reviewed', 0))
            })
        
        return formatted_posts
    
    @staticmethod
    def get_post(post_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific post.
        
        Args:
            post_id: ID of the post to retrieve
            
        Returns:
            Post dictionary or None if not found
        """
        posts = db.select(
            table='scheduled_posts',
            where='id = ?',
            where_params=(post_id,),
            limit=1
        )
        
        if not posts:
            return None
        
        post = posts[0]
        
        # Format the post for display
        try:
            schedule_datetime = datetime.fromisoformat(post['schedule_time'])
            formatted_time = schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_time = post['schedule_time']
            
        return {
            'id': post['id'],
            'text': post['post_text'],
            'scheduled_time': formatted_time,
            'status': post['status'],
            'created_at': post['created_at'],
            'needs_review': bool(post.get('needs_review', 0)),
            'reviewed': bool(post.get('reviewed', 0))
        }
    
    @staticmethod
    def update_post(post_id: int, post_text: str) -> bool:
        """
        Update a post's content.
        
        Args:
            post_id: ID of the post to update
            post_text: New content for the post
            
        Returns:
            Boolean indicating success
        """
        rowcount = db.update(
            table='scheduled_posts',
            data={
                'post_text': post_text,
                'reviewed': 1
            },
            where='id = ?',
            where_params=(post_id,)
        )
        
        return rowcount > 0
    
    @staticmethod
    def delete_post(post_id: int) -> bool:
        """
        Delete a post.
        
        Args:
            post_id: ID of the post to delete
            
        Returns:
            Boolean indicating success
        """
        scheduler.delete_post(post_id)
        return True
    
    @staticmethod
    def approve_post(post_id: int) -> bool:
        """
        Approve a post for publishing.
        
        Args:
            post_id: ID of the post to approve
            
        Returns:
            Boolean indicating success
        """
        rowcount = db.update(
            table='scheduled_posts',
            data={'reviewed': 1},
            where='id = ?',
            where_params=(post_id,)
        )
        
        return rowcount > 0
    
    @staticmethod
    def get_posts_for_review() -> List[Dict[str, Any]]:
        """
        Get posts that need review.
        
        Returns:
            List of post dictionaries
        """
        posts = scheduler.get_posts_for_review(days_ahead=7)
        
        # Format the posts for display
        formatted_posts = []
        for post in posts:
            try:
                schedule_datetime = datetime.fromisoformat(post['schedule_time'])
                formatted_time = schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = post['schedule_time']
                
            formatted_posts.append({
                'id': post['id'],
                'text': post['post_text'],
                'scheduled_time': formatted_time,
                'status': post['status'],
                'created_at': post['created_at']
            })
        
        return formatted_posts
    
    @staticmethod
    def auto_schedule(num_posts: int, days_ahead: int, category: Optional[str] = None, 
                      start_hour: int = 9, end_hour: int = 17) -> int:
        """
        Automatically schedule posts for future days.
        
        Args:
            num_posts: Number of posts to schedule
            days_ahead: Number of days to schedule posts for
            category: Optional category to filter content by
            start_hour: Start of posting window (24-hour format)
            end_hour: End of posting window (24-hour format)
            
        Returns:
            Number of posts scheduled
        """
        count = scheduler.auto_schedule_posts(
            num_posts=num_posts,
            days_ahead=days_ahead,
            category=category,
            time_range=(start_hour, end_hour)
        )
        
        return count