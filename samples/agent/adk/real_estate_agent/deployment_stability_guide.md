# Deployment Stability & Reliability Guide

To prevent recurring issues like port conflicts, dependency mismatches, and authentication errors, follow these best practices for the A2UI project.

## 1. Environment Standardization
- **Python Version**: Always verify your local Python version (`python --version`) against the `requires-python` field in `pyproject.toml`.
- **Virtual Environments**: **Always** use a fresh virtual environment for each new agent setup to prevent library pollution.
  ```bash
  rm -rf .venv && python -m venv .venv && source .venv/bin/activate
  ```

## 2. Dependency Management
- **Editable Installs**: Since the `a2ui` extension is a local package, always install it and the agent in editable mode (`pip install -e .`) to ensure code changes are reflected immediately.
- **Check for Hidden Dependencies**: Tools like `click`, `uvicorn`, and `fastapi` are often required for the local server to run but might be missing from the core SDK dependencies. Verify the `dependencies` list in `pyproject.toml`.

## 3. Port & Process Hygiene
The most common cause of "page can't be found" errors is a stale process occupying the port.
- **The "Cleanup" Command**: Before starting a new session, run this to clear standard ports:
  ```bash
  lsof -t -i :10003 -i :5173 -i :5180 | xargs kill -9 || true
  ```
- **Direct Launch**: If using Vite through a shell, launch it directly (`npx vite dev --port XXXX`) rather than through `npm run dev` to ensure port arguments are actually passed to the server.

## 4. Authentication Check
- **GCP Token Lifespan**: Google Cloud credentials (ADC) expire periodically.
- **Pre-flight Check**: If the agent stops returning results but isn't crashing, check the logs for `RefreshError`.
- **Command**: `gcloud auth application-default login --project [PROJECT_ID]`

## 5. Automated "Fresh Start" Script
Consider creating a `setup.sh` in your agent directory:
```bash
#!/bin/bash
# Kill old processes
lsof -t -i :10003 -i :5180 | xargs kill -9 || true

# Refresh environment
source .venv/bin/activate
pip install -e ../../../a2a_agents/python/a2ui_extension
pip install -e .

# Start Backend (Background)
python __main__.py &

# Start Frontend
cd ../../../samples/client/lit/shell
npx vite dev --port 5180
```
