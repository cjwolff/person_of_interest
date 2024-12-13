import pytest
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tests():
    """Run all tests and verify functionality"""
    test_paths = [
        'server/tests/core/security',
        'server/tests/core/analytics',
        'server/tests/core/behavior'
    ]
    
    failed_tests = []
    
    for path in test_paths:
        logger.info(f"Running tests in {path}")
        result = pytest.main([path, '-v'])
        if result != 0:
            failed_tests.append(path)
            
    return failed_tests

if __name__ == '__main__':
    failed = run_tests()
    if failed:
        logger.error("Tests failed in the following directories:")
        for path in failed:
            logger.error(path)
    else:
        logger.info("All tests passed successfully") 