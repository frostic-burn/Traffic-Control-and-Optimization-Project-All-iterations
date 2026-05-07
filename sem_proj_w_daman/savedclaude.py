
import cv2
import numpy as np
import yt_dlp
from collections import defaultdict
import time
import os
import csv
import contextlib
import subprocess
from datetime import datetime

# YOLOv8 via ultralytics (pip install ultralytics)
from ultralytics import YOLO


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

VEHICLE_CLASSES = {'car', 'motorcycle', 'bus', 'truck', 'bicycle'}
PERSON_CLASS    = 'person'

TRAFFIC_LEVELS    = [(0, 'EMPTY'), (3, 'LOW'), (8, 'MEDIUM'), (15, 'HIGH')]
PEDESTRIAN_LEVELS = [(0, 'EMPTY'), (5, 'LOW'), (15, 'MODERATE'), (25, 'BUSY')]

PIPE_WIDTH, PIPE_HEIGHT = 640, 480
PROCESS_EVERY_N = 2          # run inference every N frames
CSV_WRITE_EVERY_N = 30       # write CSV row every N processed frames
FPS_WINDOW = 30              # frames per FPS measurement window


# ──────────────────────────────────────────────────────────────────────────────
# Helper: level look-up
# ──────────────────────────────────────────────────────────────────────────────

def _level(value: int, thresholds: list) -> str:
    """Return the label whose upper threshold is first exceeded by value."""
    for threshold, label in thresholds:
        if value <= threshold:
            return label
    return thresholds[-1][1] + "+"          # beyond last threshold


def get_traffic_level(n: int) -> str:
    return _level(n, TRAFFIC_LEVELS + [(float('inf'), 'CONGESTED')])


def get_pedestrian_level(n: int) -> str:
    return _level(n, PEDESTRIAN_LEVELS + [(float('inf'), 'CROWDED')])


# ──────────────────────────────────────────────────────────────────────────────
# Main class
# ──────────────────────────────────────────────────────────────────────────────

