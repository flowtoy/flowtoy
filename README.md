# flow - local flow runner prototype

Minimal prototype that implements a YAML-driven flow runner with a local runner and a small status API.

Install dependencies (recommend a venv):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run a flow:

```bash
python -m flow.flow.cli run config.yaml secrets.yaml
```

Serve status API and run flow once on startup:

```bash
python -m flow.flow.cli serve config.yaml secrets.yaml
```

The API exposes:
- GET /status
- GET /outputs
