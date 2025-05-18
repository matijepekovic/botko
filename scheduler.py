import sqlite3
import time
from datetime import datetime, timedelta
import post
import random
import os

class LinkedInScheduler:
    def __init__(self, db_path="linkedin_posts.db"):
        """Initialize the scheduler with the database path"""
        self.db_path = db_path
        self.init_db()
        
    def init_db(self):
        """Create the database and tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # scheduled_posts table with all needed columns
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_text TEXT NOT NULL,
            schedule_time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            needs_review INTEGER DEFAULT 0,
            reviewed INTEGER DEFAULT 0
        )
        ''')
        
        # content_repository table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_repository (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_text TEXT NOT NULL,
            category TEXT,
            is_used INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # campaigns table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            posts_per_day INTEGER NOT NULL,
            duration_days INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            requires_review INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # campaign_topics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            is_used INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        )
        ''')
        
        # Check and add columns to existing tables if needed
        
        # Check scheduled_posts table
        cursor.execute("PRAGMA table_info(scheduled_posts)")
        columns = {column[1] for column in cursor.fetchall()}
        
        # Add missing columns to scheduled_posts
        required_columns = {
            'needs_review': 'INTEGER DEFAULT 0',
            'reviewed': 'INTEGER DEFAULT 0'
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE scheduled_posts ADD COLUMN {col_name} {col_type}')
                    print(f"Added {col_name} column to scheduled_posts table")
                except sqlite3.OperationalError as e:
                    print(f"Error adding column {col_name}: {str(e)}")
        
        conn.commit()
        conn.close()
        print(f"Database initialized at {self.db_path}")
    
    def get_campaign_topics(self, campaign_id):
        """Get all topics for a specific campaign"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, topic, is_used, created_at 
            FROM campaign_topics 
            WHERE campaign_id = ?
            ORDER BY is_used, id
            """, 
            (campaign_id,)
        )
        topics = cursor.fetchall()
        conn.close()
        return topics

    def update_campaign_topic(self, topic_id, new_topic):
        """Update a campaign topic"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE campaign_topics SET topic = ? WHERE id = ?", 
            (new_topic, topic_id)
        )
        conn.commit()
        conn.close()
        print(f"Topic {topic_id} updated to: {new_topic}")
        return True

    def delete_campaign_topic(self, topic_id):
        """Delete a campaign topic"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM campaign_topics WHERE id = ?", (topic_id,))
        conn.commit()
        conn.close()
        print(f"Topic {topic_id} deleted")
        return True
    
    def delete_all_campaign_topics(self, campaign_id):
        """Delete all topics for a specific campaign"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get count of topics before deletion
            cursor.execute("SELECT COUNT(*) FROM campaign_topics WHERE campaign_id = ?", (campaign_id,))
            topic_count = cursor.fetchone()[0]
            
            # Delete all topics
            cursor.execute("DELETE FROM campaign_topics WHERE campaign_id = ?", (campaign_id,))
            conn.commit()
            
            print(f"Deleted all {topic_count} topics for campaign {campaign_id}")
            return topic_count
        except Exception as e:
            print(f"Error deleting topics for campaign {campaign_id}: {str(e)}")
            raise
        finally:
            conn.close()
    
    def delete_campaign(self, campaign_id):
        """Delete a campaign and its related data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Start a transaction
            conn.execute("BEGIN TRANSACTION")
            
            # First, get all topics for this campaign
            cursor.execute("SELECT id FROM campaign_topics WHERE campaign_id = ?", (campaign_id,))
            topic_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete the topics
            if topic_ids:
                cursor.execute("DELETE FROM campaign_topics WHERE campaign_id = ?", (campaign_id,))
                print(f"Deleted {len(topic_ids)} topics for campaign {campaign_id}")
            
            # Delete any content in the repository associated with this campaign
            cursor.execute("DELETE FROM content_repository WHERE category LIKE ?", (f"Campaign: {campaign_id}%",))
            content_count = cursor.rowcount
            
            # Finally, delete the campaign itself
            cursor.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
            
            # Commit the transaction
            conn.commit()
            print(f"Campaign {campaign_id} deleted successfully")
            return True
        except Exception as e:
            # Rollback in case of error
            conn.rollback()
            print(f"Error deleting campaign {campaign_id}: {str(e)}")
            raise
        finally:
            conn.close()
    
    def add_post(self, post_text, schedule_time):
        """
        Add a post to the schedule
        
        Args:
            post_text: The content of the LinkedIn post
            schedule_time: ISO format datetime string (e.g., '2025-05-18T14:30:00')
        
        Returns:
            The ID of the newly scheduled post
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scheduled_posts (post_text, schedule_time) VALUES (?, ?)",
            (post_text, schedule_time)
        )
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"Post scheduled with ID {post_id} for {schedule_time}")
        return post_id
    
    def get_pending_posts(self):
        """
        Get all posts that are due to be published
        
        Returns:
            List of tuples containing (post_id, post_text) for pending posts
        """
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, post_text FROM scheduled_posts WHERE status = 'pending' AND schedule_time <= ?",
            (now,)
        )
        posts = cursor.fetchall()
        conn.close()
        return posts
    
    def get_all_scheduled_posts(self):
        """
        Get all scheduled posts (pending and published)
        
        Returns:
            List of tuples containing post details
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, post_text, schedule_time, status, created_at FROM scheduled_posts ORDER BY schedule_time"
        )
        posts = cursor.fetchall()
        conn.close()
        return posts
    
    def mark_as_published(self, post_id):
        """Mark a post as published after successful posting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE scheduled_posts SET status = 'published' WHERE id = ?",
            (post_id,)
        )
        conn.commit()
        conn.close()
        print(f"Post {post_id} marked as published")
    
    def mark_as_failed(self, post_id, error_message=None):
        """Mark a post as failed if it couldn't be published"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE scheduled_posts SET status = 'failed', post_text = post_text || ' [ERROR: ' || ? || ']' WHERE id = ?",
            (error_message or "Unknown error", post_id)
        )
        conn.commit()
        conn.close()
        print(f"Post {post_id} marked as failed: {error_message}")
    
    def delete_post(self, post_id):
        """Delete a scheduled post"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scheduled_posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()
        print(f"Post {post_id} deleted")
    
    def check_and_publish(self):
        """Check for pending posts and publish them"""
        pending_posts = self.get_pending_posts()
        if not pending_posts:
            print("No pending posts to publish")
            return
        
        print(f"Found {len(pending_posts)} posts to publish")
        
        for post_id, post_text in pending_posts:
            print(f"Publishing post {post_id}: {post_text[:50]}...")
            try:
                success = post.create_linkedin_post(post_text)
                if success:
                    self.mark_as_published(post_id)
                else:
                    self.mark_as_failed(post_id, "API returned failure")
            except Exception as e:
                print(f"Error publishing post {post_id}: {str(e)}")
                self.mark_as_failed(post_id, str(e))
    
    # === BULK CONTENT REPOSITORY METHODS ===
    
    def add_bulk_content(self, post_text, category=None):
        """
        Add content to the repository
        
        Args:
            post_text: The content to add
            category: Optional category for grouping content
            
        Returns:
            The ID of the newly added content
        """
        max_retries = 5
        retries = 0
        
        while retries < max_retries:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO content_repository (post_text, category) VALUES (?, ?)",
                    (post_text, category)
                )
                content_id = cursor.lastrowid
                conn.commit()
                conn.close()
                print(f"Content added to repository with ID {content_id}")
                return content_id
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    conn.close()
                    retries += 1
                    if retries >= max_retries:
                        raise Exception(f"Failed to add content after {max_retries} attempts: {str(e)}")
                    # Exponential backoff
                    wait_time = 0.1 * (2 ** retries)
                    time.sleep(wait_time)
                else:
                    # If it's a different error, re-raise it
                    conn.close()
                    raise
    
    def get_content_repository(self):
        """
        Get all content from repository
        
        Returns:
            List of tuples containing content details
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, post_text, category, is_used, created_at FROM content_repository ORDER BY id DESC"
        )
        content = cursor.fetchall()
        conn.close()
        return content
    
    def import_from_csv(self, csv_file):
        """
        Import bulk content from a CSV file
        
        Args:
            csv_file: Path to CSV file with format: PostContent,Category
            
        Returns:
            Count of imported posts
        """
        import csv
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        count = 0
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            header = next(csv_reader, None)  # Skip header row if it exists
            
            for row in csv_reader:
                if len(row) >= 1:
                    post_text = row[0]
                    category = row[1] if len(row) >= 2 else None
                    
                    cursor.execute(
                        "INSERT INTO content_repository (post_text, category) VALUES (?, ?)",
                        (post_text, category)
                    )
                    count += 1
        
        conn.commit()
        conn.close()
        print(f"Imported {count} posts from {csv_file}")
        return count
    
    def get_unused_content(self, category=None, limit=1):
        """
        Get content that hasn't been used yet
        
        Args:
            category: Optional category to filter by
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of tuples containing (content_id, post_text) for unused content
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute(
                "SELECT id, post_text FROM content_repository WHERE is_used = 0 AND category = ? ORDER BY RANDOM() LIMIT ?",
                (category, limit)
            )
        else:
            cursor.execute(
                "SELECT id, post_text FROM content_repository WHERE is_used = 0 ORDER BY RANDOM() LIMIT ?",
                (limit,)
            )
        
        content = cursor.fetchall()
        conn.close()
        return content
    
    def mark_content_as_used(self, content_id):
        """
        Mark content as used after scheduling
        
        Args:
            content_id: ID of the content to mark as used
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE content_repository SET is_used = 1 WHERE id = ?",
            (content_id,)
        )
        conn.commit()
        conn.close()
        print(f"Content {content_id} marked as used")
    
    def reset_content_usage(self, content_id=None):
        """
        Reset usage flag for content to allow reuse
        
        Args:
            content_id: Optional specific content ID to reset, or None for all content
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if content_id:
            cursor.execute("UPDATE content_repository SET is_used = 0 WHERE id = ?", (content_id,))
            print(f"Content {content_id} reset for reuse")
        else:
            cursor.execute("UPDATE content_repository SET is_used = 0")
            print("All content reset for reuse")
            
        conn.commit()
        conn.close()
    
    def auto_schedule_posts(self, num_posts=7, days_ahead=7, category=None, time_range=None):
        """
        Automatically schedule posts for the upcoming days
        
        Args:
            num_posts: Number of posts to schedule
            days_ahead: Number of days to schedule posts for
            category: Optional category to filter content by
            time_range: Optional tuple of (start_hour, end_hour) in 24h format
            
        Returns:
            Count of scheduled posts
        """
        if time_range is None:
            # Default to business hours
            time_range = (9, 17)  # 9 AM to 5 PM
        
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
        for i, (content_id, post_text) in enumerate(content_to_schedule):
            if i < len(schedule_times):
                # Schedule the post
                schedule_time = schedule_times[i].isoformat()
                post_id = self.add_post(post_text, schedule_time)
                
                # Mark content as used
                self.mark_content_as_used(content_id)
                scheduled_count += 1
        
        return scheduled_count

    def create_campaign(self, name, category, posts_per_day, duration_days, requires_review=False):
        """Create a new posting campaign"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate start and end dates
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_days)
        
        # Insert the campaign
        cursor.execute(
            """
            INSERT INTO campaigns 
            (name, category, posts_per_day, duration_days, start_date, end_date, requires_review) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, category, posts_per_day, duration_days, 
             start_date.isoformat(), end_date.isoformat(), 
             1 if requires_review else 0)
        )
        
        campaign_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"Campaign '{name}' created with ID {campaign_id}")
        return campaign_id    

    def generate_topics(self, campaign_id, num_topics=15, api_key=None, provider_name="openai"):
        """Generate topics for a campaign using the selected AI provider"""
        import ai_providers
        
        if not api_key:
            raise ValueError("API key is required for topic generation")
        
        # Get the appropriate AI provider
        provider = ai_providers.get_provider(provider_name, api_key)
        
        # Get campaign details
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT category FROM campaigns WHERE id = ?", (campaign_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise ValueError(f"Campaign with ID {campaign_id} not found")
        
        category = result[0]
        
        # Create the prompt for topic generation
        prompt = f"""
        Generate {num_topics} current and relevant sales topics that reflect what people in the field are dealing with right now.
        STICK TO SALES: TECHIQUES, METHODS, TIPS, TRICKS, PSYCHOLOGY IN SALES.
        The category: {category}.
        
        They should be practical, not academic. Avoid corporate buzzwords or fluff. Focus on real conversations, problems, and patterns that sales reps, consultants, and closers are facing in current year.
        Topics should be written in plain English, like how someone would say it out loud. Keep them short and direct.
        
        Format your response as a simple list with one topic per line, without numbering or bullet points.
        Each topic should be brief (3-8 words) but specific enough to generate a full LinkedIn post.
        """
        
        try:
            # Generate content using the selected provider
            content = provider.generate_content(prompt, max_tokens=500, temperature=0.8)
            
            # Extract and process the generated topics
            topics = [line.strip() for line in content.split('\n') if line.strip()]
            
            # Store the topics in the database
            for topic in topics:
                cursor.execute(
                    "INSERT INTO campaign_topics (campaign_id, topic) VALUES (?, ?)",
                    (campaign_id, topic)
                )
            
            conn.commit()
            conn.close()
            
            print(f"Generated {len(topics)} topics for campaign {campaign_id}")
            return len(topics)
            
        except Exception as e:
            conn.close()
            print(f"Error generating topics: {str(e)}")
            raise

    def schedule_campaign_posts(self, campaign_id):
        """Schedule generated content according to campaign settings"""
        # Get campaign details
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name, posts_per_day, start_date, end_date, requires_review
            FROM campaigns WHERE id = ?
            """, 
            (campaign_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise ValueError(f"Campaign with ID {campaign_id} not found")
        
        name, posts_per_day, start_date_str, end_date_str, requires_review = result
        
        # Get unscheduled content for this campaign
        cursor.execute(
            """
            SELECT id, post_text FROM content_repository 
            WHERE category LIKE ? AND is_used = 0
            """,
            (f"Campaign: {campaign_id}%",)
        )
        content = cursor.fetchall()
        
        if not content:
            conn.close()
            raise ValueError(f"No unscheduled content found for campaign {campaign_id}")
        
        # Parse dates
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)
        
        # Calculate posting schedule
        days_in_campaign = (end_date - start_date).days
        total_posts = min(len(content), days_in_campaign * posts_per_day)
        
        # Create posting time slots
        time_slots = []
        current_date = start_date
        
        # Business hours distribution
        posting_hours = [9, 11, 13, 15, 17]  # 9am, 11am, 1pm, 3pm, 5pm
        
        while current_date <= end_date and len(time_slots) < total_posts:
            # Skip weekends if desired
            if current_date.weekday() < 5:  # 0-4 are Monday to Friday
                # Add time slots for today
                for _ in range(posts_per_day):
                    if len(time_slots) >= total_posts:
                        break
                        
                    # Pick a random hour from business hours
                    hour = random.choice(posting_hours)
                    minute = random.randint(0, 59)
                    
                    post_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # Don't schedule in the past
                    if post_time > datetime.utcnow():
                        time_slots.append(post_time)
            
            current_date += timedelta(days=1)
        
        # Schedule posts
        scheduled_count = 0
        for i, post_time in enumerate(time_slots):
            if i < len(content):
                content_id, post_text = content[i]
                
                # Schedule the post
                post_id = self.add_post(post_text, post_time.isoformat())
                
                # Mark content as used
                cursor.execute(
                    "UPDATE content_repository SET is_used = 1 WHERE id = ?",
                    (content_id,)
                )
                
                # If review is required, mark post for review
                if requires_review:
                    cursor.execute(
                        "UPDATE scheduled_posts SET needs_review = 1 WHERE id = ?",
                        (post_id,)
                    )
                
                scheduled_count += 1
        
        conn.commit()
        conn.close()
        return scheduled_count  

    def get_posts_for_review(self, days_ahead=1):
        """Get posts that need review and are scheduled within the specified days"""
        # Get posts scheduled in the next X days that need review
        now = datetime.utcnow()
        future = now + timedelta(days=days_ahead)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                SELECT id, post_text, schedule_time, status, created_at 
                FROM scheduled_posts 
                WHERE needs_review = 1 
                AND reviewed = 0
                AND schedule_time BETWEEN ? AND ? 
                AND status = 'pending'
                ORDER BY schedule_time
                """,
                (now.isoformat(), future.isoformat())
            )
            posts = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Error in get_posts_for_review: {str(e)}")
            # Return empty list if there's an error (e.g., columns don't exist yet)
            posts = []
        finally:
            conn.close()
        
        return posts

    def send_review_notifications(self):
        """Send notifications for posts that need review tomorrow"""
        posts = self.get_posts_for_review(days_ahead=1)
        
        if posts:
            print("===== POSTS REQUIRING REVIEW =====")
            print(f"Found {len(posts)} posts scheduled for tomorrow that need review:")
            for post_id, text, schedule_time, status, created_at in posts:
                try:
                    schedule_datetime = datetime.fromisoformat(schedule_time)
                    formatted_time = schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_time = schedule_time
                    
                print(f"Post ID: {post_id} | Scheduled for: {formatted_time}")
                print(f"Text preview: {text[:100]}..." if len(text) > 100 else f"Text: {text}")
                print("-" * 50)
            
            print("===== END OF NOTIFICATIONS =====")
            
            # In a real implementation, you could send emails or other notifications here
            # For example:
            # self.send_email_notification(posts)
            
            return len(posts)
        else:
            print("No posts require review for tomorrow.")
            return 0

    def generate_content_for_campaign(self, campaign_id, api_key=None, provider_name="openai"):
        """Generate content for all unused campaign topics using the selected AI provider"""
        import ai_providers
        import time
        
        if not api_key:
            raise ValueError("API key is required for content generation")
        
        # Get the appropriate AI provider
        provider = ai_providers.get_provider(provider_name, api_key)
        
        # Get all unused topics for this campaign
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, topic FROM campaign_topics WHERE campaign_id = ? AND is_used = 0",
            (campaign_id,)
        )
        topics = cursor.fetchall()
        conn.close()  # Close connection immediately to avoid locking
        
        if not topics:
            raise ValueError(f"No unused topics found for campaign {campaign_id}")
        
        # Get campaign category - use a separate connection
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT category FROM campaigns WHERE id = ?", (campaign_id,))
        category = cursor.fetchone()[0]
        conn.close()  # Close connection immediately
        
        generated_count = 0
        for topic_id, topic in topics:
            # Determine post complexity based on topic length and complexity
            complexity = "simple" if len(topic.split()) < 4 else "detailed"
            
            # Create the prompt for content generation with your custom writing style
            prompt = f"""
Write a professional LinkedIn post about "{topic}" for a sales consultant.

The post should be {complexity} and provide practical sales advice related to {category}.

IMPORTANT RULES - READ CAREFULLY:
- NO STORYTELLING - Do not write in narrative form
- NO PERSONAL EXPERIENCES - Do not use phrases like "I did" or "my client" 
- NO MADE-UP STATISTICS OR DATA - Do not mention specific percentages or numbers unless citing sources
- NO CLIENT STORIES OR ANECDOTES - Do not reference specific client situations
- NO ASSUMPTIONS about the writer's background, experience, or company
- JUST GIVE ADVICE - Focus solely on practical tips, methods, and actionable guidance
- CITATION NEEDED - If quoting someone or referencing research, include the source

FORMAT REQUIREMENTS:
- ABSOLUTELY NO FIRST PERSON - Do not use "I", "me", "my", "we", or "our" anywhere
- ABSOLUTELY NO STATISTICS - Do not mention any specific numbers, percentages, or metrics
- ABSOLUTELY NO PERSONAL EXPERIENCES - Do not reference any specific projects, clients, or results
- ABSOLUTELY NO "HERE'S WHAT WORKS FOR ME" - Do not frame advice as personal experience
- NO STORYTELLING - Provide direct advice without narratives

INSTEAD:
- Write ONLY general advice and best practices
- Use phrases like "Consider using..."
- Present tips as industry knowledge, not personal experience
- Keep everything theoretical and educational

Voice and style:
- Write as a 28-year-old man living in the US (with Eastern European background)
- Use short, plain, direct sentences
- Tone should be calm, confident, and straightforward
- Keep it grounded and realistic without hype or exaggeration
- Avoid overly formal language and corporate jargon

Technical requirements:
- Flesch reading score of 80+ (simple, clear language)
- Active voice only
- No adverbs unless absolutely necessary
- No buzzwords or fluff phrases
- Use relevant sales terminology when appropriate
- Never use the phrase "it's about" or similar constructions
- No em dashes
- Never use "follow up" unless specifically explaining alternatives
- Occasional light swearing is acceptable if natural (roughly 1 in 8 posts)

End with a brief call to action and 2-3 relevant hashtags.
Keep the entire post under 1300 characters (LinkedIn's limit).
"""
            
            try:
                # Generate content using the selected provider
                content = provider.generate_content(prompt, max_tokens=700, temperature=0.7)
                
                # Add to repository - this creates its own connection internally
                content_id = self.add_bulk_content(content, f"Campaign: {campaign_id} - {topic}")
                
                # Mark topic as used - separate connection
                max_retries = 5
                retries = 0
                while retries < max_retries:
                    try:
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE campaign_topics SET is_used = 1 WHERE id = ?",
                            (topic_id,)
                        )
                        conn.commit()
                        conn.close()
                        break  # Success, exit the retry loop
                    except sqlite3.OperationalError as e:
                        # Database is locked, retry after a delay
                        conn.close()
                        retries += 1
                        if retries >= max_retries:
                            print(f"Failed to mark topic {topic_id} as used after {max_retries} attempts.")
                        else:
                            # Exponential backoff: wait longer each retry
                            wait_time = 0.1 * (2 ** retries)
                            time.sleep(wait_time)
                
                generated_count += 1
                print(f"Generated post for topic: {topic}")
                
                # Add a small delay between generations to reduce database contention
                time.sleep(0.5)
                    
            except Exception as e:
                print(f"Error generating content for topic '{topic}': {str(e)}")
        
        return generated_count

    def get_campaign_content(self, campaign_id):
        """Get all content generated for a specific campaign"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get content associated with this campaign
        cursor.execute(
            """
            SELECT id, post_text, category, is_used, created_at 
            FROM content_repository 
            WHERE category LIKE ? 
            ORDER BY is_used, created_at DESC
            """, 
            (f"Campaign: {campaign_id}%",)
        )
        content = cursor.fetchall()
        conn.close()
        
        return content

# Example usage
if __name__ == "__main__":
    # This code runs when scheduler.py is executed directly
    scheduler = LinkedInScheduler()
    
    # Example: Add content to repository
    scheduler.add_bulk_content("Just finished a great project on automated social media posting with Python! #automation #python", "Professional")
    scheduler.add_bulk_content("Excited to share thoughts on AI-driven social media management systems soon. Stay tuned! #AI #socialmedia", "Tech")
    
    # Example: Auto-schedule posts
    count = scheduler.auto_schedule_posts(num_posts=2, days_ahead=2)
    print(f"Auto-scheduled {count} posts")
    
    # Check and publish any pending posts
    scheduler.check_and_publish()