import os
import random
from pathlib import Path

random.seed(42)

class Settings:
    
    # --- 1. ΕΛΕΓΧΟΣ ΠΕΡΙΒΑΛΛΟΝΤΟΣ ---
    IS_COLAB = os.path.exists('/content')
    HAS_DRIVE = os.path.exists('/content/drive/MyDrive')
    
    # --- 2. ΟΡΙΣΜΟΣ ΒΑΣΙΚΟΥ PATH ---
    if HAS_DRIVE:
        FINAL_BASE = "/content/drive/MyDrive/Dipl_Backend_Backup"
    else:
        FINAL_BASE = "/content/Dipl_Backend"
    
    # Path για το rsync backup
    DRIVE_BACKUP_DIR = "/content/drive/MyDrive/Dipl_Backup_Folder"

    # Ορισμός των φακέλων
    DATASETS_DIR = os.path.join(FINAL_BASE, "datasets")
    TRAINING_RESULTS_DIR = os.path.join(FINAL_BASE, "training_results")
    UPLOADS_DIR = os.path.join(FINAL_BASE, "uploads")
    OUTPUTS_DIR = os.path.join(FINAL_BASE, "outputs")
    PROCESSED_DIR = os.path.join(FINAL_BASE, "processed_data")

    @classmethod
    def create_directories(cls):
        # Δημιουργία των τοπικών φακέλων (Colab ή Drive)
        folders = [
            cls.DATASETS_DIR, 
            cls.TRAINING_RESULTS_DIR, 
            cls.UPLOADS_DIR, 
            cls.OUTPUTS_DIR, 
            cls.PROCESSED_DIR
        ]
        
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
            print(f"📁 Directory ready: {folder}")

        # --- 4. ΔΙΟΡΘΩΣΗ ΓΙΑ ΤΟ DRIVE BACKUP ---
        # Δημιουργούμε τον φάκελο backup μόνο αν όντως υπάρχει Drive
        if cls.HAS_DRIVE:
            os.makedirs(cls.DRIVE_BACKUP_DIR, exist_ok=True)
            print(f"📂 Backup folder initialized at: {cls.DRIVE_BACKUP_DIR}")
        else:
            print("ℹ️ Drive not mounted. Skipping backup folder creation.")

# Εκτέλεση της δημιουργίας
Settings.create_directories()
settings = Settings()
