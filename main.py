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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_browser():
    """Set up Chrome browser with optimal settings"""
    logger.info("Setting up Chrome WebDriver...")
    chrome_options = Options()

    # Basic Chrome options
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')

    # Anti-bot detection
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option('prefs', {
        'credentials_enable_service': False,
        'profile.password_manager_enabled': False
    })

    try:
        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)

        # Stealth script
        stealth_js = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
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

def take_screenshot(driver, status="success"):
    """Take a screenshot with timestamp"""
    try:
        os.makedirs('screenshots', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'screenshots/{status}_{timestamp}.png'
        driver.save_screenshot(filename)
        logger.info(f"Screenshot saved as: {filename}")
    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")

def wait_for_element(driver, by, value, timeout=30):
    """Wait for element with better error handling"""
    try:
        logger.info(f"Waiting for element: {value}")
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

        # Additional visibility check
        if not element.is_displayed():
            logger.error(f"Element found but not visible: {value}")
            take_screenshot(driver, "error_not_visible")
            raise TimeoutException(f"Element not visible: {value}")

        # Wait for clickability
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((by, value))
        )

        logger.info(f"Element found and interactive: {value}")
        return element
    except TimeoutException:
        logger.error(f"Element not found or not clickable: {value}")
        logger.error(f"Current URL: {driver.current_url}")
        logger.error(f"Page source excerpt: {driver.page_source[:1000]}")
        take_screenshot(driver, "error_not_found")
        raise

def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def verify_dashboard(driver):
    """Verify dashboard presence"""
    try:
        elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'dashboard')]")
        if elements and elements[0].is_displayed():
            return True
        return False
    except Exception as e:
        logger.error(f"Dashboard verification error: {str(e)}")
        return False

def main():
    driver = None
    try:
        # Initial setup
        username, password = verify_credentials()
        logger.info("Credentials verified")

        driver = setup_browser()

        # Navigate to login page
        logger.info("Navigating to login page...")
        driver.get("https://dash.infiniti.fun/earn/afk")

        # Wait for page load and check redirects
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        logger.info(f"Page loaded - URL: {driver.current_url}")
        logger.info(f"Page title: {driver.title}")

        # Take screenshot of initial page
        take_screenshot(driver, "initial_page")
        time.sleep(3)  # Wait for dynamic content

        # Attempt to find login form elements
        try:
            # Try both input name and ID
            selectors = [
                (By.NAME, "username"),
                (By.ID, "username"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "input[type='email']")
            ]

            username_field = None
            for by, value in selectors:
                try:
                    username_field = wait_for_element(driver, by, value)
                    if username_field:
                        logger.info(f"Found username field with selector: {by}={value}")
                        break
                except:
                    continue

            if not username_field:
                raise Exception("Could not find username field with any selector")

            username_field.clear()
            username_field.send_keys(username)
            logger.info("Username entered")

            # Similar approach for password field
            password_selectors = [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.CSS_SELECTOR, "input[type='password']")
            ]

            password_field = None
            for by, value in password_selectors:
                try:
                    password_field = wait_for_element(driver, by, value)
                    if password_field:
                        logger.info(f"Found password field with selector: {by}={value}")
                        break
                except:
                    continue

            if not password_field:
                raise Exception("Could not find password field with any selector")

            password_field.clear()
            password_field.send_keys(password)
            logger.info("Password entered")

            # Try different button selectors
            button_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'Sign in')]")
            ]

            submit_button = None
            for by, value in button_selectors:
                try:
                    submit_button = wait_for_element(driver, by, value)
                    if submit_button:
                        logger.info(f"Found submit button with selector: {by}={value}")
                        break
                except:
                    continue

            if not submit_button:
                raise Exception("Could not find submit button with any selector")

            submit_button.click()
            logger.info("Login form submitted")

            # Check for error messages
            try:
                error_message = driver.find_element(By.CSS_SELECTOR, ".error-message, .alert-error")
                if error_message.is_displayed():
                    logger.error(f"Login error message found: {error_message.text}")
                    take_screenshot(driver, "error_login_failed")
                    raise Exception(f"Login failed: {error_message.text}")
            except NoSuchElementException:
                pass  # No error message found, continue

            # Wait for dashboard
            logger.info("Waiting for dashboard...")
            dashboard = wait_for_element(driver, By.XPATH, "//div[contains(@class, 'dashboard')]")

            if dashboard:
                logger.info("Successfully logged in")
                take_screenshot(driver, "success")

                # Track session duration
                start_time = time.time()
                logger.info("Starting session tracking...")

                while True:
                    try:
                        # Check if session is active
                        driver.execute_script("return document.readyState")

                        # Verify dashboard is still visible
                        if not verify_dashboard(driver):
                            logger.error("Dashboard no longer visible")
                            take_screenshot(driver, "error_session_lost")
                            break

                        # Log duration
                        duration = int(time.time() - start_time)
                        formatted_time = format_duration(duration)
                        logger.info(f"Session active for {formatted_time}")

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
        logger.error(f"Error occurred: {str(e)}")
        if driver:
            take_screenshot(driver, "error_final")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed successfully")
            except:
                logger.error("Error closing browser")

if __name__ == "__main__":
    main()