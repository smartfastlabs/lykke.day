import asyncio
import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import Response
from loguru import logger

from lykke.core.config import settings


@dataclass(frozen=True)
class RelayResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes


class WebhookRelayManager:
    def __init__(self) -> None:
        self._websocket: WebSocket | None = None
        self._relay_id: str | None = None
        self._connected_at: datetime | None = None
        self._pending: dict[str, asyncio.Future[RelayResponse]] = {}
        self._state_lock = asyncio.Lock()

    def is_enabled(self) -> bool:
        return settings.WEBHOOK_RELAY_ENABLED

    def is_connected(self) -> bool:
        return self._websocket is not None

    async def handle_connection(
        self, websocket: WebSocket, relay_id: str, token: str | None
    ) -> None:
        if not settings.WEBHOOK_RELAY_ENABLED:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if not token or token != settings.WEBHOOK_RELAY_TOKEN:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        await self._set_connection(websocket, relay_id)

        await websocket.send_json({"type": "relay_ready", "relay_id": relay_id})
        try:
            while True:
                message = await websocket.receive_json()
                await self._handle_message(message)
        except WebSocketDisconnect:
            logger.info("Webhook relay disconnected (relay_id={})", relay_id)
        except Exception as exc:
            logger.error("Webhook relay error: {}", exc)
        finally:
            await self._clear_connection(websocket)

    async def proxy_request(self, request: Request) -> Response | None:
        if not (self.is_enabled() and self.is_connected()):
            return None

        websocket = self._websocket
        if websocket is None:
            return None

        request_id = str(uuid4())
        future = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future

        try:
            body = await request.body()
            payload = {
                "type": "webhook_request",
                "id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": request.url.query,
                "headers": _filter_headers(dict(request.headers)),
                "body_b64": base64.b64encode(body).decode("ascii"),
            }

            await websocket.send_json(payload)
            relay_response = await asyncio.wait_for(
                future, timeout=settings.WEBHOOK_RELAY_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            logger.warning("Webhook relay timed out (id={})", request_id)
            return Response(status_code=status.HTTP_504_GATEWAY_TIMEOUT)
        except Exception as exc:
            logger.error("Webhook relay failed (id={}): {}", request_id, exc)
            return Response(status_code=status.HTTP_502_BAD_GATEWAY)
        finally:
            self._pending.pop(request_id, None)

        return Response(
            content=relay_response.body,
            status_code=relay_response.status_code,
            headers=relay_response.headers,
        )

    async def _set_connection(self, websocket: WebSocket, relay_id: str) -> None:
        async with self._state_lock:
            if self._websocket and self._websocket is not websocket:
                await self._websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
            self._websocket = websocket
            self._relay_id = relay_id
            self._connected_at = datetime.now(UTC)
            logger.info(
                "Webhook relay connected (relay_id={}, connected_at={})",
                relay_id,
                self._connected_at.isoformat(),
            )

    async def _clear_connection(self, websocket: WebSocket) -> None:
        async with self._state_lock:
            if self._websocket is websocket:
                self._websocket = None
                self._relay_id = None
                self._connected_at = None

            if self._pending:
                for pending_future in self._pending.values():
                    if not pending_future.done():
                        pending_future.set_exception(RuntimeError("Relay disconnected"))
                self._pending.clear()

    async def _handle_message(self, message: dict[str, Any]) -> None:
        if message.get("type") != "webhook_response":
            return

        response_id = message.get("id")
        if not response_id:
            return

        future = self._pending.get(response_id)
        if future is None or future.done():
            return

        try:
            body = base64.b64decode(message.get("body_b64") or "")
            status_code = int(message.get("status_code") or 502)
            headers = message.get("headers") or {}
            future.set_result(
                RelayResponse(status_code=status_code, headers=headers, body=body)
            )
        except Exception as exc:
            future.set_exception(exc)


def _filter_headers(headers: dict[str, str]) -> dict[str, str]:
    excluded = {"host", "content-length", "connection"}
    return {key: value for key, value in headers.items() if key.lower() not in excluded}


webhook_relay_manager = WebhookRelayManager()
