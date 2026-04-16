import datetime
import os
import re
from io import BytesIO

import numpy as np
import pandas as pd

try:
    import cv2
    CV2_IMPORT_ERROR = None
except Exception as exc:
    cv2 = None
    CV2_IMPORT_ERROR = str(exc)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "faces")
TRAINER_DIR = os.path.join(BASE_DIR, "trainer")
TRAINER_PATH = os.path.join(TRAINER_DIR, "trainer.yml")
LABELS_PATH = os.path.join(TRAINER_DIR, "labels.csv")
ATTENDANCE_DIR = os.path.join(BASE_DIR, "attendance")

EXPECTED_COLUMNS = ["Name", "Date", "Time"]
MODEL_IMAGE_SIZE = (200, 200)
NAME_PATTERN = re.compile(r"[^A-Za-z0-9_ ]+")


def get_opencv_status():
    if cv2 is None:
        return (
            False,
            "OpenCV could not be imported. "
            "For Streamlit Cloud use `opencv-contrib-python-headless`.\n"
            f"Import error: {CV2_IMPORT_ERROR}",
        )
    return True, ""


def _opencv_error_result(message):
    return {
        "success": False,
        "message": message,
    }


def ensure_directories():
    os.makedirs(DATASET_DIR, exist_ok=True)
    os.makedirs(TRAINER_DIR, exist_ok=True)
    os.makedirs(ATTENDANCE_DIR, exist_ok=True)


def sanitize_person_name(name):
    cleaned = NAME_PATTERN.sub("", str(name).strip())
    cleaned = cleaned.replace(" ", "_")
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def _decode_image_to_bgr(image_input):
    if cv2 is None:
        return None

    if image_input is None:
        return None

    if isinstance(image_input, np.ndarray):
        frame = image_input.copy()
        if frame.ndim == 2:
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        return frame

    if hasattr(image_input, "read"):
        image_bytes = image_input.read()
    elif isinstance(image_input, (bytes, bytearray)):
        image_bytes = bytes(image_input)
    else:
        return None

    if not image_bytes:
        return None

    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    return frame


def _get_face_detector():
    if cv2 is None:
        return None

    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    if detector.empty():
        return None
    return detector


def _next_sample_number(person_dir):
    max_num = 0
    for filename in os.listdir(person_dir):
        stem, ext = os.path.splitext(filename)
        if ext.lower() != ".jpg":
            continue
        if stem.isdigit():
            max_num = max(max_num, int(stem))
    return max_num + 1


def save_face_sample(person_name, image_input):
    ensure_directories()

    cv2_ok, cv2_message = get_opencv_status()
    if not cv2_ok:
        return _opencv_error_result(cv2_message)

    safe_name = sanitize_person_name(person_name)
    if not safe_name:
        return {
            "success": False,
            "message": "Enter a valid name (letters, numbers, underscore).",
        }

    frame = _decode_image_to_bgr(image_input)
    if frame is None:
        return {
            "success": False,
            "message": "Could not read image data.",
        }

    detector = _get_face_detector()
    if detector is None:
        return {
            "success": False,
            "message": "Failed to load Haar cascade face detector.",
        }

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.25, minNeighbors=5, minSize=(60, 60))

    if len(faces) == 0:
        return {
            "success": False,
            "message": "No face detected. Try a clearer image.",
        }

    x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
    face_crop = frame[y:y + h, x:x + w]
    if face_crop.size == 0:
        return {
            "success": False,
            "message": "Detected face region was invalid.",
        }

    person_dir = os.path.join(DATASET_DIR, safe_name)
    os.makedirs(person_dir, exist_ok=True)

    sample_num = _next_sample_number(person_dir)
    sample_path = os.path.join(person_dir, f"{sample_num}.jpg")

    saved = cv2.imwrite(sample_path, face_crop)
    if not saved:
        return {
            "success": False,
            "message": "Could not write sample image to disk.",
        }

    return {
        "success": True,
        "message": f"Saved sample {sample_num} for {safe_name}.",
        "name": safe_name,
        "sample_path": sample_path,
        "sample_number": sample_num,
    }


