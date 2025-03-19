import time
import logging
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_browser():
    """Set up Chrome browser with optimal settings"""
    logger.info("Setting up Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)
        driver.set_page_load_timeout(45)  # Increased timeout for page loads
        driver.set_script_timeout(45)  # Increased timeout for scripts
        logger.info("Chrome WebDriver initialized successfully")
        return driver
    except WebDriverException as e:
        logger.error(f"WebDriver initialization error: {str(e)}")
        logger.debug(traceback.format_exc())
        raise Exception(f"Failed to initialize WebDriver: {str(e)}")

def take_screenshot(driver, name):
    """Take a screenshot and save it to the screenshots directory"""
    try:
        # Create screenshots directory if it doesn't exist
        os.makedirs('screenshots', exist_ok=True)
        logger.info("Screenshots directory checked/created")

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'screenshots/{timestamp}_{name}.png'

        # Take screenshot
        driver.save_screenshot(filename)

        # Verify screenshot was saved
        if os.path.exists(filename):
            logger.info(f"Screenshot saved successfully: {filename}")
        else:
            logger.error(f"Screenshot file not found after saving: {filename}")

    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")
        logger.debug(traceback.format_exc())

def wait_for_element(driver, by, value, timeout=30):
    """Wait for element to be present and return it"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        logger.info(f"Element found: {value}")
        return element
    except TimeoutException:
        logger.error(f"Element not found after {timeout} seconds: {value}")
        raise

def main():
    driver = None
    start_time = None
    try:
        # Get credentials
        username = os.getenv('INFINITI_USERNAME')
        password = os.getenv('INFINITI_PASSWORD')

        if not username or not password:
            logger.error("Missing credentials")
            return

        logger.info("Starting browser...")
        driver = setup_browser()

        logger.info("Navigating to login page...")
        driver.get("https://dash.infiniti.fun/earn/afk")

        logger.info("Waiting for page load...")
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

        # Take screenshot before login
        take_screenshot(driver, 'before_login')

        logger.info("Looking for login form...")
        try:
            username_field = wait_for_element(driver, By.NAME, "username")
            password_field = wait_for_element(driver, By.NAME, "password")

            logger.info("Entering credentials...")
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)

            logger.info("Submitting login...")
            submit_button = wait_for_element(driver, By.XPATH, "//button[@type='submit']")
            submit_button.click()

            logger.info("Waiting for dashboard...")
            wait_for_element(driver, By.XPATH, "//div[contains(@class, 'dashboard')]")

            # Take screenshot after successful login
            take_screenshot(driver, 'after_login')

            logger.info("Successfully logged in, maintaining session...")
            start_time = time.time()

            # Keep session alive without refreshing
            check_interval = 60  # Check every minute
            while True:
                try:
                    # Simple check without refreshing
                    driver.execute_script("return document.readyState")

                    # Calculate and log session duration
                    current_time = time.time()
                    duration = int(current_time - start_time)
                    hours = duration // 3600
                    minutes = (duration % 3600) // 60
                    seconds = duration % 60

                    logger.info(f"Session is active - Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")

                    # Additional check for dashboard presence
                    wait_for_element(driver, By.XPATH, "//div[contains(@class, 'dashboard')]")

                    time.sleep(check_interval)  # Wait before next check

                except WebDriverException as e:
                    logger.error(f"WebDriver error during session check: {str(e)}")
                    logger.debug(traceback.format_exc())
                    break
                except Exception as e:
                    logger.error(f"Unexpected error during session check: {str(e)}")
                    logger.debug(traceback.format_exc())
                    break

        except TimeoutException as e:
            logger.error(f"Timeout waiting for login form: {str(e)}")
            logger.debug(traceback.format_exc())
        except WebDriverException as e:
            logger.error(f"WebDriver error during login: {str(e)}")
            logger.debug(traceback.format_exc())
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            logger.debug(traceback.format_exc())

    finally:
        if driver:
            try:
                if start_time:
                    duration = int(time.time() - start_time)
                    logger.info(f"Total session duration: {duration // 3600:02d}:{(duration % 3600) // 60:02d}:{duration % 60:02d}")
                driver.quit()
                logger.info("Browser closed successfully")
            except:
                logger.error("Error closing browser")

if __name__ == "__main__":
    main()