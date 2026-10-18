# Live terminal evidence capture

The saved JSON and slide table are real local results. A live Windows Terminal screenshot is still pending because the desktop automation environment blocked opening a terminal. Capture it during the group's local rehearsal; do not paste a recreated terminal image into the report.

1. In Windows Terminal, change to the `StateShield-MQTT` folder and start Docker Desktop if needed.
2. Run the baseline broker command from `README.md`.
3. Run `\.venv\Scripts\python.exe .\mqtt_pilot.py --queue-cap 1000 --docker-container statesheild-mqtt-baseline --output .\evidence\rehearsal.json`.
4. Keep the terminal visible after the program finishes. Capture the section showing `normal_delivery.pass: true`, the clean-session `0,0,0`, and durable-session `5,5,5` results. A second screenshot may be needed because the JSON is long.
5. Save the unedited Windows screenshot in `evidence/` with the run date in its filename. Confirm the screenshot and `rehearsal.json` agree, then stop the broker with `docker stop statesheild-mqtt-baseline`.

Do not claim the new screenshot exists until the group has run and checked it. The first-review deck already uses actual measured values from the prior saved runs, so the screenshot is supporting evidence rather than the only proof.
