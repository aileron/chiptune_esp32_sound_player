import json
import csv
import argparse

def json_to_csv(json_file, csv_file):
    # JSONファイルを読み込む
    with open(json_file, 'r') as f:
        data = json.load(f)

    # CSVファイルを書き込むためにオープン
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)

        # ヘッダー行を書き込む
        writer.writerow([data['song_name'], data['tempo']])
        writer.writerow(['pulse1', 'pulse2', 'triangle', 'noise', 'duration'])

        # ノートデータを書き込む
        current_note = None
        duration = 0
        for note in data['notes']:
            if current_note is None:
                current_note = note
                duration = 1
            elif note == current_note:
                duration += 1
            else:
                writer.writerow([
                    current_note['pulse1'],
                    current_note['pulse2'],
                    current_note['triangle'],
                    current_note['noise'],
                    duration
                ])
                current_note = note
                duration = 1

        # 最後のノートを書き込む
        if current_note is not None:
            writer.writerow([
                current_note['pulse1'],
                current_note['pulse2'],
                current_note['triangle'],
                current_note['noise'],
                duration
            ])

    print(f"Conversion complete. CSV file saved as {csv_file}")

def main():
    parser = argparse.ArgumentParser(description="Convert Chiptune JSON to CSV")
    parser.add_argument("input_file", help="Input JSON file")
    parser.add_argument("output_file", help="Output CSV file")
    args = parser.parse_args()

    json_to_csv(args.input_file, args.output_file)

if __name__ == "__main__":
    main()
