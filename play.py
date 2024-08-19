import json
import numpy as np
import sounddevice as sd
import threading
import time
import argparse
import signal
import sys

class ChiptunePlayer:
    def __init__(self, json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        self.song_name = data['song_name']
        self.tempo = data['tempo']
        self.notes = data['notes']
        
        self.sample_rate = 44100
        self.channels = ['pulse1', 'pulse2', 'triangle', 'noise']
        self.audio_buffers = {channel: np.zeros(0) for channel in self.channels}
        self.current_note = 0
        self.is_playing = False
        self.stream = None
        self.threads = []

    def generate_square_wave(self, frequency, duration):
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = np.sign(np.sin(2 * np.pi * frequency * t))
        return wave * 0.3

    def generate_triangle_wave(self, frequency, duration):
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = 2 * np.abs(2 * (t * frequency - np.floor(0.5 + t * frequency))) - 1
        return wave * 0.3

    def generate_noise(self, duration):
        return np.random.uniform(-0.1, 0.1, int(self.sample_rate * duration))

    def generate_audio(self, channel):
        note_duration = 60 / self.tempo
        while self.is_playing:
            if self.current_note < len(self.notes):
                note = self.notes[self.current_note]
                frequency = note[channel]
                
                if channel in ['pulse1', 'pulse2']:
                    wave = self.generate_square_wave(frequency, note_duration)
                elif channel == 'triangle':
                    wave = self.generate_triangle_wave(frequency, note_duration)
                else:  # noise
                    wave = self.generate_noise(note_duration)
                
                self.audio_buffers[channel] = np.concatenate([self.audio_buffers[channel], wave])
            
            time.sleep(note_duration)

    def play_audio(self):
        def callback(outdata, frames, time, status):
            if status:
                print(status)
            
            chdata = []
            for channel in self.channels:
                if len(self.audio_buffers[channel]) < frames:
                    chdata.append(np.zeros(frames))
                else:
                    chdata.append(self.audio_buffers[channel][:frames])
                    self.audio_buffers[channel] = self.audio_buffers[channel][frames:]
            
            outdata[:] = np.sum(chdata, axis=0).reshape(-1, 1)

        self.stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, callback=callback)
        with self.stream:
            print(f"Now playing: {self.song_name}")
            print(f"Tempo: {self.tempo} BPM")
            print("Press Ctrl+C to stop playback")
            while self.is_playing:
                sd.sleep(100)

    def play(self):
        self.is_playing = True
        for channel in self.channels:
            thread = threading.Thread(target=self.generate_audio, args=(channel,))
            thread.start()
            self.threads.append(thread)
        
        self.play_audio()

    def stop(self):
        print("\nStopping playback...")
        self.is_playing = False
        if self.stream:
            self.stream.stop()
        for thread in self.threads:
            thread.join()
        print("Playback stopped.")

def signal_handler(sig, frame):
    print("\nCtrl+C pressed. Stopping playback...")
    if player:
        player.stop()
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play a chiptune from JSON file")
    parser.add_argument("json_file", help="Path to the JSON file containing the chiptune data")
    args = parser.parse_args()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    player = ChiptunePlayer(args.json_file)
    try:
        player.play()
    except Exception as e:
        print(f"An error occurred: {e}")
        player.stop()