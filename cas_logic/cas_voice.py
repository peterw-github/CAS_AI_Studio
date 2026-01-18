"""
Text-to-Speech engine for CAS using VibeVoice/Gradio.
"""

import threading
import queue
import os
import re
import datetime
import importlib

import numpy as np
import sounddevice as sd
import soundfile as sf
from gradio_client import Client

import cas_config as cfg


class CASVoiceEngine:
    """
    Streaming TTS engine that:
    1. Connects to a Gradio VibeVoice endpoint
    2. Generates audio in chunks
    3. Plays audio via sounddevice
    4. Saves full audio to file
    """
    
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.playback_finished = threading.Event()
        self.client = None
        self.stream = None

        # Ensure output directories exist
        os.makedirs(cfg.OUTPUT_AUDIO_DIR, exist_ok=True)
        os.makedirs(cfg.OUTPUT_TEXT_DIR, exist_ok=True)

        # Start background playback thread
        self.thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.thread.start()

        # Connect to Gradio
        print(f"[VOICE] Connecting to VibeVoice at {cfg.VIBEVOICE_URL}...")
        try:
            self.client = Client(cfg.VIBEVOICE_URL)
            print("[VOICE] Connected.")
        except Exception as e:
            print(f"[VOICE] Connection failed (text-only mode): {e}")

    def _playback_loop(self):
        """Background thread for audio playback."""
        buffer = []
        BUFFER_SIZE = 2  # Buffer chunks before starting playback

        while not self.playback_finished.is_set():
            try:
                data, fs = self.audio_queue.get(timeout=0.5)
                buffer.append(data)

                # Wait for buffer to fill (unless queue is empty)
                if self.stream is None and len(buffer) < BUFFER_SIZE and not self.audio_queue.empty():
                    continue

                # Play buffered chunks
                while buffer:
                    chunk = buffer.pop(0)

                    # Initialize stream if needed
                    if self.stream is None:
                        try:
                            self.stream = sd.OutputStream(
                                samplerate=fs,
                                channels=chunk.shape[1] if len(chunk.shape) > 1 else 1,
                                dtype='float32'
                            )
                            self.stream.start()
                            print("[VOICE] Audio stream started.")
                        except Exception as e:
                            print(f"[VOICE] Stream init error: {e}")
                            continue

                    # Write to hardware
                    try:
                        self.stream.write(chunk)
                    except Exception as e:
                        print(f"[VOICE] Write error (recovering): {e}")
                        if self.stream:
                            self.stream.close()
                            self.stream = None

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[VOICE] Critical playback error: {e}")

    def _clean_text(self, text: str) -> str:
        """Clean text for TTS processing."""
        # Remove code blocks
        text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)

        # Collapse horizontal whitespace
        text = re.sub(r'[^\S\r\n]+', ' ', text)

        # Smart merge mode
        if getattr(cfg, 'VOICE_SMART_MERGE', False):
            text = text.replace('\r\n', '\n')
            text = re.sub(r'\n{4,}', '<<MAJOR_BREAK>>', text)
            text = re.sub(r'\n+', ' ', text)
            text = text.replace('<<MAJOR_BREAK>>', '\n\n')
        else:
            # Legacy paragraph spacing mode
            spacing = getattr(cfg, 'VOICE_PARAGRAPH_SPACING', 1)
            if spacing == 0:
                text = re.sub(r'\n+', ' ', text)
            else:
                replacement = "\n" * spacing
                text = re.sub(r'\n+', replacement, text)

        return text.strip()

    def _save_text_log(self, text: str):
        """Save cleaned text to file."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(cfg.OUTPUT_TEXT_DIR, f"speech_{timestamp}.md")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"[VOICE] Failed to save text log: {e}")

    def speak(self, text: str):
        """Generate and play speech from text."""
        # Hot reload config (no restart needed for setting changes)
        importlib.reload(cfg)

        if not self.client:
            return

        clean_text = self._clean_text(text)
        if not clean_text:
            return

        self._save_text_log(clean_text)
        print(f"[VOICE] Generating ({len(clean_text)} chars)...")

        # Generate in background thread
        t = threading.Thread(target=self._generate_and_queue, args=(clean_text,))
        t.start()

    def _generate_and_queue(self, text: str):
        """Generate TTS audio and queue for playback."""
        try:
            print(f"[VOICE] Speaker: '{cfg.VOICE_SPEAKER}' | CFG: {cfg.VOICE_CFG_SCALE}")
            
            job = self.client.submit(
                num_speakers=1,
                script=text,
                speaker_1=cfg.VOICE_SPEAKER,
                speaker_2="en-Frank_man",
                speaker_3=None,
                speaker_4=None,
                cfg_scale=cfg.VOICE_CFG_SCALE,
                disable_voice_cloning=cfg.DISABLE_CLONE,
                api_name="/generate_stream"
            )

            full_audio_buffer = []
            sample_rate = 24000
            chunk_count = 0

            for output_file in job:
                if output_file:
                    chunk_count += 1
                    data, fs = sf.read(output_file, dtype='float32')
                    sample_rate = fs

                    self.audio_queue.put((data, fs))
                    full_audio_buffer.append(data)
                    print(f"[VOICE] Chunk {chunk_count} ({len(data)} samples)")

            print(f"[VOICE] Complete. {chunk_count} chunks.")

            # Save full audio file
            if full_audio_buffer:
                full_audio = np.concatenate(full_audio_buffer)
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = os.path.join(cfg.OUTPUT_AUDIO_DIR, f"tts_{ts}.wav")
                sf.write(filepath, full_audio, sample_rate)

        except Exception as e:
            print(f"[VOICE] Generation error: {e}")

    def shutdown(self):
        """Signal the playback thread to stop."""
        self.playback_finished.set()
