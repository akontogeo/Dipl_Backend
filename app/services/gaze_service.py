import json
import pandas as pd
import os

class GazeService:
    def process_gaze_file(self, input_path: str, output_path: str):
        # Οι ρυθμίσεις σου
        VIDEO_WIDTH = 1920
        VIDEO_HEIGHT = 1080
        gaze_entries = []

        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('type') == 'gaze':
                        data = entry.get('data', {})
                        gaze2d = data.get('gaze2d')

                        if gaze2d:
                            # Μετατροπή σε Pixels (όπως στον κώδικά σου)
                            pixel_x = int(gaze2d[0] * VIDEO_WIDTH)
                            pixel_y = int(gaze2d[1] * VIDEO_HEIGHT)

                            # Κόρη
                            left = data.get('eyeleft', {}).get('pupildiameter')
                            right = data.get('eyeright', {}).get('pupildiameter')
                            avg_pupil = (left + right) / 2 if (left and right) else 0

                            gaze_entries.append({
                                'timestamp': entry.get('timestamp'),
                                'pixel_x': pixel_x,
                                'pixel_y': pixel_y,
                                'pupil_diameter': round(avg_pupil, 3)
                            })
                except:
                    continue

        df = pd.DataFrame(gaze_entries)
        df.to_csv(output_path, index=False)
        return len(df)