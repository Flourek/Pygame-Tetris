import copy
import json
import random

import pygame
import sys, os


from pygame.locals import (
    K_SPACE,
    K_LEFT,
    K_UP,
    K_DOWN,
    K_RIGHT,
    USEREVENT,
    KEYDOWN,
    MOUSEBUTTONUP,
    MOUSEMOTION,
    K_ESCAPE,
    QUIT,
    KEYUP,
    K_p,
    K_r,
    K_m,

)


def assets(relative_path):
    try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, f"assets/{relative_path}")



TETRIS_PIECES = [
    [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
    ],
    [
        [0, 2, 0],
        [2, 2, 2],
        [0, 0, 0]
    ],
    [
        [3, 3],
        [3, 3]
    ],
    [
        [0, 4, 4],
        [4, 4, 0],
    ],
    [
        [5, 5, 0],
        [0, 5, 5],
    ],
    [
        [0, 0, 6],
        [6, 6, 6]
    ],
    [
        [7, 0, 0],
        [7, 7, 7]
    ]

]

PIECE_COLORS = [
    (102, 204, 255),
    (153, 102, 255),
    (255, 255, 153),
    (153, 255, 153),
    (255, 51, 0),
    (51, 51, 255),
    (255, 204, 0)

]

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
BLOCK_SIZE = 30
BORDER_WIDTH = 8

