import logging

from fastapi import Response

log = logging.getLogger(__name__)
class RawASGIResponse(Response):
    """
    A dummy response class that prevents FastAPI from trying to 
    send duplicate HTTP headers after MCP has already sent them.
    """
    async def __call__(self, scope, receive, send) -> None:
        try:
            await send({"type": "http.response.body", "body": b"", "more_body": False})
        except RuntimeError as e:
            if str(e) == "Unexpected ASGI message 'http.response.body' sent, after response already completed.":
                log.debug("Received empty chunk from Uvicorn, ignoring.")
                return
            else:
                raise
        except Exception as _:
            log.error("Failed to send empty chunk to Uvicorn.")
            raise