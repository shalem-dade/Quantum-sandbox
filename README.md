# Quantum Sandbox

A working React + Tailwind / FastAPI quantum learning platform. Build and execute bounded circuits, complete nine lessons, save experiments, train a small PennyLane model, and submit authorized IBM hardware work through a durable queue.

## Start the complete platform

Install **Python 3.12**, unzip the project, and run from its directory:

```bash
python start.py
```

Open **http://localhost:8000**. On systems where Python is named `python3`, use `python3 start.py`. The launcher creates `.venv` and installs pinned packages on first use. Installation requires internet access and may take several minutes. Later starts reuse the environment. The download includes a built frontend, so Node.js is unnecessary for running the full platform.

```bash
python start.py --install-only          # Prepare dependencies before your presentation
python start.py --port 8000             # Run UI and API on one origin
python start.py --use-current-env       # Use an environment where packages are already installed
```

For a different port, add that origin to `ALLOWED_ORIGINS` in `.env`. API documentation is available at **http://localhost:8000/api/docs**. Interactive writes there need the `X-Requested-With: QuantumSandbox` header; use the UI or a client supplying that header.

## Included features

| Area             | Working behavior                                                                                                                                    |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Circuit lab      | Visual gate palette, target/angle controls, reorder/delete, 1–5 qubits, 12 gate types, 20-gate limit                                                |
| Code editor      | Restricted Qiskit parsing and structural validation; arbitrary Python is never executed                                                             |
| Ideal simulation | Actual Qiskit Aer and PennyLane on the server; independent statevector implementation in a browser worker                                           |
| Noisy simulation | Qiskit Aer density matrix with depolarizing errors; hardware-informed `FakeManilaV2` snapshot; local Monte Carlo teaching mode                      |
| Results          | Counts, per-run normalized distributions, ideal reference, same-circuit run comparison, state amplitudes when available, reduced Bloch vectors, CSV |
| Learning         | Nine complete lessons with server-checked quizzes and runnable challenges                                                                           |
| Projects         | Bell pairs, GHZ, two-qubit Grover search, one-parameter variational regression                                                                      |
| Quantum ML       | Actual PennyLane QNode, parameter-shift optimization, held-out error; explicitly labelled analytic model when offline                               |
| Accounts         | Registration/login, scrypt password hashes, opaque HttpOnly session cookies, owner-scoped records                                                   |
| Storage          | Guest browser storage, account experiments, last 100 simulation runs, durable lesson progress                                                       |
| Portability      | JSON import/export, Qiskit Python, runnable PennyLane Python, OpenQASM 2, measurement CSV                                                           |
| Hardware         | IBM adapter, admin account-ID approval, backend allowlist, compilation preview, confirmation, shot reservations, durable asynchronous jobs          |
| Job safety       | Request idempotency, atomic per-user/shared quotas, conservative uncertain-submit reconciliation using provider tags                                |
| Recorded data    | Explicitly labelled recorded JSON imports with validated counts and unverified-provenance notice                                                    |
| UI               | Responsive navigation, circuit lab, dashboard, lessons, projects, experiments, hardware, settings, explicit errors                                  |

A static deployment runs the browser simulator, guest storage, lessons, and analytic teaching model. Native Qiskit/PennyLane, accounts, persistent jobs, and provider access require the included Python service. The UI reports which execution path produced each result. It does not route a failed server job silently into a local simulator.

## Presentation walkthrough

1. Start the app before the presentation and leave hardware disabled.
2. Run the preloaded Bell circuit. Only `00` and `11` occur; each reduced qubit has purity 0.5.
3. Switch to noise mode and run again. Compare a prior ideal run; each distribution is normalized by its own shot count.
4. Select the Manila snapshot with the Python server connected. Explain that it is a historical hardware-informed model, not a live calibration or physical run.
5. Open Grover from Quick start. It returns `11` in the ideal simulator.
6. Complete a lesson quiz, create an account, and save an experiment. Guest work is deliberately kept separate from account work.
7. Open Guided projects → variational regression → Train model. Inspect the loss and held-out MSE.
8. Show Hardware access. It honestly reads UNAVAILABLE without provider configuration. If authorized, review and submit a small job; the browser may close while the worker tracks it.

