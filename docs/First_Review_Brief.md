# StateShield-MQTT: first-review brief

**Group B4:** Vinay Kumar (AP26122050024), Triphal Sahu (AP26122050013), Venkatesh (AP26122050014)
**Faculty:** Krishna Kumari
**Project:** Faculty Project 2, MQTT Protocol Security
**Review:** 23 October 2026

## Problem and scope

An MQTT broker tracks more than individual packets. It also keeps subscriptions, client-session state, and sometimes QoS 1/2 messages for disconnected clients. That state lets a device reconnect after a short outage and recover messages. It can also consume broker resources when many clients stay offline while other clients publish to their topics. A packet-by-packet rule might approve every CONNECT, SUBSCRIBE, and PUBLISH, yet miss the state built by their sequence across clients.

The question for this project is narrower than "Is MQTT insecure?" We want to know when a multi-client interaction creates a meaningful resource or delivery problem, whether that outcome is permitted by MQTT 5.0 or reflects a broker defect, and whether a runtime policy can reduce the problem without blocking ordinary use. This first review tests one candidate interaction category: disconnected persistent subscribers and a separate publisher. We use one local broker, Eclipse Mosquitto 2.1.2, rather than claiming cross-broker results.

Our lab threat model gives a client control of its own MQTT 5.0 Client ID, Clean Start, Session Expiry Interval, subscription, and QoS 1 publishing. The broker runs with anonymous access only in a Docker container bound to localhost. These settings make the sequence easy to repeat; they are not a production security configuration. We cap the test at three subscribers and five small messages each. A benign control uses the same traffic with Session Expiry 0. A normal online publish/subscribe exchange runs first.

## Protocol sequence and expected state

```text
Subscriber A/B/C       Broker (Mosquitto)            Publisher
CONNECT MQTT 5   ----> create or resume session
SUBSCRIBE QoS 1  ----> retain topic subscription
DISCONNECT       ----> keep session for 120 s
                       <---- PUBLISH QoS 1, five times
                       queue messages for offline clients
CONNECT again   ----> Session Present = true
                       ----> deliver queued messages
```

With Session Expiry 0, the broker removes each session on disconnect. Reconnecting with the same Client ID therefore yields `Session Present = false` and no offline messages. With a 120-second expiry, the session legitimately survives and queued QoS 1 messages can be delivered. The [MQTT 5.0 standard](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html) allows this behavior. We classify the observed retention as **expected, configuration-dependent protocol behavior**, not a vulnerability or a non-compliance bug.

## Measured local result (18 October 2026)

Both runs used MQTT 5.0, three subscriber sessions, five QoS 1 publications, the same topic, and a fresh Mosquitto container. The first container allowed up to 1000 queued messages per client; the second allowed three. The JSON records in `../evidence/` contain timestamps, Client IDs' run prefix, `$SYS` broker counters, and point-in-time Docker stats.

| Scenario | Queue cap | Offline messages recovered per subscriber | Session Present | Broker store-message count before -> after |
| --- | ---: | ---: | --- | --- |
| Normal online delivery | 1000 and 3 | 1 of 1 | Not applicable | Not used as a queue test |
| Clean session, expiry 0 | 1000 | 0 of 5 | false for all 3 | 55 -> 55 |
| Durable session, expiry 120 s | 1000 | 5 of 5 | true for all 3 | 56 -> 61 |
| Clean session, expiry 0 | 3 | 0 of 5 | false for all 3 | 55 -> 55 |
| Durable session, expiry 120 s | 3 | 3 of 5 | true for all 3 | 56 -> 59 |

The `$SYS` store counter rose by five in the unrestricted durable run, although three subscribers each recovered five messages. This is a broker-level count, not the sum of per-client deliveries. With a cap of three, only three queued messages were recovered per client. The cap is an existing Mosquitto setting, so it is a **comparison control**, not our proposed invention. It also demonstrates a real cost: two messages per client were no longer available after reconnecting. We need a future policy that handles abusive accumulation without casually penalizing devices experiencing a legitimate outage.

Docker's point-in-time memory readings in the unrestricted durable run were 3.109 MiB before publishing and 2.855 MiB after. In the capped run they were 3.082 MiB and 2.863 MiB. These tiny, noisy samples do not establish a memory trend or a performance benefit. The present evidence proves session/delivery behavior; longer repeated measurements are needed for CPU, memory, latency, and false-intervention claims.

## Proposed research direction

The closest paper, MBFuzzer (USENIX Security 2025), already studies multi-party MQTT broker behavior and finds real defects. We should not claim that using multiple clients is novel. Our tentative contribution would be a **runtime, state-aware policy for persistent-session pressure**: combine session age, number of disconnected subscribers, queued-message growth, and per-client delivery history; then respond conservatively. Before writing a broker plugin, we will compare that policy with built-in queue limits and a passive monitor. The policy must distinguish normal temporary disconnections from suspicious accumulation and publish a measurable trade-off in message loss and overhead.

Three candidate invariants for discussion:

1. A disconnected session's queued-message count stays below an explicit broker budget. Signal: per-session queue depth, not merely total `$SYS` storage. Action: throttle or reject further offline queueing for that session. Risk: a real device may miss messages during an outage.
2. The sum of retained offline state stays within a global resource budget over time. Signal: disconnected-session count, memory, queued bytes, and age. Action: alert first, then expire or shed the oldest excess state under a tested policy. Risk: a large, legitimate fleet restart can look similar.
3. A client may not create repeatedly abandoned durable sessions faster than a specified rate. Signal: authenticated client identity and recent Client IDs. Action: rate-limit durable-session creation. Risk: shared credentials or device replacement may be mistaken for abuse.

These are **hypotheses**, not implemented protections. `$SYS` aggregates alone cannot enforce a per-client invariant. Broker hooks or a policy-aware front end would be needed for a genuine runtime intervention.

## Next experiment and limits

Repeat the test across controlled loads and several outage durations, using a benign reconnection workload as the false-intervention control. Record per-session queue depth where the broker exposes it, or instrument the broker. Measure peak CPU/memory and publish-to-delivery latency over multiple runs, then compare a passive monitor, built-in limits, and one implemented state-aware intervention. Check a second broker only after the Mosquitto result is reproducible. We have not performed that later work yet, and no publishable novelty claim is warranted at this stage.
