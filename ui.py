from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_bootstrap import Bootstrap
import scheduler
from datetime import datetime, timedelta
import threading
import time
import os
import sqlite3
import traceback
import sys

# Global progress tracking variables
generation_progress = {
    'status': 'idle',
    'campaign_id': None,
    'completed': 0,
    'total': 0,
    'messages': []
}

def log_error(message, exception=None):
    """Log errors to console and file for debugging"""
    error_log = f"ERROR: {message}"
    if exception:
        error_log += f"\n{str(exception)}\n{traceback.format_exc()}"
    
    print(error_log)  # Console output
    
    # Also log to file
    with open("error_log.txt", "a") as f:
        f.write(f"[{datetime.now()}] {error_log}\n\n")

app = Flask(__name__)
app.secret_key = 'linkedin_bot_secret_key'  # Required for flash messages
Bootstrap(app)

# Create an instance of our scheduler
post_scheduler = scheduler.LinkedInScheduler()

# Background thread for checking posts
def background_scheduler():
    while True:
        post_scheduler.check_and_publish()
        time.sleep(60)  # Check every minute

# Start the background thread
scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
scheduler_thread.start()

@app.route('/')
def index():
    # Get all posts from the scheduler
    posts = post_scheduler.get_all_scheduled_posts()
    
    # Format the posts for display
    formatted_posts = []
    for post in posts:
        post_id, text, schedule_time, status, created_at = post
        
        # Convert ISO time to a more readable format
        try:
            schedule_datetime = datetime.fromisoformat(schedule_time)
            formatted_time = schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_time = schedule_time
            
        formatted_posts.append({
            'id': post_id,
            'text': text,
            'scheduled_time': formatted_time,
            'status': status,
            'created_at': created_at
        })
    
    return render_template('index.html', posts=formatted_posts)

