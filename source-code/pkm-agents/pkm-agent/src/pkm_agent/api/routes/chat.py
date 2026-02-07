"""Chat API endpoints."""

from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from pkm_agent.api.server import get_pkm_app
from pkm_agent.app import PKMAgentApp

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    use_context: bool = True

@router.post("/")
async def chat(
    request: ChatRequest,
    app: PKMAgentApp = Depends(get_pkm_app)
):
    """Chat with the agent (streaming response)."""
    
    async def stream_generator() -> AsyncIterator[str]:
        async for chunk in app.chat(
            message=request.message,
            conversation_id=request.conversation_id,
            use_context=request.use_context
        ):
            yield chunk

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )
