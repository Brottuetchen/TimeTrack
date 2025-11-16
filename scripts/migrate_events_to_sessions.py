#!/usr/bin/env python3
"""
Migration script: Aggregiert bestehende Events zu Sessions.
Läuft komplett lokal auf dem Pi - keine externen API-Calls.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_path))

from datetime import datetime, timedelta
from app.database import SessionLocal
from app.services.session_aggregator import aggregate_user_events


def migrate_all_users(days_back: int = 30):
    """
    Migriert Events zu Sessions für alle User.

    Args:
        days_back: Wie viele Tage zurück sollen migriert werden (default: 30)
    """
    db = SessionLocal()

    try:
        # Find all unique users from events
        from app.models import Event
        users = db.query(Event.user_id).filter(Event.user_id.isnot(None)).distinct().all()
        users = [u[0] for u in users]

        print(f"Found {len(users)} users to migrate")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        total_sessions = 0
        for user_id in users:
            print(f"\nMigrating user: {user_id}")
            print(f"  Date range: {start_date.date()} to {end_date.date()}")

            sessions = aggregate_user_events(db, user_id, start_date, end_date)
            print(f"  Created {len(sessions)} sessions")
            total_sessions += len(sessions)

        print(f"\n✓ Migration complete!")
        print(f"  Total sessions created: {total_sessions}")

    except Exception as e:
        print(f"✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def migrate_single_user(user_id: str, days_back: int = 30):
    """
    Migriert Events zu Sessions für einen einzelnen User.

    Args:
        user_id: User ID
        days_back: Wie viele Tage zurück sollen migriert werden (default: 30)
    """
    db = SessionLocal()

    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        print(f"Migrating user: {user_id}")
        print(f"Date range: {start_date.date()} to {end_date.date()}")

        sessions = aggregate_user_events(db, user_id, start_date, end_date)
        print(f"✓ Created {len(sessions)} sessions")

    except Exception as e:
        print(f"✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate existing events to aggregated sessions (100% local)"
    )
    parser.add_argument(
        "--user",
        type=str,
        help="Migrate specific user (default: all users)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to migrate (default: 30)",
    )

    args = parser.parse_args()

    if args.user:
        migrate_single_user(args.user, args.days)
    else:
        migrate_all_users(args.days)
