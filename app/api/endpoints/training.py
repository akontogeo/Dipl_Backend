# training.py
# Endpoints related to training operations
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.yolo_service import YOLOService
import os
import asyncio
from app.core.config import settings

router = APIRouter()
yolo_service = YOLOService()

@router.post("/start")
async def start_training(dataset_name: str, background_tasks: BackgroundTasks, epochs: int = 60):
    # Έλεγχος αν το dataset υπάρχει όντως στον φάκελο
    dataset_path = os.path.join(settings.DATASETS_DIR, dataset_name)
    if not os.path.exists(dataset_path):
        raise HTTPException(status_code=404, detail=f"Το dataset '{dataset_name}' δεν βρέθηκε!")

    # Προσθήκη της εκπαίδευσης στις εργασίες παρασκηνίου
    background_tasks.add_task(yolo_service.train_model, dataset_name, epochs)
    
    return {
        "message": f"Η εκπαίδευση για το dataset '{dataset_name}' ξεκίνησε επιτυχώς!",
        "epochs": epochs,
        "status": "running"
    }

@router.get("/status/{dataset_name}")
async def get_training_status(dataset_name: str):
    from app.services.yolo_service import training_progress
    
    if dataset_name not in training_progress:
        return {"status": "not_started", "percentage": 0}
    
    return training_progress[dataset_name]

@router.post("/stop/{dataset_name}")
async def stop_training(dataset_name: str):
    from app.services.yolo_service import training_progress
    
    if dataset_name not in training_progress:
        raise HTTPException(status_code=404, detail=f"Δεν βρέθηκε εκπαίδευση για το dataset '{dataset_name}'")
    
    if training_progress[dataset_name]["status"] not in ["training", "starting"]:
        raise HTTPException(status_code=400, detail=f"Η εκπαίδευση δεν τρέχει (status: {training_progress[dataset_name]['status']})")
    
    # Θέτουμε το flag για ακύρωση
    training_progress[dataset_name]["cancel_requested"] = True
    
    return {
        "message": f"Η εκπαίδευση για το dataset '{dataset_name}' θα σταματήσει σύντομα...",
        "dataset_name": dataset_name
    }

@router.get("/list-models")
async def list_trained_models():
    # Τρέχουμε το filesystem operation σε thread pool για να μην μπλοκάρει
    loop = asyncio.get_event_loop()
    
    def _get_models():
        training_results_dir = "training_results"
        if not os.path.exists(training_results_dir):
            return []
        return [d for d in os.listdir(training_results_dir) 
                if os.path.isdir(os.path.join(training_results_dir, d))]
    
    models = await loop.run_in_executor(None, _get_models)
    return {"models": models}

