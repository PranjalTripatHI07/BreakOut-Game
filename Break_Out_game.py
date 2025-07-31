import pygame
from pygame.locals import *
import random
import math

pygame.init()

# Screen configuration
screen_width = 600
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Breakout - Interactive Edition')

# Font setup
font = pygame.font.SysFont('Constantia', 30)
small_font = pygame.font.SysFont('Constantia', 20)
large_font = pygame.font.SysFont('Constantia', 40)

# Color definitions
bg = (234, 218, 184)
block_red = (255, 165, 0)
block_green = (255, 255, 0)
block_blue = (69, 177, 232)
paddle_col = (142, 135, 123)
paddle_outline = (100, 100, 100)
text_col = (78, 81, 139)
particle_colors = [(255, 255, 255), (255, 255, 150), (150, 255, 150), (150, 150, 255)]

# Game state variables
cols = 6
rows = 6
clock = pygame.time.Clock()
fps = 60
live_ball = False
game_over = 0
score = 0
level = 1
blocks_destroyed = 0
combo_count = 0
last_hit_time = 0
paddle_glow = 0
ball_trail = []

# Particle system storage
particles = []


class Particle:
    """Visual effect particles for block destruction and collisions"""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, -1)
        self.life = 30
        self.max_life = 30
        self.color = color
        self.size = random.uniform(2, 4)

    def update(self):
        """Update particle position and physics"""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= 1

    def draw(self):
        """Render particle with fading effect"""
        alpha = int(255 * (self.life / self.max_life))
        color_with_alpha = (*self.color, alpha)
        size = int(self.size * (self.life / self.max_life))
        if size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)


def create_particles(x, y, color, count=10):
    """Generate particle burst at specified location"""
    for _ in range(count):
        particles.append(Particle(x, y, color))


def update_particles():
    """Update all particles and remove expired ones"""
    global particles
    for particle in particles[:]:
        particle.update()
        if particle.life <= 0:
            particles.remove(particle)


def draw_particles():
    """Render all active particles"""
    for particle in particles:
        particle.draw()


