import cv2
import numpy as np
import yt_dlp
from collections import defaultdict
import time
import urllib.request
import os
import csv
from datetime import datetime
import contextlib
import subprocess

class LiveStreamDetector:
    def __init__(self, model_type='yolov4-tiny'):
        """
        model_type: 'yolov4-tiny' (faster) or 'yolov4' (more accurate)
        """
        self.model_type = model_type
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_file = os.path.join(self.base_dir, 'detections.csv')
        self.init_csv()
        self.download_model_files()
        
        # Load YOLO model
        print("Loading YOLO model...")
        
        if model_type == 'yolov4-tiny':
            weights_path = os.path.join(self.base_dir, "yolov4-tiny.weights")
            cfg_path = os.path.join(self.base_dir, "yolov4-tiny.cfg")
            self.net = cv2.dnn.readNet(weights_path, cfg_path)
        else:
            weights_path = os.path.join(self.base_dir, "yolov4.weights")
            cfg_path = os.path.join(self.base_dir, "yolov4.cfg")
            self.net = cv2.dnn.readNet(weights_path, cfg_path)
        
        # Load class names
        coco_names_path = os.path.join(self.base_dir, "coco.names")
        with open(coco_names_path, "r") as f:
            self.classes = [line.strip() for line in f.readlines()]
        
        # Get output layer names
        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
        
        # Define colors for different classes
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3))
        
        # Classes we're interested in
        self.vehicle_classes = ['car', 'motorcycle', 'bus', 'truck', 'bicycle']
        self.person_class = 'person'
        
        # Detection thresholds
        self.confidence_threshold = 0.4
        self.nms_threshold = 0.4
        
        print("✅ Model loaded successfully!")
    
    def init_csv(self):
        """Initialize CSV file with headers"""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'source_type', 'source_id', 
                'vehicle_count', 'person_count', 'total_objects',
                'cars', 'motorcycles', 'buses', 'trucks', 'bicycles',
                'traffic_level', 'pedestrian_level'
            ])
        print(f"✅ CSV file initialized: {os.path.basename(self.csv_file)}")
    
    def download_model_files(self):
        """Download YOLO model files if not present"""
        files = {
            'coco.names': 'https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names',
            'yolov4-tiny.cfg': 'https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg',
            'yolov4-tiny.weights': 'https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights'
        }
        
        for filename, url in files.items():
            target_path = os.path.join(self.base_dir, filename)
            if not os.path.exists(target_path):
                print(f"Downloading {filename}...")
                try:
                    urllib.request.urlretrieve(url, target_path)
                    print(f"✅ {filename} downloaded!")
                except Exception as e:
                    print(f"❌ Error downloading {filename}: {e}")
    
    def list_available_cameras(self):
        """List all available camera devices"""
        print("\n🎥 Scanning for available cameras...")
        available_cameras = []
        
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append(i)
                    print(f"   ✅ Camera {i} - Available")
                cap.release()
        
        if not available_cameras:
            print("   ❌ No cameras found!")
        
        return available_cameras
    
    def get_youtube_stream(self, youtube_url):
        """Extract best quality stream from YouTube URL"""
        try:
            ydl_opts = {
                'format': 'best[height<=720]/best',
                'quiet': True,
                'no_warnings': True,
                'source_address': '0.0.0.0'
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                stream_url = info.get('url')
                headers = info.get('http_headers', {})
                return stream_url, headers
        except Exception as e:
            print(f"❌ Error getting YouTube stream: {e}")
            return None, {}

    def _build_ffmpeg_capture_options(self, headers):
        """Build FFmpeg capture options for more reliable HLS streams."""
        options = [
            "timeout;60000000",
            "reconnect;1",
            "reconnect_streamed;1",
            "reconnect_delay_max;10",
            "protocol_whitelist;file,crypto,data,http,https,tcp,tls"
        ]

        if headers:
            header_lines = []
            user_agent = headers.get('User-Agent') or headers.get('user-agent')
            if user_agent:
                header_lines.append(f"User-Agent: {user_agent}")
            referer = headers.get('Referer') or headers.get('referer')
            if referer:
                header_lines.append(f"Referer: {referer}")
            if header_lines:
                header_block = "\\r\\n".join(header_lines) + "\\r\\n"
                options.append(f"headers;{header_block}")

        return "|".join(options)

    def _open_youtube_capture(self, stream_url, headers, retries=3):
        """Open YouTube HLS stream with FFmpeg backend and retry if needed."""
        ffmpeg_options = self._build_ffmpeg_capture_options(headers)

        for attempt in range(1, retries + 1):
            os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = ffmpeg_options
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
            if cap.isOpened():
                return cap

            with contextlib.suppress(Exception):
                cap.release()

            print(f"⚠️ Stream open failed (attempt {attempt}/{retries}), retrying...")
            time.sleep(2)

        return cv2.VideoCapture()

    def _start_ffmpeg_pipe(self, stream_url, headers, width=640, height=480):
        """Start ffmpeg process that outputs raw BGR frames to stdout."""
        command = [
            "ffmpeg",
            "-loglevel", "error",
            "-rw_timeout", "15000000",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "10"
        ]

        user_agent = headers.get('User-Agent') or headers.get('user-agent')
        if user_agent:
            command.extend(["-user_agent", user_agent])

        referer = headers.get('Referer') or headers.get('referer')
        if referer:
            command.extend(["-headers", f"Referer: {referer}\\r\\n"])

        command.extend([
            "-i", stream_url,
            "-an",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-vf", f"scale={width}:{height}",
            "-"
        ])

        try:
            return subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=10**8
            )
        except Exception as e:
            print(f"❌ Could not start ffmpeg pipe: {e}")
            return None

    def _read_ffmpeg_frame(self, process, width, height):
        """Read one frame from ffmpeg rawvideo pipe."""
        if process is None or process.stdout is None:
            return None

        frame_size = width * height * 3
        frame_bytes = process.stdout.read(frame_size)
        if len(frame_bytes) != frame_size:
            return None

        frame = np.frombuffer(frame_bytes, dtype=np.uint8)
        return frame.reshape((height, width, 3))

    def _stop_ffmpeg_pipe(self, process):
        """Stop ffmpeg pipe process safely."""
        if process is None:
            return

        with contextlib.suppress(Exception):
            process.terminate()
        with contextlib.suppress(Exception):
            process.wait(timeout=3)
        if process.poll() is None:
            with contextlib.suppress(Exception):
                process.kill()
    
    def detect_objects(self, frame):
        """Detect objects in frame using YOLO"""
        height, width, channels = frame.shape
        
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)
        
        class_ids = []
        confidences = []
        boxes = []
        
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > self.confidence_threshold:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.nms_threshold)
        
        return boxes, confidences, class_ids, indexes
    
    def count_objects(self, class_ids, indexes):
        """Count vehicles and people"""
        vehicle_count = 0
        person_count = 0
        vehicle_types = defaultdict(int)
        
        if len(indexes) > 0:
            for i in indexes.flatten():
                class_name = self.classes[class_ids[i]]
                
                if class_name in self.vehicle_classes:
                    vehicle_count += 1
                    vehicle_types[class_name] += 1
                elif class_name == self.person_class:
                    person_count += 1
        
        return vehicle_count, person_count, vehicle_types
    
    def get_traffic_level(self, vehicle_count):
        """Determine traffic level"""
        if vehicle_count == 0:
            return "EMPTY"
        elif vehicle_count <= 3:
            return "LOW"
        elif vehicle_count <= 8:
            return "MEDIUM"
        elif vehicle_count <= 15:
            return "HIGH"
        else:
            return "CONGESTED"
    
    def get_pedestrian_level(self, person_count):
        """Determine pedestrian level"""
        if person_count == 0:
            return "EMPTY"
        elif person_count <= 5:
            return "LOW"
        elif person_count <= 15:
            return "MODERATE"
        elif person_count <= 25:
            return "BUSY"
        else:
            return "CROWDED"
    
    def write_to_csv(self, source_type, source_id, vehicle_count, person_count, vehicle_types):
        """Write detection data to CSV"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_objects = vehicle_count + person_count
        traffic_level = self.get_traffic_level(vehicle_count)
        pedestrian_level = self.get_pedestrian_level(person_count)
        
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                source_type,
                source_id,
                vehicle_count,
                person_count,
                total_objects,
                vehicle_types.get('car', 0),
                vehicle_types.get('motorcycle', 0),
                vehicle_types.get('bus', 0),
                vehicle_types.get('truck', 0),
                vehicle_types.get('bicycle', 0),
                traffic_level,
                pedestrian_level
            ])
    
    def draw_detections(self, frame, boxes, confidences, class_ids, indexes):
        """Draw bounding boxes and labels"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        if len(indexes) > 0:
            for i in indexes.flatten():
                box = boxes[i]
                x, y, w, h = box
                
                label = str(self.classes[class_ids[i]])
                confidence = confidences[i]
                color = self.colors[class_ids[i]]
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                
                label_text = f"{label}: {confidence:.2f}"
                (text_width, text_height), baseline = cv2.getTextSize(label_text, font, 0.5, 2)
                cv2.rectangle(frame, (x, y - text_height - 10), (x + text_width, y), color, -1)
                cv2.putText(frame, label_text, (x, y - 5), font, 0.5, (0, 0, 0), 2)
        
        return frame
    
    def run(self, source_type='youtube', source_id=None):
        """Main detection loop"""
        use_ffmpeg_pipe = False
        ffmpeg_proc = None
        pipe_width, pipe_height = 640, 480
        
        if source_type == 'camera':
            cap = cv2.VideoCapture(source_id)
            print(f"✅ Camera {source_id} opened successfully!")
            window_title = f"Camera {source_id} Detection - Press 'q' to quit"
        else:
            print("🔗 Getting YouTube stream URL...")
            stream_url, stream_headers = self.get_youtube_stream(source_id)
            
            if stream_url is None:
                print("❌ Failed to get stream URL")
                return
            
            print(f"✅ Stream URL obtained!")
            cap = self._open_youtube_capture(stream_url, stream_headers)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            else:
                print("⚠️ OpenCV could not open stream directly. Falling back to ffmpeg pipe...")
                ffmpeg_proc = self._start_ffmpeg_pipe(stream_url, stream_headers, pipe_width, pipe_height)
                if ffmpeg_proc is not None:
                    use_ffmpeg_pipe = True
            window_title = "YouTube Live Detection - Press 'q' to quit"
        
        if not use_ffmpeg_pipe and not cap.isOpened():
            print("❌ Error: Could not open video source")
            return
        
        print(f"✅ Starting detection... Writing to {os.path.basename(self.csv_file)}")
        print("Press 'q' to quit\n")
        
        frame_count = 0
        fps_time = time.time()
        fps = 0
        process_every_n_frames = 2
        write_every_n_frames = 30  # Write to CSV every 30 frames (~1 second)
        
        while True:
            if use_ffmpeg_pipe:
                frame = self._read_ffmpeg_frame(ffmpeg_proc, pipe_width, pipe_height)
                ret = frame is not None
            else:
                ret, frame = cap.read()
            
            if not ret:
                if source_type == 'youtube':
                    print("⚠️ Stream ended. Reconnecting...")
                    if use_ffmpeg_pipe:
                        self._stop_ffmpeg_pipe(ffmpeg_proc)
                    else:
                        cap.release()
                    time.sleep(2)
                    stream_url, stream_headers = self.get_youtube_stream(source_id)
                    if stream_url:
                        if use_ffmpeg_pipe:
                            ffmpeg_proc = self._start_ffmpeg_pipe(stream_url, stream_headers, pipe_width, pipe_height)
                        else:
                            cap = self._open_youtube_capture(stream_url, stream_headers)
                            if cap.isOpened():
                                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    else:
                        break
                    continue
                else:
                    print("❌ Error reading from camera")
                    break
            
            frame_count += 1
            
            if frame_count % process_every_n_frames == 0:
                if frame_count % 30 == 0:
                    fps = 30 / (time.time() - fps_time)
                    fps_time = time.time()
                
                display_frame = frame.copy()
                if use_ffmpeg_pipe:
                    frame = display_frame
                else:
                    frame = cv2.resize(frame, (640, 480))
                
                boxes, confidences, class_ids, indexes = self.detect_objects(frame)
                vehicle_count, person_count, vehicle_types = self.count_objects(class_ids, indexes)
                
                # Write to CSV periodically
                if frame_count % write_every_n_frames == 0:
                    self.write_to_csv(source_type, str(source_id), vehicle_count, person_count, vehicle_types)
                
                scale_x = display_frame.shape[1] / frame.shape[1]
                scale_y = display_frame.shape[0] / frame.shape[0]
                
                scaled_boxes = [[int(x*scale_x), int(y*scale_y), int(w*scale_x), int(h*scale_y)] 
                               for x, y, w, h in boxes]
                
                display_frame = self.draw_detections(display_frame, scaled_boxes, confidences, class_ids, indexes)
                
                # Info panel
                overlay = display_frame.copy()
                cv2.rectangle(overlay, (0, 0), (400, 280), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, display_frame, 0.4, 0, display_frame)
                
                traffic_level = self.get_traffic_level(vehicle_count)
                pedestrian_level = self.get_pedestrian_level(person_count)
                
                # Display info
                cv2.putText(display_frame, f"Source: {source_type.upper()}", (10, 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(display_frame, f"Vehicles: {vehicle_count}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(display_frame, f"People: {person_count}", (10, 95), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Traffic: {traffic_level}", (10, 130), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(display_frame, f"Pedestrians: {pedestrian_level}", (10, 165), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 200), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(display_frame, f"CSV: {self.csv_file}", (10, 235), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                y_offset = 270
                for vehicle_type, count in vehicle_types.items():
                    if count > 0:
                        cv2.putText(display_frame, f"{vehicle_type.capitalize()}: {count}", (10, y_offset), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                        y_offset += 25
                
                cv2.imshow(window_title, display_frame)
                
                if frame_count % 30 == 0:
                    print(f"🚗 V:{vehicle_count} | 👥 P:{person_count} | 🚦 {traffic_level} | ⚡ {fps:.1f}fps")
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        if use_ffmpeg_pipe:
            self._stop_ffmpeg_pipe(ffmpeg_proc)
        else:
            cap.release()
        cv2.destroyAllWindows()
        print(f"\n✅ Detection stopped! Data saved to {self.csv_file}")


def select_input_mode():
    """Interactive mode selection"""
    print("\n" + "=" * 60)
    print("🎥 SELECT INPUT MODE")
    print("=" * 60)
    print("\n1️⃣  Camera (Webcam/USB Camera)")
    print("2️⃣  YouTube Live Stream")
    print("\n" + "=" * 60)
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == '1':
            return 'camera'
        elif choice == '2':
            return 'youtube'
        else:
            print("❌ Invalid choice! Please enter 1 or 2.")


if __name__ == "__main__":
    print("=" * 60)
    print("🎥 Vehicle & People Detection → CSV → Pathway → RAG")
    print("=" * 60)
    
    mode = select_input_mode()
    detector = LiveStreamDetector(model_type='yolov4-tiny')
    
    if mode == 'camera':
        cameras = detector.list_available_cameras()
        
        if not cameras:
            print("\n❌ No cameras found! Exiting...")
        else:
            print(f"\n📷 Available cameras: {cameras}")
            
            if len(cameras) == 1:
                camera_id = cameras[0]
                print(f"✅ Using Camera {camera_id}")
            else:
                while True:
                    try:
                        camera_input = input(f"\nSelect camera index {cameras}: ").strip()
                        camera_id = int(camera_input)
                        if camera_id in cameras:
                            break
                        else:
                            print(f"❌ Invalid camera! Choose from {cameras}")
                    except ValueError:
                        print("❌ Please enter a valid number!")
            
            detector.run(source_type='camera', source_id=camera_id)
    
    else:
        print("\n📺 Popular Live Streams:")
        print("   • Times Square NYC: https://www.youtube.com/watch?v=eJ7ZkQ5TC08")
        print("   • Abbey Road London: https://www.youtube.com/watch?v=sGYSw0D9zug")
        
        youtube_url = input("\nEnter YouTube Live Stream URL: ").strip()
        
        if not youtube_url:
            print("❌ No URL provided!")
        else:
            detector.run(source_type='youtube', source_id=youtube_url)
