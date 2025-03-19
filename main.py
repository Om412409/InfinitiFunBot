import time
import logging
import signal
import sys
import traceback
from selenium.common.exceptions import (
    WebDriverException, 
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.webdriver import setup_driver, is_session_active, wait_for_element
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.driver = None
        self.running = True
        self.login_attempts = 0
        self.max_login_attempts = 3

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Shutdown signal received. Cleaning up...")
        self.running = False
        self.cleanup()
        sys.exit(0)

    def login(self):
        """Perform login to the website"""
        if self.login_attempts >= self.max_login_attempts:
            logger.error("Maximum login attempts reached")
            return False

        try:
            logger.info("Attempting to log in...")
            self.driver.get(config.LOGIN_URL)
            logger.info("Page loaded, waiting for readyState complete...")

            # Wait for page to be fully loaded
            WebDriverWait(self.driver, config.IMPLICIT_WAIT).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            logger.info("Page ready, looking for login form...")

            # Wait for login form elements
            username_field = WebDriverWait(self.driver, config.IMPLICIT_WAIT).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            logger.info("Username field found")

            password_field = WebDriverWait(self.driver, config.IMPLICIT_WAIT).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            logger.info("Password field found")

            # Clear fields before inputting
            username_field.clear()
            password_field.clear()

            # Input credentials
            logger.info("Entering credentials...")
            username_field.send_keys(config.USERNAME)
            password_field.send_keys(config.PASSWORD)

            # Find and click login button
            logger.info("Looking for login button...")
            login_button = WebDriverWait(self.driver, config.IMPLICIT_WAIT).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            logger.info("Clicking login button...")
            login_button.click()

            # Wait for successful login indication
            logger.info("Waiting for dashboard to appear...")
            WebDriverWait(self.driver, config.IMPLICIT_WAIT).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dashboard')]"))
            )

            logger.info("Login successful")
            self.login_attempts = 0  # Reset counter on successful login
            return True

        except (TimeoutException, NoSuchElementException) as e:
            self.login_attempts += 1
            logger.error(f"Login failed (attempt {self.login_attempts}): {str(e)}")
            logger.debug(traceback.format_exc())
            return False
        except WebDriverException as e:
            self.login_attempts += 1
            logger.error(f"WebDriver error during login (attempt {self.login_attempts}): {str(e)}")
            logger.debug(traceback.format_exc())
            return False

    def maintain_session(self):
        """Main loop to maintain the session"""
        try:
            logger.info("Initializing WebDriver...")
            self.driver = setup_driver()
            self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            self.driver.set_script_timeout(config.SCRIPT_TIMEOUT)

            if not self.login():
                raise Exception("Initial login failed")

            logger.info("Starting session maintenance...")
            while self.running:
                try:
                    if not is_session_active(self.driver):
                        logger.warning("Session appears inactive, attempting recovery...")
                        if not self.login():
                            raise Exception("Session recovery failed")
                    time.sleep(config.CHECK_INTERVAL)
                except StaleElementReferenceException:
                    logger.warning("Stale element detected, checking session status...")
                    continue

        except Exception as e:
            logger.error(f"Session maintenance error: {str(e)}")
            logger.debug(traceback.format_exc())
            self.cleanup()
            sys.exit(1)

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver shutdown complete")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")

def main():
    """Main entry point"""
    if not config.USERNAME or not config.PASSWORD:
        logger.error("Credentials not found in environment variables")
        sys.exit(1)

    session_manager = SessionManager()
    try:
        session_manager.maintain_session()
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    finally:
        session_manager.cleanup()

if __name__ == "__main__":
    main()