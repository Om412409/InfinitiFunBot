import os

# Credentials from environment variables
USERNAME = os.getenv('INFINITI_USERNAME', '')
PASSWORD = os.getenv('INFINITI_PASSWORD', '')

# URLs
LOGIN_URL = "https://dash.infiniti.fun/earn/afk"

# WebDriver Settings
IMPLICIT_WAIT = 30  # Seconds for implicit waits
PAGE_LOAD_TIMEOUT = 45  # Seconds for page loads
SCRIPT_TIMEOUT = 45  # Seconds for script execution
NETWORK_TIMEOUT = 30  # Seconds for network operations

# Session Settings
SESSION_CHECK_INTERVAL = 60  # Check session every minute
MAX_SESSION_TIME = 24 * 60 * 60  # Maximum session time (24 hours)
MAX_SCREENSHOT_AGE = 24  # Maximum age for screenshots in hours

# Error Recovery
MAX_RETRIES = 3  # Maximum number of retries for operations
RETRY_DELAY = 5  # Initial delay between retries in seconds