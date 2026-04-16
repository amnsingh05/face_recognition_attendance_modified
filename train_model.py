import cv2
import os
import numpy as np
import pandas as pd
from tkinter import messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "faces")
TRAINER_DIR = os.path.join(BASE_DIR, "trainer")
TRAINER_PATH = os.path.join(TRAINER_DIR, "trainer.yml")
LABELS_PATH = os.path.join(TRAINER_DIR, "labels.csv")


def train_model():
    try:
        if not os.path.exists(DATASET_PATH):
            messagebox.showerror("Error", "Faces folder not found!")
            return

        if not hasattr(cv2, "face"):
            messagebox.showerror(
                "Missing Dependency",
                "OpenCV face module not found.\nInstall opencv-contrib-python.",
            )
            return

        os.makedirs(TRAINER_DIR, exist_ok=True)

        recognizer = cv2.face.LBPHFaceRecognizer_create()

        face_samples = []
        face_ids = []
        label_rows = []
        current_id = 0

        for person_name in sorted(os.listdir(DATASET_PATH)):
            person_dir = os.path.join(DATASET_PATH, person_name)

            if not os.path.isdir(person_dir):
                continue

            label_rows.append({"id": current_id, "name": person_name})

            for img_name in os.listdir(person_dir):
                img_path = os.path.join(person_dir, img_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue

                img = cv2.resize(img, (200, 200))
                face_samples.append(img)
                face_ids.append(current_id)

            current_id += 1

        if not face_samples:
            messagebox.showerror("Error", "No images found for training!")
            return

        recognizer.train(face_samples, np.array(face_ids))
        recognizer.save(TRAINER_PATH)
        pd.DataFrame(label_rows, columns=["id", "name"]).to_csv(
            LABELS_PATH, index=False
        )

        messagebox.showinfo(
            "Training Successful",
            f"Model trained successfully!\n"
            f"Users: {len(label_rows)}\n"
            f"Samples: {len(face_samples)}",
        )

    except Exception as e:
        messagebox.showerror("Training Failed", str(e))
