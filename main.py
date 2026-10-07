import pygame

from game.game_engine import GameEngine


# Initialize Pygame.
#
# Audio is initialized separately inside GameEngine.
# If the machine has no audio device, the game will simply
# run without sound.
pygame.init()


# Screen dimensions
WIDTH, HEIGHT = 640, 560

SCREEN = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "Brick Breaker - Pygame Version"
)


# Game timing
clock = pygame.time.Clock()
FPS = 60


# Start with Medium difficulty.
#
# Medium keeps the original game's:
# - 4 pixel/frame ball speed
# - 100 pixel paddle width
engine = GameEngine(
    WIDTH,
    HEIGHT,
    difficulty="Medium",
)


def main():
    running = True

    while running:

        # -----------------------------------------------------
        # EVENTS
        # -----------------------------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            else:
                engine.handle_event(event)

        # -----------------------------------------------------
        # GAME LOGIC
        # -----------------------------------------------------

        engine.handle_input()
        engine.update()

        # -----------------------------------------------------
        # DRAW
        # -----------------------------------------------------

        engine.render(SCREEN)

        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()