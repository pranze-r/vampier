import json
import os
from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites
from random import randint, choice

script_dir = os.path.dirname(os.path.abspath(__file__))
game_dir = os.path.dirname(script_dir)

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Vampire: The Hunter')
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'MENU'
        self.score = 0
        self.player_name = ''
        self.high_scores = []
        self.load_highscores()
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 250
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 1000)
        self.spawn_positions = []
        self.shoot_sound = pygame.mixer.Sound(os.path.join(game_dir, 'audio', 'shoot.wav'))
        self.shoot_sound.set_volume(0.2)
        self.impact_sound = pygame.mixer.Sound(os.path.join(game_dir, 'audio', 'impact.ogg'))
        self.hurt_sound = pygame.mixer.Sound(os.path.join(game_dir, 'audio', 'hurt.wav'))
        self.music = pygame.mixer.Sound(os.path.join(game_dir, 'audio', 'music.wav'))
        self.music.set_volume(0.5)
        self.load_images()
        self.setup()

    def load_highscores(self):
        try:
            with open(os.path.join(game_dir, 'highscores.json'), 'r') as f:
                self.high_scores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.high_scores = []

    def save_highscores(self):
        with open(os.path.join(game_dir, 'highscores.json'), 'w') as f:
            json.dump(self.high_scores, f, indent=4)

    def load_images(self):
        self.bullet_surf = pygame.image.load(os.path.join(game_dir, 'images', 'gun', 'bullet.png')).convert_alpha()
        self.heart_surf = pygame.image.load(os.path.join(game_dir, 'images', 'ui', 'heart.png')).convert_alpha()
        self.heart_surf = pygame.transform.rotozoom(self.heart_surf, 0, 0.05)
        self.logo_surf = pygame.image.load(os.path.join(game_dir, 'images', 'ui', 'logo.png')).convert_alpha()
        self.logo_surf = pygame.transform.rotozoom(self.logo_surf, 0, 0.5)
        self.start_button_surf = pygame.image.load(os.path.join(game_dir, 'images', 'ui', 'start.png')).convert_alpha()
        self.start_button_surf = pygame.transform.rotozoom(self.start_button_surf, 0, 0.2)
        self.quit_button_surf = pygame.image.load(os.path.join(game_dir, 'images', 'ui', 'quit.png')).convert_alpha()
        self.quit_button_surf = pygame.transform.rotozoom(self.quit_button_surf, 0, 0.2)
        self.menu_background_surf = pygame.image.load(os.path.join(game_dir, 'images', 'ui', 'menu_background.png')).convert()
        self.menu_background_surf = pygame.transform.scale(self.menu_background_surf, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.game_over_surf = pygame.image.load(os.path.join(game_dir, 'images', 'ui', 'gameover.png')).convert_alpha()
        self.game_over_surf = pygame.transform.scale(self.game_over_surf, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.main_menu_button_surf = pygame.image.load(os.path.join(game_dir, 'images', 'ui', 'main_menu.png')).convert_alpha()
        self.main_menu_button_surf = pygame.transform.rotozoom(self.main_menu_button_surf, 0, 0.2)
        self.paused_surf = pygame.image.load(os.path.join(game_dir, 'images', 'ui', 'paused.png')).convert_alpha()
        folders = list(walk(os.path.join(game_dir, 'images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(os.path.join(game_dir, 'images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key = lambda name: int(name.split('.')[0])):
                    full_path = os.path.join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

    def setup(self):
        map = load_pygame(os.path.join(game_dir, 'data', 'maps', 'world.tmx'))
        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, self.all_sprites)
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)
        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x,obj.y), self.all_sprites, self.collision_sprites, self.hurt_sound)
                self.gun = Gun(self.player, self.all_sprites)
            else:
                self.spawn_positions.append((obj.x, obj.y))
    
    def reset(self):
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.bullet_sprites.empty()
        self.enemy_sprites.empty()
        self.score = 0
        self.player_name = ''
        self.setup()

    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            self.shoot_sound.play()
            pos = self.gun.rect.center + self.gun.player_direction * 50
            Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True
                
    def run_menu(self):
        self.display_surface.blit(self.menu_background_surf, (0,0))
        font_score = pygame.font.Font(None, 40)
        
        logo_rect = self.logo_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 4))
        self.display_surface.blit(self.logo_surf, logo_rect)

        start_button_rect = self.start_button_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        quit_button_rect = self.quit_button_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 80))
        self.display_surface.blit(self.start_button_surf, start_button_rect)
        self.display_surface.blit(self.quit_button_surf, quit_button_rect)
        
        score_title_text = pygame.font.Font(None, 50).render('High Scores', True, (245, 245, 245))
        score_title_rect = score_title_text.get_rect(topright=(WINDOW_WIDTH - 20, WINDOW_HEIGHT - 150))
        self.display_surface.blit(score_title_text, score_title_rect)

        for i, score_entry in enumerate(self.high_scores[:3]):
            score_text = f"{i+1}. {score_entry['name']} - {score_entry['score']}"
            score_surf = font_score.render(score_text, True, (245, 245, 245))
            score_rect = score_surf.get_rect(topleft=(score_title_rect.left, WINDOW_HEIGHT - 100 + i * 30))
            self.display_surface.blit(score_surf, score_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button_rect.collidepoint(event.pos):
                    self.reset()
                    self.state = 'PLAYING'
                if quit_button_rect.collidepoint(event.pos):
                    self.running = False
        
        pygame.display.update()

    def run_game(self):
        dt = self.clock.tick() / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = 'PAUSED'
            if event.type == self.enemy_event:
                Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)
        self.gun_timer()
        self.input()
        self.all_sprites.update(dt)
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    self.impact_sound.play()
                    for sprite in collision_sprites:
                        sprite.destroy()
                        self.score += 10
                    bullet.kill()
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.player.take_damage()
        if self.player.health <= 0:
            self.state = 'GAME_OVER'
        self.display_surface.fill('black')
        self.all_sprites.draw(self.player.rect.center)
        for i in range(self.player.health):
            x = 10 + i * (self.heart_surf.get_width() + 4)
            y = 10
            self.display_surface.blit(self.heart_surf, (x, y))
        font = pygame.font.Font(None, 40)
        score_text = f"Score: {self.score}"
        score_surf = font.render(score_text, True, (255, 255, 255))
        score_rect = score_surf.get_rect(topright=(WINDOW_WIDTH - 20, 10))
        self.display_surface.blit(score_surf, score_rect)
        pygame.display.update()

    def run_pause_menu(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.display_surface.blit(overlay, (0, 0))

        paused_rect = self.paused_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 50))
        self.display_surface.blit(self.paused_surf, paused_rect)

        main_menu_button_rect = self.main_menu_button_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 50))
        self.display_surface.blit(self.main_menu_button_surf, main_menu_button_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = 'PLAYING'
            if event.type == pygame.MOUSEBUTTONDOWN:
                if main_menu_button_rect.collidepoint(event.pos):
                    self.state = 'MENU'
        pygame.display.update()

    def show_game_over(self):
        self.display_surface.fill('black')
        self.display_surface.blit(self.game_over_surf, (0,0))
        pygame.display.update()
        pygame.time.wait(2000)
        self.state = 'ENTER_NAME'

    def run_name_input(self):
        self.display_surface.fill('black')
        font_prompt = pygame.font.Font(None, 60)
        font_name = pygame.font.Font(None, 80)
        prompt_text = f"Your Score: {self.score}. Enter your name (4 chars):"
        prompt_surf = font_prompt.render(prompt_text, True, (255, 255, 255))
        prompt_rect = prompt_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 100))
        self.display_surface.blit(prompt_surf, prompt_rect)
        name_surf = font_name.render(self.player_name, True, (255, 255, 255))
        name_rect = name_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.display_surface.blit(name_surf, name_rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if len(self.player_name) > 0:
                        self.high_scores.append({'name': self.player_name, 'score': self.score})
                        self.high_scores = sorted(self.high_scores, key=lambda x: x['score'], reverse=True)
                        self.save_highscores()
                        self.state = 'MENU'
                elif event.key == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                elif len(self.player_name) < 4 and event.unicode.isalnum():
                    self.player_name += event.unicode
        pygame.display.update()

    def run(self):
        while self.running:
            if self.state == 'MENU':
                self.run_menu()
            elif self.state == 'PLAYING':
                self.run_game()
            elif self.state == 'PAUSED':
                self.run_pause_menu()
            elif self.state == 'GAME_OVER':
                self.show_game_over()
            elif self.state == 'ENTER_NAME':
                self.run_name_input()
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()
