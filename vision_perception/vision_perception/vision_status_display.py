"""Vision status display — renders gesture/pose state as an image for Foxglove.

Subscribes to /event/gesture_detected and /event/pose_detected,
renders a dashboard image (640x240 black bg, white text),
publishes to /vision_perception/status_image (sensor_msgs/Image BGR8).
"""
from __future__ import annotations

import json
import time

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String


class VisionStatusDisplay(Node):
    def __init__(self):
        super().__init__("vision_status_display")

        self.bridge = CvBridge()
        self._gesture = {"gesture": "—", "confidence": 0.0, "hand": "—"}
        self._pose = {"pose": "—", "confidence": 0.0}
        self._last_gesture_ts = 0.0
        self._last_pose_ts = 0.0

        self.create_subscription(String, "/event/gesture_detected", self._on_gesture, 10)
        self.create_subscription(String, "/event/pose_detected", self._on_pose, 10)
        self.image_pub = self.create_publisher(Image, "/vision_perception/status_image", 10)
        self.timer = self.create_timer(0.125, self._render)  # 8 Hz

        self.get_logger().info("VisionStatusDisplay ready — publishing to /vision_perception/status_image")

    def _on_gesture(self, msg: String):
        try:
            data = json.loads(msg.data)
            self._gesture = {
                "gesture": data.get("gesture", "?"),
                "confidence": data.get("confidence", 0.0),
                "hand": data.get("hand", "?"),
            }
            self._last_gesture_ts = time.time()
        except json.JSONDecodeError:
            pass

    def _on_pose(self, msg: String):
        try:
            data = json.loads(msg.data)
            self._pose = {
                "pose": data.get("pose", "?"),
                "confidence": data.get("confidence", 0.0),
            }
            self._last_pose_ts = time.time()
        except json.JSONDecodeError:
            pass

    def _render(self):
        img = np.zeros((240, 640, 3), dtype=np.uint8)
        now = time.time()
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Title
        cv2.putText(img, "Vision Perception Status", (20, 30), font, 0.7, (100, 200, 255), 2)
        cv2.line(img, (20, 40), (620, 40), (60, 60, 60), 1)

        # Gesture section
        g = self._gesture
        g_age = now - self._last_gesture_ts if self._last_gesture_ts > 0 else -1
        g_color = (0, 255, 0) if g_age >= 0 and g_age < 5.0 else (100, 100, 100)

        cv2.putText(img, "GESTURE", (20, 75), font, 0.5, (180, 180, 180), 1)
        cv2.putText(img, f"{g['gesture'].upper()}", (140, 75), font, 0.7, g_color, 2)
        cv2.putText(img, f"conf: {g['confidence']:.2f}   hand: {g['hand']}", (20, 105), font, 0.45, (150, 150, 150), 1)
        if g_age >= 0:
            cv2.putText(img, f"{g_age:.1f}s ago", (500, 75), font, 0.4, (120, 120, 120), 1)

        cv2.line(img, (20, 120), (620, 120), (60, 60, 60), 1)

        # Pose section
        p = self._pose
        p_age = now - self._last_pose_ts if self._last_pose_ts > 0 else -1
        if p["pose"] == "fallen":
            p_color = (0, 0, 255)  # red for fallen
        elif p_age >= 0 and p_age < 5.0:
            p_color = (0, 255, 0)
        else:
            p_color = (100, 100, 100)

        cv2.putText(img, "POSE", (20, 155), font, 0.5, (180, 180, 180), 1)
        cv2.putText(img, f"{p['pose'].upper()}", (140, 155), font, 0.7, p_color, 2)
        cv2.putText(img, f"conf: {p['confidence']:.2f}", (20, 185), font, 0.45, (150, 150, 150), 1)
        if p_age >= 0:
            cv2.putText(img, f"{p_age:.1f}s ago", (500, 155), font, 0.4, (120, 120, 120), 1)

        if p["pose"] == "fallen":
            cv2.putText(img, "!! FALLEN ALERT !!", (200, 220), font, 0.6, (0, 0, 255), 2)

        # Publish
        self.image_pub.publish(self.bridge.cv2_to_imgmsg(img, encoding="bgr8"))


def main():
    rclpy.init()
    node = VisionStatusDisplay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
