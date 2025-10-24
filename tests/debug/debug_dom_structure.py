#!/usr/bin/env python3
"""Debug script to inspect actual DOM structure"""

from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    print("Loading homepage...")
    page.goto('http://localhost:3000')
    page.wait_for_load_state('networkidle')

    # Get document card structure
    print("\n=== Inspecting Document Cards ===")

    # Find all links to documents
    doc_links = page.locator('a[href*="/documents/"]').all()
    if doc_links:
        first_card_parent = doc_links[0].locator('xpath=ancestor::*[position()<=3]').first
        html = first_card_parent.evaluate('el => el.outerHTML')
        print(f"First document card HTML (truncated):")
        print(html[:500] + "...")

        # Get class names
        classes = first_card_parent.evaluate('el => el.className')
        print(f"\nCard classes: {classes}")

    # Check for document container
    print("\n=== Document Container ===")
    containers = page.locator('div').all()
    for container in containers[:20]:
        classes = container.evaluate('el => el.className')
        if 'document' in classes.lower() or len(container.locator('a[href*="/documents/"]').all()) > 0:
            print(f"Potential container classes: {classes}")
            break

    # Test search
    print("\n=== Testing Search Results ===")
    search_input = page.locator('input[type="search"], input[placeholder*="search" i]')
    if search_input.is_visible():
        search_input.fill("test")
        search_input.press('Enter')
        page.wait_for_load_state('networkidle')

        # Wait a bit for results
        import time
        time.sleep(2)

        # Try to find result elements
        print("Looking for search results...")

        # Get all divs and check for result-like content
        page_content = page.content()

        # Look for common result patterns
        result_containers = page.locator('[class*="result"], [class*="Result"]').all()
        print(f"Elements with 'result' in class: {len(result_containers)}")

        # Check for the "Found X results" text
        results_text = page.locator('text=/Found \\d+ results/i')
        if results_text.is_visible():
            print(f"Results text found: {results_text.text_content()}")

            # Get parent structure
            parent = results_text.locator('xpath=following-sibling::*[1]')
            if parent.count() > 0:
                classes = parent.first.evaluate('el => el.className')
                print(f"Results container classes: {classes}")

    browser.close()
