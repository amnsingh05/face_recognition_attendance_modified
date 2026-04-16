import cv2
import os
import datetime
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "faces")
TRAINER_PATH = os.path.join(BASE_DIR, "trainer", "trainer.yml")
LABELS_PATH = os.path.join(BASE_DIR, "trainer", "labels.csv")
ATTENDANCE_DIR = os.path.join(BASE_DIR, "attendance")
EXPECTED_COLUMNS = ["Name", "Date", "Time"]
MODEL_IMAGE_SIZE = (200, 200)


def get_today_attendance_file():
    os.makedirs(ATTENDANCE_DIR, exist_ok=True)
    today = datetime.date.today().strftime("%Y-%m-%d")
    attendance_file = os.path.join(ATTENDANCE_DIR, f"attendance_{today}.csv")
    if not os.path.exists(attendance_file):
        pd.DataFrame(columns=EXPECTED_COLUMNS).to_csv(attendance_file, index=False)
    return attendance_file


def load_label_map():
    if os.path.exists(LABELS_PATH):
        try:
            labels_df = pd.read_csv(LABELS_PATH)
            if {"id", "name"}.issubset(labels_df.columns):
                return {
                    int(row["id"]): str(row["name"])
                    for _, row in labels_df.iterrows()
                }
        except Exception:
            pass

    if not os.path.exists(DATASET_DIR):
        return {}

    users = sorted(
        name
        for name in os.listdir(DATASET_DIR)
        if os.path.isdir(os.path.join(DATASET_DIR, name))
    )
    return {i: name for i, name in enumerate(users)}


def mark_attendance(name, attendance_file):
    name = str(name).strip()
    if not name:
        return False

    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    try:
        df = pd.read_csv(attendance_file)
    except Exception:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    if not set(EXPECTED_COLUMNS).issubset(df.columns):
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
    else:
        df = df[EXPECTED_COLUMNS].fillna("")

    same_name = df["Name"].astype(str).str.strip().str.lower() == name.lower()
    same_date = df["Date"].astype(str).str.strip() == date
    if (same_name & same_date).any():
        return False

    df.loc[len(df)] = [name, date, current_time]
    df.to_csv(attendance_file, index=False)
    print(f"Attendance marked for {name} at {current_time}")
    return True


def take_attendance():
    if not hasattr(cv2, "face"):
        print("OpenCV face module not found. Install opencv-contrib-python.")
        return False

    if not os.path.exists(DATASET_DIR):
        print("Faces folder not found. Register users first.")
        return False

    if not os.path.exists(TRAINER_PATH):
        print("trainer.yml not found. Train the model first.")
        return False

    label_dict = load_label_map()
    if not label_dict:
        print("No user labels found. Train the model first.")
        return False

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(TRAINER_PATH)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    if face_cascade.empty():
        print("Failed to load Haar cascade for face detection.")
        return False

    attendance_file = get_today_attendance_file()

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Camera not accessible.")
        return False

    print("Face attendance started. Press 'q' to quit.")
    marked_names = set()

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_region = gray[y:y + h, x:x + w]
            if face_region.size == 0:
                continue

            face_region = cv2.resize(face_region, MODEL_IMAGE_SIZE)

            try:
                detected_id, confidence = recognizer.predict(face_region)
            except cv2.error:
                detected_id, confidence = -1, 999.0

            is_match = confidence < 80 and detected_id in label_dict

            if is_match:
                name = label_dict[detected_id]
                color = (0, 200, 0)
                if name not in marked_names and mark_attendance(name, attendance_file):
                    marked_names.add(name)
            else:
                name = "Unknown"
                color = (0, 0, 255)

            confidence_text = f"{confidence:.1f}" if confidence < 999 else "n/a"
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                frame,
                f"{name} ({confidence_text})",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
            )

        cv2.imshow("Face Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()
    print("Attendance recording stopped.")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if take_attendance() else 1)
