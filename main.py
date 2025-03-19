import time
import logging
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_browser():
    """Set up Chrome browser with minimal settings"""
    logger.info("Setting up Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    try:
        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)
        driver.implicitly_wait(10)  # Add implicit wait

        # Basic anti-bot measures
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })

        logger.info("Chrome WebDriver initialized successfully")
        return driver
    except WebDriverException as e:
        logger.error(f"WebDriver initialization error: {str(e)}")
        raise

def verify_credentials():
    """Verify that required credentials are available"""
    username = os.getenv('INFINITI_USERNAME')
    password = os.getenv('INFINITI_PASSWORD')

    if not username or not password:
        raise ValueError("Missing credentials - please check INFINITI_USERNAME and INFINITI_PASSWORD environment variables")

    return username, password

def wait_for_element(driver, by, value, timeout=30):
    """Wait for element to be present and visible"""
    try:
        logger.info(f"Waiting for element: {value}")
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        WebDriverWait(driver, 5).until(
            EC.visibility_of(element)
        )
        logger.info(f"Element found and visible: {value}")
        return element
    except TimeoutException as e:
        logger.error(f"Element not found or not visible: {value}")
        logger.error(f"Current URL: {driver.current_url}")
        logger.error(f"Page title: {driver.title}")
        raise

def take_verification_screenshot(driver):
    """Take a single verification screenshot"""
    try:
        os.makedirs('screenshots', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'screenshots/verification_{timestamp}.png'
        driver.save_screenshot(filename)
        logger.info(f"Verification screenshot saved: {filename}")
    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")

def main():
    driver = None
    try:
        # Verify credentials first
        username, password = verify_credentials()
        logger.info("Credentials verified")

        # Initialize browser
        driver = setup_browser()

        # Navigate to login page
        logger.info("Navigating to login page...")
        driver.get("https://dash.infiniti.fun/earn/afk")

        # Wait for page load
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        logger.info(f"Page loaded - Title: {driver.title}")

        # Login process
        logger.info("Starting login process...")
        username_field = wait_for_element(driver, By.NAME, "username")
        username_field.clear()
        username_field.send_keys(username)
        logger.info("Username entered")

        password_field = wait_for_element(driver, By.NAME, "password")
        password_field.clear()
        password_field.send_keys(password)
        logger.info("Password entered")

        submit_button = wait_for_element(driver, By.XPATH, "//button[@type='submit']")
        submit_button.click()
        logger.info("Login form submitted")

        # Wait for dashboard
        logger.info("Waiting for dashboard...")
        dashboard = wait_for_element(driver, By.XPATH, "//div[contains(@class, 'dashboard')]")

        if dashboard:
            logger.info("Successfully logged in")
            # Take single verification screenshot
            take_verification_screenshot(driver)

            # Track session duration
            start_time = time.time()
            while True:
                current_time = time.time()
                duration = int(current_time - start_time)
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                seconds = duration % 60

                logger.info(f"Session active for {hours:02d}:{minutes:02d}:{seconds:02d}")
                time.sleep(60)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed successfully")
            except:
                logger.error("Error closing browser")

if __name__ == "__main__":
    main()