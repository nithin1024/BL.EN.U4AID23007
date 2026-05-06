import logging
import sys
import os

class LoggingMiddleware:
    def __init__(self, name="AppLogger"):
        self.logger = logging.getLogger(name)
        if not self.logger.hasHandlers():
            self.logger.setLevel(logging.DEBUG)
            
            # File Handler
            log_dir = os.path.dirname(os.path.abspath(__file__))
            fh = logging.FileHandler(os.path.join(log_dir, 'application.log'))
            fh.setLevel(logging.DEBUG)
            
            # Console Handler
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)

    def debug(self, message):
        self.logger.debug(message)

# Global instance for easy import
logger = LoggingMiddleware()
