import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from app.core.config import settings

class ReportingService:
    def generate_session_report(self, session_name: str):
        # 1. Καθορισμός Paths
        session_dir = os.path.join(settings.OUTPUTS_DIR, "sessions", session_name)
        excel_path = os.path.join(session_dir, f"results_{session_name}.xlsx")
        
        if not os.path.exists(excel_path):
            excel_path = excel_path.replace('.xlsx', '.csv')
            if not os.path.exists(excel_path):
                return {"status": "error", "message": "Δεν βρέθηκε αρχείο."}

        # 2. Φόρτωση Δεδομένων
        df = pd.read_excel(excel_path) if excel_path.endswith('.xlsx') else pd.read_csv(excel_path)
        target_col = 'looking_at' if 'looking_at' in df.columns else df.columns[-1]

        # --- ΕΚΤΕΛΕΣΗ ΟΛΩΝ ΤΩΝ REPORTS ---
        
        # A. Dwell Time & Pie Chart (Social Gaze Index)
        pie_path, social_index = self._generate_dwell_pie(df, target_col, session_dir, session_name)
        
        # B. TTFF Report (Δυναμικό για όλα τα labels)
        ttff_path = self._generate_ttff_report(df, target_col, session_dir, session_name)
        
        # C. Pupil Report (Cognitive Load)
        pupil_path = self._generate_pupil_report(df, target_col, session_dir, session_name)

        return {
            "status": "success",
            "social_gaze_index": f"{social_index:.1f}%",
            "files": {
                "pie_chart": pie_path,
                "ttff_chart": ttff_path,
                "pupil_chart": pupil_path
            }
        }

    def _generate_dwell_pie(self, df, target_col, session_dir, session_name):
        def categorize_labels(label):
            l = str(label).lower()
            if 'face' in l or 'prosopo' in l: return 'Face (Social)'
            elif 'hand' in l or 'xeri' in l: return 'Hand (Social)'
            elif 'background' in l: return 'Background (Non-Social)'
            else: return 'Puzzle (Non-Social)'

        df['Dwell_Label'] = df[target_col].apply(categorize_labels)
        dwell_times = df['Dwell_Label'].value_counts() * 0.02 # 50Hz
        
        social_val = dwell_times.get('Face (Social)', 0) + dwell_times.get('Hand (Social)', 0)
        social_index = (social_val / dwell_times.sum() * 100) if dwell_times.sum() > 0 else 0

        plt.figure(figsize=(10, 8))
        colors = {'Face (Social)': '#ff9999', 'Hand (Social)': '#ffc0cb', 'Puzzle (Non-Social)': '#66b3ff', 'Background (Non-Social)': '#d3d3d3'}
        plt.pie(dwell_times, labels=dwell_times.index, autopct='%1.1f%%', colors=[colors.get(x, '#eee') for x in dwell_times.index], startangle=140, wedgeprops={'edgecolor': 'black'})
        plt.title(f"Dwell Time: {session_name}\nSocial Gaze Index: {social_index:.1f}%")
        
        path = os.path.join(session_dir, "report_pie.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return path, social_index

    def _generate_ttff_report(self, df, target_col, session_dir, session_name):
        df_obj = df[df[target_col] != 'Background'].copy()
        if df_obj.empty: return None
        
        ttff_results = {}
        labels = df_obj[target_col].unique()
        
        for label in labels:
            # 1. Δημιουργούμε μια σειρά από True/False (1/0) αν κοιτάζει το label
            label_mask = (df_obj[target_col] == label).astype(int)
            
            # 2. Rolling sum για να βρούμε 5 συνεχή δείγματα (100ms threshold)
            # Σύμφωνα με Coel et al. (2024) / Holmqvist (2011)
            consecutive_looks = label_mask.rolling(window=5).sum()
            
            # 3. Βρίσκουμε το πρώτο index που το άθροισμα είναι 5
            first_fix_idx = consecutive_looks[consecutive_looks == 5].index
            
            if not first_fix_idx.empty:
                # Το TTFF είναι το timestamp του ΠΡΩΤΟΥ δείγματος αυτού του σερί
                actual_start_idx = first_fix_idx[0] - 4
                ttff_results[label] = df_obj.loc[actual_start_idx, 'timestamp']

        if not ttff_results: return None

        # Μετατροπή σε Series και ταξινόμηση
        ttff_data = pd.Series(ttff_results).sort_values()
        
        # Σχεδίαση Bar Chart (όπως πριν)
        plt.figure(figsize=(12, 6))
        ax = sns.barplot(x=ttff_data.values, y=ttff_data.index, palette="viridis", hue=ttff_data.index, legend=False)
        
        for i, v in enumerate(ttff_data.values):
            ax.text(v + 0.05, i, f"{v:.2f}s", va='center', fontweight='bold')
            
        plt.title(f"TTFF (Min 100ms Fixation): {session_name}")
        plt.xlabel("Time to First Fixation (seconds)")
        plt.xlim(0, ttff_data.max() * 1.2)
        
        path = os.path.join(session_dir, "report_ttff_scientific.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return path

    def generate_pupil_report(self, df, target_col, session_dir, session_name):
        # 1. Φιλτράρουμε τα 0 και τα outliers (όπως είπαμε, το "τίμιο" καθάρισμα)
        df_pupil = df[(df['pupil_diameter'] > 1.5) & (df['pupil_diameter'] < 8.0)].copy()
        
        if df_pupil.empty: return None

        # 2. Υπολογισμός του Γενικού Μέσου Όρου (Η "Ευθεία" μας)
        overall_mean = df_pupil['pupil_diameter'].mean()

        # 3. Μέσος όρος ανά αντικείμενο
        avg_pupil = df_pupil.groupby(target_col)['pupil_diameter'].mean().sort_values(ascending=False)

        # 4. Σχεδίαση
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=avg_pupil.values, y=avg_pupil.index, palette='magma')

        # ΠΡΟΣΘΗΚΗ ΤΗΣ ΕΥΘΕΙΑΣ (Baseline)
        plt.axvline(overall_mean, color='red', linestyle='--', label=f'Session Mean: {overall_mean:.2f}mm')
        
        plt.title(f'Pupil Diameter per Object vs Session Baseline\n(Red Line = Average Engagement)')
        plt.xlabel('Diameter (mm)')
        plt.legend() # Για να φαίνεται τι είναι η κόκκινη γραμμή
        
        # Zoom για να φαίνονται οι διαφορές
        plt.xlim(overall_mean - 0.5, overall_mean + 0.5)
        
        path = os.path.join(session_dir, "report_pupil.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return path
