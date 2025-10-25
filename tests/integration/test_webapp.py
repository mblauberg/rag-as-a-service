#!/usr/bin/env python3
"""
Comprehensive Web Application Testing Script for RAAS
Tests the frontend, document upload, search functionality, and captures errors.
"""

from playwright.sync_api import sync_playwright
import json
import time
import os
import sys

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": [],
    "console_errors": [],
    "console_warnings": []
}

def log_result(test_name, passed, message=""):
    """Log test result"""
    if passed:
        test_results["passed"].append(f"✓ {test_name}")
        print(f"✓ PASS: {test_name}")
    else:
        test_results["failed"].append(f"✗ {test_name}: {message}")
        print(f"✗ FAIL: {test_name}: {message}")
    if message and passed:
        print(f"  → {message}")

def test_webapp():
    """Main test function"""
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Set up console message listeners
        page.on("console", lambda msg: handle_console_message(msg))
        page.on("pageerror", lambda err: handle_page_error(err))

        print("\n" + "="*80)
        print("RAAS WEB APPLICATION COMPREHENSIVE TESTING")
        print("="*80 + "\n")

        try:
            # TEST 1: Load frontend
            print("TEST 1: Loading Frontend...")
            page.goto('http://localhost:3000')
            page.wait_for_load_state('networkidle')
            time.sleep(1)  # Extra wait for React to hydrate

            # Take initial screenshot
            page.screenshot(path='/tmp/raas_homepage.png', full_page=True)
            log_result("Frontend loads successfully", True, "Screenshot saved to /tmp/raas_homepage.png")

            # TEST 2: Check page title
            print("\nTEST 2: Checking Page Title...")
            title = page.title()
            if "RAAS" in title or title:
                log_result("Page has title", True, f"Title: '{title}'")
            else:
                log_result("Page has title", False, "Title is empty")

            # TEST 3: Discover and verify UI elements
            print("\nTEST 3: Discovering UI Elements...")

            # Check for header/navigation
            header = page.locator('header, nav, [role="banner"]').count()
            log_result("Header/Navigation present", header > 0, f"Found {header} header element(s)")

            # Check for main content area
            main_content = page.locator('main, [role="main"], .container, .app').count()
            log_result("Main content area present", main_content > 0, f"Found {main_content} main element(s)")

            # TEST 4: Check for upload functionality
            print("\nTEST 4: Checking Upload Functionality...")

            # Look for file input or upload button
            file_inputs = page.locator('input[type="file"]').count()
            upload_buttons = page.locator('button:has-text("Upload"), button:has-text("upload")').count()
            upload_areas = page.locator('[class*="upload"], [class*="Upload"]').count()

            has_upload = file_inputs > 0 or upload_buttons > 0 or upload_areas > 0
            log_result("Upload interface present", has_upload,
                      f"File inputs: {file_inputs}, Upload buttons: {upload_buttons}, Upload areas: {upload_areas}")

            if has_upload:
                # Take screenshot of upload area
                page.screenshot(path='/tmp/raas_upload_area.png', full_page=True)
                print("  → Screenshot saved to /tmp/raas_upload_area.png")

            # TEST 5: Check for search functionality
            print("\nTEST 5: Checking Search Functionality...")

            # Look for search inputs or search buttons
            search_inputs = page.locator('input[type="search"], input[placeholder*="search" i], input[placeholder*="Search" i]').count()
            search_buttons = page.locator('button:has-text("Search"), button:has-text("search")').count()
            search_areas = page.locator('[class*="search"], [class*="Search"]').count()

            has_search = search_inputs > 0 or search_buttons > 0 or search_areas > 0
            log_result("Search interface present", has_search,
                      f"Search inputs: {search_inputs}, Search buttons: {search_buttons}, Search areas: {search_areas}")

            # TEST 6: Check for navigation/routing
            print("\nTEST 6: Checking Navigation...")

            # Look for links
            links = page.locator('a').count()
            nav_links = page.locator('nav a, [role="navigation"] a').count()
            log_result("Navigation links present", links > 0, f"Total links: {links}, Nav links: {nav_links}")

            # Get all visible links
            if links > 0:
                visible_links = page.locator('a:visible').all()
                print(f"  → Found {len(visible_links)} visible links")
                for i, link in enumerate(visible_links[:5]):  # Show first 5
                    text = link.text_content()
                    href = link.get_attribute('href')
                    if text and text.strip():
                        print(f"     - {text.strip()}: {href}")

            # TEST 7: Test responsive design
            print("\nTEST 7: Testing Responsive Design...")

            # Desktop view
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/tmp/raas_desktop.png', full_page=True)
            log_result("Desktop view renders", True, "1920x1080 screenshot saved")

            # Tablet view
            page.set_viewport_size({"width": 768, "height": 1024})
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/tmp/raas_tablet.png', full_page=True)
            log_result("Tablet view renders", True, "768x1024 screenshot saved")

            # Mobile view
            page.set_viewport_size({"width": 375, "height": 667})
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/tmp/raas_mobile.png', full_page=True)
            log_result("Mobile view renders", True, "375x667 screenshot saved")

            # Reset to desktop
            page.set_viewport_size({"width": 1920, "height": 1080})

            # TEST 8: Check for API connectivity
            print("\nTEST 8: Checking API Connectivity...")

            # Monitor network requests
            api_calls = []

            def handle_request(request):
                if '/api/' in request.url:
                    api_calls.append({
                        'url': request.url,
                        'method': request.method
                    })

            page.on("request", handle_request)

            # Reload page to capture initial API calls
            page.reload()
            page.wait_for_load_state('networkidle')
            time.sleep(2)

            log_result("Frontend makes API calls", len(api_calls) > 0,
                      f"Detected {len(api_calls)} API calls")

            if api_calls:
                print("  → API Calls detected:")
                for call in api_calls[:5]:  # Show first 5
                    print(f"     - {call['method']} {call['url']}")

            # TEST 9: Test document list/view
            print("\nTEST 9: Checking Document List...")

            # Look for document list or table
            tables = page.locator('table').count()
            lists = page.locator('ul, ol').count()
            cards = page.locator('[class*="card"], [class*="Card"]').count()

            has_doc_display = tables > 0 or cards > 0
            log_result("Document display interface present", has_doc_display,
                      f"Tables: {tables}, Lists: {lists}, Cards: {cards}")

            # TEST 10: Check for error boundaries
            print("\nTEST 10: Checking Error Handling...")

            # Look for error messages or empty states
            errors = page.locator('[class*="error"], [class*="Error"], [role="alert"]').count()
            empty_states = page.locator('[class*="empty"], [class*="Empty"]').count()

            print(f"  → Error elements: {errors}, Empty state elements: {empty_states}")

            # TEST 11: Accessibility check
            print("\nTEST 11: Basic Accessibility Check...")

            # Check for ARIA labels and roles
            aria_labels = page.locator('[aria-label]').count()
            aria_roles = page.locator('[role]').count()
            buttons = page.locator('button').count()

            log_result("Accessibility attributes present", aria_labels > 0 or aria_roles > 0,
                      f"ARIA labels: {aria_labels}, ARIA roles: {aria_roles}, Buttons: {buttons}")

            # TEST 12: Performance check
            print("\nTEST 12: Performance Metrics...")

            metrics = page.evaluate("""() => {
                const perfData = window.performance.timing;
                const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                const connectTime = perfData.responseEnd - perfData.requestStart;
                const renderTime = perfData.domComplete - perfData.domLoading;

                return {
                    pageLoadTime,
                    connectTime,
                    renderTime
                };
            }""")

            if metrics['pageLoadTime'] > 0:
                log_result("Performance metrics available", True,
                          f"Page load: {metrics['pageLoadTime']}ms, " +
                          f"Connect: {metrics['connectTime']}ms, " +
                          f"Render: {metrics['renderTime']}ms")

                # Check if load time is reasonable (< 5 seconds)
                if metrics['pageLoadTime'] > 5000:
                    test_results["warnings"].append(
                        f"⚠ Slow page load time: {metrics['pageLoadTime']}ms")
                    print(f"  ⚠ WARNING: Page load time is slow ({metrics['pageLoadTime']}ms)")

        except Exception as e:
            log_result("Critical test execution", False, str(e))
            page.screenshot(path='/tmp/raas_error.png', full_page=True)
            print(f"  → Error screenshot saved to /tmp/raas_error.png")

        finally:
            browser.close()

        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        print(f"\nPassed: {len(test_results['passed'])}")
        for result in test_results['passed']:
            print(f"  {result}")

        if test_results['failed']:
            print(f"\nFailed: {len(test_results['failed'])}")
            for result in test_results['failed']:
                print(f"  {result}")

        if test_results['warnings']:
            print(f"\nWarnings: {len(test_results['warnings'])}")
            for warning in test_results['warnings']:
                print(f"  {warning}")

        if test_results['console_errors']:
            print(f"\nConsole Errors: {len(test_results['console_errors'])}")
            for error in test_results['console_errors'][:10]:  # Show first 10
                print(f"  ✗ {error}")

        if test_results['console_warnings']:
            print(f"\nConsole Warnings: {len(test_results['console_warnings'])}")
            for warning in test_results['console_warnings'][:10]:  # Show first 10
                print(f"  ⚠ {warning}")

        # Save detailed results to JSON
        with open('/tmp/raas_test_results.json', 'w') as f:
            json.dump(test_results, f, indent=2)

        print(f"\nDetailed results saved to: /tmp/raas_test_results.json")
        print("Screenshots saved to: /tmp/raas_*.png")

        # Return exit code based on results
        if test_results['failed']:
            print("\n⚠ Some tests failed!")
            return 1
        else:
            print("\n✓ All tests passed!")
            return 0

def handle_console_message(msg):
    """Handle console messages from the browser"""
    msg_type = msg.type
    msg_text = msg.text

    if msg_type == 'error':
        test_results['console_errors'].append(msg_text)
    elif msg_type == 'warning':
        test_results['console_warnings'].append(msg_text)

def handle_page_error(error):
    """Handle page errors"""
    test_results['console_errors'].append(f"Page Error: {error}")

if __name__ == "__main__":
    exit_code = test_webapp()
    sys.exit(exit_code)
