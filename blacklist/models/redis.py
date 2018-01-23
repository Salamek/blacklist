"""Redis keys used throughout the entire application (Flask, etc.)."""

# Blacklist throttling.
POLL_SIMPLE_THROTTLE = 'blacklist:poll_simple_throttle'  # Lock.
