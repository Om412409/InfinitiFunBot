from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import os
import logging
import subprocess

logger = logging.getLogger(__name__)

def find_chrome_binary():
    """Find Chrome binary in the Nix store"""
    try:
        # Check common Nix store locations
        nix_paths = [
            '/nix/store/*/bin/chromium',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser'
        ]
        
        for path_pattern in nix_paths:
            import glob
            matches = glob.glob(path_pattern)
            if matches:
                return matches[0]
                
        # Fallback to which
        result = subprocess.run(['which', 'chromium'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
            
        return None
    except Exception as e:
        logger.error(f"Error finding Chrome binary: {str(e)}")
        return None

def setup_driver():
    """Configure and return ChromeDriver with optimal settings"""
    logger.info("Setting up Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # Use new headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Try to find Chrome binary
    chrome_binary = find_chrome_binary()
    if chrome_binary:
        logger.info(f"Found Chrome binary at: {chrome_binary}")
        chrome_options.binary_location = chrome_binary
    else:
        logger.warning("Could not find Chrome binary, using default location")

    # Reduce logging noise
    chrome_options.add_argument('--log-level=3')

    try:
        # Use ChromeDriver from system path
        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)

        # Set window size explicitly
        driver.set_window_size(1920, 1080)

        # Execute stealth script to avoid detection
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        logger.info("Chrome WebDriver initialized successfully")
        return driver
    except WebDriverException as e:
        logger.error(f"WebDriver initialization error: {str(e)}")
        raise Exception(f"Failed to initialize WebDriver: {str(e)}")

def is_session_active(driver):
    """Check if the current session is still active without refreshing"""
    try:
        # Check if we can interact with the page
        driver.execute_script("return document.readyState")

        # Additional check for specific element that should be present
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dashboard')]"))
        )
        return True
    except:
        return False

def wait_for_element(driver, by, value, timeout=10):
    """Wait for element to be present and visible"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        raise Exception(f"Element not found: {value}")