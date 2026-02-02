"""Connect to production webhook relay and forward to local server."""

import argparse
import asyncio
import base64
import json
import os
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
import websockets
from loguru import logger


EXCLUDED_HEADERS = {"host", "content-length", "connection"}
PREVIEW_LIMIT = 500


def _build_relay_url(base_url: str, token: str | None, relay_id: str | None) -> str:
    parsed = urlparse(base_url)
    query = dict(parse_qsl(parsed.query))
    if token:
        query["token"] = token
    if relay_id:
        query["relay_id"] = relay_id
    return urlunparse(parsed._replace(query=urlencode(query)))


def _filter_headers(headers: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower() not in EXCLUDED_HEADERS}


def _preview_body(body: bytes) -> str:
    if not body:
        return ""
    text = body.decode("utf-8", errors="replace")
    if len(text) > PREVIEW_LIMIT:
        return f"{text[:PREVIEW_LIMIT]}... (truncated)"
    return text


async def _forward_request(
    client: httpx.AsyncClient,
    target_base_url: str,
    message: dict[str, Any],
) -> dict[str, Any]:
    request_id = message.get("id")
    path = message.get("path") or "/"
    query = message.get("query") or ""
    method = message.get("method") or "POST"
    headers = _filter_headers(message.get("headers") or {})
    body = base64.b64decode(message.get("body_b64") or "")

    url = f"{target_base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{query}"

    try:
        logger.info(
            "Inbound webhook {} {} (id={}) headers={} body={}",
            method,
            url,
            request_id,
            headers,
            _preview_body(body),
        )
        response = await client.request(method, url, headers=headers, content=body)
        response_headers = _filter_headers(dict(response.headers))
        logger.info(
            "Webhook response {} (id={}) headers={} body={}",
            response.status_code,
            request_id,
            response_headers,
            _preview_body(response.content),
        )
        return {
            "type": "webhook_response",
            "id": request_id,
            "status_code": response.status_code,
            "headers": response_headers,
            "body_b64": base64.b64encode(response.content).decode("ascii"),
        }
    except Exception as exc:
        logger.error("Failed to forward webhook {}: {}", request_id, exc)
        return {
            "type": "webhook_response",
            "id": request_id,
            "status_code": 502,
            "headers": {},
            "body_b64": base64.b64encode(str(exc).encode("utf-8")).decode("ascii"),
        }


async def _run(relay_url: str, target_base_url: str, timeout: float) -> None:
    async with websockets.connect(
        relay_url,
        ping_interval=20,
        ping_timeout=20,
        max_size=None,
    ) as websocket:
        logger.info("Connected to webhook relay: {}", relay_url)
        async with httpx.AsyncClient(timeout=timeout) as client:
            while True:
                raw_message = await websocket.recv()
                message = json.loads(raw_message)
                if message.get("type") != "webhook_request":
                    continue
                response = await _forward_request(client, target_base_url, message)
                await websocket.send(json.dumps(response))


def main() -> None:
    parser = argparse.ArgumentParser(description="Webhook relay client")
    parser.add_argument(
        "--relay-url",
        default=os.getenv("WEBHOOK_RELAY_URL", ""),
        help="Production relay WebSocket URL (ws/wss)",
    )
    parser.add_argument(
        "--relay-token",
        default=os.getenv("WEBHOOK_RELAY_TOKEN", ""),
        help="Shared relay token",
    )
    parser.add_argument(
        "--relay-id",
        default=os.getenv("WEBHOOK_RELAY_ID", "default"),
        help="Relay identifier",
    )
    parser.add_argument(
        "--target-base-url",
        default=os.getenv("WEBHOOK_RELAY_TARGET_BASE_URL", "http://localhost:8080"),
        help="Local server base URL",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("WEBHOOK_RELAY_TIMEOUT", "20")),
        help="Local request timeout seconds",
    )

    args = parser.parse_args()
    if not args.relay_url:
        raise SystemExit("WEBHOOK_RELAY_URL is required (ws/wss)")

    relay_url = _build_relay_url(args.relay_url, args.relay_token, args.relay_id)
    asyncio.run(_run(relay_url, args.target_base_url, args.timeout))


if __name__ == "__main__":
    main()
