import pygame
from .paddle import Paddle
from .ball import Ball
from .brick import Brick

# Game Engine

WHITE = (255, 255, 255)
BG = (15, 15, 25)
BRICK_COLORS = [
    (200, 60, 60),
    (200, 140, 60),
    (200, 200, 60),
    (80, 180, 80),
    (80, 140, 200),
]

# Difficulty presets: key -> (name, ball speed, paddle width)
DIFFICULTIES = {
    pygame.K_1: ("Easy", 3, 140),
    pygame.K_2: ("Medium", 4, 100),
    pygame.K_3: ("Hard", 6, 70),
}

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.rows, self.cols = 5, 8
        self.font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 56, bold=True)
        self.quit_requested = False
        self.reset(DIFFICULTIES[pygame.K_2])

    def reset(self, difficulty):
        self.difficulty, self.ball_speed, paddle_width = difficulty

        self.paddle = Paddle(self.width // 2 - paddle_width // 2, self.height - 30, paddle_width, 14)

        self.ball = Ball(self.width // 2, self.height - 50, radius=8)
        self._reset_ball()

        self.bricks = self._build_bricks(self.rows, self.cols)

        self.lives = 3
        self.score = 0
        self.game_over = False
        self.result = None  # "win" or "lose"

    def _build_bricks(self, rows, cols):
        bricks = []
        margin, gap, top = 30, 6, 60
        brick_w = (self.width - margin * 2 - gap * (cols - 1)) // cols
        brick_h = 22
        for r in range(rows):
            for c in range(cols):
                x = margin + c * (brick_w + gap)
                y = top + r * (brick_h + gap)
                bricks.append(Brick(x, y, brick_w, brick_h))
        return bricks

    def handle_event(self, event):
        # Paddle movement is continuous and handled in handle_input; the
        # only discrete input is on the end screen.
        if not self.game_over or event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            self.quit_requested = True
        elif event.key in DIFFICULTIES:
            self.reset(DIFFICULTIES[event.key])

    def handle_input(self):
        if self.game_over:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(-self.paddle.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(self.paddle.speed, self.width)

    def update(self):
        if self.game_over:
            return

        self.ball.move()

        # Set the direction explicitly (instead of flipping) and clamp the
        # ball inside the screen so it can never get stuck in a wall.
        if self.ball.x - self.ball.radius <= 0:
            self.ball.x = self.ball.radius
            self.ball.vx = abs(self.ball.vx)
        elif self.ball.x + self.ball.radius >= self.width:
            self.ball.x = self.width - self.ball.radius
            self.ball.vx = -abs(self.ball.vx)
        if self.ball.y - self.ball.radius <= 0:
            self.ball.y = self.ball.radius
            self.ball.vy = abs(self.ball.vy)

        if self.ball.rect().colliderect(self.paddle.rect()):
            self._bounce_off(self.paddle.rect())

        for brick in self.bricks:
            if brick.alive and self.ball.rect().colliderect(brick.rect()):
                brick.alive = False
                self.score += 1
                self._bounce_off(brick.rect())
                break

        if self.ball.y - self.ball.radius > self.height:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self.result = "lose"
            else:
                self._reset_ball()

        if all(not b.alive for b in self.bricks):
            self.game_over = True
            self.result = "win"

    def _bounce_off(self, rect):
        # The side that was hit is the axis with the smaller overlap:
        # a thin horizontal overlap means the ball came in from the left
        # or right, a thin vertical overlap means from the top or bottom.
        ball = self.ball.rect()
        overlap_x = min(ball.right, rect.right) - max(ball.left, rect.left)
        overlap_y = min(ball.bottom, rect.bottom) - max(ball.top, rect.top)
        if overlap_x < overlap_y:
            # Side hit: send the ball back sideways and push it out.
            if self.ball.x < rect.centerx:
                self.ball.vx = -abs(self.ball.vx)
                self.ball.x -= overlap_x
            else:
                self.ball.vx = abs(self.ball.vx)
                self.ball.x += overlap_x
        else:
            # Top/bottom hit: send the ball back vertically and push it out.
            if self.ball.y < rect.centery:
                self.ball.vy = -abs(self.ball.vy)
                self.ball.y -= overlap_y
            else:
                self.ball.vy = abs(self.ball.vy)
                self.ball.y += overlap_y

    def _reset_ball(self):
        self.ball.x, self.ball.y = self.width // 2, self.height - 50
        self.ball.vx, self.ball.vy = self.ball_speed, -self.ball_speed

    def render(self, screen):
        screen.fill(BG)

        pygame.draw.rect(screen, WHITE, self.paddle.rect())
        pygame.draw.circle(screen, WHITE, (int(self.ball.x), int(self.ball.y)), self.ball.radius)

        for i, brick in enumerate(self.bricks):
            if brick.alive:
                row = i // self.cols
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                pygame.draw.rect(screen, color, brick.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (self.width - 130, 10))

        if self.game_over:
            self._render_end_screen(screen)

    def _end_screen_lines(self):
        return [
            ("Play again - choose difficulty:", WHITE),
            ("1  Easy     2  Medium     3  Hard", (240, 200, 90)),
            ("Esc / Q  Quit", (170, 170, 170)),
        ]

    def _render_end_screen(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        won = self.result == "win"
        title = self.big_font.render("YOU WIN!" if won else "GAME OVER", True,
                                     (90, 220, 110) if won else (230, 70, 70))
        screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 90)))

        score = self.font.render(f"Final score: {self.score}", True, WHITE)
        screen.blit(score, score.get_rect(center=(self.width // 2, self.height // 2 - 30)))

        y = self.height // 2 + 30
        for text, color in self._end_screen_lines():
            line = self.font.render(text, True, color)
            screen.blit(line, line.get_rect(center=(self.width // 2, y)))
            y += 40
