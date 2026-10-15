import numpy as np
import pygame as pg

try:
    from .matrix_functions import rotate, rotate_y, rotate_z, scale, translate
except ImportError:  # pragma: no cover - allow direct execution from the repo root
    try:
        from ThornEngine.matrix_functions import rotate, rotate_y, rotate_z, scale, translate
    except ImportError:
        from matrix_functions import rotate, rotate_y, rotate_z, scale, translate


class Object3D:
    def __init__(self, render):
        self.render = render
        self.position = np.zeros(3, dtype=float)
        self.rotation = np.zeros(3, dtype=float)
        self.scale_factors = np.ones(3, dtype=float)
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

        self.font = None
        if pg.font and pg.font.get_init():
            try:
                self.font = pg.font.SysFont('Arial', 30, bold=True)
            except (AttributeError, NotImplementedError):
                self.font = None
        self.color_faces = [(pg.Color('orange'), face) for face in self.faces]
        self.movement_flag = True
        self.draw_vertexes = True
        self.label = ''

    def movement(self):
        if self.movement_flag:
            self.rotate_y(pg.time.get_ticks() * 0.0000005)

    def screen_projection(self):
        camera_vertexes = self.vertexes @ self.render.camera.camera_matrix()
        clip_vertexes = camera_vertexes @ self.render.projection.projection_matrix
        visible = self._inside_clip_volume(clip_vertexes)
        screen_vertexes = self._to_screen(clip_vertexes)

        face_depths = []
        for index, (color, face) in enumerate(self.color_faces):
            clipped = self._clip_polygon(clip_vertexes[face])
            if len(clipped) < 2:
                continue
            points = self._to_screen(np.asarray(clipped))
            points = np.rint(points).astype(int)
            points[:, 0] = np.clip(points[:, 0], 0, self.render.WIDTH - 1)
            points[:, 1] = np.clip(points[:, 1], 0, self.render.HEIGHT - 1)
            depth = float(np.mean(camera_vertexes[face, 2]))
            face_depths.append((depth, index, color, points))

        for _, index, color, points in sorted(face_depths, reverse=True, key=lambda item: item[0]):
            if len(points) == 2:
                pg.draw.line(self.render.screen, color, points[0], points[1], 2)
            else:
                pg.draw.polygon(self.render.screen, color, points, 3)
            if self.label and index < len(self.label) and self.font is not None:
                text = self.font.render(self.label[index], True, pg.Color("white"))
                label_position = points[-1] + np.array([8, -8])
                self.render.screen.blit(text, label_position)

        return screen_vertexes, visible

    @staticmethod
    def _clip_planes():
        return (
            np.array((1.0, 0.0, 0.0, 1.0)),
            np.array((-1.0, 0.0, 0.0, 1.0)),
            np.array((0.0, 1.0, 0.0, 1.0)),
            np.array((0.0, -1.0, 0.0, 1.0)),
            np.array((0.0, 0.0, 1.0, 1.0)),
            np.array((0.0, 0.0, -1.0, 1.0)),
        )

    @classmethod
    def _inside_clip_volume(cls, vertices):
        return np.logical_and.reduce(
            [vertices @ plane >= 0 for plane in cls._clip_planes()]
        )

    @classmethod
    def _clip_polygon(cls, vertices):
        polygon = [vertex.copy() for vertex in vertices]
        for plane in cls._clip_planes():
            if not polygon:
                break
            clipped = []
            previous = polygon[-1]
            previous_distance = float(previous @ plane)
            for current in polygon:
                current_distance = float(current @ plane)
                previous_inside = previous_distance >= 0
                current_inside = current_distance >= 0
                if previous_inside != current_inside:
                    amount = previous_distance / (previous_distance - current_distance)
                    clipped.append(previous + amount * (current - previous))
                if current_inside:
                    clipped.append(current)
                previous = current
                previous_distance = current_distance
            polygon = clipped
        return polygon

    def _to_screen(self, clip_vertices):
        clip_vertices = np.asarray(clip_vertices, dtype=float)
        if clip_vertices.size == 0:
            return np.empty((0, 2), dtype=float)
        w = clip_vertices[:, 3]
        ndc = np.zeros_like(clip_vertices)
        valid = w > 0
        ndc[valid] = clip_vertices[valid] / w[valid, np.newaxis]
        screen = ndc @ self.render.projection.to_screen_matrix
        return screen[:, :2]

    def draw(self):
        vertexes, visible = self.screen_projection()

        if self.draw_vertexes:
            for vertex, is_valid in zip(vertexes, visible):
                if is_valid:
                    pg.draw.circle(
                        self.render.screen,
                        pg.Color("white"),
                        np.rint(vertex).astype(int),
                        6,
                    )

        self.movement()

    def translate(self, pos):
        offset = np.asarray(pos, dtype=float)
        self.vertexes = self.vertexes @ translate(offset)
        self.position += offset

    def scale(self, scale_to):
        factors = np.asarray(scale_to, dtype=float)
        if factors.ndim == 0:
            factors = np.full(3, factors)
            matrix = scale(float(factors[0]))
        elif factors.shape == (3,):
            matrix = np.diag((*factors, 1.0))
        else:
            raise ValueError("scale must be a scalar or a three-component vector")

        center = translate(-self.position)
        self.vertexes = self.vertexes @ center @ matrix @ translate(self.position)
        self.scale_factors *= factors

    def rotate_x(self, angle):
        self._rotate_around_center(rotate(angle), 0, angle)

    def rotate_y(self, angle):
        self._rotate_around_center(rotate_y(angle), 1, angle)

    def rotate_z(self, angle):
        self._rotate_around_center(rotate_z(angle), 2, angle)

    def _rotate_around_center(self, matrix, axis, angle):
        self.vertexes = (
            self.vertexes
            @ translate(-self.position)
            @ matrix
            @ translate(self.position)
        )
        self.rotation[axis] += angle

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