@app.route('/add', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        post_text = request.form.get('post_text')
        schedule_date = request.form.get('schedule_date')
        schedule_time = request.form.get('schedule_time')
        
        # Combine date and time into ISO format
        try:
            schedule_datetime = datetime.strptime(f"{schedule_date} {schedule_time}", '%Y-%m-%d %H:%M')
            schedule_iso = schedule_datetime.isoformat()
            
            # Add post to scheduler
            post_id = post_scheduler.add_post(post_text, schedule_iso)
            flash(f'Post scheduled successfully with ID: {post_id}', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error scheduling post: {str(e)}', 'danger')
    
    # For GET request, just show the form
    # Default to tomorrow for date
    tomorrow = datetime.now() + timedelta(days=1)
    default_date = tomorrow.strftime('%Y-%m-%d')
    default_time = '12:00'
    
    return render_template('add_post.html', default_date=default_date, default_time=default_time)

@app.route('/campaigns')
def list_campaigns():
    """List all campaigns"""
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    
    # Create campaigns table if it doesn't exist
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
    
    cursor.execute(
        """
        SELECT id, name, category, posts_per_day, duration_days, 
               start_date, end_date, requires_review, status, created_at
        FROM campaigns
        ORDER BY created_at DESC
        """
    )
    campaigns = cursor.fetchall()
    conn.close()
    
    formatted_campaigns = []
    for campaign in campaigns:
        (campaign_id, name, category, posts_per_day, 
         duration_days, start_date, end_date, 
         requires_review, status, created_at) = campaign
        
        # Format dates
        try:
            start = datetime.fromisoformat(start_date).strftime('%Y-%m-%d')
            end = datetime.fromisoformat(end_date).strftime('%Y-%m-%d')
        except:
            start = start_date
            end = end_date
            
        formatted_campaigns.append({
            'id': campaign_id,
            'name': name,
            'category': category,
            'posts_per_day': posts_per_day,
            'duration_days': duration_days,
            'start_date': start,
            'end_date': end,
            'requires_review': bool(requires_review),
            'status': status,
            'created_at': created_at
        })
    
    return render_template('campaigns.html', campaigns=formatted_campaigns)

@app.route('/create_campaign', methods=['GET', 'POST'])
def create_campaign():
    """Create a new campaign"""
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        posts_per_day = int(request.form.get('posts_per_day', 1))
        duration_days = int(request.form.get('duration_days', 30))
        requires_review = 'requires_review' in request.form
        
        try:
            campaign_id = post_scheduler.create_campaign(
                name=name,
                category=category,
                posts_per_day=posts_per_day,
                duration_days=duration_days,
                requires_review=requires_review
            )
            
            flash(f'Campaign "{name}" created successfully with ID: {campaign_id}', 'success')
            return redirect(url_for('campaign_detail', campaign_id=campaign_id))
        except Exception as e:
            flash(f'Error creating campaign: {str(e)}', 'danger')
    
    return render_template('create_campaign.html')

@app.route('/campaign/<int:campaign_id>')
def campaign_detail(campaign_id):
    """Show campaign details and actions"""
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    
    # Get campaign details
    cursor.execute(
        """
        SELECT name, category, posts_per_day, duration_days, 
               start_date, end_date, requires_review, status
        FROM campaigns
        WHERE id = ?
        """,
        (campaign_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        flash(f'Campaign with ID {campaign_id} not found', 'danger')
        return redirect(url_for('list_campaigns'))
    
    (name, category, posts_per_day, duration_days, 
     start_date, end_date, requires_review, status) = result
    
    # Get topic count
    cursor.execute(
        "SELECT COUNT(*) FROM campaign_topics WHERE campaign_id = ?",
        (campaign_id,)
    )
    topic_count = cursor.fetchone()[0] or 0
    
    # Get unused topic count
    cursor.execute(
        "SELECT COUNT(*) FROM campaign_topics WHERE campaign_id = ? AND is_used = 0",
        (campaign_id,)
    )
    unused_topic_count = cursor.fetchone()[0] or 0
    
    # Get scheduled post count
    cursor.execute(
        """
        SELECT COUNT(*) FROM scheduled_posts 
        WHERE post_text IN (
            SELECT post_text FROM content_repository 
            WHERE category LIKE ?
        )
        """,
        (f"Campaign: {campaign_id}%",)
    )
    scheduled_post_count = cursor.fetchone()[0] or 0
    
    conn.close()
    
    campaign = {
        'id': campaign_id,
        'name': name,
        'category': category,
        'posts_per_day': posts_per_day,
        'duration_days': duration_days,
        'start_date': datetime.fromisoformat(start_date).strftime('%Y-%m-%d'),
        'end_date': datetime.fromisoformat(end_date).strftime('%Y-%m-%d'),
        'requires_review': bool(requires_review),
        'status': status,
        'topic_count': topic_count,
        'unused_topic_count': unused_topic_count,
        'scheduled_post_count': scheduled_post_count
    }
    
    return render_template('campaign_detail.html', campaign=campaign)

@app.route('/campaign/<int:campaign_id>/generate_topics', methods=['GET', 'POST'])
def generate_campaign_topics(campaign_id):
    """Generate topics for a campaign"""
    if request.method == 'POST':
        try:
            api_key = request.form.get('api_key')
            provider_name = request.form.get('provider_name', 'openai')  # Add this line
            num_topics = int(request.form.get('num_topics', 15))
            
            try:
                count = post_scheduler.generate_topics(
                    campaign_id=campaign_id,
                    num_topics=num_topics,
                    api_key=api_key,
                    provider_name=provider_name  # Add this parameter
                )
                
                flash(f'Successfully generated {count} topics for your campaign', 'success')
                return redirect(url_for('campaign_detail', campaign_id=campaign_id))
            except Exception as e:
                log_error(f"Error generating topics with {provider_name}", e)
                flash(f'Error generating topics: {str(e)}', 'danger')
        except Exception as e:
            log_error("Error in generate_campaign_topics form processing", e)
            flash("There was an error processing your request. See logs for details.", "danger")
    
    try:
        return render_template('generate_topics.html', campaign_id=campaign_id)
    except Exception as e:
        log_error("Error rendering generate_topics.html template", e)
        flash("Error displaying template. See logs for details.", "danger")
        return redirect(url_for('index'))

@app.route('/campaign/<int:campaign_id>/generate_content', methods=['GET', 'POST'])
def generate_campaign_content(campaign_id):
    """Generate content for a campaign's topics"""
    global generation_progress
    
    if request.method == 'POST':
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        api_key = request.form.get('api_key')
        provider_name = request.form.get('provider_name', 'openai')
        
        try:
            # Reset progress tracking
            generation_progress = {
                'status': 'in_progress',
                'campaign_id': campaign_id,
                'completed': 0,
                'total': 0,
                'messages': ['Starting content generation...']
            }
            
            # Get topic count to update total
            conn = sqlite3.connect(post_scheduler.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM campaign_topics WHERE campaign_id = ? AND is_used = 0",
                (campaign_id,)
            )
            topic_count = cursor.fetchone()[0]
            conn.close()
            
            generation_progress['total'] = topic_count
            
            # Run content generation in a separate thread
            def generate_content_thread():
                global generation_progress
                try:
                    # Override the original generate_content_for_campaign method to track progress
                    original_method = post_scheduler.generate_content_for_campaign
                    
                    def progress_tracking_method(campaign_id, api_key=None, provider_name="openai"):
                        global generation_progress
                        
                        # Get all unused topics for this campaign
                        conn = sqlite3.connect(post_scheduler.db_path)
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT id, topic FROM campaign_topics WHERE campaign_id = ? AND is_used = 0",
                            (campaign_id,)
                        )
                        topics = cursor.fetchall()
                        conn.close()
                        
                        if not topics:
                            generation_progress['messages'].append("No unused topics found for this campaign")
                            generation_progress['status'] = 'completed'
                            return 0
                        
                        # Get campaign category
                        conn = sqlite3.connect(post_scheduler.db_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT category FROM campaigns WHERE id = ?", (campaign_id,))
                        category = cursor.fetchone()[0]
                        conn.close()
                        
                        import ai_providers
                        provider = ai_providers.get_provider(provider_name, api_key)
                        
                        generation_progress['messages'].append(f"Using {provider_name} to generate content for {len(topics)} topics")
                        generation_progress['total'] = len(topics)
                        
                        generated_count = 0
                        for topic_id, topic in topics:
                            generation_progress['messages'].append(f"Generating post for topic: {topic}")
                            
                            # Use the rest of the original method logic for each topic
                            complexity = "simple" if len(topic.split()) < 4 else "detailed"
                            
                            prompt = f"""
                            Write a professional LinkedIn post about "{topic}" for a sales consultant.
                            
                            This post should be {complexity} and include practical insights relevant to the 
                            {category} aspect of home sales.
                            
                            The tone should be professional but conversational, positioning the author as an 
                            expert in the field. Include a call to action at the end.
                            
                            Write as a 28-year-old guy who lives in the U.S. but was born in Eastern Europe. The tone should be calm, confident, and direct. Avoid formal or fluffy language. Use short, plain English sentences. Keep it honest, grounded, and human. Sound like someone who's been in the field, not in a meeting.
                            
                            Writing Rules:
                            - Flesch reading score of 80 or higher
                            - Use active voice
                            - Avoid adverbs unless necessary
                            - No buzzwords, no fluff
                            - Use relevant sales or trade jargon when it fits
                            - Never say "its about this, its about that"
                            - Never use em dashes
                            - Never use the word "follow up," unless explaining what else to say instead
                            - Lightly swear once in every 8 posts (optional, natural tone only)
                            
                            Finish with 2-3 relevant hashtags.
                            
                            Keep the post under 1300 characters (LinkedIn's limit).
                            """
                            
                            try:
                                content = provider.generate_content(prompt, max_tokens=700, temperature=0.7)
                                
                                # Add to repository
                                content_id = post_scheduler.add_bulk_content(content, f"Campaign: {campaign_id} - {topic}")
                                
                                # Mark topic as used - with retry logic
                                max_retries = 5
                                retries = 0
                                while retries < max_retries:
                                    try:
                                        conn = sqlite3.connect(post_scheduler.db_path)
                                        cursor = conn.cursor()
                                        cursor.execute(
                                            "UPDATE campaign_topics SET is_used = 1 WHERE id = ?",
                                            (topic_id,)
                                        )
                                        conn.commit()
                                        conn.close()
                                        break
                                    except sqlite3.OperationalError as e:
                                        conn.close()
                                        retries += 1
                                        if retries >= max_retries:
                                            generation_progress['messages'].append(f"Warning: Failed to mark topic {topic_id} as used after {max_retries} attempts")
                                        else:
                                            wait_time = 0.1 * (2 ** retries)
                                            time.sleep(wait_time)
                                
                                generated_count += 1
                                generation_progress['completed'] = generated_count
                                generation_progress['messages'].append(f"Successfully generated post #{generated_count} for topic: {topic}")
                                
                                # Add a small delay between generations
                                time.sleep(0.5)
                                
                            except Exception as e:
                                generation_progress['messages'].append(f"Error generating content for topic '{topic}': {str(e)}")
                                import traceback
                                traceback.print_exc()
                        
                        generation_progress['status'] = 'completed'
                        generation_progress['messages'].append(f"Content generation completed - {generated_count} posts generated")
                        return generated_count
                    
                    # Override the method temporarily
                    post_scheduler.generate_content_for_campaign = progress_tracking_method
                    
                    # Call our modified method
                    count = post_scheduler.generate_content_for_campaign(
                        campaign_id=campaign_id,
                        api_key=api_key,
                        provider_name=provider_name
                    )
                    
                    # Restore the original method
                    post_scheduler.generate_content_for_campaign = original_method
                    
                    generation_progress['status'] = 'completed'
                    generation_progress['messages'].append(f"Successfully generated {count} posts")
                    
                except Exception as e:
                    generation_progress['status'] = 'error'
                    generation_progress['messages'].append(f"Error: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # Start the generation thread
            thread = threading.Thread(target=generate_content_thread)
            thread.daemon = True
            thread.start()
            
            # For AJAX requests, return JSON response
            if is_ajax:
                # Wait a moment to allow the progress tracking to be initialized
                time.sleep(0.5)
                return jsonify({
                    'status': 'success',
                    'message': 'Content generation started',
                    'count': generation_progress.get('total', 0)
                })
            else:
                # For regular form submissions, use a flash message and redirect
                flash(f'Content generation has been started for your campaign', 'success')
                return redirect(url_for('campaign_detail', campaign_id=campaign_id))
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            if is_ajax:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                })
            else:
                flash(f'Error generating content: {str(e)}', 'danger')
    
    return render_template('generate_campaign_content.html', campaign_id=campaign_id)

@app.route('/campaign/<int:campaign_id>/generate_content/progress')
def get_generation_progress(campaign_id):
    """API endpoint to check content generation progress"""
    global generation_progress
    
    # Only return progress for the requested campaign
    if generation_progress['campaign_id'] != campaign_id:
        return jsonify({
            'status': 'not_started',
            'campaign_id': campaign_id,
            'completed': 0,
            'total': 0,
            'messages': []
        })
    
    # If completed, check if we need to return the full content payload
    if generation_progress['status'] == 'completed':
        return jsonify({
            'status': 'success',
            'campaign_id': campaign_id,
            'completed': generation_progress['completed'],
            'total': generation_progress['total'],
            'messages': generation_progress['messages'],
            'count': generation_progress['completed']
        })
    
    return jsonify(generation_progress)

@app.route('/campaign/<int:campaign_id>/schedule', methods=['GET', 'POST'])
def schedule_campaign(campaign_id):
    """Schedule posts for a campaign"""
    if request.method == 'POST':
        try:
            count = post_scheduler.schedule_campaign_posts(campaign_id)
            
            flash(f'Successfully scheduled {count} posts for your campaign', 'success')
            return redirect(url_for('campaign_detail', campaign_id=campaign_id))
        except Exception as e:
            flash(f'Error scheduling posts: {str(e)}', 'danger')
    
    return render_template('schedule_campaign.html', campaign_id=campaign_id)

@app.route('/campaign/<int:campaign_id>/content')
def campaign_content(campaign_id):
    """Show all content for a campaign"""
    # Get campaign details
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, category FROM campaigns WHERE id = ?", (campaign_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        flash('Campaign not found', 'danger')
        return redirect(url_for('list_campaigns'))
    
    name, category = result
    
    # Get campaign content
    content = post_scheduler.get_campaign_content(campaign_id)
    
    formatted_content = []
    for item in content:
        content_id, post_text, content_category, is_used, created_at = item
        
        # Extract the topic from the category (format is "Campaign: ID - Topic")
        topic = content_category.split(" - ", 1)[1] if " - " in content_category else ""
        
        formatted_content.append({
            'id': content_id,
            'text': post_text,
            'topic': topic,
            'is_used': bool(is_used),
            'created_at': created_at
        })
    
    campaign = {
        'id': campaign_id,
        'name': name,
        'category': category
    }
    
    return render_template('campaign_content.html', 
                          campaign=campaign, 
                          content=formatted_content)

@app.route('/posts_for_review')
def posts_for_review():
    """Show posts that need review"""
    try:
        # Wrap the core functionality in a try-except
        try:
            posts = post_scheduler.get_posts_for_review(days_ahead=7)
        except Exception as e:
            log_error("Error retrieving posts for review", e)
            # Provide an empty list if the method fails
            posts = []
            flash("Could not retrieve posts for review. See error log for details.", "warning")
        
        formatted_posts = []
        for post in posts:
            try:
                post_id, text, schedule_time, status, created_at = post
                
                # Convert ISO time to a more readable format
                try:
                    schedule_datetime = datetime.fromisoformat(schedule_time)
                    formatted_time = schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_time = schedule_time
                    
                formatted_posts.append({
                    'id': post_id,
                    'text': text,
                    'scheduled_time': formatted_time,
                    'status': status,
                    'created_at': created_at
                })
            except Exception as post_e:
                log_error(f"Error formatting post {post}", post_e)
        
        # Render template with error handling
        try:
            return render_template('posts_for_review.html', posts=formatted_posts)
        except Exception as template_e:
            log_error("Error rendering posts_for_review.html template", template_e)
            flash("Error displaying posts for review template.", "danger")
            return redirect(url_for('index'))
            
    except Exception as route_e:
        log_error("Unhandled error in posts_for_review route", route_e)
        flash("An unexpected error occurred. Check the logs for details.", "danger")
        return redirect(url_for('index'))

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    """Edit a post"""
    if request.method == 'POST':
        new_text = request.form.get('post_text')
        
        conn = sqlite3.connect(post_scheduler.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE scheduled_posts SET post_text = ?, reviewed = 1 WHERE id = ?",
            (new_text, post_id)
        )
        conn.commit()
        conn.close()
        
        flash(f'Post {post_id} updated successfully', 'success')
        return redirect(url_for('posts_for_review'))
    
    # Get post details
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT post_text, schedule_time FROM scheduled_posts WHERE id = ?",
        (post_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        flash('Post not found', 'danger')
        return redirect(url_for('posts_for_review'))
    
    post_text, schedule_time = result
    
    try:
        schedule_datetime = datetime.fromisoformat(schedule_time)
        formatted_time = schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')
    except:
        formatted_time = schedule_time
    
    return render_template('edit_post.html', post_id=post_id, post_text=post_text, scheduled_time=formatted_time)

@app.route('/approve_post/<int:post_id>', methods=['POST'])
def approve_post(post_id):
    """Approve a post"""
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE scheduled_posts SET reviewed = 1 WHERE id = ?",
        (post_id,)
    )
    conn.commit()
    conn.close()
    
    flash(f'Post {post_id} approved', 'success')
    return redirect(url_for('posts_for_review'))

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    post_scheduler.delete_post(post_id)
    flash(f'Post {post_id} deleted', 'success')
    return redirect(url_for('index'))

# For the second occurrence (change to this):
@app.route('/deletes/<int:post_id>', methods=['POST'])
def delete_review_post(post_id):  # <-- Changed function name here
    post_scheduler.delete_post(post_id)
    flash(f'Post {post_id} deleted', 'success')
    return redirect(url_for('posts_for_review'))

# BULK CONTENT REPOSITORY ROUTES

@app.route('/repository')
def content_repository():
    # Get all content from the repository
    content = post_scheduler.get_content_repository()
    
    formatted_content = []
    for item in content:
        content_id, text, category, is_used, created_at = item
        formatted_content.append({
            'id': content_id,
            'text': text,
            'category': category or "None",
            'is_used': bool(is_used),
            'created_at': created_at
        })
    
    return render_template('repository.html', content=formatted_content)

@app.route('/add_content', methods=['GET', 'POST'])
def add_content():
    if request.method == 'POST':
        post_text = request.form.get('post_text')
        category = request.form.get('category')
        
        if not category or category.strip() == "":
            category = None
            
        # Add content to repository
        content_id = post_scheduler.add_bulk_content(post_text, category)
        flash(f'Content added to repository with ID: {content_id}', 'success')
        return redirect(url_for('content_repository'))
    
    # Get existing categories for dropdown
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM content_repository WHERE category IS NOT NULL")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return render_template('add_content.html', categories=categories)

@app.route('/import_csv', methods=['GET', 'POST'])
def import_csv():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file:
            file_path = 'temp_import.csv'
            file.save(file_path)
            
            try:
                count = post_scheduler.import_from_csv(file_path)
                flash(f'Successfully imported {count} posts from CSV', 'success')
                return redirect(url_for('content_repository'))
            except Exception as e:
                flash(f'Error importing CSV: {str(e)}', 'danger')
            finally:
                # Clean up temp file
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    return render_template('import_csv.html')

@app.route('/auto_schedule', methods=['GET', 'POST'])
def auto_schedule():
    if request.method == 'POST':
        num_posts = int(request.form.get('num_posts', 7))
        days_ahead = int(request.form.get('days_ahead', 7))
        category = request.form.get('category') or None
        start_hour = int(request.form.get('start_hour', 9))
        end_hour = int(request.form.get('end_hour', 17))
        
        count = post_scheduler.auto_schedule_posts(
            num_posts=num_posts, 
            days_ahead=days_ahead, 
            category=category,
            time_range=(start_hour, end_hour)
        )
        
        flash(f'Successfully scheduled {count} posts automatically', 'success')
        return redirect(url_for('index'))
    
    # Get available categories for dropdown
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM content_repository WHERE category IS NOT NULL")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Count unused content
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM content_repository WHERE is_used = 0")
    unused_count = cursor.fetchone()[0]
    conn.close()
    
    return render_template('auto_schedule.html', categories=categories, unused_count=unused_count)


@app.route('/campaign/<int:campaign_id>/topics')
def campaign_topics(campaign_id):
    """Show all topics for a campaign"""
    # Get campaign details
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, category FROM campaigns WHERE id = ?", (campaign_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        flash('Campaign not found', 'danger')
        return redirect(url_for('list_campaigns'))
    
    name, category = result
    
    # Get campaign topics
    topics = post_scheduler.get_campaign_topics(campaign_id)
    
    formatted_topics = []
    for topic in topics:
        topic_id, topic_text, is_used, created_at = topic
        formatted_topics.append({
            'id': topic_id,
            'text': topic_text,
            'is_used': bool(is_used),
            'created_at': created_at
        })
    
    campaign = {
        'id': campaign_id,
        'name': name,
        'category': category
    }
    
    return render_template('campaign_topics.html', 
                          campaign=campaign, 
                          topics=formatted_topics)

@app.route('/campaign/topic/<int:topic_id>/edit', methods=['GET', 'POST'])
def edit_campaign_topic(topic_id):
    """Edit a campaign topic"""
    # Get topic and campaign details
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    
    # Get topic details
    cursor.execute(
        """
        SELECT t.topic, t.campaign_id, c.name 
        FROM campaign_topics t
        JOIN campaigns c ON t.campaign_id = c.id
        WHERE t.id = ?
        """, 
        (topic_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        flash('Topic not found', 'danger')
        return redirect(url_for('list_campaigns'))
    
    topic_text, campaign_id, campaign_name = result
    
    if request.method == 'POST':
        new_topic = request.form.get('topic_text')
        
        if new_topic:
            post_scheduler.update_campaign_topic(topic_id, new_topic)
            flash('Topic updated successfully', 'success')
            return redirect(url_for('campaign_topics', campaign_id=campaign_id))
        else:
            flash('Topic text cannot be empty', 'danger')
    
    return render_template('edit_topic.html', 
                          topic_id=topic_id,
                          topic_text=topic_text,
                          campaign_id=campaign_id,
                          campaign_name=campaign_name)

@app.route('/campaign/topic/<int:topic_id>/delete', methods=['POST'])
def delete_campaign_topic(topic_id):
    """Delete a campaign topic"""
    # Get campaign ID before deleting
    conn = sqlite3.connect(post_scheduler.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT campaign_id FROM campaign_topics WHERE id = ?", (topic_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        flash('Topic not found', 'danger')
        return redirect(url_for('list_campaigns'))
    
    campaign_id = result[0]
    
    # Delete the topic
    post_scheduler.delete_campaign_topic(topic_id)
    flash('Topic deleted successfully', 'success')
    
    return redirect(url_for('campaign_topics', campaign_id=campaign_id))

@app.route('/reset_content/<int:content_id>', methods=['POST'])
def reset_content(content_id):
    """Reset content status to allow reuse"""
    # Get the referer URL to determine where to redirect back to
    referer = request.headers.get('Referer', '')
    
    # Reset the content status
    post_scheduler.reset_content_usage(content_id)
    flash(f'Content {content_id} reset for reuse', 'success')
    
    # Check if we came from a campaign content page
    if '/campaign/' in referer and '/content' in referer:
        # Extract campaign_id from the referer URL
        try:
            campaign_id = int(referer.split('/campaign/')[1].split('/')[0])
            return redirect(url_for('campaign_content', campaign_id=campaign_id))
        except:
            pass
    
    # Default redirect to content repository
    return redirect(url_for('content_repository'))

@app.route('/reset_all_content', methods=['POST'])
def reset_all_content():
    post_scheduler.reset_content_usage()
    flash('All content reset for reuse', 'success')
    return redirect(url_for('content_repository'))

@app.route('/campaign/<int:campaign_id>/delete', methods=['POST'])
def delete_campaign(campaign_id):
    """Delete a campaign and all its associated data"""
    try:
        # Get campaign name for the flash message
        conn = sqlite3.connect(post_scheduler.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM campaigns WHERE id = ?", (campaign_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            flash('Campaign not found', 'danger')
            return redirect(url_for('list_campaigns'))
        
        campaign_name = result[0]
        
        # Delete the campaign
        post_scheduler.delete_campaign(campaign_id)
        flash(f'Campaign "{campaign_name}" has been deleted successfully', 'success')
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error deleting campaign: {str(e)}', 'danger')
    
    return redirect(url_for('list_campaigns'))

@app.route('/campaign/<int:campaign_id>/topics/delete_all', methods=['POST'])
def delete_all_campaign_topics(campaign_id):
    """Delete all topics for a campaign"""
    try:
        # Get campaign name for the flash message
        conn = sqlite3.connect(post_scheduler.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM campaigns WHERE id = ?", (campaign_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            flash('Campaign not found', 'danger')
            return redirect(url_for('list_campaigns'))
        
        campaign_name = result[0]
        
        # Delete all topics
        count = post_scheduler.delete_all_campaign_topics(campaign_id)
        
        if count > 0:
            flash(f'Successfully deleted all {count} topics for campaign "{campaign_name}"', 'success')
        else:
            flash(f'No topics found to delete for campaign "{campaign_name}"', 'info')
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error deleting topics: {str(e)}', 'danger')
    
    return redirect(url_for('campaign_topics', campaign_id=campaign_id))

if __name__ == '__main__':
    try:
        print("Starting LinkedIn Bot web interface...")
        # Check if the database file exists
        if not os.path.exists(post_scheduler.db_path):
            print(f"WARNING: Database file {post_scheduler.db_path} does not exist. It will be created.")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        log_error("Failed to start Flask application", e)
        print("\nApplication failed to start. Check error_log.txt for details.")
        sys.exit(1)