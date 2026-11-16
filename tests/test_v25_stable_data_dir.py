#!/usr/bin/env python3
"""Integration test: versioned program path must keep user data in stable storage."""
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]


def request(base, path, method="GET", payload=None, cookie=None):
    headers = {}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode()
    if cookie:
        headers["Cookie"] = cookie
    if method in ("POST", "PUT", "DELETE"):
        headers["Origin"] = base
    req = urllib.request.Request(base + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()


def run():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    temp = Path(tempfile.mkdtemp(prefix="maclasse-stable-data-"))
    app = temp / "program"
    data = temp / "persistent-data"
    shutil.copytree(SOURCE, app, ignore=shutil.ignore_patterns('data', '.git', '.venv', '__pycache__'))
    env = os.environ.copy()
    env.update({"MACLASSE_HOST": "127.0.0.1", "MACLASSE_PORT": str(port),
                "MACLASSE_DATA_DIR": str(data)})
    process = subprocess.Popen(["python3", "server.py"], cwd=app, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            try:
                request(base, "/api/health")
                break
            except Exception:
                time.sleep(.1)
        status, _, body = request(base, "/api/auth/setup", "POST",
                                  {"first": "Direction", "last": "Test",
                                   "username": "direction",
                                   "password": "unMotDePasseTresSolidePourTest!"})
        assert status == 201, body
        cookie = request(base, "/api/auth/login", "POST",
                         {"username": "direction",
                          "password": "unMotDePasseTresSolidePourTest!"})[1].get("Set-Cookie").split(";")[0]
        target = data / "uploads" / "general" / "piece.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fichier conservé hors du code", encoding="utf-8")
        status, _, body = request(base, "/data/uploads/general/piece.txt", cookie=cookie)
        assert status == 200 and body.decode("utf-8") == "fichier conservé hors du code"
        assert (data / "maclasse.json").is_file()
        assert not (app / "data" / "maclasse.json").exists()
        print("OK — base et pièces jointes servies depuis MACLASSE_DATA_DIR, indépendamment du dossier de code.")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    run()
