import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import os

def mark_attendance(name):
    file_path = 'attendance.csv'
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not os.path.exists(file_path):
        pd.DataFrame(columns=['Name', 'Time']).to_csv(file_path, index=False)

    df = pd.read_csv(file_path)

    if name not in df['Name'].values:
        new_entry = pd.DataFrame([[name, now]], columns=['Name', 'Time'])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(file_path, index=False)
        print(f"[INFO] Attendance marked for {name}")

def recognize_faces():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('trainer/trainer.yml')

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Example: you can map user IDs to names here
    names = {1: "Aman", 2: "Rahul", 3: "Priya"}

    cam = cv2.VideoCapture(0)

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            id, confidence = recognizer.predict(gray[y:y + h, x:x + w])
            if confidence < 60:
                name = names.get(id, "Unknown")
                mark_attendance(name)
                color = (0, 255, 0)
            else:
                name = "Unknown"
                color = (0, 0, 255)

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"{name} ({round(100 - confidence)}%)", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Face Recognition Attendance", frame)

        if cv2.waitKey(1) == 27:  # ESC key
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    recognize_faces()
