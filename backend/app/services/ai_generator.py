from openai import OpenAI
import os
from typing import List, Optional

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AIContentGenerator:
    def __init__(self):
        self.model = "gpt-4o-mini"
    
    async def generate_post(
        self,
        platform: str,
        knowledge_base: Optional[List[str]] = None,
        trending_topics: Optional[List[str]] = None,
        custom_prompt: Optional[str] = None,
        tone: str = "professional"
    ) -> str:
        """
        Generate social media post content using AI.
        
        Args:
            platform: "twitter" or "tiktok"
            knowledge_base: List of knowledge doc contents
            trending_topics: List of trending topic descriptions
            custom_prompt: User's custom instructions
            tone: Tone of the post (professional, casual, funny, etc.)
        """
        # Build context from knowledge base
        kb_context = ""
        if knowledge_base:
            kb_context = "\n\nKnowledge Base Context:\n" + "\n".join(knowledge_base[:3])
        
        # Build trending topics context
        trending_context = ""
        if trending_topics:
            trending_context = "\n\nTrending Topics to Consider:\n" + "\n".join(trending_topics[:5])
        
        # Platform-specific instructions
        platform_instructions = {
            "twitter": "Create an engaging tweet (max 280 characters). Include relevant hashtags.",
            "tiktok": "Create a compelling TikTok caption with hooks and trending hashtags. Keep it engaging and brief."
        }
        
        system_prompt = f"""You are a social media content creator specializing in {platform} posts.
Your goal is to create engaging, authentic content that resonates with the audience.

Tone: {tone}
Platform: {platform}
Instructions: {platform_instructions.get(platform, "Create engaging social media content.")}

Guidelines:
- Be authentic and valuable
- Use emojis sparingly and naturally
- Include 2-3 relevant hashtags
- Keep it concise and impactful
- Don't use overly promotional language"""
        
        user_prompt = f"""Create a {platform} post.
{kb_context}
{trending_context}

{f'Custom Instructions: {custom_prompt}' if custom_prompt else ''}

Generate only the post content, no explanations."""
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")
    
    async def generate_multiple_posts(
        self,
        count: int,
        platform: str,
        **kwargs
    ) -> List[str]:
        """Generate multiple post variations."""
        posts = []
        for i in range(count):
            post = await self.generate_post(platform=platform, **kwargs)
            posts.append(post)
        return posts
    
    async def improve_post(self, original_post: str, feedback: str) -> str:
        """Improve an existing post based on feedback."""
        prompt = f"""Original post:
{original_post}

Feedback: {feedback}

Please improve the post based on the feedback. Return only the improved post."""
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a social media content editor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Post improvement failed: {str(e)}")
