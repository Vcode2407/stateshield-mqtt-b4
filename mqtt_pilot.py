"""Bounded, localhost-only MQTT 5 pilot for the first project review."""

import argparse
import json
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Lock

import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes


HOST = "127.0.0.1"
TOPIC = "stateshield/pilot/messages"
SYS_KEYS = (
    "$SYS/broker/clients/connected",
    "$SYS/broker/clients/disconnected",
    "$SYS/broker/clients/total",
    "$SYS/broker/store/messages/count",
    "$SYS/broker/subscriptions/count",
)


def connect_properties(expiry):
    properties = Properties(PacketTypes.CONNECT)
    properties.SessionExpiryInterval = expiry
    return properties


class Peer:
    def __init__(self, client_id, port, expiry, clean_start, subscribe=None, watch_sys=False):
        self.messages = []
        self.metrics = {}
        self.lock = Lock()
        self.connected = Event()
        self.subscribed = Event()
        self.session_present = None
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            protocol=mqtt.MQTTv5,
        )
        self.client.on_connect = self._on_connect
        self.client.on_subscribe = self._on_subscribe
        self.client.on_message = self._on_message
        self.subscribe = subscribe
        self.watch_sys = watch_sys
        self.client.connect(HOST, port, clean_start=clean_start, properties=connect_properties(expiry))
        self.client.loop_start()
        if not self.connected.wait(5):
            self.close()
            raise TimeoutError(f"{client_id}: MQTT connection timed out")
        if subscribe and not self.subscribed.wait(5):
            self.close()
            raise TimeoutError(f"{client_id}: subscription timed out")

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            return
        self.session_present = flags.session_present
        self.connected.set()
        if self.subscribe:
            client.subscribe(self.subscribe, qos=1)
        if self.watch_sys:
            client.subscribe("$SYS/broker/#", qos=0)

    def _on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        if all(not code.is_failure for code in reason_code_list):
            self.subscribed.set()

    def _on_message(self, client, userdata, message):
        value = message.payload.decode("utf-8", errors="replace")
        with self.lock:
            if message.topic.startswith("$SYS/"):
                if message.topic in SYS_KEYS:
                    try:
                        self.metrics[message.topic] = int(value)
                    except ValueError:
                        pass
            else:
                self.messages.append(value)

    def snapshot(self):
        with self.lock:
            return {key.removeprefix("$SYS/broker/"): self.metrics.get(key) for key in SYS_KEYS}

    def received(self):
        with self.lock:
            return list(self.messages)

    def close(self):
        self.client.disconnect()
        self.client.loop_stop()


def wait_for_messages(peer, expected, seconds=4):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if len(peer.received()) >= expected:
            break
        time.sleep(0.05)
    return peer.received()


def measure(monitor):
    # $SYS values are published at the configured broker sys_interval.
    time.sleep(1.4)
    return monitor.snapshot()


def docker_stats(container):
    if not container:
        return None
    command = ["docker", "stats", "--no-stream", "--format", "{{json .}}", container]
    completed = subprocess.run(command, capture_output=True, text=True, check=True, timeout=15)
    return json.loads(completed.stdout)


def run_case(label, run_id, port, count, messages, expiry, monitor, container):
    ids = [f"ss-{run_id}-{label}-{index}" for index in range(count)]
    expected = [f"{run_id}-{label}-{index}" for index in range(messages)]
    subscribers = []
    try:
        for client_id in ids:
            subscribers.append(Peer(client_id, port, expiry, True, subscribe=TOPIC))
        for peer in subscribers:
            peer.close()
        subscribers.clear()
        before = measure(monitor)
        resources_before = docker_stats(container)
        publisher = Peer(f"ss-{run_id}-{label}-publisher", port, 0, True)
        try:
            for payload in expected:
                info = publisher.client.publish(TOPIC, payload, qos=1)
                info.wait_for_publish(timeout=5)
                if not info.is_published():
                    raise TimeoutError(f"Publish failed: {payload}")
        finally:
            publisher.close()
        after = measure(monitor)
        resources_after = docker_stats(container)
        recovered = []
        session_present = []
        for client_id in ids:
            peer = Peer(client_id, port, 0, False)
            subscribers.append(peer)
            session_present.append(bool(peer.session_present))
            recovered.append(wait_for_messages(peer, messages))
        return {
            "scenario": label,
            "session_expiry_seconds": expiry,
            "subscriber_count": count,
            "published_per_subscriber": messages,
            "before_publish": before,
            "after_publish": after,
            "container_stats_before": resources_before,
            "container_stats_after": resources_after,
            "session_present_on_reconnect": session_present,
            "received_per_subscriber": [len(items) for items in recovered],
            "received_payloads_per_subscriber": recovered,
            "exact_payloads_received": [items == expected for items in recovered],
        }
    finally:
        for peer in subscribers:
            peer.close()


