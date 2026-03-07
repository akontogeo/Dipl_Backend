import uuid
from fastapi import APIRouter, BackgroundTasks
from app.services.final_analysis_service import FinalAnalysisService, analysis_progress
import os

router = APIRouter()
service = FinalAnalysisService()


@router.post("/run")
async def start_analysis(background_tasks: BackgroundTasks, session_name: str):
    analysis_id = str(uuid.uuid4())

    # Εντοπισμός video file
    videos_dir = f"uploads/sessions/{session_name}/videos"
    video_files = [f for f in os.listdir(videos_dir) if f.endswith('.mp4')]
    if not video_files:
        return {"status": "error", "message": "Δεν βρέθηκε video file για το session."}
    video_filename = video_files[0]  # Παίρνει το πρώτο .mp4

    video_path = os.path.join(videos_dir, video_filename)
    gaze_csv = f"processed_data/sessions/{session_name}/gaze_csv/processed_gazedata.csv"
    yolo_csv = f"processed_data/sessions/{session_name}/yolo_csv/detections_{video_filename.replace('.mp4', '.csv')}"

    output_video = f"outputs/sessions/{session_name}/final_{video_filename}"
    output_excel = f"outputs/sessions/{session_name}/results_{video_filename.replace('.mp4', '.xlsx')}"

    os.makedirs(f"outputs/sessions/{session_name}", exist_ok=True)

    background_tasks.add_task(
        service.run_master_analysis,
        analysis_id, video_path, gaze_csv, yolo_csv, output_video, output_excel
    )

    return {"analysis_id": analysis_id, "session_name": session_name, "message": "Η τελική ανάλυση ξεκίνησε!"}

@router.get("/status/{analysis_id}")
async def get_status(analysis_id: str):
    return analysis_progress.get(analysis_id, {"status": "not_found"})
