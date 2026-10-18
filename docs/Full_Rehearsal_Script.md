# First-review rehearsal script

**Target:** 9 minutes 30 seconds speaking, leaving about 30 seconds for slide changes. The three speaker assignments below are suggestions; the group should agree on them before presenting. Read this aloud once with a timer and trim where needed. Do not describe the pilot as an attack or vulnerability.

## Slide 1 - Title (0:00-0:40, suggested speaker: Vinay)

Good morning. We are Group B4, and our project is StateShield-MQTT, under the faculty's second project topic on MQTT protocol security. I'm Vinay; our other members are Triphal and Venkatesh. For this first review, we are looking at one narrow part of broker behavior: what happens when several subscribers disconnect but ask the broker to preserve their MQTT 5.0 sessions. We have a small working local experiment and a research question. We have not built a new defense or found a broker vulnerability at this stage.

## Slide 2 - Why the state matters (0:40-1:40, suggested speaker: Vinay)

MQTT is useful for devices with unstable connections. A subscriber can go offline and later reconnect without losing its subscription. For quality-of-service level one messages, the broker can keep messages while that subscriber is away. This is a normal, valuable feature. The concern we want to investigate is that the broker's work is not explained by one packet alone. One client creates a durable session, another publishes, and the broker retains state until the first client returns or its session expires. With many such interactions, the cost might grow. But we are not assuming every large queue is malicious. An outage affecting real devices can produce a similar picture. Our project must distinguish the two and measure the cost of any intervention.

## Slide 3 - Sequence (1:40-2:40, suggested speaker: Vinay)

Here is the exact sequence in our first test. Three subscribers connect to the same local Mosquitto broker and subscribe to one topic at QoS 1. We disconnect all three. In the durable case, each session asks to survive for 120 seconds. A fourth client publishes five small messages to the topic. Then the subscribers reconnect with the same Client IDs. If their sessions still exist, the broker reports Session Present and delivers the waiting messages. We repeat the pattern with Session Expiry set to zero, which is our clean-session control. That control tells us whether the messages arrive because of retained session state, rather than because the script happened to subscribe again.

## Slide 4 - Related work (2:40-3:55, suggested speaker: Triphal)

The closest paper is MBFuzzer from USENIX Security 2025. It already uses a multi-party MQTT test model, evaluates six brokers, and reports 73 bugs. So simply using several clients is not our contribution. ProtocolGuard, published at NDSS 2026, looks for protocol non-compliance with static and dynamic analysis. That would matter if our broker violated the MQTT rules, but our current observation appears to be allowed by the standard. MQTT-I studies end-to-end data integrity when the broker is not trusted. SIMMS looks at security across a wider IoT gateway architecture. Those papers help us locate the problem, but they do not by themselves answer whether a runtime policy can handle legitimate, resource-intensive session retention better than existing broker settings. We still have to test whether that question is useful.

## Slide 5 - Local pilot (3:55-4:55, suggested speaker: Triphal)

Our setup is deliberately small and isolated. We used Mosquitto 2.1.2 in Docker, with the port bound only to 127.0.0.1. The clients use Python 3.12 and Paho's MQTT 5.0 API. The script limits itself to three subscribers and five QoS 1 publications in the saved runs. It starts with an ordinary online publish-and-subscribe check. Then it runs clean and durable sessions. We also compare two broker configurations. One allows up to 1000 queued messages per client, and the other allows three. That queue setting is already provided by Mosquitto. The script writes the received message counts, Session Present flags, selected broker counters, and point-in-time Docker statistics to JSON so the same experiment can be checked again.

## Slide 6 - Results (4:55-6:20, suggested speaker: Triphal)

The online message arrived correctly in both configurations. For the clean control, all three clients recovered zero of the five offline publications, and the broker said no previous session was present. For durable sessions with the larger queue cap, all three clients recovered all five messages, and each reconnect reported a present session. With the cap of three, each recovered only three. The broker's store-message counter rose from 56 to 61 in the larger-cap run and from 56 to 59 with the smaller cap. That counter is broker-level storage; it is not supposed to equal five messages times three subscribers. The main result is the delivery trade-off: the native limit bounds what the broker retains, but it can also remove messages a legitimate offline device would have received. We classify this as expected MQTT behavior controlled by configuration. It is not evidence that Mosquitto is non-compliant.

## Slide 7 - Candidate invariants (6:20-7:35, suggested speaker: Venkatesh)

We have three candidate rules to study, not three implemented defenses. First, a per-session budget would cap the number or bytes of messages held for one disconnected client. This is simple, but a genuine outage could lose data. Second, a global retained-state budget could consider how many sessions are offline, how old they are, and how much memory and queue space they consume together. A large fleet reconnecting after a power failure might trigger that rule even though the clients are legitimate. Third, a rate limit on creating and abandoning durable sessions could help when one authenticated identity repeatedly leaves state behind. But shared credentials or device replacement could create false alarms. These risks are why we need a benign comparison workload before choosing an intervention.

## Slide 8 - What we do not know (7:35-8:25, suggested speaker: Venkatesh)

This is one broker, a tiny workload, and one final run per configuration. We sampled Docker memory around three mebibytes, but those readings move up and down even in this small test. They are not peak measurements and do not prove a performance gain. We have not measured latency, false interventions, or behavior under repeated load. We have not built a policy inside the broker, and we have not tested a second broker. We are making those limits explicit so the first review can guide the scope rather than making an early claim that the pilot does not support.

## Slide 9 - Proposed next study (8:25-9:30, suggested speaker: Venkatesh)

If this is a suitable interaction category, the next step is to obtain per-client queue state through broker instrumentation or hooks. We would implement one conservative policy and compare three conditions: monitoring only, Mosquitto's fixed queue limit, and our state-aware intervention. We would repeat tests under both controlled accumulation and benign disconnections. The outcomes would include state reduction, legitimate delivery, false interventions, peak CPU and memory, and publish-to-delivery latency. We would try a second broker only after the first-broker study is repeatable. Our question for the faculty is whether persistent-session pressure is the right first category for this project, or whether we should choose a more direct multi-client semantic case.

## Before presenting

- Each member confirms their speaking part and individual CLA-3 topic separately.
- Open the raw `evidence/baseline.json` and `evidence/capped.json` if asked for proof. Do not read the entire JSON on screen.
- Time one group rehearsal. If it exceeds ten minutes, cut repeated wording from slides 2, 4, and 7 before cutting the measured results or limitations.
- Record faculty questions and decisions after the 23 October review. No feedback can be written in advance.
