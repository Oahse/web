#!/usr/bin/env python3
"""
ARQ Worker Startup Script
Run this to start the ARQ background task worker
"""
import asyncio
import logging
from arq import run_worker
from lib.arq_worker import WorkerSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Start the ARQ worker"""
    logger.info("Starting ARQ worker...")
    run_worker(WorkerSettings)

if __name__ == "__main__":
    main()