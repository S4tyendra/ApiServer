import requests
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urljoin, urlparse
import re
from typing import Optional, Tuple, List, Dict
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os
import socket

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WebToMarkdown:
    def __init__(
            self,
            include_images: bool = False,
            max_length: Optional[int] = None,
            timeout: Optional[int] = None,
            wait_after_load: Optional[int] = None,
            gather_links_at_end: bool = False,
            use_image_captions: bool = False,
            browser_locale: str = "en-US",
            enable_iframe_extraction: bool = False,
            max_retries: int = 3,
            retry_delay: int = 5
    ):
        """
        Initialize WebToMarkdown converter with various options

        Args:
            include_images: Whether to include image references in markdown
            max_length: Maximum length of output text
            timeout: Request timeout in seconds
            wait_after_load: Seconds to wait after page load (for JavaScript content)
            gather_links_at_end: Collect all links at the end of the document
            use_image_captions: Use image alt text instead of URLs
            browser_locale: Browser locale for requests
            enable_iframe_extraction: Whether to extract content from iframes
            max_retries: Maximum number of retries for driver creation
            retry_delay: Delay between retries in seconds
        """
        self.include_images = include_images
        self.max_length = max_length
        self.timeout = timeout or 30
        self.wait_after_load = min(30, wait_after_load) if wait_after_load else None
        self.gather_links_at_end = gather_links_at_end
        self.use_image_captions = use_image_captions
        self.browser_locale = browser_locale
        self.enable_iframe_extraction = enable_iframe_extraction
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.collected_links: Dict[str, str] = {}
        self.base_domain: Optional[str] = None

        self.h2t = html2text.HTML2Text()
        self.configure_html2text()

    def configure_html2text(self):
        """Configure html2text settings for optimal markdown conversion"""
        self.h2t.ignore_links = False
        self.h2t.ignore_images = not self.include_images
        self.h2t.ignore_tables = False
        self.h2t.body_width = 0  # Don't wrap text
        self.h2t.protect_links = True
        self.h2t.unicode_snob = True  # Use Unicode instead of ASCII
        self.h2t.wrap_links = False
        self.h2t.emphasis_mark = '*'
        self.h2t.links_each_paragraph = False

    def clean_text(self, text: str) -> str:
        """Clean up the converted markdown text"""
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\t+', ' ', text)
        text = re.sub(r'\[!\[\]\(([^\)]+)\)\]', r'![\1](\1)', text)
        text = re.sub(r'\n\s*\*\s*\n', '\n\n', text)
        if self.use_image_captions:
            text = re.sub(r'!\[(.*?)\]\(.*?\)', r'![Image: \1]()', text)
        if self.gather_links_at_end and self.collected_links:
            text += "\n\n---\n\n### References\n\n"
            for name, url in self.collected_links.items():
                if self.base_domain in url:
                    text += f"[{name}]({url})\n"
        if self.max_length and len(text) > self.max_length:
            text = text[:self.max_length].rsplit('\n', 1)[0] + '\n\n[Content truncated...]'
        return text.strip()

    def extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Extract the main content from the webpage, removing navigation, ads, etc."""
        unwanted_tags = [
            'script', 'style', 'nav', 'footer', 'header',
            'aside', 'noscript', 'meta', 'button', 'svg', 'path'
        ]
        if not self.enable_iframe_extraction:
            unwanted_tags.append('iframe')

        unwanted_classes = [
            'ads', 'advertisement', 'social-share', 'nav', 'navbar',
            'menu', 'footer', 'header', 'sidebar', 'cookie', 'popup'
        ]
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()

        for class_name in unwanted_classes:
            for element in soup.find_all(class_=re.compile(class_name, re.I)):
                element.decompose()

        if self.enable_iframe_extraction:
            for iframe in soup.find_all('iframe'):
                try:
                    iframe_url = iframe.get('src', '')
                    if iframe_url:
                        iframe_content = self.fetch_url(iframe_url)[0]
                        if iframe_content:
                            iframe_soup = BeautifulSoup(iframe_content, 'html.parser')
                            iframe.replace_with(iframe_soup.body or iframe_soup)
                except Exception:
                    iframe.decompose()
        return soup

    def collect_link(self, name: str, url: str):
        """Collect links for end-of-document reference"""
        if self.gather_links_at_end:
            name = re.sub(r'\s+', ' ', name).strip()
            url = url.strip()
            if name and url:
                self.collected_links[name] = url

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except socket.error:
                return False

    def _get_available_port(self, start_port: int = 9515) -> int:
        """Find an available port starting from the given port number."""
        port = start_port
        while not self._is_port_available(port) and port < start_port + 1000:
            port += 1
        if port >= start_port + 1000:
            raise RuntimeError("No available ports found")
        return port

    def create_chrome_driver(self):
        """Create and configure Chrome webdriver with robust error handling and retries"""
        for attempt in range(self.max_retries):
            try:
                # Configure Chrome options
                chrome_options = ChromeOptions()
                chrome_options.add_argument('--headless=new')  # Use new headless mode
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_optionfalses.add_argument('--disable-gpu')
                chrome_options.add_argument(f'--lang={self.browser_locale}')
                chrome_options.add_argument('--disable-notifications')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-infobars')

                # Additional stability options
                chrome_options.add_argument('--disable-features=NetworkService')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--start-maximized')
                chrome_options.add_argument('--ignore-certificate-errors')

                # Find an available port
                port = self._get_available_port()
                logger.info(f"Attempting to start Chrome driver on port {port}")

                # Create Chrome service with the available port
                service = ChromeService(
                    log_path=os.path.join(os.getcwd(), "chromedriver.log.txt")
                )

                # Initialize the driver
                driver = webdriver.Chrome(
                    service=service,
                    options=chrome_options
                )

                # Set various timeouts
                driver.set_page_load_timeout(self.timeout)
                driver.implicitly_wait(self.timeout)

                # Verify driver is responsive
                driver.current_url  # This will raise an exception if driver isn't responding

                logger.info("Chrome driver created successfully")
                return driver

            except WebDriverException as e:
                logger.error(f"WebDriver error on attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                self._cleanup_driver(driver) if 'driver' in locals() else None
                import traceback
                traceback.print_exc()

            except TimeoutException as e:
                logger.error(f"Timeout error on attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                self._cleanup_driver(driver) if 'driver' in locals() else None

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                self._cleanup_driver(driver) if 'driver' in locals() else None

            if attempt < self.max_retries - 1:
                logger.info(f"Waiting {self.retry_delay} seconds before retry...")
                time.sleep(self.retry_delay)
        raise RuntimeError("Failed to create Chrome driver after all retry attempts")

    def _cleanup_driver(self, driver):
        """Safely clean up the driver instance"""
        try:
            if driver:
                driver.quit()
        except Exception as e:
            logger.warning(f"Error during driver cleanup: {e}")

    def fetch_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Fetch URL content and handle errors"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': self.browser_locale
            }

            if self.wait_after_load:
                driver = None
                try:
                    driver = self.create_chrome_driver()
                    if not driver:
                        raise Exception("Failed to initialize Chrome driver")

                    logger.info(f"Fetching URL with Chrome: {url}")
                    driver.get(url)

                    if self.wait_after_load:
                        time.sleep(self.wait_after_load)

                    content = driver.page_source
                    logger.info("Successfully retrieved page content")
                    return content, 'utf-8'

                except Exception as e:
                    logger.error(f"Error during Selenium fetch: {e}")
                    logger.info("Falling back to requests method")
                    response = requests.get(url, headers=headers, timeout=self.timeout)
                    response.raise_for_status()
                    return response.text, response.apparent_encoding

                finally:
                    if driver:
                        self._cleanup_driver(driver)

            else:
                response = requests.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response.text, response.apparent_encoding

        except Exception as e:
            logger.error(f"Error fetching URL: {e}")
            return f"Error fetching URL: {e}", f"Error fetching URL: {e}"

    def convert_url_to_markdown(self, url: str) -> Optional[str]:
        """Convert a webpage to Markdown format"""
        self.base_domain = urlparse(url).netloc
        self.collected_links = {}

        html_content, encoding = self.fetch_url(url)
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else ''
        soup = self.extract_main_content(soup)

        if self.gather_links_at_end:
            for a in soup.find_all('a', href=True):
                self.collect_link(a.get_text(), urljoin(url, a['href']))

        markdown = self.h2t.handle(str(soup))
        header = f"# {title}\n\nSource: {url}\n\n---\n\n"
        markdown = header + markdown
        markdown = self.clean_text(markdown)

        return markdown