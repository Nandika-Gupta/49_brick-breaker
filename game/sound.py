import array
import math
import pygame

# Sound effects are synthesized at startup, so no audio files are needed.
# (name -> list of note frequencies in Hz, seconds per note)
EFFECTS = {
    "brick": ([880], 0.06),
    "paddle": ([440], 0.06),
    "wall": ([300], 0.04),
    "win": ([523, 659, 784, 1047], 0.12),
    "lose": ([392, 330, 262, 196], 0.15),
}

class SoundFX:
    def __init__(self, volume=0.3):
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            rate, size, channels = pygame.mixer.get_init()
        except pygame.error:
            return  # No audio device: play silently.
        if size != -16:
            return  # Tones are generated as signed 16-bit samples.
        for name, (notes, note_len) in EFFECTS.items():
            self.sounds[name] = self._tone(notes, note_len, rate, channels, volume)

    @staticmethod
    def _tone(notes, note_len, rate, channels, volume):
        samples = array.array("h")
        n = int(rate * note_len)
        for freq in notes:
            for i in range(n):
                fade = 1 - i / n  # Fade out each note to avoid clicks.
                value = int(32767 * volume * fade * math.sin(2 * math.pi * freq * i / rate))
                samples.extend([value] * channels)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        sound = self.sounds.get(name)
        if sound:
            sound.play()
