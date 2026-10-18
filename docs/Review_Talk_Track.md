# Ten-minute first-review talk track

**0:00-0:45, title and scope.** We chose faculty Project 2. Our first review uses one broker and one MQTT 5.0 interaction category. We have a working local pilot, not a completed defense.

**0:45-1:45, normal behavior.** MQTT brokers route publications to subscriptions. In MQTT 5.0 a device can ask the broker to keep its session after disconnect. This is useful when the network is unreliable.

**1:45-2:45, state sequence.** Three subscribers connect, subscribe, and disconnect with a 120-second expiry. A separate client publishes five QoS 1 messages. When the subscribers reconnect, the broker reports Session Present and delivers queued messages. The same sequence with expiry 0 leaves no session to resume.

**2:45-3:45, literature.** MBFuzzer is the closest paper and already demonstrates multi-party MQTT testing across six brokers. ProtocolGuard finds non-compliance. MQTT-I protects data-flow integrity with an untrusted broker. SIMMS is broader IoT gateway security. We cannot claim novelty from using two or more clients.

**3:45-5:30, actual run.** Show `evidence/baseline.json` and `evidence/capped.json`. Online delivery passed in both. Clean sessions recovered 0/5 messages. Durable sessions recovered 5/5 with the 1000-message cap and 3/5 with a cap of 3. The broker store counter changed 56 to 61 and 56 to 59 respectively. Explain that store count is not the sum of deliveries to three clients.

**5:30-6:15, classification.** This is permitted MQTT 5.0 behavior. The fixed queue limit is an existing broker control and can lose offline messages. We have not found a broker vulnerability.

**6:15-7:30, three candidate invariants.** Per-session queue budget; global retained-state budget over time; and rate of abandoned durable sessions by authenticated identity. Each needs finer state than aggregate `$SYS` metrics and each can affect legitimate devices.

**7:30-8:45, next implementation.** Instrument one broker or use broker hooks to observe per-session state, implement a conservative policy, and compare it with monitoring-only and native limits. Measure prevention, false interventions, delivery, peak CPU/memory, latency, and compatibility. Only then consider a second broker.

**8:45-10:00, limitations and questions.** One broker, tiny workload, one run per configuration, no attack claim, no tested intervention. Ask faculty whether persistent-session pressure is a suitable first interaction category before expanding.

## Questions worth rehearsing

**Is this already a solved problem?** Mosquitto has limits, as our comparison shows. Our research question is whether a state-aware runtime decision improves the delivery/resource trade-off. We have not shown that it does yet.

**Why is this a security project?** A legitimate protocol feature can become a resource-exhaustion avenue under adversarial client behavior, but the present small pilot only establishes mechanics. We must demonstrate impact and compare benign workloads before calling it abuse.

**What does the memory number prove?** Very little. `docker stats --no-stream` gave noisy point samples around 2.8-3.1 MiB. The first review should use them only to show the measurement path exists, not as evidence of an improvement.

**How do we enforce an invariant?** `$SYS` offers aggregates for observation. Enforcing per-client queue policy needs broker integration or a policy-aware proxy. That is planned, not done.
