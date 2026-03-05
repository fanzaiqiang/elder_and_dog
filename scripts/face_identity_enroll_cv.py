#!/usr/bin/env python3
import argparse
import os
import time
from pathlib import Path

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


def resolve_cascade_path() -> Path:
    candidates = []
    if hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
        candidates.append(
            Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        )
    candidates.extend(
        [
            Path("/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"),
            Path("/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Cannot find haarcascade_frontalface_default.xml")


class FaceEnrollNode(Node):
    def __init__(self, args):
        super().__init__("face_identity_enroll_cv")
        self.args = args
        self.bridge = CvBridge()
        self.headless = not bool(os.environ.get("DISPLAY")) or args.headless
        self.face = cv2.CascadeClassifier(str(resolve_cascade_path()))
        if self.face.empty():
            raise RuntimeError("Failed to load Haar cascade")

        self.person_dir = Path(args.output_dir) / args.person_name
        self.person_dir.mkdir(parents=True, exist_ok=True)

        self.saved = 0
        self.last_save_ts = 0.0
        self.last_preview_ts = 0.0

        self.create_subscription(Image, args.color_topic, self.cb_color, 10)
        self.debug_image_pub = self.create_publisher(
            Image, "/face_enroll/debug_image", 10
        )

        self.get_logger().info(f"Enroll person={args.person_name}")
        self.get_logger().info(f"Output dir={self.person_dir}")
        self.get_logger().info(f"Headless={self.headless}")

    def cb_color(self, msg):
        if self.saved >= self.args.samples:
            self.get_logger().info("Target samples reached, shutting down")
            rclpy.shutdown()
            return

        img = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        draw = img.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
        )

        if len(faces) == 0:
            cv2.putText(
                draw,
                f"captured={self.saved}/{self.args.samples}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
            )
            self.debug_image_pub.publish(
                self.bridge.cv2_to_imgmsg(draw, encoding="bgr8")
            )
            now = time.time()
            if self.headless and now - self.last_preview_ts >= 1.0:
                cv2.imwrite("/tmp/face_enroll_debug.jpg", draw)
                self.last_preview_ts = now
            if not self.headless:
                cv2.imshow("face_enroll", img)
                cv2.waitKey(1)
            return

        x, y, w, h = max(faces, key=lambda t: t[2] * t[3])
        crop = gray[y : y + h, x : x + w]
        crop = cv2.resize(crop, (160, 160), interpolation=cv2.INTER_AREA)

        now = time.time()
        if now - self.last_save_ts < self.args.capture_interval:
            cv2.rectangle(draw, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                draw,
                f"captured={self.saved}/{self.args.samples}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            self.debug_image_pub.publish(
                self.bridge.cv2_to_imgmsg(draw, encoding="bgr8")
            )
            if self.headless and now - self.last_preview_ts >= 1.0:
                cv2.imwrite("/tmp/face_enroll_debug.jpg", draw)
                self.last_preview_ts = now
            if not self.headless:
                draw = img.copy()
                cv2.rectangle(draw, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    draw,
                    f"captured={self.saved}/{self.args.samples}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow("face_enroll", draw)
                cv2.waitKey(1)
            return

        out_file = self.person_dir / f"{self.args.person_name}_{self.saved:04d}.png"
        cv2.imwrite(str(out_file), crop)
        self.saved += 1
        self.last_save_ts = now
        self.get_logger().info(f"saved {out_file} ({self.saved}/{self.args.samples})")

        cv2.rectangle(draw, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            draw,
            f"captured={self.saved}/{self.args.samples}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
        self.debug_image_pub.publish(self.bridge.cv2_to_imgmsg(draw, encoding="bgr8"))
        if self.headless and now - self.last_preview_ts >= 1.0:
            cv2.imwrite("/tmp/face_enroll_debug.jpg", draw)
            self.last_preview_ts = now

        if not self.headless:
            draw = img.copy()
            cv2.rectangle(draw, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                draw,
                f"captured={self.saved}/{self.args.samples}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            cv2.imshow("face_enroll", draw)
            cv2.waitKey(1)


def parse_args():
    p = argparse.ArgumentParser(description="Enroll face samples from ROS2 color topic")
    p.add_argument("--person-name", required=True)
    p.add_argument("--samples", type=int, default=30)
    p.add_argument("--capture-interval", type=float, default=0.25)
    p.add_argument("--output-dir", default="/home/jetson/face_db")
    p.add_argument("--color-topic", default="/camera/camera/color/image_raw")
    p.add_argument("--headless", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    rclpy.init()
    node = FaceEnrollNode(args)
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
