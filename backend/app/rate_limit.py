from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared by main.py (registers it on the app) and any route module that
# needs a tighter per-endpoint limit — defined here, not in main.py, so
# route modules can import it without a circular import back to main.
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
