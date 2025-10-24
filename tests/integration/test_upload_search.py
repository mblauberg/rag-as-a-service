#!/usr/bin/env python3
"""
Focused tests for Document Upload and Search functionality
"""

from playwright.sync_api import sync_playwright
import time
import os
import tempfile

def create_test_file():
    """Create a temporary test file for upload"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for the RAAS upload functionality.\n")
        f.write("It contains some sample text to test semantic search.\n")
        f.write("The quick brown fox jumps over the lazy dog.\n")
        return f.name

def test_upload_and_search():
    """Test upload and search workflows"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Track console errors
        console_errors = []
        console_warnings = []

        def handle_console(msg):
            if msg.type == 'error':
                console_errors.append(msg.text)
            elif msg.type == 'warning':
                console_warnings.append(msg.text)

        page.on("console", handle_console)
        page.on("pageerror", lambda err: console_errors.append(f"Page Error: {err}"))

        print("\n" + "="*80)
        print("UPLOAD AND SEARCH WORKFLOW TESTING")
        print("="*80 + "\n")

        try:
            # Navigate to homepage
            print("1. Loading homepage...")
            page.goto('http://localhost:3000')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            # Take initial screenshot
            page.screenshot(path='/tmp/raas_before_upload.png', full_page=True)
            print("   ✓ Homepage loaded")

            # Check initial document count
            doc_count_text = page.locator('text=/\\d+ documents?/i').first
            if doc_count_text.is_visible():
                initial_count = doc_count_text.text_content()
                print(f"   → Initial document count: {initial_count}")

            # TEST: Click Upload button
            print("\n2. Testing Upload Button...")
            upload_button = page.locator('button:has-text("Upload")')

            if upload_button.is_visible():
                print("   ✓ Upload button found and visible")
                upload_button.click()
                time.sleep(0.5)

                # Check if modal/dialog opened
                page.screenshot(path='/tmp/raas_upload_modal.png', full_page=True)

                # Look for file input
                file_input = page.locator('input[type="file"]')
                if file_input.count() > 0:
                    print("   ✓ File input found in upload dialog")

                    # Create and upload test file
                    test_file = create_test_file()
                    print(f"   → Created test file: {test_file}")

                    try:
                        file_input.set_input_files(test_file)
                        print("   ✓ Test file selected")
                        time.sleep(1)

                        # Look for submit/upload button in modal
                        submit_buttons = page.locator('button:has-text("Upload"), button[type="submit"]')
                        if submit_buttons.count() > 1:  # More than just the header button
                            submit_button = submit_buttons.nth(1)  # Get the modal button
                            if submit_button.is_visible() and submit_button.is_enabled():
                                print("   ✓ Upload submit button found")
                                submit_button.click()
                                print("   → Upload initiated")

                                # Wait for upload to complete
                                time.sleep(3)
                                page.wait_for_load_state('networkidle')

                                # Check for success message or new document
                                page.screenshot(path='/tmp/raas_after_upload.png', full_page=True)

                                # Check if document count increased
                                if doc_count_text.is_visible():
                                    new_count = doc_count_text.text_content()
                                    print(f"   → New document count: {new_count}")
                                    if new_count != initial_count:
                                        print("   ✓ Document count increased - upload successful!")
                                    else:
                                        print("   ⚠ Document count unchanged - upload may have failed")
                            else:
                                print("   ✗ Submit button not visible or enabled")
                        else:
                            print("   ⚠ Could not find submit button in modal")
                    finally:
                        # Clean up test file
                        os.unlink(test_file)
                        print(f"   → Cleaned up test file")
                else:
                    print("   ✗ File input not found in upload dialog")
            else:
                print("   ✗ Upload button not found")

            # TEST: Search Functionality
            print("\n3. Testing Search Functionality...")

            # Find search input
            search_input = page.locator('input[type="search"], input[placeholder*="search" i]')

            if search_input.is_visible():
                print("   ✓ Search input found and visible")

                # Test search with a query
                test_query = "test"
                search_input.fill(test_query)
                print(f"   → Entered search query: '{test_query}'")
                time.sleep(0.5)

                # Check if search triggers automatically or needs enter/button
                search_input.press('Enter')
                print("   → Pressed Enter to search")

                # Wait for search results
                time.sleep(2)
                page.wait_for_load_state('networkidle')

                page.screenshot(path='/tmp/raas_search_results.png', full_page=True)
                print("   ✓ Search executed, screenshot saved")

                # Check for results
                # Look for document cards or result items
                results = page.locator('[class*="document"], [class*="Document"], .card, [class*="card"]').count()
                print(f"   → Found {results} potential result elements")

                # Clear search
                search_input.fill("")
                search_input.press('Enter')
                time.sleep(1)
                print("   → Cleared search")

            else:
                print("   ✗ Search input not found")

            # TEST: Model Selector
            print("\n4. Testing Model Selector...")

            model_selector = page.locator('button:has-text("Select model"), [class*="model"]')
            if model_selector.count() > 0:
                selector = model_selector.first
                if selector.is_visible():
                    print("   ✓ Model selector found")
                    selector.click()
                    time.sleep(0.5)

                    page.screenshot(path='/tmp/raas_model_dropdown.png', full_page=True)

                    # Look for dropdown options
                    options = page.locator('[role="option"], [role="menuitem"], li').all_text_contents()
                    if options:
                        print(f"   ✓ Found {len(options)} model options")
                        for opt in options[:5]:  # Show first 5
                            if opt.strip():
                                print(f"      - {opt.strip()}")

                    # Close dropdown
                    page.keyboard.press('Escape')
                    time.sleep(0.5)
                else:
                    print("   ⚠ Model selector not visible")
            else:
                print("   ✗ Model selector not found")

            # TEST: Document Actions
            print("\n5. Testing Document Actions...")

            # Find document links (to view details)
            doc_links = page.locator('a[href*="/documents/"]')
            if doc_links.count() > 0:
                print(f"   ✓ Found {doc_links.count()} document link(s)")

                # Click first document to view details
                first_link = doc_links.first
                doc_title = first_link.text_content()
                print(f"   → Clicking document: {doc_title}")

                first_link.click()
                time.sleep(2)
                page.wait_for_load_state('networkidle')

                page.screenshot(path='/tmp/raas_document_detail.png', full_page=True)
                print("   ✓ Document detail page loaded")

                # Check URL changed
                current_url = page.url
                if '/documents/' in current_url:
                    print(f"   ✓ URL changed to: {current_url}")

                # Go back to home
                page.go_back()
                time.sleep(1)
                print("   → Returned to homepage")
            else:
                print("   ⚠ No document links found")

            # TEST: Delete Functionality
            print("\n6. Testing Delete Functionality...")

            delete_buttons = page.locator('button:has-text("Delete")')
            if delete_buttons.count() > 0:
                print(f"   ✓ Found {delete_buttons.count()} delete button(s)")
                print("   ⚠ Skipping delete test to preserve test data")
                # We could test delete, but it would remove documents
            else:
                print("   ⚠ No delete buttons found")

            # Print summary
            print("\n" + "="*80)
            print("WORKFLOW TEST SUMMARY")
            print("="*80)

            if console_errors:
                print(f"\n⚠ Console Errors ({len(console_errors)}):")
                for error in console_errors[:10]:
                    print(f"   ✗ {error}")
            else:
                print("\n✓ No console errors detected")

            if console_warnings:
                print(f"\n⚠ Console Warnings ({len(console_warnings)}):")
                for warning in console_warnings[:5]:
                    print(f"   ⚠ {warning}")

            print("\nScreenshots saved:")
            print("   - /tmp/raas_before_upload.png")
            print("   - /tmp/raas_upload_modal.png")
            print("   - /tmp/raas_after_upload.png")
            print("   - /tmp/raas_search_results.png")
            print("   - /tmp/raas_model_dropdown.png")
            print("   - /tmp/raas_document_detail.png")

        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            page.screenshot(path='/tmp/raas_workflow_error.png', full_page=True)
            import traceback
            traceback.print_exc()

        finally:
            browser.close()

if __name__ == "__main__":
    test_upload_and_search()
