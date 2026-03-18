"""Thin bridge: gesture/pose events -> Go2 actions + TTS.

Does NOT touch speech events or face events (llm_bridge handles those).
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# go2_interfaces 可能沒在 vision_perception 的依賴裡，
# 所以用 std_msgs/String 發 JSON 到 /webrtc_req（跟 llm_bridge 一樣的方式）
# 不要 import go2_interfaces

# 注意：/event/gesture_detected 的 gesture enum 用的是 v2.0 contract 值
# fist 實作層發出的是 "ok"（GESTURE_COMPAT_MAP 已轉換）
GESTURE_ACTION_MAP = {
    "wave": {"api_id": 1016, "topic": "rt/api/sport/request", "tts": "你好！"},
    "stop": {"api_id": 1003, "topic": "rt/api/sport/request", "tts": None},
    "ok":   {"api_id": 1020, "topic": "rt/api/sport/request", "tts": None},  # fist -> ok via compat map
}

POSE_ACTION_MAP = {
    "fallen": {"api_id": None, "tts": "偵測到跌倒！請注意安全"},
}


class EventActionBridge(Node):
    def __init__(self):
        super().__init__("event_action_bridge")

        self.declare_parameter("gesture_cooldown", 3.0)
        self.declare_parameter("fallen_cooldown", 10.0)

        self.gesture_cooldown = self.get_parameter("gesture_cooldown").value
        self.fallen_cooldown = self.get_parameter("fallen_cooldown").value

        self._last_action_ts = {}  # action_name -> timestamp

        # Subscribe to vision events
        self.create_subscription(String, "/event/gesture_detected", self._on_gesture, 10)
        self.create_subscription(String, "/event/pose_detected", self._on_pose, 10)

        # Publish to Go2 (same interface as llm_bridge uses)
        self.webrtc_pub = self.create_publisher(String, "/webrtc_req", 10)
        self.tts_pub = self.create_publisher(String, "/tts", 10)

        self.get_logger().info("EventActionBridge ready")

    def _check_cooldown(self, key: str, cooldown: float) -> bool:
        """Return True if action is allowed (cooldown elapsed)."""
        now = time.time()
        last = self._last_action_ts.get(key, 0.0)
        if now - last < cooldown:
            return False
        self._last_action_ts[key] = now
        return True

    def _send_action(self, api_id: int, topic: str = "rt/api/sport/request"):
        """Send Go2 sport action via /webrtc_req."""
        msg = String()
        msg.data = json.dumps({
            "type": "req",
            "topic": topic,
            "data": {"api_id": api_id},
        })
        self.webrtc_pub.publish(msg)
        self.get_logger().info(f"Action: api_id={api_id}")

    def _send_tts(self, text: str):
        """Send TTS text."""
        msg = String()
        msg.data = text
        self.tts_pub.publish(msg)
        self.get_logger().info(f"TTS: {text}")

    def _on_gesture(self, msg: String):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            return

        gesture = data.get("gesture")
        if not gesture:
            return

        mapping = GESTURE_ACTION_MAP.get(gesture)
        if not mapping:
            return

        # stop has no cooldown (safety priority)
        if gesture == "stop":
            if mapping["api_id"]:
                self._send_action(mapping["api_id"], mapping["topic"])
            return

        # Other gestures have cooldown
        if not self._check_cooldown(f"gesture_{gesture}", self.gesture_cooldown):
            return

        if mapping["api_id"]:
            self._send_action(mapping["api_id"], mapping["topic"])
        if mapping.get("tts"):
            self._send_tts(mapping["tts"])

    def _on_pose(self, msg: String):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            return

        pose = data.get("pose")
        if not pose:
            return

        mapping = POSE_ACTION_MAP.get(pose)
        if not mapping:
            return

        cooldown = self.fallen_cooldown if pose == "fallen" else self.gesture_cooldown
        if not self._check_cooldown(f"pose_{pose}", cooldown):
            return

        if mapping.get("api_id"):
            self._send_action(mapping["api_id"])
        if mapping.get("tts"):
            self._send_tts(mapping["tts"])


def main():
    rclpy.init()
    node = EventActionBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