FPS_MAX = 30
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Tetrisus')
icon_surf = pygame.image.load(assets("icon.png")).convert_alpha()
icon_surf.fill((255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
pygame.display.set_icon(icon_surf)
pygame.font.init()
font_smol = pygame.font.SysFont('Arial', 17)
font_big = pygame.font.SysFont('Arial', 23)

pygame.mixer.music.load(assets('korobeiniki.mp3'))
pygame.mixer.music.play(-1)


def surf_with_border(surf, inner_color=(0, 0, 0, 200), outside_color=(255, 255, 255)):
    rect = surf.get_rect()
    box = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    box.fill(outside_color, rect)
    box.fill(inner_color, rect.inflate(-BORDER_WIDTH*2, -BORDER_WIDTH*2))
    surf.blit(box, (0, 0))


class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, id, sprite):
        super(Button, self).__init__()
        self.sprite = sprite
        self.x = x
        self.y = y
        self.id = id
        self.mouse_hovered = False
        self.draw()

    def draw(self):
        self.surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        surf_with_border(self.surf)
        icon = pygame.image.load(assets(f"{self.sprite}.png")).convert_alpha()
        icon = pygame.transform.smoothscale(icon, (30,30))
        self.surf.blit(icon, (15,15))
        self.rect = self.surf.get_rect(x=self.x, y=self.y)

        if self.mouse_hovered:
            gray_overlay = pygame.Surface((60, 60), pygame.SRCALPHA)
            gray_overlay.fill((255, 255, 255, 150))
            self.surf.blit(gray_overlay, (0, 0))

    def click(self):
        if self.id == "restart_button":
            tetris.new_game()

        if self.id == "pausing_button":
            tetris.switch_pause()

        if self.id == "audio_button":
            tetris.switch_mute()

        elif self.id == "settings_button":
            options()

    def update(self):
        if self.id == "pausing_button":
            if tetris.game_paused:
                self.sprite = "play"
            else:
                self.sprite = "pause"
        
        if self.id == "audio_button":        
            if tetris.muted:
                self.sprite = "unmute"
            else:
                self.sprite = "mute"
            
        self.draw()        


class Score(pygame.sprite.Sprite):
    def __init__(self):
        super(Score, self).__init__()
        self.score = 0
        self.cleared_lines = 0
        self.level = 1
        self.draw()

    def draw(self):
        self.surf = pygame.Surface((220, 150), pygame.SRCALPHA)
        surf_with_border(self.surf)
        self.rect = self.surf.get_rect(x=360, y=20)

        current_score_surf = font_big.render(f'SCORE: {self.score}', True, (255, 255, 255))
        level_surf = font_big.render(f'LEVEL: {self.level}', True, (255, 255, 255))
        best_score_surf = font_smol.render(f'D\'BEST: {self.get_best()}', True, (255, 255, 255))

        self.surf.blit(current_score_surf, (15, 20))
        self.surf.blit(level_surf, (15, 50))
        self.surf.blit(best_score_surf, (15, 90))

    def get_score(self):
        return self.score
    
    
    def get_best(self):
        try:
            with open('./score.json', 'r') as f:  
                data = json.load(f)     
                best_score = data['score']
                f.close()
                return best_score
        except IOError:
            return 0

    def set_best(self):
        with open('./score.json', 'w') as f:
            data = {"score": self.score}
            json.dump(data, f)
            f.close()
        self.draw()

    def update(self):
        full_rows = grid.remove_full_rows()

        if full_rows == 1:
            self.score += 100
        elif full_rows == 2:
            self.score += 300
        elif full_rows == 3:
            self.score += 500
        elif full_rows == 4:
            self.score += 800
        else:
            self.score += 18

        self.cleared_lines += full_rows
        if self.level != 1:
            self.level = self.cleared_lines // 10

        if tetris.level_speed > 1:
            tetris.level_speed = 16 - self.level

        self.draw()


class Queue(pygame.sprite.Sprite):
    def __init__(self):
        super(Queue, self).__init__()
        self.next_piece = random.randint(0, 6)
        self.draw()

    def draw(self):
        self.surf = pygame.Surface((220, 160), pygame.SRCALPHA)
        surf_with_border(self.surf)
        self.rect = self.surf.get_rect(x=360, y=190)

        next_surf = font_big.render('NEXT:', True, (255, 255, 255))
        self.surf.blit(next_surf, (75, 15))

    def next(self):
        current_piece = self.next_piece
        self.next_piece = random.randint(0, 6)
        self.draw()
        
        next_piece = TETRIS_PIECES[self.next_piece]
        x = 100 - int((len(next_piece[0]) * BLOCK_SIZE) / 2) 
        Piece.draw(self.surf, next_piece, (x, 50))
        
        return TETRIS_PIECES[current_piece]


class Keybinds(pygame.sprite.Sprite):
    def __init__(self):
        super(Keybinds, self).__init__()
        self.surf = pygame.Surface((216, 201), pygame.SRCALPHA)
        surf_with_border(self.surf)
        self.rect = self.surf.get_rect(x=360, y=580)
      
        drop_surf = font_smol.render('Space to drop piece', True, (255, 255, 255))
        restart_surf = font_smol.render('R to restart', True, (255, 255, 255))
        rotate_surf = font_smol.render('Arrow Up to rotate', True, (255, 255, 255))
        quit_surf = font_smol.render('Escape to quit', True, (255, 255, 255))
        pause_surf = font_smol.render('P to pause', True, (255, 255, 255))
        mute_surf = font_smol.render('M to mute', True, (255, 255, 255))
        self.surf.blit(drop_surf, (15, 20))
        self.surf.blit(rotate_surf, (15, 45))
        self.surf.blit(restart_surf, (15, 70))
        self.surf.blit(pause_surf, (15, 95))
        self.surf.blit(mute_surf, (15, 120))
        self.surf.blit(quit_surf, (15, 145))


class Game_Over(pygame.sprite.Sprite):
    def __init__(self):
        super(Game_Over, self).__init__()
        self.draw()

    def draw(self):
        self.surf = pygame.Surface((200, 150), pygame.SRCALPHA)
        surf_with_border(self.surf, inner_color=(0, 0, 0))
        self.rect = self.surf.get_rect(x=200, y=300)

        game_over_surf = font_big.render('game over e', True, (255, 40, 40))
        self.surf.blit(game_over_surf, (36, 20))
        score_surf = font_big.render(
            f'Your score: {score.score}', True, (255, 40, 40))
        self.surf.blit(score_surf, (25, 45))

        if score.score > score.get_best():
            new_best_surf = font_smol.render(
                'New best tho', True, (255, 40, 40))
            self.surf.blit(new_best_surf, (30, 97))

        screen.blit(self.surf, self.rect)


class Grid(pygame.sprite.Sprite):
    def __init__(self):
        super(Grid, self).__init__()
        self.width = 10
        self.height = 25
        self.surf = None
        self.board = [[0 for j in range(self.width)]
                      for i in range(self.height)]
        self.draw()

    def draw(self):
        self.surf = pygame.Surface((311 + BORDER_WIDTH*2, 745 + BORDER_WIDTH*2), pygame.SRCALPHA)
        self.surf.blit(pygame.image.load(assets("moscow.png")), (0, 0))
        surf_with_border(self.surf)
        self.rect = self.surf.get_rect().move(20, 20)

    def update(self):
        self.draw()
        Piece.draw(self.surf, self.board[1::])

    def remove_full_rows(self):
        full_rows = [i for i, row in enumerate(self.board) if 0 not in row]

        for i in full_rows:
            pygame.time.delay(16)
            del self.board[i]
            self.board.insert(0, [0 for _ in range(self.width)])

        return len(full_rows)


class Piece:
    def __init__(self, piece):
        self.x = 4
        self.y = 0
        self.piece = piece
        self.change_board()

    @staticmethod
    def draw(surf, list_2D, offset=(0, 0)):
        for y, row in enumerate(list_2D):
            for x, piece_block in enumerate(row):
                if piece_block != 0:
                    outer_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
                    inner_surf = pygame.Surface(
                        (BLOCK_SIZE - 10, BLOCK_SIZE - 10))

                    if piece_block < len(TETRIS_PIECES) + 1:
                        color = PIECE_COLORS[piece_block - 1]
                    else:
                        color = (200, 200, 200)

                    inner_surf.fill(color)
                    outer_surf.fill([max(0, i - 30) for i in color])

                    outer_rect = inner_surf.get_rect(x=offset[0] + BORDER_WIDTH + (BLOCK_SIZE + 1) * x + 1,
                                                     y=offset[1] + BORDER_WIDTH + (BLOCK_SIZE + 1) * y + 1)
                    inner_rect = outer_surf.get_rect(
                        x=outer_rect.x + 5, y=outer_rect.y + 5)

                    surf.blit(outer_surf, outer_rect)
                    surf.blit(inner_surf, inner_rect)


    def change_board(self, erase=False):
        for i, row in enumerate(self.piece):
            for j, piece_block in enumerate(row):

                if erase:
                    grid.board[min(grid.height - 1, self.y + i)][min(grid.width - 1, self.x + j)] -= piece_block
                else:
                    grid.board[min(grid.height - 1, self.y + i)][min(grid.width - 1, self.x + j)] += piece_block


    def is_valid_move(self, x=0, y=0, rotate=False):
        new_board = copy.deepcopy(grid.board)

        if rotate:
            changed_piece = [
                [self.piece[j][i]
                    for j, _ in reversed(list(enumerate(self.piece)))]
                for i, _ in enumerate(self.piece[0])]
        else:
            changed_piece = self.piece

        for i, row in enumerate(changed_piece):
            for j, piece_block in enumerate(row):

                # Keep in boundaries
                if piece_block != 0:
                    # Right
                    if self.x + j + x == grid.width:
                        return False

                    # Left
                    if self.x + j + x == -1:
                        return False

                    # Bottom
                    if self.y + i + y == grid.height:
                        return False

                    # This makes sure that if u add together 2 color values it doesn't end up as one of the available colors
                    piece_block = len(TETRIS_PIECES) + 1

                new_board_block = new_board[min(
                    grid.height - 1, self.y + i + y)][min(grid.width - 1, self.x + j + x)]
                new_board_block += piece_block

                # Only true if 2 blocks other than 0 are added to eachother
                if new_board_block > len(TETRIS_PIECES) + 1:
                    return False

        return True


    def move_horizontaly(self, x: int):
        self.change_board(erase=True)

        if not self.is_valid_move(x=x):
            pass
        else:
            self.x += x

        self.change_board()


    def move_down(self):
        self.change_board(erase=True)

        if not self.is_valid_move(y=1):
            pygame.event.clear(USEREVENT + 1)
            pygame.event.post(PIECE_PLACED)
        else:
            self.y += 1

        self.change_board()


    def drop(self):
        self.change_board(erase=True)

        for _ in range(grid.height):
            if self.is_valid_move(y=1):
                pygame.event.clear(USEREVENT + 1)
                pygame.event.post(PIECE_PLACED)
                self.y += 1
            else:
                break

        self.change_board()


    def rotate_clockwise(self):
        self.change_board(erase=True)

        if self.is_valid_move(rotate=True):
            self.piece = [
                [self.piece[j][i]
                    for j, _ in reversed(list(enumerate(self.piece)))]
                for i, _ in enumerate(self.piece[0])
            ]

        self.change_board()


class Tetris():
    def __init__(self):
        self.game_paused = False
        self.game_over = False
        self.muted = False
        self.level_speed = 15

    def switch_pause(self):
        self.game_paused = not self.game_paused

    def switch_mute(self):
        self.muted = not self.muted

        if self.muted:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()

    def new_game(self):
        pygame.event.post(NEW_GAME)


def options():
    running = True
    while running:
        screen.fill((0,0,0))
        
        for entity in all_sprites:
            screen.blit(entity.surf, entity.rect)

        yes = pygame.image.load(assets("yes.png")).convert_alpha()
        yes = pygame.transform.smoothscale(yes, (500,500))
        screen.blit(yes, (0,300))

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False        
        
        pygame.display.update()
        clock.tick(FPS_MAX)


PIECE_PLACED = pygame.event.Event(pygame.USEREVENT + 1, attr1='Event1')
NEW_GAME = pygame.event.Event(pygame.USEREVENT + 2, attr1='Event1')
pygame.key.set_repeat(250, 100)

clock = pygame.time.Clock()
counter_cooldown = 15
counter = 0

all_sprites = pygame.sprite.Group()
buttons = pygame.sprite.Group()
buttons.add(Button(360, 527, "restart_button", "restart"), Button(412, 527, "pausing_button", "pause"), 
            Button(464, 527, "audio_button","mute"), Button(516, 527, "settings_button", "yes"))

tetris = Tetris()
score = Score()

pygame.event.post(NEW_GAME)

running = True

while running:
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event == NEW_GAME:
            if score.get_score() > score.get_best():
                score.set_best()

            tetris = Tetris()
            grid = Grid()
            score = Score()
            queue = Queue()

            all_sprites.empty()
            all_sprites.add(grid, score, queue, buttons, Keybinds())

            pygame.event.clear(USEREVENT + 1)
            live_piece = Piece(queue.next())

        if event.type == QUIT:
            running = False

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False

            if event.key == K_p:
                tetris.switch_pause()

            if event.key == K_m:
                tetris.switch_mute()

            if event.key == K_r:
                pygame.event.post(NEW_GAME)

            if not tetris.game_over and not tetris.game_paused:
                if event.key == K_LEFT:
                    live_piece.move_horizontaly(x=-1)

                if event.key == K_RIGHT:
                    live_piece.move_horizontaly(x=1)

                if event.key == K_UP:
                    live_piece.rotate_clockwise()

                if event.key == K_DOWN:
                    counter = 0
                    tetris.level_speed = 1

                if event.key == K_SPACE:
                    live_piece.drop()

        if event.type == KEYUP:
            if event.key == K_DOWN:
                tetris.level_speed = 16 - score.level

        if event.type == MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            hovered_sprites = [s for s in buttons if s.rect.collidepoint(mouse_pos)]

            for button in buttons:
                if button in hovered_sprites:
                    button.mouse_hovered = True
                    button.update()
                else:
                    button.mouse_hovered = False

        if event.type == MOUSEBUTTONUP:
            mouse_pos = pygame.mouse.get_pos()

            clicked_sprites = [s for s in buttons if s.rect.collidepoint(mouse_pos)]
            for button in clicked_sprites:
                button.click()

        if event == PIECE_PLACED:
            score.update()

            if grid.board[1] != [0 for i in range(grid.width)]:
                tetris.game_over = True
                break

            live_piece = Piece(queue.next())


    if not tetris.game_over and not tetris.game_paused:
        grid.update()

        counter += 1
        if counter >= tetris.level_speed:
            live_piece.move_down()
            counter = 0

    buttons.update()

    for entity in all_sprites:
        screen.blit(entity.surf, entity.rect)

    if tetris.game_over and not tetris.game_paused:
        Game_Over().draw()

    pygame.display.flip()
    clock.tick(FPS_MAX)


