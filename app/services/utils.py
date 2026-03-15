import os
import subprocess
from app.core.config import settings

def sync_data_to_drive():
    local_dir = "/content/Dipl_Backend_Local/"
    
    # ΔΙΟΡΘΩΣΗ ΕΔΩ: Χρησιμοποιούμε το σωστό όνομα από τα Settings σου
    drive_dir = settings.DRIVE_BACKUP_DIR 
    
    if not os.path.exists('/content/drive/MyDrive'):
        print("ℹ️ Skip Sync: Το Google Drive δεν είναι συνδεδεμένο. Τα αρχεία παραμένουν μόνο τοπικά.")
        return False

    try:
        # Το rsync χρειάζεται προσοχή στα slashes: 
        # local_dir/ σημαίνει "αντέγραψε τα περιεχόμενα αυτού του φακέλου"
        command = f"rsync -auz {local_dir} {drive_dir}"
        
        subprocess.run(command, shell=True, check=True)
        print(f"🔄 Sync Complete: {local_dir} -> {drive_dir}")
        return True
    except Exception as e:
        print(f"❌ Sync Failed: {str(e)}")
        return False
