import math
import struct

import pygame

from .paddle import Paddle
from .ball import Ball
from .brick import Brick


WHITE = (255, 255, 255)
BG = (15, 15, 25)

BRICK_COLORS = [
    (200, 60, 60),
    (200, 140, 60),
    (200, 200, 60),
    (80, 180, 80),
    (80, 140, 200),
]


DIFFICULTIES = {
    "Easy": {
        "ball_speed": 3.5,
        "paddle_width": 120,
    },
    "Medium": {
        "ball_speed": 4.0,
        "paddle_width": 100,
    },
    "Hard": {
        "ball_speed": 5.5,
        "paddle_width": 85,
    },
}


class SoundManager:
    """
    Generates short sound effects entirely in code.

    Audio is optional. If the mixer/audio device is unavailable,
    the game continues silently instead of crashing.
    """

    def __init__(self):
        self.enabled = False
        self.sounds = {}

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()

            self.sounds = {
                "wall": self._make_tone(520, 0.06, 0.18),
                "paddle": self._make_tone(700, 0.07, 0.20),
                "brick": self._make_tone(900, 0.08, 0.22),
                "end": self._make_tone(260, 0.28, 0.25),
            }

            self.enabled = True

        except (pygame.error, OSError):
            # No audio device / mixer available.
            # Gameplay must still work normally.
            self.enabled = False
            self.sounds = {}

    @staticmethod
    def _make_tone(frequency, duration, volume):
        sample_rate = 44100
        sample_count = int(sample_rate * duration)

        samples = bytearray()

        for i in range(sample_count):
            t = i / sample_rate

            # Fade the sound out naturally.
            envelope = 1.0 - (i / sample_count)

            sample = int(
                32767
                * volume
                * envelope
                * math.sin(2 * math.pi * frequency * t)
            )

            samples.extend(struct.pack("<h", sample))

        return pygame.mixer.Sound(buffer=bytes(samples))

    def play(self, name):
        if not self.enabled:
            return

        try:
            sound = self.sounds.get(name)

            if sound is not None:
                sound.play()

        except pygame.error:
            # Audio failure should never stop gameplay.
            pass