def validation_errors(result):
    errors = []
    if not result["normal_delivery"]["pass"]:
        errors.append("Online publish/subscribe delivery failed")
    clean, durable = result["cases"]
    clients = clean["subscriber_count"]
    messages = clean["published_per_subscriber"]
    expected_durable = min(messages, result["queue_cap_configured"])
    if clean["session_present_on_reconnect"] != [False] * clients:
        errors.append("Clean sessions unexpectedly survived reconnect")
    if clean["received_per_subscriber"] != [0] * clients:
        errors.append("Clean sessions received offline messages")
    if durable["session_present_on_reconnect"] != [True] * clients:
        errors.append("Durable sessions did not survive reconnect")
    if durable["received_per_subscriber"] != [expected_durable] * clients:
        errors.append("Durable delivery did not match the configured per-client queue cap")
    expected_payloads = [
        f"{result['run_id']}-durable-{index}" for index in range(messages)
    ]
    for index, received in enumerate(durable["received_payloads_per_subscriber"]):
        if received != [payload for payload in expected_payloads if payload in received]:
            errors.append(f"Subscriber {index} received unexpected, repeated, or reordered payloads")
    if expected_durable == messages and not all(durable["exact_payloads_received"]):
        errors.append("Uncapped durable delivery did not match the published payloads")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18883)
    parser.add_argument("--clients", type=int, default=3)
    parser.add_argument("--messages", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("evidence/pilot.json"))
    parser.add_argument("--queue-cap", type=int, default=1000)
    parser.add_argument("--docker-container", help="Local Docker container name for point-in-time stats")
    parser.add_argument("--quiet", action="store_true", help="Save JSON without printing it")
    parser.add_argument("--progress", action="store_true", help="Show concise stage updates")
    args = parser.parse_args()
    if not 1 <= args.clients <= 8 or not 1 <= args.messages <= 20:
        parser.error("Limit the local pilot to 1-8 clients and 1-20 messages")
    if not 1 <= args.queue_cap <= 1000:
        parser.error("--queue-cap must be between 1 and 1000")

    run_id = uuid.uuid4().hex[:8]
    monitor = Peer(f"ss-{run_id}-monitor", args.port, 0, True, watch_sys=True)
    try:
        initial = measure(monitor)
        initial_resources = docker_stats(args.docker_container)
        # Normal online delivery is checked before offline-session experiments.
        online = Peer(f"ss-{run_id}-online", args.port, 0, True, subscribe=TOPIC)
        publisher = Peer(f"ss-{run_id}-normal-publisher", args.port, 0, True)
        try:
            payload = f"{run_id}-normal-delivery"
            info = publisher.client.publish(TOPIC, payload, qos=1)
            info.wait_for_publish(timeout=5)
            normal_received = wait_for_messages(online, 1)
        finally:
            publisher.close()
            online.close()
        if args.progress:
            print("  1/3 Online delivery checked", flush=True)
        clean = run_case("clean", run_id, args.port, args.clients, args.messages, 0, monitor, args.docker_container)
        if args.progress:
            print("  2/3 Clean-session control checked", flush=True)
        durable = run_case("durable", run_id, args.port, args.clients, args.messages, 120, monitor, args.docker_container)
        if args.progress:
            print("  3/3 Durable offline session checked", flush=True)
        result = {
            "run_utc": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "broker": f"{HOST}:{args.port}",
            "protocol": "MQTT 5.0",
            "queue_cap_configured": args.queue_cap,
            "initial_broker_metrics": initial,
            "initial_container_stats": initial_resources,
            "normal_delivery": {"published": payload, "received": normal_received, "pass": normal_received == [payload]},
            "cases": [clean, durable],
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        errors = validation_errors(result)
        result["validation"] = {"pass": not errors, "errors": errors}
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        if not args.quiet:
            print(json.dumps(result, indent=2))
        if errors:
            raise SystemExit("Pilot validation failed: " + "; ".join(errors))
    finally:
        monitor.close()


if __name__ == "__main__":
    main()
