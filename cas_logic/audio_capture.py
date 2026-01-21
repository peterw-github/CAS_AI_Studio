"""
Audio capture for CAS ambient mode.

Records system audio via WASAPI loopback for the ambient context feature.
Uses pyaudiowpatch (PyAudio fork with WASAPI loopback support).

Install with: pip install pyaudiowpatch
"""

import os
import threading
import time
import wave
import struct

import cas_config as cfg


class AudioRecorder:
    """
    Background audio recorder using WASAPI loopback.
    
    Records what you hear (system audio output) rather than microphone input.
    
    Usage:
        recorder = AudioRecorder()
        recorder.start()
        time.sleep(30)
        filepath = recorder.stop()  # Returns path to saved file
    """
    
    def __init__(self):
        self._recording = False
        self._audio_data = []
        self._stream = None
        self._pyaudio = None
        self._thread = None
        self._lock = threading.Lock()
        
        # Audio settings (will be set from device)
        self._sample_rate = 44100
        self._channels = 2
        self._sample_width = 2  # 16-bit
    
    def _find_loopback_device(self):
        """
        Find the WASAPI loopback device for the default output.
        
        Returns (device_index, device_info) or (None, None) if not found.
        """
        try:
            import pyaudiowpatch as pyaudio
            
            p = pyaudio.PyAudio()
            
            # Get default WASAPI output device
            try:
                wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            except OSError:
                print("[AUDIO] WASAPI not available on this system")
                p.terminate()
                return None, None
            
            # Get the default output device for WASAPI
            default_output_index = wasapi_info["defaultOutputDevice"]
            default_output = p.get_device_info_by_index(default_output_index)
            
            print(f"[AUDIO] Default output: {default_output['name']}")
            
            # Find the loopback device for this output
            # Loopback devices have the same name but with input channels
            for i in range(p.get_device_count()):
                device = p.get_device_info_by_index(i)
                
                # Check if it's a loopback device:
                # - Same host API (WASAPI)
                # - Has input channels (for recording)
                # - Is marked as loopback device
                if (device["hostApi"] == wasapi_info["index"] and
                    device.get("isLoopbackDevice", False)):
                    
                    print(f"[AUDIO] Found loopback device [{i}]: {device['name']}")
                    p.terminate()
                    return i, device
            
            # Fallback: look for device with matching name
            for i in range(p.get_device_count()):
                device = p.get_device_info_by_index(i)
                
                if (device["hostApi"] == wasapi_info["index"] and
                    device["maxInputChannels"] > 0 and
                    default_output["name"] in device["name"]):
                    
                    print(f"[AUDIO] Found matching device [{i}]: {device['name']}")
                    p.terminate()
                    return i, device
            
            print("[AUDIO] No loopback device found")
            p.terminate()
            return None, None
            
        except ImportError:
            print("[AUDIO ERROR] pyaudiowpatch not installed. Run: pip install pyaudiowpatch")
            return None, None
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to find loopback device: {e}")
            return None, None
    
    def start(self) -> bool:
        """
        Start recording in background.
        
        Returns True if started successfully.
        """
        if self._recording:
            print("[AUDIO] Already recording!")
            return False
        
        try:
            import pyaudiowpatch as pyaudio
            
            # Find loopback device
            device_index, device_info = self._find_loopback_device()
            
            if device_index is None:
                print("[AUDIO ERROR] Could not find loopback device")
                return False
            
            # Get device settings
            self._sample_rate = int(device_info["defaultSampleRate"])
            self._channels = device_info["maxInputChannels"]
            
            # Initialize PyAudio
            self._pyaudio = pyaudio.PyAudio()
            self._audio_data = []
            self._recording = True
            
            # Open stream
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self._channels,
                rate=self._sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024,
                stream_callback=self._audio_callback
            )
            
            self._stream.start_stream()
            
            print(f"[AUDIO] Recording started (rate={self._sample_rate}, channels={self._channels})")
            return True
            
        except ImportError:
            print("[AUDIO ERROR] pyaudiowpatch not installed. Run: pip install pyaudiowpatch")
            self._recording = False
            return False
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to start: {e}")
            self._recording = False
            return False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Called by PyAudio for each audio chunk."""
        import pyaudiowpatch as pyaudio
        
        if status:
            print(f"[AUDIO] Stream status: {status}")
        
        with self._lock:
            if self._recording:
                self._audio_data.append(in_data)
        
        return (None, pyaudio.paContinue)
    
    def stop(self, output_dir: str = None) -> str:
        """
        Stop recording and save to file.
        
        Args:
            output_dir: Directory to save file (default: temp dir)
        
        Returns:
            Path to saved audio file, or None on failure
        """
        if not self._recording:
            print("[AUDIO] Not currently recording!")
            return None
        
        try:
            # Stop recording
            self._recording = False
            
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
            
            if self._pyaudio:
                self._pyaudio.terminate()
                self._pyaudio = None
            
            # Combine audio chunks
            with self._lock:
                if not self._audio_data:
                    print("[AUDIO] No audio data captured!")
                    return None
                
                audio_bytes = b''.join(self._audio_data)
                self._audio_data = []
            
            # Determine output path
            if output_dir is None:
                output_dir = getattr(cfg, 'AMBIENT_TEMP_DIR', 'ambient_temp')
            
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"ambient_audio_{timestamp}.wav")
            
            # Save to WAV file
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self._channels)
                wf.setsampwidth(self._sample_width)
                wf.setframerate(self._sample_rate)
                wf.writeframes(audio_bytes)
            
            duration = len(audio_bytes) / (self._sample_rate * self._channels * self._sample_width)
            print(f"[AUDIO] Saved {duration:.1f}s audio to {filepath}")
            
            return filepath
            
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to stop/save: {e}")
            import traceback
            traceback.print_exc()
            self._recording = False
            return None
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording
    
    def cancel(self):
        """Cancel recording without saving."""
        self._recording = False
        
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
            self._stream = None
        
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except:
                pass
            self._pyaudio = None
        
        with self._lock:
            self._audio_data = []
        
        print("[AUDIO] Recording cancelled.")


# Convenience function for simple use
def record_audio(duration: float, output_dir: str = None) -> str:
    """
    Record audio for specified duration (blocking).
    
    Returns path to saved file or None on failure.
    """
    recorder = AudioRecorder()
    
    if not recorder.start():
        return None
    
    time.sleep(duration)
    
    return recorder.stop(output_dir)


if __name__ == "__main__":
    print("--- Testing Audio Capture (WASAPI Loopback) ---")
    print("Recording 5 seconds of system audio...")
    print("Play some audio on your computer!")
    print()
    
    filepath = record_audio(5)
    
    if filepath:
        print(f"\nSuccess! Saved to: {filepath}")
    else:
        print("\nRecording failed. Make sure pyaudiowpatch is installed:")
        print("  pip install pyaudiowpatch")
