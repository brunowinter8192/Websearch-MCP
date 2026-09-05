#!/usr/bin/env python3
"""Starts the url_discovery fixture site (_fixture_site.py) standalone and blocks until
interrupted — the zero-context entry point for a human or agent who wants to curl/inspect it
directly, or point src/crawler/discovery.py's discover_urls_workflow at a stable local URL without
wiring up start_fixture_server()/stop_fixture_server() themselves.

Start: ./venv/bin/python3 dev/url_discovery/02_fixture_site_server.py [--port N]
Stop:  Ctrl+C — shuts the server down cleanly before exiting.
"""
# INFRASTRUCTURE
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _fixture_site import start_fixture_server, stop_fixture_server, ground_truth, seed_url  # noqa: E402

DEFAULT_PORT = 8935


# ORCHESTRATOR

# Start the fixture on the given/default port, print its seed URL + ground truth, block until
# Ctrl+C, then shut it down cleanly (finally runs on the KeyboardInterrupt too, before it propagates)
def fixture_site_server_workflow(port: int) -> None:
    server, thread, bound_port = start_fixture_server(port=port)
    print(f"Fixture serving on http://127.0.0.1:{bound_port}/", file=sys.stderr)
    print(f"Seed URL for discover_urls_workflow: {seed_url(bound_port)}", file=sys.stderr)
    print(json.dumps(ground_truth(), indent=2), file=sys.stderr)
    print("Ctrl+C to stop.", file=sys.stderr)
    try:
        while True:
            time.sleep(3600)
    finally:
        stop_fixture_server(server, thread)
        print("Fixture server stopped.", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    fixture_site_server_workflow(args.port)
