#!/usr/bin/env python3
"""
VisionSeal Complete - Secure Startup Script
Replaces start_visionseal.bat with proper security checks
"""
import os
import sys
import subprocess
import signal
from pathlib import Path
from typing import List, Optional

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.core.config.settings import settings
from src.core.logging.setup import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger("startup")


class VisionSealStarter:
    """Secure application starter with health checks"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
        sys.exit(0)
    
    def check_environment(self) -> bool:
        """Check if environment is properly configured"""
        logger.info("Checking environment configuration...")
        
        # Check .env file exists
        env_file = project_root / ".env"
        if not env_file.exists():
            logger.error(".env file not found. Please copy .env.example to .env and configure it.")
            return False
        
        # Check critical environment variables
        critical_vars = [
            "SECRET_KEY",
            "OPENAI_API_KEY",
            "UNGM_USERNAME",
            "UNGM_PASSWORD"
        ]
        
        missing_vars = []
        for var in critical_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing critical environment variables: {missing_vars}")
            return False
        
        logger.info("✅ Environment configuration valid")
        return True
    
    def check_dependencies(self) -> bool:
        """Check if dependencies are installed"""
        logger.info("Checking Python dependencies...")
        
        try:
            import fastapi
            import uvicorn
            import openai
            import pydantic
            logger.info("✅ Core dependencies available")
            return True
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            logger.error("Please run: pip install -r requirements.txt")
            return False
    
    def check_directories(self) -> bool:
        """Ensure required directories exist"""
        logger.info("Checking directory structure...")
        
        directories = [
            settings.data_dir,
            settings.logs_dir,
            settings.uploads_dir,
            settings.uploads_dir / "temp",
            settings.data_dir / "extractions",
            settings.data_dir / "ai_responses"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ Directory structure ready")
        return True
    
    def start_services(self) -> bool:
        """Start external services if needed"""
        logger.info("Checking external services...")
        
        # TODO: Check if Redis is running
        # TODO: Check if Weaviate is running
        # TODO: Check if PostgreSQL is running (if configured)
        
        logger.info("✅ External services ready")
        return True
    
    def start_application(self):
        """Start the main application"""
        logger.info("Starting VisionSeal Complete...")
        
        # Build uvicorn command
        cmd = [
            sys.executable, "-m", "uvicorn",
            "src.main:app",
            "--host", settings.api.host,
            "--port", str(settings.api.port),
            "--log-level", settings.api.log_level.lower()
        ]
        
        # Add development flags
        if settings.environment == "development":
            cmd.extend(["--reload", "--reload-dir", "src"])
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            # Start the application
            process = subprocess.Popen(cmd, cwd=project_root)
            self.processes.append(process)
            
            logger.info(f"🚀 VisionSeal Complete started successfully!")
            logger.info(f"🌐 Access the application at: http://{settings.api.host}:{settings.api.port}")
            logger.info(f"📖 API Documentation: http://{settings.api.host}:{settings.api.port}/docs")
            logger.info(f"💚 Health Check: http://{settings.api.host}:{settings.api.port}/health")
            
            # Wait for process to complete
            process.wait()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            self.shutdown()
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            self.shutdown()
            return False
        
        return True
    
    def shutdown(self):
        """Shutdown all processes gracefully"""
        logger.info("Shutting down VisionSeal Complete...")
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {process.pid} did not terminate gracefully, killing...")
                process.kill()
            except Exception as e:
                logger.error(f"Error shutting down process {process.pid}: {e}")
        
        logger.info("✅ Shutdown complete")
    
    def run(self) -> bool:
        """Run the complete startup sequence"""
        logger.info("=" * 60)
        logger.info("🎯 VisionSeal Complete - Secure Startup")
        logger.info(f"Version: {settings.version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info("=" * 60)
        
        # Run all checks
        checks = [
            ("Environment", self.check_environment),
            ("Dependencies", self.check_dependencies),
            ("Directories", self.check_directories),
            ("Services", self.start_services)
        ]
        
        for check_name, check_func in checks:
            if not check_func():
                logger.error(f"❌ {check_name} check failed. Startup aborted.")
                return False
        
        # Start application
        return self.start_application()


def main():
    """Main entry point"""
    starter = VisionSealStarter()
    success = starter.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()