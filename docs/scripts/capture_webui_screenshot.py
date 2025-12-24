#!/usr/bin/env python
"""
Capture a screenshot of the flowtoy webui for documentation.

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    python capture_webui_screenshot.py flow.yaml output.png

Example:
    python capture_webui_screenshot.py docs/demo-flow.yaml \
        docs/images/webui-screenshot.png
"""

import argparse
import socket
import subprocess
import time

from playwright.sync_api import sync_playwright


def find_available_port():
    """Find an available port by binding to port 0."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def capture_webui_screenshot(flow_file, output_path, port=None):
    """Start webui, capture screenshot, cleanup."""

    # Find an available port if not specified
    if port is None:
        port = find_available_port()

    # Start webui server
    print(f"Starting webui on port {port}...")
    process = subprocess.Popen(
        ["python", "-m", "flowtoy", "webui", flow_file, "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait for server to start and flow to execute
    print("Waiting for flow to execute...")
    time.sleep(5)

    # Check if process is still running
    if process.poll() is not None:
        output, _ = process.communicate()
        print(f"Server failed to start:\n{output}")
        raise RuntimeError("Server failed to start")

    try:
        # Launch browser and capture screenshot
        print(f"Capturing screenshot from http://127.0.0.1:{port}...")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 800})

            try:
                page.goto(f"http://127.0.0.1:{port}", timeout=10000)

                # Wait for content to load
                page.wait_for_selector("#steps", timeout=5000)
                time.sleep(1)  # Extra time for any animations

                # Take screenshot
                page.screenshot(path=output_path)
                print(f"Screenshot saved to {output_path}")
            except Exception as e:
                print(f"Error capturing screenshot: {e}")
                raise
            finally:
                browser.close()

    finally:
        # Stop server
        print("Stopping server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print("Server stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Capture a screenshot of the flowtoy webui for documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python capture_webui_screenshot.py docs/demo-flow.yaml \\
        docs/images/webui-screenshot.png --port 8080
        """,
    )
    parser.add_argument(
        "flow_file",
        help="Path to flow YAML file",
    )
    parser.add_argument(
        "output_path",
        help="Path to save screenshot PNG",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to run webui on (default: auto-select available port)",
    )

    args = parser.parse_args()

    capture_webui_screenshot(args.flow_file, args.output_path, args.port)
