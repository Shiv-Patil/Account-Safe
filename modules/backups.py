import json
from modules import encryption
from kivymd.app import MDApp
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from cryptography.fernet import InvalidToken
import traceback
import os
app = MDApp.get_running_app()

user_json = {
    "type": "object",
    "required": ['user', 'accounts'],
    "properties": {
        "user": {
            "type": "array",
            "items": [
                {"type": "string"},
                {"type": "string"},
                {"type": "string"},
                {"type": "string"}
            ]
        },
        "accounts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "pinned", "passwords"],
                "properties": {
                    "name": {"type": "string"},
                    "pinned": {"type": "number"},
                    "passwords": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["username", "password", "strength", "color"],
                            "properties": {
                                "username": {"type": "string"},
                                "password": {"type": "string"},
                                "strength": {"type": "string"},
                                "color": {"type": "string"}
                            }
                        }
                    },
                }
            }
        }
    }
}


def save_backup(path):
    backup = dict()

    user = app.dashboard.current_user
    backup['user'] = [user.text, user.key,
                      user.salt.decode('cp437'), user.source]
    backup['accounts'] = []

    select_query = "SELECT * FROM accounts WHERE user = ?"
    account_list = app.db.execute_read_query(select_query, (user.id,))

    for i in account_list:
        select_query = "SELECT * FROM passwords WHERE account = ?"
        password_list = app.db.execute_read_query(select_query, (i[0],))
        passwords = []
        for pw in password_list:
            _ = {
                "username": pw[3],
                "password": pw[4],
                "strength": pw[5],
                "color": pw[6],
            }
            passwords.append(_)
        tmp = {
            "name": i[2],
            "pinned": i[3],
            "passwords": passwords
        }
        backup['accounts'].append(tmp)

    try:
        validate(backup, user_json)
    except ValidationError:
        return False

    key = encryption.generate_key(
        b'y\xcb\xed\nU\xa9\x12n\xb4\xb8\x8d<\xff\xc0\x1b\xcb', 'KrYmZiN')
    to_store = encryption.encrypt(key, json.dumps(backup))

    dir = os.path.dirname(path)
    if not os.path.isdir(dir):
        os.makedirs(dir)

    with open(path, 'w') as f:
        f.write(to_store)

    return True


def load_backup(path):
    file = ""
    try:
        if not path.endswith(".accountsafebackup"):
            raise Exception("Invalid backup file")
        with open(path, 'r') as f:
            file = f.read()
    except:
        traceback.print_exc()
        return (False, "Invalid backup file")
    key = encryption.generate_key(
        b'y\xcb\xed\nU\xa9\x12n\xb4\xb8\x8d<\xff\xc0\x1b\xcb', 'KrYmZiN')
    try:
        loaded = encryption.decrypt(key, file)
    except InvalidToken:
        return (False, "Backup file corrupted")
    loaded = json.loads(loaded)
    try:
        validate(loaded, user_json)
    except ValidationError:
        return (False, "Backup file corrupted")
    loaded['user'][2] = loaded['user'][2].encode('cp437')
    return (True, loaded)
