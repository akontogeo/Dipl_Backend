import os
import subprocess
from app.core.config import settings

def sync_data_to_drive():
    """
    Συγχρονίζει τα τοπικά δεδομένα του Colab (/content/Dipl_Backend_Local) 
    στο μόνιμο φάκελο του Google Drive.
    """
    # Τοπικός φάκελος (Πηγή)
    local_dir = "/content/Dipl_Backend_Local/"
    
    # Φάκελος στο Drive (Προορισμός) 
    # Βεβαιώσου ότι το DRIVE_BASE_DIR ορίζεται στο settings.py σου
    # π.χ. DRIVE_BASE_DIR = "/content/drive/MyDrive/Dipl_Backend_Backup"
    drive_dir = getattr(settings, "DRIVE_BASE_DIR", "/content/drive/MyDrive/Dipl_Backend_Backup/")

    # Δημιουργία του φακέλου στο Drive αν δεν υπάρχει
    if not os.path.exists(drive_dir):
        os.makedirs(drive_dir, exist_ok=True)

    try:
        # Εκτέλεση της εντολής rsync
        # -a: archive mode (κρατάει permissions κτλ)
        # -u: update (αντιγράφει μόνο νεότερα αρχεία)
        # -z: compression (για πιο γρήγορη μεταφορά μέσω δικτύου)
        command = f"rsync -auz {local_dir} {drive_dir}"
        
        # Τρέχουμε την εντολή στο σύστημα
        subprocess.run(command, shell=True, check=True)
        print(f"🔄 Sync Complete: {local_dir} -> {drive_dir}")
        return True
    except Exception as e:
        print(f"❌ Sync Failed: {str(e)}")
        return False
