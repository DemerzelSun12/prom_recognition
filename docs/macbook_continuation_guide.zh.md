# MacBook 继续开发指引

这份文档记录当前项目状态，以及明天切换到 MacBook 后如何继续做 HPMA 舞会圆圈识别。

## 当前目标

项目目前要从录制好的游戏视频中识别舞会节奏圆圈。

圆圈逻辑是：

1. 先出现一个固定大小的目标圆圈 `a`。
2. 外侧出现一个更大的圆圈 `b`。
3. 圆圈 `b` 会从外向内逐渐收缩。
4. 当 `b` 的半径收缩到和 `a` 差不多一样大时，就是理想点击时机。
5. `a` 不会改变大小，真正随时间变化的是 `b`。

所以识别问题分成两部分：

1. 识别固定目标圆 `a`，用来校准目标半径。
2. 追踪外侧收缩圆 `b` 的半径变化，用来预测点击时机。

## 当前配置基线

最新一版可用视频是原生 `2560 x 1440`、`60 fps`。

OpenCV 检测到视频里有一点稳定黑边：

```text
原始视频尺寸: 2560 x 1440
有效画面边界: x=40..2520, y=16..1411
有效裁剪区域: x=40, y=16, width=2480, height=1395
```

当前配置文件在：

```text
configs/default.yaml
```

关键配置如下：

```yaml
window:
  width: 2560
  height: 1440

video:
  input_crop:
    x: 40
    y: 16
    width: 2480
    height: 1395

roi:
  x: 0
  y: 145
  width: 2480
  height: 1145

timing:
  target_radius: 89
```

`target_radius: 89` 来自已经手工标注的固定目标圆 `a`。

目前 `a` 的人工标注统计：

```text
标注圆圈数量: 99
覆盖图片数量: 24
覆盖时间范围: 11.5s - 23.0s
半径范围: 79 - 96 px
平均半径: 88.59 px
半径中位数: 89 px
```

## 重要文件

核心代码：

```text
src/prom_recognition/config.py
src/prom_recognition/detector.py
src/prom_recognition/tracker.py
src/prom_recognition/main.py
src/prom_recognition/debug_view.py
```

辅助脚本：

```text
scripts/process_video.py
scripts/annotate_circles.py
```

生成数据位置：

```text
data/videos/hpma.mp4
data/screenshots/hpma_frames/
data/annotations/hpma_debug/
data/annotations/hpma_detections.csv
data/annotations/hpma_tracks.csv
data/annotations/hpma_manual_circles.csv
data/annotations/hpma_manual_outer_circles.csv
```

注意：`data/screenshots`、`data/videos`、`data/annotations` 默认被 git 忽略，只保留 `.gitkeep`。

如果要在 MacBook 上继续使用已有素材，需要手动传过去。

至少建议传：

```text
C:\Users\Xiao Sun\Videos\hpma.mp4
data/annotations/hpma_manual_circles.csv
```

视频可以重新抽帧，帧图和检测结果也可以重新生成；但人工标注 CSV 最好保留。

## MacBook 环境配置

在项目根目录执行：

```bash
conda env create -f environment.yml
conda activate prom-recognition
python -m pytest -q
```

说明：

- `requirements.txt` 里有 Windows 专用依赖，但使用了平台条件，macOS 上应该会跳过 `pywin32` 和 `dxcam`。
- 离线视频识别在 macOS 上应该可以继续做。
- 实时绑定窗口、截图、自动点击属于后续工作，未来需要按 macOS 单独适配。

如果环境已经存在，可以执行：

```bash
conda activate prom-recognition
python -m pip install -e . -r requirements.txt pytest
```

## 重新生成帧图和识别结果

把视频放到 MacBook 任意位置，例如：

```text
/Users/<you>/Videos/hpma.mp4
```

然后运行：

```bash
python scripts/process_video.py --video "/Users/<you>/Videos/hpma.mp4"
```

这个脚本会做几件事：

1. 把视频复制到 `data/videos/hpma.mp4`。
2. 抽帧到 `data/screenshots/hpma_frames/`。
3. 执行圆圈检测。
4. 输出逐帧检测 CSV。
5. 输出收缩轨迹汇总 CSV。
6. 输出带绿色检测叠图的 debug 图片。

默认输出：

```text
data/annotations/hpma_detections.csv
data/annotations/hpma_tracks.csv
data/annotations/hpma_debug/
```

## 为外侧收缩圆 b 做密集抽帧

之前的稀疏抽帧不够用，因为 `b` 收缩很快。

原视频是 `60 fps`，如果只按 `2 fps` 抽帧，很容易出现：

```text
上一张看不到 b
下一张 b 已经比 a 还小
```

这时已经错过点击时机。

目前最有价值的时间段是：

```text
11.5s - 23.5s
```

建议对这个区间逐帧抽取：

```bash
python scripts/process_video.py \
  --video "/Users/<you>/Videos/hpma.mp4" \
  --dense-start-seconds 11.5 \
  --dense-until-seconds 23.5 \
  --dense-step-frames 1 \
  --max-debug-frames 160
```

这会保留全视频的稀疏概览，同时对 `11.5s - 23.5s` 做逐帧抽取。

这个密集区间的帧名大致是：

```text
hpma_f000690_t011.500.png
hpma_f000691_t011.517.png
...
hpma_f001410_t023.500.png
```

这一段大约有 721 张图。

如果 MacBook 上处理较慢，可以降低密度：

```bash
python scripts/process_video.py \
  --video "/Users/<you>/Videos/hpma.mp4" \
  --dense-start-seconds 11.5 \
  --dense-until-seconds 23.5 \
  --dense-step-frames 2 \
  --max-debug-frames 80
```

或者只处理更短一段：

