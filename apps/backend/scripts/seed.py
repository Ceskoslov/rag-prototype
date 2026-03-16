#!/usr/bin/env python3
import asyncio
import sys

from app.core.settings import settings
from app.repositories.vectorstore import ChromaRepository
from app.services.seed import SeedService


async def main() -> int:
    try:
        chroma_repo = ChromaRepository()
        seed_service = SeedService(chroma_repo, settings.redis_url)

        print("=" * 60)
        print("Seed All Departments - ARQ Job Enqueueing")
        print("=" * 60)

        print("\nChecking current seed status...")
        status = await seed_service.check_seed_status()
        print("\nCurrent document counts per department:")
        for dept, count in status.items():
            status_str = f"  {dept:20} → {count:3} documents"
            print(status_str)

        print("\nStarting seeding process...")
        results = await seed_service.seed_all_departments()

        print("\nSeeding results:")
        for dept, result_status in results.items():
            if result_status == "seeded":
                print(f"  {dept:20} → ENQUEUED (ARQ job started)")
            elif result_status == "skipped":
                print(f"  {dept:20} → SKIPPED (already populated)")

        print("\n" + "=" * 60)
        print("Seeding jobs enqueued successfully!")
        print("=" * 60)
        print("\nNote: Jobs are running in the background via ARQ worker.")
        print("      Check ARQ worker logs for ingestion progress.")
        print("      Re-run this script to check final document counts.\n")

        return 0

    except KeyboardInterrupt:
        print("\n\nSeeding interrupted by user.")
        return 130
    except Exception as exc:
        print(f"\n\nERROR: Seeding failed - {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