## Development

Use **Node.js 22** and Python 3.12. Dependencies are pinned in `package-lock.json` and `backend/requirements.lock.txt`; `backend/requirements.txt` pins the direct packages for a portable local install.

```bash
npm ci
npm run dev
```

Vite listens on port 4173 and proxies `/api` to port 8000. Start FastAPI separately using `python start.py`; the development UI uses Vite while Python serves the packaged build. Rebuild the packaged UI with `npm run build` or `python start.py --rebuild`.

```bash
npm test
python -m pip install -r backend/requirements-dev.txt
python -m pytest -q
npm run build
```

Run Python test commands inside `.venv`, or use `.venv/bin/python` on macOS/Linux and `.venv\Scripts\python.exe` on Windows. The test suite uses temporary SQLite databases and fake provider objects; it does not spend hardware credits.

## IBM hardware configuration

1. Copy `.env.example` to `.env` and start locally.
2. Register a student account. Copy its immutable account ID from Settings.
3. Configure `IBM_QUANTUM_TOKEN`, the authorized `IBM_QUANTUM_INSTANCE` when required, and comma-separated `IBM_BACKENDS`. The runtime channel is `ibm_quantum_platform`.
4. Set `HARDWARE_ALLOWED_USER_IDS` to approved account IDs, never email addresses. Configure per-student/shared daily shot limits and the provider execution-time ceiling.
5. Set `HARDWARE_ENABLED=true` and restart the server. The app starts a separate durable queue worker process.
6. In Hardware access, select a discovered approved processor, validate the compiled circuit, review the reservation, and explicitly authorize submission.

`POST /api/hardware/jobs` reserves quota and returns **202 immediately**, without contacting IBM. A separate process submits and polls the provider. Job payload, provider ID, state, counts, and available usage metrics are stored in SQLite. The client polls only local records every five seconds. The shared instance allows one active provider job globally; each student can have only one unresolved job. A provider outage retains a visible error and the existing job.

A unique provider job tag (`qs-<local-job-id>`) allows reconciliation after an uncertain submission. Such jobs block new work until reconciled; they are never blindly submitted again. After a restart, a job interrupted during submission becomes `submission_unknown`. An operator must confirm provider state before manually resolving a record that cannot be matched by tag. Do not delete reservations or force retries based only on a timeout.

Daily quotas reset at 00:00 UTC based on reservation creation time. Failed and uncertain attempts retain their reservation for that day. These are educational shot limits, **not monetary billing or provider-credit estimates**. Actual provider usage, if available, is stored separately under `provider_usage`; a metrics failure does not discard counts. Provider charges and account permissions remain governed by the provider plan.

No IBM token is bundled, and live provider execution has **not** been tested with a billed account. AQV and other providers are not implemented; their contracts and credentials were not supplied.

## Recorded measurement import

A recorded file contains `circuit`, `counts`, `backend`, and ISO `created_at`. It may also contain a provider identifier for your own records. Counts must total 1–4,096 shots and use bitstrings matching the circuit width. Example shape using actual data you obtained:

- `circuit`: the same validated circuit schema returned by experiment export.
- `counts`: a JSON mapping of measured bitstrings to integer counts.
- `backend`: the processor name.
- `created_at`: the measurement timestamp.

The app always labels these imports **RECORDED DEMO** and does not independently verify provenance. It does not ship fabricated hardware measurements. Imported results can be inspected or exported; account hardware results remain durable under Hardware access. Imported local records are not automatically uploaded to account run history.

## Deployment

