# AGENTS.md

Instructions for AI coding agents operating in this repository.

## Project Overview

**Elder and Dog (老人與狗)** - A ROS2-based smart item-finding system using Unitree Go2 quadruped robot with SLAM, Nav2 navigation, and AI perception (YOLO-World + Depth Anything).

**Tech Stack:**
- ROS2 Humble (Ubuntu 22.04)
- Python 3.10+ / C++17
- Unitree Go2 robot (WebRTC/CycloneDDS connectivity)
- SLAM (slam_toolbox) + Nav2 navigation
- PyTorch/TorchVision for object detection

---

## Build Commands

```bash
# Source ROS2 environment (REQUIRED before building)
source /opt/ros/humble/setup.bash
source install/setup.bash

# Build all packages
colcon build

# Build specific package
colcon build --packages-select go2_robot_sdk
colcon build --packages-select lidar_processor_cpp
colcon build --packages-select search_logic

# Force CMake reconfigure
colcon build --cmake-force-configure

# Install ROS2 dependencies
rosdep install --from-paths src --ignore-src -r -y

# Install Python dependencies (ALWAYS use uv, NOT pip)
uv pip install -r requirements.txt
```

---

## Test Commands

```bash
# Run pytest tests for a package
colcon test --packages-select search_logic
colcon test-result --verbose

# Run single test file directly
python3 src/search_logic/test/test_import.py

# Run pytest with verbose output
cd src/search_logic && python3 -m pytest test/test_import.py -v
```

---

## Lint & Format

```bash
# Python linting (flake8, max-line-length 100)
flake8 --max-line-length=100 go2_robot_sdk/

# C++ formatting check (ament_uncrustify)
ament_uncrustify --check lidar_processor_cpp/src/

# ros-mcp-server uses ruff
cd ros-mcp-server && ruff check . && ruff format --check .
```

---

## Run Commands

```bash
# Set environment variables (REQUIRED)
export ROBOT_IP="192.168.12.1"
export CONN_TYPE="webrtc"  # or "cyclonedds"

# Full system launch
ros2 launch go2_robot_sdk robot.launch.py slam:=true nav2:=true rviz2:=true foxglove:=true

# Minimal driver only
ros2 launch go2_robot_sdk robot.launch.py slam:=false nav2:=false

# Object detection node
ros2 run coco_detector coco_detector_node --ros-args -p device:=cuda

# Patrol/search logic node
ros2 run search_logic simple_patrol_node --ros-args -p auto_start:=true

# Phase 1 automated testing (recommended)
zsh phase1_test.sh env   # Environment check
zsh phase1_test.sh t1    # Start driver
zsh phase1_test.sh t3    # Start SLAM + Nav2
```

---

## Code Style Guidelines

### Python

- **Line length:** 100 characters max
- **Linter:** flake8
- **Imports:** Standard library, third-party, then local imports (separated by blank lines)
- **Docstrings:** Use triple-quoted docstrings for modules, classes, and functions
- **Type hints:** Preferred for function signatures
- **Dataclasses:** Use `@dataclass` for data containers (see `domain/entities/`)
- **Naming:**
  - `snake_case` for functions, variables, modules
  - `PascalCase` for classes
  - `UPPER_SNAKE_CASE` for constants
- **SPDX License header required:**
  ```python
  # Copyright (c) 2024, RoboVerse community
  # SPDX-License-Identifier: BSD-3-Clause
  ```

### C++ (C++17)

- **Standard:** C++17 required
- **Compiler warnings:** `-Wall -Wextra -Wpedantic`
- **Formatting:** ament_uncrustify
- **Naming:**
  - `snake_case` for functions, variables
  - `PascalCase` for classes
  - `kCamelCase` for constants
- **Thread safety:** Use `std::lock_guard<std::mutex>` for shared data
- **SPDX License header required:**
  ```cpp
  // Copyright (c) 2024, RoboVerse community
  // SPDX-License-Identifier: BSD-3-Clause
  ```

### ROS2 Conventions

