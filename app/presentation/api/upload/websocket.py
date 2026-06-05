"""
WebSocket endpoint for real-time upload progress tracking.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
import json
import logging

logger = logging.getLogger(__name__)

upload_ws_router = APIRouter(prefix="/ws", tags=["websocket"])


class UploadProgressManager:
    """Singleton to track upload progress across requests."""

    def __init__(self):
        self.clients: dict[int, list[WebSocket]] = {}  # upload_id -> [websockets]
        self.progress: dict[int, dict] = {}  # upload_id -> progress_dict

    async def connect(self, upload_id: int, websocket: WebSocket):
        await websocket.accept()
        if upload_id not in self.clients:
            self.clients[upload_id] = []
        self.clients[upload_id].append(websocket)
        # Send current progress if available
        if upload_id in self.progress:
            await websocket.send_json(self.progress[upload_id])

    async def disconnect(self, upload_id: int, websocket: WebSocket):
        if upload_id in self.clients:
            self.clients[upload_id].remove(websocket)
            if not self.clients[upload_id]:
                del self.clients[upload_id]

    async def broadcast_progress(self, upload_id: int, progress: dict):
        """Send progress update to all clients watching this upload."""
        self.progress[upload_id] = progress
        if upload_id in self.clients:
            disconnected = []
            for ws in self.clients[upload_id]:
                try:
                    await ws.send_json(progress)
                except Exception as e:
                    logger.warning(f"Failed to send progress to client: {e}")
                    disconnected.append(ws)
            # Clean up disconnected clients
            for ws in disconnected:
                await self.disconnect(upload_id, ws)


_progress_manager = UploadProgressManager()


def get_progress_manager() -> UploadProgressManager:
    return _progress_manager


@upload_ws_router.websocket("/uploads/{upload_id}/progress")
async def websocket_upload_progress(
    websocket: WebSocket,
    upload_id: int,
):
    """
    WebSocket endpoint for real-time upload progress.
    Client connects with: ws://localhost:8000/ws/uploads/{upload_id}/progress
    """
    manager = get_progress_manager()
    await manager.connect(upload_id, websocket)

    try:
        while True:
            # Keep connection alive, receive any messages from client
            data = await websocket.receive_text()
            # Client can send heartbeat or other messages
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(upload_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for upload {upload_id}: {e}")
        await manager.disconnect(upload_id, websocket)
