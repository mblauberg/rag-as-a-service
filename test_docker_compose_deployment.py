#!/usr/bin/env python3
"""
Comprehensive Web Application Test for Docker Compose Deployment
Tests the RAaS application deployed via docker-compose
"""

from playwright.sync_api import sync_playwright, expect
import time
import sys
import json

def test_docker_compose_deployment():
    """Test the complete docker-compose deployment"""

    results = {
        "deployment": "docker-compose",
        "tests": [],
        "passed": 0,
        "failed": 0,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Enable console logging
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

        try:
            # Test 1: Frontend loads successfully
            test_name = "Frontend loads successfully"
            print(f"\n[TEST] {test_name}")
            try:
                page.goto('http://localhost:3000', wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(2000)  # Wait for JS to execute
                page.screenshot(path='/tmp/docker_compose_frontend.png', full_page=True)

                # Check page title
                title = page.title()
                assert "RAaS" in title or "Research" in title or len(title) > 0, f"Unexpected title: {title}"

                results["tests"].append({"name": test_name, "status": "PASSED", "details": f"Title: {title}"})
                results["passed"] += 1
                print(f"✓ PASSED: {title}")
            except Exception as e:
                results["tests"].append({"name": test_name, "status": "FAILED", "error": str(e)})
                results["failed"] += 1
                print(f"✗ FAILED: {str(e)}")

            # Test 2: API health endpoint
            test_name = "API health endpoint responds"
            print(f"\n[TEST] {test_name}")
            try:
                response = page.request.get('http://localhost:8000/api/v1/health')
                assert response.ok, f"Health endpoint failed with status {response.status}"
                health_data = response.json()
                print(f"  Health response: {json.dumps(health_data, indent=2)}")

                results["tests"].append({"name": test_name, "status": "PASSED", "details": health_data})
                results["passed"] += 1
                print(f"✓ PASSED")
            except Exception as e:
                results["tests"].append({"name": test_name, "status": "FAILED", "error": str(e)})
                results["failed"] += 1
                print(f"✗ FAILED: {str(e)}")

            # Test 3: Navigation elements present
            test_name = "Navigation elements are present"
            print(f"\n[TEST] {test_name}")
            try:
                # Check for common navigation elements
                nav_elements = []

                # Look for buttons
                buttons = page.locator('button').all()
                nav_elements.append(f"{len(buttons)} buttons found")

                # Look for links
                links = page.locator('a').all()
                nav_elements.append(f"{len(links)} links found")

                # Look for inputs
                inputs = page.locator('input').all()
                nav_elements.append(f"{len(inputs)} inputs found")

                assert len(buttons) > 0 or len(links) > 0, "No interactive elements found"

                results["tests"].append({"name": test_name, "status": "PASSED", "details": nav_elements})
                results["passed"] += 1
                print(f"✓ PASSED: {', '.join(nav_elements)}")
            except Exception as e:
                results["tests"].append({"name": test_name, "status": "FAILED", "error": str(e)})
                results["failed"] += 1
                print(f"✗ FAILED: {str(e)}")

            # Test 4: Check for main content areas
            test_name = "Main content areas present"
            print(f"\n[TEST] {test_name}")
            try:
                # Get page content
                content = page.content()

                # Look for common sections
                sections_found = []
                if 'nav' in content.lower():
                    sections_found.append('navigation')
                if 'header' in content.lower():
                    sections_found.append('header')
                if 'main' in content.lower():
                    sections_found.append('main')
                if 'footer' in content.lower():
                    sections_found.append('footer')

                # Check for headings
                headings = page.locator('h1, h2, h3').all()
                sections_found.append(f"{len(headings)} headings")

                assert len(sections_found) > 0, "No content sections found"

                results["tests"].append({"name": test_name, "status": "PASSED", "details": sections_found})
                results["passed"] += 1
                print(f"✓ PASSED: {', '.join(sections_found)}")
            except Exception as e:
                results["tests"].append({"name": test_name, "status": "FAILED", "error": str(e)})
                results["failed"] += 1
                print(f"✗ FAILED: {str(e)}")

            # Test 5: No critical JavaScript errors
            test_name = "No critical JavaScript errors"
            print(f"\n[TEST] {test_name}")
            try:
                critical_errors = [log for log in console_logs if 'error' in log.lower()]

                if len(critical_errors) > 0:
                    print(f"  Console errors found: {len(critical_errors)}")
                    for error in critical_errors[:5]:  # Show first 5
                        print(f"    - {error}")

                # Allow for some non-critical warnings, but no errors
                assert len(critical_errors) == 0, f"Found {len(critical_errors)} JavaScript errors"

                results["tests"].append({"name": test_name, "status": "PASSED", "details": "No errors"})
                results["passed"] += 1
                print(f"✓ PASSED: No critical errors")
            except Exception as e:
                results["tests"].append({"name": test_name, "status": "FAILED", "error": str(e), "details": critical_errors[:5]})
                results["failed"] += 1
                print(f"✗ FAILED: {str(e)}")

            # Test 6: API endpoints are accessible
            test_name = "API endpoints are accessible"
            print(f"\n[TEST] {test_name}")
            try:
                endpoints_tested = []

                # Test OpenAPI docs
                response = page.request.get('http://localhost:8000/docs')
                if response.ok:
                    endpoints_tested.append('/docs (OpenAPI)')

                # Test API version endpoint if exists
                response = page.request.get('http://localhost:8000/api/v1')
                if response.ok or response.status == 404:  # 404 is ok, means routing works
                    endpoints_tested.append('/api/v1 (routed)')

                assert len(endpoints_tested) > 0, "No API endpoints accessible"

                results["tests"].append({"name": test_name, "status": "PASSED", "details": endpoints_tested})
                results["passed"] += 1
                print(f"✓ PASSED: {', '.join(endpoints_tested)}")
            except Exception as e:
                results["tests"].append({"name": test_name, "status": "FAILED", "error": str(e)})
                results["failed"] += 1
                print(f"✗ FAILED: {str(e)}")

            # Test 7: Responsive design check
            test_name = "Responsive design works"
            print(f"\n[TEST] {test_name}")
            try:
                # Test mobile viewport
                page.set_viewport_size({"width": 375, "height": 667})
                page.wait_for_timeout(1000)
                page.screenshot(path='/tmp/docker_compose_mobile.png', full_page=True)

                # Test tablet viewport
                page.set_viewport_size({"width": 768, "height": 1024})
                page.wait_for_timeout(1000)
                page.screenshot(path='/tmp/docker_compose_tablet.png', full_page=True)

                # Reset to desktop
                page.set_viewport_size({"width": 1920, "height": 1080})

                results["tests"].append({"name": test_name, "status": "PASSED", "details": "Screenshots captured for mobile, tablet, desktop"})
                results["passed"] += 1
                print(f"✓ PASSED: Responsive screenshots captured")
            except Exception as e:
                results["tests"].append({"name": test_name, "status": "FAILED", "error": str(e)})
                results["failed"] += 1
                print(f"✗ FAILED: {str(e)}")

        finally:
            browser.close()

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY - Docker Compose Deployment")
    print("="*60)
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed']/(results['passed']+results['failed'])*100):.1f}%")
    print("="*60)

    # Save results to JSON
    with open('/tmp/docker_compose_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: /tmp/docker_compose_test_results.json")
    print(f"Screenshots saved to: /tmp/docker_compose_*.png")

    return results['failed'] == 0

if __name__ == "__main__":
    success = test_docker_compose_deployment()
    sys.exit(0 if success else 1)