- **Node naming:** Use descriptive `snake_case` names (e.g., `go2_driver_node`)
- **Topics:** Use `/namespace/topic_name` pattern
- **Parameters:** Declare with `declare_parameter()`, validate inputs
- **QoS:** Use appropriate profiles (BEST_EFFORT for sensors, RELIABLE for commands)

---

## Architecture Overview

The main package `go2_robot_sdk` follows **Clean Architecture**:

```
go2_robot_sdk/
├── domain/           # Pure business logic (no ROS2 deps)
│   ├── entities/     # Data structures (RobotState, IMUData, etc.)
│   ├── interfaces/   # Abstract ports
│   ├── constants/    # Domain constants
│   └── math/         # Kinematics, geometry
├── application/      # Use cases and services
│   ├── services/     # RobotDataService, RobotControlService
│   └── utils/        # Command generation
├── infrastructure/   # External adapters
│   ├── webrtc/       # WebRTC connection to Go2
│   ├── sensors/      # LiDAR, camera decoders
│   └── ros2/         # ROS2 publishers
└── presentation/     # ROS2 node entry points
    └── go2_driver_node.py
```

**Design principles:**
- Domain layer has NO external dependencies
- Application/infrastructure depend on domain interfaces
- Presentation layer is the thin ROS2 entry point

---

## Key Packages

| Package | Language | Description |
|---------|----------|-------------|
| `go2_robot_sdk` | Python | Main Go2 driver, WebRTC/CycloneDDS connection |
| `go2_interfaces` | C++ | Custom ROS2 message definitions |
| `lidar_processor` | Python | LiDAR point cloud processing |
| `lidar_processor_cpp` | C++ | High-performance LiDAR with PCL |
| `coco_detector` | Python | Object detection (TorchVision) |
| `search_logic` | Python | Patrol and navigation FSM |
| `speech_processor` | Python | TTS (ElevenLabs API) |
| `ros-mcp-server` | Python | MCP protocol for LLM-robot control |

---

## Important Configuration Files

- `go2_robot_sdk/config/nav2_params.yaml` - Nav2 parameters
- `go2_robot_sdk/config/mapper_params_online_async.yaml` - SLAM parameters
- `go2_robot_sdk/config/twist_mux.yaml` - Velocity command multiplexing
- `go2_robot_sdk/config/cyclonedds.xml` - DDS network configuration

---

## Error Handling

- **Never suppress errors silently** - log or re-raise
- **Use ROS2 logging:** `self.get_logger().error()`, `.warn()`, `.info()`, `.debug()`
- **Validate parameters** at node startup
- **Graceful shutdown:** Handle `KeyboardInterrupt` and cleanup resources

---

## Critical Coordinate Frames

| Frame | Description | Notes |
|-------|-------------|-------|
| `map` | SLAM world frame | Nav2 goals use this |
| `base_link` | Robot body center | Motion control reference |
| `front_camera` | Default camera frame | NOT `camera_link` in default URDF! |

---

## Agent-Specific Instructions

1. **Language:** Reply in **Traditional Chinese (繁體中文)** when conversing
2. **Package manager:** ALWAYS use `uv pip install`, NEVER plain `pip install`
3. **Shell:** Default shell is `zsh` for scripts
4. **Code review mode:** If asked to review, adopt Linus Torvalds persona - be strict, focus on architecture and performance
5. **Clean Architecture:** Respect layer boundaries. Domain layer must have no ROS2 dependencies
6. **Testing:** Run `colcon test` after significant changes
7. **Launch files:** No rebuild needed for launch file changes - just restart

---

## Common Development Scenarios

### Adding a New ROS2 Node

1. Create node file in appropriate package
2. Update `setup.py` entry_points:
   ```python
   'console_scripts': [
       'my_node = package.my_node:main',
   ],
   ```
3. `colcon build --packages-select <package>`
4. `source install/setup.bash`
5. `ros2 run <package> my_node`

### Debugging TF Issues

```bash
ros2 run tf2_tools view_frames  # Generates frames.pdf
ros2 run tf2_ros tf2_echo map base_link  # Real-time TF
```

### Saving/Loading Maps

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map
ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=~/maps/my_map.yaml
```
