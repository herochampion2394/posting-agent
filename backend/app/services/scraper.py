import httpx
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime, timedelta

class WebScraper:
    async def get_trending_topics(self, sources: List[str] = None) -> List[Dict]:
        """
        Scrape trending topics from various sources.
        
        Args:
            sources: List of sources to scrape (e.g., ["twitter", "google"])
        
        Returns:
            List of trending topics with descriptions
        """
        if sources is None:
            sources = ["google"]
        
        all_trends = []
        
        for source in sources:
            if source == "google":
                trends = await self._scrape_google_trends()
                all_trends.extend(trends)
        
        return all_trends
    
    async def _scrape_google_trends(self) -> List[Dict]:
        """
        Scrape Google Trends daily trends.
        """
        try:
            url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.content, "xml")
                items = soup.find_all("item")
                
                trends = []
                for item in items[:10]:  # Get top 10
                    title = item.find("title").text if item.find("title") else ""
                    description = item.find("description").text if item.find("description") else ""
                    link = item.find("link").text if item.find("link") else ""
                    
                    # Extract traffic volume if available
                    traffic = item.find("ht:approx_traffic")
                    volume = int(traffic.text.replace("+", "").replace(",", "")) if traffic else 0
                    
                    trends.append({
                        "platform": "google",
                        "topic": title,
                        "description": description,
                        "url": link,
                        "volume": volume,
                        "scraped_at": datetime.utcnow(),
                        "expires_at": datetime.utcnow() + timedelta(hours=24)
                    })
                
                return trends
        except Exception as e:
            print(f"Google Trends scraping failed: {e}")
            return []
    
    async def scrape_url_content(self, url: str) -> Dict:
        """
        Scrape content from a specific URL.
        Useful for users who want to extract content from articles/blogs.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0, follow_redirects=True)
                
                if response.status_code != 200:
                    return {"error": "Failed to fetch URL"}
                
                soup = BeautifulSoup(response.content, "html.parser")
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get title
                title = soup.find("title")
                title_text = title.text if title else ""
                
                # Get main content (try common article tags)
                content_tags = soup.find_all(["article", "main", "p"])
                content = " ".join([tag.get_text() for tag in content_tags])
                
                # Clean up whitespace
                content = " ".join(content.split())
                
                return {
                    "url": url,
                    "title": title_text,
                    "content": content[:5000],  # Limit to 5000 chars
                    "scraped_at": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {"error": str(e)}
