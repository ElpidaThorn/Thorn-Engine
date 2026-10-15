import math
import sys
import subprocess
from pathlib import Path

import pygame as pg

try:
    from .camera import Camera
    from .object_3d import Object3D, Axes
    from .projection import Projection
    from .system_stats import SystemStats
except ImportError:  # pragma: no cover - allow direct execution from the repo root
    try:
        from ThornEngine.camera import Camera
        from ThornEngine.object_3d import Object3D, Axes
        from ThornEngine.projection import Projection
        from ThornEngine.system_stats import SystemStats
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
        self.transform_panel_open = False
        self.transform_mode_index = 0
        self.transform_axis_index = 0
        self.transform_modes = ("MOVE", "ROTATE", "SCALE")
        self.transform_axes = ("X", "Y", "Z")
        self.terminal_process = None
        self.terminal_status = ""
        self.terminal_status_until = 0
        self.screen = pg.display.set_mode(self.RES, pg.RESIZABLE)
        self.clock = pg.time.Clock()
        self.system_stats = SystemStats()
        self.stats_font = None
        self.stats_font_checked = False
        self.stats_font_path = None
        self.stats_font_cache = {}
        self.rendered_stats = None
        self.stats_text = ()
        self.stats_snapshot = None
        self.stats_refreshed_at = 0
        self.stats_refresh_interval = 1000
        pg.display.set_caption("ThornEngine-GraphicsAPI")
        self.create_object()

    def resize(self, size):
        width, height = size
        if width <= 0 or height <= 0:
            return

        self.WIDTH, self.HEIGHT = width, height
        if not self.fullscreen:
            self.RES = self.windowed_size = (width, height)
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.camera.update_aspect_ratio(self.WIDTH, self.HEIGHT)
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
        self.draw_transform_panel()
        self.draw_terminal_status()
        self.draw_controls_footer()

    def _ensure_stats_font(self, size=17):
        if not self.stats_font_checked:
            self.stats_font_checked = True
            if pg.font and pg.font.get_init():
                for name in (
                    "JetBrainsMono Nerd Font Mono",
                    "JetBrains Mono",
                    "DejaVu Sans Mono",
                    "monospace",
                ):
                    self.stats_font_path = pg.font.match_font(name, bold=True)
                    if self.stats_font_path:
                        break
        if not pg.font or not pg.font.get_init():
            return None
        if size not in self.stats_font_cache:
            self.stats_font_cache[size] = pg.font.Font(
                self.stats_font_path, size
            )
        self.stats_font = self.stats_font_cache[size]
        return self.stats_font

    def draw_system_stats(self):
        if not self.show_system_stats:
            return

        now = pg.time.get_ticks()
        if (
            self.stats_snapshot is None
            or now - self.stats_refreshed_at >= self.stats_refresh_interval
        ):
            self.stats_snapshot = self.system_stats.refresh()
            self.stats_refreshed_at = now
        stats = self.stats_snapshot
        if self._ensure_stats_font() is None:
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

    def draw_transform_panel(self):
        if not self.transform_panel_open:
            return
        font = self._ensure_stats_font()
        if font is None:
            return

        axis = self.transform_axis_index
        position = self.object.position
        rotation = self.object.rotation
        scale = self.object.scale_factors
        lines = (
            "THORN / OBJECT EDITOR [B]",
            "TARGET: CUBE",
            f"MODE: {self.transform_modes[self.transform_mode_index]}  [TAB]",
            f"AXIS: {self.transform_axes[axis]}  [X / Y / Z]",
            f"POS   X{position[0]:+7.2f} Y{position[1]:+7.2f} Z{position[2]:+7.2f}",
            f"ROT   X{math.degrees(rotation[0]):+7.1f} "
            f"Y{math.degrees(rotation[1]):+7.1f} "
            f"Z{math.degrees(rotation[2]):+7.1f}",
            f"SCALE X{scale[0]:6.2f} Y{scale[1]:6.2f} Z{scale[2]:6.2f}",
            "<- / -> ADJUST SELECTED AXIS",
        )
        rendered = tuple(font.render(line, True, pg.Color("#00ff66")) for line in lines)
        width = max(
            1,
            min(max(420, max(text.get_width() for text in rendered) + 24), self.WIDTH - 24),
        )
        height = 18 + len(rendered) * 23
        x = max(12, self.WIDTH - width - 12)
        y = 12
        panel = pg.Surface((width, height), pg.SRCALPHA)
        panel.fill((10, 31, 32, 235))
        pg.draw.rect(panel, pg.Color("#00ff66"), panel.get_rect(), 2)
        pg.draw.line(panel, pg.Color("#00ff66"), (2, 39), (width - 2, 39), 1)
        self.screen.blit(panel, (x, y))
        self.screen.blit(rendered[0], (x + 12, y + 8))
        for index, text in enumerate(rendered[1:]):
            self.screen.blit(text, (x + 12, y + 44 + index * 23))

    def draw_terminal_status(self):
        if not self.terminal_status or pg.time.get_ticks() >= self.terminal_status_until:
            return
        font = self._ensure_stats_font()
        if font is None:
            return
        text = font.render(self.terminal_status, True, pg.Color("#ffd866"))
        padding = 12
        panel = pg.Surface(
            (text.get_width() + padding * 2, text.get_height() + padding),
            pg.SRCALPHA,
        )
        panel.fill((10, 31, 32, 235))
        pg.draw.rect(panel, pg.Color("#ffd866"), panel.get_rect(), 2)
        x = 12
        y = max(12, self.HEIGHT - panel.get_height() - 150)
        self.screen.blit(panel, (x, y))
        self.screen.blit(text, (x + padding, y + padding // 2))

    def draw_controls_footer(self):
        font = self._ensure_stats_font()
        if font is None:
            return

        rows = (
            "WASD MOVE | Q/E UP-DOWN | ARROWS ROTATE | RMB+MOUSE LOOK | SCROLL DOLLY",
            "B EDITOR | TAB MODE | X/Y/Z AXIS | LEFT/RIGHT ADJUST | "
            "F11 FULLSCREEN | F12 TERMINAL | ~ STATS",
        )
        title = "THORN ENGINE / CONTROLS"
        font_size = 16
        available_width = max(1, self.WIDTH - 40)
        while font_size > 10:
            font = self._ensure_stats_font(font_size)
            if font is None:
                return
            if max(font.size(line)[0] for line in (*rows, title)) <= available_width - 24:
                break
            font_size -= 1

        color = pg.Color("#00ff66")
        title_surface = font.render(title, True, color)
        row_surfaces = tuple(font.render(line, True, color) for line in rows)
        content_width = max(
            title_surface.get_width(),
            *(surface.get_width() for surface in row_surfaces),
        )
        panel_width = max(1, min(max(1, self.WIDTH - 24), content_width + 24))
        line_height = font.get_linesize()
        panel_height = 26 + line_height * (1 + len(row_surfaces))
        x = max(12, (self.WIDTH - panel_width) // 2)
        y = max(0, self.HEIGHT - panel_height - 12)

        panel = pg.Surface((panel_width, panel_height), pg.SRCALPHA)
        panel.fill((10, 31, 32, 235))
        pg.draw.rect(panel, color, panel.get_rect(), 2)
        pg.draw.line(
            panel,
            color,
            (2, 12 + line_height),
            (panel_width - 2, 12 + line_height),
            1,
        )
        self.screen.blit(panel, (x, y))
        self.screen.blit(title_surface, (x + 12, y + 5))
        for index, surface in enumerate(row_surfaces):
            self.screen.blit(surface, (x + 12, y + 14 + line_height * (index + 1)))

    def adjust_object_transform(self, direction):
        axis = self.transform_axis_index
        mode = self.transform_modes[self.transform_mode_index]
        if mode == "MOVE":
            offset = [0.0, 0.0, 0.0]
            offset[axis] = direction * 0.1
            self.object.translate(offset)
        elif mode == "ROTATE":
            angle = direction * math.radians(5)
            (self.object.rotate_x, self.object.rotate_y, self.object.rotate_z)[axis](angle)
        else:
            current = self.object.scale_factors[axis]
            updated = max(0.1, current * (1.1 if direction > 0 else 1 / 1.1))
            factors = [1.0, 1.0, 1.0]
            factors[axis] = updated / current
            self.object.scale(factors)

    def open_terminal(self):
        if self.terminal_process is not None and self.terminal_process.poll() is None:
            self._set_terminal_status("Thorn terminal is already open.")
            return

        terminal_script = Path(__file__).with_name("terminal.py")
        try:
            self.terminal_process = subprocess.Popen(
                [sys.executable, str(terminal_script)],
                cwd=terminal_script.parent.parent,
                start_new_session=True,
            )
        except OSError as error:
            self._set_terminal_status(f"Could not open Thorn terminal: {error.strerror}")
            return
        self._set_terminal_status("Opened Thorn terminal.")

    def _set_terminal_status(self, message):
        self.terminal_status = message
        self.terminal_status_until = pg.time.get_ticks() + 5000

    def toggle_system_stats(self):
        self.show_system_stats = not self.show_system_stats
        if not self.show_system_stats:
            self.stats_snapshot = None
            self.rendered_stats = None
            self.stats_text = ()

    @staticmethod
    def _fahrenheit(celsius):
        return celsius * 9 / 5 + 32

    @staticmethod
    def _terminal_bar(percent, width=10):
        amount = max(0, min(width, round((percent or 0) / 100 * width)))
        return "█" * amount + "░" * (width - amount)

    def run(self):
        try:
            while True:
                delta_time = min(self.clock.tick(self.FPS) / 1000.0, 0.1)
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_F11:
                            self.toggle_fullscreen()
                        elif event.key == pg.K_F12:
                            self.open_terminal()
                        elif event.key == pg.K_b:
                            self.transform_panel_open = not self.transform_panel_open
                        elif self.transform_panel_open and event.key == pg.K_TAB:
                            self.transform_mode_index = (
                                self.transform_mode_index + 1
                            ) % len(self.transform_modes)
                        elif self.transform_panel_open and event.key in (
                            pg.K_x, pg.K_y, pg.K_z
                        ):
                            self.transform_axis_index = {
                                pg.K_x: 0,
                                pg.K_y: 1,
                                pg.K_z: 2,
                            }[event.key]
                        elif self.transform_panel_open and event.key == pg.K_LEFT:
                            self.adjust_object_transform(-1)
                        elif self.transform_panel_open and event.key == pg.K_RIGHT:
                            self.adjust_object_transform(1)
                        elif (
                            event.key == pg.K_BACKQUOTE
                            or event.unicode in ("`", "~")
                        ):
                            self.toggle_system_stats()
                    elif event.type == pg.MOUSEBUTTONDOWN and event.button == pg.BUTTON_RIGHT:
                        self.camera.set_mouse_look(True)
                    elif event.type == pg.MOUSEBUTTONUP and event.button == pg.BUTTON_RIGHT:
                        self.camera.set_mouse_look(False)
                    elif event.type == pg.MOUSEMOTION:
                        self.camera.handle_mouse_motion(event.rel)
                    elif event.type == pg.MOUSEWHEEL:
                        self.camera.scroll(event.y)
                    elif event.type == pg.WINDOWFOCUSLOST:
                        self.camera.set_mouse_look(False)
                    elif event.type in (
                        pg.VIDEORESIZE,
                        pg.WINDOWRESIZED,
                        pg.WINDOWSIZECHANGED,
                    ) and not self.fullscreen:
                        size = event.size if hasattr(event, "size") else (event.x, event.y)
                        self.resize(size)
                self.camera.control(
                    delta_time,
                    allow_rotation=not self.transform_panel_open,
                )
                self.draw()
                pg.display.flip()
        except KeyboardInterrupt:
            pass
        finally:
            self.camera.set_mouse_look(False)
            pg.quit()

if __name__ == "__main__":
    app = SoftwareRender()
    app.run()