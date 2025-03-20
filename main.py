import atexit
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
import signal
from functools import wraps
import config
from threading import Event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Global variables
running = True
shutdown_event = Event()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    running = False
    shutdown_event.set()

def cleanup_screenshots():
    """Clean up old screenshots while keeping the most recent success"""
    try:
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
            return

        current_time = time.time()
        kept_success = False

        # Sort screenshots by creation time (newest first)
        screenshots = []
        for filename in os.listdir('screenshots'):
            if filename.endswith('.png'):
                filepath = os.path.join('screenshots', filename)
                ctime = os.path.getctime(filepath)
                screenshots.append((ctime, filepath, filename))
        screenshots.sort(reverse=True)

        # Process screenshots
        for ctime, filepath, filename in screenshots:
            file_age = current_time - ctime

            # Keep most recent success screenshot
            if 'success' in filename and not kept_success:
                kept_success = True
                logger.info(f"Keeping success screenshot: {filename}")
                continue

            # Remove old files
            if file_age > (config.MAX_SCREENSHOT_AGE * 3600):
                try:
                    os.remove(filepath)
                    logger.debug(f"Removed old screenshot: {filename}")
                except Exception as e:
                    logger.error(f"Error removing screenshot {filename}: {e}")

        logger.info("Screenshot cleanup completed")
    except Exception as e:
        logger.error(f"Error during screenshot cleanup: {str(e)}")

def retry_on_exception(retries=None, delay=None):
    """Retry decorator with exponential backoff"""
    retries = retries or config.MAX_RETRIES
    delay = delay or config.RETRY_DELAY

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == retries - 1:
                        logger.error(f"Final attempt failed for {func.__name__}: {str(e)}")
                        raise
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            raise last_exception
        return wrapper
    return decorator

def setup_browser():
    """Set up Chrome browser with enhanced anti-bot measures"""
    logger.info("Setting up Chrome WebDriver...")
    chrome_options = Options()

    # Basic Chrome options
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-notifications')

    # Anti-bot measures
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)

        # Configure timeouts
        driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(config.IMPLICIT_WAIT)
        driver.set_script_timeout(config.SCRIPT_TIMEOUT)

        # Apply stealth script
        stealth_js = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
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

@retry_on_exception()
def verify_credentials():
    """Verify that required credentials are available"""
    username = config.USERNAME
    password = config.PASSWORD

    if not username or not password:
        raise ValueError("Missing credentials - please set INFINITI_USERNAME and INFINITI_PASSWORD environment variables")

    return username, password

def take_screenshot(driver, status="success"):
    """Take a screenshot with enhanced error reporting"""
    try:
        os.makedirs('screenshots', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'screenshots/{status}_{timestamp}.png'
        driver.save_screenshot(filename)
        logger.info(f"Screenshot saved: {filename}")
        logger.info(f"Screenshot context - URL: {driver.current_url}")
        logger.info(f"Screenshot context - Title: {driver.title}")
    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")

@retry_on_exception(retries=2, delay=2)
def wait_for_element(driver, by, value, timeout=None):
    """Wait for element with enhanced error handling and logging"""
    timeout = timeout or config.IMPLICIT_WAIT
    try:
        logger.info(f"Waiting for element: {value}")
        logger.debug(f"Current page state - URL: {driver.current_url}")
        logger.debug(f"Current page state - Title: {driver.title}")

        # Wait for presence
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        logger.debug("Element found in DOM")

        # Check visibility
        if not element.is_displayed():
            logger.error(f"Element found but not visible: {value}")
            logger.debug(f"Element HTML: {element.get_attribute('outerHTML')}")
            take_screenshot(driver, "error_not_visible")
            raise TimeoutException(f"Element not visible: {value}")
        logger.debug("Element is visible")

        # Check clickability
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((by, value))
        )
        logger.debug("Element is clickable")

        logger.info(f"Element successfully found and interactive: {value}")
        return element
    except TimeoutException:
        logger.error(f"Element not found or not interactive: {value}")
        logger.error(f"Current URL: {driver.current_url}")
        logger.error(f"Page title: {driver.title}")
        logger.debug(f"Page source excerpt: {driver.page_source[:1000]}")
        take_screenshot(driver, "error_not_found")
        raise

