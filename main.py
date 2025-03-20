
import atexit
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from flask import Flask
import os
import logging
import config
import signal
from threading import Event
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables
shutdown_event = Event()

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_event.set()

def setup_browser():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-notifications')

    # Anti-bot settings
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(config.IMPLICIT_WAIT)
    
    return driver

@app.route('/')
def home():
    return "Bot is running successfully!"

def run_bot():
    driver = None
    try:
        driver = setup_browser()
        logger.info("Bot is running...")

        # Example task to keep the bot alive
        while not shutdown_event.is_set():
            logger.info("Session is active")
            time.sleep(config.SESSION_CHECK_INTERVAL)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")

@atexit.register
def cleanup():
    shutdown_event.set()
    logger.info("Cleanup complete")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the bot in a separate thread
    from threading import Thread
    Thread(target=run_bot).start()

    # Start Flask server
    app.run(host='0.0.0.0', port=8080)
