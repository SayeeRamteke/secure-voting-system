import requests
import time

BASE_URL = "http://localhost:8000"

ENDPOINTS = [
    ("GET",  "/health"),
    ("POST", "/register/begin"),
    ("POST", "/vote/begin"),
]

RUNS = 5

print("=" * 50)
print("LATENCY BENCHMARK")
print("=" * 50)

for method, endpoint in ENDPOINTS:
    times = []

    for _ in range(RUNS):
        try:
            start = time.time()
            if method == "GET":
                requests.get(BASE_URL + endpoint, timeout=3)
            else:
                requests.post(BASE_URL + endpoint, json={}, timeout=3)
            end = time.time()
            times.append((end - start) * 1000)
        except Exception:
            times.append(None)

    valid = [t for t in times if t is not None]

    if valid:
        avg = sum(valid) / len(valid)
        print(f"{method} {endpoint}")
        print(f"  Avg: {avg:.1f}ms  Min: {min(valid):.1f}ms  Max: {max(valid):.1f}ms")
    else:
        print(f"{method} {endpoint} — server not reachable")

print("=" * 50)
print("Benchmark complete.")