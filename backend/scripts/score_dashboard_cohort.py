import argparse

from backend.db.session import get_engine
from backend.services.scoring_service import ScoringService


def main() -> None:
    parser = argparse.ArgumentParser(description="Score the configured synthetic dashboard cohort")
    parser.add_argument("--generation-version", default="mvp_v2.3")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = ScoringService(get_engine()).score_generation(
        args.generation_version, args.dry_run
    )
    print(result)


if __name__ == "__main__":
    main()

