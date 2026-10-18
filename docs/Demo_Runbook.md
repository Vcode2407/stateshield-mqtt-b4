# First-review live demonstration

Run from the repository root in PowerShell, with Docker Desktop running and the image already pulled:

```powershell
.\.venv\Scripts\python.exe .\demo.py
```

The script uses only `127.0.0.1:18883`. Allow it to finish both broker cases before discussing the result. It starts and stops its own fresh containers; it does not stop another container. The printed progress and final comparison are the live demonstration, and the two `evidence/demo_*.json` files are the machine-readable record. The run takes longer than a single publish because it waits for broker `$SYS` samples and offline delivery.

## What to say

1. **Before running:** "We first prove ordinary MQTT 5.0 delivery works. Then we disconnect three subscribers and publish five QoS 1 messages. A clean session is our benign control; a 120-second durable session is the state-retention case."
2. **At the baseline result:** "All three clean sessions recover zero. All three durable sessions report Session Present and recover five messages. This is expected protocol behavior, not an exploit."
3. **At the capped result:** "The only broker setting we changed is `max_queued_messages`, from 1000 to 3. Each durable subscriber now recovers three messages, while online delivery and clean-session behavior still pass. The two-message loss is the trade-off of a built-in limit."
4. **At the final line:** "Our research question is whether a state-aware policy can curb abusive offline buildup while avoiding this same loss for legitimate, temporarily disconnected devices. That policy is proposed, not implemented in this pilot."

## Evidence and questions

- Open `evidence/demo_baseline.json` and `evidence/demo_capped.json` to show exact received payload lists, `session_present_on_reconnect`, validation status, and the queue-cap setting. The Python argument records the cap; the actual broker setting is checked against each configuration file by `demo.py` before the run.
- `exact_payloads_received` asks whether **all five** published messages arrived. `false` is expected for the clean control (none arrive) and the capped durable case (three arrive); use `validation.pass` and the received-payload lists to judge whether each case met its own expectation.
- `$SYS/broker/store/messages/count` is a broker-level count, not per-client queue depth or the sum of deliveries. Its change supports the observation but does not prove memory pressure.
- `docker stats` values are point-in-time samples. They are not peak memory, CPU, performance improvement, or a security-impact result.
- Mosquitto's queue cap is an existing control, not our contribution. The pilot does not yet implement detection or prevention.
- If Docker is unavailable during review, show the previously saved JSON and slide deck, say plainly that this is recorded evidence, and do not call it a live run. The existing `evidence/baseline.json` and `evidence/capped.json` were produced on 18 October 2026.

The demonstration should take only the middle portion of the ten-minute review. Use the slides for the threat model, related research, candidate invariants, and next-step plan; keep the live output focused on the measured contrast.