def list_registered_users():
    ensure_directories()
    users = [
        name
        for name in os.listdir(DATASET_DIR)
        if os.path.isdir(os.path.join(DATASET_DIR, name))
    ]
    return sorted(users)


def count_face_samples(name=None):
    ensure_directories()

    if name:
        person_dir = os.path.join(DATASET_DIR, name)
        if not os.path.isdir(person_dir):
            return 0
        return sum(
            1
            for filename in os.listdir(person_dir)
            if filename.lower().endswith(".jpg")
        )

    total = 0
    for user in list_registered_users():
        total += count_face_samples(user)
    return total


def train_model_from_dataset():
    ensure_directories()

    cv2_ok, cv2_message = get_opencv_status()
    if not cv2_ok:
        return _opencv_error_result(cv2_message)

    if not hasattr(cv2, "face"):
        return {
            "success": False,
            "message": "OpenCV face module missing. Install opencv-contrib-python-headless.",
        }

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    face_samples = []
    face_ids = []
    label_rows = []
    current_id = 0

    for person_name in list_registered_users():
        person_dir = os.path.join(DATASET_DIR, person_name)

        person_samples = []
        for img_name in os.listdir(person_dir):
            img_path = os.path.join(person_dir, img_name)
            image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue

            image = cv2.resize(image, MODEL_IMAGE_SIZE)
            person_samples.append(image)

        if not person_samples:
            continue

        label_rows.append({"id": current_id, "name": person_name})
        face_samples.extend(person_samples)
        face_ids.extend([current_id] * len(person_samples))
        current_id += 1

    if not face_samples:
        return {
            "success": False,
            "message": "No valid face images found. Register users first.",
        }

    recognizer.train(face_samples, np.array(face_ids))
    recognizer.save(TRAINER_PATH)

    labels_df = pd.DataFrame(label_rows, columns=["id", "name"])
    labels_df.to_csv(LABELS_PATH, index=False)

    return {
        "success": True,
        "message": "Model trained successfully.",
        "users": len(label_rows),
        "samples": len(face_samples),
        "labels": labels_df,
    }


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

    users = list_registered_users()
    return {idx: name for idx, name in enumerate(users)}


def get_today_attendance_file():
    ensure_directories()
    today = datetime.date.today().strftime("%Y-%m-%d")
    attendance_file = os.path.join(ATTENDANCE_DIR, f"attendance_{today}.csv")

    if not os.path.exists(attendance_file):
        pd.DataFrame(columns=EXPECTED_COLUMNS).to_csv(attendance_file, index=False)

    return attendance_file


def mark_attendance(name, attendance_file=None):
    attendance_file = attendance_file or get_today_attendance_file()
    person_name = str(name).strip()

    if not person_name:
        return False

    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    try:
        df = pd.read_csv(attendance_file)
    except Exception:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    if not set(EXPECTED_COLUMNS).issubset(df.columns):
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
    else:
        df = df[EXPECTED_COLUMNS].fillna("")

    duplicate = (
        df["Name"].astype(str).str.strip().str.lower().eq(person_name.lower())
        & df["Date"].astype(str).str.strip().eq(today)
    )

    if duplicate.any():
        return False

    df.loc[len(df)] = [person_name, today, current_time]
    df.to_csv(attendance_file, index=False)
    return True


def get_attendance_files():
    ensure_directories()
    files = [
        os.path.join(ATTENDANCE_DIR, filename)
        for filename in os.listdir(ATTENDANCE_DIR)
        if filename.lower().endswith(".csv")
    ]
    return sorted(files, key=os.path.getmtime, reverse=True)


