#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> int:
    parser = argparse.ArgumentParser(description="Readiness probe with optional Host header.")
    parser.add_argument('--url', default=os.getenv('MEDICAL_API_HEALTHCHECK_URL', 'http://127.0.0.1:8000/api/v1/readyz'))
    parser.add_argument('--host', default=os.getenv('MEDICAL_API_HEALTHCHECK_HOST'))
    parser.add_argument('--timeout', type=float, default=5)
    args = parser.parse_args()
    headers = {'User-Agent': 'medical-api-health-probe/1.0'}
    if args.host:
        headers['Host'] = args.host
    try:
        with urlopen(Request(args.url, headers=headers), timeout=args.timeout) as response:
            body = response.read()
            payload = json.loads(body)
            if response.status != 200 or payload.get('status') != 'ok':
                raise RuntimeError(f'unhealthy status={response.status} payload={payload}')
    except (HTTPError, URLError, ValueError, RuntimeError) as exc:
        print(f'FAIL {exc}')
        return 2
    print(f"OK revision={payload.get('database_revision')} api={payload.get('api_version')}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
