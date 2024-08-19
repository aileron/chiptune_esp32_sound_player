# import module
import machine
import time
import json
import random
import utime


# Functions creating Noise
class SimpleNoiseGenerator:
    
    ## Variables initialization
    def __init__(self, pin_number):
        self.noise_pin = machine.PWM(machine.Pin(pin_number))
        self.timer = machine.Timer(-1)
        self.is_on = False
    
    ## Noise updater function
    def _update_noise(self, timer):
        if self.is_on:
            random_value = random.randint(0, 1023)
            self.noise_pin.duty(random_value)

    ## Noise setting function
    def set_noise(self, frequency):
        if frequency == 0:
            self.stop()
        else:
            self.is_on = True
            self.timer.init(freq=frequency, mode=machine.Timer.PERIODIC, callback=self._update_noise)

    ## Noise stopper function
    def stop(self):
        self.is_on = False
        self.timer.deinit()
        self.noise_pin.duty(0)


# Functions playing musics
class GameMusicPlayer:
    
    ## Variables initialization
    def __init__(self, current_song_index, pulse1_pin, pulse2_pin, triangle_pin, noise_pin):
        self.noise_gen = SimpleNoiseGenerator(noise_pin)
        self.pulse1 = machine.PWM(machine.Pin(pulse1_pin))
        self.pulse2 = machine.PWM(machine.Pin(pulse2_pin))
        self.triangle = machine.PWM(machine.Pin(triangle_pin))
        
        self.songs = []
        self.current_song_index = current_song_index
        self.current_note = 0
        self.timer = machine.Timer(0)
    
    ## Songs loader function
    def load_songs(self, filenames):
        for filename in filenames:
            with open(filename, 'r') as f:
                self.songs.append(json.load(f))
        print(f"Loaded {len(self.songs)} songs.")
    
    ## Pulse setting function
    def set_pulse(self, pwm, freq, duty=512):
        if freq == 0:
            pwm.duty(0)
        else:
            pwm.freq(freq)
            pwm.duty(duty)
    
    ## Triangle creator function
    def set_triangle(self, freq):
        if freq == 0:
            self.triangle.duty(0)
        else:
            self.triangle.freq(freq)
            self.triangle.duty(512)
    
    ## Noise setting function
    def set_noise(self, frequency):
        self.noise_gen.set_noise(frequency)
        
    ## note reader function
    def play_note(self, timer):
        song = self.songs[self.current_song_index]
        if self.current_note < len(song['notes']):
            chord = song['notes'][self.current_note]
            
            self.set_pulse(self.pulse1, chord['pulse1'])
            self.set_pulse(self.pulse2, chord['pulse2'])
            self.set_triangle(chord['triangle'])
            self.set_noise(chord['noise'])
            
            self.current_note += 1
        else:
            self.current_note = 0

    ## playback starting function
    def start_playback(self):
        song = self.songs[self.current_song_index]
        tempo = song['tempo']
        timer_period = int(60000 / (tempo * 4))  # 16分音符単位
        self.timer.init(period=timer_period, mode=machine.Timer.PERIODIC, callback=self.play_note)
        print(f"Now playing: {song['song_name']}")
        print(f"Tempo: {tempo} BPM")

    ## playback stopping function
    def stop_playback(self):
        self.timer.deinit()
        self.pulse1.deinit()
        self.pulse2.deinit()
        self.triangle.deinit()
        self.noise_gen.stop()
       

# Functions that will observe buttons
class ButtonObserver:
    
    ## Variable initialization
    def __init__(self, songs, button_pin, change_pin, debounce_ms=300):
        self.songs = songs
        self.current_song_index = 0
        self.led = machine.Pin(0, machine.Pin.OUT)
        self.button = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.button.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.handler)
        self.change_button = machine.Pin(change_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.change_button.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.change_handler)
        
        self.player = None
        self.debounce_ms = debounce_ms
        self.state = 1
        self.last_trigger_time = None
        self.last_change_trigger_time = None
        
    ## Play/stop button handler function
    def handler(self, pin):
        new_state = pin.value()
        current_time = utime.ticks_ms()
        if utime.ticks_diff(current_time, self.last_trigger_time) > self.debounce_ms:
            if new_state != self.state:
                self.state = new_state
                self.last_trigger_time = current_time
                self.toggle_song()
        
    ## Changing button handler function
    def change_handler(self, pin):
        new_state = pin.value()
        current_time = utime.ticks_ms()
        if utime.ticks_diff(current_time, self.last_change_trigger_time) > self.debounce_ms:
            if new_state != self.state:
                self.state = new_state
                self.last_change_trigger_time = current_time
                self.change_song()
    
    ## Song changer function
    def change_song(self):
        self.stop_if_playing()
        self.current_song_index = (self.current_song_index + 1) % len(self.songs)
        self.start()
    
    ## Songs toggler function
    def toggle_song(self):
        if self.player != None:
            print("toggle_song:stop")
            self.stop_if_playing()
        else:
            print("toggle_song:start")
            self.start()
    
    ## Function that will stop Music if it was still playing
    def stop_if_playing(self):
        print("stop-----------")
        if self.player != None:
            self.led.value(0)
            self.player.stop_playback()
            self.player = None
            time.sleep(0.5)
           
    ## Function that will play Music
    def start(self):
        print("start----------")
        self.led.value(1)
        self.player = GameMusicPlayer(
            current_song_index=self.current_song_index,
            pulse1_pin=12,
            pulse2_pin=14,
            triangle_pin=27,
            noise_pin=26
        )
        self.player.load_songs(self.songs)
        self.player.start_playback()

# Main Program
def main():
    songs = ['pixel.json', 'rpg.json', 'megalovania.json']
    button_observer = ButtonObserver(button_pin=2, change_pin=19, songs=songs)
    button_observer.led.value(0)
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        button_observer.stop_if_playing()
        button_observer.led.value(0)
        print("Playback stopped.")

if __name__ == "__main__":
    main()