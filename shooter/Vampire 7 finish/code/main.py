import json
from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites

from random import randint, choice

class Game:
    def __init__(self):
        # setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'MENU'

        # score
        self.score = 0
        self.player_name = ''
        self.high_scores = []
        self.load_highscores()

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        # gun timer
        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 100

        # enemy timer
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 1000)
        self.spawn_positions = []

        # audio
        self.shoot_sound = pygame.mixer.Sound(join('audio', 'shoot.wav'))
        self.shoot_sound.set_volume(0.2)
        self.impact_sound = pygame.mixer.Sound(join('audio', 'impact.ogg'))
        self.music = pygame.mixer.Sound(join('audio', 'music.wav'))
        self.music.set_volume(0.5)
        # self.music.play(loops = -1)

        # setup
        self.load_images()
        self.setup()

    def load_highscores(self):
        try:
            with open(join('highscores.json'), 'r') as f:
                self.high_scores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.high_scores = []

    def save_highscores(self):
        with open(join('highscores.json'), 'w') as f:
            json.dump(self.high_scores, f, indent=4)

    def load_images(self):
        self.bullet_surf = pygame.image.load(join('images', 'gun', 'bullet.png')).convert_alpha()
        self.heart_surf = pygame.image.load(join('images', 'ui', 'heart.png')).convert_alpha()
        self.heart_surf = pygame.transform.rotozoom(self.heart_surf, 0, 0.05)


        folders = list(walk(join('images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key = lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

    def setup(self):
        map = load_pygame(join('data', 'maps', 'world.tmx'))

        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, self.all_sprites)

        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x,obj.y), self.all_sprites, self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites)
            else:
                self.spawn_positions.append((obj.x, obj.y))
    
    def reset(self):
        # Reset the game for a new round
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
        self.display_surface.fill('black')
        font_title = pygame.font.Font(None, 100)
        font_button = pygame.font.Font(None, 50)
        font_score = pygame.font.Font(None, 40)

        # Title
        title_text = font_title.render('Vampire Survivor', True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 4))
        self.display_surface.blit(title_text, title_rect)

        # Buttons
        start_button = pygame.Rect(WINDOW_WIDTH / 2 - 100, WINDOW_HEIGHT / 2, 200, 50)
        quit_button = pygame.Rect(WINDOW_WIDTH / 2 - 100, WINDOW_HEIGHT / 2 + 60, 200, 50)
        pygame.draw.rect(self.display_surface, (0, 255, 0), start_button)
        pygame.draw.rect(self.display_surface, (255, 0, 0), quit_button)
        start_text = font_button.render('Start', True, (255, 255, 255))
        quit_text = font_button.render('Quit', True, (255, 255, 255))
        self.display_surface.blit(start_text, start_text.get_rect(center=start_button.center))
        self.display_surface.blit(quit_text, quit_text.get_rect(center=quit_button.center))
        
        # High Scores
        score_title_text = font_button.render('High Scores', True, (255, 255, 255))
        score_title_rect = score_title_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 150))
        self.display_surface.blit(score_title_text, score_title_rect)

        for i, score_entry in enumerate(self.high_scores[:3]):
            score_text = f"{i+1}. {score_entry['name']} - {score_entry['score']}"
            score_surf = font_score.render(score_text, True, (255, 255, 255))
            score_rect = score_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 100 + i * 30))
            self.display_surface.blit(score_surf, score_rect)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    self.reset()
                    self.state = 'PLAYING'
                if quit_button.collidepoint(event.pos):
                    self.running = False
        
        pygame.display.update()

    def run_game(self):
        dt = self.clock.tick() / 1000

        # event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == self.enemy_event:
                Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)

        # update
        self.gun_timer()
        self.input()
        self.all_sprites.update(dt)
        
        # collisions
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

        # draw
        self.display_surface.fill('black')
        self.all_sprites.draw(self.player.rect.center)
        # Hearts
        for i in range(self.player.health):
            x = 10 + i * (self.heart_surf.get_width() + 4)
            y = 10
            self.display_surface.blit(self.heart_surf, (x, y))
        # Score
        font = pygame.font.Font(None, 40)
        score_text = f"Score: {self.score}"
        score_surf = font.render(score_text, True, (255, 255, 255))
        score_rect = score_surf.get_rect(topright=(WINDOW_WIDTH - 20, 10))
        self.display_surface.blit(score_surf, score_rect)


        pygame.display.update()

    def show_game_over(self):
        self.display_surface.fill('black')
        font = pygame.font.Font(None, 100)
        text = font.render('Game Over', True, (255, 255, 255))
        text_rect = text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.display_surface.blit(text, text_rect)
        pygame.display.update()
        pygame.time.wait(2000)
        self.state = 'ENTER_NAME'

    def run_name_input(self):
        self.display_surface.fill('black')
        font_prompt = pygame.font.Font(None, 60)
        font_name = pygame.font.Font(None, 80)
        
        # Prompt
        prompt_text = f"Your Score: {self.score}. Enter your name (4 chars):"
        prompt_surf = font_prompt.render(prompt_text, True, (255, 255, 255))
        prompt_rect = prompt_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 100))
        self.display_surface.blit(prompt_surf, prompt_rect)

        # Name Input Box
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
                elif len(self.player_name) < 4:
                    self.player_name += event.unicode
        
        pygame.display.update()


    def run(self):
        while self.running:
            if self.state == 'MENU':
                self.run_menu()
            elif self.state == 'PLAYING':
                self.run_game()
            elif self.state == 'GAME_OVER':
                self.show_game_over()
            elif self.state == 'ENTER_NAME':
                self.run_name_input()
        
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()