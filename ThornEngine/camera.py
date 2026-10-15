import math

import numpy as np
import pygame as pg

try:
    from .matrix_functions import rotate, rotate_y
except ImportError:  # pragma: no cover - allow direct execution from the repo root
    try:
        from ThornEngine.matrix_functions import rotate, rotate_y
    except ImportError:
        from matrix_functions import rotate, rotate_y

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
        self.update_aspect_ratio(render.WIDTH, render.HEIGHT)
        self.near_plane = 0.1
        self.far_plane = 100
        self.moving_speed = 3.0
        self.rotate_speed = 1.0
        self.mouse_sensitivity = 0.003
        self.scroll_speed = 0.5
        self.mouse_look = False

    def set_mouse_look(self, enabled):
        if self.mouse_look == enabled:
            return

        self.mouse_look = enabled
        pg.event.set_grab(enabled)
        pg.mouse.set_visible(not enabled)
        pg.mouse.get_rel()

    def handle_mouse_motion(self, relative):
        if self.mouse_look:
            dx, dy = relative
            self.camera_yaw(-dx * self.mouse_sensitivity)
            self.camera_pitch(-dy * self.mouse_sensitivity)

    def control(self, delta_time=1 / 60, allow_rotation=True):
        key = pg.key.get_pressed()
        movement = np.zeros(4)
        if key[pg.K_a]:
            movement -= self.right
        if key[pg.K_d]:
            movement += self.right
        if key[pg.K_q]:
            movement += self.up
        if key[pg.K_e]:
            movement -= self.up
        if key[pg.K_w]:
            movement += self.forward
        if key[pg.K_s]:
            movement -= self.forward

        movement_length = np.linalg.norm(movement[:3])
        if movement_length:
            self.position += (
                movement / movement_length * self.moving_speed * delta_time
            )

        if allow_rotation:
            if key[pg.K_RIGHT]:
                self.camera_yaw(-self.rotate_speed * delta_time)
            if key[pg.K_LEFT]:
                self.camera_yaw(self.rotate_speed * delta_time)
            if key[pg.K_DOWN]:
                self.camera_pitch(-self.rotate_speed * delta_time)
            if key[pg.K_UP]:
                self.camera_pitch(self.rotate_speed * delta_time)

    def scroll(self, amount):
        self.position += self.forward * (amount * self.scroll_speed)

    def update_aspect_ratio(self, width, height):
        if width <= 0 or height <= 0:
            return
        aspect_ratio = width / height
        self.v_fov = 2 * math.atan(math.tan(self.h_fov / 2) / aspect_ratio)

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