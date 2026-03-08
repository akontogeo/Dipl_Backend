# yolo_service.py
# Service for interacting with Ultralytics YOLO
from ultralytics import YOLO
import os
import yaml
import shutil
from app.core.config import settings
import torch
from app.services.utils import sync_data_to_drive

training_progress = {}
class YOLOService:
    def update_data_yaml(self, dataset_name: str):
        """Ενημερώνει το data.yaml με τα σωστά τοπικά paths των Windows"""
        dataset_path = os.path.abspath(os.path.join(settings.DATASETS_DIR, dataset_name))
        yaml_path = os.path.join(dataset_path, "data.yaml")
        
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Δυναμική ρύθμιση των paths για να τα βρει το YOLO
            data['path'] = dataset_path
            data['train'] = "train/images"
            data['val'] = "valid/images"
            
            with open(yaml_path, 'w') as f:
                yaml.dump(data, f)
        return yaml_path

    def train_model(self, dataset_name: str, epochs: int):
        # Αρχικοποίηση progress
        training_progress[dataset_name] = {
            "status": "starting", 
            "current_epoch": 0, 
            "total_epochs": epochs, 
            "percentage": 0,
            "cancel_requested": False
        }

        # 1. Προετοιμασία του YAML
        yaml_path = self.update_data_yaml(dataset_name)
        
        # Χρησιμοποιούμε ένα Callback της Ultralytics για να ενημερώνουμε το progress
        def on_train_epoch_end(trainer):
            # Έλεγχος αν ζητήθηκε ακύρωση
            if training_progress[dataset_name].get("cancel_requested", False):
                print(f"\n🛑 Ακύρωση εκπαίδευσης για το {dataset_name}...")
                training_progress[dataset_name]["status"] = "cancelled"
                raise KeyboardInterrupt("Training cancelled by user")
            
            curr = trainer.epoch + 1
            percent = int((curr / epochs) * 100)
            training_progress[dataset_name].update({
                "status": "training",
                "current_epoch": curr,
                "total_epochs": epochs,
                "percentage": percent
            })

        # 2. Φόρτωση του μοντέλου (yolo11s όπως στο notebook σου)
        model = YOLO('yolo11s.pt')
        model.add_callback("on_train_epoch_end", on_train_epoch_end)

        print(f"\n--- Ξεκινά η εκπαίδευση για το dataset: {dataset_name} ---")
        results_dir = settings.TRAINING_RESULTS_DIR 
        model_dir = os.path.join(results_dir, f"train_{dataset_name}")
        
        # Βεβαιώσου ότι ο κεντρικός φάκελος υπάρχει
        os.makedirs(results_dir, exist_ok=True)
        
        # Έλεγχος αν υπάρχει ήδη trained model με το ίδιο όνομα και διαγραφή του
        if os.path.exists(model_dir):
            print(f"⚠️  Υπάρχει ήδη model '{dataset_name}' - Διαγράφεται για αντικατάσταση...")
            shutil.rmtree(model_dir)

        # 3. Εκτέλεση Training με τις παραμέτρους σου
        try:
            # ΑΝΙΧΝΕΥΣΗ GPU: 0 αν υπάρχει CUDA (GPU), αλλιώς 'cpu'
            # Αυτό διασφαλίζει ότι η GPU θα "ξυπνήσει" μόνο τώρα
            current_device = 0 if torch.cuda.is_available() else 'cpu'
            
            print(f" usando hardware: {'GPU (CUDA)' if current_device == 0 else 'CPU'}")
            results = model.train(
                data=yaml_path,
                epochs=epochs,
                batch=8,
                project=results_dir,
                imgsz=320,
                name=f"train_{dataset_name}",
                exist_ok=True,  # Επιτρέπει overwrite αν υπάρχει ήδη
                patience=20,
                device=current_device
            )
            training_progress[dataset_name]["status"] = "completed"
            training_progress[dataset_name]["percentage"] = 100
            print(f"\n✅ Η εκπαίδευση για το {dataset_name} ολοκληρώθηκε!")
            return results
        except KeyboardInterrupt:
            print(f"\n⚠️ Η εκπαίδευση για το {dataset_name} ακυρώθηκε από τον χρήστη.")
            training_progress[dataset_name]["status"] = "cancelled"
            return None

        finally:
            # ΠΟΛΥ ΣΗΜΑΝΤΙΚΟ: Απελευθέρωση της μνήμης της GPU μετά το τέλος
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            print("🔄 Συγχρονισμός αποτελεσμάτων εκπαίδευσης με το Google Drive...")
            sync_data_to_drive()
