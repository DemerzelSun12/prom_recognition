# MacBook Continuation Guide

This document records the current project state and the next steps for continuing HPMA prom circle recognition on another machine.

## Current Goal

The project is trying to detect HPMA prom rhythm circles from recorded gameplay video.

The important game logic is:

1. A fixed target circle `a` appears first.
2. A larger outer circle `b` appears outside `a`.
3. Circle `b` shrinks inward over time.
4. The desired click moment is when `b` becomes approximately the same radius as `a`.
5. Circle `a` does not change size. Circle `b` is the moving/shrinking object.

So the detection problem has two parts:

1. Detect stable target circles `a` to calibrate the target radius.
2. Track shrinking outer circles `b` over time and predict when their radius reaches the target radius.

## Current Config Baseline

The latest working video was recorded as native 2560 x 1440 at 60 fps.

OpenCV detected a small stable black border in the video:

```text
raw video size: 2560 x 1440
effective content bbox: x=40..2520, y=16..1411
effective crop: x=40, y=16, width=2480, height=1395
```

The active config is in:

```text
configs/default.yaml
```

Key values currently are:

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

`target_radius: 89` comes from manual annotations of the fixed target circle `a`.

Current manual annotation statistics for `a`:

```text
annotated circles: 99
annotated images: 24
time range: 11.5s - 23.0s
radius range: 79 - 96 px
mean radius: 88.59 px
median radius: 89 px
```

## Important Files

Core code:

```text
src/prom_recognition/config.py
src/prom_recognition/detector.py
src/prom_recognition/tracker.py
src/prom_recognition/main.py
src/prom_recognition/debug_view.py
```

Helper scripts:

```text
scripts/process_video.py
scripts/annotate_circles.py
```

Generated data locations:

```text
data/videos/hpma.mp4
data/screenshots/hpma_frames/
data/annotations/hpma_debug/
data/annotations/hpma_detections.csv
data/annotations/hpma_tracks.csv
data/annotations/hpma_manual_circles.csv
data/annotations/hpma_manual_outer_circles.csv
```

Important: `data/screenshots`, `data/videos`, and `data/annotations` are ignored by git except `.gitkeep`. If you need existing videos, frames, or manual annotation CSV files on the MacBook, transfer them manually.

At minimum, transfer:

```text
C:\Users\Xiao Sun\Videos\hpma.mp4
data/annotations/hpma_manual_circles.csv
```

The video can be regenerated into frames, but manual annotations should be preserved.

## Environment Setup On MacBook

From the project root:

```bash
conda env create -f environment.yml
conda activate prom-recognition
python -m pytest -q
```

Notes:

- `requirements.txt` has Windows-only dependencies guarded by platform markers, so `pywin32` and `dxcam` should be skipped on macOS.
- Offline video recognition should work on macOS.
- Realtime window binding and click automation are still future work and will likely need platform-specific code.

If the conda env already exists:

```bash
conda activate prom-recognition
python -m pip install -e . -r requirements.txt pytest
```

## Recreate Frames And Detection Outputs

Place the transferred video anywhere convenient. Example:

```text
/Users/<you>/Videos/hpma.mp4
```

Then run:

```bash
python scripts/process_video.py --video "/Users/<you>/Videos/hpma.mp4"
```

This will:

1. Copy the video into `data/videos/hpma.mp4`.
2. Extract frames into `data/screenshots/hpma_frames/`.
3. Run circle detection.
4. Write detection CSV output.
5. Write shrinking track summary CSV output.
6. Write debug images with green detection overlays.

Default outputs:

```text
data/annotations/hpma_detections.csv
data/annotations/hpma_tracks.csv
data/annotations/hpma_debug/
```

## Dense Frame Extraction For Outer Circle b

The first sparse extraction was too coarse for `b`: one frame might show no outer circle, while the next sampled frame already shows `b` smaller than `a`.

The video is 60 fps, so for annotating `b`, extract a dense time window.

The currently useful annotated target-circle region is roughly:

```text
11.5s - 23.5s
```

Run:

```bash
python scripts/process_video.py \
  --video "/Users/<you>/Videos/hpma.mp4" \
  --dense-start-seconds 11.5 \
  --dense-until-seconds 23.5 \
  --dense-step-frames 1 \
  --max-debug-frames 160
```

This keeps a sparse overview of the full video and extracts every frame in the 11.5s - 23.5s segment.

Expected dense segment:

```text
hpma_f000690_t011.500.png
hpma_f000691_t011.517.png
...
hpma_f001410_t023.500.png
```

There are about 721 frames in that dense segment.

If processing is slow on the MacBook, use one of these lighter options:

```bash
python scripts/process_video.py \
  --video "/Users/<you>/Videos/hpma.mp4" \
  --dense-start-seconds 11.5 \
  --dense-until-seconds 23.5 \
  --dense-step-frames 2 \
  --max-debug-frames 80
```

or:

```bash
python scripts/process_video.py \
  --video "/Users/<you>/Videos/hpma.mp4" \
  --dense-start-seconds 11.5 \
  --dense-until-seconds 16.0 \
  --dense-step-frames 1 \
  --max-debug-frames 80
```

