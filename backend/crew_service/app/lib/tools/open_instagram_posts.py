import sys
import time
from pathlib import Path
from typing import Any, Awaitable, Callable, Coroutine, Dict, List, Optional, Union
from urllib.parse import urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

# Add project root to path when running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from app.lib.tools.playwright_utils import fetch_page_with_playwright, BrowserConfig
from config import settings

# -------------------- Config --------------------
DEFAULT_SLEEP_SECONDS = 0.5
REQUEST_TIMEOUT = 20

# --- Instagram UI selectors (conservative) ---
CAPTION_CSS_STRICT = (
    "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.xt0psk2.x1i0vuye.xvs91rp.xo1l8bm."
    "x5n08af.x10wh9bi.xpm28yp.x8viiok.x1o7cslx.x126k92a"
)
USERNAME_CSS_STRICT = (
    "div.html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69"
    ".x1c1uobl.x9f619.xjbqb8w.x78zum5.x15mokao.x1ga7v0g.x16uus16.xbiv7yw"
    ".x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x1qjc9v5"
    ".x1oa3qoh.x1nhvcw1 span._ap3a._aaco._aacw._aacx._aad7._aade"
)
CAROUSEL_NEXT_CSS = "button[aria-label='Next']"
CONTENT_CSS = "ul._acay"

# -------------------- Helpers --------------------

def _canonical_ig_url(u: str) -> str:
    parts = urlsplit(u.strip())
    path = parts.path
    if not path.endswith("/"):
        path += "/"
    return urlunsplit((parts.scheme or "https", parts.netloc or "www.instagram.com", path, "", ""))

def _requests_fetch(url: str, timeout: int = REQUEST_TIMEOUT, retries: int = 1) -> Optional[str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1",
    }
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200 and "<html" in resp.text.lower():
                return resp.text
        except Exception:
            pass
        time.sleep(0.2 * (attempt + 1))
    return None

def _best_img_url(img) -> Optional[str]:
    src = (img.get("src") or "").strip()
    srcset = (img.get("srcset") or "").strip()
    if srcset:
        parts = [p.strip().split(" ") for p in srcset.split(",")]
        urls = [p[0] for p in parts if p]
        if urls:
            return urls[-1]
    if src and not src.startswith("blob:"):
        return src
    return None

def _looks_like_photo(u: str) -> bool:
    u2 = u.lower()
    return ("cdninstagram" in u2) or u2.endswith((".jpg", ".jpeg", ".png", ".webp", ".heic"))

def _extract_from_meta(soup: BeautifulSoup) -> Dict[str, Any]:
    def _get(p: str) -> Optional[str]:
        tag = soup.select_one(f'meta[property="{p}"]')
        val = tag.get("content") if tag else None
        return val.strip() if isinstance(val, str) else None

    desc = _get("og:description")
    if desc:
        desc = desc.replace('":', ':').replace('".', '.').strip().strip('"')

    img = _get("og:image")
    photos = [img] if img else []
    return {"description": desc, "photo_urls": photos}

def _extract_from_dom(soup: BeautifulSoup) -> Dict[str, Any]:
    description = None
    caption_node = soup.select_one(CAPTION_CSS_STRICT)
    if caption_node:
        description = caption_node.get_text("\n", strip=True)

    username = None
    username_node = soup.select_one(USERNAME_CSS_STRICT)
    if username_node:
        username = username_node.get_text("\n", strip=True)

    imgs = []
    for img in soup.select("li._acaz img"):
        best = _best_img_url(img)
        if best:
            imgs.append(best)
    imgs = list(dict.fromkeys([u for u in imgs if _looks_like_photo(u)]))

    return {"username": username, "description": description, "photo_urls": imgs}

def _create_instagram_carousel_interaction() -> Callable[[Any], Coroutine[Any, Any, List[str]]]:
    """Create a page interaction function for Instagram carousel navigation.
    
    Returns:
        An async function that can be passed to fetch_page_with_playwright to interact
        with Instagram carousels and collect media URLs.
    """
    async def _collect_media_now(page) -> List[str]:
        """Collect media URLs from the current carousel state."""
        js = """
        (sel) => {
          const ul = document.querySelector(sel);
          if (!ul) return [];
          const pick = (el) => {
            const s = el.currentSrc || el.src || (el.srcset ? el.srcset.split(',').pop().trim().split(' ')[0] : '');
            return s || '';
          };
          const nodes = [
            ...ul.querySelectorAll(':scope > li img'),
            ...ul.querySelectorAll(':scope > li video'),
            ...ul.querySelectorAll(':scope > li video source'),
          ];
          const urls = nodes.map(pick).filter(Boolean).filter(u => !u.startsWith('blob:'));
          const seen = new Set();
          return urls.filter(u => (seen.has(u) ? false : (seen.add(u), true)));
        }
        """
        return await page.evaluate(js, CONTENT_CSS)

    async def _click_through_carousel(page, max_clicks: int = 30, pause_ms: int = 300) -> List[str]:
        """Click through Instagram carousel to collect all media URLs."""
        seen: List[str] = []
        seen_set: set[str] = set()

        # Collect initial media
        initial_media = await _collect_media_now(page)
        for u in initial_media:
            if u not in seen_set:
                seen_set.add(u)
                seen.append(u)

        # Click through carousel
        clicks = 0
        while clicks < max_clicks:
            btn = page.locator(CAROUSEL_NEXT_CSS).first
            if await btn.count() == 0:
                break

            progressed = False
            attempts = [
                lambda: btn.click(timeout=700),
                lambda: page.keyboard.press("ArrowRight"),
            ]
            for attempt in attempts:
                try:
                    await attempt()
                except Exception:
                    pass
                await page.wait_for_timeout(pause_ms)
                new = []
                new_media = await _collect_media_now(page)
                for u in new_media:
                    if u not in seen_set:
                        seen_set.add(u)
                        new.append(u)
                if new:
                    seen.extend(new)
                    progressed = True
                    break
            if not progressed:
                break
            clicks += 1
        return seen
    
    return _click_through_carousel