def load_attendance_dataframe(file_path):
    try:
        df = pd.read_csv(file_path)
    except Exception:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    if df.empty:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    df.columns = [str(c).strip().lower() for c in df.columns]

    name_col = next((c for c in df.columns if c in ["name", "username"]), None)
    date_col = next((c for c in df.columns if c == "date" or "date" in c), None)
    time_col = next((c for c in df.columns if c == "time" or "time" in c), None)

    if not name_col or not time_col:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    normalized = pd.DataFrame(
        {
            "Name": df[name_col].astype(str).str.strip().replace("", "-"),
            "Date": (
                df[date_col].astype(str).str.strip().replace("", "-")
                if date_col
                else "-"
            ),
            "Time": df[time_col].astype(str).str.strip().replace("", "-"),
        }
    )

    return normalized.reset_index(drop=True)


def _load_recognizer():
    cv2_ok, cv2_message = get_opencv_status()
    if not cv2_ok:
        return None, cv2_message

    if not hasattr(cv2, "face"):
        return None, "OpenCV face module missing. Install opencv-contrib-python-headless."

    if not os.path.exists(TRAINER_PATH):
        return None, "Model not trained yet. Train model first."

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(TRAINER_PATH)
    return recognizer, None


def recognize_and_mark_attendance(image_input, confidence_threshold=80.0):
    ensure_directories()

    recognizer, recognizer_error = _load_recognizer()
    if recognizer_error:
        return {
            "success": False,
            "message": recognizer_error,
        }

    label_map = load_label_map()
    if not label_map:
        return {
            "success": False,
            "message": "No registered users found. Register and train first.",
        }

    detector = _get_face_detector()
    if detector is None:
        return {
            "success": False,
            "message": "Failed to load face detector.",
        }

    frame = _decode_image_to_bgr(image_input)
    if frame is None:
        return {
            "success": False,
            "message": "Could not read image data.",
        }

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.25, minNeighbors=5, minSize=(60, 60))

    attendance_file = get_today_attendance_file()

    detections = []
    marked_names = []
    already_marked_names = []

    for (x, y, w, h) in faces:
        region = gray[y:y + h, x:x + w]
        if region.size == 0:
            continue

        region = cv2.resize(region, MODEL_IMAGE_SIZE)

        try:
            detected_id, confidence = recognizer.predict(region)
        except cv2.error:
            detected_id, confidence = -1, 999.0

        matched = confidence < float(confidence_threshold) and detected_id in label_map

        if matched:
            name = label_map[detected_id]
            marked = mark_attendance(name, attendance_file)
            if marked:
                marked_names.append(name)
            else:
                already_marked_names.append(name)
            color = (18, 133, 98)
        else:
            name = "Unknown"
            marked = False
            color = (205, 63, 69)

        label_conf = f"{confidence:.1f}" if confidence < 999 else "n/a"
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            frame,
            f"{name} ({label_conf})",
            (x, max(y - 10, 0)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

        detections.append(
            {
                "Name": name,
                "Confidence": round(float(confidence), 2) if confidence < 999 else None,
                "Marked": bool(marked),
            }
        )

    annotated_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    return {
        "success": True,
        "message": "Recognition completed.",
        "detections": detections,
        "faces_found": int(len(faces)),
        "marked_names": sorted(set(marked_names)),
        "already_marked_names": sorted(set(already_marked_names)),
        "attendance_file": attendance_file,
        "annotated_rgb": annotated_rgb,
    }


def dataframe_to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
    output.seek(0)
    return output.getvalue()


def get_dashboard_stats():
    users = list_registered_users()
    attendance_files = get_attendance_files()

    latest_file = attendance_files[0] if attendance_files else None
    latest_df = load_attendance_dataframe(latest_file) if latest_file else pd.DataFrame(columns=EXPECTED_COLUMNS)

    return {
        "users": len(users),
        "samples": count_face_samples(),
        "attendance_files": len(attendance_files),
        "latest_records": len(latest_df),
        "latest_file": latest_file,
    }
