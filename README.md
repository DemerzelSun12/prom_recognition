# HPMA Prom Recognition

基于实时屏幕采集与时序圆形目标跟踪的舞会节奏圆识别项目。

本项目当前第一阶段目标是完成“只识别、不点击”：

1. 固定游戏窗口分辨率与 ROI。
2. 采集舞会玩法截图或录屏。
3. 使用 OpenCV 检测收缩圆圈。
4. 对同一个圆圈进行多帧跟踪。
5. 估计圆圈收缩速度和理论触发时刻。

## Recommended Environment

- OS: Windows 11 or macOS
- Python: 3.10 or 3.11
- GPU: NVIDIA RTX 5070 Ti, optional for later deep learning experiments
- Game window: 2048 x 1080
- Windows display scale: 100% recommended
- macOS permission: enable Screen Recording for Terminal or VS Code

## Setup

```bash
python -m venv .venv
pip install -r requirements.txt
```

Activate the virtual environment with `.venv\Scripts\activate` on Windows or
`source .venv/bin/activate` on macOS/Linux.

## Project Structure

```text
prom_recognition/
  README.md
  requirements.txt
  pyproject.toml
  .gitignore
  configs/
    default.yaml
  data/
    screenshots/
    videos/
    annotations/
  docs/
    preparation.md
  logs/
  src/
    prom_recognition/
      __init__.py
      main.py
      config.py
      capture.py
      detector.py
      tracker.py
      debug_view.py
      clicker.py
      utils/
        __init__.py
        geometry.py
        timing.py
  tests/
    test_geometry.py
```

## First Milestone

先运行静态截图识别，而不是实时点击：

```bash
python -m prom_recognition.main --image data/screenshots/sample.png
```

后续实现时建议按以下顺序推进：

1. 静态截图圆圈检测。
2. 视频逐帧检测。
3. 多目标轨迹跟踪。
4. 实时窗口截图。
5. 点击时机预测。
6. 鼠标点击执行与延迟校准。
