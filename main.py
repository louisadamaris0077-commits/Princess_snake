import os
import math
import wave
import random
import struct
from array import array

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.utils import get_color_from_hex

Window.clearcolor = get_color_from_hex("#120B20")
SAMPLE_RATE = 22050


def create_music(path):
    """Create a short original Afro-inspired instrumental loop locally."""
    if os.path.exists(path):
        return

    duration = 9.6
    total = int(SAMPLE_RATE * duration)
    samples = array("f", [0.0]) * total

    def add_sound(start, length, fn):
        first = int(start * SAMPLE_RATE)
        count = min(int(length * SAMPLE_RATE), total - first)
        for i in range(max(0, count)):
            t = i / SAMPLE_RATE
            samples[first + i] += fn(t, length)

    beat = 60.0 / 100.0

    # Kick rhythm
    for b in range(16):
        def kick(t, length):
            freq = 105 - 65 * (t / length)
            return 0.62 * math.sin(2 * math.pi * freq * t) * math.exp(-16 * t)
        add_sound(b * beat, 0.22, kick)

    # Claps
    for b in range(16):
        if b % 2:
            def clap(t, length):
                return random.uniform(-1, 1) * 0.20 * math.exp(-24 * t)
            add_sound(b * beat, 0.14, clap)

    # Shakers
    for b in range(32):
        def shaker(t, length):
            return random.uniform(-1, 1) * 0.065 * math.exp(-12 * t)
        add_sound(b * beat / 2, 0.055, shaker)

    # Bass line
    notes = [55, 55, 65.4, 73.4, 55, 65.4, 49, 55]
    for b, freq in enumerate(notes):
        def bass(t, length, f=freq):
            return 0.22 * (
                math.sin(2 * math.pi * f * t)
                + 0.22 * math.sin(4 * math.pi * f * t)
            ) * math.exp(-2.7 * t)
        add_sound(b * beat * 2, 0.5, bass)

    # Bright original plucked melody
    melody = [261.63, 329.63, 392, 329.63, 293.66, 349.23, 440, 349.23]
    for b in range(16):
        freq = melody[b % len(melody)]
        def pluck(t, length, f=freq):
            return 0.10 * math.sin(2 * math.pi * f * t) * math.exp(-5 * t)
        add_sound(b * beat * 0.75, 0.32, pluck)

    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for value in samples:
            value = max(-0.95, min(0.95, value * 0.65))
            frames.extend(struct.pack("<h", int(value * 32767)))
        wav.writeframes(frames)


def create_effect(path, frequency=850):
    if os.path.exists(path):
        return
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for i in range(int(SAMPLE_RATE * 0.18)):
            t = i / SAMPLE_RATE
            value = 0.32 * math.sin(2 * math.pi * frequency * t) * math.exp(-18 * t)
            frames.extend(struct.pack("<h", int(value * 32767)))
        wav.writeframes(frames)


