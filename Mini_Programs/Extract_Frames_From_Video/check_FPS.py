from moviepy import VideoFileClip


def check_fps_moviepy(video_path):
    try:
        # We use 'with' to ensure the file opens and closes cleanly
        with VideoFileClip(video_path) as clip:
            fps = clip.fps
            duration = clip.duration
            print(f"--- VIDEO INFO ---")
            print(f"File: {video_path}")
            print(f"FPS: {fps}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"Total estimated frames: {int(fps * duration)}")

    except Exception as e:
        print(f"Error reading video: {e}")


# --- USAGE ---
check_fps_moviepy("Halo 2.webm")