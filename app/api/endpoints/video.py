
from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import StreamingResponse
import os

router = APIRouter()

@router.get("/video")
async def serve_video(request: Request, file: str = Query(..., description="Path to video file")):
    allowed_root = os.path.abspath("outputs/sessions/")
    abs_path = os.path.abspath(file)
    if not abs_path.startswith(allowed_root):
        return {"status": "error", "message": "Δεν επιτρέπεται πρόσβαση σε αυτό το αρχείο."}
    if not os.path.exists(abs_path):
        return {"status": "error", "message": "Το αρχείο δεν βρέθηκε."}

    file_size = os.path.getsize(abs_path)
    range_header = request.headers.get("range")
    if range_header:
        # Υποστήριξη partial content (streaming)
        range_value = range_header.replace("bytes=", "")
        start_str, end_str = range_value.split("-")
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
        chunk_size = end - start + 1
        def file_stream():
            with open(abs_path, "rb") as f:
                f.seek(start)
                yield f.read(chunk_size)
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": "video/mp4"
        }
        return StreamingResponse(file_stream(), status_code=206, headers=headers)
    else:
        def file_stream():
            with open(abs_path, "rb") as f:
                yield from f
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4"
        }
        return StreamingResponse(file_stream(), status_code=200, headers=headers)
