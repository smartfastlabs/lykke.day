import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lykke.infrastructure.gateways.sendgrid import SendGridGateway  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a test email using the SendGrid gateway.",
    )
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Plain text body")
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    gateway = SendGridGateway()
    await gateway.send_message(
        email_address=args.to,
        subject=args.subject,
        body=args.body,
    )


if __name__ == "__main__":
    asyncio.run(_main())
