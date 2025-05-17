import time
from datetime import datetime, timedelta
import scheduler

def main():
    print("Starting LinkedIn Automation Bot")
    print("Press Ctrl+C to exit")
    
    # Initialize scheduler
    linkedin_scheduler = scheduler.LinkedInScheduler()
    
    # Example: Schedule a post for 5 minutes from now
    now = datetime.utcnow()
    post_time = (now + timedelta(minutes=5)).isoformat()
    post_id = linkedin_scheduler.add_post(
        "This is an automated post from my LinkedIn bot! #automation #pythondevelopment", 
        post_time
    )
    print(f"Scheduled post created with ID: {post_id}")
    
    # Run the scheduler loop
    print("Bot is running. Checking for posts every 60 seconds...")
    try:
        while True:
            print(f"\nChecking for posts to publish at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            linkedin_scheduler.check_and_publish()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    
if __name__ == "__main__":
    main()