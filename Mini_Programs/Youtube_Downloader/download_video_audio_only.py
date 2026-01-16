import yt_dlp

def download_audio(video_url):
    # Options for downloading
    ydl_opts = {
        'format': 'bestaudio/best',  # Download best available audio quality
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3', # Convert to mp3
            'preferredquality': '192', # Audio quality (192 kbps)
        }],
        'outtmpl': '%(title)s.%(ext)s', # Save file as "Video Title.mp3"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading audio from: {video_url}")
            ydl.download([video_url])
            print("Download complete!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Replace this string with your specific YouTube URL
    url = input("Enter the YouTube URL: ")
    download_audio(url)