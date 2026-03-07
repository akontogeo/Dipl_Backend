# inference.py
# Endpoints related to inference operations
import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
import os
import shutil
from app.services.inference_service import InferenceService, inference_progress

router = APIRouter()
inference_service = InferenceService()

UPLOAD_VIDEO_DIR = "uploads/videos"
os.makedirs(UPLOAD_VIDEO_DIR, exist_ok=True)

@router.post("/start-tracking")
async def start_inference(background_tasks: BackgroundTasks, session_name: str, dataset_name: str, file: UploadFile = File(...)):
    video_id = str(uuid.uuid4())
    
    # Δημιουργία session-based directories για uploads και processed
    session_upload_dir = os.path.join("uploads/sessions", session_name, "videos")
    session_output_dir = os.path.join("processed_data/sessions", session_name, "yolo_csv")
    os.makedirs(session_upload_dir, exist_ok=True)
    os.makedirs(session_output_dir, exist_ok=True)
    
    # 1. Path για το βίντεο και το μοντέλο (αποθήκευση στο session folder)
    video_path = os.path.join(session_upload_dir, file.filename)
    model_path = f"training_results/train_{dataset_name}/weights/best.pt"
    output_csv = os.path.join(session_output_dir, f"detections_{file.filename.replace('.mp4', '.csv')}")

    # 2. Αποθήκευση βίντεο
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Προσθήκη του tracking στα Background Tasks
    background_tasks.add_task(inference_service.run_tracking, video_id,video_path, model_path, output_csv)

    return {
        "video_id": video_id,
        "session_name": session_name,
        "message": "Η επεξεργασία ξεκίνησε."
    }

@router.get("/status/{video_id}")
async def get_inference_status(video_id: str):
    data = inference_progress.get(video_id)
    
    if not data:
        return {"status": "not_found", "message": "Το ID δεν βρέθηκε ή ο server έκανε επανεκκίνηση."}
    
    return data