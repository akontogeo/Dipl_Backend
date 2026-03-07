import zipfile
import os
import shutil
from app.core.config import settings
import glob
import random
from app.services.augment_service import AugmentService

class DatasetService:
    def __init__(self):
        self.dataset_path = settings.DATASETS_DIR
        self.augment_service = AugmentService()
    def process_zip_dataset(self, zip_path: str, folder_name: str):
        """
        Αποσυμπιέζει το zip σε έναν συγκεκριμένο υποφάκελο μέσα στο datasets/
        """
        # Ορίζουμε τη διαδρομή: datasets/όνομα_φακέλου
        target_path = os.path.join(self.dataset_path, folder_name)

        # Αν ο φάκελος υπάρχει ήδη, τον καθαρίζουμε
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        os.makedirs(target_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_path)
        
        # 2. Διαχωρισμός 90/10 (Train/Valid)
        self.rebalance_dataset(target_path)
        # 3. Augmentation (μόνο στις εικόνες του Train)
        self.augment_service.augment_dataset(target_path, multiplier=3)
        
        return target_path

    def _get_image_list(self, folder):
        # Υποστηρίζουμε jpg, jpeg, png
        return glob.glob(os.path.join(folder, "images", "*.[jJ][pP]*[gG]")) + \
               glob.glob(os.path.join(folder, "images", "*.png"))

    def rebalance_dataset(self, dataset_path):
        train_path = os.path.join(dataset_path, "train")
        valid_path = os.path.join(dataset_path, "valid")

        # Δημιουργία φακέλων αν λείπουν (π.χ. αν το zip είχε μόνο train)
        for p in [train_path, valid_path]:
            os.makedirs(os.path.join(p, "images"), exist_ok=True)
            os.makedirs(os.path.join(p, "labels"), exist_ok=True)

        train_imgs = self._get_image_list(train_path)
        valid_imgs = self._get_image_list(valid_path)
        
        total = len(train_imgs) + len(valid_imgs)
        if total == 0: return
        
        valid_ratio = len(valid_imgs) / total

        # Αν το valid είναι εκτός ορίων (π.χ. κάτω από 8% ή πάνω από 12%)
        if valid_ratio < 0.12 or valid_ratio > 0.17:
            target_valid_count = int(total * 0.15)  # Στοχεύουμε στο 15%
            all_imgs = train_imgs + valid_imgs
            random.shuffle(all_imgs)
            
            # Νέος διαχωρισμός
            new_valid_imgs = all_imgs[:target_valid_count]
            new_train_imgs = all_imgs[target_valid_count:]

            self._move_files(new_valid_imgs, valid_path)
            self._move_files(new_train_imgs, train_path)
            return f"Rebalanced: Train={len(new_train_imgs)}, Valid={len(new_valid_imgs)}"
        
        return "Dataset ratio is fine."

    def _move_files(self, img_list, target_folder):
        for img_path in img_list:
            # Μετακίνηση εικόνας
            img_name = os.path.basename(img_path)
            shutil.move(img_path, os.path.join(target_folder, "images", img_name))
            
            # Μετακίνηση αντίστοιχου label (.txt)
            label_name = os.path.splitext(img_name)[0] + ".txt"
            label_src = os.path.join(os.path.dirname(os.path.dirname(img_path)), "labels", label_name)
            if os.path.exists(label_src):
                shutil.move(label_src, os.path.join(target_folder, "labels", label_name))