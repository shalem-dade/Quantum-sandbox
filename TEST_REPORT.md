# Verification report

Verified in this workspace on 22 September 2026 with Python 3.12 and the locked dependencies.

- **Production frontend:** TypeScript compilation and Vite production build passed. The prebuilt `dist/` directory is included in the download.
- **Frontend tests:** 10 passed. Bell/GHZ/Grover outcomes, phase sign, bit order, unitary norm, noisy mixed states, deterministic seeds, safe parsing/export, execution limits, and all lesson challenge circuits.
- **Backend tests:** 37 passed. Native Qiskit and PennyLane, Aer density-matrix noise, the bundled Manila noise snapshot, parameter-shift learning, bounded parsing, schema limits, sessions, record ownership, quiz grading, request limits, real SDK subprocess execution, durable queues, quotas, idempotency, uncertain submission recovery, result provenance, and provider metrics failures.
- **Single-command startup:** `start.py --use-current-env` started Uvicorn, returned a successful API health response, and executed a Bell circuit through the real Qiskit subprocess over HTTP.
- **Error visibility:** malformed circuit requests return validation errors; authentication and ownership failures return explicit statuses; internal failures return a reference while the service stays responsive.

Hardware tests use mocked provider objects. No billed hardware execution was performed. Provider credentials and approved student/backend IDs are required for a live run.

The Python test stack emits two upstream deprecation warnings concerning the current Starlette/httpx testing adapter and AnyIO alias. They do not fail the tests; they are not hidden.

Browser visual testing was not completed because preview permission was denied earlier. Docker was not available, so the supplied container configuration was not built here. Private online publication is pending recovery of the earlier failed site registration. Native application startup, actual quantum SDK execution, and the frontend production build were checked independently of hosting.
