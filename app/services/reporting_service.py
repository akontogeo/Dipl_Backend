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
        # Υποθέτουμε 50Hz (0.02s ανά δείγμα) - προσάρμοσε το αν το FPS είναι διαφορετικό
        duration = df[target_col].value_counts() * 0.02
        df_obj = df[df[target_col] != 'Background'].copy()
        sns.set_style("whitegrid")
        plt.rcParams['figure.facecolor'] = 'white'
        
        changes = df[target_col] != df[target_col].shift()
        groups = changes.cumsum()
        temp = df.copy()
        temp['segment_id'] = groups
        visits = temp.groupby(target_col)['segment_id'].nunique()
        avg_fixation = duration / visits

        metrics = pd.DataFrame({
            'Total Duration (sec)': duration,
            'Visit Count': visits,
            'Avg Fixation (sec)': avg_fixation
        }).sort_values('Total Duration (sec)', ascending=False).round(3)

        # Αποθήκευση CSV Μετρικών
        metrics_csv_path = os.path.join(session_dir, f"metrics_{session_name}.csv")
        metrics.to_csv(metrics_csv_path)

        # 4. Παραγωγή Γραφημάτων
        plt.rcParams['figure.facecolor'] = 'white'
        
        # --- PIE CHART ---
        def categorize(label):
            label_str = str(label).lower()
            if 'background' in label_str: return 'Background'
            elif 'face' in label_str or 'prosopo' in label_str: return 'Therapist Face'
            elif 'xeri' in label_str or 'hand' in label_str: return 'Therapist Hand'
            else: return 'Puzzle Game'

        df['Category'] = df[target_col].apply(categorize)
        pie_data = df['Category'].value_counts()
        
        colors_map = {
            'Puzzle Game': '#a8d8ea', 'Therapist Hand': '#f5b7b1',
            'Background': '#e0e0e0', 'Therapist Face': '#fdebd0'
        }
        pie_colors = [colors_map.get(k, '#cccccc') for k in pie_data.index]

        plt.figure(figsize=(8, 8))
        plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=140,
                colors=pie_colors, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        plt.title(f'Attention Distribution: {session_name}')
        
        pie_path = os.path.join(session_dir, "report_pie.png")
        plt.savefig(pie_path, dpi=150, bbox_inches='tight')
        plt.close()

        # --- BAR CHART (Duration) ---
        sns.set_style("whitegrid")
        plt.figure(figsize=(10, 6))
        sns.barplot(x=metrics['Total Duration (sec)'], y=metrics.index, palette='pastel')
        plt.title('Total Duration per Object (sec)')
        
        bar_path = os.path.join(session_dir, "report_duration.png")
        plt.savefig(bar_path, dpi=150, bbox_inches='tight')
        plt.close()

        # 3. [ΝΕΟ] TTFF (Time to First Fixation)
        if not df_obj.empty:
            ttff = df_obj.groupby(target_col)['timestamp'].min().sort_values()
            plt.figure(figsize=(10, 6))
            sns.barplot(x=ttff.values, y=ttff.index, palette='coolwarm')
            plt.title('Time to First Fixation (TTFF) - Ποιο είδε πρώτο;')
            plt.xlabel('Seconds')
            plt.savefig(os.path.join(session_dir, "report_ttff.png"), dpi=150)
            plt.close()

        # 4. [ΝΕΟ] Pupil Diameter (Cognitive Load)
        if 'pupil_diameter' in df.columns:
            df_pupil = df_obj[df_obj['pupil_diameter'] > 1.5].copy()
            if not df_pupil.empty:
                avg_pupil = df_pupil.groupby(target_col)['pupil_diameter'].mean().sort_values(ascending=False)
                plt.figure(figsize=(10, 6))
                sns.barplot(x=avg_pupil.values, y=avg_pupil.index, palette='magma')
                plt.title('Average Pupil Diameter (Cognitive Load)')
                plt.xlabel('Diameter (mm)')
                # Zoom για να φαίνονται οι διαφορές
                plt.xlim(max(0, avg_pupil.min() - 0.2), avg_pupil.max() + 0.1)
                plt.savefig(os.path.join(session_dir, "report_pupil.png"), dpi=150)
                plt.close()

        return {
            "status": "success",
            "files": {
                "metrics": metrics_csv_path,
                "pie_chart": pie_path,
                "bar_chart": bar_path
            }
        }
