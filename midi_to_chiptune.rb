require 'midilib'
require 'json'

class MidiToChiptuneConverter
  TICKS_PER_BEAT = 480  # 一般的なMIDIファイルの分解能

  def initialize(midi_file)
    @midi_file = midi_file
    @seq = MIDI::Sequence.new()
    File.open(midi_file, 'rb') { |file| @seq.read(file) }
    @tempo = 120
    @notes = []
  end

  def convert
    extract_tempo
    extract_notes
    generate_json
  end

  private

  def extract_tempo
    @seq.each do |track|
      track.each do |event|
        if event.is_a?(MIDI::Tempo)
          @tempo = 60_000_000.0 / event.tempo
          return
        end
      end
    end
  end

  def extract_notes
    melody_track = find_melody_track
    return if melody_track.nil?

    current_tick = 0
    melody_track.each do |event|
      current_tick += event.delta_time
      if event.is_a?(MIDI::NoteOn) && event.velocity > 0
        frequency = midi_note_to_frequency(event.note)
        @notes << create_note_event(frequency, current_tick)
      end
    end
  end

  def find_melody_track
    @seq.tracks.find { |track| track.name != "Tempo Track" && track.events.any? { |e| e.is_a?(MIDI::NoteOn) } }
  end

  def midi_note_to_frequency(note)
    440.0 * (2 ** ((note - 69) / 12.0))
  end

  def create_note_event(frequency, tick)
    {
      "pulse1" => [frequency.round(2)],
      "pulse2" => [0],
      "triangle" => [0],
      "noise" => 0,
      "tick" => tick
    }
  end

  def generate_json
    {
      song_name: File.basename(@midi_file, '.*'),
      tempo: @tempo.round(2),
      ticks_per_beat: TICKS_PER_BEAT,
      notes: @notes
    }.to_json
  end
end

# 使用例
if ARGV.empty?
  puts "Usage: ruby midi_to_chiptune.rb <midi_file>"
  exit
end

begin
  converter = MidiToChiptuneConverter.new(ARGV[0])
  puts converter.convert
rescue => e
  puts "Error: #{e.message}"
  puts "Backtrace:"
  puts e.backtrace
  exit 1
end