class GameEngine:
    def __init__(self, width, height, difficulty="Medium"):
        self.width = width
        self.height = height

        self.rows = 5
        self.cols = 8

        self.difficulty = (
            difficulty if difficulty in DIFFICULTIES else "Medium"
        )

        self.font = pygame.font.SysFont("Arial", 28)
        self.title_font = pygame.font.SysFont(
            "Arial",
            44,
            bold=True,
        )
        self.small_font = pygame.font.SysFont("Arial", 22)

        self.sound = SoundManager()

        self.game_over = False
        self.result = None
        self._game_over_sound_played = False

        self._create_game_state()

    # ---------------------------------------------------------
    # GAME SETUP
    # ---------------------------------------------------------

    def _create_game_state(self):
        settings = DIFFICULTIES[self.difficulty]

        paddle_width = settings["paddle_width"]

        self.paddle = Paddle(
            self.width // 2 - paddle_width // 2,
            self.height - 30,
            paddle_width,
            14,
        )

        self.ball = Ball(
            self.width // 2,
            self.height - 50,
            radius=8,
        )

        self.ball_speed = settings["ball_speed"]

        self.bricks = self._build_bricks(
            self.rows,
            self.cols,
        )

        self.lives = 3
        self.score = 0

        self.game_over = False
        self.result = None
        self._game_over_sound_played = False

        self._reset_ball()

    def restart(self, difficulty=None):
        if difficulty in DIFFICULTIES:
            self.difficulty = difficulty

        self._create_game_state()

    def _build_bricks(self, rows, cols):
        bricks = []

        margin = 30
        gap = 6
        top = 60

        brick_w = (
            self.width
            - margin * 2
            - gap * (cols - 1)
        ) // cols

        brick_h = 22

        for r in range(rows):
            for c in range(cols):
                x = margin + c * (brick_w + gap)
                y = top + r * (brick_h + gap)

                bricks.append(
                    Brick(
                        x,
                        y,
                        brick_w,
                        brick_h,
                    )
                )

        return bricks

    # ---------------------------------------------------------
    # INPUT
    # ---------------------------------------------------------

    def handle_event(self, event):
        """
        Handle keyboard input used by the end screen.

        E = Easy
        M = Medium
        H = Hard
        Q = Exit
        """

        if event.type != pygame.KEYDOWN:
            return

        if not self.game_over:
            return

        if event.key == pygame.K_e:
            self.restart("Easy")

        elif event.key == pygame.K_m:
            self.restart("Medium")

        elif event.key == pygame.K_h:
            self.restart("Hard")

        elif event.key == pygame.K_q:
            # Explicit exit option required by the README.
            pygame.event.post(
                pygame.event.Event(pygame.QUIT)
            )

    def handle_input(self):
        if self.game_over:
            return

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(
                -self.paddle.speed,
                self.width,
            )

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(
                self.paddle.speed,
                self.width,
            )

    # ---------------------------------------------------------
    # GAME UPDATE
    # ---------------------------------------------------------

    def update(self):
        if self.game_over:
            return

        previous_x = self.ball.x
        previous_y = self.ball.y

        self.ball.move()

        # -----------------------------------------------------
        # WALL COLLISIONS
        # -----------------------------------------------------

        if self.ball.x - self.ball.radius <= 0:
            self.ball.x = self.ball.radius
            self.ball.vx = abs(self.ball.vx)

            self.sound.play("wall")

        elif self.ball.x + self.ball.radius >= self.width:
            self.ball.x = (
                self.width - self.ball.radius
            )
            self.ball.vx = -abs(self.ball.vx)

            self.sound.play("wall")

        if self.ball.y - self.ball.radius <= 0:
            self.ball.y = self.ball.radius
            self.ball.vy = abs(self.ball.vy)

            self.sound.play("wall")

        # -----------------------------------------------------
        # PADDLE COLLISION
        # -----------------------------------------------------

        paddle_rect = self.paddle.rect()
        ball_rect = self.ball.rect()

        if ball_rect.colliderect(paddle_rect):

            if previous_y + self.ball.radius <= paddle_rect.top:
                self.ball.y = (
                    paddle_rect.top - self.ball.radius
                )

                self.ball.vy = -abs(self.ball.vy)

                paddle_center = (
                    self.paddle.x
                    + self.paddle.width / 2
                )

                hit_offset = (
                    self.ball.x - paddle_center
                ) / (self.paddle.width / 2)

                self.ball.vx += hit_offset * 1.0

                self._limit_horizontal_speed()

            elif previous_y - self.ball.radius >= paddle_rect.bottom:
                self.ball.y = (
                    paddle_rect.bottom
                    + self.ball.radius
                )

                self.ball.vy = abs(self.ball.vy)

            elif previous_x + self.ball.radius <= paddle_rect.left:
                self.ball.x = (
                    paddle_rect.left
                    - self.ball.radius
                )

                self.ball.vx = -abs(self.ball.vx)

            else:
                self.ball.x = (
                    paddle_rect.right
                    + self.ball.radius
                )

                self.ball.vx = abs(self.ball.vx)

            self.sound.play("paddle")

        # -----------------------------------------------------
        # BRICK COLLISIONS
        # -----------------------------------------------------

        for brick in self.bricks:

            if not brick.alive:
                continue

            brick_rect = brick.rect()
            ball_rect = self.ball.rect()

            if not ball_rect.colliderect(brick_rect):
                continue

            overlap_x = min(
                ball_rect.right,
                brick_rect.right,
            ) - max(
                ball_rect.left,
                brick_rect.left,
            )

            overlap_y = min(
                ball_rect.bottom,
                brick_rect.bottom,
            ) - max(
                ball_rect.top,
                brick_rect.top,
            )

            if overlap_x < overlap_y:

                if previous_x < brick_rect.left:
                    self.ball.x = (
                        brick_rect.left
                        - self.ball.radius
                    )

                    self.ball.vx = -abs(
                        self.ball.vx
                    )

                else:
                    self.ball.x = (
                        brick_rect.right
                        + self.ball.radius
                    )

                    self.ball.vx = abs(
                        self.ball.vx
                    )

            else:

                if previous_y < brick_rect.top:
                    self.ball.y = (
                        brick_rect.top
                        - self.ball.radius
                    )

                    self.ball.vy = -abs(
                        self.ball.vy
                    )

                else:
                    self.ball.y = (
                        brick_rect.bottom
                        + self.ball.radius
                    )

                    self.ball.vy = abs(
                        self.ball.vy
                    )

            brick.alive = False
            self.score += 1

            self.sound.play("brick")

            break

        # -----------------------------------------------------
        # BALL LOST
        # -----------------------------------------------------

        if self.ball.y - self.ball.radius > self.height:

            self.lives -= 1

            if self.lives <= 0:
                self.game_over = True
                self.result = "lose"

                self._play_end_sound()

            else:
                self._reset_ball()

        # -----------------------------------------------------
        # WIN CONDITION
        # -----------------------------------------------------

        if self.score == self.rows * self.cols:

            self.game_over = True
            self.result = "win"

            self._play_end_sound()

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def _limit_horizontal_speed(self):
        max_vx = self.ball_speed * 1.35

        if self.ball.vx > max_vx:
            self.ball.vx = max_vx

        elif self.ball.vx < -max_vx:
            self.ball.vx = -max_vx

    def _play_end_sound(self):
        if not self._game_over_sound_played:
            self.sound.play("end")
            self._game_over_sound_played = True

    def _reset_ball(self):
        self.ball.x = self.width // 2
        self.ball.y = self.height - 50

        self.ball.vx = self.ball_speed
        self.ball.vy = -self.ball_speed

    # ---------------------------------------------------------
    # RENDERING
    # ---------------------------------------------------------

    def render(self, screen):
        screen.fill(BG)

        pygame.draw.rect(
            screen,
            WHITE,
            self.paddle.rect(),
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (
                int(self.ball.x),
                int(self.ball.y),
            ),
            self.ball.radius,
        )

        for i, brick in enumerate(self.bricks):

            if brick.alive:
                row = i // self.cols

                color = BRICK_COLORS[
                    row % len(BRICK_COLORS)
                ]

                pygame.draw.rect(
                    screen,
                    color,
                    brick.rect(),
                )

        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            WHITE,
        )

        screen.blit(
            score_text,
            (10, 10),
        )

        lives_text = self.font.render(
            f"Lives: {self.lives}",
            True,
            WHITE,
        )

        screen.blit(
            lives_text,
            (self.width - 130, 10),
        )

        difficulty_text = self.small_font.render(
            f"Difficulty: {self.difficulty}",
            True,
            WHITE,
        )

        screen.blit(
            difficulty_text,
            (10, self.height - 30),
        )

        if self.game_over:
            self._render_end_screen(screen)

    def _render_end_screen(self, screen):

        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (0, 0, 0, 190)
        )

        screen.blit(
            overlay,
            (0, 0),
        )

        title = (
            "YOU WIN!"
            if self.result == "win"
            else "GAME OVER"
        )

        title_surface = self.title_font.render(
            title,
            True,
            WHITE,
        )

        title_rect = title_surface.get_rect(
            center=(
                self.width // 2,
                170,
            )
        )

        screen.blit(
            title_surface,
            title_rect,
        )

        score_surface = self.font.render(
            f"Final Score: {self.score}",
            True,
            WHITE,
        )

        score_rect = score_surface.get_rect(
            center=(
                self.width // 2,
                225,
            )
        )

        screen.blit(
            score_surface,
            score_rect,
        )

        # Explicitly show all four available options.
        prompt = self.small_font.render(
            "E = Easy   M = Medium   H = Hard   Q = Exit",
            True,
            WHITE,
        )

        prompt_rect = prompt.get_rect(
            center=(
                self.width // 2,
                295,
            )
        )

        screen.blit(
            prompt,
            prompt_rect,
        )