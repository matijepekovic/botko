"""
Campaign service that manages LinkedIn post campaigns.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import random

from ..core.database import db
from ..core.scheduler import scheduler
from ..core.ai_providers import get_provider

class CampaignService:
    """Service for managing campaigns."""
    
    @staticmethod
    def create_campaign(name: str, category: str, posts_per_day: int, 
                        duration_days: int, requires_review: bool = False) -> int:
        """
        Create a new campaign.
        
        Args:
            name: Campaign name
            category: Campaign category
            posts_per_day: Number of posts per day
            duration_days: Duration in days
            requires_review: Whether posts require review
            
        Returns:
            ID of the new campaign
        """
        # Calculate start and end dates
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_days)
        
        # Insert the campaign
        campaign_id = db.insert(
            'campaigns',
            {
                'name': name,
                'category': category,
                'posts_per_day': posts_per_day,
                'duration_days': duration_days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'requires_review': 1 if requires_review else 0
            }
        )
        
        return campaign_id
    
    @staticmethod
    def get_all_campaigns() -> List[Dict[str, Any]]:
        """
        Get all campaigns.
        
        Returns:
            List of campaign dictionaries
        """
        campaigns = db.select(
            table='campaigns',
            order_by='created_at DESC'
        )
        
        # Format campaigns for display
        formatted_campaigns = []
        for campaign in campaigns:
            # Format dates
            try:
                start = datetime.fromisoformat(campaign['start_date']).strftime('%Y-%m-%d')
                end = datetime.fromisoformat(campaign['end_date']).strftime('%Y-%m-%d')
            except:
                start = campaign['start_date']
                end = campaign['end_date']
                
            formatted_campaigns.append({
                'id': campaign['id'],
                'name': campaign['name'],
                'category': campaign['category'],
                'posts_per_day': campaign['posts_per_day'],
                'duration_days': campaign['duration_days'],
                'start_date': start,
                'end_date': end,
                'requires_review': bool(campaign['requires_review']),
                'status': campaign['status'],
                'created_at': campaign['created_at']
            })
        
        return formatted_campaigns
    
    @staticmethod
    def get_campaign(campaign_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific campaign with detailed info.
        
        Args:
            campaign_id: ID of the campaign to retrieve
            
        Returns:
            Campaign dictionary or None if not found
        """
        campaigns = db.select(
            table='campaigns',
            where='id = ?',
            where_params=(campaign_id,),
            limit=1
        )
        
        if not campaigns:
            return None
        
        campaign = campaigns[0]
        
        # Get topic count
        topic_count_result = db.execute(
            "SELECT COUNT(*) as count FROM campaign_topics WHERE campaign_id = ?",
            (campaign_id,)
        ).fetchone()
        topic_count = topic_count_result['count'] if topic_count_result else 0
        
        # Get unused topic count
        unused_topic_count_result = db.execute(
            "SELECT COUNT(*) as count FROM campaign_topics WHERE campaign_id = ? AND is_used = 0",
            (campaign_id,)
        ).fetchone()
        unused_topic_count = unused_topic_count_result['count'] if unused_topic_count_result else 0
        
        # Get scheduled post count
        scheduled_post_count_result = db.execute(
            """
            SELECT COUNT(*) as count FROM scheduled_posts 
            WHERE post_text IN (
                SELECT post_text FROM content_repository 
                WHERE category LIKE ?
            )
            """,
            (f"Campaign: {campaign_id}%",)
        ).fetchone()
        scheduled_post_count = scheduled_post_count_result['count'] if scheduled_post_count_result else 0
        
        # Format dates
        try:
            start = datetime.fromisoformat(campaign['start_date']).strftime('%Y-%m-%d')
            end = datetime.fromisoformat(campaign['end_date']).strftime('%Y-%m-%d')
        except:
            start = campaign['start_date']
            end = campaign['end_date']
            
        return {
            'id': campaign['id'],
            'name': campaign['name'],
            'category': campaign['category'],
            'posts_per_day': campaign['posts_per_day'],
            'duration_days': campaign['duration_days'],
            'start_date': start,
            'end_date': end,
            'requires_review': bool(campaign['requires_review']),
            'status': campaign['status'],
            'created_at': campaign['created_at'],
            'topic_count': topic_count,
            'unused_topic_count': unused_topic_count,
            'scheduled_post_count': scheduled_post_count
        }
    
    @staticmethod
    def delete_campaign(campaign_id: int) -> bool:
        """
        Delete a campaign and its related data.
        
        Args:
            campaign_id: ID of the campaign to delete
            
        Returns:
            Boolean indicating success
        """
        # Start a transaction
        db.execute("BEGIN TRANSACTION")
        
        try:
            # Delete the topics
            db.delete(
                table='campaign_topics',
                where='campaign_id = ?',
                where_params=(campaign_id,)
            )
            
            # Delete any content in the repository associated with this campaign
            db.delete(
                table='content_repository',
                where='category LIKE ?',
                where_params=(f"Campaign: {campaign_id}%",)
            )
            
            # Delete the campaign itself
            db.delete(
                table='campaigns',
                where='id = ?',
                where_params=(campaign_id,)
            )
            
            # Commit the transaction
            db.commit()
            return True
        except:
            # Rollback in case of error
            db.rollback()
            raise
    
    @staticmethod
    def generate_topics(campaign_id: int, num_topics: int = 15, api_key: str = None, provider_name: str = "openai") -> int:
        """Generate topics for a campaign using the selected AI provider"""
        
        # Get campaign details
        campaign = CampaignService.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign with ID {campaign_id} not found")
        
        category = campaign['category']
        
        # Get the appropriate AI provider
        from ai_providers import get_provider
        provider = get_provider(provider_name, api_key)
        
        # Create the prompt for topic generation - MODIFIED FOR ANY CATEGORY
        prompt = f"""
        Generate {num_topics} current and relevant topics about {category} that reflect what professionals in this field are dealing with right now.
        
        These topics should be practical, not academic. Avoid corporate buzzwords or fluff. Focus on real conversations, problems, and patterns that professionals in {category} are facing in the current year.
        
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
                db.insert(
                    'campaign_topics',
                    {
                        'campaign_id': campaign_id,
                        'topic': topic
                    }
                )
            
            return len(topics)
                
        except Exception as e:
            print(f"Error generating topics: {str(e)}")
            raise
    
    @staticmethod
    def get_campaign_topics(campaign_id: int) -> List[Dict[str, Any]]:
        """
        Get all topics for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            List of topic dictionaries
        """
        topics = db.select(
            table='campaign_topics',
            where='campaign_id = ?',
            where_params=(campaign_id,),
            order_by='is_used, id'
        )
        
        formatted_topics = []
        for topic in topics:
            formatted_topics.append({
                'id': topic['id'],
                'text': topic['topic'],
                'is_used': bool(topic['is_used']),
                'created_at': topic['created_at']
            })
        
        return formatted_topics
    
    @staticmethod
    def update_topic(topic_id: int, topic_text: str) -> bool:
        """
        Update a campaign topic.
        
        Args:
            topic_id: Topic ID
            topic_text: New topic text
            
        Returns:
            Boolean indicating success
        """
        rowcount = db.update(
            table='campaign_topics',
            data={'topic': topic_text},
            where='id = ?',
            where_params=(topic_id,)
        )
        
        return rowcount > 0
    
    @staticmethod
    def delete_topic(topic_id: int) -> bool:
        """
        Delete a campaign topic.
        
        Args:
            topic_id: Topic ID
            
        Returns:
            Boolean indicating success
        """
        rowcount = db.delete(
            table='campaign_topics',
            where='id = ?',
            where_params=(topic_id,)
        )
        
        return rowcount > 0
    
    @staticmethod
    def delete_all_topics(campaign_id: int) -> int:
        """
        Delete all topics for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Number of topics deleted
        """
        # Get count first
        topic_count_result = db.execute(
            "SELECT COUNT(*) as count FROM campaign_topics WHERE campaign_id = ?",
            (campaign_id,)
        ).fetchone()
        topic_count = topic_count_result['count'] if topic_count_result else 0
        
        # Delete all topics
        db.delete(
            table='campaign_topics',
            where='campaign_id = ?',
            where_params=(campaign_id,)
        )
        
        return topic_count
    
    @staticmethod
    def generate_content(campaign_id: int, api_key: str = None, provider_name: str = "openai", 
                        persona: dict = None) -> int:
        """
        Generate content for campaign topics.
        
        Args:
            campaign_id: Campaign ID
            api_key: API key for the AI provider
            provider_name: Name of the AI provider to use
            persona: Optional dictionary with persona details
                
        Returns:
            Number of content items generated
        """
        # Get the campaign
        campaign = CampaignService.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign with ID {campaign_id} not found")
        
        category = campaign['category']
        
        # Use default persona if none provided
        if not persona:
            # You can load this from a settings file or database in the future
            persona = {
                "profession": "professional",
                "age": "28",
                "background": "lives in the U.S. but was born in Eastern Europe",
                "tone": "calm, confident, and direct",
                "style": "honest, grounded, and human"
            }
        
        # Get all unused topics
        topics = db.select(
            table='campaign_topics',
            where='campaign_id = ? AND is_used = 0',
            where_params=(campaign_id,)
        )
        
        if not topics:
            raise ValueError(f"No unused topics found for campaign {campaign_id}")
        
        # Get the AI provider
        provider = get_provider(provider_name, api_key)
        
        generated_count = 0
        for topic in topics:
            topic_id = topic['id']
            topic_text = topic['topic']
            
            # Determine post complexity based on topic length and complexity
            complexity = "simple" if len(topic_text.split()) < 4 else "detailed"
            
            # Create the prompt for content generation with dynamic components
            prompt = f"""
            Write a professional LinkedIn post about "{topic_text}" for a {category} {persona['profession']}.
            
            This post should be {complexity} and include practical insights relevant to {category}.
            
            The tone should be professional but conversational, positioning the author as an 
            expert in the field. Include a call to action at the end.
            Only include information that is factual and can be substantiated.
            
            Write as a {persona['age']}-year-old who {persona['background']}. 
            The tone should be {persona['tone']}. 
            The style should be {persona['style']}.
            Use plain English with short sentences. Sound like someone who's been in the field, not in a meeting.
            
            Writing Rules:
            - Use active voice
            - Avoid unnecessary adverbs
            - No corporate buzzwords or fluff
            - Use relevant industry terminology when it fits
            - Keep it conversational but professional
            - Break up long paragraphs for readability
            - Include at least one concrete example or insight
            
            Finish with 2-3 relevant hashtags.
            
            Keep the post under 1300 characters (LinkedIn's limit).
            """
            
            # Generate content
            content = provider.generate_content(prompt, max_tokens=700, temperature=0.7)
            
            # Add to repository
            content_id = db.insert(
                'content_repository',
                {
                    'post_text': content,
                    'category': f"Campaign: {campaign_id} - {topic_text}"
                }
            )
            
            # Mark topic as used
            db.update(
                table='campaign_topics',
                data={'is_used': 1},
                where='id = ?',
                where_params=(topic_id,)
            )
            
            generated_count += 1
        
        return generated_count
    
    @staticmethod
    def get_campaign_content(campaign_id: int) -> List[Dict[str, Any]]:
        """
        Get all content for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            List of content dictionaries
        """
        content = db.select(
            table='content_repository',
            where='category LIKE ?',
            where_params=(f"Campaign: {campaign_id}%",),
            order_by='is_used, created_at DESC'
        )
        
        formatted_content = []
        for item in content:
            # Extract the topic from the category (format is "Campaign: ID - Topic")
            category = item['category'] or ""
            topic = category.split(" - ", 1)[1] if " - " in category else ""
            
            formatted_content.append({
                'id': item['id'],
                'text': item['post_text'],
                'topic': topic,
                'is_used': bool(item['is_used']),
                'created_at': item['created_at']
            })
        
        return formatted_content
    
    @staticmethod
    def schedule_campaign_posts(campaign_id: int) -> int:
        """
        Schedule posts for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Number of posts scheduled
        """
        # Get campaign details
        campaign = CampaignService.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign with ID {campaign_id} not found")
        
        posts_per_day = campaign['posts_per_day']
        requires_review = campaign['requires_review']
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(campaign['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(campaign['end_date'].replace('Z', '+00:00'))
        except:
            # Fallback to current date range if parsing fails
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=campaign['duration_days'])
        
        # Get unscheduled content for this campaign
        content = db.select(
            table='content_repository',
            where='category LIKE ? AND is_used = 0',
            where_params=(f"Campaign: {campaign_id}%",)
        )
        
        if not content:
            raise ValueError(f"No unscheduled content found for campaign {campaign_id}")
        
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
                content_item = content[i]
                content_id = content_item['id']
                post_text = content_item['post_text']
                
                # Schedule the post
                post_id = db.insert(
                    'scheduled_posts',
                    {
                        'post_text': post_text,
                        'schedule_time': post_time.isoformat(),
                        'needs_review': 1 if requires_review else 0
                    }
                )
                
                # Mark content as used
                db.update(
                    table='content_repository',
                    data={'is_used': 1},
                    where='id = ?',
                    where_params=(content_id,)
                )
                
                scheduled_count += 1
        
        return scheduled_count