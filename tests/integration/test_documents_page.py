#!/usr/bin/env python3
"""Test script to view and analyze the document detail page."""

import asyncio
from playwright.async_api import async_playwright

async def test_documents_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        print("Navigating to main page...")
        await page.goto('http://localhost:3000/')

        # Wait for page to load
        await page.wait_for_timeout(2000)

        # Check for documents
        document_cards = page.locator('[data-testid="document-card"], .document-card, a[href^="/documents/"]')
        doc_count = await document_cards.count()
        print(f"\n=== Found {doc_count} document(s) ===")

        if doc_count > 0:
            # Click on the first document
            print("Clicking on first document...")
            await document_cards.first.click()
            await page.wait_for_timeout(2000)

            # Take screenshot of the document detail page
            await page.screenshot(path='/tmp/document_detail_page.png')
            print("Screenshot saved to /tmp/document_detail_page.png")

            # Get page structure
            print("\n=== Page Structure ===")

            # Check for margins and padding
            outer_container = page.locator('div.min-h-screen')
            if await outer_container.count() > 0:
                print("✓ Found outer container with min-h-screen")

                inner_container = page.locator('div.max-w-7xl')
                if await inner_container.count() > 0:
                    print("✓ Found inner container with max-w-7xl")
                    box = await inner_container.first.bounding_box()
                    if box:
                        print(f"  Container width: {box['width']}px")
                        print(f"  Container x position: {box['x']}px (shows left margin)")

            # Check for back button
            back_button = page.locator('a:has-text("Back to Home"), a:has-text("Back")')
            back_button_count = await back_button.count()
            print(f"\n=== Back Button ===")
            print(f"Found {back_button_count} back button(s)")

            if back_button_count > 0:
                href = await back_button.first.get_attribute('href')
                print(f"✓ Back button href: {href}")
                if href == '/':
                    print("✓ Correctly navigates to home page")
                else:
                    print(f"✗ WARNING: Navigates to {href} instead of /")

            # Check background color
            bg_element = page.locator('div.bg-gray-50').first
            if await bg_element.count() > 0:
                print("\n=== Design ===")
                print("✓ Has gray background for better visual hierarchy")

            # Keep browser open for manual inspection
            print("\n=== Browser open for inspection ===")
            print("Press Ctrl+C to close...")
            await page.wait_for_timeout(60000)
        else:
            print("No documents found. Please upload a document first.")
            await page.screenshot(path='/tmp/main_page_no_docs.png')
            print("Screenshot saved to /tmp/main_page_no_docs.png")
            await page.wait_for_timeout(10000)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_documents_page())
