# Literature matrix: starting papers for Project 2

This matrix distinguishes the closest MQTT broker work from wider IoT security work. The "boundary" column describes what the paper does **not appear to evaluate for our specific question** based on the linked publisher or author abstract and, for MBFuzzer, the USENIX paper. It is not a claim that the authors overlooked an obvious problem.

| Paper | Main question and method | Evidence reported by authors | Relation to our pilot / boundary |
| --- | --- | --- | --- |
| Song et al., [MBFuzzer: A Multi-Party Protocol Fuzzer for MQTT Brokers](https://www.usenix.org/conference/usenixsecurity25/presentation/song-xiangpu), USENIX Security 2025, pp. 6179-6197 | Black-box multi-party fuzzing with two input senders, a Petri-net model, scheduling, and differential non-compliance checks. | Six brokers; 73 bugs reported, including memory and non-compliance bugs, with 11 CVEs assigned. | **Closest work.** It establishes that multi-party broker testing is not new. Our possible angle is runtime handling of spec-permitted persistent-state pressure and its delivery cost, not another claim to have invented multi-client tests. We must verify that a proposed policy adds value beyond existing broker settings. |
| Song et al., [ProtocolGuard: Detecting Protocol Non-compliance Bugs via LLM-guided Static Analysis and Dynamic Verification](https://www.ndss-symposium.org/wp-content/uploads/2026-f521-paper.pdf), NDSS 2026, DOI 10.14722/ndss.2026.240521 | Combines LLM-guided static analysis with fuzzing-based dynamic verification to find protocol non-compliance. | Paper reports improved bug-finding precision and recall against comparison tools. | Relevant if a broker violates MQTT 5.0. Our present observed queueing is permitted behavior, so ProtocolGuard addresses a different classification. Do not call it a runtime queue defense. |
| Buccafurri, De Angelis and Lazzaro, [MQTT-I: Achieving End-to-End Data Flow Integrity in MQTT](https://iris.unirc.it/handle/20.500.12318/142287), IEEE TDSC 21(5), 2024, pp. 4717-4734, DOI 10.1109/TDSC.2024.3358630 | Protects publisher-to-subscriber data-flow integrity when the broker is untrusted; uses a Merkle-hash-tree-inspired protocol. | Theoretical and experimental overhead analysis reported by the authors. | Helpful contrast in MQTT threat modeling, but it studies message integrity rather than a broker's offline-session resource budget. |
| [SIMMS: Securing the IoT Through a Multi-Protocol Multi-Gateway System](https://xplorestaging.ieee.org/document/11480700/), IEEE TETC 2026, DOI 10.1109/TETC.2026.3681542 | Multi-protocol IoT gateway architecture combining authentication, role-based authorization, and encryption. | Publisher abstract describes evaluation of the gateway design. | Broader system architecture. Useful context for identity and access controls, but not direct evidence about MQTT 5.0 broker session retention. |

## Standards and implementation references

- [OASIS MQTT Version 5.0](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html): authority for Clean Start, Session Expiry Interval, subscription/session state, and QoS behavior.
- [Mosquitto configuration manual](https://mosquitto.org/man/mosquitto-conf-5.html): `max_queued_messages`, `sys_interval`, and session-related broker settings.
- [Mosquitto broker manual](https://mosquitto.org/man/mosquitto-8.html): meaning of the `$SYS/broker/...` counters used in this pilot.
- [Paho Python client documentation](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html): MQTT 5.0 client and callback usage.

## Research gap to verify

The current gap is a **question**, not a proven literature omission: can a session-aware runtime policy better balance broker state pressure and legitimate offline delivery than static queue limits? To answer it, the group must implement that policy, identify a defensible attacker/benign split, test false interventions, and compare against native Mosquitto controls. A single clean-versus-durable demonstration cannot establish novelty or security impact.