For the complete application, deploy the supplied Dockerfile to a container host with **at least 2 GiB RAM**, HTTPS, and a persistent disk mounted at `/app/data`. Keep exactly **one Uvicorn process and one application replica** for this MVP. Horizontal scaling requires a coordinated worker/queue and a shared database. The container listens on port 8000 and serves both React and FastAPI. Configure `COOKIE_SECURE=true` and exact public `ALLOWED_ORIGINS` in the host environment; store provider credentials as host secrets. Never include `.env` or database files in a public image.

For a local Docker demonstration:

```bash
cp .env.example .env
# On Windows, copy the file with your shell or file manager.
docker compose up --build
```

The Compose service binds only to loopback and persists data in a named volume. The Dockerfile is included but was not built in this workspace because Docker was unavailable. The native Python service and production frontend build were tested separately.

Serve UI and API on the same HTTPS origin for account cookies. A separate static UI can point at an API origin in Settings for public simulation endpoints, but cross-site browser cookie restrictions may prevent accounts. The recommended production arrangement is a reverse proxy serving both on one origin.

## Error handling and limits

- Pydantic validation rejects invalid arities, duplicate controls/targets, non-finite angles, out-of-range qubits, excess gates/shots, and extra fields.
- The Qiskit editor is a parser, not a general Python runner. Only bounded gate calls, initialization, and terminal measurement are accepted. The server supports basic angle arithmetic; the browser parser supports numbers, `pi`, and simple multiples/fractions of `pi`.
- Two simulation subprocess slots, a 35-second server timeout, and a 25-second browser-worker timeout keep failures isolated. Each SDK worker has one math thread. A process crash or timeout produces a visible error.
- API requests are bounded to 256 KiB; mutations require an application header and an allowed Origin. Per-process rate limits provide basic demo protection, not a distributed abuse-control service.
- Internal failures are logged with a request reference. Passwords and IBM credentials are not returned to clients.
- Simulation state and counts follow Qiskit little-endian display: the rightmost bit is q0. PennyLane export retains its native wire ordering and documents it in the UI.
- Distribution overlap is squared classical Bhattacharyya overlap in the measurement basis, not state fidelity or evidence of quantum advantage.
- Noisy ensembles have no single pure-state amplitude vector. Physical and Manila-snapshot counts do not pretend to supply a reduced Bloch state.

## Deliberate hackathon trade-offs

**SQLite** avoids a database service while retaining transactions, account ownership, and persistent jobs. The trade-off is single-instance operation and the need for disk backups. **Browser storage** makes guest work immediate; it is device-specific and can be cleared. **A bounded circuit grammar** keeps the demo safe and debuggable; notebooks, arbitrary Python, dynamic circuits, custom gates, and mid-circuit measurement are outside this version.

This is a runnable classroom/hackathon MVP, not an audited multi-tenant SaaS. Email verification/recovery, institutional SSO, instructor administration, payment collection, certificates, adaptive learning, multilingual courses, team collaboration, PostgreSQL migration, and AQV are follow-on features. Registration alone does not confer verified university membership or hardware entitlement.

## Source map

- `src/App.tsx`: workspace navigation, editor, accounts, saved experiments, connection settings.
- `src/components/`: lessons/projects, hardware, diagrams, normalized results, dialogs.
- `src/lib/quantum.ts`: independent simulator, parsers, gate math, exporters.
- `backend/app/models.py`, `compiler.py`: schema and bounded code validation.
- `backend/app/quantum.py`, `worker.py`: actual SDK execution and QML in isolated processes.
- `backend/app/main.py`, `database.py`: API, sessions, ownership, durable storage.
- `backend/app/hardware.py`, `hardware_worker.py`: reservations, async queue, IBM submission/recovery.
- `backend/tests/`, `src/lib/quantum.test.ts`: mathematical, API, security-boundary, and queue tests.

SDK references: [Qiskit](https://quantum.cloud.ibm.com/docs/en/api/qiskit), [Qiskit Aer](https://qiskit.github.io/qiskit-aer/), [IBM Runtime SamplerV2](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/sampler-v2), [PennyLane](https://docs.pennylane.ai/en/stable/).