class LiveStreamDetector:
    """Detect & track vehicles/people using YOLOv8m + ByteTrack."""

    def __init__(self, model_name: str = 'yolov8m.pt'):
        self.base_dir  = os.path.dirname(os.path.abspath(__file__))
        self.csv_file  = os.path.join(self.base_dir, 'detections.csv')

        self._init_csv()

        print(f"Loading YOLOv8 model: {model_name}  (downloads automatically if needed)")
        # model_name can be 'yolov8n.pt', 'yolov8m.pt', 'yolov8x.pt', etc.
        self.model = YOLO(model_name)

        # Class name list comes from the model itself
        self.class_names: dict[int, str] = self.model.names   # {id: name}

        # Stable colour per class id
        rng = np.random.default_rng(42)
        self.colors = rng.integers(80, 255, size=(len(self.class_names), 3)).tolist()

        self.confidence_threshold = 0.40
        self.iou_threshold        = 0.45

        print("✅ YOLOv8m loaded successfully!")

    # ── CSV ───────────────────────────────────────────────────────────────────

    def _init_csv(self):
        with open(self.csv_file, 'w', newline='') as f:
            csv.writer(f).writerow([
                'timestamp', 'source_type', 'source_id',
                'vehicle_count', 'person_count', 'total_objects',
                'cars', 'motorcycles', 'buses', 'trucks', 'bicycles',
                'traffic_level', 'pedestrian_level',
            ])
        print(f"✅ CSV initialised: {os.path.basename(self.csv_file)}")

    def _write_csv(self, source_type, source_id, vehicle_count, person_count, vehicle_types):
        traffic_level    = get_traffic_level(vehicle_count)
        pedestrian_level = get_pedestrian_level(person_count)
        with open(self.csv_file, 'a', newline='') as f:
            csv.writer(f).writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                source_type, source_id,
                vehicle_count, person_count, vehicle_count + person_count,
                vehicle_types.get('car', 0),
                vehicle_types.get('motorcycle', 0),
                vehicle_types.get('bus', 0),
                vehicle_types.get('truck', 0),
                vehicle_types.get('bicycle', 0),
                traffic_level, pedestrian_level,
            ])

    # ── YouTube helpers ───────────────────────────────────────────────────────

    def _get_youtube_stream(self, url: str):
        """Return (stream_url, http_headers) or (None, {}) on failure."""
        # Try multiple client profiles because some YouTube videos reject
        # default web extraction with a bot-check challenge.
        opts_list = [
            {
                'format': 'best[height<=720]/best',
                'quiet': True,
                'no_warnings': True,
                'source_address': '0.0.0.0',
            },
            {
                'format': 'best[height<=720]/best',
                'quiet': True,
                'no_warnings': True,
                'source_address': '0.0.0.0',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android']
                    }
                },
            },
        ]

        last_error = None
        for opts in opts_list:
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info.get('url'), info.get('http_headers', {})
            except Exception as e:
                last_error = e

        print(f"❌ yt-dlp error: {last_error}")
        return None, {}

    def _ffmpeg_options_str(self, headers: dict) -> str:
        parts = [
            "timeout;60000000",
            "reconnect;1",
            "reconnect_streamed;1",
            "reconnect_delay_max;10",
            "protocol_whitelist;file,crypto,data,http,https,tcp,tls",
        ]
        ua  = headers.get('User-Agent') or headers.get('user-agent', '')
        ref = headers.get('Referer')    or headers.get('referer', '')
        hdr_lines = []
        if ua:  hdr_lines.append(f"User-Agent: {ua}")
        if ref: hdr_lines.append(f"Referer: {ref}")
        if hdr_lines:
            parts.append("headers;" + "\\r\\n".join(hdr_lines) + "\\r\\n")
        return "|".join(parts)

    def _open_cv_capture(self, stream_url: str, headers: dict, retries: int = 3):
        os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = self._ffmpeg_options_str(headers)
        for attempt in range(1, retries + 1):
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return cap
            with contextlib.suppress(Exception):
                cap.release()
            print(f"⚠️  CV2 open attempt {attempt}/{retries} failed, retrying…")
            time.sleep(2)
        return None

    # ── FFmpeg pipe (fallback) ────────────────────────────────────────────────

    def _start_ffmpeg_pipe(self, stream_url: str, headers: dict,
                           width: int = PIPE_WIDTH, height: int = PIPE_HEIGHT):
        cmd = ["ffmpeg", "-loglevel", "error",
               "-rw_timeout", "15000000",
               "-reconnect", "1", "-reconnect_streamed", "1",
               "-reconnect_delay_max", "10"]
        ua  = headers.get('User-Agent') or headers.get('user-agent', '')
        ref = headers.get('Referer')    or headers.get('referer', '')
        if ua:  cmd.extend(["-user_agent", ua])
        if ref: cmd.extend(["-headers", f"Referer: {ref}\r\n"])
        cmd.extend(["-i", stream_url, "-an",
                    "-f", "rawvideo", "-pix_fmt", "bgr24",
                    "-vf", f"scale={width}:{height}", "-"])
        try:
            return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, bufsize=10**8)
        except Exception as e:
            print(f"❌ ffmpeg pipe start error: {e}")
            return None

    def _read_pipe_frame(self, proc, width: int, height: int):
        if proc is None or proc.stdout is None:
            return None
        raw = proc.stdout.read(width * height * 3)
        if len(raw) != width * height * 3:
            return None
        return np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3))

    @staticmethod
    def _stop_pipe(proc):
        if proc is None:
            return
        with contextlib.suppress(Exception): proc.terminate()
        with contextlib.suppress(Exception): proc.wait(timeout=3)
        if proc.poll() is None:
            with contextlib.suppress(Exception): proc.kill()

    # ── Detection (YOLOv8m + ByteTrack) ──────────────────────────────────────

    def detect_and_track(self, frame: np.ndarray):
        """
        Run YOLOv8m inference + ByteTrack on one frame.
        Returns list of dicts: {track_id, class_id, class_name, conf, box (x1,y1,x2,y2)}
        """
        results = self.model.track(
            frame,
            persist=True,                    # ByteTrack needs this
            tracker="bytetrack.yaml",        # bundled with ultralytics
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False,
        )

        detections = []
        if results and results[0].boxes is not None:
            boxes_data = results[0].boxes
            for i in range(len(boxes_data)):
                cls_id    = int(boxes_data.cls[i].item())
                conf      = float(boxes_data.conf[i].item())
                cls_name  = self.class_names.get(cls_id, str(cls_id))
                track_id  = (int(boxes_data.id[i].item())
                             if boxes_data.id is not None else -1)
                x1, y1, x2, y2 = boxes_data.xyxy[i].tolist()
                detections.append({
                    'track_id':   track_id,
                    'class_id':   cls_id,
                    'class_name': cls_name,
                    'conf':       conf,
                    'box':        (int(x1), int(y1), int(x2), int(y2)),
                })
        return detections

    # ── Counting ──────────────────────────────────────────────────────────────

    @staticmethod
    def count_objects(detections: list):
        vehicle_count  = 0
        person_count   = 0
        vehicle_types  = defaultdict(int)
        for det in detections:
            name = det['class_name']
            if name in VEHICLE_CLASSES:
                vehicle_count += 1
                vehicle_types[name] += 1
            elif name == PERSON_CLASS:
                person_count += 1
        return vehicle_count, person_count, vehicle_types

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw_detections(self, frame: np.ndarray, detections: list) -> np.ndarray:
        font = cv2.FONT_HERSHEY_SIMPLEX
        for det in detections:
            x1, y1, x2, y2 = det['box']
            color  = self.colors[det['class_id'] % len(self.colors)]
            tid    = det['track_id']
            label  = (f"[{tid}] {det['class_name']} {det['conf']:.2f}"
                      if tid >= 0 else f"{det['class_name']} {det['conf']:.2f}")
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            (tw, th), _ = cv2.getTextSize(label, font, 0.5, 2)
            cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 2, y1), color, -1)
            cv2.putText(frame, label, (x1 + 1, y1 - 4), font, 0.5, (0, 0, 0), 2)
        return frame

    def _draw_hud(self, frame: np.ndarray, source_type: str, fps: float,
                  vehicle_count: int, person_count: int,
                  vehicle_types: dict) -> np.ndarray:
        """Overlay semi-transparent info panel."""
        traffic_level    = get_traffic_level(vehicle_count)
        pedestrian_level = get_pedestrian_level(person_count)

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (420, 300), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        font  = cv2.FONT_HERSHEY_SIMPLEX
        white = (255, 255, 255)
        green = (80, 230, 80)
        cyan  = (0, 255, 255)
        yellow= (0, 220, 255)

        lines = [
            (f"Source : {source_type.upper()}",     0.65, white),
            (f"Vehicles: {vehicle_count}",           0.80, green),
            (f"People  : {person_count}",            0.80, green),
            (f"Traffic : {traffic_level}",           0.70, cyan),
            (f"Peds    : {pedestrian_level}",        0.70, cyan),
            (f"FPS     : {fps:.1f}",                 0.80, yellow),
            (f"Tracker : ByteTrack",                 0.55, white),
        ]
        y = 28
        for text, scale, color in lines:
            cv2.putText(frame, text, (10, y), font, scale, color, 2)
            y += int(scale * 50)

        for vtype, cnt in vehicle_types.items():
            if cnt > 0:
                cv2.putText(frame, f"  {vtype.capitalize()}: {cnt}",
                            (10, y), font, 0.50, (200, 200, 200), 1)
                y += 22

        return frame

    # ── Camera scanner ────────────────────────────────────────────────────────

    def list_available_cameras(self) -> list:
        print("\n🎥 Scanning cameras…")
        found = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    found.append(i)
                    print(f"   ✅ Camera {i}")
            cap.release()
        if not found:
            print("   ❌ No cameras found.")
        return found

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self, source_type: str = 'youtube', source_id=None):
        """Main detection/tracking loop."""
        use_pipe    = False
        pipe_proc   = None
        cap         = None
        stream_url  = None
        stream_hdrs = {}

        # ── Open source ───────────────────────────────────────────────────────
        if source_type == 'camera':
            cap = cv2.VideoCapture(source_id)
            if not cap.isOpened():
                print(f"❌ Cannot open camera {source_id}")
                return
            print(f"✅ Camera {source_id} opened.")
            window_title = f"Camera {source_id} — press Q to quit"

        else:  # youtube
            print("🔗 Fetching stream URL…")
            stream_url, stream_hdrs = self._get_youtube_stream(source_id)
            if not stream_url:
                print("❌ Could not retrieve stream URL.")
                return
            print("✅ Stream URL obtained.")

            cap = self._open_cv_capture(stream_url, stream_hdrs)
            if cap is None:
                print("⚠️  OpenCV fallback to ffmpeg pipe…")
                pipe_proc = self._start_ffmpeg_pipe(stream_url, stream_hdrs)
                if pipe_proc:
                    use_pipe = True
                else:
                    print("❌ ffmpeg pipe also failed.")
                    return
            window_title = "YouTube Detection — press Q to quit"

        print(f"✅ Detection started. CSV → {os.path.basename(self.csv_file)}")
        print("Press Q in the window (or Ctrl-C) to quit.\n")

        frame_count  = 0
        processed    = 0            # frames actually inferred
        fps          = 0.0
        fps_t0       = time.time()
        fps_counter  = 0

        last_vehicle_count = 0
        last_person_count  = 0
        last_vehicle_types: dict = {}

        while True:
            # ── Read frame ────────────────────────────────────────────────────
            if use_pipe:
                frame = self._read_pipe_frame(pipe_proc, PIPE_WIDTH, PIPE_HEIGHT)
                ok    = frame is not None
            else:
                ok, frame = cap.read()

            # ── Reconnect if stream dropped ───────────────────────────────────
            if not ok:
                if source_type == 'youtube':
                    print("⚠️  Stream lost. Reconnecting in 3 s…")
                    time.sleep(3)
                    if use_pipe:
                        self._stop_pipe(pipe_proc)
                    else:
                        cap.release()
                        cap = None

                    stream_url, stream_hdrs = self._get_youtube_stream(source_id)
                    if not stream_url:
                        print("❌ Re-fetch failed. Giving up.")
                        break

                    if use_pipe:
                        pipe_proc = self._start_ffmpeg_pipe(stream_url, stream_hdrs)
                        if pipe_proc is None:
                            break
                    else:
                        cap = self._open_cv_capture(stream_url, stream_hdrs)
                        if cap is None:
                            # fall back to pipe on reconnect too
                            pipe_proc = self._start_ffmpeg_pipe(stream_url, stream_hdrs)
                            if pipe_proc:
                                use_pipe = True
                            else:
                                break
                    continue
                else:
                    print("❌ Camera read error.")
                    break

            frame_count += 1

            # ── Only infer every N frames ─────────────────────────────────────
            if frame_count % PROCESS_EVERY_N != 0:
                continue

            processed += 1

            # Resize for inference; keep a display copy at original size
            display = frame.copy()
            infer_frame = cv2.resize(frame, (640, 480))

            # ── Inference ─────────────────────────────────────────────────────
            detections = self.detect_and_track(infer_frame)

            # Scale boxes back to display resolution
            sx = display.shape[1] / infer_frame.shape[1]
            sy = display.shape[0] / infer_frame.shape[0]
            for det in detections:
                x1, y1, x2, y2 = det['box']
                det['box'] = (int(x1*sx), int(y1*sy), int(x2*sx), int(y2*sy))

            vehicle_count, person_count, vehicle_types = self.count_objects(detections)

            # Cache for HUD between CSV writes
            last_vehicle_count = vehicle_count
            last_person_count  = person_count
            last_vehicle_types = dict(vehicle_types)

            # ── CSV write ─────────────────────────────────────────────────────
            if processed % CSV_WRITE_EVERY_N == 0:
                self._write_csv(source_type, str(source_id),
                                vehicle_count, person_count, vehicle_types)

            # ── FPS ───────────────────────────────────────────────────────────
            fps_counter += 1
            if fps_counter >= FPS_WINDOW:
                elapsed = time.time() - fps_t0
                fps     = FPS_WINDOW / elapsed if elapsed > 0 else 0.0
                fps_t0  = time.time()
                fps_counter = 0
                print(f"🚗 V:{vehicle_count:3d} | 👥 P:{person_count:3d} "
                      f"| 🚦 {get_traffic_level(vehicle_count):9s} | ⚡ {fps:.1f} fps")

            # ── Draw & show ───────────────────────────────────────────────────
            display = self.draw_detections(display, detections)
            display = self._draw_hud(display, source_type, fps,
                                     last_vehicle_count, last_person_count,
                                     last_vehicle_types)

            cv2.imshow(window_title, display)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # ── Cleanup ───────────────────────────────────────────────────────────
        if use_pipe:
            self._stop_pipe(pipe_proc)
        elif cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print(f"\n✅ Stopped. Data saved → {self.csv_file}")


