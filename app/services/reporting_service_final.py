import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from collections import Counter
from app.core.config import settings

class ReportingService:
    def generate_session_report(self, session_name: str):
        # 1. Καθορισμός Paths
        session_dir = os.path.join(settings.OUTPUTS_DIR, "sessions", session_name)
        # Ψάχνουμε το αρχείο results_SESSIONNAME.xlsx
        excel_path = os.path.join(session_dir, f"results_{session_name}.xlsx")
        
        if not os.path.exists(excel_path):
            # Δοκιμή για .csv αν δεν υπάρχει .xlsx
            excel_path = excel_path.replace('.xlsx', '.csv')
            if not os.path.exists(excel_path):
                return {"status": "error", "message": f"Δεν βρέθηκε αρχείο αποτελεσμάτων στο {session_dir}"}

        # 2. Φόρτωση Δεδομένων
        if excel_path.endswith('.xlsx'):
            df = pd.read_excel(excel_path)
        else:
            df = pd.read_csv(excel_path)

        # Επιλογή στήλης
        target_col = 'looking_at' if 'looking_at' in df.columns else df.columns[-1]

        # 3. Υπολογισμός Μετρικών
       # --- ROI Categorization με τα 4 συγκεκριμένα ονόματα ---

        def categorize_labels(label):
            l = str(label).lower()
            if 'face' in l or 'prosopo' in l:
                return 'Face (Social)'
            elif 'hand' in l or 'xeri' in l:
                return 'Hand (Social)'
            elif 'background' in l:
                return 'Background (Non-Social)'
            else:
                # Οτιδήποτε άλλο (π.χ. puzzle, toy) ονομάζεται Puzzle
                return 'Puzzle (Non-Social)'
        
        # Εφαρμογή της κατηγοριοποίησης
        df['Dwell_Label'] = df[target_col].apply(categorize_labels)
        
        # Υπολογισμός Dwell Time σε δευτερόλεπτα (Frames * 0.02)
        dwell_times = df['Dwell_Label'].value_counts() * 0.02
        
        # Υπολογισμός Social Gaze Index (Biomarker)
        # Social = Face + Hand / Non-Social = Puzzle (εξαιρούμε το Background από το Engagement)
        social_val = dwell_times.get('Face (Social)', 0) + dwell_times.get('Hand (Social)', 0)
        puzzle_val = dwell_times.get('Puzzle (Non-Social)', 0)
        
        social_index = (social_val / (social_val + puzzle_val) * 100) if (social_val + puzzle_val) > 0 else 0
        
        # --- Δημιουργία Pie Chart ---
        plt.figure(figsize=(10, 8))
        colors = {
            'Face (Social)': '#ff9999', 
            'Hand (Social)': '#ffc0cb', 
            'Puzzle (Non-Social)': '#66b3ff', 
            'Background (Non-Social)': '#d3d3d3'
        }
        
        plt.pie(dwell_times, labels=dwell_times.index, autopct='%1.1f%%', 
                colors=[colors.get(x, '#white') for x in dwell_times.index],
                startangle=140, wedgeprops={'edgecolor': 'black'})
        
        plt.title(f"Dwell Time Analysis: {session_name}\nSocial Gaze Index: {social_index:.1f}%")

        # # --- BAR CHART (Duration) ---
        # sns.set_style("whitegrid")
        # plt.figure(figsize=(10, 6))
        # sns.barplot(x=metrics['Total Duration (sec)'], y=metrics.index, palette='pastel')
        # plt.title('Total Duration per Object (sec)')
        
        # bar_path = os.path.join(session_dir, "report_duration.png")
        # plt.savefig(bar_path, dpi=150, bbox_inches='tight')
        # plt.close()

        # # 3. [ΝΕΟ] TTFF (Time to First Fixation)
        # if not df_obj.empty:
        #     ttff = df_obj.groupby(target_col)['timestamp'].min().sort_values()
        #     plt.figure(figsize=(10, 6))
        #     sns.barplot(x=ttff.values, y=ttff.index, palette='coolwarm')
        #     plt.title('Time to First Fixation (TTFF) - Ποιο είδε πρώτο;')
        #     plt.xlabel('Seconds')
        #     plt.savefig(os.path.join(session_dir, "report_ttff.png"), dpi=150)
        #     plt.close()

        # # 4. [ΝΕΟ] Pupil Diameter (Cognitive Load)
        # if 'pupil_diameter' in df.columns:
        #     df_pupil = df_obj[df_obj['pupil_diameter'] > 1.5].copy()
        #     if not df_pupil.empty:
        #         avg_pupil = df_pupil.groupby(target_col)['pupil_diameter'].mean().sort_values(ascending=False)
        #         plt.figure(figsize=(10, 6))
        #         sns.barplot(x=avg_pupil.values, y=avg_pupil.index, palette='magma')
        #         plt.title('Average Pupil Diameter (Cognitive Load)')
        #         plt.xlabel('Diameter (mm)')
        #         # Zoom για να φαίνονται οι διαφορές
        #         plt.xlim(max(0, avg_pupil.min() - 0.2), avg_pupil.max() + 0.1)
        #         plt.savefig(os.path.join(session_dir, "report_pupil.png"), dpi=150)
        #         plt.close()

        return {
            "status": "success",
            "files": {
                "metrics": metrics_csv_path,
                "pie_chart": pie_path,
                "bar_chart": bar_path
            }
        }
