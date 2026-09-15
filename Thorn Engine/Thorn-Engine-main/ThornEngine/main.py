from object_3d import *
from camera import *
from object_3d import Object3D
from projection import *
import pygame as pg


class SoftwareRender:
    def __init__(self):
        pg.init()
        self.RES = self.WIDTH, self.HEIGHT = 1600, 900
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.FPS = 60
        self.fullscreen = False
        self.screen = pg.display.set_mode(self.RES, pg.RESIZABLE)
        self.clock = pg.time.Clock()
        self.create_object()

    def resize(self, size):
        self.WIDTH, self.HEIGHT = size
        self.RES = self.WIDTH, self.HEIGHT
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.screen = pg.display.set_mode(self.RES, pg.RESIZABLE)
        self.camera.v_fov = self.camera.h_fov * (self.HEIGHT / self.WIDTH)
        self.projection = Projection(self)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
        else:
            self.screen = pg.display.set_mode(self.RES, pg.RESIZABLE)
        self.WIDTH, self.HEIGHT = self.screen.get_size()
        self.RES = self.WIDTH, self.HEIGHT
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.camera.v_fov = self.camera.h_fov * (self.HEIGHT / self.WIDTH)
        self.projection = Projection(self)

    def create_object(self):
        self.camera = Camera(self, [-.5, 1, -4])
        self.projection = Projection(self)
        self.object = Object3D(self)
        self.object.movement_flag = False
        self.object.rotate_y(math.pi / 6)
        self.object.translate([-0.5, 1.0, 1.5])
        self.axes = Axes(self)
        self.axes.movement_flag = False
        self.axes.scale(2.5)
        self.axes.rotate_y(math.pi / 6)
        self.axes.translate([-0.5, 1.0, 1.5])


    def draw(self):
        self.screen.fill(pg.Color("#2f5559"))
        self.axes.draw()
        self.object.draw()

    def run(self):
        while True:
            self.draw()
            self.camera.control()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    return
                if event.type == pg.KEYDOWN and event.key == pg.K_F11:
                    self.toggle_fullscreen()
                elif event.type == pg.VIDEORESIZE and not self.fullscreen:
                    self.resize(event.size)
            pg.display.set_caption("ThornEngine")
            pg.display.flip()
            self.clock.tick(self.FPS)

if __name__ == "__main__":
    app = SoftwareRender()
    app.run()