# ──────────────────────────────────────────────────────────────────────────────
# CLI helpers
# ──────────────────────────────────────────────────────────────────────────────

def select_input_mode() -> str:
    print("\n" + "=" * 60)
    print("  SELECT INPUT MODE")
    print("=" * 60)
    print("  1  Camera (webcam / USB)")
    print("  2  YouTube Live Stream")
    print("=" * 60)
    while True:
        choice = input("Choice [1/2]: ").strip()
        if choice == '1': return 'camera'
        if choice == '2': return 'youtube'
        print("❌ Enter 1 or 2.")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Vehicle & People Detector — YOLOv8m + ByteTrack")
    print("=" * 60)

    mode = select_input_mode()

    # model_name can be swapped: 'yolov8n.pt' (fastest) … 'yolov8x.pt' (best)
    detector = LiveStreamDetector(model_name='yolov8m.pt')

    if mode == 'camera':
        cameras = detector.list_available_cameras()
        if not cameras:
            print("❌ No cameras found. Exiting.")
        else:
            print(f"\n📷 Available cameras: {cameras}")
            if len(cameras) == 1:
                cam_id = cameras[0]
                print(f"✅ Auto-selecting camera {cam_id}")
            else:
                while True:
                    try:
                        cam_id = int(input(f"Select camera {cameras}: ").strip())
                        if cam_id in cameras:
                            break
                        print(f"❌ Choose from {cameras}")
                    except ValueError:
                        print("❌ Enter a number.")
            detector.run(source_type='camera', source_id=cam_id)

    else:
        print("\n📺 Example live streams:")
        print("   Times Square : https://www.youtube.com/watch?v=eJ7ZkQ5TC08")
        print("   Abbey Road   : https://www.youtube.com/watch?v=sGYSw0D9zug")
        url = input("\nYouTube Live Stream URL: ").strip()
        if not url:
            print("❌ No URL entered. Exiting.")
        else:
            detector.run(source_type='youtube', source_id=url)
