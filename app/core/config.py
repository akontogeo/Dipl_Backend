import os
import random

random.seed(42)

class Settings:
    # 1. Ορίζουμε ως βάση το Google Drive (εφόσον το έχεις κάνει mount)
    # Προσοχή: Βεβαιώσου ότι έχεις φτιάξει τον φάκελο Dipl_Backend στο Drive σου!
    DRIVE_BASE = "/content/drive/MyDrive/Dipl_Backend"
    
    # 2. Αν το Drive δεν είναι συνδεδεμένο (π.χ. το τρέχεις τοπικά), 
    # χρησιμοποίησε τον παλιό τρόπο ως εναλλακτική
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Τελική επιλογή φακέλων: Αν υπάρχει το Drive, σώσε εκεί. Αν όχι, τοπικά.
    FINAL_BASE = DRIVE_BASE if os.path.exists("/content/drive") else BASE_DIR

    # Οι φάκελοι πλέον θα δείχνουν στο Drive
    DATASETS_DIR = os.path.join(FINAL_BASE, "datasets")
    WEIGHTS_DIR = os.path.join(FINAL_BASE, "weights")
    UPLOADS_DIR = os.path.join(FINAL_BASE, "uploads")
    # Πρόσθεσε και τους υπόλοιπους που είδαμε ότι χρειάζεσαι
    OUTPUTS_DIR = os.path.join(FINAL_BASE, "outputs")
    PROCESSED_DIR = os.path.join(FINAL_BASE, "processed_data")

settings = Settings()
