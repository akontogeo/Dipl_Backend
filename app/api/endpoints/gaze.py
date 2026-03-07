from fastapi import APIRouter, UploadFile, File
import os
import shutil
import asyncio
from app.services.gaze_service import GazeService

router = APIRouter()
gaze_service = GazeService()

UPLOAD_DIR = "uploads/gaze_logs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/list-sessions")
async def list_sessions():
    # Τρέχουμε το filesystem operation σε thread pool για να μην μπλοκάρει
    loop = asyncio.get_event_loop()
    
    def _get_sessions():
        sessions_dir = "processed_data/sessions"
        if not os.path.exists(sessions_dir):
            return []
        return [d for d in os.listdir(sessions_dir) 
                if os.path.isdir(os.path.join(sessions_dir, d))]
    
    sessions = await loop.run_in_executor(None, _get_sessions)
    return {"sessions": sessions}

@router.post("/process-gaze")
async def process_gaze(session_name: str, file: UploadFile = File(...)):
    # Δημιουργία session-based directories για uploads και processed
    session_upload_dir = os.path.join("uploads/sessions", session_name, "gaze_logs")
    session_output_dir = os.path.join("processed_data/sessions", session_name, "gaze_csv")
    os.makedirs(session_upload_dir, exist_ok=True)
    os.makedirs(session_output_dir, exist_ok=True)
    
    # 1. Αποθήκευση του αρχείου .txt που ανέβασε ο χρήστης στο session folder
    input_path = os.path.join(session_upload_dir, file.filename)
    output_filename = f"processed_{file.filename.replace('.txt', '.csv')}"
    output_path = os.path.join(session_output_dir, output_filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Επεξεργασία
    records_count = gaze_service.process_gaze_file(input_path, output_path)

    return {
        "status": "success",
        "session_name": session_name,
        "records": records_count,
        "csv_name": output_filename,
        "path": output_path
    }