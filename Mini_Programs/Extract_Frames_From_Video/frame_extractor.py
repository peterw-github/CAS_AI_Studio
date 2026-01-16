import subprocess
import os


def extract_frames_gpu(video_path, start_time, end_time, output_folder):
    """
    Extracts frames using FFMPEG with NVIDIA GPU acceleration (CUDA).
    This is significantly faster than MoviePy/CPU.
    """

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Calculate duration because FFMPEG -t takes duration, not end time
    duration = end_time - start_time

    # Construct the FFMPEG command
    # -hwaccel cuda: Uses your NVIDIA GPU for decoding
    # -ss: Start time
    # -t: Duration to capture
    # -vf fps=1: OPTIONAL - remove this part if you want ALL frames.
    #             Currently set to capture 1 image per second.
    # qscale:v 2: High quality jpg (1-31, 1 is best)

    command = [
        "ffmpeg",
        "-hwaccel", "cuda",  # Use NVIDIA GPU
        "-ss", str(start_time),  # Start second
        "-i", video_path,  # Input file
        "-t", str(duration),  # How long to extract
        "-vf", "fps=60",  # FILTER: 1 frame per second. Remove for all frames.
        "-qscale:v", "2",  # Quality (2 is excellent)
        os.path.join(output_folder, "frame_%04d.jpg")  # Output filename pattern
    ]

    print(f"🚀 Starting GPU extraction for {duration} seconds of video...")

    try:
        # Run the command and capture output to avoid spamming the console
        subprocess.run(command, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print(f"✅ Done! Check the '{output_folder}' folder.")
    except subprocess.CalledProcessError as e:
        print("❌ Error: FFMPEG failed. Make sure FFMPEG is installed and added to PATH.")
        print("Details:", e.stderr.decode())


# --- USAGE ---
extract_frames_gpu(
    video_path="Halo 2.webm",
    start_time=543,  # Start at 70 seconds
    end_time=549,  # End at 75 seconds
    output_folder="gpu_extracted_images"
)