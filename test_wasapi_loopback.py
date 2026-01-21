"""
Test script for WASAPI loopback audio capture.

This tests whether pyaudiowpatch is working correctly for 
capturing system audio (what you hear).

Install: pip install pyaudiowpatch
"""

def test_loopback():
    print("=" * 50)
    print("WASAPI Loopback Audio Test")
    print("=" * 50)
    print()
    
    # Step 1: Check if pyaudiowpatch is installed
    try:
        import pyaudiowpatch as pyaudio
        print("[OK] pyaudiowpatch is installed")
    except ImportError:
        print("[ERROR] pyaudiowpatch is NOT installed")
        print("       Run: pip install pyaudiowpatch")
        return False
    
    # Step 2: Check WASAPI availability
    p = pyaudio.PyAudio()
    
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        print(f"[OK] WASAPI available (index: {wasapi_info['index']})")
    except OSError:
        print("[ERROR] WASAPI not available on this system")
        p.terminate()
        return False
    
    # Step 3: Find default output device
    default_output_index = wasapi_info["defaultOutputDevice"]
    default_output = p.get_device_info_by_index(default_output_index)
    print(f"[OK] Default output: {default_output['name']}")
    
    # Step 4: Find loopback device
    loopback_device = None
    loopback_index = None
    
    print()
    print("Searching for loopback devices...")
    
    for i in range(p.get_device_count()):
        device = p.get_device_info_by_index(i)
        
        # Check for loopback flag (pyaudiowpatch specific)
        if device.get("isLoopbackDevice", False):
            print(f"  [{i}] {device['name']} (LOOPBACK)")
            if loopback_device is None:
                loopback_device = device
                loopback_index = i
    
    if loopback_device is None:
        print("[ERROR] No loopback devices found!")
        print("        This might mean pyaudiowpatch is not compiled with loopback support.")
        p.terminate()
        return False
    
    print()
    print(f"[OK] Using loopback device: {loopback_device['name']}")
    print(f"     Sample rate: {int(loopback_device['defaultSampleRate'])}")
    print(f"     Channels: {loopback_device['maxInputChannels']}")
    
    # Step 5: Test recording
    print()
    print("=" * 50)
    print("Recording 3 seconds of system audio...")
    print("PLAY SOME AUDIO ON YOUR COMPUTER NOW!")
    print("=" * 50)
    
    import time
    import wave
    import os
    
    sample_rate = int(loopback_device['defaultSampleRate'])
    channels = loopback_device['maxInputChannels']
    audio_data = []
    
    def callback(in_data, frame_count, time_info, status):
        audio_data.append(in_data)
        return (None, pyaudio.paContinue)
    
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=loopback_index,
            frames_per_buffer=1024,
            stream_callback=callback
        )
        
        stream.start_stream()
        time.sleep(3)
        stream.stop_stream()
        stream.close()
        
        print()
        print(f"[OK] Captured {len(audio_data)} audio chunks")
        
        # Save to file
        os.makedirs("ambient_temp", exist_ok=True)
        filepath = "ambient_temp/test_loopback.wav"
        
        audio_bytes = b''.join(audio_data)
        
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_bytes)
        
        file_size = os.path.getsize(filepath)
        duration = len(audio_bytes) / (sample_rate * channels * 2)
        
        print(f"[OK] Saved to: {filepath}")
        print(f"     Duration: {duration:.1f}s")
        print(f"     Size: {file_size / 1024:.1f} KB")
        
        if file_size < 1000:
            print()
            print("[WARNING] File is very small - may be silent!")
            print("          Make sure audio was playing during recording.")
        
        p.terminate()
        return True
        
    except Exception as e:
        print(f"[ERROR] Recording failed: {e}")
        import traceback
        traceback.print_exc()
        p.terminate()
        return False


if __name__ == "__main__":
    success = test_loopback()
    print()
    print("=" * 50)
    if success:
        print("TEST PASSED - WASAPI loopback is working!")
    else:
        print("TEST FAILED - See errors above")
    print("=" * 50)
