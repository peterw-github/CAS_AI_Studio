# Video Frame Extraction Toolkit

This project contains Python scripts to inspect video files (specifically `.webm`, though others work too) and extract individual frames as images.

It includes two main capabilities:

1. **Frame Extraction:** Pulling every image (or a specific sampling) from a time range.
2. **FPS Checking:** Quickly analyzing a video's frame rate to plan your extraction.

## 🛠 Prerequisites

### 1. Python Libraries

You will need to install the following libraries. Open your terminal/command prompt and run:

```
pip install moviepy pillow opencv-python
```

### 2. FFMPEG (For GPU Acceleration)

To use the **GPU-accelerated** extraction (recommended for RTX 5070 Ti), you must have **FFmpeg** installed and added to your system PATH.

- **Download:** [FFmpeg.org](https://ffmpeg.org/download.html)
- *Note: If you only use the CPU (MoviePy) method, this is handled automatically by Python.*

## 📂 The Scripts

### 1. `check_fps.py` (Analyze Video)

Run this script first to see how many frames per second your video has. This helps you decide if you need to limit the output (e.g., if the video is 60fps, you might want to extract only 1 frame per second).

**Key Features:**

- Uses `moviepy` (slower, loads file) or `opencv` (instant, reads header).

### 2. `extract_frames.py` (The Main Tool)

This script extracts images from a specific start/end time. It contains two functions; choose the one that fits your needs.

#### Option A: CPU Extraction (MoviePy 2.0)

- **Best for:** Short clips, exact frame precision, or if you don't have FFmpeg installed system-wide.
- **Note:** Uses the modern `clip.subclipped()` syntax (fixing the old `subclip` error).

#### Option B: GPU Extraction (FFmpeg + CUDA)

- **Best for:** High-resolution video (4K/1080p), long clips, or leveraging your **NVIDIA RTX 5070 Ti**.
- **Speed:** 10x-20x faster than CPU.
- **Requirements:** Requires FFmpeg on system PATH and NVIDIA drivers.

## 🚀 Usage Guide

### Step 1: Check your video details

Open `check_fps.py` and edit the bottom line:

```
check_fps_moviepy("my_video.webm")
```

Run it in your terminal:

```
python check_fps.py
```

### Step 2: Extract Images

Open `extract_frames.py` and scroll to the bottom. Update the usage section:

```
# Select your method:

# METHOD 1: CPU (Slower, easier setup)
extract_frames_cpu(
    video_path="my_video.webm",
    start_time=70,  # 1 min 10 sec
    end_time=75,    # 1 min 15 sec
    output_folder="frames_cpu"
)

# OR

# METHOD 2: GPU (Fastest for RTX 5070 Ti)
extract_frames_gpu(
    video_path="my_video.webm",
    start_time=70,
    end_time=75,
    output_folder="frames_gpu"
)
```

Run the script:

```
python extract_frames.py
```

## ⚠️ Common Issues & Fixes

**Error: `AttributeError: 'VideoFileClip' object has no attribute 'subclip'`**

- **Cause:** You are using MoviePy 2.0+.
- **Fix:** Ensure your code uses `.subclipped(start, end)` instead of `.subclip(start, end)`.

**Error: `FileNotFoundError` (WinError 2)**

- **Cause:** FFmpeg is not found when running the GPU script.
- **Fix:** Ensure FFmpeg is installed and added to your Windows Environment Variables (PATH). Alternatively, use the CPU method.

**Error: `MemoryError` or Disk Full**

- **Cause:** Extracting high-FPS video without limiting frames (e.g., 60fps = 3,600 images per minute).
- **Fix:** In the GPU script, ensure `-vf fps=1` is included to only take 1 picture per second.