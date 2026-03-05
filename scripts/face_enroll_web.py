#!/usr/bin/env python3
import argparse
import re
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Any, Deque, Optional

try:
    from flask import Flask, Response, jsonify, request
except ImportError as exc:
    raise SystemExit(
        "Flask not installed. Install with: sudo apt install -y python3-flask"
    ) from exc


class ProcState:
    def __init__(self, name: str):
        self.name = name
        self.proc: Optional[subprocess.Popen[str]] = None
        self.logs: Deque[str] = deque(maxlen=300)
        self.saved = 0
        self.total = 0
        self.lock = threading.Lock()

    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def pid(self) -> Optional[int]:
        proc = self.proc
        if proc is not None and proc.poll() is None:
            return proc.pid
        return None


app = Flask(__name__)
ENROLL = ProcState("enroll")
INFER = ProcState("infer")
CONFIG = {
    "db_dir": "/home/jetson/face_db",
    "enroll_script": "/home/jetson/elder_and_dog/scripts/face_identity_enroll_cv.py",
    "infer_script": "/home/jetson/elder_and_dog/scripts/face_identity_infer_cv.py",
}


def _spawn_reader(state: ProcState):
    progress_re = re.compile(r"\((\d+)/(\d+)\)")
    if state.proc is None or state.proc.stdout is None:
        return
    for line in state.proc.stdout:
        text = line.rstrip("\n")
        with state.lock:
            state.logs.append(text)
            m = progress_re.search(text)
            if m:
                state.saved = int(m.group(1))
                state.total = int(m.group(2))
    state.proc.wait()


def _start_process(state: ProcState, cmd: list[str]) -> int:
    state.proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    t = threading.Thread(target=_spawn_reader, args=(state,), daemon=True)
    t.start()
    return state.proc.pid


def _list_people(db_dir: Path):
    if not db_dir.exists():
        return []
    result = []
    for person_dir in sorted(db_dir.iterdir()):
        if not person_dir.is_dir():
            continue
        count = len(list(person_dir.glob("*.png")))
        result.append({"name": person_dir.name, "samples": count})
    return result


def _guidance(saved: int, total: int) -> str:
    if total <= 0:
        return "Enter name, sample count, and interval, then press Start Scan."
    ratio = saved / total
    if ratio < 0.25:
        return "Keep your face centered, look straight, and stay at medium distance."
    if ratio < 0.5:
        return "Slightly turn left and right to capture profile variation."
    if ratio < 0.75:
        return "Move closer and farther a bit to add distance diversity."
    if ratio < 1.0:
        return "Great. Hold steady for final captures and avoid motion blur."
    return "Scan complete. You can add another person or start recognition demo."


