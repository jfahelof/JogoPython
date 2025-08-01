import pgzrun
from pygame import Rect
import random

WIDTH = 1280
HEIGHT = 720

# Estados do jogo
game_state = "menu"
sound_on = True
death_timer = 0

# Botões do menu
button_start = Rect(480, 200, 300, 80)
button_sound = Rect(480, 300, 300, 80)
button_exit = Rect(480, 400, 300, 80)

# Física
gravity = 1
jump_strength = -20
speed = 5

# Animação
ANIMATION_DELAY = 0.2
animation_time = 0

# Som
step_channel = None
menu_music_playing = False
game_music_playing = False

# Limites de salto
MAX_JUMPS = 4

# Plataforma
platforms = []
platform_timer = 0
PLATFORM_SPAWN_INTERVAL = 7
BLOCK_SIZE = 32  

# --------------------------------
# Classes
# ------------------------------

class Hero:
    def __init__(self):
        self.actor = Actor("hero_idle1")
        self.actor.pos = 200, HEIGHT - 240
        self.vx = 0
        self.vy = 0
        self.frame = 0
        self.jump_count = 0

    def update(self):
        self.vx = 0
        if keyboard.right:
            self.actor.x += speed
            self.vx = speed
        elif keyboard.left:
            self.actor.x -= speed
            self.vx = -speed

        self.actor.y += self.vy

        if self.actor.y >= HEIGHT - 240:
            self.actor.y = HEIGHT - 240
            self.vy = 0
            self.jump_count = 0

    def animate(self):
        if self.vy != 0:
            self.actor.image = "hero_jump"
        elif self.vx != 0:
            self.frame = (self.frame + 1) % 2
            self.actor.image = f"hero_walk{self.frame + 1}"
        else:
            self.frame = (self.frame + 1) % 3
            self.actor.image = f"hero_idle{self.frame + 1}"

    def draw(self):
        self.actor.draw()

    def jump(self):
        if self.jump_count < MAX_JUMPS:
            self.vy = jump_strength
            self.jump_count += 1
            self.actor.image = "hero_jump"
            if sound_on:
                sounds.jump.play()


class Enemy:
    def __init__(self):
        self.actor = Actor("enemy_walk1")
        self.actor.pos = WIDTH + 50, HEIGHT - 240
        self.frame = 0
        self.velocity = random.randint(1, 3)
        self.idle = False
        self.idle_timer = 0

    def update(self, dt):
        if self.idle:
            self.idle_timer += dt
            if self.idle_timer > 2:
                self.idle = False
                self.idle_timer = 0
        else:
            self.actor.x -= self.velocity
            if random.random() < 0.01:
                self.idle = True

    def animate(self):
        if self.idle:
            self.frame = (self.frame + 1) % 2
            self.actor.image = f"enemy_idle{self.frame + 1}"
        else:
            self.frame = (self.frame + 1) % 4
            self.actor.image = f"enemy_walk{self.frame + 1}"

    def draw(self):
        self.actor.draw()

    def is_off_screen(self):
        return self.actor.right < 0

    def collides_with(self, other_actor):
        return self.actor.colliderect(other_actor)


class Platform:
    def __init__(self):
        self.block_count = random.randint(3, 7)
        self.blocks = []
        self.velocity = random.uniform(1.0, 3.0)

        base_x = -self.block_count * BLOCK_SIZE
        y = random.randint(HEIGHT - 720, HEIGHT - 300)

        for i in range(self.block_count):
            block = Actor("block")
            block.x = base_x + i * BLOCK_SIZE
            block.y = y
            self.blocks.append(block)

    def update(self, dt):
        for block in self.blocks:
            block.x += self.velocity

    def draw(self):
        for block in self.blocks:
            block.draw()

    def collides_with(self, actor):
        for block in self.blocks:
            if actor.colliderect(block):
                return True
        return False

    def on_top(self, actor):
        for block in self.blocks:
            if (
                abs(actor.bottom - block.top) <= 10
                and actor.right > block.left
                and actor.left < block.right
            ):
                return True
        return False

    def is_off_screen(self):
        return all(block.left > WIDTH for block in self.blocks)


# ---------------------------
# Inicialização
# --------------------------------

