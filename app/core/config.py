import os
import random
from pathlib import Path

random.seed(42)

class Settings:
    # 1. Ορίζουμε τη βάση του Colab (Τοπικός δίσκος - ΠΟΛΥ ΓΡΗΓΟΡΟΣ)
    # Χρησιμοποιούμε το /content που είναι ο standard φάκελος του Colab
    COLAB_BASE = "/content/Dipl_Backend_Local"

    # 2. Βάση για το Google Drive (Μόνιμη αποθήκευση)
    # Εδώ θα γίνονται τα backups για να μη χάνεις τίποτα
    DRIVE_BACKUP_DIR = "/content/drive/MyDrive/Dipl_Backend_Backup"
    
    # 2. Αν τρέχεις τοπικά στο PC σου (Windows/Mac), βρίσκει το φάκελο του project
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Επιλογή: Αν είμαστε σε Colab, χρησιμοποίησε τον τοπικό φάκελο /content
    # αλλιώς χρησιμοποίησε το BASE_DIR του project
    IS_COLAB = os.path.exists("/content")
    FINAL_BASE = COLAB_BASE if IS_COLAB else BASE_DIR

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

# Δημιουργούμε τους φακέλους αμέσως
Settings.create_directories()
settings = Settings()