@app.get("/")
def index():
    html = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Face Enrollment Studio</title>
  <style>
    :root {
      --bg: #f4f6f8;
      --card: #ffffff;
      --text: #101318;
      --muted: #5b6574;
      --accent: #1f7aec;
      --accent-soft: #e8f1ff;
      --ok: #1f9d55;
      --warn: #e28700;
      --danger: #cb2f2f;
      --border: #dde3ea;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: radial-gradient(circle at 20% 0%, #ffffff 0%, var(--bg) 55%); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    .wrap { max-width: 1320px; margin: 0 auto; padding: 20px; }
    .top { display: flex; gap: 16px; flex-wrap: wrap; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 16px; box-shadow: 0 6px 18px rgba(10,20,40,0.05); }
    .controls { flex: 1 1 340px; }
    .progress-card { flex: 1 1 340px; }
    .people { flex: 1 1 280px; }
    h1 { margin: 0 0 4px; font-size: 24px; letter-spacing: -0.02em; }
    .sub { color: var(--muted); margin-bottom: 12px; }
    label { font-size: 13px; color: var(--muted); display: block; margin-bottom: 6px; }
    input { width: 100%; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--border); margin-bottom: 10px; }
    .row3 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
    button { border: 0; border-radius: 10px; padding: 10px 14px; cursor: pointer; font-weight: 600; }
    .primary { background: var(--accent); color: #fff; }
    .ghost { background: var(--accent-soft); color: var(--accent); }
    .danger { background: #ffe9e9; color: var(--danger); }
    .status { margin-top: 10px; font-size: 13px; color: var(--muted); }
    .bar { width: 100%; height: 12px; border-radius: 999px; background: #e9edf2; overflow: hidden; margin-top: 10px; }
    .bar > div { height: 100%; width: 0%; background: linear-gradient(90deg, #4aa0ff, #1f7aec); transition: width 0.2s ease; }
    .guide { margin-top: 8px; padding: 10px; border-radius: 10px; background: #f7fafc; color: #3c4656; font-size: 13px; }
    .grid { margin-top: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .panel-title { font-weight: 700; margin-bottom: 10px; }
    .preview { width: 100%; border: 1px solid var(--border); border-radius: 14px; background: #000; aspect-ratio: 16 / 9; object-fit: contain; }
    pre { margin: 0; height: 220px; overflow: auto; background: #0e1220; color: #74ff8e; border-radius: 12px; padding: 12px; font-size: 12px; }
    .pill { display: inline-block; padding: 5px 10px; border-radius: 999px; background: #edf2f7; color: #3c4656; font-size: 12px; margin-right: 6px; margin-bottom: 6px; }
    .ok { color: var(--ok); }
    .warn { color: var(--warn); }
    @media (max-width: 1100px) {
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Face Enrollment Studio</h1>
    <div class="sub">Interactive multi-person capture with real-time guidance, progress, and recognition demo.</div>

    <div class="top">
      <div class="card controls">
        <div class="panel-title">Scan Setup</div>
        <label>Person Name</label>
        <input id="person" value="alice" placeholder="alice" />
        <div class="row3">
          <div>
            <label>Samples</label>
            <input id="samples" type="number" value="30" min="1" max="500" />
          </div>
          <div>
            <label>Interval (sec)</label>
            <input id="interval" type="number" step="0.05" value="0.35" />
          </div>
        </div>
        <div class="actions">
          <button id="startEnrollBtn" class="primary" onclick="startEnroll()">Start Scan</button>
          <button id="stopEnrollBtn" class="danger" onclick="stopEnroll()">Stop Scan</button>
          <button id="startInferBtn" class="ghost" onclick="startInfer()">Start Recognition Demo</button>
          <button id="stopInferBtn" class="danger" onclick="stopInfer()">Stop Demo</button>
        </div>
        <div class="status" id="status">idle</div>
      </div>

      <div class="card progress-card">
        <div class="panel-title">Capture Progress</div>
        <div id="progressText">0 / 0</div>
        <div class="bar"><div id="bar"></div></div>
        <div class="guide" id="guide">Enter setup and press Start Scan.</div>
      </div>

      <div class="card people">
        <div class="panel-title">Registered People</div>
        <div id="peopleList"></div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <div class="panel-title">Enrollment Preview</div>
        <img id="enrollPreview" class="preview" src="__ENROLL_SRC__" />
      </div>
      <div class="card">
        <div class="panel-title">Recognition Demo Preview</div>
        <img id="inferPreview" class="preview" src="__INFER_SRC__" />
      </div>
      <div class="card">
        <div class="panel-title">Enrollment Logs</div>
        <pre id="enrollLogs"></pre>
      </div>
      <div class="card">
        <div class="panel-title">Recognition Logs</div>
        <pre id="inferLogs"></pre>
      </div>
    </div>
  </div>

<script>
function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function httpGetJson(url, cb) {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', url, true);
  xhr.onreadystatechange = function () {
    if (xhr.readyState !== 4) return;
    if (xhr.status < 200 || xhr.status >= 300) {
      cb(new Error('GET ' + url + ' failed: ' + xhr.status));
      return;
    }
    try {
      cb(null, JSON.parse(xhr.responseText));
    } catch (e) {
      cb(e);
    }
  };
  xhr.onerror = function () { cb(new Error('network error')); };
  xhr.send();
}

function httpPostJson(url, body, cb) {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', url, true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.onreadystatechange = function () {
    if (xhr.readyState !== 4) return;
    var data = {};
    try { data = JSON.parse(xhr.responseText || '{}'); } catch (e) {}
    if (xhr.status < 200 || xhr.status >= 300) {
      cb(new Error(data.error || ('POST ' + url + ' failed: ' + xhr.status)), data);
      return;
    }
    cb(null, data);
  };
  xhr.onerror = function () { cb(new Error('network error'), {}); };
  xhr.send(JSON.stringify(body || {}));
}

function httpPost(url, cb) {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', url, true);
  xhr.onreadystatechange = function () {
    if (xhr.readyState !== 4) return;
    if (xhr.status < 200 || xhr.status >= 300) {
      cb(new Error('POST ' + url + ' failed: ' + xhr.status));
      return;
    }
    cb(null);
  };
  xhr.onerror = function () { cb(new Error('network error')); };
  xhr.send();
}

function setImageWithFallback(img, primary, fallback) {
  var onFallback = img.src && img.src.indexOf('/preview/') !== -1;
  if (img._primary === primary && !onFallback) return;
  img._primary = primary;
  img.onerror = function () {
    this.onerror = null;
    this.src = fallback + '?t=' + Date.now();
  };
  img.src = primary;
}

function setBusy(btnId, busy, busyText, normalText) {
  var btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = !!busy;
  btn.style.opacity = busy ? '0.65' : '1';
  btn.style.cursor = busy ? 'not-allowed' : 'pointer';
  btn.innerText = busy ? busyText : normalText;
}

function startEnroll() {
  setBusy('startEnrollBtn', true, 'Starting...', 'Start Scan');
  document.getElementById('status').innerText = 'starting enroll...';
  var body = {
    person_name: document.getElementById('person').value.replace(/^\s+|\s+$/g, ''),
    samples: Number(document.getElementById('samples').value),
    interval: Number(document.getElementById('interval').value)
  };
  httpPostJson('/api/enroll/start', body, function (err) {
    setBusy('startEnrollBtn', false, 'Starting...', 'Start Scan');
    if (err) {
      document.getElementById('status').innerText = 'start enroll failed';
      alert(err.message || 'Failed to start enroll');
      return;
    }
    document.getElementById('status').innerText = 'enroll started';
  });
}

function stopEnroll() {
  setBusy('stopEnrollBtn', true, 'Stopping...', 'Stop Scan');
  httpPost('/api/enroll/stop', function () {
    setBusy('stopEnrollBtn', false, 'Stopping...', 'Stop Scan');
  });
}

function startInfer() {
  setBusy('startInferBtn', true, 'Starting Demo...', 'Start Recognition Demo');
  document.getElementById('status').innerText = 'starting demo...';
  httpPost('/api/infer/start', function (err) {
    setBusy('startInferBtn', false, 'Starting Demo...', 'Start Recognition Demo');
    if (err) {
      document.getElementById('status').innerText = 'start demo failed';
      alert(err.message || 'Failed to start infer');
      return;
    }
    document.getElementById('status').innerText = 'demo started';
  });
}

function stopInfer() {
  setBusy('stopInferBtn', true, 'Stopping Demo...', 'Stop Demo');
  httpPost('/api/infer/stop', function () {
    setBusy('stopInferBtn', false, 'Stopping Demo...', 'Stop Demo');
  });
}

function renderPeople(people) {
  var host = document.getElementById('peopleList');
  if (!people || !people.length) {
    host.innerHTML = '<span class="pill warn">No people enrolled yet</span>';
    return;
  }
  var html = '';
  for (var i = 0; i < people.length; i++) {
    html += '<span class="pill">' + esc(people[i].name) + ' (' + people[i].samples + ')</span>';
  }
  host.innerHTML = html;
}

function poll() {
  httpGetJson('/api/status', function (err, s) {
    if (err || !s) {
      document.getElementById('status').innerText = 'connection issue: retrying...';
      return;
    }

    var host = window.location.hostname;
    var liveColor = 'http://' + host + ':8081/stream?topic=/camera/camera/color/image_raw&quality=70';
    var liveEnroll = 'http://' + host + ':8081/stream?topic=/face_enroll/debug_image&quality=70';
    var liveInfer = 'http://' + host + ':8081/stream?topic=/face_identity/compare_image&quality=70';

    var enrollState = s.enroll.running ? ('enroll running pid=' + s.enroll.pid) : 'enroll idle';
    var inferState = s.infer.running ? ('infer running pid=' + s.infer.pid) : 'infer idle';
    document.getElementById('status').innerText = enrollState + ' | ' + inferState;

    var saved = s.enroll.saved || 0;
    var total = s.enroll.total || 0;
    document.getElementById('progressText').innerText = saved + ' / ' + total;
    var pct = total > 0 ? Math.min(100, Math.round(saved * 100 / total)) : 0;
    document.getElementById('bar').style.width = pct + '%';
    document.getElementById('guide').innerText = s.enroll.guidance || '';

    document.getElementById('enrollLogs').innerText = (s.enroll.logs || []).join('\\n');
    document.getElementById('inferLogs').innerText = (s.infer.logs || []).join('\\n');
    renderPeople(s.people || []);

    var enrollPreview = document.getElementById('enrollPreview');
    var inferPreview = document.getElementById('inferPreview');
    var enrollPrimary = s.enroll.running ? liveEnroll : liveColor;
    var inferPrimary = s.infer.running ? liveInfer : liveColor;
    setImageWithFallback(enrollPreview, enrollPrimary, '/preview/enroll.jpg');
    setImageWithFallback(inferPreview, inferPrimary, '/preview/identity.jpg');
  });
}

setInterval(poll, 1000);
poll();
</script>
</body>
</html>"""
    host = request.host.split(":")[0]
    live_color = (
        "http://"
        + host
        + ":8081/stream?topic=/camera/camera/color/image_raw&quality=70"
    )
    html = html.replace("__ENROLL_SRC__", live_color)
    html = html.replace("__INFER_SRC__", live_color)
    return Response(
        html,
        mimetype="text/html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )


@app.get("/preview/enroll.jpg")
def preview_enroll():
    p = Path("/tmp/face_enroll_debug.jpg")
    if not p.exists():
        return Response(status=204)
    return Response(
        p.read_bytes(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"}
    )


@app.get("/preview/identity.jpg")
def preview_identity():
    p = Path("/tmp/face_identity_compare.jpg")
    if not p.exists():
        return Response(status=204)
    return Response(
        p.read_bytes(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"}
    )


@app.get("/api/status")
def status():
    db_dir = Path(CONFIG["db_dir"])
    with ENROLL.lock:
        enroll_obj = {
            "running": ENROLL.running(),
            "pid": ENROLL.pid(),
            "saved": ENROLL.saved,
            "total": ENROLL.total,
            "logs": list(ENROLL.logs),
            "guidance": _guidance(ENROLL.saved, ENROLL.total),
        }
    with INFER.lock:
        infer_obj = {
            "running": INFER.running(),
            "pid": INFER.pid(),
            "logs": list(INFER.logs),
        }
    return jsonify(
        {"enroll": enroll_obj, "infer": infer_obj, "people": _list_people(db_dir)}
    )


@app.post("/api/enroll/start")
def enroll_start():
    payload = request.get_json(silent=True) or {}
    person_name = str(payload.get("person_name", "")).strip()
    samples = int(payload.get("samples", 30))
    interval = float(payload.get("interval", 0.35))

    if not person_name:
        return jsonify({"error": "person_name is required"}), 400
    if samples <= 0:
        return jsonify({"error": "samples must be > 0"}), 400
    if interval <= 0:
        return jsonify({"error": "interval must be > 0"}), 400

    with ENROLL.lock:
        if ENROLL.running():
            return jsonify({"error": "enroll already running"}), 409
        ENROLL.logs.clear()
        ENROLL.saved = 0
        ENROLL.total = samples
        cmd = [
            "python3",
            CONFIG["enroll_script"],
            "--person-name",
            person_name,
            "--samples",
            str(samples),
            "--capture-interval",
            str(interval),
            "--output-dir",
            CONFIG["db_dir"],
            "--headless",
        ]
        pid = _start_process(ENROLL, cmd)
    return jsonify({"ok": True, "pid": pid})


@app.post("/api/enroll/stop")
def enroll_stop():
    with ENROLL.lock:
        if ENROLL.running():
            proc = ENROLL.proc
            if proc is not None:
                proc.terminate()
            return jsonify({"ok": True, "stopping": True})
    return jsonify({"ok": True, "stopping": False})


@app.post("/api/infer/start")
def infer_start():
    with INFER.lock:
        if INFER.running():
            return jsonify({"error": "infer already running"}), 409
        INFER.logs.clear()
        cmd = [
            "python3",
            CONFIG["infer_script"],
            "--db-dir",
            CONFIG["db_dir"],
            "--model-path",
            str(Path(CONFIG["db_dir"]) / "model_centroid.pkl"),
            "--headless",
        ]
        pid = _start_process(INFER, cmd)
    return jsonify({"ok": True, "pid": pid})


@app.post("/api/infer/stop")
def infer_stop():
    with INFER.lock:
        if INFER.running():
            proc = INFER.proc
            if proc is not None:
                proc.terminate()
            return jsonify({"ok": True, "stopping": True})
    return jsonify({"ok": True, "stopping": False})


def parse_args():
    p = argparse.ArgumentParser(description="Face enrollment web studio")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8090)
    p.add_argument("--db-dir", default="/home/jetson/face_db")
    p.add_argument(
        "--enroll-script",
        default="/home/jetson/elder_and_dog/scripts/face_identity_enroll_cv.py",
    )
    p.add_argument(
        "--infer-script",
        default="/home/jetson/elder_and_dog/scripts/face_identity_infer_cv.py",
    )
    return p.parse_args()


def main():
    args = parse_args()
    CONFIG["db_dir"] = args.db_dir
    CONFIG["enroll_script"] = args.enroll_script
    CONFIG["infer_script"] = args.infer_script

    if not Path(CONFIG["enroll_script"]).exists():
        raise SystemExit(f"Enroll script not found: {CONFIG['enroll_script']}")
    if not Path(CONFIG["infer_script"]).exists():
        raise SystemExit(f"Infer script not found: {CONFIG['infer_script']}")

    Path(CONFIG["db_dir"]).mkdir(parents=True, exist_ok=True)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