def draw_text(text, font, text_col, x, y, glow=False):
    """Render text with optional glow effect"""
    if glow:
        glow_surface = font.render(text, True, (255, 255, 255))
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx != 0 or dy != 0:
                    screen.blit(glow_surface, (x + dx, y + dy))

    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_ui():
    """Display game interface elements"""
    draw_text(f'Score: {score}', small_font, text_col, 10, 10)
    draw_text(f'Level: {level}', small_font, text_col, 10, 35)

    # Combo multiplier display
    if combo_count > 1:
        combo_alpha = max(0, 255 - (pygame.time.get_ticks() - last_hit_time) // 10)
        if combo_alpha > 0:
            combo_text = f'Combo x{combo_count}!'
            combo_surface = small_font.render(combo_text, True, text_col)
            combo_width = combo_surface.get_width()
            draw_text(combo_text, small_font, text_col, screen_width - combo_width - 10, 10, True)

    # Visual lives indicator
    heart_size = 15
    for i in range(3):
        heart_x = screen_width - 40 - (i * 25)
        heart_y = screen_height - 25
        pygame.draw.circle(screen, (100, 150, 255), (heart_x, heart_y), heart_size // 2)
        pygame.draw.circle(screen, (80, 120, 200), (heart_x, heart_y), heart_size // 2, 2)


class wall():
    """Manages the destructible block wall"""
    def __init__(self):
        self.width = screen_width // cols
        self.height = 50

    def create_wall(self):
        """Generate wall with blocks of varying strength"""
        self.blocks = []
        block_individual = []
        for row in range(rows):
            block_row = []
            for col in range(cols):
                block_x = col * self.width
                block_y = row * self.height
                rect = pygame.Rect(block_x, block_y, self.width, self.height)
                # Assign block durability based on row position
                if row < 2:
                    strength = 3
                elif row < 4:
                    strength = 2
                elif row < 6:
                    strength = 1
                block_individual = [rect, strength]
                block_row.append(block_individual)
            self.blocks.append(block_row)

    def draw_wall(self):
        """Render all active blocks with visual effects"""
        for row in self.blocks:
            for block in row:
                if block[0] != (0, 0, 0, 0):
                    # Color based on block strength
                    if block[1] == 3:
                        block_col = block_blue
                    elif block[1] == 2:
                        block_col = block_green
                    elif block[1] == 1:
                        block_col = block_red

                    # Animated pulsing effect
                    pulse = int(10 * math.sin(pygame.time.get_ticks() * 0.005))
                    enhanced_color = tuple(max(0, min(255, c + pulse)) for c in block_col)

                    pygame.draw.rect(screen, enhanced_color, block[0])
                    pygame.draw.rect(screen, bg, (block[0]), 2)

                    # 3D highlight effect
                    inner_rect = pygame.Rect(block[0].x + 3, block[0].y + 3,
                                             block[0].width - 6, block[0].height - 6)
                    inner_color = tuple(max(0, min(255, c + 30)) for c in block_col)
                    pygame.draw.rect(screen, inner_color, inner_rect)


class paddle():
    """Player-controlled paddle"""
    def __init__(self):
        self.reset()

    def move(self):
        """Update paddle position based on mouse input"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_x = mouse_pos[0]

        prev_x = self.rect.x

        self.rect.x = mouse_x - (self.width // 2)

        # Screen boundary constraints
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width

        # Movement direction calculation for ball physics
        if self.rect.x > prev_x:
            self.direction = 1
        elif self.rect.x < prev_x:
            self.direction = -1
        else:
            self.direction = 0

    def draw(self):
        """Render paddle with glow and visual details"""
        global paddle_glow

        # Dynamic glow effect based on movement
        if abs(self.direction) > 0:
            paddle_glow = min(50, paddle_glow + 5)
        else:
            paddle_glow = max(0, paddle_glow - 2)

        # Glow outline when moving
        if paddle_glow > 0:
            glow_rect = pygame.Rect(self.rect.x - 5, self.rect.y - 5,
                                    self.rect.width + 10, self.rect.height + 10)
            glow_color = tuple(max(0, min(255, c + paddle_glow)) for c in paddle_col)
            pygame.draw.rect(screen, glow_color, glow_rect, border_radius=5)

        pygame.draw.rect(screen, paddle_col, self.rect, border_radius=3)
        pygame.draw.rect(screen, paddle_outline, self.rect, 3, border_radius=3)

        # Grip texture lines
        for i in range(3):
            line_x = self.rect.x + (self.rect.width // 4) * (i + 1)
            pygame.draw.line(screen, paddle_outline,
                             (line_x, self.rect.y + 5),
                             (line_x, self.rect.y + self.rect.height - 5), 2)

    def reset(self):
        """Initialize paddle properties"""
        self.height = 20
        self.width = int(screen_width / cols)
        self.x = int((screen_width / 2) - (self.width / 2))
        self.y = screen_height - (self.height * 2)
        self.speed = 10
        self.rect = Rect(self.x, self.y, self.width, self.height)
        self.direction = 0


class game_ball():
    """Game ball with physics and collision detection"""
    def __init__(self, x, y):
        self.reset(x, y)

    def move(self):
        """Update ball position and handle all collisions"""
        global score, blocks_destroyed, combo_count, last_hit_time

        # Trail effect management
        ball_trail.append((self.rect.centerx, self.rect.centery))
        if len(ball_trail) > 8:
            ball_trail.pop(0)

        collision_thresh = 5
        wall_destroyed = 1
        row_count = 0
        hit_block = False

        # Block collision detection and destruction
        for row in wall.blocks:
            item_count = 0
            for item in row:
                if self.rect.colliderect(item[0]):
                    hit_block = True
                    block_strength = item[1]

                    # Collision direction detection and response
                    if abs(self.rect.bottom - item[0].top) < collision_thresh and self.speed_y > 0:
                        self.speed_y *= -1
                    if abs(self.rect.top - item[0].bottom) < collision_thresh and self.speed_y < 0:
                        self.speed_y *= -1
                    if abs(self.rect.right - item[0].left) < collision_thresh and self.speed_x > 0:
                        self.speed_x *= -1
                    if abs(self.rect.left - item[0].right) < collision_thresh and self.speed_x < 0:
                        self.speed_x *= -1

                    # Scoring and particle effects based on block type
                    if block_strength == 3:
                        particle_color = block_blue
                        points = 30
                    elif block_strength == 2:
                        particle_color = block_green
                        points = 20
                    else:
                        particle_color = block_red
                        points = 10

                    create_particles(item[0].centerx, item[0].centery, particle_color, 8)

                    # Block damage and destruction logic
                    if wall.blocks[row_count][item_count][1] > 1:
                        wall.blocks[row_count][item_count][1] -= 1
                        score += points // 2
                    else:
                        wall.blocks[row_count][item_count][0] = (0, 0, 0, 0)
                        score += points
                        blocks_destroyed += 1

                        # Combo system for consecutive hits
                        current_time = pygame.time.get_ticks()
                        if current_time - last_hit_time < 1000:
                            combo_count += 1
                        else:
                            combo_count = 1
                        last_hit_time = current_time

                        # Bonus scoring for combos
                        if combo_count > 1:
                            score += combo_count * 5

                # Check for remaining blocks
                if wall.blocks[row_count][item_count][0] != (0, 0, 0, 0):
                    wall_destroyed = 0
                item_count += 1
            row_count += 1

        # Reset combo timer
        if not hit_block:
            current_time = pygame.time.get_ticks()
            if current_time - last_hit_time > 1000:
                combo_count = 0

        # Victory condition check
        if wall_destroyed == 1:
            self.game_over = 1

        # Wall boundary collisions
        if self.rect.left < 0 or self.rect.right > screen_width:
            self.speed_x *= -1

        # Ceiling and floor collisions
        if self.rect.top < 0:
            self.speed_y *= -1
        if self.rect.bottom > screen_height:
            self.game_over = -1

        # Paddle collision with enhanced physics
        if self.rect.colliderect(player_paddle.rect):
            if abs(self.rect.bottom - player_paddle.rect.top) < collision_thresh and self.speed_y > 0:
                self.speed_y *= -1
                self.speed_x += player_paddle.direction
                if self.speed_x > self.speed_max:
                    self.speed_x = self.speed_max
                elif self.speed_x < 0 and self.speed_x < -self.speed_max:
                    self.speed_x = -self.speed_max

                create_particles(self.rect.centerx, self.rect.centery, (255, 255, 255), 5)
            else:
                self.speed_x *= -1

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        return self.game_over

    def draw(self):
        """Render ball with trail and glow effects"""
        # Motion trail rendering
        for i, pos in enumerate(ball_trail):
            alpha = int(255 * (i / len(ball_trail)))
            trail_size = int(self.ball_rad * (i / len(ball_trail)))
            if trail_size > 0:
                trail_color = tuple(max(0, min(255, c + 50)) for c in paddle_col)
                pygame.draw.circle(screen, trail_color, pos, trail_size)

        # Main ball with glow effect
        glow_radius = self.ball_rad + 3
        pygame.draw.circle(screen, (255, 255, 255),
                           (self.rect.x + self.ball_rad, self.rect.y + self.ball_rad),
                           glow_radius)
        pygame.draw.circle(screen, paddle_col,
                           (self.rect.x + self.ball_rad, self.rect.y + self.ball_rad),
                           self.ball_rad)
        pygame.draw.circle(screen, paddle_outline,
                           (self.rect.x + self.ball_rad, self.rect.y + self.ball_rad),
                           self.ball_rad, 3)

    def reset(self, x, y):
        """Initialize ball properties and position"""
        global ball_trail
        ball_trail = []
        self.ball_rad = 10
        self.x = x - self.ball_rad
        self.y = y
        self.rect = Rect(self.x, self.y, self.ball_rad * 2, self.ball_rad * 2)
        self.speed_x = 4
        self.speed_y = -4
        self.speed_max = 5
        self.game_over = 0


# Animated background elements setup
bg_elements = []
for _ in range(20):
    bg_elements.append({
        'x': random.randint(0, screen_width),
        'y': random.randint(0, screen_height),
        'speed': random.uniform(0.5, 2),
        'size': random.randint(1, 3)
    })


def draw_animated_background():
    """Render moving background particles"""
    for element in bg_elements:
        element['y'] += element['speed']
        if element['y'] > screen_height:
            element['y'] = -10
            element['x'] = random.randint(0, screen_width)

        alpha = int(30 + 20 * math.sin(pygame.time.get_ticks() * 0.01 + element['x']))
        color = tuple(max(0, min(255, c + alpha)) for c in bg)
        pygame.draw.circle(screen, color, (int(element['x']), int(element['y'])), element['size'])


# Game object initialization
wall = wall()
wall.create_wall()
player_paddle = paddle()
ball = game_ball(player_paddle.x + (player_paddle.width // 2), player_paddle.y - player_paddle.height)

# Main game loop
run = True
while run:
    clock.tick(fps)

    # Background rendering
    screen.fill(bg)
    draw_animated_background()

    # Particle system update
    update_particles()
    draw_particles()

    # Game object rendering
    wall.draw_wall()
    player_paddle.draw()
    ball.draw()

    # Interface display
    draw_ui()

    # Active gameplay logic
    if live_ball:
        player_paddle.move()
        game_over = ball.move()
        if game_over != 0:
            live_ball = False

    # Menu and game state screens
    if not live_ball:
        # Pulsing text effect
        pulse = int(20 * math.sin(pygame.time.get_ticks() * 0.01))
        pulse_color = tuple(max(0, min(255, c + pulse)) for c in text_col)

        if game_over == 0:
            # Main menu display
            title_surface = large_font.render('BREAKOUT GAME', True, pulse_color)
            title_width = title_surface.get_width()
            title_x = (screen_width - title_width) // 2

            start_surface = font.render('CLICK ANYWHERE TO START', True, text_col)
            start_width = start_surface.get_width()
            start_x = (screen_width - start_width) // 2

            instruction_surface = small_font.render('Move mouse to control paddle', True, text_col)
            instruction_width = instruction_surface.get_width()
            instruction_x = (screen_width - instruction_width) // 2

            draw_text('BREAKOUT GAME', large_font, pulse_color, title_x, screen_height // 2 - 50, True)
            draw_text('CLICK ANYWHERE TO START', font, text_col, start_x, screen_height // 2 + 100)
            draw_text('Move mouse to control paddle', small_font, text_col, instruction_x, screen_height // 2 + 130)

        elif game_over == 1:
            # Victory screen display
            victory_surface = large_font.render('VICTORY!', True, (100, 255, 100))
            victory_width = victory_surface.get_width()
            victory_x = (screen_width - victory_width) // 2

            score_surface = font.render(f'Final Score: {score}', True, pulse_color)
            score_width = score_surface.get_width()
            score_x = (screen_width - score_width) // 2

            play_again_surface = font.render('CLICK TO PLAY AGAIN', True, text_col)
            play_again_width = play_again_surface.get_width()
            play_again_x = (screen_width - play_again_width) // 2

            draw_text('VICTORY!', large_font, (100, 255, 100), victory_x, screen_height // 2 + 20, True)
            draw_text(f'Final Score: {score}', font, pulse_color, score_x, screen_height // 2 + 70)
            draw_text('CLICK TO PLAY AGAIN', font, text_col, play_again_x, screen_height // 2 + 100)

        elif game_over == -1:
            # Game over screen display
            game_over_surface = large_font.render('GAME OVER', True, text_col)
            game_over_width = game_over_surface.get_width()
            game_over_x = (screen_width - game_over_width) // 2

            score_surface = font.render(f'Final Score: {score}', True, pulse_color)
            score_width = score_surface.get_width()
            score_x = (screen_width - score_width) // 2

            try_again_surface = font.render('CLICK TO TRY AGAIN', True, text_col)
            try_again_width = try_again_surface.get_width()
            try_again_x = (screen_width - try_again_width) // 2

            draw_text('GAME OVER', large_font, text_col, game_over_x, screen_height // 2 + 20, True)
            draw_text(f'Final Score: {score}', font, pulse_color, score_x, screen_height // 2 + 70)
            draw_text('CLICK TO TRY AGAIN', font, text_col, try_again_x, screen_height // 2 + 100)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN and live_ball == False:
            live_ball = True
            # Game state reset on restart
            if game_over != 0:
                score = 0
                blocks_destroyed = 0
                combo_count = 0
                level = 1
            ball.reset(player_paddle.x + (player_paddle.width // 2), player_paddle.y - player_paddle.height)
            player_paddle.reset()
            wall.create_wall()

    pygame.display.update()

pygame.quit()
