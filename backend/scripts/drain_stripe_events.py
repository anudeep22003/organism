from __future__ import annotations

import argparse
import asyncio

from dotenv import load_dotenv

load_dotenv(override=False, dotenv_path=".env.local")

import core.auth.models  # noqa: E402, I001
import core.payments.models  # noqa: E402, I001, F401
from core.infrastructure.database import configure_psycopg_json_dumps  # noqa: E402
from core.payments.webhooks import StripeEventDrainer  # noqa: E402

configure_psycopg_json_dumps()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay persisted Stripe events.")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of Stripe events to drain in one batch.",
    )
    parser.add_argument(
        "--drain-all",
        action="store_true",
        help="Keep draining batches until no drainable events remain.",
    )
    return parser.parse_args()


async def _run() -> None:
    args = parse_args()
    drainer = StripeEventDrainer()

    total_processed = 0
    total_retryable_failed = 0
    total_terminal_failed = 0
    total_already_processed = 0

    while True:
        summary = await drainer.drain(limit=args.limit)
        total_processed += summary.processed
        total_retryable_failed += summary.retryable_failed
        total_terminal_failed += summary.terminal_failed
        total_already_processed += summary.already_processed

        print(
            "stripe drain batch:",
            {
                "scanned": summary.scanned,
                "processed": summary.processed,
                "retryable_failed": summary.retryable_failed,
                "terminal_failed": summary.terminal_failed,
                "already_processed": summary.already_processed,
            },
        )

        if not args.drain_all or summary.scanned == 0:
            break

    print(
        "stripe drain total:",
        {
            "processed": total_processed,
            "retryable_failed": total_retryable_failed,
            "terminal_failed": total_terminal_failed,
            "already_processed": total_already_processed,
        },
    )


if __name__ == "__main__":
    asyncio.run(_run())
