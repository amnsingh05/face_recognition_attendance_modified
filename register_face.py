import cv2
import os
import tkinter as tk
from tkinter import simpledialog, messagebox

DATASET_DIR = "faces"

def register_face():
    # Ensure dataset folder exists
    if not os.path.exists(DATASET_DIR):
        os.makedirs(DATASET_DIR)

    # Create a hidden Tkinter window for name input
    root = tk.Tk()
    root.withdraw()

    # Ask user for name safely via GUI
    user_name = simpledialog.askstring("Register Face", "Enter your name:")
    if not user_name or not user_name.strip():
        messagebox.showwarning("Input Required", "⚠️ Name cannot be empty!")
        return

    user_name = user_name.strip().replace(" ", "_")  # sanitize name for folder
    user_dir = os.path.join(DATASET_DIR, user_name)
    os.makedirs(user_dir, exist_ok=True)

    # Initialize webcam
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        messagebox.showerror("Camera Error", "❌ Could not access the camera.")
        return

    # Load face detector
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    messagebox.showinfo("Instructions", f"📸 Capturing images for '{user_name}'.\n\n"
                                        "➡️ Press 'q' to stop early.\n"
                                        "➡️ 30 samples will be taken automatically.")

    print(f"\n📸 Capturing images for '{user_name}'...")
    count = 0

    while True:
        ret, frame = cam.read()
        if not ret:
            print("⚠️ Failed to grab frame from camera.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            count += 1
            face = frame[y:y+h, x:x+w]
            file_path = os.path.join(user_dir, f"{count}.jpg")
            cv2.imwrite(file_path, face)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"Samples: {count}/30", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("Register Face", frame)

        # Stop when 'q' pressed or 30 samples collected
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        elif count >= 30:
            break

    cam.release()
    cv2.destroyAllWindows()

    if count > 0:
        messagebox.showinfo("Success", f"✅ Successfully collected {count} face samples for '{user_name}'.")
        print(f"\n✅ Successfully collected {count} face samples for '{user_name}'.")
    else:
        messagebox.showwarning("No Faces Detected",
                               "⚠️ No faces captured. Try again with better lighting or camera position.")
        print("⚠️ No faces captured. Try again with better lighting or camera position.")

if __name__ == "__main__":
    register_face()
