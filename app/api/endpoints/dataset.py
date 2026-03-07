# dataset.py
# Endpoints related to dataset operations
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.dataset_service import DatasetService
from app.core.config import settings
import os
import shutil
import asyncio
from functools import partial

router = APIRouter()
dataset_service = DatasetService()

@router.post("/upload-zip")
async def upload_dataset(
    dataset_name: str, # Προσθέσαμε το όνομα που θα δίνει ο χρήστης
    file: UploadFile = File(...)
):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Το αρχείο πρέπει να είναι .zip")

    temp_zip_path = os.path.join(settings.UPLOADS_DIR, file.filename)
    
    with open(temp_zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Περνάμε το dataset_name στο service
    extracted_path = dataset_service.process_zip_dataset(temp_zip_path, dataset_name)
    os.remove(temp_zip_path)

    return {"message": f"Dataset {dataset_name} ready!", "location": extracted_path}

@router.get("/list")
async def list_datasets():
    # Τρέχουμε το filesystem operation σε thread pool για να μην μπλοκάρει
    loop = asyncio.get_event_loop()
    
    def _get_datasets():
        if not os.path.exists(settings.DATASETS_DIR):
            return []
        return [d for d in os.listdir(settings.DATASETS_DIR) 
                if os.path.isdir(os.path.join(settings.DATASETS_DIR, d))]
    
    datasets = await loop.run_in_executor(None, _get_datasets)
    return {"datasets": datasets}


@router.get("/stats/{dataset_name}")
async def get_dataset_stats(dataset_name: str):
    import glob
    
    base_path = os.path.join(settings.DATASETS_DIR, dataset_name)
    if not os.path.exists(base_path):
        raise HTTPException(status_code=404, detail="Dataset not found")

    stats = {}
    for split in ["train", "valid"]:
        img_path = os.path.join(base_path, split, "images")
        # Μετράμε πόσα jpg και png υπάρχουν
        images = glob.glob(os.path.join(img_path, "*.[jJ][pP]*[gG]")) + \
                 glob.glob(os.path.join(img_path, "*.png"))
        
        # Μετράμε πόσα είναι augmented (έχουν το '_aug' στο όνομα)
        aug_count = len([img for img in images if "_aug" in img])
        original_count = len(images) - aug_count
        
        stats[split] = {
            "total_images": len(images),
            "original": original_count,
            "augmented": aug_count
        }

    return {
        "dataset": dataset_name,
        "stats": stats,
        "ratio": f"{stats['train']['total_images'] / (stats['train']['total_images'] + stats['valid']['total_images']):.2%}" if (stats['train']['total_images'] + stats['valid']['total_images']) > 0 else 0
    }