"""Entry point for running the actor via `python -m src`."""
import asyncio
from src.main import main

if __name__ == '__main__':
    asyncio.run(main())
