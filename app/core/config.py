import os
import random
from pathlib import Path

random.seed(42)

class Settings:
    if os.path.exists('/content/drive/MyDrive'):
        FINAL_BASE = "/content/drive/MyDrive/Dipl_Backend_Backup"
    else:
        # Αν όχι, αποθήκευση τοπικά στο project folder του Colab
        FINAL_BASE = "/content/Dipl_Backend"
    
    # 2. Αν τρέχεις τοπικά στο PC σου (Windows/Mac), βρίσκει το φάκελο του project
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Ορισμός των φακέλων
    DATASETS_DIR = os.path.join(FINAL_BASE, "datasets")
    TRAINING_RESULTS_DIR = os.path.join(FINAL_BASE, "training_results")
    UPLOADS_DIR = os.path.join(FINAL_BASE, "uploads")
    OUTPUTS_DIR = os.path.join(FINAL_BASE, "outputs")
    PROCESSED_DIR = os.path.join(FINAL_BASE, "processed_data")

    # ΑΥΤΟΜΑΤΗ ΔΗΜΙΟΥΡΓΙΑ ΦΑΚΕΛΩΝ (για να μην κρασάρει το API)
    @classmethod
    def create_directories(cls):
        for folder in [cls.DATASETS_DIR, cls.TRAINING_RESULTS_DIR, cls.UPLOADS_DIR, cls.OUTPUTS_DIR, cls.PROCESSED_DIR]:
            os.makedirs(folder, exist_ok=True)
        # ΠΡΟΣΘΕΣΕ ΑΥΤΟ: Δημιουργία του Backup φακέλου στο Drive
        if cls.IS_COLAB:
            os.makedirs(cls.DRIVE_BACKUP_DIR, exist_ok=True)
            print(f"📂 Backup folder initialized at: {cls.DRIVE_BACKUP_DIR}")
# Δημιουργούμε τους φακέλους αμέσως
Settings.create_directories()
settings = Settings()
