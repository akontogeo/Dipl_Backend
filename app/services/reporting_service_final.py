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

        # D. Fixation Reports
        timeline_path = self._generate_fixation_timeline(df, target_col, session_dir, session_name)
        mean_fix_path = self._generate_mean_fixation_report(df, target_col, session_dir, session_name)

        #Ε. Dwell Bar Chart (Συνολικός χρόνος ανά αντικείμενο)
        dwell_bar_path = self._generate_dwell_bar(df, target_col, session_dir, session_name)

        # F. Pupil Time Series 
        pupil_time_path = self._generate_pupil_time_series(df, session_dir, session_name)

        
        return {
            "status": "success",
            "social_gaze_index": f"{social_index:.1f}%",
            "files": {
                "pie_chart": pie_path,
                "ttff_chart": ttff_path,
                "pupil_chart": pupil_path,
                "timeline_chart": timeline_path,
                "dwell_bar_chart": dwell_bar_path,
                "pupil_time_chart": pupil_time_path,
                "mean_fixation": mean_fix_path
                
            }
        }

    def _generate_dwell_pie(self, df, target_col, session_dir, session_name):
        # 1. Δυναμική Κατηγοριοποίηση με Search Logic
        def categorize_labels(label):
            l = str(label).lower()
            # Λογική αναζήτησης μέσα στο string (πιο ευέλικτο)
            if any(word in l for word in ['face', 'prosopo', 'mati', 'mouth']): 
                return 'Social'
            elif any(word in l for word in ['hand', 'xeri', 'arm']): 
                return 'Hand'
            elif any(word in l for word in ['background', 'environment', 'wall']): 
                return 'Background (Non-Social)'
            else: 
                return 'Session Objects (Non-Social)'

        df['Dwell_Label'] = df[target_col].apply(categorize_labels)
        dwell_counts = df['Dwell_Label'].value_counts()
        dwell_times = dwell_counts * 0.02 # 50Hz
        
        # Υπολογισμός Social Gaze Index
        social_val = dwell_times.get('Social', 0)
        total_val = dwell_times.sum()
        social_index = (social_val / total_val * 100) if total_val > 0 else 0

        # 2. Σχεδίαση με την παλέτα "deep" (ίδια με το Timeline)
        plt.figure(figsize=(10, 8))
        
        # Παίρνουμε ακριβώς τα χρώματα που χρησιμοποιεί το Seaborn στο Timeline
        palette_colors = sns.color_palette("deep", len(dwell_times))

        plt.pie(
            dwell_times, 
            labels=dwell_times.index, 
            autopct='%1.1f%%', 
            colors=palette_colors, 
            startangle=140, 
            wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
        )
        
        plt.title(f"Dwell Time Analysis: {session_name}\nSocial Preference Index: {social_index:.1f}%", 
                  fontsize=14, pad=20, fontweight='bold')
        
        path = os.path.join(session_dir, "report_pie.png")
        # 300 DPI για να φαίνεται τέλειο στην εκτύπωση της διπλωματικής
        plt.savefig(path, dpi=300, bbox_inches='tight')
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
        ax = sns.barplot(x=ttff_data.values, y=ttff_data.index, palette="deep", hue=ttff_data.index, legend=False)
        
        for i, v in enumerate(ttff_data.values):
            ax.text(v + 0.05, i, f"{v:.2f}s", va='center', fontweight='bold')
            
        plt.title(f"TTFF (Min 100ms Fixation): {session_name}")
        plt.xlabel("Time to First Fixation (seconds)")
        plt.xlim(0, ttff_data.max() * 1.2)
        
        path = os.path.join(session_dir, "report_ttff_scientific.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return path

    
    def _generate_dwell_bar(self, df, target_col, session_dir, session_name):
        # 1. Υπολογισμός Dwell Time (ίδια λογική με το Pie Chart)
        # Μετράμε πόσες φορές εμφανίζεται κάθε label (συμπεριλαμβανομένου του Background)
        # και πολλαπλασιάζουμε με 0.02 (για 50Hz frequency)
        dwell_data = df[target_col].value_counts() * 0.02
        
        # Ταξινόμηση για να φαίνονται πρώτα τα αντικείμενα με τον περισσότερο χρόνο
        dwell_data = dwell_data.sort_values(ascending=False)

        # 2. Σχεδίαση Bar Chart
        plt.figure(figsize=(12, 7))
        
        # Χρήση της παλέτας "deep" για απόλυτη ομοιομορφία με το Timeline
        ax = sns.barplot(
            x=dwell_data.values, 
            y=dwell_data.index, 
            palette="deep", 
            hue=dwell_data.index, 
            legend=False
        )

        # 3. Προσθήκη των τιμών δευτερολέπτων στις μπάρες
        for i, v in enumerate(dwell_data.values):
            ax.text(v + 0.05, i, f"{v:.2f}s", va='center', fontweight='bold', fontsize=10)

        plt.title(f"Total Dwell Time: {session_name}", fontsize=14, pad=15, fontweight='bold')
        plt.xlabel("Duration (seconds)", fontsize=12)
        plt.ylabel("All Recorded Labels", fontsize=12)
        
        # Προσθήκη ορίου στον άξονα για να μην "κολλάνε" τα νούμερα στο τέλος
        plt.xlim(0, dwell_data.max() * 1.2)
        plt.grid(axis='x', linestyle='--', alpha=0.5)

        # Αποθήκευση σε υψηλή ανάλυση (300 DPI)
        path = os.path.join(session_dir, "report_dwell_bar.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return path
    def _generate_pupil_report(self, df, target_col, session_dir, session_name):
        # 1. Φιλτράρουμε τα 0 και τα outliers (όπως είπαμε, το "τίμιο" καθάρισμα)
        df_pupil = df[(df['pupil_diameter'] > 1.5) & (df['pupil_diameter'] < 8.0)].copy()
        
        if df_pupil.empty: return None

        # 2. Υπολογισμός του Γενικού Μέσου Όρου (Η "Ευθεία" μας)
        overall_mean = df_pupil['pupil_diameter'].mean()

        # 3. Μέσος όρος ανά αντικείμενο
        avg_pupil = df_pupil.groupby(target_col)['pupil_diameter'].mean().sort_values(ascending=False)

        # 4. Σχεδίαση
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=avg_pupil.values, y=avg_pupil.index, palette='deep')

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
        
    def _generate_pupil_time_series(self, df, session_dir, session_name):
        # 1. Καθαρισμός δεδομένων (όπως και στο άλλο pupil report)
        df_pupil = df[(df['pupil_diameter'] > 1.5) & (df['pupil_diameter'] < 8.0)].copy()
        
        if df_pupil.empty: return None

        # 2. Υπολογισμός Κινητού Μέσου Όρου (Smoothing)
        # Χρησιμοποιούμε παράθυρο 25 δειγμάτων (0.5 δευτερόλεπτο στα 50Hz)
        df_pupil['pupil_smooth'] = df_pupil['pupil_diameter'].rolling(window=25, center=True).mean()

        # 3. Σχεδίαση
        plt.figure(figsize=(14, 6))
        
        # Σχεδιάζουμε το αρχικό σήμα με χαμηλό opacity και το smooth σήμα από πάνω
        plt.plot(df_pupil['timestamp'], df_pupil['pupil_diameter'], 
                 alpha=0.2, color='#34495e', label='Raw Data')
        plt.plot(df_pupil['timestamp'], df_pupil['pupil_smooth'], 
                 color='#e74c3c', linewidth=2, label='Moving Average (0.5s)')

        # Προσθήκη Baseline (Μέσος όρος session)
        overall_mean = df_pupil['pupil_diameter'].mean()
        plt.axhline(overall_mean, color='black', linestyle='--', alpha=0.6, 
                    label=f'Session Mean ({overall_mean:.2f}mm)')

        plt.title(f"Pupil Diameter Over Time: {session_name}", fontsize=14, pad=15, fontweight='bold')
        plt.xlabel("Time (seconds)", fontsize=12)
        plt.ylabel("Pupil Diameter (mm)", fontsize=12)
        plt.legend(loc='upper right')
        plt.grid(True, linestyle=':', alpha=0.5)

        path = os.path.join(session_dir, "report_pupil_timeline.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return path
    def _generate_mean_fixation_report(self, df, target_col, session_dir, session_name):
        # 1. Φιλτράρισμα Background
        df_obj = df[df[target_col] != 'Background'].copy()
        if df_obj.empty: return None

        all_fixations = []
        
        # 2. Εξαγωγή Fixations (όπως στο timeline)
        for label in df_obj[target_col].unique():
            label_mask = (df_obj[target_col] == label).astype(int)
            blocks = (label_mask != label_mask.shift()).cumsum()
            
            group = df_obj[label_mask == 1].groupby(blocks)
            for _, g in group:
                duration = len(g) * 0.02
                if duration >= 0.1: # Threshold 100ms για να θεωρηθεί fixation
                    all_fixations.append({
                        'label': label,
                        'duration': duration
                    })

        if not all_fixations: return None
        fix_df = pd.DataFrame(all_fixations)

        # 3. Υπολογισμός Μέσου Όρου ανά Label
        mean_fix = fix_df.groupby('label')['duration'].mean().sort_values(ascending=False)

        # 4. Σχεδίαση
        plt.figure(figsize=(12, 6))
        ax = sns.barplot(
            x=mean_fix.values, 
            y=mean_fix.index, 
            palette="deep", 
            hue=mean_fix.index, 
            legend=False
        )

        # Προσθήκη τιμών στις μπάρες
        for i, v in enumerate(mean_fix.values):
            ax.text(v + 0.01, i, f"{v:.3f}s", va='center', fontweight='bold')

        plt.title(f"Mean Fixation Duration per Object: {session_name}\n(Threshold > 100ms)", fontsize=14, pad=15)
        plt.xlabel("Average Duration (seconds)", fontsize=12)
        plt.ylabel("Objects", fontsize=12)
        
        plt.xlim(0, mean_fix.max() * 1.2)
        plt.grid(axis='x', linestyle='--', alpha=0.6)

        path = os.path.join(session_dir, "report_mean_fixation.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return path
        
    def _generate_fixation_timeline(self, df, target_col, session_dir, session_name):
        df_obj = df[df[target_col] != 'Background'].copy()
        if df_obj.empty: return None

        all_fixations = []
        
        for label in df_obj[target_col].unique():
            label_mask = (df_obj[target_col] == label).astype(int)
            blocks = (label_mask != label_mask.shift()).cumsum()
            
            # Υπολογίζουμε διάρκεια ΚΑΙ το timestamp έναρξης
            group = df_obj[label_mask == 1].groupby(blocks)
            for _, g in group:
                duration = len(g) * 0.02
                if duration >= 0.1: # Threshold 100ms
                    all_fixations.append({
                        'label': label,
                        'duration': duration,
                        'start_time': g['timestamp'].iloc[0]
                    })

        fix_df = pd.DataFrame(all_fixations)
        
        # Σχεδίαση Scatter Plot
        plt.figure(figsize=(14, 6))
        sns.scatterplot(data=fix_df, x='start_time', y='duration', hue='label', s=100, alpha=0.7)
        
        plt.title(f"Fixation Duration Evolution: {session_name}")
        plt.xlabel("Session Time (seconds)")
        plt.ylabel("Fixation Duration (seconds)")
        plt.grid(True, linestyle='--', alpha=0.6)
        
        path = os.path.join(session_dir, "report_fixation_timeline.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return path
