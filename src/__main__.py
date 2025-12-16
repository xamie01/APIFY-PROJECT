"""
Apify actor entry point for O-SATE.

This file is required by Apify to run Python actors.
It imports and runs the main function from src.main module.
"""
import asyncio
from src.main import main

if __name__ == '__main__':
    asyncio.run(main())
