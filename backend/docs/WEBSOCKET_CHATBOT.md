# WebSocket Chatbot Implementation

## Overview

The chatbot has been migrated from HTTP to WebSocket for real-time bidirectional communication. This implementation uses persistent connections with connection-scoped entity caching to minimize database queries.

## Architecture

### Connection Flow

1. Client connects to `/api/v1/conversations/{conversation_id}/ws`
2. Server authenticates user from cookie or query parameter token
3. Server loads and caches: User, Conversation, BotPersonality
4. Server sends `connection_ack` message
5. Bidirectional message streaming begins
6. Connection maintained until client disconnects

### Key Components

#### 1. **ConnectionState** (`websocket/connection_state.py`)

A stateful presentation-layer helper that manages connection-scoped state:

- Cached entities (User, Conversation, BotPersonality)
- Repository factories
- Unit of Work factory
- Connection metadata

**Benefits:**

- Entities loaded once at connection time
- No refetching on every message
- ~60-70% reduction in database queries

#### 2. **WebSocket Endpoint** (`chatbot.py`)

Main WebSocket route handler:

- Accepts WebSocket connections
- Authenticates users
- Routes incoming messages
- Handles errors gracefully
- Manages connection lifecycle

#### 3. **Message Protocol** (`websocket_message.py`)

Structured message types for client-server communication:

**Client → Server:**

```json
{
  "type": "user_message",
  "content": "Hello bot!",
  "message_id": "optional-uuid-for-idempotency"
}
```

**Server → Client:**

```json
// Acknowledgment (uses MessageSchema)
{
  "type": "message_received",
  "message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "user",
    "content": "Hello bot!",
    "created_at": "2026-01-12T...",
    "meta": {}
  }
}

// Complete assistant message (uses MessageSchema)
{
  "type": "assistant_message",
  "message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "assistant",
    "content": "Hello! How can I help you?",
    "created_at": "2026-01-12T...",
    "meta": {}
  }
}

// Error
{
  "type": "error",
  "code": "MESSAGE_ERROR",
  "message": "Error description"
}
```

#### 4. **Authentication** (`dependencies/user.py`)

WebSocket authentication via `get_current_user_from_token`:

- Extracts JWT from cookies (browser) or query params (non-browser)
- Validates token
- Loads user from database
- Returns domain entity

## Message Flow

### User Message → Assistant Response

1. Client sends `user_message`
2. Server validates and creates `MessageEntity`
3. Server persists user message via Unit of Work
4. Server updates conversation timestamp (cached)
5. Server sends `message_received` acknowledgment
6. Server generates assistant response (currently dummy, ready for LLM)
7. Server persists assistant message
8. Server sends complete `assistant_message`

## Performance Improvements

### HTTP Approach (Old)

- ~5-7 DB queries per message:
  - Get user (auth)
  - Get conversation
  - Get bot personality
  - Insert user message
  - Insert assistant message
  - Update conversation

### WebSocket Approach (New)

- Initial connection: 3 queries (user, conversation, bot personality)
- Per message: 2-3 queries (insert messages, update conversation)
- **~60-70% reduction in queries**

## LLM Integration Ready

The implementation is ready for LLM integration:

- Replace `generate_dummy_response()` with actual LLM calls
- Response sent as complete message once generated
- Can add streaming in the future if needed

## Error Handling

Graceful error handling at multiple levels:

- Authentication errors → Close connection with error message
- Not found errors → Send error, close connection
- Message handling errors → Send error, keep connection alive
- Unknown message types → Send error, keep connection alive
- WebSocket disconnect → Clean logging, no errors

## Security

- JWT authentication required
- Token validated on connection
- User-scoped repositories
- Conversation ownership verified
- All database operations use user_id scoping

## Usage Example

### JavaScript Client

```javascript
// Connect to WebSocket
const ws = new WebSocket(
  `wss://api.lykke.day/api/v1/conversations/${conversationId}/ws`
);

ws.onopen = () => {
  console.log("Connected to chatbot");
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case "connection_ack":
      console.log("Connection established:", message);
      break;

    case "message_received":
      console.log("Message sent:", message.message.id);
      break;

    case "assistant_message":
      // Display complete assistant response (full MessageSchema)
      displayAssistantMessage(message.message);
      console.log("Response received:", message.message.id);
      break;

    case "error":
      console.error("Error:", message.code, message.message);
      break;
  }
};

// Send message
function sendMessage(content) {
  ws.send(
    JSON.stringify({
      type: "user_message",
      content: content,
      message_id: generateUUID(), // Optional for idempotency
    })
  );
}
```

### Python Client

```python
import asyncio
import json
from websockets import connect

async def chatbot_client(conversation_id: str, token: str):
    uri = f"ws://localhost:8000/api/v1/conversations/{conversation_id}/ws"

    async with connect(uri, extra_headers={"Cookie": f"lykke_auth={token}"}) as ws:
        # Receive connection ack
        ack = json.loads(await ws.recv())
        print(f"Connected: {ack}")

        # Send message
        await ws.send(json.dumps({
            "type": "user_message",
            "content": "Hello bot!"
        }))

        # Receive responses
        async for message in ws:
            data = json.loads(message)

            if data["type"] == "assistant_message":
                msg = data["message"]
                print(f"\nAssistant: {msg['content']}")
                print(f"Message ID: {msg['id']}")
                break
```

## Future Enhancements

1. **LLM Integration**: Replace `generate_dummy_response` with actual LLM calls
2. **Streaming Responses**: Add chunked streaming for long LLM responses (if needed)
3. **Connection Manager**: Track active connections for multi-client scenarios
4. **Presence Indicators**: Show when other users are typing
5. **Message History**: Send recent messages on connection
6. **Reconnection**: Handle connection drops gracefully
7. **Rate Limiting**: Prevent message spam
8. **Typing Indicators**: Real-time typing status

## Testing

To test the WebSocket endpoint:

```bash
# Using wscat (install: npm install -g wscat)
wscat -c "ws://localhost:8000/api/v1/conversations/{conversation_id}/ws" \
  -H "Cookie: lykke_auth={your_token}"

# Send message
> {"type": "user_message", "content": "Hello!"}
```

## Migration Notes

- **No backward compatibility**: HTTP endpoint removed
- **Breaking change**: Clients must migrate to WebSocket
- **Authentication**: Same JWT tokens work with WebSocket
- **Database schema**: No changes required
- **Domain layer**: No changes required
- **Application layer**: Reuses existing `SendMessageHandler` logic

## Clean Architecture Compliance

✅ **Domain Layer**: Unchanged, no WebSocket knowledge
✅ **Application Layer**: Reuses existing commands/queries
✅ **Infrastructure Layer**: No changes needed
✅ **Presentation Layer**: WebSocket-specific, properly isolated
✅ **Dependency Rules**: All respected, inner layers unaware of WebSocket

## Files Changed/Added

### Added:

- `presentation/api/websocket/` - New directory for WebSocket-specific components
- `presentation/api/websocket/connection_state.py` - Connection state management
- `presentation/api/schemas/websocket_message.py` - WebSocket message schemas

### Modified:

- `presentation/api/routers/chatbot.py` - Replaced HTTP with WebSocket
- `presentation/api/routers/dependencies/user.py` - Added WebSocket auth
- `presentation/api/schemas/__init__.py` - Export WebSocket schemas

### Removed:

- None (HTTP endpoint replaced, not removed separately)

### Architecture Note:

`ConnectionState` is a stateful, mutable presentation-layer helper class (not a value object or domain concept). It's WebSocket-specific and manages the lifecycle of a single connection.