async def _get_html(url: str) -> Optional[tuple[str, List[str]]]:
    """Fetch HTML content from URL, trying Playwright first, then falling back to requests.
    
    Args:
        url: URL to fetch
        
    Returns:
        Tuple of (HTML content, media URLs) or None if fetch fails
    """

    try:
        config = BrowserConfig(headless=settings.HEADLESS)
        carousel_interaction = _create_instagram_carousel_interaction()
        result = await fetch_page_with_playwright(
            url,
            timeout_ms=settings.PLAYWRIGHT_TIMEOUT_MS,
            config=config,
            page_interaction=carousel_interaction,
        )
        if result:
            return result
    except Exception as e:
        pass

    html = _requests_fetch(url)
    if html:
        return (html, [])
    return None

async def _scrape_one(url: str, sleep_seconds: float = DEFAULT_SLEEP_SECONDS) -> Dict[str, Any]:
    out = {"post_url": url, "username": None, "description": None, "photo_urls": [], "error": None}
    try:
        canon = _canonical_ig_url(url)
        pack = await _get_html(canon)
        if not pack:
            out["error"] = "fetch_failed"
            return out

        html, pw_media = pack
        soup = BeautifulSoup(html, "html.parser")

        caption: Optional[str] = None
        images: List[str] = list(pw_media) if pw_media else []
        
        # 1) Use Playwright-harvested media first
        images = pw_media

        # 2) Use Hydrated DOM to get caption and fallback images
        dom = _extract_from_dom(soup)
        caption = dom.get("description")
        username = dom.get("username")
        if len(images) == 0:
            for u in dom.get("photo_urls", []):
                if u not in images and _looks_like_photo(u):
                    images.append(u)

        # 3) Meta fallbacks
        meta = _extract_from_meta(soup)
        if not caption and meta.get("description"):
            caption = meta["description"]
        for u in meta.get("photo_urls", []):
            if u not in images and _looks_like_photo(u):
                images.append(u)

        out["description"] = caption
        out["username"] = username
        out["photo_urls"] = images
        if not caption and not images:
            out["error"] = "no_data_found"

    except Exception as e:
        out["error"] = f"exception:{type(e).__name__}"
    finally:
        time.sleep(sleep_seconds)

    return out

def _coerce_urls(maybe_urls: Union[str, List[str]]) -> List[str]:
    if isinstance(maybe_urls, list):
        items = [u.strip() for u in maybe_urls if isinstance(u, str) and u.strip()]
    elif isinstance(maybe_urls, str):
        raw = maybe_urls.replace(",", " ").replace("\n", " ")
        items = [u.strip() for u in raw.split(" ") if u.strip()]
    else:
        items = []
    return list(dict.fromkeys(items))

# -------------------- CrewAI tool entrypoint --------------------
@tool("open instagram posts")
def open_instagram_posts(urls: Union[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Opens and extracts poster's username, caption and image URLs from one or more Instagram post pages.
    
    The AI Agent can use this tool to scrape public Instagram post pages to retrieve
    the poster's username, main caption text and all associated image URLs.

    Args:
        website_urls: Either
            - List[str] of Instagram post URLs, or
            - A single string with URLs separated by commas, spaces, or newlines.

    Returns:
        List[Dict]: One dict per input URL:
        {
            "post_url": str,
            "username": Optional[str],
            "description": Optional[str],
            "photo_urls": List[str],
            "error": Optional[str]
        }
    """
    import asyncio
    
    urls = _coerce_urls(urls)
    if not urls:
        return [{
            "post_url": urls if isinstance(urls, str) else None,
            "username": None,
            "description": None,
            "photo_urls": [],
            "error": "invalid_input",
        }]

    # Run async code in the existing event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _scrape_all_async(urls)
                )
                return future.result()
        else:
            return loop.run_until_complete(_scrape_all_async(urls))
    except RuntimeError:
        # No event loop, create a new one
        return asyncio.run(_scrape_all_async(urls))


async def _scrape_all_async(urls: List[str]) -> List[Dict[str, Any]]:
    """Async helper to scrape all URLs."""
    results: List[Dict[str, Any]] = []
    for u in urls:
        results.append(await _scrape_one(u))
    return results

if __name__ == "__main__":
    print(open_instagram_posts.func("https://www.instagram.com/p/DPdB40zk7Xr/"))