class SnakeBoard(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 20
        self.rows = 20
        self.cell = 15
        self.snake = []
        self.food = (5, 5)
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.running = False
        self.game_over = False
        self.paused = False
        self.speed = 0.15
        self.event = None
        self.touch_start = None

        self.message = Label(
            text="", font_size="22sp", bold=True,
            color=(1, 0.85, 0.55, 1),
            halign="center", valign="middle"
        )
        self.add_widget(self.message)
        self.bind(size=self.draw, pos=self.draw)
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.speed = 0.15
        cx, cy = self.cols // 2, self.rows // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.game_over = False
        self.paused = False
        self.running = True
        self.message.text = ""
        self.place_food()
        self.start_timer()
        self.draw()
        self.parent_app_update()

    def start_timer(self):
        if self.event:
            self.event.cancel()
        self.event = Clock.schedule_interval(self.update_game, self.speed)

    def place_food(self):
        available = [
            (x, y) for x in range(self.cols) for y in range(self.rows)
            if (x, y) not in self.snake
        ]
        if available:
            self.food = random.choice(available)

    def change_direction(self, direction):
        if self.game_over or self.paused:
            return
        if direction[0] + self.direction[0] == 0 and direction[1] + self.direction[1] == 0:
            return
        self.next_direction = direction

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_start = touch.pos
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.touch_start is not None:
            dx = touch.x - self.touch_start[0]
            dy = touch.y - self.touch_start[1]
            if max(abs(dx), abs(dy)) > dp(20):
                if abs(dx) > abs(dy):
                    self.change_direction((1, 0) if dx > 0 else (-1, 0))
                else:
                    self.change_direction((0, 1) if dy > 0 else (0, -1))
            self.touch_start = None
            return True
        return super().on_touch_up(touch)

    def update_game(self, dt):
        if not self.running or self.paused or self.game_over:
            return
        self.direction = self.next_direction
        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        if not (0 <= new_head[0] < self.cols and 0 <= new_head[1] < self.rows):
            self.end_game()
            return

        eating = new_head == self.food
        body = self.snake if eating else self.snake[:-1]
        if new_head in body:
            self.end_game()
            return

        self.snake.insert(0, new_head)
        if eating:
            self.score += 10
            self.play_effect()
            self.place_food()
            if self.score % 50 == 0:
                self.speed = max(0.065, self.speed - 0.008)
                self.start_timer()
        else:
            self.snake.pop()

        self.draw()
        self.parent_app_update()

    def parent_app_update(self):
        app = App.get_running_app()
        if app:
            app.update_score(self.score)

    def end_game(self):
        self.game_over = True
        self.running = False
        self.message.text = f"GAME OVER!\n\nYour score: {self.score}\n\nPress RESTART"
        app = App.get_running_app()
        if app:
            app.update_high_score(self.score)
        self.draw()

    def pause_game(self):
        if self.game_over:
            return
        self.paused = not self.paused
        self.message.text = "PAUSED\n\nPress RESUME" if self.paused else ""
        self.draw()

    def play_effect(self):
        app = App.get_running_app()
        if app and app.eat_sound:
            app.eat_sound.stop()
            app.eat_sound.play()

    def draw(self, *args):
        if self.width <= 0 or self.height <= 0:
            return
        self.canvas.clear()
        self.cell = min(self.width / self.cols, self.height / self.rows)
        board_w = self.cols * self.cell
        board_h = self.rows * self.cell
        ox = self.x + (self.width - board_w) / 2
        oy = self.y + (self.height - board_h) / 2

        with self.canvas:
            Color(*get_color_from_hex("#1B1030"))
            Rectangle(pos=self.pos, size=self.size)
            Color(*get_color_from_hex("#21143A"))
            Rectangle(pos=(ox, oy), size=(board_w, board_h))

            Color(0.5, 0.3, 0.65, 0.16)
            for x in range(self.cols + 1):
                xx = ox + x * self.cell
                Line(points=[xx, oy, xx, oy + board_h], width=0.5)
            for y in range(self.rows + 1):
                yy = oy + y * self.cell
                Line(points=[ox, yy, ox + board_w, yy], width=0.5)

            fx, fy = self.food
            Color(*get_color_from_hex("#FFD45C"))
            Ellipse(
                pos=(ox + fx * self.cell + self.cell * 0.12,
                     oy + fy * self.cell + self.cell * 0.12),
                size=(self.cell * 0.76, self.cell * 0.76)
            )

            for index, (sx, sy) in enumerate(self.snake):
                if index == 0:
                    Color(*get_color_from_hex("#FF72BC"))
                else:
                    Color(0.75, max(0.25, 0.55 - index * 0.008), 0.95, 1)
                Ellipse(
                    pos=(ox + sx * self.cell + self.cell * 0.06,
                         oy + sy * self.cell + self.cell * 0.06),
                    size=(self.cell * 0.88, self.cell * 0.88)
                )
                if index == 0:
                    Color(0.12, 0.05, 0.2, 1)
                    eye = self.cell * 0.12
                    Ellipse(pos=(ox + sx * self.cell + self.cell * 0.28,
                                 oy + sy * self.cell + self.cell * 0.62),
                            size=(eye, eye))
                    Ellipse(pos=(ox + sx * self.cell + self.cell * 0.63,
                                 oy + sy * self.cell + self.cell * 0.62),
                            size=(eye, eye))

        self.message.pos = self.pos
        self.message.size = self.size


class PrincessSnakeApp(App):
    def build(self):
        self.title = "Princess Snake"
        os.makedirs(self.user_data_dir, exist_ok=True)
        music_path = os.path.join(self.user_data_dir, "princess_afro.wav")
        effect_path = os.path.join(self.user_data_dir, "eat.wav")
        create_music(music_path)
        create_effect(effect_path)

        self.music = SoundLoader.load(music_path)
        self.eat_sound = SoundLoader.load(effect_path)
        self.high_score = 0

        if self.music:
            self.music.loop = True
            self.music.volume = 0.35
            self.music.play()

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        title = Label(
            text="[b][color=FF72BC]PRINCESS[/color] [color=FFD45C]SNAKE[/color][/b]  👑",
            markup=True, font_size="26sp",
            size_hint_y=None, height=dp(48)
        )
        root.add_widget(title)

        self.score_label = Label(
            text="SCORE: 0       BEST: 0",
            color=get_color_from_hex("#FFD45C"),
            bold=True, font_size="18sp",
            size_hint_y=None, height=dp(35)
        )
        root.add_widget(self.score_label)

        self.board = SnakeBoard()
        root.add_widget(self.board)

        instruction = Label(
            text="SWIPE YOUR FINGER TO MOVE THE SNAKE",
            color=get_color_from_hex("#E9B6FF"),
            font_size="13sp", size_hint_y=None, height=dp(30)
        )
        root.add_widget(instruction)

        buttons = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(8))

        pause_btn = Button(
            text="PAUSE", background_normal="",
            background_color=get_color_from_hex("#713EAA"),
            font_size="16sp", bold=True
        )
        pause_btn.bind(on_release=lambda *_: self.board.pause_game())

        restart_btn = Button(
            text="RESTART", background_normal="",
            background_color=get_color_from_hex("#D94B96"),
            font_size="16sp", bold=True
        )
        restart_btn.bind(on_release=lambda *_: self.restart_game())

        self.music_btn = Button(
            text="MUSIC ON", background_normal="",
            background_color=get_color_from_hex("#9C6B31"),
            font_size="15sp", bold=True
        )
        self.music_btn.bind(on_release=lambda *_: self.toggle_music())

        buttons.add_widget(pause_btn)
        buttons.add_widget(restart_btn)
        buttons.add_widget(self.music_btn)
        root.add_widget(buttons)
        return root

    def update_score(self, score):
        self.score_label.text = f"SCORE: {score}       BEST: {self.high_score}"

    def update_high_score(self, score):
        self.high_score = max(self.high_score, score)
        self.update_score(score)

    def restart_game(self):
        self.board.reset_game()

    def toggle_music(self):
        if not self.music:
            return
        if self.music.state == "play":
            self.music.stop()
            self.music_btn.text = "MUSIC OFF"
        else:
            self.music.play()
            self.music_btn.text = "MUSIC ON"

    def on_pause(self):
        if self.music:
            self.music.stop()
        return True

    def on_stop(self):
        if self.music:
            self.music.stop()


if __name__ == "__main__":
    PrincessSnakeApp().run()
