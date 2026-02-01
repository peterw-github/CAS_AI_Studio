import os
import subprocess


def process_folder_gpu():
    current_folder = os.getcwd()
    files = [f for f in os.listdir(current_folder) if f.endswith(".webm")]

    if not files:
        print("No .webm files found in this folder.")
        return

    print(f"Found {len(files)} .webm files. Starting GPU conversion with RTX 5070 Ti...\n")

    for filename in files:
        name_without_ext = os.path.splitext(filename)[0]
        output_filename = f"{name_without_ext}_1080p.mp4"

        if os.path.exists(output_filename):
            print(f"Skipping {filename} (Output file already exists)")
            continue

        print(f"Processing: {filename} -> {output_filename}")

        # GPU ACCELERATION COMMAND EXPLAINED:
        # -hwaccel cuda               : Uses the GPU to decode the input video (reads it fast)
        # -hwaccel_output_format cuda : Keeps the video data in VRAM (doesn't copy back to CPU)
        # -vf scale_cuda=-1:1080      : Resizes the video strictly using the GPU CUDA cores
        # -c:v h264_nvenc             : Uses the dedicated NVIDIA Encoder chip (NVENC)
        # -preset p4                  : NVENC Performance preset (p1=fastest, p7=highest quality, p4=balanced)
        # -cq 23                      : Constant Quality setting (approx equivalent to CRF)

        command = [
            'ffmpeg',
            '-hwaccel', 'cuda',
            '-hwaccel_output_format', 'cuda',
            '-i', filename,
            '-vf', 'scale_cuda=-1:1080',
            '-c:v', 'h264_nvenc',
            '-preset', 'p4',
            '-cq', '23',
            '-c:a', 'aac',
            output_filename
        ]

        try:
            subprocess.run(command, check=True)
            print(f"Finished: {filename}\n")

        except subprocess.CalledProcessError as e:
            print(f"Error converting {filename}: {e}\n")


if __name__ == "__main__":
    process_folder_gpu()
    print("All tasks completed.")