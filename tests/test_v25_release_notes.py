#!/usr/bin/env python3
"""HTTP integration tests for the V25.2 release-notes flow."""
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


def call(base, path, method="GET", payload=None, cookie=None):
    headers = {}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    if cookie:
        headers["Cookie"] = cookie
    if method in ("POST", "PUT", "DELETE"):
        headers["Origin"] = base
    request = urllib.request.Request(base + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()


def main():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    temporary = Path(tempfile.mkdtemp(prefix="maclasse-v252-release-notes-"))
    app = temporary / "app"
    shutil.copytree(SOURCE, app)
    env = os.environ.copy()
    env["MACLASSE_HOST"] = "127.0.0.1"
    env["MACLASSE_PORT"] = str(port)
    env.pop("MACLASSE_TLS_CERT", None)
    env.pop("MACLASSE_TLS_KEY", None)
    process = subprocess.Popen(
        ["python3", "server.py"], cwd=app, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        ready = False
        for _ in range(60):
            try:
                status, _, _ = call(base, "/api/health")
                if status == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.1)
        assert ready, "Temporary MaClasse server did not start."

        assert call(base, "/api/release-notes/state")[0] == 401
        assert call(base, "/api/release-notes/history")[0] == 401
        assert call(base, "/api/release-notes/ack", "POST", {"version": "25.2.0"})[0] == 401

        status, headers, body = call(base, "/api/auth/setup", "POST", {
            "first": "Test", "last": "Direction", "username": "direction",
            "password": "motDePasseTestLongEtSolide!"
        })
        assert status == 201, body.decode("utf-8", "replace")
        account = json.loads(body)["user"]
        cookie = headers.get("Set-Cookie").split(";")[0]
        account_id = str(account["id"])

        status, _, body = call(base, "/api/release-notes/state", cookie=cookie)
        assert status == 200
        state = json.loads(body)
        assert state["version"] == "25.2.0"
        assert state["seen_version"] == ""

        status, _, body = call(base, "/api/release-notes/history", cookie=cookie)
        assert status == 200
        history = json.loads(body)
        assert history["current_version"] == "25.2.0"
        source_paths = {item["path"] for item in history["history_documents"]}
        assert "docs/HISTORIQUE_VERSIONS.md" in source_paths
        assert "docs/archives/ETATS_AUDITS_ET_RECETTES_ANTERIEURS.md" in source_paths
        assert "docs/archives/README_PRE_REORGANISATION.md" in source_paths
        assert "V25.2.0" in history["current_release_markdown"]

        status, _, body = call(base, "/api/release-notes/ack", "POST", {
            "version": "25.2.0", "account_id": "forged-other-account"
        }, cookie)
        assert status == 200, body.decode("utf-8", "replace")
        saved = json.loads(body)
        assert saved["seen_version"] == "25.2.0"

        # A second login cookie for the same account sees the server-side acknowledgement.
        status, login_headers, _ = call(base, "/api/auth/login", "POST", {
            "username": "direction", "password": "motDePasseTestLongEtSolide!"
        })
        assert status == 200
        second_cookie = login_headers.get("Set-Cookie").split(";")[0]
        status, _, body = call(base, "/api/release-notes/state", cookie=second_cookie)
        assert status == 200 and json.loads(body)["seen_version"] == "25.2.0"

        assert call(base, "/api/release-notes/ack", "POST", {"version": "25.2.1"}, cookie)[0] == 409
        assert call(base, "/api/release-notes/state")[0] == 401
        assert account_id

        print("OK — V25.2.0 nouveautés : routes protégées, historique multi-sources, compte serveur et accusé inter-session.")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    main()
