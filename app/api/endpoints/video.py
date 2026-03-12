from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from app.core.config import settings
import os

router = APIRouter()

@router.get("/video")
async def serve_video(file: str = Query(..., description="Path to video file")):
    # 1. Κατασκευή Απόλυτου Path
    # Διασφαλίζουμε ότι κοιτάμε στο Local folder του Colab
    abs_path = os.path.join(settings.FINAL_BASE, file) if not file.startswith("/") else file
    
    # Debug print για να βλέπεις στο Colab τι πάει να διαβάσει
    print(f"🎬 Serving video from: {abs_path}")

    # 2. Έλεγχος αν υπάρχει
    if not os.path.exists(abs_path):
        print(f"❌ File not found at: {abs_path}")
        raise HTTPException(status_code=404, detail="Video file not found")

    # 3. Η FileResponse κάνει ΟΛΗ τη δουλειά αυτόματα:
    # - Υποστηρίζει Range requests (για να παίζει ο player)
    # - Βάζει σωστά Content-Length και Content-Type
    # - Επιτρέπει το κατέβασμα
    return FileResponse(
        path=abs_path,
        media_type="video/mp4",
        filename=os.path.basename(abs_path)
    )
