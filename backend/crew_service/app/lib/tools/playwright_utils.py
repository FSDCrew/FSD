import sys
import traceback
from contextlib import suppress
from typing import Any, Callable, List, Optional, Tuple

from playwright.sync_api import sync_playwright

from config import logger, settings


_playwright_browsers_checked = False


def ensure_browsers_installed() -> None:
    """Ensure Playwright browsers are installed. Installs them if missing.
    
    Raises:
        RuntimeError: If browser installation fails
    """
    global _playwright_browsers_checked
    
    if _playwright_browsers_checked:
        return
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=settings.HEADLESS)
            browser.close()
        _playwright_browsers_checked = True
    except Exception:
        logger.info("Playwright browsers not found. Installing Chromium...")
        import subprocess
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True,
                capture_output=True,
            )
            logger.info("Chromium installed successfully.")
            _playwright_browsers_checked = True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Chromium: {e}")
            raise RuntimeError(
                "Playwright browsers are not installed and automatic installation failed. "
                "Please run: playwright install chromium"
            ) from e


class BrowserConfig:
    """Configuration for browser launch settings."""
    
    def __init__(
        self,
        headless: Optional[bool] = None,
        user_agent: Optional[str] = None,
        viewport_width: int = 1360,
        viewport_height: int = 900,
        locale: str = "en-US",
        slow_mo: int = 50,
    ):
        self.headless = headless if headless is not None else settings.HEADLESS
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.locale = locale
        self.slow_mo = slow_mo


def fetch_page_with_playwright(
    url: str,
    timeout_ms: int = 9000,
    config: Optional[BrowserConfig] = None,
    page_interaction: Optional[Callable[[Any], List[str]]] = None,
) -> Optional[Tuple[str, List[str]]]:
    """Fetch a web page using Playwright with optional page interactions.
    
    Args:
        url: The URL to fetch
        timeout_ms: Timeout in milliseconds for page load
        config: Browser configuration (uses defaults if None)
        page_interaction: Optional function to interact with the page before extracting content.
                         Should accept a page object and return a List[str] (e.g., media URLs)
    
    Returns:
        Tuple of (HTML content, interaction results) or None if fetch fails.
        Interaction results will be empty list if page_interaction is not provided.
    """
    ensure_browsers_installed()
    
    if config is None:
        config = BrowserConfig()
    
    browser = context = page = None
    interaction_results: List[str] = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config.headless, slow_mo=config.slow_mo)
            context = browser.new_context(
                user_agent=config.user_agent,
                locale=config.locale,
                viewport={"width": config.viewport_width, "height": config.viewport_height},
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            
            with suppress(Exception):
                page.wait_for_load_state("networkidle", timeout=timeout_ms)

            with suppress(Exception):
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)

            if page_interaction:
                try:
                    interaction_results = page_interaction(page) or []
                except Exception as e:
                    logger.warning(f"Page interaction failed: {e}")
            
            html = page.content()
            return (html, interaction_results)
            
    except Exception as e:
        logger.error(f"Playwright error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None
    finally:
        with suppress(Exception):
            if context:
                context.close()
        with suppress(Exception):
            if browser:
                browser.close()

