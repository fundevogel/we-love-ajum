import os
import json
import hashlib


def create_path(path):
    # Determine if (future) target is appropriate data file
    if os.path.splitext(path)[1].lower() == '.json':
        path = os.path.dirname(path)

    if not os.path.exists(path):
        try:
            os.makedirs(path)

        # Guard against race condition
        except OSError:
            pass


def load_json(json_file):
    try:
        with open(json_file, 'r') as file:
            return json.load(file)

    except json.decoder.JSONDecodeError:
        raise Exception

    return {}


def dump_json(data, json_file):
    create_path(json_file)

    with open(json_file, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def dict2hash(source: dict) -> str:
    return hashlib.md5(str(source).encode('utf-8')).hexdigest()
