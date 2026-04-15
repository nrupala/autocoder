"""
AutoCoder E2E Testing with Playwright
"""

import asyncio
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class BrowserConfig:
    headless: bool = True
    slow_mo: int = 0
    timeout: int = 30000


class PlaywrightAutomation:
    """Browser automation for AutoCoder."""

    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        self.browser = None
        self.context = None
        self.page = None

    async def __aenter__(self):
        from playwright.async_api import async_playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.headless
        )
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def navigate(self, url: str):
        await self.page.goto(url, timeout=self.config.timeout)

    async def click(self, selector: str):
        await self.page.click(selector)

    async def fill(self, selector: str, value: str):
        await self.page.fill(selector, value)

    async def get_text(self, selector: str) -> str:
        return await self.page.text_content(selector)

    async def get_html(self) -> str:
        return await self.page.content()

    async def screenshot(self, path: str):
        await self.page.screenshot(path=path)

    async def evaluate(self, script: str):
        return await self.page.evaluate(script)

    async def wait_for_selector(self, selector: str, timeout: int = None):
        await self.page.wait_for_selector(selector, timeout=timeout or self.config.timeout)


class PlaywrightTool:
    """Playwright tool for automation tasks."""

    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()

    async def screenshot(self, url: str, path: str, selector: str = None) -> str:
        """Take screenshot of a URL."""
        async with PlaywrightAutomation(self.config) as pw:
            await pw.navigate(url)
            if selector:
                element = await pw.page.query_selector(selector)
                if element:
                    await element.screenshot(path=path)
            else:
                await pw.screenshot(path=path)
        return f"Screenshot saved to {path}"

    async def scrape(self, url: str, selectors: dict) -> dict:
        """Scrape data from URL using selectors."""
        async with PlaywrightAutomation(self.config) as pw:
            await pw.navigate(url)
            results = {}
            for key, selector in selectors.items():
                try:
                    results[key] = await pw.get_text(selector)
                except:
                    results[key] = None
        return results

    async def fill_form(self, url: str, form_data: dict) -> str:
        """Fill and submit a form."""
        async with PlaywrightAutomation(self.config) as pw:
            await pw.navigate(url)
            for selector, value in form_data.items():
                await pw.fill(selector, value)
            return "Form filled"

    async def test_app(self, url: str, test_steps: list[dict]) -> dict:
        """Run automated test steps on an app."""
        results = []
        async with PlaywrightAutomation(self.config) as pw:
            await pw.navigate(url)
            for step in test_steps:
                action = step.get("action")
                try:
                    if action == "click":
                        await pw.click(step["selector"])
                    elif action == "fill":
                        await pw.fill(step["selector"], step["value"])
                    elif action == "wait":
                        await pw.wait_for_selector(step["selector"])
                    elif action == "assert_text":
                        text = await pw.get_text(step["selector"])
                        assert step["expected"] in text, f"Expected '{step['expected']}' in '{text}'"
                    results.append({"step": step, "status": "pass"})
                except Exception as e:
                    results.append({"step": step, "status": "fail", "error": str(e)})
        return {"results": results}


def run_playwright_test(url: str, steps: list[dict]):
    """Sync wrapper for Playwright tests."""
    tool = PlaywrightTool()
    return asyncio.run(tool.test_app(url, steps))
