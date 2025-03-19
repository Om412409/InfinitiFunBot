from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

def setup_driver():
    """Configure and return ChromeDriver with optimal settings"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    
    # Reduce logging noise
    chrome_options.add_argument('--log-level=3')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except WebDriverException as e:
        raise Exception(f"Failed to initialize WebDriver: {str(e)}")

def is_session_active(driver):
    """Check if the current session is still active"""
    try:
        # Perform a simple DOM check without refreshing
        driver.execute_script("return document.readyState")
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
