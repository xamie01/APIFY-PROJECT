"""Entry point for running the actor via `python -m src`."""
import asyncio
import sys

# Ensure Apify is available
try:
    from apify import Actor
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False
    print("Warning: apify package not available, running in standalone mode", file=sys.stderr)

from src.main import main

if __name__ == '__main__':
    if APIFY_AVAILABLE:
        # Use Apify's actor context
        asyncio.run(main())
    else:
        # Standalone execution
        asyncio.run(main())