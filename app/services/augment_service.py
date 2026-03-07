# augment_service.py
# Service for data augmentation
import albumentations as A
import cv2
import os
import glob
from tqdm import tqdm
import numpy as np

class AugmentService:
    def __init__(self):
        # Ορισμός του Pipeline Augmentation με διάφορες τεχνικές
        self.transform = A.Compose([
            A.HorizontalFlip(p=0.5),
            A.RandomRotate90(p=0.5), # Clockwise, Counter-Clockwise
            A.Rotate(limit=15, p=0.5), # Rotation -15 to +15
            A.Affine(shear={'x': (-10, 10), 'y': (-10, 10)}, p=0.5), # Shear ±10°
            A.HueSaturationValue(hue_shift_limit=0, sat_shift_limit=20, val_shift_limit=0, p=0.5), # Saturation ±20%
            A.RandomBrightnessContrast(brightness_limit=0.25, contrast_limit=0.2, p=0.5), # Brightness ±25%
            A.Blur(blur_limit=3, p=0.3), # 1.5px blur αντιστοιχεί περίπου σε limit 3
            A.GaussNoise(std_range=(0.01, 0.05), p=0.3) # Noise up to 0.1%
        ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))

    def augment_dataset(self, dataset_path, multiplier=3):
        train_path = os.path.join(dataset_path, "train")
        images_path = os.path.join(train_path, "images")
        labels_path = os.path.join(train_path, "labels")
        
        image_files = glob.glob(os.path.join(images_path, "*.jpg")) + glob.glob(os.path.join(images_path, "*.png"))

        print(f"Ξεκινάει το Augmentation για {len(image_files)} εικόνες...")

        for img_path in tqdm(image_files):
            # 1. Φόρτωση εικόνας με υποστήριξη για Ελληνικά Paths (Unicode)
            image_array = np.fromfile(img_path, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if image is None:
                print(f"Παράλειψη αρχείου (δεν διαβάζεται): {img_path}")
                continue

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 2. Φόρτωση Labels
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            label_file = os.path.join(labels_path, f"{base_name}.txt")
            
            if not os.path.exists(label_file):
                continue
                
            bboxes = []
            class_labels = []
            with open(label_file, 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) == 5:
                            try:
                                # Τα bboxes πρέπει να είναι ακριβώς 4 floats
                                coords = [float(x) for x in parts[1:5]]
                                bboxes.append(coords)
                                class_labels.append(int(parts[0]))
                            except ValueError:
                                continue
            if not bboxes:
                continue
                    

            
            # 3. Δημιουργία των 3 (multiplier) παραλλαγών
            num_new_images = multiplier - 1
            for i in range(num_new_images):
                augmented = self.transform(image=image, bboxes=bboxes, class_labels=class_labels)
                aug_img = augmented['image']
                aug_bboxes = augmented['bboxes']

                # Αποθήκευση νέας εικόνας
                new_img_name = f"{base_name}_aug_{i}.jpg"
                new_img_path = os.path.join(images_path, new_img_name)
                is_success, buffer = cv2.imencode(".jpg", cv2.cvtColor(aug_img, cv2.COLOR_RGB2BGR))
                if is_success:
                    with open(new_img_path, "wb") as f:
                        f.write(buffer)
                
                # Αποθήκευση νέου label
                new_label_name = f"{base_name}_aug_{i}.txt"
                with open(os.path.join(labels_path, new_label_name), 'w') as f:
                    for idx, bbox in enumerate(aug_bboxes):
                        f.write(f"{class_labels[idx]} {' '.join([str(x) for x in bbox])}\n")