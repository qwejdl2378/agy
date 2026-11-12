# Incident Report: EU Checkout Degradation (INC-2291)

**Status:** Resolved · **Severity:** SEV-2 · **Incident commander:** M. Okafor · **Report date:** 2026-11-10

## Summary
On 2026-11-06 between 09:12 and 09:59 UTC (47 minutes), customers in the EU region experienced failed or very slow checkouts. Approximately 12% of EU checkout attempts failed outright, and the p95 checkout latency rose from 1.1 s to 9.8 s. No data was lost and no duplicate charges were made. Customers in the US and APAC regions were not affected. An estimated 3,400 orders were not completed during the window; based on historical recovery rates we expect roughly 60% of those customers to have retried successfully within 24 hours.

## Timeline (UTC)
- 08:55 — A routine certificate rotation for the internal payments gateway was started by the platform team.
- 09:12 — The new intermediate certificate was missing from the trust bundle on 4 of 9 EU gateway nodes. Requests routed to those nodes began failing TLS handshakes with the payment processor.
- 09:19 — Automated alert "EU checkout error rate > 5%" fired. On-call engineer acknowledged at 09:21.
- 09:34 — On-call initially suspected the payment processor and opened a ticket with them. This cost about 15 minutes.
- 09:48 — The handshake errors were correlated with the certificate rotation via the deployment log.
- 09:52 — The affected nodes were drained from the load balancer.
- 09:59 — Error rate returned to baseline. Nodes were fixed and re-added at 10:40.

## Root cause
The rotation script copied the new leaf certificate but rebuilt the trust bundle only on nodes that had been restarted in the last 7 days. Five nodes had been restarted recently and received the full chain; four had not. The script reported success because it only verified that the leaf certificate file existed, not that a TLS handshake succeeded.

## What went well
- Alerting fired within 7 minutes of impact.
- Draining nodes was quick once the cause was known.

## What went poorly
- No pre-rotation canary: the change hit all nodes in one step.
- The runbook for checkout failures listed "contact the payment processor" as the first step, which sent on-call down the wrong path.
- Customer support learned about the incident from customers, 25 minutes after impact began.

## Action items
| # | Action | Owner | Due |
|---|--------|-------|-----|
| 1 | Rotation script must perform a real TLS handshake against the processor on every node before reporting success | Platform (J. Lindqvist) | 2026-11-20 |
| 2 | Roll certificate changes through a single canary node and wait 30 minutes before the rest | Platform (J. Lindqvist) | 2026-11-27 |
| 3 | Update the checkout runbook: check recent changes (deploy log) before contacting third parties | Payments on-call (A. Rossi) | 2026-11-14 |
| 4 | Auto-notify the support channel when any SEV-2+ alert fires | SRE (K. Tanaka) | 2026-12-04 |

## Customer impact & communication
Affected merchants will receive a service credit of 5% of their November EU transaction fees. A status-page post was published at 10:15 UTC; a detailed customer email has not yet been sent.
