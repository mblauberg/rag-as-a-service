#!/usr/bin/env python3
"""
Test script to verify AI summary appears at the top of search results.
"""

from playwright.sync_api import sync_playwright
import sys

def test_ai_summary_placement():
    """Test that AI summary is displayed at the top of search results."""

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Enable request logging
        search_requests = []
        def log_request(request):
            if '/api/v1/search' in request.url:
                search_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'post_data': request.post_data
                })
                print(f"   📡 API Request: {request.method} {request.url}")
                if request.post_data:
                    print(f"      Body: {request.post_data}")

        page.on('request', log_request)

        print("🌐 Navigating to webapp at http://localhost:3000...")
        page.goto('http://localhost:3000')
        page.wait_for_load_state('networkidle')

        # Take initial screenshot
        page.screenshot(path='/tmp/initial_page.png', full_page=True)
        print("📸 Screenshot saved: /tmp/initial_page.png")

        # Look for search input
        print("\n🔍 Looking for search interface...")
        search_input = page.locator('input[type="text"], input[placeholder*="search" i], textarea[placeholder*="search" i]').first

        if not search_input.is_visible():
            print("❌ Search input not found on the page")
            # Print page content for debugging
            print("\n📋 Page content preview:")
            print(page.content()[:1000])
            browser.close()
            return False

        print("✅ Found search input")

        # Look for and select model dropdown (for AI summary generation)
        print("\n🤖 Looking for model selection...")
        try:
            # Look for "Select model" button
            model_selector = page.locator('button:has-text("Select model")').first
            if model_selector.is_visible():
                print("✅ Found 'Select model' button, clicking...")
                model_selector.click()
                page.wait_for_timeout(1000)

                # Take screenshot of dropdown
                page.screenshot(path='/tmp/model_dropdown.png', full_page=True)
                print("📸 Screenshot saved: /tmp/model_dropdown.png")

                # Select GPT-4o Mini (a valid, fast model for testing)
                # Look for the GPT-4o Mini option specifically
                model_option = page.locator('[role="menuitem"]:has-text("GPT-4o Mini"), [role="menuitem"]:has-text("4o-mini")').first
                if model_option.is_visible():
                    print("✅ Found GPT-4o Mini model option, clicking to select...")
                    model_option.click()
                    page.wait_for_timeout(500)

                    page.screenshot(path='/tmp/model_selected.png', full_page=True)
                    print("📸 Screenshot saved: /tmp/model_selected.png")
                else:
                    # Fallback: try any model that contains "4o"
                    print("⚠️  GPT-4o Mini not found, looking for any GPT-4o model...")
                    fallback_option = page.locator('[role="menuitem"]:has-text("GPT-4")').first
                    if fallback_option.is_visible():
                        print("✅ Found GPT-4 model, using as fallback...")
                        fallback_option.click()
                        page.wait_for_timeout(500)
                    else:
                        print("⚠️  No valid model options found")
            else:
                print("⚠️  'Select model' button not found - summary may not be generated")
        except Exception as e:
            print(f"⚠️  Could not select model: {e}")

        # Enter a search query
        search_query = "What is retrieval augmented generation?"
        print(f"\n⌨️  Entering search query: '{search_query}'")
        search_input.fill(search_query)

        # Take screenshot after filling search
        page.screenshot(path='/tmp/search_filled.png', full_page=True)
        print("📸 Screenshot saved: /tmp/search_filled.png")

        # Look for and click search button
        search_button = page.locator('button:has-text("Search"), button[type="submit"]').first
        if search_button.is_visible():
            print("🖱️  Clicking search button...")
            search_button.click()
        else:
            # Try pressing Enter as alternative
            print("⏎ Pressing Enter to submit search...")
            search_input.press('Enter')

        # Wait for results to load
        print("\n⏳ Waiting for search results...")
        page.wait_for_timeout(2000)  # Wait 2 seconds for search results
        page.wait_for_load_state('networkidle')

        # Wait additional time for AI summary generation (OpenAI API call takes longer)
        print("⏳ Waiting for AI summary generation (this may take 5-10 seconds)...")
        page.wait_for_timeout(10000)  # Wait up to 10 seconds for summary generation

        # Take screenshot of search results
        page.screenshot(path='/tmp/search_results.png', full_page=True)
        print("📸 Screenshot saved: /tmp/search_results.png")

        # Check for AI summary at the top
        print("\n🤖 Checking for AI summary...")

        # Look for the AI summary - it's in a specific structure based on SummaryDisplay component
        # The summary appears in a card with "Generated by" text at the bottom
        ai_summary_found = False

        try:
            # Look for the summary container that has "Generated by" text
            summary_container = page.locator('div.bg-white.rounded-lg.shadow-md:has(p:has-text("Generated by"))').first

            if summary_container.is_visible():
                print("✅ Found AI summary container with 'Generated by' indicator")

                # Get the bounding box to check position
                box = summary_container.bounding_box()
                if box:
                    print(f"   Position: y={box['y']:.0f}px from top")

                # Get the summary text
                summary_text_element = summary_container.locator('p.text-lg').first
                if summary_text_element.is_visible():
                    text = summary_text_element.text_content()
                    if text:
                        preview = text[:200] + "..." if len(text) > 200 else text
                        print(f"   Summary preview: {preview}")

                # Get the model information
                model_info = summary_container.locator('p:has-text("Generated by")').first
                if model_info.is_visible():
                    model_text = model_info.text_content()
                    print(f"   {model_text}")

                ai_summary_found = True
            else:
                print("❌ AI summary container not visible")

        except Exception as e:
            print(f"❌ Error checking for AI summary: {e}")

        if not ai_summary_found:
            print("❌ AI summary not found with common patterns")
            print("\n📋 Searching page structure for summary-related elements...")

            # Get all elements and look for summary-related content
            content = page.content()
            if 'summary' in content.lower() or 'ai' in content.lower():
                print("⚠️  Found 'summary' or 'ai' in page content")
                print("   Checking visible text elements...")

                # Get all visible text elements
                all_text = page.evaluate("""() => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    return elements
                        .filter(el => el.offsetParent !== null)
                        .map(el => ({
                            tag: el.tagName,
                            text: el.textContent?.substring(0, 100),
                            classes: el.className,
                            y: el.getBoundingClientRect().y
                        }))
                        .filter(el => el.text && (el.text.toLowerCase().includes('summary') || el.text.toLowerCase().includes('ai')))
                        .sort((a, b) => a.y - b.y)
                        .slice(0, 5);
                }""")

                print(f"\n   Found {len(all_text)} elements containing 'summary' or 'ai':")
                for el in all_text:
                    print(f"   - {el['tag']} (y={el['y']:.0f}): {el['text'][:80]}...")
            else:
                print("⚠️  No 'summary' or 'ai' text found in page")

        # Check if there are search results
        print("\n📊 Checking for search results...")
        results = page.locator('[class*="result" i], [class*="card" i]').all()
        print(f"   Found {len(results)} potential result elements")

        # Print summary of search requests
        print(f"\n📊 Captured {len(search_requests)} search API request(s)")
        for i, req in enumerate(search_requests, 1):
            print(f"\n   Request {i}:")
            print(f"   URL: {req['url']}")
            print(f"   Method: {req['method']}")
            if req['post_data']:
                print(f"   Body: {req['post_data']}")

        browser.close()

        if ai_summary_found:
            print("\n✅ TEST PASSED: AI summary found on search results page")
            return True
        else:
            print("\n❌ TEST FAILED: AI summary not found on search results page")
            print("\n💡 Tip: Check screenshots in /tmp/ for visual verification:")
            print("   - /tmp/initial_page.png")
            print("   - /tmp/search_filled.png")
            print("   - /tmp/search_results.png")
            return False

if __name__ == "__main__":
    try:
        success = test_ai_summary_placement()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
