import requests
from linkedin_token import ACCESS_TOKEN  # Changed from "token" to "linkedin_token"

def create_linkedin_post(post_text):
    """Create a simple text post on LinkedIn"""
    
    print(f"Attempting to post: {post_text}")
    
    # LinkedIn API endpoint for posting
    post_url = "https://api.linkedin.com/v2/ugcPosts"
    
    # Headers with your access token
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    # Get user URN (required for posting)
    user_info_url = "https://api.linkedin.com/v2/me"
    user_response = requests.get(user_info_url, headers=headers)
    
    if user_response.status_code != 200:
        print(f"Error getting user info: {user_response.status_code}")
        print(user_response.text)
        return False
    
    user_data = user_response.json()
    user_urn = f"urn:li:person:{user_data['id']}"
    print(f"Found user URN: {user_urn}")
    
    # Create the post payload
    post_data = {
        "author": user_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    # Make the API call to create the post
    response = requests.post(post_url, headers=headers, json=post_data)
    
    if response.status_code == 201:
        print("Post created successfully!")
        return True
    else:
        print(f"Error creating post: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    # Test post
    create_linkedin_post("This is a test post from my LinkedIn automation bot! #learning #pythondevelopment")