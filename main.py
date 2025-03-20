from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import os
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_browser():
    """Set up Chrome browser with enhanced debugging"""
    logger.info("Setting up Chrome WebDriver...")
    chrome_options = Options()

    # Basic Chrome options - headless disabled for debugging
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-notifications')

    # Realistic browser configuration
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    chrome_options.add_argument('--accept-lang=en-US,en;q=0.9')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)

        # Enhanced stealth script
        stealth_js = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {} };
        """
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': stealth_js
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
        raise ValueError("Missing credentials - please set INFINITI_USERNAME and INFINITI_PASSWORD environment variables")

    return username, password

def take_screenshot(driver, status="initial"):
    """Take a screenshot with status indicator"""
    try:
        os.makedirs('screenshots', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'screenshots/{status}_{timestamp}.png'
        driver.save_screenshot(filename)
        logger.info(f"Screenshot saved: {filename}")

        # Log page information with screenshot
        logger.info(f"Current URL when taking screenshot: {driver.current_url}")
        logger.info(f"Page title when taking screenshot: {driver.title}")
    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")

def wait_for_element(driver, by, value, timeout=30):
    """Wait for element with enhanced error handling and logging"""
    try:
        logger.debug(f"Attempting to find element: {by}={value}")
        logger.debug(f"Current page title: {driver.title}")
        logger.debug(f"Current URL: {driver.current_url}")

        # First wait for presence
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        logger.debug("Element found in DOM")

        # Then check visibility
        if not element.is_displayed():
            logger.error(f"Element found but not visible: {value}")
            logger.debug(f"Element HTML: {element.get_attribute('outerHTML')}")
            take_screenshot(driver, "error_not_visible")
            raise TimeoutException(f"Element not visible: {value}")
        logger.debug("Element is visible")

        # Finally check if clickable
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((by, value))
        )
        logger.debug("Element is clickable")

        logger.info(f"Element successfully found and interactive: {value}")
        return element
    except TimeoutException:
        logger.error(f"Failed to find element: {value}")
        logger.error(f"Current URL: {driver.current_url}")
        logger.error(f"Current page source excerpt: {driver.page_source[:1000]}")
        take_screenshot(driver, "error_find_element")
        raise

def verify_page_loaded(driver):
    """Verify page load with enhanced checks"""
    try:
        logger.info("Waiting for page load...")
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

        # Additional checks
        logger.info(f"Page loaded - Title: {driver.title}")
        logger.info(f"Current URL: {driver.current_url}")

        # Take screenshot after load
        take_screenshot(driver, "page_loaded")
        return True
    except TimeoutException:
        logger.error("Page load timeout")
        take_screenshot(driver, "error_page_load")
        return False

def main():
    driver = None
    try:
        username, password = verify_credentials()
        logger.info("Credentials verified")

        driver = setup_browser()

        # Navigate to login page
        logger.info("Navigating to login page...")
        driver.get("https://dash.infiniti.fun/earn/afk")

        if not verify_page_loaded(driver):
            raise Exception("Failed to load login page properly")

        try:
            # Find and interact with login form
            username_field = wait_for_element(driver, By.CSS_SELECTOR, "input[type='text'], input[type='email']")
            username_field.clear()
            username_field.send_keys(username)
            logger.info("Username entered")

            password_field = wait_for_element(driver, By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(password)
            logger.info("Password entered")

            submit_button = wait_for_element(driver, By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            logger.info("Login form submitted")

            # Wait for dashboard
            logger.info("Waiting for dashboard...")
            dashboard = wait_for_element(driver, By.CSS_SELECTOR, ".dashboard")

            if dashboard:
                logger.info("Successfully logged in")
                take_screenshot(driver, "success")

                # Track session
                start_time = time.time()
                logger.info("Starting session tracking...")

                while True:
                    try:
                        # Verify session is active
                        driver.execute_script("return document.readyState")

                        # Log duration
                        duration = int(time.time() - start_time)
                        hours = duration // 3600
                        minutes = (duration % 3600) // 60
                        seconds = duration % 60
                        logger.info(f"Session active for {hours:02d}:{minutes:02d}:{seconds:02d}")

                        # Check if dashboard is still visible
                        if not driver.find_element(By.CSS_SELECTOR, ".dashboard").is_displayed():
                            logger.error("Dashboard no longer visible")
                            take_screenshot(driver, "error_session")
                            break

                        time.sleep(60)
                    except Exception as e:
                        logger.error(f"Session verification failed: {str(e)}")
                        take_screenshot(driver, "error_session")
                        break

        except Exception as e:
            logger.error(f"Login process failed: {str(e)}")
            take_screenshot(driver, "error_login")
            raise

    except Exception as e:
        logger.error(f"Script error: {str(e)}")
        if driver:
            take_screenshot(driver, "error_final")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

if __name__ == "__main__":
    main()