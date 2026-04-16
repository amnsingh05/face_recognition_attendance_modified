import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.csv")
REQUIRED_COLUMNS = ["username", "password", "security_question", "security_answer"]


def _empty_users_df():
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def _read_users():
    try:
        users = pd.read_csv(USERS_FILE)
    except Exception:
        users = _empty_users_df()

    for col in REQUIRED_COLUMNS:
        if col not in users.columns:
            users[col] = ""

    users = users[REQUIRED_COLUMNS].fillna("")
    users = users.astype(str).apply(lambda x: x.str.strip())
    return users


def _save_users(users):
    users = users[REQUIRED_COLUMNS].fillna("")
    users.to_csv(USERS_FILE, index=False)


def init_users():
    """
    Create users.csv if missing, or repair it if it contains non-admin data.
    """
    if not os.path.exists(USERS_FILE):
        _save_users(_empty_users_df())

    raw_users = _read_users()
    raw_users = raw_users[
        (raw_users["username"] != "") & (raw_users["password"] != "")
    ].copy()
    if raw_users.empty:
        print("No admin found. Creating default admin account (admin/admin123)")
        raw_users = pd.DataFrame([
            {
                "username": "admin",
                "password": "admin123",
                "security_question": "What is your favorite color?",
                "security_answer": "blue",
            }
        ])

    _save_users(raw_users)


def verify_login(username, password):
    users = _read_users()
    username = str(username).strip()
    password = str(password).strip()
    user = users[(users["username"] == username) & (users["password"] == password)]
    return not user.empty


def add_user(username, password, security_question, security_answer):
    users = _read_users()
    username = str(username).strip()

    if username.lower() in users["username"].str.lower().values:
        return False

    new_user = pd.DataFrame(
        {
            "username": [username],
            "password": [str(password).strip()],
            "security_question": [str(security_question).strip()],
            "security_answer": [str(security_answer).strip()],
        }
    )
    users = pd.concat([users, new_user], ignore_index=True)
    _save_users(users)
    return True


def change_password(username, old_password, new_password):
    users = _read_users()
    username = str(username).strip()
    old_password = str(old_password).strip()

    match = (users["username"] == username) & (users["password"] == old_password)
    if match.any():
        users.loc[match, "password"] = str(new_password).strip()
        _save_users(users)
        return True
    return False


def get_security_question(username):
    users = _read_users()
    user = users[users["username"] == str(username).strip()]
    if not user.empty:
        return user.iloc[0]["security_question"]
    return None


def reset_password_if_correct(username, answer, new_password):
    users = _read_users()
    username = str(username).strip()
    user = users[users["username"] == username]
    if user.empty:
        return False

    saved_answer = str(user.iloc[0]["security_answer"]).strip().lower()
    provided_answer = str(answer).strip().lower()
    if saved_answer != provided_answer:
        return False

    if not str(new_password).strip():
        return False

    users.loc[users["username"] == username, "password"] = str(new_password).strip()
    _save_users(users)
    return True


init_users()
