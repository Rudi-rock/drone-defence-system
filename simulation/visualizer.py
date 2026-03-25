"""
Swarm Visualizer — Real-time 2D visualization using Pygame.

Renders:
  - Drones (color-coded by role: cyan=scout, red=guard, green=relay)
  - Drone trails (position history)
  - Obstacle silhouettes
  - Threat actors (amber dots)
  - Sensor range circles
  - Communication mesh links
  - HUD with battery, speed, and swarm stats
"""

from __future__ import annotations

import math
import sys
from typing import Optional

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from src.core.types import DroneState, Role, Vec3
from src.intelligence.path_planner import Obstacle
from simulation.world import ThreatActor


# Color palette
COLORS = {
    "bg": (15, 15, 25),
    "grid": (30, 30, 45),
    "scout": (0, 200, 255),
    "guard": (255, 80, 80),
    "relay": (80, 255, 80),
    "threat": (255, 200, 0),
    "obstacle": (60, 60, 80),
    "trail": (50, 50, 70),
    "sensor": (40, 40, 60),
    "mesh": (40, 80, 40),
    "text": (180, 180, 200),
    "hud_bg": (20, 20, 35, 180),
}

ROLE_COLORS = {
    Role.SCOUT: COLORS["scout"],
    Role.GUARD: COLORS["guard"],
    Role.RELAY: COLORS["relay"],
}


