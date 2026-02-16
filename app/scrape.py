import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def _fetch_html(url, timeout=60000):
    async with async_playwright() as p:
        # Launch browser with anti-detection flags
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
            ]
        )
        
        # Create a context with a realistic user agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=timeout)
            
            # Wait for the page to be mostly stable
            await page.wait_for_load_state("domcontentloaded")
            
            # WORKDAY SPECIFIC:
            # Workday loads the job description dynamically. We must wait for the container.
            # Most Workday sites use 'data-automation-id="jobPostingDescription"'
            try:
                # Wait up to 10 seconds for the Workday-specific content to appear
                await page.wait_for_selector('div[data-automation-id="jobPostingDescription"]', state="visible", timeout=10000)
            except:
                # Fallback: Just wait a few seconds if the specific selector isn't found
                # (Some sites might be slower or use different IDs)
                await asyncio.sleep(5)
            
            # Get the full HTML after the wait
            html = await page.content()
            
        except Exception as e:
            print(f"Error fetching page: {e}")
            html = ""
        finally:
            await browser.close()
            
        return html

def get_cleaned_text_from_url(url):
    try:
        html = asyncio.run(_fetch_html(url))
        if not html:
            return ""
            
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. Remove script/style junk
        for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "iframe"]):
            tag.decompose()
        
        # 2. Extract content intelligently
        text_parts = []
        
        # A. Try Workday Title
        wd_title = soup.find(attrs={"data-automation-id": "jobPostingHeader"})
        if wd_title:
            text_parts.append(wd_title.get_text(separator=" ").strip())
            
        # B. Try Workday Description
        wd_desc = soup.find(attrs={"data-automation-id": "jobPostingDescription"})
        if wd_desc:
            text_parts.append(wd_desc.get_text(separator="\n").strip())
        
        # C. Fallback: If no Workday specific content found, get body
        if not text_parts:
            text = soup.get_text(separator="\n")
        else:
            text = "\n\n".join(text_parts)
        

        lines = (line.strip() for line in text.splitlines())
        # Filter out empty lines, then join with newlines
        clean_text = "\n".join(line for line in lines if line)
        # print(clean_text)
        return clean_text

    except Exception as e:
        print(f"Scraping error: {e}")
        return ""