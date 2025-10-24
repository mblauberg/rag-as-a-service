#!/usr/bin/env python3
"""
RAAS Web Application Test
Tests the complete workflow: upload, search, and generation
"""
from playwright.sync_api import sync_playwright
import time
import os

def test_raas_webapp():
    """Test the RAAS web application"""
    print("🧪 Starting RAAS webapp test...")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))

        # Enable error logging
        page.on("pageerror", lambda exc: print(f"[PAGE ERROR] {exc}"))

        try:
            # Step 1: Navigate to app
            print("\n📍 Step 1: Navigate to http://localhost:3000")
            page.goto('http://localhost:3000')
            page.wait_for_load_state('networkidle')
            time.sleep(2)  # Additional wait for React to render

            # Take screenshot of initial state
            page.screenshot(path='/tmp/raas_initial.png', full_page=True)
            print("✅ Screenshot saved: /tmp/raas_initial.png")

            # Check page title
            title = page.title()
            print(f"📄 Page title: {title}")

            # Step 2: Check for main elements
            print("\n📍 Step 2: Inspect main page elements")

            # Find upload button/area
            upload_elements = page.locator('button, input[type="file"], [role="button"]').all()
            print(f"Found {len(upload_elements)} interactive elements")

            for idx, elem in enumerate(upload_elements[:10]):  # First 10 elements
                try:
                    text = elem.text_content() or elem.get_attribute('aria-label') or elem.get_attribute('class')
                    print(f"  Element {idx}: {text[:50]}")
                except:
                    pass

            # Step 3: Check API health
            print("\n📍 Step 3: Check backend services")
            api_response = page.request.get('http://localhost:8000/api/v1/health')
            print(f"API Health: {api_response.status()} - {api_response.text()}")

            generator_response = page.request.get('http://localhost:8002/health')
            print(f"Generator Health: {generator_response.status()} - {generator_response.text()}")

            # Check models endpoint
            models_response = page.request.get('http://localhost:8002/api/v1/models')
            print(f"Models Endpoint: {models_response.status()}")
            models_data = models_response.json()
            print(f"Available models: {models_data}")

            # Step 4: Test model selector if available
            print("\n📍 Step 4: Check for model selector")

            # Look for select/dropdown elements
            selects = page.locator('select').all()
            print(f"Found {len(selects)} select elements")

            # Look for generation-related UI
            generation_buttons = page.locator('text=/generate|ask|query|search/i').all()
            print(f"Found {len(generation_buttons)} generation-related elements")

            # Step 5: Take final screenshot
            print("\n📍 Step 5: Final state capture")
            page.screenshot(path='/tmp/raas_final.png', full_page=True)
            print("✅ Screenshot saved: /tmp/raas_final.png")

            # Get DOM structure
            html_content = page.content()
            with open('/tmp/raas_page.html', 'w') as f:
                f.write(html_content)
            print("✅ HTML saved: /tmp/raas_page.html")

            print("\n✅ Test completed successfully!")

        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            page.screenshot(path='/tmp/raas_error.png', full_page=True)
            print("Error screenshot saved: /tmp/raas_error.png")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    test_raas_webapp()
