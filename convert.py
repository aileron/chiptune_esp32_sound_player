import mido
import csv
import argparse

def midi_note_to_freq(note):
    return round(440 * (2 ** ((note - 69) / 12)))

def midi_to_csv(midi_file, max_file_size=50000):  # max_file_size in bytes
    mid = mido.MidiFile(midi_file)
    
    song_name = midi_file.split('/')[-1].split('.')[0]
    tempo = 120
    notes = []

    # Find the first track with notes
    melody_track = next((track for track in mid.tracks if any(msg.type == 'note_on' for msg in track)), None)
    
    if melody_track is None:
        raise ValueError("No melody track found in MIDI file")

    current_time = 0
    active_notes = {}
    for msg in melody_track:
        current_time += msg.time
        
        if msg.type == 'set_tempo':
            tempo = round(mido.tempo2bpm(msg.tempo))
        
        elif msg.type == 'note_on' and msg.velocity > 0:
            freq = midi_note_to_freq(msg.note)
            active_notes[msg.note] = (freq, current_time)
        
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in active_notes:
                start_freq, start_time = active_notes[msg.note]
                duration = current_time - start_time
                if duration > 0:
                    notes.append([start_freq, 0, 0, 0, round(duration)])
                del active_notes[msg.note]

    # Create CSV content
    csv_content = f"{song_name},{tempo}\n"
    csv_content += "pulse1,pulse2,triangle,noise,duration\n"
    for note in notes:
        csv_content += ",".join(map(str, note)) + "\n"

    # Check file size and reduce notes if necessary
    if len(csv_content.encode('utf-8')) > max_file_size:
        reduction_factor = max_file_size / len(csv_content.encode('utf-8'))
        notes = notes[::int(1/reduction_factor)]
        csv_content = f"{song_name},{tempo}\n"
        csv_content += "pulse1,pulse2,triangle,noise,duration\n"
        for note in notes:
            csv_content += ",".join(map(str, note)) + "\n"

    return csv_content

def main():
    parser = argparse.ArgumentParser(description="Convert MIDI to optimized CSV")
    parser.add_argument("input_file", help="Input MIDI file")
    parser.add_argument("output_file", help="Output CSV file")
    args = parser.parse_args()

    result = midi_to_csv(args.input_file)
    
    with open(args.output_file, 'w', newline='') as f:
        f.write(result)
    
    print(f"Conversion complete. Output saved to {args.output_file}")
    print(f"File size: {len(result.encode('utf-8'))} bytes")

if __name__ == "__main__":
    main()