import time
import logging
import signal
import sys
from selenium.common.exceptions import (
    WebDriverException, 
    TimeoutException, 
    NoSuchElementException
)
from selenium.webdriver.common.by import By
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
        try:
            logger.info("Attempting to log in...")
            self.driver.get(config.LOGIN_URL)
            
            # Wait for login form elements
            username_field = wait_for_element(
                self.driver, 
                By.NAME, 
                "username"  # Adjust selector based on actual page
            )
            password_field = wait_for_element(
                self.driver, 
                By.NAME, 
                "password"  # Adjust selector based on actual page
            )
            
            # Input credentials
            username_field.send_keys(config.USERNAME)
            password_field.send_keys(config.PASSWORD)
            
            # Find and click login button
            login_button = wait_for_element(
                self.driver, 
                By.XPATH, 
                "//button[@type='submit']"  # Adjust selector based on actual page
            )
            login_button.click()
            
            # Wait for successful login indication
            wait_for_element(
                self.driver,
                By.XPATH,
                "//div[contains(@class, 'dashboard')]"  # Adjust selector based on actual page
            )
            
            logger.info("Login successful")
            return True
            
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Login failed: {str(e)}")
            return False
        except WebDriverException as e:
            logger.error(f"WebDriver error during login: {str(e)}")
            return False

    def maintain_session(self):
        """Main loop to maintain the session"""
        try:
            self.driver = setup_driver()
            self.driver.implicitly_wait(config.IMPLICIT_WAIT)
            
            if not self.login():
                raise Exception("Initial login failed")
            
            logger.info("Starting session maintenance...")
            while self.running:
                if not is_session_active(self.driver):
                    logger.warning("Session appears inactive, attempting recovery...")
                    if not self.login():
                        raise Exception("Session recovery failed")
                
                time.sleep(config.CHECK_INTERVAL)
                
        except Exception as e:
            logger.error(f"Session maintenance error: {str(e)}")
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
