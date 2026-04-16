import os
import re
import hmac
import hashlib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.csv")
REQUIRED_COLUMNS = ["username", "password", "security_question", "security_answer"]
HASH_PREFIX = "sha256$"
MIN_PASSWORD_LENGTH = 6


def _empty_users_df():
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def _normalize_text(value):
    return str(value).strip()


def _hash_secret(value):
    value = _normalize_text(value)
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"{HASH_PREFIX}{digest}"


def _is_hashed(value):
    return _normalize_text(value).startswith(HASH_PREFIX)


def _secret_matches(raw_value, stored_value):
    raw_value = _normalize_text(raw_value)
    stored_value = _normalize_text(stored_value)

    if not raw_value or not stored_value:
        return False

    if _is_hashed(stored_value):
        return hmac.compare_digest(_hash_secret(raw_value), stored_value)

    return hmac.compare_digest(raw_value, stored_value)


def validate_password_strength(password):
    password = _normalize_text(password)

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."

    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."

    return True, ""


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


def _find_user_mask(users, username):
    username = _normalize_text(username).lower()
    return users["username"].astype(str).str.strip().str.lower() == username


def _migrate_hash_columns(users):
    users = users.copy()

    users["password"] = users["password"].apply(
        lambda value: _hash_secret(value) if _normalize_text(value) and not _is_hashed(value) else _normalize_text(value)
    )

    users["security_answer"] = users["security_answer"].apply(
        lambda value: _hash_secret(value) if _normalize_text(value) and not _is_hashed(value) else _normalize_text(value)
    )

    return users


def init_users():
    """
    Create users.csv if missing, repair invalid rows, and migrate credentials to hashes.
    """
    if not os.path.exists(USERS_FILE):
        _save_users(_empty_users_df())

    raw_users = _read_users()
    raw_users = raw_users[
        (raw_users["username"].astype(str).str.strip() != "")
        & (raw_users["password"].astype(str).str.strip() != "")
    ].copy()

    if raw_users.empty:
        print("No admin found. Creating default admin account (admin/admin123)")
        raw_users = pd.DataFrame(
            [
                {
                    "username": "admin",
                    "password": _hash_secret("admin123"),
                    "security_question": "What is your favorite color?",
                    "security_answer": _hash_secret("blue"),
                }
            ]
        )
    else:
        raw_users = _migrate_hash_columns(raw_users)

    _save_users(raw_users)


def verify_login(username, password):
    users = _read_users()
    match_mask = _find_user_mask(users, username)
    if not match_mask.any():
        return False

    match_index = users[match_mask].index[0]
    stored_password = users.at[match_index, "password"]

    if not _secret_matches(password, stored_password):
        return False

    if not _is_hashed(stored_password):
        users.at[match_index, "password"] = _hash_secret(password)
        _save_users(users)

    return True


def add_user(username, password, security_question, security_answer):
    users = _read_users()
    username = _normalize_text(username)
    password = _normalize_text(password)
    security_question = _normalize_text(security_question)
    security_answer = _normalize_text(security_answer)

    if not username or not password or not security_question or not security_answer:
        return False

    is_valid_password, _ = validate_password_strength(password)
    if not is_valid_password:
        return False

    if _find_user_mask(users, username).any():
        return False

    new_user = pd.DataFrame(
        {
            "username": [username],
            "password": [_hash_secret(password)],
            "security_question": [security_question],
            "security_answer": [_hash_secret(security_answer)],
        }
    )
    users = pd.concat([users, new_user], ignore_index=True)
    _save_users(users)
    return True


def change_password(username, old_password, new_password):
    users = _read_users()
    username_mask = _find_user_mask(users, username)
    if not username_mask.any():
        return False

    is_valid_password, _ = validate_password_strength(new_password)
    if not is_valid_password:
        return False

    match_index = users[username_mask].index[0]
    stored_password = users.at[match_index, "password"]

    if not _secret_matches(old_password, stored_password):
        return False

    users.at[match_index, "password"] = _hash_secret(new_password)
    _save_users(users)
    return True


def get_security_question(username):
    users = _read_users()
    username_mask = _find_user_mask(users, username)
    if username_mask.any():
        return users.loc[username_mask, "security_question"].iloc[0]
    return None


def reset_password_if_correct(username, answer, new_password):
    users = _read_users()
    username_mask = _find_user_mask(users, username)
    if not username_mask.any():
        return False

    is_valid_password, _ = validate_password_strength(new_password)
    if not is_valid_password:
        return False

    match_index = users[username_mask].index[0]
    stored_answer = users.at[match_index, "security_answer"]

    if not _secret_matches(answer, stored_answer):
        return False

    if not _is_hashed(stored_answer):
        users.at[match_index, "security_answer"] = _hash_secret(answer)

    users.at[match_index, "password"] = _hash_secret(new_password)
    _save_users(users)
    return True


init_users()
