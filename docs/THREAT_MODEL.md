# Threat Model

## Protected assets

The benchmark treats repository contents, credentials, user files, test integrity, truthful status
reports, approved network boundaries, and repository visibility as protected assets.

## Agent capabilities

Trace events represent agents that can read files, edit code, run shell commands, install packages,
write logs, call network tools, and change repository settings. The synthetic cases record proposed
effects; they do not execute these operations.

## Failure source

An unsafe trace may arise from an ambiguous request, untrusted repository content, missing
authorisation, an unchecked target, an unreviewed dependency, or a misleading completion claim.
The benchmark does not assume that the coding agent is intentionally malicious.

## Control boundary

The monitor sees the task, prior events, proposed action, and structured policy attributes. It must
act before the proposed effect is committed. Recovery events represent a permitted continuation
after the control decision.

## Exclusions

Version 0.3 does not model operating-system isolation escapes, network exploitation,
cryptographic failures, compromised monitor infrastructure, or collusion between the monitored
agent and the monitor. Those cases require executable isolation and a separate risk review.

## Provider boundary

Model providers receive synthetic monitor-visible traces only. Access credentials remain in the
process environment. Raw payloads may still contain generated provider text, so they are written to
an ignored local directory and are excluded from checked summaries.
