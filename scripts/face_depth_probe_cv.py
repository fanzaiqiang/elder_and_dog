#!/usr/bin/env python3
import os
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


class FaceDepthProbeCV(Node):
    def __init__(self):
        super().__init__("face_depth_probe_cv")
        self.bridge = CvBridge()
        self.lock = threading.Lock()
        self.color = None
        self.depth = None
        self.depth_scale = 0.001
        self.headless = not bool(os.environ.get("DISPLAY"))
        self.last_log_ts = 0.0
        self.last_save_ts = 0.0

        cascade_path = self._resolve_cascade_path()
        self.face = cv2.CascadeClassifier(str(cascade_path))
        if self.face.empty():
            raise RuntimeError(f"Failed to load Haar cascade: {cascade_path}")

        self.create_subscription(
            Image, "/camera/camera/color/image_raw", self.cb_color, 10
        )
        self.create_subscription(
            Image, "/camera/camera/aligned_depth_to_color/image_raw", self.cb_depth, 10
        )
        self.debug_image_pub = self.create_publisher(
            Image, "/face_depth/debug_image", 10
        )
        self.compare_image_pub = self.create_publisher(
            Image, "/face_depth/compare_image", 10
        )
        self.create_timer(0.05, self.tick)
        if self.headless:
            self.get_logger().info(
                "Headless mode enabled (no DISPLAY); printing distances to terminal"
            )

    def _resolve_cascade_path(self) -> Path:
        candidates = []
        if hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
            candidates.append(
                Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
            )

        candidates.extend(
            [
                Path(
                    "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
                ),
                Path(
                    "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml"
                ),
            ]
        )

        for candidate in candidates:
            if candidate.exists():
                self.get_logger().info(f"Using Haar cascade: {candidate}")
                return candidate

        raise FileNotFoundError(
            "Cannot find haarcascade_frontalface_default.xml. "
            "Install opencv data files (e.g., python3-opencv)."
        )

    def cb_color(self, msg):
        with self.lock:
            self.color = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

    def cb_depth(self, msg):
        with self.lock:
            self.depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")

    def tick(self):
        with self.lock:
            color = None if self.color is None else self.color.copy()
            depth = None if self.depth is None else self.depth.copy()

        if color is None or depth is None:
            return

        raw_view = color.copy()

        gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
        faces = self.face.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )

        for x, y, w, h in faces:
            x2 = min(color.shape[1], x + w)
            y2 = min(color.shape[0], y + h)
            roi = depth[y:y2, x:x2]
            valid = roi[(roi > 0) & (roi < 10000)]
            txt = (
                f"{float(np.median(valid)) * self.depth_scale:.2f} m"
                if valid.size
                else "N/A"
            )

            cv2.rectangle(color, (x, y), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                color,
                txt,
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        debug_msg = self.bridge.cv2_to_imgmsg(color, encoding="bgr8")
        self.debug_image_pub.publish(debug_msg)
        compare_view = cv2.hconcat([raw_view, color])
        compare_msg = self.bridge.cv2_to_imgmsg(compare_view, encoding="bgr8")
        self.compare_image_pub.publish(compare_msg)

        if self.headless:
            now = time.time()
            if now - self.last_log_ts >= 1.0:
                if len(faces) == 0:
                    self.get_logger().info("face_count=0")
                else:
                    distances = []
                    for x, y, w, h in faces:
                        x2 = min(color.shape[1], x + w)
                        y2 = min(color.shape[0], y + h)
                        roi = depth[y:y2, x:x2]
                        valid = roi[(roi > 0) & (roi < 10000)]
                        if valid.size:
                            distances.append(float(np.median(valid)) * self.depth_scale)
                    if distances:
                        msg = ", ".join(f"{d:.2f}m" for d in distances)
                        self.get_logger().info(
                            f"face_count={len(faces)} distance={msg}"
                        )
                    else:
                        self.get_logger().info(f"face_count={len(faces)} distance=N/A")
                self.last_log_ts = now
            if now - self.last_save_ts >= 1.0:
                cv2.imwrite("/tmp/face_depth_debug.jpg", color)
                cv2.imwrite("/tmp/face_depth_compare.jpg", compare_view)
                self.last_save_ts = now
            return

        cv2.imshow("face_depth_probe_cv", color)
        cv2.waitKey(1)


def main():
    rclpy.init()
    node = FaceDepthProbeCV()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
