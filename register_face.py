import cv2
import os
import tkinter as tk
from tkinter import simpledialog, messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "faces")
MAX_SAMPLES = 30


def register_face():
    os.makedirs(DATASET_DIR, exist_ok=True)

    root = tk.Tk()
    root.withdraw()

    cam = None

    try:
        user_name = simpledialog.askstring("Register Face", "Enter your name:")
        if not user_name or not user_name.strip():
            messagebox.showwarning("Input Required", "Name cannot be empty.")
            return

        user_name = user_name.strip().replace(" ", "_")
        user_dir = os.path.join(DATASET_DIR, user_name)
        os.makedirs(user_dir, exist_ok=True)

        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            messagebox.showerror("Camera Error", "Could not access the camera.")
            return

        detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        if detector.empty():
            messagebox.showerror("Error", "Failed to load face detector.")
            return

        messagebox.showinfo(
            "Instructions",
            (
                f"Capturing images for '{user_name}'.\n\n"
                "Press 'q' to stop early.\n"
                f"{MAX_SAMPLES} samples will be captured automatically."
            ),
        )

        print(f"Capturing images for '{user_name}'...")
        count = 0

        while True:
            ret, frame = cam.read()
            if not ret:
                print("Failed to grab frame from camera.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

            for (x, y, w, h) in faces:
                count += 1
                face = frame[y:y + h, x:x + w]
                file_path = os.path.join(user_dir, f"{count}.jpg")
                cv2.imwrite(file_path, face)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"Samples: {count}/{MAX_SAMPLES}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

                if count >= MAX_SAMPLES:
                    break

            cv2.imshow("Register Face", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            if count >= MAX_SAMPLES:
                break

        if count > 0:
            messagebox.showinfo(
                "Success",
                f"Successfully collected {count} face samples for '{user_name}'.",
            )
            print(f"Successfully collected {count} face samples for '{user_name}'.")
        else:
            messagebox.showwarning(
                "No Faces Detected",
                "No faces captured. Try again with better lighting or camera position.",
            )
            print("No faces captured. Try again with better lighting or camera position.")

    finally:
        if cam is not None:
            cam.release()
        cv2.destroyAllWindows()
        root.destroy()


if __name__ == "__main__":
    register_face()