## Manual Annotation Workflow

The annotation tool opens frame images and writes circle coordinates to CSV.

It displays the cropped coordinate system used by the detector. This is important: the annotation coordinates match the detector coordinates after `video.input_crop`.

### Annotating target circle a

Target circle `a` is the fixed inner target circle. It does not shrink.

Run:

```bash
python scripts/annotate_circles.py \
  --output data/annotations/hpma_manual_circles.csv \
  --state target_inner \
  --scale 0.4
```

Mouse/keyboard controls:

```text
left click 1: circle center
left click 2: circle edge
n: next frame
p: previous frame
u: undo last annotation on current image
q or Esc: quit
```

For target circle `a`, click:

1. The center of `a`.
2. The edge of `a`.

### Annotating outer shrinking circle b

Outer circle `b` is the moving/shrinking circle. This is what we need for click prediction.

Run:

```bash
python scripts/annotate_circles.py \
  --output data/annotations/hpma_manual_outer_circles.csv \
  --state shrinking_outer \
  --start hpma_f000690_t011.500.png \
  --scale 0.4
```

For outer circle `b`, click:

1. The same center as the target circle.
2. The outer shrinking ring edge.

Do not try to annotate every frame. Instead, for the same circle, annotate a few moments:

```text
b is large
b is midway
b is close to a
```

A useful first batch would be:

```text
30 - 50 annotations of b
```

Prefer consecutive frames for the same circle when possible, because we need radius-over-time behavior.

Example sequence:

```text
hpma_f001080_t018.000.png
hpma_f001090_t018.167.png
hpma_f001100_t018.333.png
hpma_f001110_t018.500.png
```

If `b` is already smaller than `a`, skip that frame. That is already too late for click prediction.

## CSV Formats

Manual annotations use:

```csv
image,x,y,outer_radius,color,state,notes
```

For `a`, `outer_radius` currently means the radius of the fixed target circle.

For `b`, `outer_radius` means the radius of the outer shrinking circle.

Use `state` to distinguish them:

```text
target_inner
shrinking_outer
```

Detection output:

```text
data/annotations/hpma_detections.csv
```

Columns:

```csv
frame,time_s,detection_index,x,y,radius,confidence
```

Track output:

```text
data/annotations/hpma_tracks.csv
```

Columns:

```csv
track_id,observations,first_time_s,last_time_s,duration_s,latest_x,latest_y,first_radius,last_radius,shrink_speed_px_s
```

## Current Detector Behavior

The current detector uses HSV color ranges for bright blue and gold circles, then uses Hough circles and a ring-score filter.

It can detect real circles, but there are still false positives from:

```text
fireplace flames
bright character faces
hair highlights
window highlights
gold UI effects
```

This is expected at this stage.

The next useful improvement is not more blind parameter tuning. It is to compare:

```text
manual annotations of a and b
vs
automatic detections
```

Then tune or filter based on actual precision/recall.

## Recommended Next Coding Step

After enough `b` annotations exist, add an evaluation script:

```text
scripts/evaluate_annotations.py
```

It should:

1. Load manual CSV annotations.
2. Load automatic detections.
3. Match detections to annotations by center distance and radius error.
4. Report:
   - true positives
   - false positives
   - missed circles
   - radius error
   - center error
5. Separate metrics for `target_inner` and `shrinking_outer`.

Suggested matching thresholds:

```text
center distance <= 40 px for 2560 video crop coordinates
radius error <= 30 px for b
radius error <= 15 px for a
```

Then use the result to improve:

```text
detector.hsv_ranges
detector.min_ring_score
detector.hough_param2
tracker.max_center_distance
tracker.min_shrink_speed
timing.target_radius
```

## Suggested Tomorrow Plan

1. Clone or copy the repo to the MacBook.
2. Create the conda environment.
3. Transfer the latest `hpma.mp4`.
4. Transfer `hpma_manual_circles.csv` if you want to keep today's target-circle labels.
5. Run `process_video.py` with dense extraction for 11.5s - 23.5s.
6. Annotate 30 - 50 outer circle `b` samples into `hpma_manual_outer_circles.csv`.
7. Add or run an evaluation script to compare manual labels against automatic detections.
8. Tune detector/tracker based on measured errors.

## Quick Commands

Setup:

```bash
conda env create -f environment.yml
conda activate prom-recognition
python -m pytest -q
```

Process video:

```bash
python scripts/process_video.py --video "/Users/<you>/Videos/hpma.mp4"
```

Dense extraction:

```bash
python scripts/process_video.py \
  --video "/Users/<you>/Videos/hpma.mp4" \
  --dense-start-seconds 11.5 \
  --dense-until-seconds 23.5 \
  --dense-step-frames 1 \
  --max-debug-frames 160
```

Annotate target circle `a`:

```bash
python scripts/annotate_circles.py \
  --output data/annotations/hpma_manual_circles.csv \
  --state target_inner \
  --scale 0.4
```

Annotate shrinking circle `b`:

```bash
python scripts/annotate_circles.py \
  --output data/annotations/hpma_manual_outer_circles.csv \
  --state shrinking_outer \
  --start hpma_f000690_t011.500.png \
  --scale 0.4
```

