import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.final_analysis_service import FinalAnalysisService, analysis_progress
from app.core.config import settings
import os

router = APIRouter()
service = FinalAnalysisService()

@router.post("/run")
async def start_analysis(background_tasks: BackgroundTasks, session_name: str):
    analysis_id = str(uuid.uuid4())
    session_name = session_name.strip()

    # 1. Σωστά Paths χρησιμοποιώντας το settings (Απόλυτα paths στο Local)
    session_upload_dir = os.path.join(settings.UPLOADS_DIR, "sessions", session_name, "videos")
    session_gaze_dir = os.path.join(settings.PROCESSED_DIR, "sessions", session_name)
    session_yolo_dir = os.path.join(settings.PROCESSED_DIR, "sessions", session_name, "yolo_csv")
    session_output_dir = os.path.join(settings.OUTPUTS_DIR, "sessions", session_name)

    # 2. Εντοπισμός video file
    if not os.path.exists(session_upload_dir):
         raise HTTPException(status_code=404, detail="Session video directory not found")

    video_files = [f for f in os.listdir(session_upload_dir) if f.endswith('.mp4')]
    if not video_files:
        return {"status": "error", "message": "Δεν βρέθηκε video file για το session."}
    
    video_filename = video_files[0]
    video_path = os.path.join(session_upload_dir, video_filename)

    # 3. Σύνδεση με τα CSV (Προσοχή: Τα ονόματα πρέπει να είναι ίδια με αυτά που σώζουν τα άλλα endpoints)
    # Εδώ χρησιμοποιούμε τα ονόματα που ορίσαμε στο gaze.py και inference.py
    gaze_csv = os.path.join(session_gaze_dir, "processed_gazedata.csv")
    yolo_csv = os.path.join(session_yolo_dir, "detections_scenevideo.csv")

    # 4. Output Paths
    output_video = os.path.join(session_output_dir, f"final_{video_filename}")
    output_excel = os.path.join(session_output_dir, f"results_{session_name}.xlsx")

    os.makedirs(session_output_dir, exist_ok=True)

    # Έλεγχος αν υπάρχουν τα αρχεία πριν ξεκινήσει η βαριά ανάλυση
    if not os.path.exists(gaze_csv) or not os.path.exists(yolo_csv):
        return {
            "status": "error", 
            "message": f"Λείπουν αρχεία! Gaze: {os.path.exists(gaze_csv)}, YOLO: {os.path.exists(yolo_csv)}"
        }

    background_tasks.add_task(
        service.run_master_analysis,
        analysis_id, video_path, gaze_csv, yolo_csv, output_video, output_excel
    )

    return {
        "analysis_id": analysis_id, 
        "session_name": session_name, 
        "message": "Η τελική ανάλυση ξεκίνησε στο Local!"
    }

@router.get("/status/{analysis_id}")
async def get_status(analysis_id: str):
    return analysis_progress.get(analysis_id, {"status": "not_found"})
