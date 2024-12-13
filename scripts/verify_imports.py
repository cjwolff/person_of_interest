import ast
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_imports():
    """Verify all imports are using new structure"""
    old_patterns = [
        'app.api.v2.utils.auth',
        'app.core.utils.security',
        'app.services.behavior_analysis_service',
        'app.services.analytics_service'
    ]
    
    issues = []
    
    for file_path in Path('server').rglob('*.py'):
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    module = node.names[0].name if isinstance(node, ast.Import) else node.module
                    if any(pattern in str(module) for pattern in old_patterns):
                        issues.append(f"Old import pattern in {file_path}: {module}")
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
            
    return issues

if __name__ == '__main__':
    issues = verify_imports()
    if issues:
        logger.warning("Found old import patterns:")
        for issue in issues:
            logger.warning(issue)
    else:
        logger.info("All imports are using new structure") 