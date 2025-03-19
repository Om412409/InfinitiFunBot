import os

# Credentials from environment variables
USERNAME = os.getenv('INFINITI_USERNAME', '')
PASSWORD = os.getenv('INFINITI_PASSWORD', '')

# URLs
LOGIN_URL = "https://dash.infiniti.fun/earn/afk"

# WebDriver Settings
IMPLICIT_WAIT = 10
PAGE_LOAD_TIMEOUT = 30
SCRIPT_TIMEOUT = 30

# Session Settings
CHECK_INTERVAL = 60  # Check session status every 60 seconds
