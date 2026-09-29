import math
import pygame as pg

try:
    from .camera import Camera
    from .object_3d import Object3D, Axes
    from .projection import Projection
    from .system_stats import SystemStats
except ImportError:
    from camera import Camera
    from object_3d import Object3D, Axes
    from projection import Projection
    from system_stats import SystemStats


class SoftwareRender:
    def __init__(self):
        pg.init()
        self.RES = self.WIDTH, self.HEIGHT = 1600, 900
        self.windowed_size = self.RES
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.FPS = 60
        self.fullscreen = False
        self.show_system_stats = False
        self.screen = pg.display.set_mode(self.RES, pg.RESIZABLE)
        self.clock = pg.time.Clock()
        self.system_stats = SystemStats()
        self.stats_font = None
        self.stats_font_checked = False
        self.rendered_stats = None
        self.stats_text = ()
        pg.display.set_caption("ThornEngine")
        self.create_object()

    def resize(self, size):
        width, height = size
        if width <= 0 or height <= 0:
            return

        self.WIDTH, self.HEIGHT = width, height
        if not self.fullscreen:
            self.RES = self.windowed_size = (width, height)
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.camera.v_fov = self.camera.h_fov * (self.HEIGHT / self.WIDTH)
        self.projection = Projection(self)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
        else:
            self.screen = pg.display.set_mode(self.windowed_size, pg.RESIZABLE)
        self.resize(self.screen.get_size())

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
        self.draw_system_stats()

    def draw_system_stats(self):
        if not self.show_system_stats:
            return

        stats = self.system_stats.refresh()
        if not self.stats_font_checked:
            self.stats_font_checked = True
            if pg.font and pg.font.get_init():
                self.stats_font = pg.font.SysFont(
                    "JetBrainsMono Nerd Font Mono", 17, bold=True
                )
        if self.stats_font is None:
            return

        if stats is not self.rendered_stats:
            self.rendered_stats = stats
            self.stats_text = self._render_system_stats(stats)
        for index, text in enumerate(self.stats_text):
            self.screen.blit(text, (12, 12 + index * 22))

    def _render_system_stats(self, stats):
        cpu_temp = (
            f"{self._fahrenheit(stats.cpu_temperature):.0f}°F"
            if stats.cpu_temperature is not None
            else "--°F"
        )
        gpu_usage = (
            f"{stats.gpu_percent:.0f}%"
            if stats.gpu_percent is not None
            else "--%"
        )
        gpu_temp = (
            f"{self._fahrenheit(stats.gpu_temperature):.0f}°F"
            if stats.gpu_temperature is not None
            else "--°F"
        )
        cpu_bar = self._terminal_bar(stats.cpu_percent)
        gpu_bar = self._terminal_bar(stats.gpu_percent or 0)
        ram_bar = self._terminal_bar(stats.memory_percent)
        rows = (
            f" CPU [{cpu_bar}] {stats.cpu_percent:4.1f}% {cpu_temp}",
            f"󰢮 GPU [{gpu_bar}] {gpu_usage:>3} {gpu_temp}",
            f"󰍛 RAM [{ram_bar}] {stats.memory_percent:3.0f}% "
            f"{stats.memory_used_gib:.1f}/{stats.memory_total_gib:.1f}G",
        )
        width = max(len(" SYSTEM MONITOR "), *(len(row) for row in rows))
        lines = (
            "┌" + "─" * (width + 2) + "┐",
            "│ " + "SYSTEM MONITOR".ljust(width) + " │",
            "├" + "─" * (width + 2) + "┤",
            *(f"│ {row.ljust(width)} │" for row in rows),
            "└" + "─" * (width + 2) + "┘",
        )
        return tuple(
            self.stats_font.render(line, True, pg.Color("#00ff66"))
            for line in lines
        )

    @staticmethod
    def _fahrenheit(celsius):
        return celsius * 9 / 5 + 32

    @staticmethod
    def _terminal_bar(percent, width=10):
        amount = max(0, min(width, round((percent or 0) / 100 * width)))
        return "█" * amount + "░" * (width - amount)

    def run(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.camera.set_mouse_look(False)
                    pg.quit()
                    return
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_F11:
                        self.toggle_fullscreen()
                    elif event.key == pg.K_BACKQUOTE or event.unicode == "~":
                        self.show_system_stats = not self.show_system_stats
                        if not self.show_system_stats:
                            self.rendered_stats = None
                            self.stats_text = ()
                elif event.type == pg.MOUSEBUTTONDOWN and event.button == pg.BUTTON_RIGHT:
                    self.camera.set_mouse_look(True)
                elif event.type == pg.MOUSEBUTTONUP and event.button == pg.BUTTON_RIGHT:
                    self.camera.set_mouse_look(False)
                elif event.type == pg.MOUSEMOTION:
                    self.camera.handle_mouse_motion(event.rel)
                elif event.type == pg.WINDOWFOCUSLOST:
                    self.camera.set_mouse_look(False)
                elif event.type in (
                    pg.VIDEORESIZE,
                    pg.WINDOWRESIZED,
                    pg.WINDOWSIZECHANGED,
                ) and not self.fullscreen:
                    size = event.size if hasattr(event, "size") else (event.x, event.y)
                    self.resize(size)
            self.camera.control()
            self.draw()
            pg.display.flip()
            self.clock.tick(self.FPS)

if __name__ == "__main__":
    app = SoftwareRender()
    app.run()