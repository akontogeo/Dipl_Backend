import cv2
import csv
import pandas as pd
from ultralytics import YOLO
from app.services.utils import sync_data_to_drive # Εισαγωγή του sync

# Global dictionary για την παρακολούθηση
inference_progress = {}

class InferenceService:
    def run_tracking(self, video_id: str, video_path: str, model_path: str, output_csv: str):
        try:
            inference_progress[video_id] = {"status": "processing", "message": "Το tracking ξεκίνησε..."}
            
            # 1. Άνοιγμα βίντεο για διαστάσεις και FPS
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps == 0: fps = 25
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()

            # 2. Φόρτωση Μοντέλου
            model = YOLO(model_path)

            # 3. Εκτέλεση Tracking (imgsz=1024 για υψηλή ακρίβεια)
            results_generator = model.track(
                source=video_path,
                persist=True,
                tracker="bytetrack.yaml",
                imgsz=1024,
                conf=0.3,
                iou=0.5,
                verbose=False,
                stream=True
            )

            all_data = []

            for i, result in enumerate(results_generator):
                timestamp = i / fps
                if result.boxes and result.boxes.id is not None:
                    boxes = result.boxes.xyxyn.cpu().numpy()
                    track_ids = result.boxes.id.cpu().numpy()
                    cls_ids = result.boxes.cls.cpu().numpy()

                    for box, track_id, cls_id in zip(boxes, track_ids, cls_ids):
                        name = result.names[int(cls_id)]
                        # Μετατροπή σε pixels
                        x1, y1, x2, y2 = int(box[0]*width), int(box[1]*height), int(box[2]*width), int(box[3]*height)
                        
                        # Προσθήκη στη λίστα
                        all_data.append([i, f"{timestamp:.3f}", name, int(track_id), x1, y1, x2, y2])
                if i % 300 == 0:
                    gc.collect()
            # 4. ΚΑΘΑΡΙΣΜΟΣ ΜΕ PANDAS (Το βήμα που ήθελες)
            if all_data:
                df = pd.DataFrame(all_data, columns=['frame_index', 'timestamp', 'object_name', 'track_id', 'x_min', 'y_min', 'x_max', 'y_max'])
                
                # Φίλτρο: Ghost filtering
                id_counts = df['track_id'].value_counts()
                valid_ids = id_counts[id_counts >= 5].index
                df_clean = df[df['track_id'].isin(valid_ids)].copy()

                # 5. Αποθήκευση του Καθαρού CSV
                df_clean.to_csv(output_csv, index=False)
                removed_ghosts = len(id_counts) - len(valid_ids)

            else:
                # Αν δεν βρέθηκε τίποτα απολύτως στο βίντεο
                df = pd.DataFrame(columns=['frame_index', 'timestamp', 'object_name', 'track_id', 'x_min', 'y_min', 'x_max', 'y_max'])
                df.to_csv(output_csv, index=False)
                removed_ghosts = 0
                
            print(f"🔄 Ανεβάζω το αποτέλεσμα του tracking στο Drive...")
            sync_data_to_drive()
               
            inference_progress[video_id] = {
                "status": "completed", 
                "message": f"Ολοκληρώθηκε! Διαγράφηκαν {len(id_counts) - len(valid_ids)} ghost detections.",
                "file": output_csv
            }

        except Exception as e:
            inference_progress[video_id] = {"status": "error", "message": str(e)}
        
        return output_csv
