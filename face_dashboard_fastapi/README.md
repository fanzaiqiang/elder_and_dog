# Face Dashboard FastAPI Backend

## Run

```bash
cd /home/jetson/elder_and_dog/face_dashboard_fastapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /api/status`
- `GET /api/stream/health`
- `POST /api/enroll/start`
- `POST /api/enroll/stop`
- `POST /api/infer/start`
- `POST /api/infer/stop`
