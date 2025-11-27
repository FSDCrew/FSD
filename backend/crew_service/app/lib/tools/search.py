import json
from typing import Any, Dict, List, Optional

from crewai.tools import tool
from crewai_tools.tools.brightdata_tool.brightdata_serp import BrightDataSearchTool
from crewai_tools.tools.scrape_website_tool.scrape_website_tool import ScrapeWebsiteTool


def _extract_organic_results(raw_result: Any) -> List[Dict[str, Any]]:
    """Parse the Bright Data response and return only organic results."""

    def _to_dict(payload: Any) -> Optional[Dict[str, Any]]:
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                return None
            return _to_dict(parsed)
        return None

    payload = _to_dict(raw_result)
    if not payload:
        return []

    organic_results = payload.get("organic")
    return organic_results if isinstance(organic_results, list) else []


@tool("search internet")
def search_internet(query: str):
    """
    Performs a Google search to find relevant web results for the given query.

    The AI Agent can use this tool to gather up-to-date information from the web.
    It returns summarized search results (titles, snippets, and URLs) from Google
    based on the query provided.
    """
    tool = BrightDataSearchTool(
        query=query,
        country="SG",
    )
    return _extract_organic_results(tool.run())

@tool("search instagram")
def search_instagram(query: str):
    """
    Performs a Google search limited to Instagram post results.

    The AI Agent can use this tool to find public Instagram profiles or posts 
    related to the query by searching `site:instagram.com` through Google.
    It returns summarized results with page titles, snippets, and URLs.
    """
    tool = BrightDataSearchTool(
        query=f"site:instagram.com/p/ {query}",
        country="SG",
    )
    return _extract_organic_results(tool.run())

@tool("open pages")
def open_pages(website_urls: list[str]):
    """
    Opens and extracts the readable text content from one or more webpages.

    The AI Agent can use this tool to access one or more webpages and retrieve their main text 
    (such as article content, descriptions, or captions). This helps the Agent 
    understand what the pages are about for deeper context or summarization.
    """
    results = []
    for website_url in website_urls:
        scrape_tool = ScrapeWebsiteTool(
            website_url=website_url,
        )
        results.append(scrape_tool.run())
    
    return results