hero = Hero()
enemies = []
enemy_timer = 0

# ------------------------
# Funções do Jogo
# ------------------------------

def start_menu_music():
    global menu_music_playing, game_music_playing
    if sound_on and not menu_music_playing:
        music.stop()
        music.play("game_music")
        menu_music_playing = True
        game_music_playing = False

def draw():
    screen.clear()
    if game_state == "menu":
        draw_menu()
    elif game_state == "playing":
        draw_game()
    elif game_state == "dead":
        screen.blit("infectado", (0, 0))
        screen.draw.text("Você perdeu!", center=(WIDTH // 2, HEIGHT // 2), fontsize=80, color="red")

def draw_menu():
    screen.blit("menu_background", (0, 0))
    screen.draw.text("Menu Principal", center=(WIDTH // 2, 100), fontsize=80, color="brown")

    screen.draw.filled_rect(button_start, "darkgreen")
    screen.draw.text("Começar o jogo", center=button_start.center, fontsize=30, color="white")

    screen.draw.filled_rect(button_sound, "darkblue")
    sound_text = "Música e sons: ligados" if sound_on else "Música e sons: desligados"
    screen.draw.text(sound_text, center=button_sound.center, fontsize=30, color="white")

    screen.draw.filled_rect(button_exit, "darkred")
    screen.draw.text("Saída", center=button_exit.center, fontsize=30, color="white")

def draw_game():
    screen.blit("game_background", (0, 0))
    hero.draw()
    for enemy in enemies:
        enemy.draw()
    for platform in platforms:
        platform.draw()

def on_mouse_down(pos):
    global game_state, sound_on, menu_music_playing
    if game_state == "menu":
        if button_start.collidepoint(pos):
            reset_game()
            game_state = "playing"
        elif button_sound.collidepoint(pos):
            sound_on = not sound_on
            if not sound_on:
                music.stop()
            else:
                menu_music_playing = False
        elif button_exit.collidepoint(pos):
            exit()

def reset_game():
    global enemies, hero, platforms, platform_timer
    enemies = []
    platforms = []
    platform_timer = 0
    hero.__init__()

def update(dt):
    global enemy_timer, game_state, death_timer, animation_time
    global menu_music_playing, game_music_playing, platform_timer

    if game_state == "menu":
        start_menu_music()

    elif game_state == "playing":
        if sound_on and not game_music_playing:
            music.stop()
            music.play("game_music")
            game_music_playing = True
            menu_music_playing = False

        hero.update()

        for platform in platforms:
            platform.update(dt)

        for platform in platforms:
            if platform.collides_with(hero.actor) and not platform.on_top(hero.actor):
                if sound_on:
                    sounds.hit.play()
                game_state = "dead"
                death_timer = 0
                music.stop()
                return

        on_any_platform = False
        for platform in platforms:
            if platform.on_top(hero.actor):
                hero.actor.y = platform.blocks[0].top - hero.actor.height // 2
                hero.vy = 0
                hero.jump_count = 0
                on_any_platform = True
                break

        if not on_any_platform and hero.actor.y < HEIGHT - 240:
            hero.vy += gravity

        for enemy in enemies:
            enemy.update(dt)

        for enemy in enemies:
            if enemy.collides_with(hero.actor):
                if sound_on:
                    sounds.hit.play()
                game_state = "dead"
                death_timer = 0
                music.stop()
                return

        enemy_timer += dt
        if enemy_timer >= 9:
            enemies.append(Enemy())
            enemy_timer = 0

        platform_timer += dt
        if platform_timer >= PLATFORM_SPAWN_INTERVAL:
            platforms.append(Platform())
            platform_timer = 0

        animation_time += dt
        if animation_time >= ANIMATION_DELAY:
            hero.animate()
            for enemy in enemies:
                enemy.animate()
            animation_time = 0

        enemies[:] = [e for e in enemies if not e.is_off_screen()]
        platforms[:] = [p for p in platforms if not p.is_off_screen()]

    elif game_state == "dead":
        death_timer += dt
        if death_timer >= 2:
            game_state = "menu"
            menu_music_playing = False

def on_key_down(key):
    if game_state != "playing":
        return
    if key == keys.UP:
        hero.jump()

pgzrun.go()

