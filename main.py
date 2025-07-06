#!/usr/bin/env python3
"""
VisionSeal Production Entry Point
Simple uvicorn server start for Railway deployment
"""
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable with fallback
    port = int(os.getenv("PORT", 8080))
    
    # Start uvicorn server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=1
    )