import pygame as pg
from matrix_functions import *

class Camera:
    def __init__(self, render, position):
        self.render = render
        self.position = np.array([*position, 1.0])
        self.forward = np.array([0, 0, 1, 0])
        self.up = np.array([0, 1, 0, 0])
        self.right = np.array([1, 0, 0, 0])
        self.yaw = 0.0
        self.pitch = 0.0
        self.h_fov = math.pi / 3
        self.v_fov = self.h_fov * (render.HEIGHT / render.WIDTH)
        self.near_plane = 0.1
        self.far_plane = 100
        self.moving_speed = 0.02
        self.rotate_speed = 0.01

    def control(self):
        key = pg.key.get_pressed()
        if key[pg.K_a]:
            self.position -= self.right * self.moving_speed
        if key[pg.K_d]:
            self.position += self.right * self.moving_speed
        if key[pg.K_q]:
            self.position += self.up * self.moving_speed
        if key[pg.K_e]:
            self.position -= self.up * self.moving_speed
        if key[pg.K_w]:
            self.position += self.forward * self.moving_speed
        if key[pg.K_s]:
            self.position -= self.forward * self.moving_speed

        if key[pg.K_RIGHT]:
            self.camera_yaw(-self.rotate_speed)
        if key[pg.K_LEFT]:
            self.camera_yaw(self.rotate_speed)
        if key[pg.K_DOWN]:
            self.camera_pitch(-self.rotate_speed)
        if key[pg.K_UP]:
            self.camera_pitch(self.rotate_speed)

    def camera_yaw(self, angle):
        self.yaw += angle
        self._update_basis()

    def camera_pitch(self, angle):
        limit = math.pi / 2 - 0.01
        self.pitch = max(-limit, min(limit, self.pitch + angle))
        self._update_basis()

    def _update_basis(self):
        yaw_matrix = rotate_y(self.yaw)
        pitch_matrix = rotate(self.pitch)
        self.right = np.array([1, 0, 0, 0]) @ yaw_matrix
        self.up = np.array([0, 1, 0, 0]) @ pitch_matrix @ yaw_matrix
        self.forward = np.array([0, 0, 1, 0]) @ pitch_matrix @ yaw_matrix

    def translate_matrix(self):
        x, y, z, w = self.position
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [-x, -y, -z, 1]
        ])

    def rotate_matrix(self):
        rx, ry, rz, w = self.right
        fx, fy, fz, w = self.forward
        ux, uy, uz, w = self.up
        return np.array([
            [rx, ux, fx, 0],
            [ry, uy, fy, 0],
            [rz, uz, fz, 0],
            [0, 0, 0, 1]
        ])

    def camera_matrix(self):
        return self.translate_matrix() @ self.rotate_matrix()