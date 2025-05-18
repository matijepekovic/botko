"""
Scheduler module that handles post scheduling and execution.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import random

from .database import db
from .linkedin_api import linkedin_api

class Scheduler:
    """
    Handles scheduling and publishing of LinkedIn posts.
    """
    
    def __init__(self):
        """Initialize the scheduler."""
        self._stop_event = threading.Event()
        self._scheduler_thread = None
        self._check_interval = 60  # Check for posts every 60 seconds by default
    
    def add_post(self, post_text: str, schedule_time: str) -> int:
        """
        Add a post to the schedule.
        
        Args:
            post_text: The content of the LinkedIn post
            schedule_time: ISO format datetime string (e.g., '2025-05-18T14:30:00')
        
        Returns:
            The ID of the newly scheduled post
        """
        post_id = db.insert('scheduled_posts', {
            'post_text': post_text,
            'schedule_time': schedule_time
        })
        
        print(f"Post scheduled with ID {post_id} for {schedule_time}")
        return post_id
    
    def get_pending_posts(self) -> List[Dict[str, Any]]:
        """
        Get all posts that are due to be published.
        
        Returns:
            List of post dictionaries for pending posts
        """
        now = datetime.utcnow().isoformat()
        
        pending_posts = db.select(
            table='scheduled_posts',
            where="status = 'pending' AND schedule_time <= ? AND (reviewed = 1 OR needs_review = 0)",
            where_params=(now,)
        )
        
        return pending_posts
    
    def get_all_scheduled_posts(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled posts (pending and published).
        
        Returns:
            List of post dictionaries
        """
        posts = db.select(
            table='scheduled_posts',
            order_by='schedule_time'
        )
        
        return posts
    
    def mark_as_published(self, post_id: int) -> None:
        """
        Mark a post as published after successful posting.
        
        Args:
            post_id: ID of the post to mark
        """
        db.update(
            table='scheduled_posts',
            data={'status': 'published'},
            where='id = ?',
            where_params=(post_id,)
        )
        
        print(f"Post {post_id} marked as published")
    
    def mark_as_failed(self, post_id: int, error_message: Optional[str] = None) -> None:
        """
        Mark a post as failed if it couldn't be published.
        
        Args:
            post_id: ID of the post to mark
            error_message: Optional error message
        """
        # Get the current post text
        post = db.select(
            table='scheduled_posts',
            where='id = ?',
            where_params=(post_id,),
            limit=1
        )[0]
        
        updated_text = post['post_text'] + f" [ERROR: {error_message or 'Unknown error'}]"
        
        db.update(
            table='scheduled_posts',
            data={
                'status': 'failed',
                'post_text': updated_text
            },
            where='id = ?',
            where_params=(post_id,)
        )
        
        print(f"Post {post_id} marked as failed: {error_message}")
    
    def delete_post(self, post_id: int) -> None:
        """
        Delete a scheduled post.
        
        Args:
            post_id: ID of the post to delete
        """
        db.delete(
            table='scheduled_posts',
            where='id = ?',
            where_params=(post_id,)
        )
        
        print(f"Post {post_id} deleted")
    
    def check_and_publish(self) -> None:
        """Check for pending posts and publish them."""
        pending_posts = self.get_pending_posts()
        
        if not pending_posts:
            print("No pending posts to publish")
            return
        
        print(f"Found {len(pending_posts)} posts to publish")
        
        for post in pending_posts:
            post_id = post['id']
            post_text = post['post_text']
            
            print(f"Publishing post {post_id}: {post_text[:50]}...")
            
            try:
                success = linkedin_api.create_post(post_text)
                
                if success:
                    self.mark_as_published(post_id)
                else:
                    self.mark_as_failed(post_id, "API returned failure")
            except Exception as e:
                print(f"Error publishing post {post_id}: {str(e)}")
                self.mark_as_failed(post_id, str(e))
    
    def start_scheduler(self, check_interval: int = 60) -> None:
        """
        Start the scheduler thread to periodically check for posts to publish.
        
        Args:
            check_interval: Seconds between checks for posts to publish
        """
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            print("Scheduler is already running")
            return
        
        self._check_interval = check_interval
        self._stop_event.clear()
        
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self._scheduler_thread.daemon = True
        self._scheduler_thread.start()
        
        print(f"Scheduler started, checking for posts every {check_interval} seconds")
    
    def stop_scheduler(self) -> None:
        """Stop the scheduler thread."""
        if not self._scheduler_thread or not self._scheduler_thread.is_alive():
            print("Scheduler is not running")
            return
        
        print("Stopping scheduler...")
        self._stop_event.set()
        self._scheduler_thread.join(timeout=10)
        print("Scheduler stopped")
    
    def _scheduler_loop(self) -> None:
        """Main loop for the scheduler thread."""
        while not self._stop_event.is_set():
            try:
                self.check_and_publish()
            except Exception as e:
                print(f"Error in scheduler loop: {str(e)}")
            
            # Sleep until next check, but allow stopping during sleep
            self._stop_event.wait(self._check_interval)
    
    # === CONTENT REPOSITORY METHODS ===
    
    def add_content(self, post_text: str, category: Optional[str] = None) -> int:
        """
        Add content to the repository.
        
        Args:
            post_text: The content to add
            category: Optional category for grouping content
            
        Returns:
            The ID of the newly added content
        """
        content_id = db.insert('content_repository', {
            'post_text': post_text,
            'category': category
        })
        
        print(f"Content added to repository with ID {content_id}")
        return content_id
    
    def get_content_repository(self) -> List[Dict[str, Any]]:
        """
        Get all content from repository.
        
        Returns:
            List of content dictionaries
        """
        content = db.select(
            table='content_repository',
            order_by='id DESC'
        )
        
        return content
    
    def get_unused_content(self, category: Optional[str] = None, limit: int = 1) -> List[Dict[str, Any]]:
        """
        Get content that hasn't been used yet.
        
        Args:
            category: Optional category to filter by
            limit: Maximum number of items to retrieve
            
        Returns:
            List of content dictionaries for unused content
        """
        if category:
            content = db.select(
                table='content_repository',
                where='is_used = 0 AND category = ?',
                where_params=(category,),
                order_by='RANDOM()',
                limit=limit
            )
        else:
            content = db.select(
                table='content_repository',
                where='is_used = 0',
                order_by='RANDOM()',
                limit=limit
            )
        
        return content
    
    def mark_content_as_used(self, content_id: int) -> None:
        """
        Mark content as used after scheduling.
        
        Args:
            content_id: ID of the content to mark as used
        """
        db.update(
            table='content_repository',
            data={'is_used': 1},
            where='id = ?',
            where_params=(content_id,)
        )
        
        print(f"Content {content_id} marked as used")
    
    def reset_content_usage(self, content_id: Optional[int] = None) -> None:
        """
        Reset usage flag for content to allow reuse.
        
        Args:
            content_id: Optional specific content ID to reset, or None for all content
        """
        if content_id:
            db.update(
                table='content_repository',
                data={'is_used': 0},
                where='id = ?',
                where_params=(content_id,)
            )
            print(f"Content {content_id} reset for reuse")
        else:
            db.update(
                table='content_repository',
                data={'is_used': 0},
                where='1=1',
                where_params=()
            )
            print("All content reset for reuse")
    
    def auto_schedule_posts(self, num_posts: int = 7, days_ahead: int = 7, 
                           category: Optional[str] = None, time_range: Tuple[int, int] = (9, 17)) -> int:
        """
        Automatically schedule posts for the upcoming days.
        
        Args:
            num_posts: Number of posts to schedule
            days_ahead: Number of days to schedule posts for
            category: Optional category to filter content by
            time_range: Tuple of (start_hour, end_hour) in 24h format
            
        Returns:
            Count of scheduled posts
        """
        start_hour, end_hour = time_range
        
        # Generate posting times (one post per day at varied times)
        schedule_times = []
        for i in range(min(num_posts, days_ahead)):
            # Get a date i days from now
            post_date = datetime.now() + timedelta(days=i)
            
            # Set a random hour between start_hour and end_hour
            hour = random.randint(start_hour, end_hour)
            minute = random.randint(0, 59)
            
            post_time = post_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            schedule_times.append(post_time)
        
        # Get content from repository
        content_to_schedule = self.get_unused_content(category=category, limit=num_posts)
        
        scheduled_count = 0
        for i, content in enumerate(content_to_schedule):
            if i < len(schedule_times):
                content_id = content['id']
                post_text = content['post_text']
                
                # Schedule the post
                schedule_time = schedule_times[i].isoformat()
                post_id = self.add_post(post_text, schedule_time)
                
                # Mark content as used
                self.mark_content_as_used(content_id)
                scheduled_count += 1
        
        return scheduled_count

    def get_posts_for_review(self, days_ahead=1):
        """Get posts that need review and are scheduled within the specified days"""
        # Get posts scheduled in the next X days that need review
        now = datetime.utcnow()
        future = now + timedelta(days=days_ahead)
        
        posts = db.select(
            table='scheduled_posts',
            where="needs_review = 1 AND reviewed = 0 AND schedule_time BETWEEN ? AND ? AND status = 'pending'",
            where_params=(now.isoformat(), future.isoformat()),
            order_by='schedule_time'
        )
        
        return posts

# Create a global instance
scheduler = Scheduler()