```bash
python scripts/process_video.py \
  --video "/Users/<you>/Videos/hpma.mp4" \
  --dense-start-seconds 11.5 \
  --dense-until-seconds 16.0 \
  --dense-step-frames 1 \
  --max-debug-frames 80
```

## 手工标注流程

标注工具会打开图片，并把圆心和半径写入 CSV。

工具显示的是经过 `video.input_crop` 裁剪后的画面，所以标注坐标和检测器使用的是同一套坐标。

### 标注目标圆 a

目标圆 `a` 是固定内圈，不会收缩。

运行：

```bash
python scripts/annotate_circles.py \
  --output data/annotations/hpma_manual_circles.csv \
  --state target_inner \
  --scale 0.4
```

操作方式：

```text
左键第一次：点圆心
左键第二次：点圆边缘
n：下一张
p：上一张
u：撤销当前图片最后一个标注
q 或 Esc：退出
```

标注 `a` 时：

1. 第一下点 `a` 的圆心。
2. 第二下点 `a` 的边缘。

### 标注外侧收缩圆 b

外侧圆 `b` 是会随时间收缩的圆，这是预测点击时机最关键的数据。

运行：

```bash
python scripts/annotate_circles.py \
  --output data/annotations/hpma_manual_outer_circles.csv \
  --state shrinking_outer \
  --start hpma_f000690_t011.500.png \
  --scale 0.4
```

标注 `b` 时：

1. 第一下点圆心，通常和 `a` 的圆心一致。
2. 第二下点外侧收缩圆 `b` 的边缘。

不要每一帧都标，太累。

建议对同一个圆圈标几个关键时刻：

```text
b 很大
b 收缩到中间
b 接近 a
```

第一批标注目标：

```text
30 - 50 个 b 标注
```

如果能对同一个圆圈连续标几帧，会非常有用，因为我们要看半径随时间的变化。

例如：

```text
hpma_f001080_t018.000.png
hpma_f001090_t018.167.png
hpma_f001100_t018.333.png
hpma_f001110_t018.500.png
```

如果某一帧里 `b` 已经比 `a` 小，就不用标了，因为那已经是点击过晚的状态。

## CSV 格式

人工标注 CSV 格式：

```csv
image,x,y,outer_radius,color,state,notes
```

对于 `a`，`outer_radius` 表示固定目标圆半径。

对于 `b`，`outer_radius` 表示外侧收缩圆半径。

用 `state` 区分两种标注：

```text
target_inner
shrinking_outer
```

自动检测输出：

```text
data/annotations/hpma_detections.csv
```

列：

```csv
frame,time_s,detection_index,x,y,radius,confidence
```

轨迹输出：

```text
data/annotations/hpma_tracks.csv
```

列：

```csv
track_id,observations,first_time_s,last_time_s,duration_s,latest_x,latest_y,first_radius,last_radius,shrink_speed_px_s
```

## 当前检测器表现

当前检测器会根据蓝色和金色高亮区域找圆，然后用 Hough Circle 和 ring score 过滤。

目前已经能识别真实圆圈，但仍然会有误检，主要来自：

```text
壁炉火光
人物脸部高亮
头发高光
窗户高光
金色 UI 特效
```

这是当前阶段正常现象。

下一步不要继续盲目调参数，而是要用人工标注做评估：

```text
人工标注的 a / b
vs
自动检测结果
```

然后根据评估结果决定怎么调。

## 下一步推荐开发内容

等有足够的 `b` 标注后，建议新增一个评估脚本：

```text
scripts/evaluate_annotations.py
```

它应该做：

1. 读取人工标注 CSV。
2. 读取自动检测 CSV。
3. 按圆心距离和半径误差匹配检测结果。
4. 输出：
   - 命中数量
   - 漏检数量
   - 误检数量
   - 圆心误差
   - 半径误差
5. 分别评估 `target_inner` 和 `shrinking_outer`。

建议初始匹配阈值：

```text
2560 视频裁剪坐标下:
圆心距离 <= 40 px
b 半径误差 <= 30 px
a 半径误差 <= 15 px
```

然后根据评估结果调整：

```text
detector.hsv_ranges
detector.min_ring_score
detector.hough_param2
tracker.max_center_distance
tracker.min_shrink_speed
timing.target_radius
```

## 明天推荐流程

1. 把仓库复制或拉到 MacBook。
2. 创建 conda 环境。
3. 把最新的 `hpma.mp4` 传到 MacBook。
4. 如果要保留今天的标注，把 `hpma_manual_circles.csv` 也传过去。
5. 用 `process_video.py` 对 11.5s - 23.5s 做逐帧抽帧。
6. 标注 30 - 50 个外侧收缩圆 `b`。
7. 编写或运行评估脚本，对比人工标注和自动检测。
8. 根据评估结果调检测器和追踪器。

## 常用命令

创建环境：

```bash
conda env create -f environment.yml
conda activate prom-recognition
python -m pytest -q
```

处理视频：

```bash
python scripts/process_video.py --video "/Users/<you>/Videos/hpma.mp4"
```

密集抽帧：

```bash
python scripts/process_video.py \
  --video "/Users/<you>/Videos/hpma.mp4" \
  --dense-start-seconds 11.5 \
  --dense-until-seconds 23.5 \
  --dense-step-frames 1 \
  --max-debug-frames 160
```

标注目标圆 `a`：

```bash
python scripts/annotate_circles.py \
  --output data/annotations/hpma_manual_circles.csv \
  --state target_inner \
  --scale 0.4
```

标注收缩圆 `b`：

```bash
python scripts/annotate_circles.py \
  --output data/annotations/hpma_manual_outer_circles.csv \
  --state shrinking_outer \
  --start hpma_f000690_t011.500.png \
  --scale 0.4
```

