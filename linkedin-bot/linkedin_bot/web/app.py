"""
Flask web application for LinkedIn Bot.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_bootstrap import Bootstrap
import threading
import time
import os
import traceback
import sys
from datetime import datetime 

from ..services.post_service import PostService
from ..services.content_service import ContentService
from ..services.campaign_service import CampaignService
from ..services.auth_service import AuthService
from ..core.scheduler import scheduler

app = Flask(__name__)
app.secret_key = 'linkedin_bot_secret_key'  # Required for flash messages
Bootstrap(app)

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

# Background thread for checking posts
def background_scheduler():
    while True:
        scheduler.check_and_publish()
        time.sleep(60)  # Check every minute

# Start the background thread
scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
scheduler_thread.start()

@app.route('/')
def index():
    # Get all posts from the service
    posts = PostService.get_all_posts()
    return render_template('index.html', posts=posts)

@app.route('/add', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        post_text = request.form.get('post_text')
        schedule_date = request.form.get('schedule_date')
        schedule_time = request.form.get('schedule_time')
        
        try:
            post_id = PostService.add_post(post_text, schedule_date, schedule_time)
            flash(f'Post scheduled successfully with ID: {post_id}', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error scheduling post: {str(e)}', 'danger')
    
    # For GET request, just show the form
    # Default to tomorrow for date
    from datetime import datetime, timedelta
    tomorrow = datetime.now() + timedelta(days=1)
    default_date = tomorrow.strftime('%Y-%m-%d')
    default_time = '12:00'
    
    return render_template('add_post.html', default_date=default_date, default_time=default_time)

@app.route('/campaigns')
def list_campaigns():
    """List all campaigns"""
    formatted_campaigns = CampaignService.get_all_campaigns()
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
            campaign_id = CampaignService.create_campaign(
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
    campaign = CampaignService.get_campaign(campaign_id)
    
    if not campaign:
        flash(f'Campaign with ID {campaign_id} not found', 'danger')
        return redirect(url_for('list_campaigns'))
    
    return render_template('campaign_detail.html', campaign=campaign)

# Add more routes from your ui.py file, adapting them to use the service layer...

def main():
    try:
        print("Starting LinkedIn Bot web interface...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        log_error("Failed to start Flask application", e)
        print("\nApplication failed to start. Check error_log.txt for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()

@app.route('/posts_for_review')
def posts_for_review():
    """Show posts that need review"""
    try:
        posts = PostService.get_posts_for_review()
        return render_template('posts_for_review.html', posts=posts)
    except Exception as e:
        log_error("Error retrieving posts for review", e)
        flash("Could not retrieve posts for review. See error log for details.", "warning")
        return redirect(url_for('index'))

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    """Edit a post"""
    if request.method == 'POST':
        new_text = request.form.get('post_text')
        
        try:
            success = PostService.update_post(post_id, new_text)
            if success:
                flash(f'Post {post_id} updated successfully', 'success')
            else:
                flash(f'Failed to update post {post_id}', 'danger')
        except Exception as e:
            log_error(f"Error updating post {post_id}", e)
            flash(f"Error updating post: {str(e)}", "danger")
            
        return redirect(url_for('posts_for_review'))
    
    # For GET request, show the edit form
    post = PostService.get_post(post_id)
    if not post:
        flash('Post not found', 'danger')
        return redirect(url_for('posts_for_review'))
    
    return render_template('edit_post.html', 
                          post_id=post_id, 
                          post_text=post['text'], 
                          scheduled_time=post['scheduled_time'])

@app.route('/approve_post/<int:post_id>', methods=['POST'])
def approve_post(post_id):
    """Approve a post"""
    try:
        success = PostService.approve_post(post_id)
        if success:
            flash(f'Post {post_id} approved', 'success')
        else:
            flash(f'Failed to approve post {post_id}', 'danger')
    except Exception as e:
        log_error(f"Error approving post {post_id}", e)
        flash(f"Error approving post: {str(e)}", "danger")
        
    return redirect(url_for('posts_for_review'))

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    """Delete a post"""
    try:
        success = PostService.delete_post(post_id)
        if success:
            flash(f'Post {post_id} deleted', 'success')
        else:
            flash(f'Failed to delete post {post_id}', 'danger')
    except Exception as e:
        log_error(f"Error deleting post {post_id}", e)
        flash(f"Error deleting post: {str(e)}", "danger")
        
    return redirect(url_for('index'))

# Content Repository Routes
@app.route('/repository')
def content_repository():
    """Show content repository"""
    try:
        content = ContentService.get_all_content()
        return render_template('repository.html', content=content)
    except Exception as e:
        log_error("Error retrieving content repository", e)
        flash("Could not retrieve content repository. See error log for details.", "warning")
        return redirect(url_for('index'))

@app.route('/add_content', methods=['GET', 'POST'])
def add_content():
    """Add content to repository"""
    if request.method == 'POST':
        post_text = request.form.get('post_text')
        category = request.form.get('category')
        
        if not category or category.strip() == "":
            category = None
            
        try:
            content_id = ContentService.add_content(post_text, category)
            flash(f'Content added to repository with ID: {content_id}', 'success')
            return redirect(url_for('content_repository'))
        except Exception as e:
            log_error("Error adding content to repository", e)
            flash(f"Error adding content: {str(e)}", "danger")
    
    # For GET request, show the add form
    try:
        categories = ContentService.get_categories()
        return render_template('add_content.html', categories=categories)
    except Exception as e:
        log_error("Error retrieving categories", e)
        flash("Could not retrieve categories. See error log for details.", "warning")
        return render_template('add_content.html', categories=[])

@app.route('/import_csv', methods=['GET', 'POST'])
def import_csv():
    """Import content from CSV file"""
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file:
            try:
                file_data = file.read()
                count = ContentService.import_from_uploaded_file(file_data)
                flash(f'Successfully imported {count} posts from CSV', 'success')
                return redirect(url_for('content_repository'))
            except Exception as e:
                log_error("Error importing CSV", e)
                flash(f'Error importing CSV: {str(e)}', 'danger')
    
    return render_template('import_csv.html')

@app.route('/reset_content/<int:content_id>', methods=['POST'])
def reset_content(content_id):
    """Reset content to allow reuse"""
    try:
        success = ContentService.reset_content(content_id)
        if success:
            flash(f'Content {content_id} reset for reuse', 'success')
        else:
            flash(f'Failed to reset content {content_id}', 'danger')
    except Exception as e:
        log_error(f"Error resetting content {content_id}", e)
        flash(f"Error resetting content: {str(e)}", "danger")
        
    return redirect(url_for('content_repository'))

@app.route('/reset_all_content', methods=['POST'])
def reset_all_content():
    """Reset all content to allow reuse"""
    try:
        success = ContentService.reset_content()
        if success:
            flash('All content reset for reuse', 'success')
        else:
            flash('Failed to reset content', 'danger')
    except Exception as e:
        log_error("Error resetting all content", e)
        flash(f"Error resetting content: {str(e)}", "danger")
        
    return redirect(url_for('content_repository'))    