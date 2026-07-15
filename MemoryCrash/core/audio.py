"""Runtime-generated game sounds with a safe no-audio fallback."""

from __future__ import annotations

from array import array
import math
from pathlib import Path
import random

import pygame


class AudioManager:
    SAMPLE_RATE = 22050

    def __init__(self) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.ambience_channel: pygame.mixer.Channel | None = None
        self.current_ambience: str | None = None
        try:
            pygame.mixer.init(frequency=self.SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self.enabled = True
            self.sounds = self._build_sounds()
            self.ambience_channel = pygame.mixer.Channel(0)
        except pygame.error:
            # Machines without an available output device can still run the game.
            pass

    def _sound(self, samples: list[float]) -> pygame.mixer.Sound:
        data = array("h", (int(max(-1.0, min(1.0, value)) * 32767) for value in samples))
        return pygame.mixer.Sound(buffer=data.tobytes())

    def _tone(self, duration: float, start: float, end: float, volume: float, noise: float = 0.0) -> list[float]:
        length = max(1, int(self.SAMPLE_RATE * duration))
        phase = 0.0
        values: list[float] = []
        for index in range(length):
            t = index / self.SAMPLE_RATE
            phase += math.tau * (start + (end - start) * index / length) / self.SAMPLE_RATE
            envelope = min(1.0, t * 45) * max(0.0, 1.0 - t / duration) ** 1.7
            values.append((math.sin(phase) + random.uniform(-noise, noise)) * envelope * volume)
        return values

    def _ambience(self, duration: float, pitches: tuple[float, ...], volume: float) -> list[float]:
        values: list[float] = []
        for index in range(int(self.SAMPLE_RATE * duration)):
            t = index / self.SAMPLE_RATE
            pulse = max(0.0, math.sin(math.tau * 1.8 * t)) ** 8
            voices = sum(math.sin(math.tau * pitch * t) for pitch in pitches) / len(pitches)
            values.append((voices * (0.18 + pulse * 0.45) + random.uniform(-0.45, 0.45) * 0.18) * volume)
        return values

    def _cough_ambience(self, duration: float) -> list[float]:
        """Make spaced, soft cough-like noise bursts for Level 1's outbreak."""
        values: list[float] = []
        cough_starts = (0.35, 1.15, 2.05, 2.8)
        for index in range(int(self.SAMPLE_RATE * duration)):
            t = index / self.SAMPLE_RATE
            burst = 0.0
            for start in cough_starts:
                age = t - start
                if 0.0 <= age < 0.20:
                    burst += math.sin(math.tau * (145 - age * 240) * t) * (1 - age / 0.20) ** 2
                    burst += random.uniform(-0.8, 0.8) * (1 - age / 0.20) ** 3
            values.append(burst * 0.13)
        return values

    def _build_sounds(self) -> dict[str, pygame.mixer.Sound]:
        sounds = {
            "button": self._sound(self._tone(0.055, 820, 540, 0.22)),
            "hit_light": self._sound(self._tone(0.09, 250, 95, 0.24, 0.10)),
            "hit_heavy": self._sound(self._tone(0.13, 150, 55, 0.42, 0.16)),
            "whoosh": self._sound(self._tone(0.18, 230, 1040, 0.20, 0.08)),
            "penalty_cheer": self._sound(self._ambience(1.35, (178, 224, 267), 0.60)),
            "ai_transform": self._sound(self._tone(1.1, 95, 1580, 0.34, 0.06) + self._tone(0.28, 720, 180, 0.20)),
            "covid_coughs": self._sound(self._cough_ambience(3.4)),
            "rogue_machines": self._sound(self._ambience(3.2, (72, 108, 151), 0.20) + self._tone(0.25, 950, 130, 0.18, 0.15)),
        }
        crowd_file = Path(__file__).resolve().parent.parent / "assets" / "Generate_a_seamless__#2-1784087027035.mp3"
        penalty_file = Path(__file__).resolve().parent.parent / "assets" / "air-horn-club-sample_heugSrA.mp3"
        rogue_file = Path(__file__).resolve().parent.parent / "assets" / "Fast,_hyper-dense_me_#3-1784088824912.mp3"
        try:
            sounds["stadium_chant"] = pygame.mixer.Sound(str(crowd_file))
            sounds["stadium_chant"].set_volume(0.72)
        except pygame.error:
            # Keep the game playable if the optional file is missing or invalid.
            sounds["stadium_chant"] = self._sound(self._ambience(3.8, (196, 247, 294), 0.28))
        try:
            sounds["penalty_cheer"] = pygame.mixer.Sound(str(penalty_file))
            sounds["penalty_cheer"].set_volume(0.78)
        except pygame.error:
            pass
        try:
            sounds["rogue_machines"] = pygame.mixer.Sound(str(rogue_file))
            sounds["rogue_machines"].set_volume(0.60)
        except pygame.error:
            pass
        return sounds

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def set_combat_ambience(self, level_index: int, *, rebel: bool = False) -> None:
        name = "rogue_machines" if rebel else {1: "covid_coughs", 2: "stadium_chant"}.get(level_index)
        if name == self.current_ambience:
            return
        self.stop_ambience()
        self.current_ambience = name
        if self.enabled and name and self.ambience_channel:
            self.ambience_channel.play(self.sounds[name], loops=-1)

    def pause_ambience(self) -> None:
        if self.enabled and self.ambience_channel:
            self.ambience_channel.pause()

    def resume_ambience(self) -> None:
        if self.enabled and self.current_ambience and self.ambience_channel:
            self.ambience_channel.unpause()

    def stop_ambience(self) -> None:
        if self.enabled and self.ambience_channel:
            self.ambience_channel.stop()
        self.current_ambience = None

    def stop_all(self) -> None:
        """Silence effects and ambience when gameplay has fully ended."""
        if self.enabled:
            pygame.mixer.stop()
        self.current_ambience = None
