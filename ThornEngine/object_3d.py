import numpy as np
import pygame as pg
from matrix_functions import rotate, rotate_y, rotate_z, scale, translate

class Object3D:
    def __init__(self, render):
        self.render = render
        self.vertexes = np.array([
            (-0.5, -0.5, -0.5, 1),
            (-0.5, 0.5, -0.5, 1),
            (0.5, 0.5, -0.5, 1),
            (0.5, -0.5, -0.5, 1),
            (-0.5, -0.5, 0.5, 1),
            (-0.5, 0.5, 0.5, 1),
            (0.5, 0.5, 0.5, 1),
            (0.5, -0.5, 0.5, 1),
        ])

        self.faces = np.array([
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (0, 4, 5, 1),
            (2, 3, 7, 6),
            (1, 2, 6, 5),
            (0, 3, 7, 4)])

        self.font = pg.font.SysFont('Arial', 30, bold=True)
        self.color_faces = [(pg.Color('orange'), face) for face in self.faces]
        self.movement_flag = True
        self.draw_vertexes = True
        self.label = ''

    def movement(self):
        if self.movement_flag:
            self.rotate_y(pg.time.get_ticks() * 0.0000005)

    def screen_projection(self):
        vertexes = self.vertexes @ self.render.camera.camera_matrix()
        vertexes = vertexes @ self.render.projection.projection_matrix
        w = vertexes[:, -1]
        depth_valid = w > 0
        vertexes[depth_valid] /= w[depth_valid, np.newaxis]
        visible = depth_valid & np.all(
            (vertexes[:, :3] >= -1) & (vertexes[:, :3] <= 1),
            axis=1,
        )
        vertexes = vertexes @ self.render.projection.to_screen_matrix
        vertexes = vertexes[:, :2]

        for index, color_face in enumerate(self.color_faces):
            color, face = color_face
            if np.all(depth_valid[face]):
                polygon = vertexes[face]
                pg.draw.polygon(self.render.screen, color, polygon, 3)
                if self.label:
                    text = self.font.render(
                        self.label[index], True, pg.Color('white')
                    )
                    label_position = polygon[-1].astype(int) + np.array([8, -8])
                    self.render.screen.blit(text, label_position)

        return vertexes, visible

    def draw(self):
        vertexes, visible = self.screen_projection()

        for vertex, is_valid in zip(vertexes, visible):
            if is_valid:
                pg.draw.circle(self.render.screen, pg.Color('white'), vertex, 6)

        self.movement()

    def translate(self, pos):
        self.vertexes = self.vertexes @ translate(pos)

    def scale(self, scale_to):
        self.vertexes = self.vertexes @ scale(scale_to)

    def rotate_x(self, angle):
        self.vertexes = self.vertexes @ rotate(angle)

    def rotate_y(self, angle):
        self.vertexes = self.vertexes @ rotate_y(angle)

    def rotate_z(self, angle):
        self.vertexes = self.vertexes @ rotate_z(angle)

class Axes(Object3D):
    def __init__(self, render):
        super().__init__(render)
        self.vertexes = np.array([
            (-0.5, 0, 0, 1),
            (0.5, 0, 0, 1),
            (0, -0.5, 0, 1),
            (0, 0.5, 0, 1),
            (0, 0, -0.5, 1),
            (0, 0, 0.5, 1),
        ])
        self.faces = np.array([(0, 1), (2, 3), (4, 5)])
        self.colors = [pg.Color('red'), pg.Color('green'), pg.Color('blue')]
        self.color_faces = [(color, face) for color, face in zip(self.colors, self.faces)]
        self.draw_vertexes = False
        self.label = 'XYZ'