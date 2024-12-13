import os
import shutil
from pathlib import Path
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodebaseMigration:
    def __init__(self):
        self.migration_log = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = f"server/migration_backup_{self.timestamp}"
        
    def backup_codebase(self):
        """Create backup before migration"""
        logger.info("Creating backup of codebase...")
        shutil.copytree("server", self.backup_dir)
        
    def create_new_structure(self):
        """Create new directory structure"""
        new_dirs = [
            'server/app/core/security',
            'server/app/core/analytics',
            'server/app/core/behavior',
            'server/tests/core/security',
            'server/tests/core/analytics',
            'server/tests/core/behavior'
        ]
        
        for dir_path in new_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            
    def move_files(self):
        """Move files to new locations"""
        moves = {
            'server/app/api/v2/utils/auth': 'server/app/core/security/auth',
            'server/app/core/utils/security/crypto': 'server/app/core/security/crypto',
            'server/app/services/behavior_analysis_service.py': 'server/app/core/behavior/analyzer.py',
            'server/app/services/analytics_service.py': 'server/app/core/analytics/analyzer.py'
        }
        
        for old_path, new_path in moves.items():
            if os.path.exists(old_path):
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                shutil.move(old_path, new_path)
                logger.info(f"Moved: {old_path} -> {new_path}")
                self.migration_log.append(f"Moved {old_path} to {new_path}")

    def update_imports(self):
        """Update import statements"""
        import_mappings = {
            r'from app\.api\.v2\.utils\.auth': 'from app.core.security.auth',
            r'from app\.core\.utils\.security\.crypto': 'from app.core.security.crypto',
            r'from app\.services\.behavior_analysis_service': 'from app.core.behavior.analyzer',
            r'from app\.services\.analytics_service': 'from app.core.analytics.analyzer'
        }
        
        for file_path in Path('server').rglob('*.py'):
            self._update_file_imports(file_path, import_mappings)

    def _update_file_imports(self, file_path: Path, mappings: dict):
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            original = content
            for pattern, replacement in mappings.items():
                content = re.sub(pattern, replacement, content)

            if content != original:
                with open(file_path, 'w') as f:
                    f.write(content)
                logger.info(f"Updated imports in: {file_path}")
                self.migration_log.append(f"Updated imports in {file_path}")
        except Exception as e:
            logger.error(f"Error updating {file_path}: {e}")

    def add_deprecation_warnings(self):
        """Add deprecation warnings to old files"""
        warning_template = '''import warnings

warnings.warn(
    "{message}",
    DeprecationWarning,
    stacklevel=2
)
'''
        old_paths = [
            'server/app/api/v2/utils',
            'server/app/core/utils/security'
        ]
        
        for old_path in old_paths:
            if os.path.exists(old_path):
                for file_path in Path(old_path).rglob('*.py'):
                    self._add_warning_to_file(file_path, warning_template)

    def _add_warning_to_file(self, file_path: Path, template: str):
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            warning = template.format(
                message=f"This module is deprecated and will be removed in future versions. "
                       f"Use the new location in app.core.* instead."
            )

            with open(file_path, 'w') as f:
                f.write(warning + content)
            logger.info(f"Added deprecation warning to: {file_path}")
            self.migration_log.append(f"Added deprecation warning to {file_path}")
        except Exception as e:
            logger.error(f"Error adding warning to {file_path}: {e}")

    def save_migration_log(self):
        """Save migration log to file"""
        log_file = f"server/migration_log_{self.timestamp}.txt"
        with open(log_file, 'w') as f:
            f.write('\n'.join(self.migration_log))
        logger.info(f"Migration log saved to: {log_file}")

def run_migration():
    migration = CodebaseMigration()
    
    try:
        # Execute migration steps
        migration.backup_codebase()
        migration.create_new_structure()
        migration.move_files()
        migration.update_imports()
        migration.add_deprecation_warnings()
        migration.save_migration_log()
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Restore from backup if needed
        if os.path.exists(migration.backup_dir):
            shutil.rmtree("server")
            shutil.copytree(migration.backup_dir, "server")
            logger.info("Restored from backup")

if __name__ == '__main__':
    run_migration() 