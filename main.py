import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_browser():
    """Set up Chrome browser with optimal settings"""
    logger.info("Setting up Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # Use new headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)
        logger.info("Chrome WebDriver initialized successfully")
        return driver
    except WebDriverException as e:
        logger.error(f"WebDriver initialization error: {str(e)}")
        raise Exception(f"Failed to initialize WebDriver: {str(e)}")

def main():
    driver = None
    try:
        # Get credentials
        username = os.getenv('INFINITI_USERNAME')
        password = os.getenv('INFINITI_PASSWORD')

        if not username or not password:
            logger.error("Missing credentials")
            return

        logger.info("Starting browser...")
        driver = setup_browser()

        # Login process
        logger.info("Navigating to login page...")
        driver.get("https://dash.infiniti.fun/earn/afk")

        logger.info("Waiting for page load...")
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

        # Extra time for JavaScript initialization
        time.sleep(5)

        logger.info("Looking for login form...")
        username_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        logger.info("Username field found")

        password_field = driver.find_element(By.NAME, "password")
        logger.info("Password field found")

        logger.info("Entering credentials...")
        username_field.send_keys(username)
        password_field.send_keys(password)

        logger.info("Submitting login...")
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        logger.info("Waiting for dashboard...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dashboard')]"))
        )

        logger.info("Successfully logged in, maintaining session...")

        # Keep session alive without refreshing
        while True:
            try:
                # Simple check without refreshing
                driver.execute_script("return document.readyState")
                logger.info("Session is active")
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Session check failed: {e}")
                break

    except TimeoutException as e:
        logger.error(f"Timeout error: {str(e)}")
        logger.debug(traceback.format_exc())
    except WebDriverException as e:
        logger.error(f"WebDriver error: {str(e)}")
        logger.debug(traceback.format_exc())
    except NoSuchElementException as e:
        logger.error(f"Element not found: {str(e)}")
        logger.debug(traceback.format_exc())
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.debug(traceback.format_exc())
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed successfully")
            except:
                logger.error("Error closing browser")

if __name__ == "__main__":
    main()