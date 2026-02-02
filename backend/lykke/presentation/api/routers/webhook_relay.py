from fastapi import APIRouter, WebSocket

from lykke.presentation.webhook_relay import webhook_relay_manager

router = APIRouter()


@router.websocket("/webhook-relay")
async def webhook_relay_websocket(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    relay_id = websocket.query_params.get("relay_id") or "default"
    await webhook_relay_manager.handle_connection(websocket, relay_id, token)