def verify_session(driver):
    """Check if the current session is still active with enhanced logging"""
    try:
        logger.info("Verifying session status...")
        # Check if page is responsive
        driver.execute_script("return document.readyState")
        logger.debug(f"Current URL: {driver.current_url}")
        logger.debug(f"Page title: {driver.title}")

        # Check dashboard visibility
        dashboard = driver.find_element(By.CSS_SELECTOR, ".dashboard")
        if not dashboard.is_displayed():
            logger.error("Dashboard element found but not visible")
            logger.debug(f"Dashboard HTML: {dashboard.get_attribute('outerHTML')}")
            return False

        # Check for session error messages
        error_messages = driver.find_elements(By.CSS_SELECTOR, ".error-message, .alert-danger, .session-expired")
        if error_messages and any(msg.is_displayed() for msg in error_messages):
            visible_errors = [msg.text for msg in error_messages if msg.is_displayed()]
            logger.error(f"Session error messages found: {', '.join(visible_errors)}")
            return False

        logger.info("Session verification successful")
        return True
    except Exception as e:
        logger.error(f"Session verification failed: {str(e)}")
        return False

def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def cleanup_driver(driver):
    """Cleanup function for driver"""
    if driver:
        try:
            driver.quit()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

def main():
    driver = None
    try:
        # Clean up old screenshots
        cleanup_screenshots()

        # Verify credentials
        username, password = verify_credentials()
        logger.info("Credentials verified")

        # Initialize browser
        driver = setup_browser()
        atexit.register(cleanup_driver, driver)

        # Navigate to login page with retry
        max_retries = config.MAX_RETRIES
        for attempt in range(max_retries):
            try:
                logger.info("Navigating to login page...")
                driver.get(config.LOGIN_URL)

                # Wait for page load
                WebDriverWait(driver, config.PAGE_LOAD_TIMEOUT).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                time.sleep(3)  # Additional wait for dynamic content
                logger.info(f"Page loaded - Title: {driver.title}")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Page load attempt {attempt + 1} failed, retrying...")
                time.sleep(config.RETRY_DELAY)

        # Login process
        try:
            # Login form interaction
            username_field = wait_for_element(driver, By.CSS_SELECTOR, "input[type='text']")
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

            # Check for login errors
            time.sleep(2)  # Wait for error messages
            error_messages = driver.find_elements(By.CSS_SELECTOR, ".error-message, .alert-danger, .text-danger")
            if error_messages and any(msg.is_displayed() for msg in error_messages):
                visible_errors = [msg.text for msg in error_messages if msg.is_displayed()]
                error_text = ', '.join(visible_errors)
                logger.error(f"Login error detected: {error_text}")
                take_screenshot(driver, "error_login")
                raise Exception(f"Login failed: {error_text}")

            # Wait for dashboard
            logger.info("Waiting for dashboard...")
            dashboard = wait_for_element(driver, By.CSS_SELECTOR, ".dashboard")

            if dashboard:
                logger.info("Successfully logged in")
                take_screenshot(driver, "success")

                # Track session
                start_time = time.time()
                session_duration = 0
                last_success_time = time.time()
                logger.info("Starting session tracking...")

                while running and session_duration < config.MAX_SESSION_TIME:
                    try:
                        if shutdown_event.is_set():
                            logger.info("Shutdown event detected, ending session...")
                            break

                        if not verify_session(driver):
                            # Only consider it a failure if we haven't had success in the last minute
                            if time.time() - last_success_time > 60:
                                logger.error("Session verification failed")
                                take_screenshot(driver, "error")
                                break
                            else:
                                logger.warning("Temporary session verification failure, retrying...")
                                continue

                        # Update last success time
                        last_success_time = time.time()

                        # Log session duration
                        session_duration = int(time.time() - start_time)
                        formatted_time = format_duration(session_duration)
                        logger.info(f"Session active for {formatted_time}")

                        time.sleep(config.SESSION_CHECK_INTERVAL)
                    except Exception as e:
                        logger.error(f"Session verification error: {str(e)}")
                        if time.time() - last_success_time > 60:
                            take_screenshot(driver, "error")
                            break
                        else:
                            logger.warning("Temporary error in session verification, retrying...")
                            continue

                if session_duration >= config.MAX_SESSION_TIME:
                    logger.info("Maximum session time reached")

        except Exception as e:
            logger.error(f"Login process failed: {str(e)}")
            take_screenshot(driver, "error")
            raise

    except Exception as e:
        logger.error(f"Script error: {str(e)}")
        if driver:
            take_screenshot(driver, "error")
    finally:
        cleanup_driver(driver)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main()