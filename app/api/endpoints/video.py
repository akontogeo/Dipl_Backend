from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from app.core.config import settings
import os
import urllib.parse

router = APIRouter()

@router.get("/download")
async def download_video(file_path: str = Query(...)):
    # 1. Καθαρίζουμε το path από τα %CE%A34 κτλ
    decoded_path = urllib.parse.unquote(file_path)
    
    # 2. Φτιάχνουμε το πλήρες path για το Colab
    if decoded_path.startswith("/content"):
        abs_path = decoded_path
    else:
        abs_path = os.path.join(settings.FINAL_BASE, decoded_path)

    # 3. Έλεγχος αν υπάρχει όντως το αρχείο
    if not os.path.exists(abs_path):
        print(f"❌ DOWNLOAD ERROR: File not found at {abs_path}")
        raise HTTPException(status_code=404, detail="Το αρχείο δεν βρέθηκε στο διακομιστή")

    # 4. Επιστροφή αρχείου
    # Το filename παραμέτρος είναι που λέει στον browser "ΚΑΤΕΒΑΣΕ ΤΟ, ΜΗΝ ΤΟ ΠΑΙΞΕΙΣ"
    return FileResponse(
        path=abs_path,
        media_type='video/mp4',
        filename=os.path.basename(abs_path) 
    )
