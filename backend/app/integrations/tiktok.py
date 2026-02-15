import httpx
from typing import Optional
import os

class TikTokClient:
    def __init__(self, access_token: str):
        """
        Initialize TikTok client with OAuth 2.0 access token.
        
        For production, you'll need:
        - TikTok developer account
        - Client Key and Client Secret
        - Approved for Content Posting API access
        """
        self.access_token = access_token
        self.base_url = "https://open.tiktokapis.com/v2"
    
    async def post_video(
        self,
        video_url: str,
        caption: str,
        privacy_level: str = "PUBLIC_TO_EVERYONE"
    ) -> dict:
        """
        Post a video to TikTok.
        
        Args:
            video_url: URL of the video to post
            caption: Video caption/description
            privacy_level: "PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"
        
        Returns:
            dict with publish_id and status
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "post_info": {
                "title": caption,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_URL",
                "video_url": video_url
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/post/publish/video/init/",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "publish_id": data.get("data", {}).get("publish_id"),
                        "upload_url": data.get("data", {}).get("upload_url")
                    }
                else:
                    return {
                        "success": False,
                        "error": response.text
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_info(self) -> dict:
        """Get authenticated user's TikTok info."""
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/user/info/",
                    headers=headers,
                    params={"fields": "open_id,union_id,avatar_url,display_name"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    user_data = data.get("data", {}).get("user", {})
                    return {
                        "id": user_data.get("open_id"),
                        "username": user_data.get("display_name"),
                        "avatar_url": user_data.get("avatar_url")
                    }
                else:
                    return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

# OAuth helper functions
def get_tiktok_oauth_url() -> str:
    """
    Generate TikTok OAuth URL for user authorization.
    """
    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    redirect_uri = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:3000/auth/tiktok/callback")
    
    scopes = "user.info.basic,video.publish"
    
    oauth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={client_key}"
        f"&scope={scopes}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
    )
    
    return oauth_url

async def exchange_tiktok_code(code: str) -> dict:
    """
    Exchange authorization code for access token.
    """
    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
    redirect_uri = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:3000/auth/tiktok/callback")
    
    payload = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token"),
                    "expires_in": data.get("expires_in"),
                    "token_type": data.get("token_type")
                }
            else:
                return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}
