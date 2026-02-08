# Phase 3C Release Notes

## Summary
- Enforced durability gates for tool parity, schema contracts, and benchmark budgets
- Two-lane benchmark model (deterministic PR gate + real nightly observability)
- Structured durability events with reducer summary output

## Enforced Gates
- Tool parity check (blocking)
- Schema contract check (blocking)
- Benchmark budget gate (blocking, deterministic)

## Job Lanes
- Blocking: PR/push durability gates (deterministic benchmark + budget check)
- Non-blocking: nightly/manual real benchmark (observability only)

## Observability
- Event schema version: v1
- Events emitted per gate run (NDJSON under artifacts/events)
- Summary reducer output: artifacts/latest/observability-summary.json
