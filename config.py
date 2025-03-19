import os

# Credentials from environment variables
USERNAME = os.getenv('INFINITI_USERNAME', '')
PASSWORD = os.getenv('INFINITI_PASSWORD', '')

# URLs
LOGIN_URL = "https://dash.infiniti.fun/earn/afk"

# WebDriver Settings
IMPLICIT_WAIT = 30  # Increased timeout for element waits
PAGE_LOAD_TIMEOUT = 45  # Increased timeout for page loads
SCRIPT_TIMEOUT = 45  # Increased timeout for scripts

# Session Settings
CHECK_INTERVAL = 300  # Check session status every 5 minutes to reduce server load