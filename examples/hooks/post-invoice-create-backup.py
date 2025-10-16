#!/usr/bin/env python3
"""
DESCRIPTION: Backup database after invoice creation
AUTHOR: OpenFatture Team
TIMEOUT: 30
REQUIRES: none (stdlib only)
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


def main():
    """Backup database after invoice creation."""
    # Get event data
    invoice_number = os.getenv("OPENFATTURE_INVOICE_NUMBER", "unknown")
    invoice_id = os.getenv("OPENFATTURE_INVOICE_ID", "unknown")

    print(f"📦 Backing up database after invoice {invoice_number} creation...")

    # Determine database path
    # Assuming SQLite database at ~/.openfatture/data/openfatture.db
    home = Path.home()
    db_path = home / ".openfatture" / "data" / "openfatture.db"

    if not db_path.exists():
        print(f"⚠️  Database not found at {db_path}")
        print("Backup skipped (not an error)")
        return 0

    # Create backup directory
    backup_dir = home / ".openfatture" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"openfatture_backup_{timestamp}_invoice_{invoice_id}.db"
    backup_path = backup_dir / backup_filename

    # Copy database file
    try:
        shutil.copy2(db_path, backup_path)
        print("✅ Database backed up successfully")
        print(f"   Location: {backup_path}")
        print(f"   Size: {backup_path.stat().st_size / 1024:.1f} KB")

        # Cleanup old backups (keep last 10)
        _cleanup_old_backups(backup_dir, keep=10)

        return 0

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return 1


def _cleanup_old_backups(backup_dir: Path, keep: int = 10):
    """Remove old backup files, keeping only the most recent."""
    backups = sorted(
        backup_dir.glob("openfatture_backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if len(backups) > keep:
        removed_count = 0
        for old_backup in backups[keep:]:
            try:
                old_backup.unlink()
                removed_count += 1
            except Exception:
                pass

        if removed_count > 0:
            print(f"🗑️  Removed {removed_count} old backup(s)")


if __name__ == "__main__":
    sys.exit(main())
