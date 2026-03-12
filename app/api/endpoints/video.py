from fastapi.responses import FileResponse
import urllib.parse

@router.get("/video")
async def serve_video(file: str = Query(...)):
    # Καθαρισμός του path από τα %CE%A34
    decoded_path = urllib.parse.unquote(file)
    
    # Σιγουρέψου ότι το path είναι σωστό για το Colab
    if not decoded_path.startswith("/content"):
        abs_path = os.path.join(settings.FINAL_BASE, decoded_path)
    else:
        abs_path = decoded_path

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Το αρχείο χάθηκε στις διαδρομές")

    return FileResponse(
        path=abs_path,
        media_type="video/mp4",
        filename=os.path.basename(abs_path)
    )
