import os
import random

# Το seed για να είναι σταθερά τα αποτελέσματα
random.seed(42)

class Settings:
    # Βρίσκει αυτόματα τη διαδρομή του φακέλου backend
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Οι 3 φάκελοι που χρειάζεσαι οπωσδήποτε
    DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
    WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
    UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

settings = Settings()