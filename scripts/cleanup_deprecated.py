import shutil
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_deprecated():
    """Remove deprecated code paths"""
    deprecated_paths = [
        'server/app/api/v2/utils/auth',
        'server/app/core/utils/security',
        'server/app/services/behavior_analysis_service.py',
        'server/app/services/analytics_service.py'
    ]
    
    # Create backup before removal
    backup_dir = f"server/deprecated_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    for path in deprecated_paths:
        if os.path.exists(path):
            # Backup first
            rel_path = os.path.relpath(path, 'server')
            backup_path = os.path.join(backup_dir, rel_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            if os.path.isdir(path):
                shutil.copytree(path, backup_path)
                shutil.rmtree(path)
            else:
                shutil.copy2(path, backup_path)
                os.remove(path)
                
            logger.info(f"Removed deprecated path: {path}")
            logger.info(f"Backup created at: {backup_path}")

if __name__ == '__main__':
    cleanup_deprecated() 