from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
import scheduler
from datetime import datetime, timedelta
import threading
import time
import os
import sqlite3

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
        api_key = request.form.get('api_key')
        num_topics = int(request.form.get('num_topics', 15))
        
        try:
            count = post_scheduler.generate_topics(
                campaign_id=campaign_id,
                num_topics=num_topics,
                api_key=api_key
            )
            
            flash(f'Successfully generated {count} topics for your campaign', 'success')
            return redirect(url_for('campaign_detail', campaign_id=campaign_id))
        except Exception as e:
            flash(f'Error generating topics: {str(e)}', 'danger')
    
    return render_template('generate_topics.html', campaign_id=campaign_id)

@app.route('/campaign/<int:campaign_id>/generate_content', methods=['GET', 'POST'])
def generate_campaign_content(campaign_id):
    """Generate content for a campaign's topics"""
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        provider_name = request.form.get('provider_name', 'openai')
        num_posts = int(request.form.get('num_posts', 5))
        
        try:
            count = post_scheduler.generate_content_for_campaign(
                campaign_id=campaign_id,
                num_posts=num_posts,
                api_key=api_key,
                provider_name=provider_name
            )
            
            flash(f'Successfully generated {count} posts using {provider_name} for your campaign', 'success')
            return redirect(url_for('campaign_detail', campaign_id=campaign_id))
        except Exception as e:
            flash(f'Error generating content: {str(e)}', 'danger')
    
    return render_template('generate_campaign_content.html', campaign_id=campaign_id)

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

@app.route('/posts_for_review')
def posts_for_review():
    """Show posts that need review"""
    posts = post_scheduler.get_posts_for_review(days_ahead=7)  # Get posts for next week
    
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
    
    return render_template('posts_for_review.html', posts=formatted_posts)

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

@app.route('/reset_content/<int:content_id>', methods=['POST'])
def reset_content(content_id):
    post_scheduler.reset_content_usage(content_id)
    flash(f'Content {content_id} reset for reuse', 'success')
    return redirect(url_for('content_repository'))

@app.route('/reset_all_content', methods=['POST'])
def reset_all_content():
    post_scheduler.reset_content_usage()
    flash('All content reset for reuse', 'success')
    return redirect(url_for('content_repository'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)