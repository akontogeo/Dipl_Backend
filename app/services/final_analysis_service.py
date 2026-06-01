import cv2
import pandas as pd
import numpy as np
import os
import gc
from collections import Counter
from app.services.utils import sync_data_to_drive 
from app.core.config import settings
from app.services.reporting_service_final import ReportingService

# Tracker για το UI
analysis_progress = {}

class FinalAnalysisService:
    def run_master_analysis(self, analysis_id: str, session_name: str, video_path: str, gaze_csv: str, yolo_csv: str, output_video: str, output_excel: str):
        try:
            analysis_progress[analysis_id] = {"status": "starting", "percentage": 0}
            
            # --- ΡΥΘΜΙΣΕΙΣ ---
            PADDING = 15
            WINDOW_RADIUS = 2

            # --- ΦΟΡΤΩΣΗ ---
            df_gaze = pd.read_csv(gaze_csv)
            df_yolo = pd.read_csv(yolo_csv)
            
            # Υπολογισμός εμβαδού
            df_yolo['area'] = (df_yolo['x_max'] - df_yolo['x_min']) * (df_yolo['y_max'] - df_yolo['y_min'])

            # --- VIDEO SETUP ---
            cap = cv2.VideoCapture(video_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

            # --- ΣΩΣΤΟ INDEXING & ΜΕΤΑΤΡΟΠΗ ΣΕ DICTIONARIES (ΓΙΑ ΤΑΧΥΤΗΤΑ) ---
            # Αν το gaze δεν έχει έτοιμο frame_index, το υπολογίζουμε προσεκτικά
            if 'frame_index' not in df_gaze.columns:
                df_gaze['frame_index'] = np.round(df_gaze['timestamp'] * fps).astype(int)
            
            # Το YOLO έχει ήδη έτοιμο frame_index από το tracking, μην το ξαναχαλάς!
            if 'frame_index' not in df_yolo.columns:
                df_yolo['frame_index'] = np.round(df_yolo['timestamp'] * fps).astype(int)

            # Μετατροπή σε dict groups για αστραπιαίο lookup στο loop
            gaze_dict = {k: v for k, v in df_gaze.groupby('frame_index')}
            yolo_dict = {k: v for k, v in df_yolo.groupby('frame_index')}
            
            df_gaze['looking_at'] = "Background"

            print(f"🎬 Ξεκινάει η επεξεργασία για {total_frames} frames...")

            # --- PROCESSING LOOP ---
            for frame_idx in range(total_frames):
                ret, frame = cap.read()
                if not ret: 
                    break

                found_obj_name = "Background"
                found_obj_box = None
                has_gaze = False
                gx, gy = 0, 0

                # Lookup στο dictionary (τάχιστο)
                if frame_idx in gaze_dict:
                    gaze_points = gaze_dict[frame_idx]
                    gx = int(gaze_points['pixel_x'].mean())
                    gy = int(gaze_points['pixel_y'].mean())
                    has_gaze = True

                    if frame_idx in yolo_dict:
                        # Ταξινομούμε τα αντικείμενα από το μικρότερο στο μεγαλύτερο (για overlapping)
                        objs = yolo_dict[frame_idx].sort_values('area', ascending=True)

                        for _, obj in objs.iterrows():
                            # Εφαρμογή Padding 15px
                            if (obj['x_min'] - PADDING) <= gx <= (obj['x_max'] + PADDING) and \
                               (obj['y_min'] - PADDING) <= gy <= (obj['y_max'] + PADDING):
                                found_obj_name = obj['object_name']
                                found_obj_box = obj
                                # Ενημέρωση στο αρχικό DataFrame χρησιμοποιώντας τα index των συγκεκριμένων rows
                                df_gaze.loc[gaze_points.index, 'looking_at'] = found_obj_name
                                break

                # --- ΖΩΓΡΑΦΙΚΗ (Visualization) ---
                # Αχνά κουτιά (Background objects)
                if frame_idx in yolo_dict:
                    for _, obj in yolo_dict[frame_idx].iterrows():
                        cv2.rectangle(frame, (int(obj['x_min']), int(obj['y_min'])), (int(obj['x_max']), int(obj['y_max'])), (200, 200, 200), 1)

                # Έντονο HIT κουτί
                if found_obj_box is not None:
                    cv2.rectangle(frame, (int(found_obj_box['x_min']), int(found_obj_box['y_min'])), (int(found_obj_box['x_max']), int(found_obj_box['y_max'])), (0, 0, 255), 2)
                    cv2.putText(frame, f"HIT: {found_obj_name}", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                # Κύκλος ματιού
                if has_gaze:
                    color = (0, 0, 255) if found_obj_name != "Background" else (255, 0, 0)
                    cv2.circle(frame, (gx, gy), 8, color, -1)

                out.write(frame)
                
                # Update progress κάθε 50 frames (ΕΞΩ από τα ifs για να δουλεύει ΠΑΝΤΑ)
                if frame_idx % 50 == 0 or frame_idx == total_frames - 1:
                    pct = int((frame_idx / total_frames) * 100)
                    analysis_progress[analysis_id] = {"status": "processing", "percentage":int(pct)}
                    # Προαιρετικό print για να βλέπεις τι γίνεται στα logs του Colab
                    print(f"⏳ Progress: {int(pct)}% (Frame {frame_idx}/{total_frames})")

            cap.release()
            out.release()
            
            # Απελευθέρωση μνήμης των dicts
            del gaze_dict
            del yolo_dict
            gc.collect()
            
            # --- ΕΞΤΡΑ ΒΗΜΑ: TEMPORAL SMOOTHING ---
            analysis_progress[analysis_id]["message"] = "Εφαρμογή Smoothing στα αποτελέσματα..."
            
            raw_labels = df_gaze['looking_at'].tolist()
            smoothed_labels = []

            for i in range(len(raw_labels)):
                start = max(0, i - WINDOW_RADIUS)
                end = min(len(raw_labels), i + WINDOW_RADIUS + 1)
                window = raw_labels[start:end]
                most_common = Counter(window).most_common(1)[0][0]
                smoothed_labels.append(most_common)

            df_gaze['looking_at_original'] = raw_labels 
            df_gaze['looking_at'] = smoothed_labels      

            # Εξαγωγή Excel
            df_gaze.to_excel(output_excel, index=False)
            
            # Αναφορές
            reporting = ReportingService()
            reporting.generate_session_report(session_name)

            relative_video_path = f"outputs/{output_video.split('outputs/')[-1]}"
            relative_excel_path = f"outputs/{output_excel.split('outputs/')[-1]}"
            
            analysis_progress[analysis_id] = {
                "status": "completed", 
                "percentage": 100, 
                "video_file": relative_video_path,  
                "excel_file": relative_excel_path,
                "pie_chart": f"outputs/sessions/{session_name}/report_pie.png",
                "ttff_chart": f"outputs/sessions/{session_name}/report_ttff_scientific.png",
                "pupil_chart": f"outputs/sessions/{session_name}/report_pupil.png",
                "timeline_chart": f"outputs/sessions/{session_name}/report_fixation_timeline.png",
                "dwell_bar_chart": f"outputs/sessions/{session_name}/report_dwell_bar.png", 
                "pupil_time_chart": f"outputs/sessions/{session_name}/report_pupil_timeline.png",
                "mean_fixation": f"outputs/sessions/{session_name}/report_mean_fixation.png"
            }
            
            print("🔄 Συγχρονισμός τελικών αποτελεσμάτων με το Drive...")
            sync_data_to_drive()

        except Exception as e:
            analysis_progress[analysis_id] = {"status": "error", "message": str(e)}
            print(f"❌ ERROR: {str(e)}")
        
        return output_video
