from fastapi import APIRouter
from pydantic import BaseModel

from functions.api.webagent.web2md import WebToMarkdown

web2mdr = APIRouter()


class Web2MdModel(BaseModel):
    url: str
    include_images: bool = False
    max_length: int | None = None
    timeout: int = 30
    wait_after_load: int | None = None
    gather_links_at_end: bool = True
    use_image_captions: bool = True
    browser_locale: str = "en-US"
    enable_iframe_extraction: bool = True
    max_retries: int = 1
    retry_delay: int = 1


@web2mdr.post("/web2md")
async def web2md(web2mddata: Web2MdModel):
    if (
            web2mddata.timeout > 60 or
            (web2mddata.wait_after_load and web2mddata.wait_after_load > 60) or
            web2mddata.max_retries > 5 or
            web2mddata.retry_delay > 5
    ):
        return {
            "error": "Values for timeout, wait_after_load, max_retries, and retry_delay must be less than or equal to 60 and 5, respectively."}
    """
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
    :return:
    string: The markdown content
    """
    convertor = WebToMarkdown(
        include_images=web2mddata.include_images,
        max_length=web2mddata.max_length,
        timeout=web2mddata.timeout,
        wait_after_load=web2mddata.wait_after_load,
        gather_links_at_end=web2mddata.gather_links_at_end,
        use_image_captions=web2mddata.use_image_captions,
        browser_locale=web2mddata.browser_locale,
        enable_iframe_extraction=web2mddata.enable_iframe_extraction,
        max_retries=web2mddata.max_retries,
        retry_delay=web2mddata.retry_delay
    )
    try:
        md = convertor.convert_url_to_markdown(web2mddata.url)
        return md
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

