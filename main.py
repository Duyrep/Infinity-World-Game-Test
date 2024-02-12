import numpy as np
import pygame as pg
import sys, os, math, pickle


class Main:

    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((640, 480), pg.RESIZABLE | pg.DOUBLEBUF)
        self.clock = pg.time.Clock()
        self.fps = 120
        self.font = pg.font.SysFont(None, 20)
        self.block_size = 10
        self.screen_size = self.screen.get_size()
        self.player_pos = [0, 0]
        self.player_xy = [0, 0]
        self.player_chunk_pos = [0, 0]
        self.player_rotate = 0
        self.player_speed = 400
        self.chunk_size = 32
        self.zoom_int = 40
        self.zoom = 1
        self.zoom_max_min = (2, 0.4)
        self.chunk_render = 2
        self.dt = self.clock.tick(self.fps) / 1000
        self.world = {}
        self.load_world()
        self.scroll = [self.player_pos[0] * self.zoom - 0 - self.screen_size[0] / 2,
                       self.player_pos[1] * self.zoom - 0 - self.screen_size[1] / 2]
        self.cell_size = 10
        self.block_img_dict = {}
        self.unit_img_dict = {}
        self.load_img()
        self.block_img_dict_resize = {}
        self.unit_img_dict_resize = {}
        self.resize_img()
        pg.display.set_caption("Game")
    
    def event(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                with open("world.pkl", "wb") as file:
                    pickle.dump(self.world, file)
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEWHEEL:
                if event.y > 0 and self.zoom < self.zoom_max_min[0]:
                    self.zoom_int += 8
                if event.y < 0 and self.zoom > self.zoom_max_min[1]:
                    self.zoom_int -= 8
                self.zoom = self.zoom_int / 40
                self.cell_size = self.zoom * 10
                self.resize_img()
                self.scroll[0] += (self.player_pos[0] * self.zoom - self.scroll[0] - self.screen_size[0] / 2)
                self.scroll[1] += (self.player_pos[1] * self.zoom - self.scroll[1] - self.screen_size[1] / 2)

        dt = self.clock.tick(self.fps) / 1000
        keys = pg.key.get_pressed()
        move_vec = pg.math.Vector2(0, 0)
        target_rotate = self.player_rotate

        if keys[pg.K_w]:
            move_vec.y -= 1
            target_rotate = 0
        if keys[pg.K_s]:
            move_vec.y += 1
            target_rotate = 180
        if keys[pg.K_a]:
            move_vec.x -= 1
            target_rotate = 90
        if keys[pg.K_d]:
            move_vec.x += 1
            target_rotate = -90

        # Calculate the difference in angle in a way that always turns clockwise
        angle_diff = (target_rotate - self.player_rotate) % 360
        if angle_diff > 180:
            angle_diff -= 360

        # Lerp rotation
        self.player_rotate += angle_diff * 0.1

        if move_vec.length() > 0:
            move_vec.scale_to_length(self.player_speed * self.zoom * dt)
        self.player_pos += move_vec

        if keys[pg.K_w] and keys[pg.K_a]:
            target_rotate = 45
        if keys[pg.K_w] and keys[pg.K_d]:
            target_rotate = -45
        if keys[pg.K_s] and keys[pg.K_a]:
            target_rotate = 135
        if keys[pg.K_s] and keys[pg.K_d]:
            target_rotate = -135

        angle_diff_diag = (target_rotate - self.player_rotate) % 360
        if angle_diff_diag > 180:
            angle_diff_diag -= 360

        self.player_rotate += angle_diff_diag * 0.6

        mouse = pg.mouse.get_pressed()
        if mouse[0]:
            scroll = [self.scroll[0], self.scroll[1]]
            scroll[0] += self.player_pos[0] * self.zoom - scroll[0] - self.screen_size[0] / 2
            scroll[1] += self.player_pos[1] * self.zoom - scroll[1] - self.screen_size[1] / 2
            mouse_pos = pg.mouse.get_pos()
            mouse_pos = ((self.player_pos[0] * self.zoom + mouse_pos[0] - self.screen_size[0] / 2) - scroll[0],
                         (self.player_pos[1] * self.zoom + mouse_pos[1] - self.screen_size[1] / 2) - scroll[1])
            d_pos = (mouse_pos[0] - (self.player_pos[0] * self.zoom - scroll[0]),
                     mouse_pos[1] - (self.player_pos[1] * self.zoom - scroll[1]))
            pg.draw.rect(self.screen, "yellow", (mouse_pos[0], mouse_pos[1], 5, 5))
            self.player_rotate = math.degrees(math.atan2(-d_pos[0], d_pos[1]) * -1 + 135)
            
    def draw(self):
        self.screen.fill("black")
        chunk_render = {}
        surface_chunk = {}
        for i in range(-self.chunk_render, self.chunk_render):
            for j in range(-self.chunk_render, self.chunk_render):
                chunk_render[(int(self.player_chunk_pos[0] + i), int(self.player_chunk_pos[1] + j))] = self.world[(int(self.player_chunk_pos[0] + i), int(self.player_chunk_pos[1] + j))]
        chunk_size_px = self.cell_size * self.chunk_size
        for chunk_pos, chunk in chunk_render.items():
            surface = pg.Surface([chunk_size_px] * 2, pg.HWSURFACE)
            for i in range(self.chunk_size):
                for j in range(self.chunk_size):
                    if chunk[i][j] == 0:
                        surface.blit(self.block_img_dict_resize["grass"], (i * self.cell_size, j * self.cell_size))
                    elif chunk[i][j] == 1:
                        surface.blit(self.block_img_dict_resize["sand"], (i * self.cell_size, j * self.cell_size))
            surface_chunk[chunk_pos] = surface
        for chunk_pos, surface in surface_chunk.items():
            surface_pos = (chunk_pos[0] * self.chunk_size * self.cell_size - self.scroll[0], chunk_pos[1] * self.chunk_size * self.cell_size - self.scroll[1])
            if -self.cell_size * self.chunk_size < surface_pos[0] < self.screen_size[0] and -self.cell_size * self.chunk_size < surface_pos[1] < self.screen_size[1]:
                self.screen.blit(surface, surface_pos)
                pg.draw.rect(self.screen, "black", (surface_pos[0], surface_pos[1], chunk_size_px, chunk_size_px), 1)
        surface_unit = pg.Surface(self.unit_img_dict_resize["gamma"].get_size(), pg.SRCALPHA)
        surface_unit.blit(pg.transform.rotate(self.unit_img_dict_resize["gamma"], self.player_rotate), (0, 0))
        surface_unit.blit(pg.transform.rotate(self.unit_img_dict_resize["gamma-cell"], self.player_rotate), (0, 0))
        self.screen.blit(
            surface_unit,
            ((self.player_pos[0] * self.zoom - self.scroll[0]) - self.unit_img_dict_resize["gamma"].get_rect().center[0],
             (self.player_pos[1] * self.zoom - self.scroll[1]) - self.unit_img_dict_resize["gamma"].get_rect().center[1]))
        pg.draw.rect(self.screen, "red",
            ((self.player_pos[0] * self.zoom - self.scroll[0]) - self.unit_img_dict_resize["gamma"].get_rect().center[0],
             (self.player_pos[1] * self.zoom - self.scroll[1]) - self.unit_img_dict_resize["gamma"].get_rect().center[1],
             surface_unit.get_size()[0], surface_unit.get_size()[1]), 1)
        self.draw_text(0, 0, f"Fps:{self.clock.get_fps():.1f}")
        self.draw_text(0, 20, f"XY:{self.player_xy[0]:.1f} / {self.player_xy[1]:.1f}")
        self.draw_text(0, 40, f"Chunk XY:{self.player_chunk_pos[0]:.1f} / {self.player_chunk_pos[1]:.1f}")
        self.draw_text(0, 60, f"Zoom:{self.zoom}x")
        self.draw_text(0, 80, f"Scroll:{self.scroll[0]:.1f} / {self.scroll[1]:.1f}")
        self.draw_text(0, 100, f"Pos:{self.player_pos[0]:.1f} / {self.player_pos[1]:.1f}")
    
    def update(self):
        dt = (self.clock.tick(60) / 1000.0) * self.player_speed
        self.clock.tick(self.fps)
        self.dt = self.clock.tick(self.fps) / 1000
        for i in range(-5, 5):
            for j in range(-5, 5):
                if (int(self.player_chunk_pos[0] + i), int(self.player_chunk_pos[1] + j)) not in self.world:
                    self.world[(int(self.player_chunk_pos[0] + i), int(self.player_chunk_pos[1] + j))] = self.generate_chunk()
        if self.screen_size != self.screen.get_size():
            self.screen_size = self.screen.get_size()
            self.scroll[0] += (self.player_pos[0] * self.zoom - self.scroll[0] - self.screen_size[0] / 2)
            self.scroll[1] += (self.player_pos[1] * self.zoom - self.scroll[1] - self.screen_size[1] / 2)
        self.player_xy[0] = self.player_pos[0] * self.zoom / self.cell_size
        self.player_xy[1] = self.player_pos[1] * self.zoom / self.cell_size
        self.player_chunk_pos[0] = self.player_xy[0] / self.chunk_size
        self.player_chunk_pos[1] = self.player_xy[1] / self.chunk_size
        self.scroll[0] += ((self.player_pos[0] * self.zoom - self.scroll[0] - self.screen_size[0] / 2) / 20) * dt
        self.scroll[1] += ((self.player_pos[1] * self.zoom - self.scroll[1] - self.screen_size[1] / 2) / 20) * dt
        self.clock.tick(self.fps)
        pg.display.update()
    
    def load_world(self):
        try:
            with open("world.pkl", "rb") as file:
                self.world = pickle.load(file)
        except:
            with open("world.pkl", "wb") as file:
                pickle.dump(self.world, file)
    
    def load_img(self):
        for file in os.listdir("img/block"):
            if file.endswith(".jpg") or file.endswith(".png"):
                self.block_img_dict[file[:-4]] = pg.image.load(f"img/block/{file}").convert()
        for file in os.listdir("img/unit"):
            if file.endswith(".jpg") or file.endswith(".png"):
                self.unit_img_dict[file[:-4]] = pg.image.load(f"img/unit/{file}").convert_alpha()
    
    def resize_img(self):
        for _, img in self.block_img_dict.items():
            self.block_img_dict_resize[_] = pg.transform.scale(img, [self.cell_size] * 2)
        for _, img in self.unit_img_dict.items():
            self.unit_img_dict_resize[_] = pg.transform.scale(img, [self.cell_size * 2.5] * 2)
    
    def draw_text(self, x, y, text):
        font_text = self.font.render(text, True, "white")
        self.screen.blit(font_text, (x, y))
    
    def generate_chunk(self):
        chunk_data = np.zeros([self.chunk_size] * 2)
        return chunk_data
    
    def run(self):
        while True:
            self.event()
            self.update()
            self.draw()

if __name__ == "__main__":
    main = Main()
    main.run()