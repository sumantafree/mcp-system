"""
MCP 7: Website Agent
- Broken link detection
- Auto page generation
- Performance analysis
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
from agents.base_agent import BaseMCPAgent
from database import models
from datetime import datetime
from urllib.parse import urljoin, urlparse


WEBSITE_SYSTEM_PROMPT = """You are a web developer and SEO specialist.
You audit websites for technical issues, performance, and SEO problems.
You provide actionable fixes and optimization strategies."""


class WebsiteAgent(BaseMCPAgent):
    MODULE_NAME = "website"

    async def scan_broken_links(self, website_url: str, max_pages: int = 50) -> dict:
        """Crawl website and detect broken links."""
        visited = set()
        broken_links = []
        to_visit = [website_url]
        base_domain = urlparse(website_url).netloc

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            pages_crawled = 0
            while to_visit and pages_crawled < max_pages:
                url = to_visit.pop(0)
                if url in visited:
                    continue
                visited.add(url)
                pages_crawled += 1

                try:
                    response = await client.get(url)
                    if response.status_code >= 400:
                        broken_links.append({
                            "url": url,
                            "status_code": response.status_code,
                            "source": "direct",
                        })
                        continue

                    if "text/html" not in response.headers.get("content-type", ""):
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")
                    for tag in soup.find_all("a", href=True):
                        href = tag["href"]
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)
                        if parsed.netloc == base_domain and full_url not in visited:
                            to_visit.append(full_url)

                except Exception as e:
                    broken_links.append({
                        "url": url,
                        "status_code": 0,
                        "error": str(e),
                        "source": "crawl_error",
                    })

        # Save broken links to DB
        for link in broken_links:
            bl = models.BrokenLink(
                source_url=website_url,
                broken_url=link["url"],
                status_code=link.get("status_code"),
                owner_id=self.user_id,
            )
            self.db.add(bl)
        self.db.commit()

        self.track_event("website_scanned", {
            "url": website_url,
            "pages_crawled": pages_crawled,
            "broken_count": len(broken_links),
        })

        return {
            "website_url": website_url,
            "pages_crawled": pages_crawled,
            "broken_links": broken_links,
            "broken_count": len(broken_links),
        }

    async def generate_page(
        self,
        page_type: str,
        keyword: str,
        business_info: dict,
        language: str = "en",
    ) -> dict:
        """Auto-generate a web page with AI."""
        prompt = f"""Generate a complete {page_type} page:

Target Keyword: {keyword}
Business: {business_info.get('name', 'Our Business')}
Industry: {business_info.get('industry', 'General')}
Language: {"Hindi" if language == "hi" else "English"}

Return JSON:
{{
  "page_title": "...",
  "slug": "url-slug",
  "meta_title": "...",
  "meta_description": "...",
  "content": "full HTML page content",
  "sections": [
    {{"section": "hero", "content": "..."}}
  ],
  "schema_markup": {{}}
}}"""
        response = await self.ai.generate(
            prompt, WEBSITE_SYSTEM_PROMPT, temperature=0.75, max_tokens=4096, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("page_generated", {"type": page_type, "keyword": keyword})
        return result

    async def analyze_performance(self, url: str) -> dict:
        """Analyze page performance metrics."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                import time
                start = time.time()
                response = await client.get(url)
                load_time_ms = (time.time() - start) * 1000

                soup = BeautifulSoup(response.text, "html.parser")
                images = soup.find_all("img")
                scripts = soup.find_all("script")
                styles = soup.find_all("link", rel="stylesheet")

                # Basic analysis
                has_title = bool(soup.find("title"))
                has_meta_desc = bool(soup.find("meta", attrs={"name": "description"}))
                has_h1 = bool(soup.find("h1"))
                img_without_alt = [img for img in images if not img.get("alt")]

                perf_score = 100
                perf_score -= min(40, load_time_ms / 100)  # deduct for slow load
                perf_score -= len(scripts) * 2
                perf_score -= len(img_without_alt) * 3
                perf_score = max(0, perf_score)

                return {
                    "url": url,
                    "status_code": response.status_code,
                    "load_time_ms": round(load_time_ms, 2),
                    "performance_score": round(perf_score),
                    "seo": {
                        "has_title": has_title,
                        "has_meta_description": has_meta_desc,
                        "has_h1": has_h1,
                        "images_without_alt": len(img_without_alt),
                    },
                    "resources": {
                        "images": len(images),
                        "scripts": len(scripts),
                        "stylesheets": len(styles),
                    },
                    "page_size_kb": round(len(response.content) / 1024, 2),
                }
        except Exception as e:
            return {"url": url, "error": str(e)}

    async def generate_optimization_plan(self, scan_result: dict) -> str:
        """Generate AI optimization recommendations."""
        prompt = f"""Based on this website scan, create a prioritized optimization plan:

{scan_result}

Provide 5-7 specific, actionable recommendations ranked by impact.
Focus on quick wins first, then long-term improvements."""
        return await self.ai.generate(prompt, WEBSITE_SYSTEM_PROMPT)
