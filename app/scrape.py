import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def fetch_with_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")
        html = await page.content()
        await browser.close()
        return html

def get_cleaned_text_from_url(url):
    html = asyncio.run(fetch_with_playwright(url))
    soup = BeautifulSoup(html, 'html.parser')

    for tag in soup(['script', 'style']):
        tag.decompose()

    text = soup.get_text(separator=' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text
