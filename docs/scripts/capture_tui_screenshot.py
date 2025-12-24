#!/usr/bin/env python
"""
Capture a screenshot of the flowtoy TUI for documentation.

Requirements:
    pip install textual

Usage:
    python capture_tui_screenshot.py flow.yaml output.svg

Example:
    python capture_tui_screenshot.py docs/how-to-files/monitor-flow.yaml \
        docs/images/tui-screenshot.svg

This script uses Textual's Pilot API to programmatically control and screenshot the TUI.
"""

import argparse
import asyncio
import socket
import subprocess
import time


def find_available_port():
    """Find an available port by binding to port 0."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


async def capture_screenshot_with_pilot(status_url, output_path, wait_time=3.0):
    """Capture a screenshot using Textual's Pilot for programmatic control.

    Pilot provides programmatic control of Textual apps, allowing us to:
    - Wait for the app to reach a desired state
    - Trigger screenshot capture
    - Exit cleanly

    Args:
        status_url: URL of the status endpoint to monitor
        output_path: Path to save the SVG screenshot
        wait_time: Seconds to wait before capturing (to let flow make progress)
    """
    import shutil
    import tempfile
    from pathlib import Path

    from flowtoy.tui import FlowToyTUI

    # Create the TUI app
    app = FlowToyTUI(status_url=status_url, poll_interval=1.0)

    # Use pilot to control the app
    async with app.run_test() as pilot:
        # Wait for initial data and flow progress
        await pilot.pause(wait_time)

        # save_screenshot expects a directory, so use temp dir
        with tempfile.TemporaryDirectory() as tmpdir:
            # Take screenshot to temp directory
            app.save_screenshot(path=tmpdir)

            # Find the generated SVG file
            svg_files = list(Path(tmpdir).glob("*.svg"))
            if not svg_files:
                raise RuntimeError("No screenshot was generated")

            # Move to desired location
            shutil.move(str(svg_files[0]), output_path)
            print(f"Screenshot saved to {output_path}")

    # Pilot's context manager handles cleanup


def capture_tui_screenshot(flow_file, output_path, wait_time=5.0):
    """Start flow with status server, capture TUI screenshot, cleanup.

    Args:
        flow_file: Path to flow YAML file
        output_path: Path to save screenshot SVG
        wait_time: Seconds to wait for flow to make progress before capturing
    """
    port = find_available_port()
    print(f"Starting flow with status server on port {port}...")

    # Start flow with status server
    flow_process = subprocess.Popen(
        ["python", "-m", "flowtoy", "run", flow_file, "--status-port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Give server time to start
    time.sleep(2)

    if flow_process.poll() is not None:
        output, _ = flow_process.communicate()
        print(f"Flow failed to start:\n{output}")
        raise RuntimeError("Flow failed to start")

    try:
        # Capture screenshot using Pilot
        status_url = f"http://127.0.0.1:{port}/status"
        print(f"Capturing TUI screenshot from {status_url}...")

        # Run the async screenshot capture
        asyncio.run(capture_screenshot_with_pilot(status_url, output_path, wait_time))

    finally:
        # Stop flow
        print("Stopping flow...")
        flow_process.terminate()
        try:
            flow_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            flow_process.kill()
            flow_process.wait()
        print("Flow stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Capture a screenshot of the flowtoy TUI for documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python capture_tui_screenshot.py docs/how-to-files/monitor-flow.yaml \\
        docs/images/tui-screenshot.svg --wait-time 3.0
        """,
    )
    parser.add_argument(
        "flow_file",
        help="Path to flow YAML file",
    )
    parser.add_argument(
        "output_path",
        help="Path to save screenshot SVG",
    )
    parser.add_argument(
        "--wait-time",
        type=float,
        default=5.0,
        help="Seconds to wait before capturing screenshot (default: 5.0)",
    )

    args = parser.parse_args()

    capture_tui_screenshot(args.flow_file, args.output_path, args.wait_time)
