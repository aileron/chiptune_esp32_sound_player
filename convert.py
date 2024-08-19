import mido
import json
import math
import argparse
from pathlib import Path

def midi_note_to_freq(note):
    return int(round(440 * (2 ** ((note - 69) / 12))))

def convert_midi_to_chiptune(midi_file):
    mid = mido.MidiFile(midi_file)
    
    # Find the tempo
    tempo = 500000  # Default tempo (120 BPM)
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break
        if tempo != 500000:
            break
    
    bpm = int(round(60000000 / tempo))
    
    # Find the track with notes
    melody_track = None
    for track in mid.tracks:
        if any(msg.type == 'note_on' for msg in track):
            melody_track = track
            break
    
    if melody_track is None:
        raise ValueError("No melody track found in MIDI file")

    notes = []
    current_time = 0
    for msg in melody_track:
        current_time += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            freq = midi_note_to_freq(msg.note)
            notes.append({
                "pulse1": freq,
                "pulse2": 0,
                "triangle": 0,
                "noise": 0,
                "tick": int(current_time)
            })

    return {
        "song_name": Path(midi_file).stem,
        "tempo": bpm,
        "notes": notes
    }

def main():
    parser = argparse.ArgumentParser(description="Convert MIDI to Chiptune JSON")
    parser.add_argument("midi_file", help="Path to the input MIDI file")
    parser.add_argument("output_file", help="Path to the output JSON file")
    args = parser.parse_args()

    try:
        chiptune_data = convert_midi_to_chiptune(args.midi_file)
        
        with open(args.output_file, 'w') as f:
            json.dump(chiptune_data, f, indent=2)
        
        print(f"Conversion complete. Output saved to {args.output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()