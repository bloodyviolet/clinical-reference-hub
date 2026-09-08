#!/usr/bin/env python3
"""Small dependency-free HTTP load probe for release/staging use (not a replacement for distributed load testing)."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import statistics
import time
from urllib.request import Request, urlopen


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, math.ceil(p * len(ordered)) - 1))
    return ordered[idx]


def fetch(url: str, timeout: float) -> tuple[int, float, int]:
    started = time.perf_counter()
    request = Request(url, headers={"User-Agent": "medical-api-load-probe/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            status = response.status
    except Exception:
        return 0, (time.perf_counter() - started) * 1000, 0
    return status, (time.perf_counter() - started) * 1000, len(body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--min-success-rate", type=float, default=0.99)
    args = parser.parse_args()
    started = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(fetch, args.url, args.timeout) for _ in range(args.requests)]
        for future in as_completed(futures):
            results.append(future.result())
    elapsed = time.perf_counter() - started
    latencies = [latency for status, latency, _ in results if status]
    successes = sum(1 for status, _, _ in results if 200 <= status < 400)
    payload = {
        "url": args.url,
        "requests": len(results),
        "concurrency": args.concurrency,
        "successes": successes,
        "success_rate": round(successes / max(1, len(results)), 4),
        "elapsed_seconds": round(elapsed, 3),
        "requests_per_second": round(len(results) / max(elapsed, 0.0001), 2),
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 3) if latencies else 0,
            "p50": round(percentile(latencies, 0.50), 3),
            "p95": round(percentile(latencies, 0.95), 3),
            "p99": round(percentile(latencies, 0.99), 3),
            "max": round(max(latencies), 3) if latencies else 0,
        },
        "bytes_received": sum(size for _, _, size in results),
    }
    print(json.dumps(payload, indent=2))
    return 0 if payload["success_rate"] >= args.min_success_rate else 2


if __name__ == "__main__":
    raise SystemExit(main())
