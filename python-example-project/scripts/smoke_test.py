"""Smoke-test a running copy of the app: `python scripts/smoke_test.py [BASE_URL]`.

CI runs this against the Docker image after building it. It does not replace the
test suite: it checks that the thing we would ship starts, serves the page, and
can log in. Standard library only, so it runs without installing anything.

BASE_URL defaults to http://localhost:8000. The script waits up to 30 seconds for
the server to come up, then exits non-zero on the first failed check.
"""
import json
import sys
import time
import urllib.error
import urllib.request

base = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")


def request(method, path, body=None, cookie=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return res.status, res.headers, res.read()
    except urllib.error.HTTPError as err:
        return err.code, err.headers, err.read()


def check(label, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        sys.exit(1)


deadline = time.time() + 30
while True:
    try:
        request("GET", "/")
        break
    except OSError:  # refused, reset, or timed out: not up yet
        if time.time() > deadline:
            sys.exit(f"FAIL  server did not start on {base}")
        time.sleep(0.5)

status, _, page = request("GET", "/")
check("GET / serves the login page", status == 200 and b"<html" in page.lower())

status, _, _ = request("GET", "/api/widgets")
check("GET /api/widgets without a cookie is 401", status == 401)

status, headers, _ = request("POST", "/api/login", {"username": "admin", "password": "password"})
cookie = (headers.get("Set-Cookie") or "").split(";")[0]
check("POST /api/login with the seeded admin sets a cookie", status == 200 and cookie.startswith("token="))

status, _, body = request("GET", "/api/widgets", cookie=cookie)
check("GET /api/widgets with the cookie returns widgets", status == 200 and len(json.loads(body)) > 0)

print(f"Smoke test passed against {base}")
