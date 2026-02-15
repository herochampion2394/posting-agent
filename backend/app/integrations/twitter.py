import tweepy
from typing import Optional, List
import os

class TwitterClient:
    def __init__(self, access_token: str, access_token_secret: str):
        """
        Initialize Twitter client with OAuth 1.0a tokens.
        
        For production, you'll need:
        - TWITTER_API_KEY (Consumer Key)
        - TWITTER_API_SECRET (Consumer Secret)
        - User's access_token and access_token_secret (from OAuth flow)
        """
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        
        # Initialize Tweepy client
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
    
    async def post_tweet(self, text: str, media_ids: Optional[List[str]] = None) -> dict:
        """
        Post a tweet.
        
        Args:
            text: Tweet content (max 280 chars)
            media_ids: List of media IDs (uploaded separately)
        
        Returns:
            dict with tweet_id and tweet_url
        """
        try:
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids
            )
            
            tweet_id = response.data["id"]
            tweet_url = f"https://twitter.com/i/status/{tweet_id}"
            
            return {
                "success": True,
                "tweet_id": tweet_id,
                "tweet_url": tweet_url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_media(self, media_path: str) -> Optional[str]:
        """Upload media and return media_id."""
        try:
            # For media upload, we need API v1.1 with OAuth 1.0a
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            api = tweepy.API(auth)
            
            media = api.media_upload(media_path)
            return media.media_id_string
        except Exception as e:
            print(f"Media upload failed: {e}")
            return None
    
    async def get_user_info(self) -> dict:
        """Get authenticated user's info."""
        try:
            user = self.client.get_me()
            return {
                "id": user.data.id,
                "username": user.data.username,
                "name": user.data.name
            }
        except Exception as e:
            return {"error": str(e)}

# OAuth helper functions
def get_twitter_oauth_url() -> str:
    """
    Generate Twitter OAuth URL for user authorization.
    User should call this to start the OAuth flow.
    """
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    callback_url = os.getenv("TWITTER_CALLBACK_URL", "http://localhost:3000/auth/twitter/callback")
    
    oauth1_user_handler = tweepy.OAuth1UserHandler(
        api_key,
        api_secret,
        callback=callback_url
    )
    
    return oauth1_user_handler.get_authorization_url()

def handle_twitter_callback(oauth_token: str, oauth_verifier: str) -> dict:
    """
    Handle Twitter OAuth callback and exchange for access tokens.
    """
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    
    oauth1_user_handler = tweepy.OAuth1UserHandler(
        api_key,
        api_secret
    )
    
    oauth1_user_handler.request_token = {
        "oauth_token": oauth_token,
        "oauth_token_secret": oauth_verifier
    }
    
    try:
        access_token, access_token_secret = oauth1_user_handler.get_access_token(oauth_verifier)
        return {
            "access_token": access_token,
            "access_token_secret": access_token_secret
        }
    except Exception as e:
        return {"error": str(e)}
