"""Seed script for test_media_dash dashboard.

This script is now a thin wrapper around the db.seeders module.
Use `uv run python -c "from mkobi.db.seeders import ensure_test_media_dash; import asyncio; asyncio.run(ensure_test_media_dash())"` 
or let the application auto-seed in development mode.
"""

import asyncio

from mkobi.db.seeders.test_media_dash import ensure_test_media_dash


async def main() -> None:
    """Run the seed script and print summary."""
    print("Seeding test_media_dash dashboard...")

    result = await ensure_test_media_dash()

    print(f"Dashboard ID: {result['dashboard_id']}")
    print(f"Action: {result['action']}")
    print(f"Filter IDs: {result['filter_ids']}")
    print(f"Graph IDs: {result['graph_ids']}")
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())