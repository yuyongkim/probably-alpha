"""Single-command server: API + Frontend in one process.

Usage:
    python scripts/serve.py
    python scripts/serve.py --api-port 8000 --frontend-port 8080
    python scripts/serve.py --no-browser

Starts both uvicorn (API) and http.server (frontend) as subprocesses,
opens the browser, and keeps running until Ctrl+C.
"""
from __future__ import annotations

import argparse
import http.server
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(str(ROOT))


def start_api(host: str, port: int) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'sepa.api.app:app', '--host', host, '--port', str(port)],
        cwd=str(ROOT),
    )


def start_frontend(port: int) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(port), '--directory', 'sepa/frontend'],
        cwd=str(ROOT),
    )


def wait_for_health(url: str, timeout: int = 30) -> bool:
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(f'{url}/api/health', timeout=2)
            if resp.status == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(description='SEPA Server (API + Frontend)')
    parser.add_argument('--api-host', default='127.0.0.1')
    parser.add_argument('--api-port', type=int, default=8000)
    parser.add_argument('--frontend-port', type=int, default=8080)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()

    api_url = f'http://{args.api_host}:{args.api_port}'
    frontend_url = f'http://127.0.0.1:{args.frontend_port}'

    print(f'[1/3] Starting API server on {args.api_host}:{args.api_port}...')
    api_proc = start_api(args.api_host, args.api_port)

    print(f'[2/3] Starting frontend on 127.0.0.1:{args.frontend_port}...')
    frontend_proc = start_frontend(args.frontend_port)

    print('[3/3] Waiting for API health check...')
    if wait_for_health(api_url):
        print(f'API OK: {api_url}')
    else:
        print('WARNING: API health check timed out, but server may still be starting.')

    if not args.no_browser:
        webbrowser.open(frontend_url)

    print(f'\n  Frontend: {frontend_url}')
    print(f'  API:      {api_url}')
    print(f'  Backtest: {frontend_url}/backtest.html')
    print(f'\n  Press Ctrl+C to stop.\n')

    try:
        while True:
            if api_proc.poll() is not None:
                print('API server stopped. Restarting...')
                api_proc = start_api(args.api_host, args.api_port)
            if frontend_proc.poll() is not None:
                print('Frontend server stopped. Restarting...')
                frontend_proc = start_frontend(args.frontend_port)
            time.sleep(2)
    except KeyboardInterrupt:
        print('\nShutting down...')
        api_proc.terminate()
        frontend_proc.terminate()
        api_proc.wait(timeout=5)
        frontend_proc.wait(timeout=5)
        print('Done.')


if __name__ == '__main__':
    main()
