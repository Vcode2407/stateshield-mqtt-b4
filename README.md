# StateShield-MQTT: first-review pilot

Group B4: Vinay Kumar (AP26122050024), Triphal Sahu (AP26122050013), Venkatesh (AP26122050014). Faculty: Krishna Kumari. First review: 23 October 2026.

This is a small, isolated MQTT 5.0 experiment for the first project review. It shows normal delivery, clean-session behavior, durable-session queueing, and the delivery trade-off from Mosquitto's existing queue limit. It does **not** demonstrate a broker vulnerability or a new protection mechanism.

## Safety and scope

- Broker port is mapped to `127.0.0.1:18883` only. The broker configuration allows anonymous access solely for this isolated local lab.
- The script connects only to `127.0.0.1`, with at most 8 subscribers and 20 QoS 1 messages.
- Do not reuse these broker configurations on a public interface or production network.

## One-command live demonstration

Requirements: Python 3.12+, Docker Desktop running, and Docker image `eclipse-mosquitto:2.1.2-alpine`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
docker pull eclipse-mosquitto:2.1.2-alpine
.\.venv\Scripts\python.exe .\demo.py
```

`demo.py` starts a fresh localhost-only broker for each setting, runs normal delivery and both offline-session controls, checks the outcomes, prints a compact comparison, saves `evidence/demo_baseline.json` and `evidence/demo_capped.json`, and stops only the containers it created. The demonstration passes only when all three subscribers recover five messages with cap 1000 and three with cap 3. The saved JSON also records the actual payloads, Session Present flags, broker counters, and point-in-time Docker stats. See [the demo runbook](docs/Demo_Runbook.md) for a short speaking sequence and interpretation.

## Manual reproduction on Windows PowerShell

Use these commands to inspect or rerun one broker at a time after the setup above. The `--queue-cap` argument must match the broker configuration; it is not applied by the Python pilot.

```powershell
docker run --name stateshield-mqtt-baseline --rm -d -p 127.0.0.1:18883:1883 -v "${PWD}\mosquitto.baseline.conf:/mosquitto/config/mosquitto.conf:ro" eclipse-mosquitto:2.1.2-alpine
.\.venv\Scripts\python.exe .\mqtt_pilot.py --queue-cap 1000 --docker-container stateshield-mqtt-baseline --output .\evidence\baseline.json
docker stop stateshield-mqtt-baseline

docker run --name stateshield-mqtt-capped --rm -d -p 127.0.0.1:18883:1883 -v "${PWD}\mosquitto.capped.conf:/mosquitto/config/mosquitto.conf:ro" eclipse-mosquitto:2.1.2-alpine
.\.venv\Scripts\python.exe .\mqtt_pilot.py --queue-cap 3 --docker-container stateshield-mqtt-capped --output .\evidence\capped.json
docker stop stateshield-mqtt-capped
```

The original `evidence/baseline.json` and `evidence/capped.json` files are actual local runs from 18 October 2026; `demo_*.json` holds the later one-command run. `docker stats` is a point-in-time reading, not a peak CPU/memory measurement. `$SYS/broker/store/messages/count` includes Mosquitto's own stored messages; compare changes within a scenario, not the absolute total.

## Files

- `mqtt_pilot.py`: bounded experiment harness and assertions.
- `demo.py`: one-command, two-configuration live demonstration with cleanup.
- `mosquitto.baseline.conf`, `mosquitto.capped.conf`: the only changed setting is `max_queued_messages` (1000 versus 3).
- `evidence/baseline.json`, `evidence/capped.json`: unedited machine-readable run records.
- `evidence/demo_baseline.json`, `evidence/demo_capped.json`: validated records from the one-command live demonstration.
- `docs/First_Review_Brief.md`: project explanation and measured findings.
- `docs/StateShield-MQTT_B4_First_Review_Brief.pdf`: two-page review handout.
- `docs/Literature_Matrix.md`: starting-paper comparison and research boundary.
- `docs/Review_Talk_Track.md`: ten-minute speaking guide and likely questions.
- `docs/Full_Rehearsal_Script.md`: complete slide-by-slide script and suggested speaker split.
- `docs/Live_Capture_Checklist.md`: how to capture an unedited live terminal screenshot.
- `docs/Demo_Runbook.md`: 90-second live speaking sequence and backup procedure.
- `slides/output/StateShield-MQTT_B4_First_Review.pptx`: editable nine-slide review deck.

## Sources

[MQTT 5.0 specification](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html), [Mosquitto configuration manual](https://mosquitto.org/man/mosquitto-conf-5.html), [Mosquitto broker $SYS manual](https://mosquitto.org/man/mosquitto-8.html), [Paho Python client documentation](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html).
