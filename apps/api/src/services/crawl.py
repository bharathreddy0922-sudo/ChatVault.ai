import asyncio
import logging
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urljoin, urlparse
import re
import requests
import trafilatura
from ..config import settings

logger = logging.getLogger(__name__)


class WebCrawler:
    def __init__(self):
        self.max_depth = settings.max_crawl_depth
        self.max_urls = settings.max_urls_per_crawl
        self.timeout = settings.crawl_timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    async def crawl_url(self, root_url: str, depth: int = None, render_js: bool = False) -> Dict[str, Any]:
        """Crawl a URL and extract content"""
        if depth is None:
            depth = self.max_depth
        
        try:
            if render_js and settings.enable_playwright:
                return await self._crawl_with_playwright(root_url, depth)
            else:
                return await self._crawl_with_requests(root_url, depth)
                
        except Exception as e:
            logger.error(f"Error crawling {root_url}: {e}")
            raise
    
    async def _crawl_with_requests(self, root_url: str, depth: int) -> Dict[str, Any]:
        """Crawl using requests + trafilatura (lightweight)"""
        crawled_urls = []
        visited_urls = set()
        
        await self._crawl_recursive_requests(root_url, depth, 0, crawled_urls, visited_urls)
        
        return {
            'root_url': root_url,
            'crawled_urls': crawled_urls,
            'total_urls': len(crawled_urls),
            'method': 'requests+trafilatura'
        }
    
    async def _crawl_with_playwright(self, root_url: str, depth: int) -> Dict[str, Any]:
        """Crawl using Playwright (optional, heavy)"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                crawled_urls = []
                visited_urls = set()
                
                await self._crawl_recursive_playwright(page, root_url, depth, 0, crawled_urls, visited_urls)
                
                await browser.close()
                
                return {
                    'root_url': root_url,
                    'crawled_urls': crawled_urls,
                    'total_urls': len(crawled_urls),
                    'method': 'playwright'
                }
                
        except ImportError:
            logger.warning("Playwright not available, falling back to requests")
            return await self._crawl_with_requests(root_url, depth)
    
    async def _crawl_recursive_requests(self, url: str, max_depth: int, current_depth: int,
                                      crawled_urls: List[Dict[str, Any]], visited_urls: Set[str]):
        """Recursively crawl URLs using requests"""
        if current_depth > max_depth or len(crawled_urls) >= self.max_urls:
            return
        
        if url in visited_urls:
            return
        
        visited_urls.add(url)
        
        try:
            # Fetch the page
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Extract content using trafilatura
            extracted = trafilatura.extract(response.text, include_formatting=True)
            
            if extracted and extracted.strip():
                # Get title
                title = trafilatura.extract_metadata(response.text).get('title', 'Untitled')
                
                crawled_urls.append({
                    'url': url,
                    'title': title,
                    'text': extracted,
                    'depth': current_depth
                })
            
            # Find links for next level
            if current_depth < max_depth and len(crawled_urls) < self.max_urls:
                links = self._extract_links_from_html(response.text, url)
                
                for link in links[:5]:  # Limit links per page
                    if len(crawled_urls) >= self.max_urls:
                        break
                    await self._crawl_recursive_requests(link, max_depth, current_depth + 1,
                                                       crawled_urls, visited_urls)
                    
        except Exception as e:
            logger.warning(f"Error crawling {url}: {e}")
    
    async def _crawl_recursive_playwright(self, page, url: str, max_depth: int, current_depth: int,
                                        crawled_urls: List[Dict[str, Any]], visited_urls: Set[str]):
        """Recursively crawl URLs using Playwright"""
        if current_depth > max_depth or len(crawled_urls) >= self.max_urls:
            return
        
        if url in visited_urls:
            return
        
        visited_urls.add(url)
        
        try:
            # Navigate to the page
            await page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
            
            # Extract content
            title = await page.title()
            content = await page.content()
            
            # Use trafilatura for content extraction
            extracted = trafilatura.extract(content, include_formatting=True)
            
            if extracted and extracted.strip():
                crawled_urls.append({
                    'url': url,
                    'title': title,
                    'text': extracted,
                    'depth': current_depth
                })
            
            # Find links for next level
            if current_depth < max_depth and len(crawled_urls) < self.max_urls:
                links = await self._extract_links_playwright(page, url)
                
                for link in links[:5]:  # Limit links per page
                    if len(crawled_urls) >= self.max_urls:
                        break
                    await self._crawl_recursive_playwright(page, link, max_depth, current_depth + 1,
                                                         crawled_urls, visited_urls)
                    
        except Exception as e:
            logger.warning(f"Error crawling {url}: {e}")
    
    def _extract_links_from_html(self, html: str, base_url: str) -> List[str]:
        """Extract links from HTML using regex (lightweight)"""
        try:
            # Simple regex to find href attributes
            href_pattern = r'href=["\']([^"\']+)["\']'
            matches = re.findall(href_pattern, html, re.IGNORECASE)
            
            valid_links = []
            base_domain = urlparse(base_url).netloc
            
            for link in matches:
                if not link:
                    continue
                
                # Parse the link
                parsed = urlparse(link)
                
                # Only follow links from the same domain
                if parsed.netloc == base_domain:
                    # Normalize the URL
                    normalized = urljoin(base_url, link)
                    
                    # Skip anchors, javascript, etc.
                    if self._is_valid_url(normalized):
                        valid_links.append(normalized)
            
            return list(set(valid_links))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    async def _extract_links_playwright(self, page, base_url: str) -> List[str]:
        """Extract links using Playwright"""
        try:
            links = await page.eval_on_selector_all('a[href]', '''
                (elements) => elements.map(el => el.href)
            ''')
            
            valid_links = []
            base_domain = urlparse(base_url).netloc
            
            for link in links:
                if not link:
                    continue
                
                parsed = urlparse(link)
                if parsed.netloc == base_domain:
                    normalized = urljoin(base_url, link)
                    if self._is_valid_url(normalized):
                        valid_links.append(normalized)
            
            return list(set(valid_links))
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid for crawling"""
        if not url:
            return False
        
        # Skip anchors, javascript, mailto, etc.
        invalid_schemes = ['javascript:', 'mailto:', 'tel:', '#']
        for scheme in invalid_schemes:
            if url.startswith(scheme):
                return False
        
        # Skip file extensions that are not web pages
        invalid_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.css', '.js']
        for ext in invalid_extensions:
            if url.lower().endswith(ext):
                return False
        
        return True
    
    def process_crawled_content(self, crawled_data: Dict[str, Any]) -> str:
        """Process crawled content into a single text document"""
        try:
            content_parts = []
            
            for url_data in crawled_data['crawled_urls']:
                title = url_data['title']
                text = url_data['text']
                url = url_data['url']
                
                # Add URL and title as section header
                content_parts.append(f"# {title}")
                content_parts.append(f"Source: {url}")
                content_parts.append("")
                content_parts.append(text)
                content_parts.append("")
                content_parts.append("---")
                content_parts.append("")
            
            return '\n'.join(content_parts)
            
        except Exception as e:
            logger.error(f"Error processing crawled content: {e}")
            return ""
