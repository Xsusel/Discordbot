from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to the web dashboard
            page.goto("http://localhost:5000", timeout=10000)

            # Wait for the main heading to be visible to ensure the page is loaded
            expect(page.get_by_role("heading", name="Bot Dashboard")).to_be_visible()

            # Take a screenshot of the entire page
            screenshot_path = "jules-scratch/verification/dashboard_screenshot.png"
            page.screenshot(path=screenshot_path)

            print(f"Screenshot saved to {screenshot_path}")

        except Exception as e:
            print(f"An error occurred during verification: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()