class SwarmVisualizer:
    """
    Real-time 2D top-down swarm visualization.

    The world is projected onto a 2D plane (XY), with altitude
    indicated by drone size. Press ESC or close window to exit.
    """

    def __init__(
        self,
        window_size: tuple[int, int] = (1200, 800),
        world_bounds: tuple[tuple[float, float], tuple[float, float]] = ((-200, 200), (-200, 200)),
        fps: int = 60,
        show_trails: bool = True,
        trail_length: int = 50,
        show_sensor_range: bool = True,
        sensor_radius: float = 50.0,
        show_mesh_links: bool = True,
        mesh_range: float = 80.0,
    ) -> None:
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required for visualization. Install: pip install pygame")

        self.window_size = window_size
        self.world_bounds = world_bounds
        self.fps = fps
        self.show_trails = show_trails
        self.trail_length = trail_length
        self.show_sensor_range = show_sensor_range
        self.sensor_radius = sensor_radius
        self.show_mesh_links = show_mesh_links
        self.mesh_range = mesh_range

        # Trails: drone_id → list of screen positions
        self.trails: dict[str, list[tuple[int, int]]] = {}

        # Pygame state
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.font: Optional[pygame.font.Font] = None
        self.font_sm: Optional[pygame.font.Font] = None
        self._initialized = False

    def init(self) -> None:
        """Initialize Pygame window."""
        pygame.init()
        self.screen = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Drone Swarm Security — Digital Twin")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 14)
        self.font_sm = pygame.font.SysFont("consolas", 11)
        self._initialized = True

    def render(
        self,
        drones: list[DroneState],
        obstacles: list[Obstacle] | None = None,
        threats: list[ThreatActor] | None = None,
        sim_time: float = 0.0,
    ) -> bool:
        """
        Render one frame.

        Returns:
            True if window is still open, False if user closed it.
        """
        if not self._initialized:
            self.init()

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

        self.screen.fill(COLORS["bg"])

        # Draw grid
        self._draw_grid()

        # Draw obstacles
        if obstacles:
            for obs in obstacles:
                self._draw_obstacle(obs)

        # Draw sensor ranges (under drones)
        if self.show_sensor_range:
            for drone in drones:
                self._draw_sensor_range(drone)

        # Draw mesh links
        if self.show_mesh_links:
            self._draw_mesh_links(drones)

        # Draw trails
        if self.show_trails:
            self._update_and_draw_trails(drones)

        # Draw threats
        if threats:
            for threat in threats:
                if threat.active:
                    self._draw_threat(threat)

        # Draw drones
        for drone in drones:
            self._draw_drone(drone)

        # Draw HUD
        self._draw_hud(drones, sim_time)

        pygame.display.flip()
        self.clock.tick(self.fps)
        return True

    def close(self) -> None:
        """Close Pygame window."""
        if self._initialized:
            pygame.quit()
            self._initialized = False

    # ──────────────────────────────────────
    # Coordinate conversion
    # ──────────────────────────────────────

    def _world_to_screen(self, pos: Vec3) -> tuple[int, int]:
        """Convert world XY to screen pixel coordinates."""
        (xmin, xmax), (ymin, ymax) = self.world_bounds
        w, h = self.window_size

        # Leave margins for HUD
        margin = 60
        draw_w = w - 2 * margin
        draw_h = h - 2 * margin

        sx = int(margin + (pos.x - xmin) / (xmax - xmin) * draw_w)
        sy = int(margin + (1.0 - (pos.y - ymin) / (ymax - ymin)) * draw_h)  # flip Y
        return (sx, sy)

    def _world_to_screen_scale(self, distance: float) -> int:
        """Convert a world distance to screen pixels."""
        (xmin, xmax), _ = self.world_bounds
        w, _ = self.window_size
        margin = 60
        draw_w = w - 2 * margin
        return max(1, int(distance / (xmax - xmin) * draw_w))

    # ──────────────────────────────────────
    # Drawing functions
    # ──────────────────────────────────────

    def _draw_grid(self) -> None:
        """Draw a subtle background grid."""
        w, h = self.window_size
        step = 40
        for x in range(0, w, step):
            pygame.draw.line(self.screen, COLORS["grid"], (x, 0), (x, h))
        for y in range(0, h, step):
            pygame.draw.line(self.screen, COLORS["grid"], (0, y), (w, y))

    def _draw_obstacle(self, obs: Obstacle) -> None:
        """Draw an obstacle as a filled rectangle."""
        center = self._world_to_screen(obs.position)
        half_w = self._world_to_screen_scale(obs.size.x)
        half_h = self._world_to_screen_scale(obs.size.y)
        rect = pygame.Rect(
            center[0] - half_w, center[1] - half_h,
            half_w * 2, half_h * 2,
        )
        pygame.draw.rect(self.screen, COLORS["obstacle"], rect)
        pygame.draw.rect(self.screen, (80, 80, 100), rect, 1)

    def _draw_drone(self, drone: DroneState) -> None:
        """Draw a drone as a directional triangle."""
        pos = self._world_to_screen(drone.position)
        color = ROLE_COLORS.get(drone.role, COLORS["scout"])

        # Size proportional to altitude (min 5, max 12)
        size = int(5 + 7 * min(drone.position.z, 50) / 50)

        # Triangle pointing in heading direction
        angle = drone.heading
        points = [
            (pos[0] + int(size * 1.5 * math.cos(angle)),
             pos[1] - int(size * 1.5 * math.sin(angle))),
            (pos[0] + int(size * math.cos(angle + 2.5)),
             pos[1] - int(size * math.sin(angle + 2.5))),
            (pos[0] + int(size * math.cos(angle - 2.5)),
             pos[1] - int(size * math.sin(angle - 2.5))),
        ]
        pygame.draw.polygon(self.screen, color, points)

        # Glow effect
        glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, 30), (size * 2, size * 2), size * 2)
        self.screen.blit(glow_surf, (pos[0] - size * 2, pos[1] - size * 2))

        # ID label
        label = self.font_sm.render(drone.id[-3:], True, (150, 150, 170))
        self.screen.blit(label, (pos[0] + size + 3, pos[1] - 5))

    def _draw_threat(self, threat: ThreatActor) -> None:
        """Draw a threat actor as a pulsing amber dot."""
        pos = self._world_to_screen(threat.position)
        # Pulsing effect using pygame ticks
        pulse = 6 + int(3 * math.sin(pygame.time.get_ticks() / 200))
        pygame.draw.circle(self.screen, COLORS["threat"], pos, pulse)
        pygame.draw.circle(self.screen, (255, 255, 200), pos, 3)

        label = self.font_sm.render(threat.classification[:3].upper(), True, COLORS["threat"])
        self.screen.blit(label, (pos[0] + pulse + 3, pos[1] - 5))

    def _draw_sensor_range(self, drone: DroneState) -> None:
        """Draw translucent sensor range circle."""
        pos = self._world_to_screen(drone.position)
        radius = self._world_to_screen_scale(self.sensor_radius)
        color = ROLE_COLORS.get(drone.role, COLORS["scout"])

        sensor_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(sensor_surf, (*color, 15), (radius, radius), radius)
        pygame.draw.circle(sensor_surf, (*color, 40), (radius, radius), radius, 1)
        self.screen.blit(sensor_surf, (pos[0] - radius, pos[1] - radius))

    def _draw_mesh_links(self, drones: list[DroneState]) -> None:
        """Draw communication mesh links between nearby drones."""
        for i, d1 in enumerate(drones):
            for d2 in drones[i + 1:]:
                dist = d1.position.distance_to(d2.position)
                if dist < self.mesh_range:
                    p1 = self._world_to_screen(d1.position)
                    p2 = self._world_to_screen(d2.position)
                    # Fade link as distance increases
                    alpha = int(200 * (1 - dist / self.mesh_range))
                    link_color = (40, 120 + alpha // 3, 40)
                    pygame.draw.line(self.screen, link_color, p1, p2, 1)

    def _update_and_draw_trails(self, drones: list[DroneState]) -> None:
        """Update position history and draw trails."""
        for drone in drones:
            pos = self._world_to_screen(drone.position)
            if drone.id not in self.trails:
                self.trails[drone.id] = []
            trail = self.trails[drone.id]
            trail.append(pos)
            if len(trail) > self.trail_length:
                trail.pop(0)

            # Draw trail with fading opacity
            color = ROLE_COLORS.get(drone.role, COLORS["scout"])
            for i in range(1, len(trail)):
                alpha = int(100 * i / len(trail))
                trail_color = (
                    min(255, color[0] // 3 + alpha // 4),
                    min(255, color[1] // 3 + alpha // 4),
                    min(255, color[2] // 3 + alpha // 4),
                )
                pygame.draw.line(self.screen, trail_color, trail[i - 1], trail[i], 1)

    def _draw_hud(self, drones: list[DroneState], sim_time: float) -> None:
        """Draw heads-up display with swarm statistics."""
        w, h = self.window_size

        # HUD background
        hud_rect = pygame.Rect(w - 220, 10, 210, 180)
        hud_surf = pygame.Surface((210, 180), pygame.SRCALPHA)
        hud_surf.fill((20, 20, 35, 180))
        self.screen.blit(hud_surf, (w - 220, 10))
        pygame.draw.rect(self.screen, (60, 60, 80), hud_rect, 1)

        # Title
        title = self.font.render("SWARM STATUS", True, COLORS["text"])
        self.screen.blit(title, (w - 210, 15))

        # Stats
        active = sum(1 for d in drones if d.status.name == "ACTIVE")
        avg_battery = sum(d.battery_pct for d in drones) / max(len(drones), 1)
        scouts = sum(1 for d in drones if d.role == Role.SCOUT)
        guards = sum(1 for d in drones if d.role == Role.GUARD)
        relays = sum(1 for d in drones if d.role == Role.RELAY)

        lines = [
            f"Time: {sim_time:.1f}s",
            f"Active: {active}/{len(drones)}",
            f"Avg Battery: {avg_battery:.1f}%",
            f"",
            f"Scouts:  {scouts}",
            f"Guards:  {guards}",
            f"Relays:  {relays}",
        ]

        y = 38
        for line in lines:
            surf = self.font_sm.render(line, True, COLORS["text"])
            self.screen.blit(surf, (w - 210, y))
            y += 18

        # Legend at bottom
        legend_y = h - 30
        for role, color in ROLE_COLORS.items():
            pygame.draw.circle(self.screen, color, (50, legend_y), 5)
            label = self.font_sm.render(role.name, True, COLORS["text"])
            self.screen.blit(label, (60, legend_y - 6))
            legend_y -= 18
