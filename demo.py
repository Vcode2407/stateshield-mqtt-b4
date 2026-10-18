"""Run the two isolated broker cases and show a concise review demonstration."""

import json
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PORT = 18883
IMAGE = "eclipse-mosquitto:2.1.2-alpine"
CASES = (("baseline", 1000), ("capped", 3))


def run(command, **kwargs):
    return subprocess.run(command, cwd=ROOT, check=True, text=True, **kwargs)


def configured_cap(path):
    settings = [
        line.split("#", 1)[0].split()
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    values = [int(parts[1]) for parts in settings if parts[:1] == ["max_queued_messages"] and len(parts) == 2]
    if len(values) != 1:
        raise ValueError(f"Expected one max_queued_messages setting in {path.name}")
    return values[0]


def wait_for_broker(container):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    logs = run(["docker", "logs", container], capture_output=True).stderr
    raise TimeoutError(f"Broker did not open localhost:{PORT}. Docker logs:\n{logs}")


def display(label, cap, result, output):
    clean, durable = result["cases"]
    before = durable["before_publish"]["store/messages/count"]
    after = durable["after_publish"]["store/messages/count"]
    counts = lambda case: " / ".join(str(value) for value in case["received_per_subscriber"])
    sessions = lambda case: " / ".join("Yes" if value else "No" for value in case["session_present_on_reconnect"])
    print(f"\n{label.upper()} | max_queued_messages={cap}")
    print(f"  Online publish/subscribe: {'PASS' if result['normal_delivery']['pass'] else 'FAIL'}")
    print("  Scenario                 Recovered (A/B/C)   Session Present (A/B/C)")
    print(f"  Clean, expiry 0 s        {counts(clean):<19} {sessions(clean)}")
    print(f"  Durable, expiry 120 s    {counts(durable):<19} {sessions(durable)}")
    print(f"  Broker store-message change:   {before} -> {after} (+{after - before})")
    print(f"  Validation: {'PASS' if result['validation']['pass'] else 'FAIL'}")
    print(f"  Raw evidence: {output.relative_to(ROOT)}")


def main():
    try:
        run(["docker", "version", "--format", "{{.Server.Version}}"], capture_output=True)
        run(["docker", "image", "inspect", IMAGE], capture_output=True)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", PORT))
        results = {}
        for label, cap in CASES:
            config = ROOT / f"mosquitto.{label}.conf"
            if configured_cap(config) != cap:
                raise ValueError(f"{config.name} does not declare queue cap {cap}")
            container = f"stateshield-demo-{label}-{uuid.uuid4().hex[:8]}"
            output = ROOT / "evidence" / f"demo_{label}.json"
            started = False
            try:
                print(f"\nStarting fresh {label} broker on 127.0.0.1:{PORT}...", flush=True)
                run([
                    "docker", "run", "--name", container, "--rm", "-d",
                    "-p", f"127.0.0.1:{PORT}:1883",
                    "-v", f"{config}:/mosquitto/config/mosquitto.conf:ro", IMAGE,
                ], capture_output=True)
                started = True
                wait_for_broker(container)
                run([
                    sys.executable, str(ROOT / "mqtt_pilot.py"),
                    "--port", str(PORT), "--clients", "3", "--messages", "5",
                    "--queue-cap", str(cap), "--docker-container", container,
                    "--output", str(output), "--quiet", "--progress",
                ])
                result = json.loads(output.read_text(encoding="utf-8"))
                display(label, cap, result, output)
                if not result["validation"]["pass"]:
                    raise RuntimeError(f"{label} pilot validation failed")
                results[label] = result
            finally:
                if started:
                    run(["docker", "stop", container], capture_output=True)

        baseline = results["baseline"]["cases"][1]["received_per_subscriber"]
        capped = results["capped"]["cases"][1]["received_per_subscriber"]
        if baseline != [5, 5, 5] or capped != [3, 3, 3]:
            raise RuntimeError("The two broker settings did not produce the expected contrast")
        print("\nCOMPARISON: Queue cap 3 retained two fewer messages per disconnected client.")
        print("INTERPRETATION: MQTT's intended session behavior; the cap is an existing Mosquitto control.")
        print("RESEARCH QUESTION: Can a state-aware policy limit abusive buildup with less legitimate delivery loss?")
        print("DEMONSTRATION PASS")
    except (OSError, ValueError, TimeoutError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"\nDEMONSTRATION FAILED: {exc}", file=sys.stderr)
        print("Check Docker Desktop, the image, port 18883, and evidence JSON if a pilot started.", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
