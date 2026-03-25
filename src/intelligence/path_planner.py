"""
Path Planner — A* and RRT path planning with obstacle avoidance.

Provides two algorithms:
  - A*: optimal for grid-based 2D planning (fast, guaranteed shortest)
  - RRT (Rapidly-exploring Random Tree): for 3D planning in continuous space
"""

from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass, field
from typing import Optional

from src.core.types import Vec3


@dataclass
class Obstacle:
    """Axis-aligned bounding box obstacle."""
    position: Vec3          # center
    size: Vec3              # half-extents (width/2, depth/2, height/2)

    def contains(self, point: Vec3) -> bool:
        """Check if a point is inside this obstacle."""
        return (
            abs(point.x - self.position.x) < self.size.x
            and abs(point.y - self.position.y) < self.size.y
            and abs(point.z - self.position.z) < self.size.z
        )

    def distance_to(self, point: Vec3) -> float:
        """Approximate distance from point to obstacle surface."""
        dx = max(0, abs(point.x - self.position.x) - self.size.x)
        dy = max(0, abs(point.y - self.position.y) - self.size.y)
        dz = max(0, abs(point.z - self.position.z) - self.size.z)
        return math.sqrt(dx * dx + dy * dy + dz * dz)


# ──────────────────────────────────────────────
# A* Planner (2D grid-based)
# ──────────────────────────────────────────────

@dataclass(order=True)
class _AStarNode:
    f_cost: float
    position: tuple[int, int] = field(compare=False)
    g_cost: float = field(compare=False, default=0.0)
    parent: Optional[tuple[int, int]] = field(compare=False, default=None)


class AStarPlanner:
    """
    Grid-based A* path planner (2D, fixed altitude).

    Discretizes the world into a grid and finds the shortest
    obstacle-free path from start to goal.
    """

    def __init__(
        self,
        grid_resolution: float = 5.0,
        world_bounds: tuple[tuple[float, float], tuple[float, float]] = (
            (-200, 200), (-200, 200)
        ),
    ) -> None:
        self.resolution = grid_resolution
        self.x_bounds, self.y_bounds = world_bounds
        self.grid_w = int((self.x_bounds[1] - self.x_bounds[0]) / grid_resolution)
        self.grid_h = int((self.y_bounds[1] - self.y_bounds[0]) / grid_resolution)
        self._obstacle_grid: set[tuple[int, int]] = set()

    def set_obstacles(self, obstacles: list[Obstacle]) -> None:
        """Rasterize obstacles onto the grid."""
        self._obstacle_grid.clear()
        for gx in range(self.grid_w):
            for gy in range(self.grid_h):
                wx = self.x_bounds[0] + gx * self.resolution
                wy = self.y_bounds[0] + gy * self.resolution
                for obs in obstacles:
                    if (
                        abs(wx - obs.position.x) < obs.size.x + self.resolution
                        and abs(wy - obs.position.y) < obs.size.y + self.resolution
                    ):
                        self._obstacle_grid.add((gx, gy))
                        break

    def plan(self, start: Vec3, goal: Vec3) -> list[Vec3]:
        """
        Find shortest path from start to goal.

        Returns:
            List of Vec3 waypoints (world coordinates), or empty list if no path found.
        """
        start_cell = self._world_to_grid(start)
        goal_cell = self._world_to_grid(goal)

        if start_cell in self._obstacle_grid or goal_cell in self._obstacle_grid:
            return []

        open_set: list[_AStarNode] = []
        closed_set: set[tuple[int, int]] = set()
        came_from: dict[tuple[int, int], tuple[int, int]] = {}

        start_node = _AStarNode(
            f_cost=self._heuristic(start_cell, goal_cell),
            position=start_cell,
            g_cost=0.0,
        )
        heapq.heappush(open_set, start_node)

        g_costs: dict[tuple[int, int], float] = {start_cell: 0.0}

        while open_set:
            current = heapq.heappop(open_set)

            if current.position == goal_cell:
                return self._reconstruct_path(came_from, goal_cell, start.z)

            if current.position in closed_set:
                continue
            closed_set.add(current.position)

            for neighbor in self._get_neighbors(current.position):
                if neighbor in closed_set or neighbor in self._obstacle_grid:
                    continue

                move_cost = (
                    1.414 if abs(neighbor[0] - current.position[0]) + abs(neighbor[1] - current.position[1]) == 2
                    else 1.0
                )
                tentative_g = current.g_cost + move_cost

                if tentative_g < g_costs.get(neighbor, float("inf")):
                    g_costs[neighbor] = tentative_g
                    came_from[neighbor] = current.position
                    f = tentative_g + self._heuristic(neighbor, goal_cell)
                    heapq.heappush(open_set, _AStarNode(f, neighbor, tentative_g))

        return []  # No path found

    def _world_to_grid(self, pos: Vec3) -> tuple[int, int]:
        gx = int((pos.x - self.x_bounds[0]) / self.resolution)
        gy = int((pos.y - self.y_bounds[0]) / self.resolution)
        gx = max(0, min(gx, self.grid_w - 1))
        gy = max(0, min(gy, self.grid_h - 1))
        return (gx, gy)

    def _grid_to_world(self, cell: tuple[int, int], z: float) -> Vec3:
        wx = self.x_bounds[0] + cell[0] * self.resolution + self.resolution / 2
        wy = self.y_bounds[0] + cell[1] * self.resolution + self.resolution / 2
        return Vec3(wx, wy, z)

    def _heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _get_neighbors(self, cell: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = cell
        neighbors = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_w and 0 <= ny < self.grid_h:
                    neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(
        self,
        came_from: dict[tuple[int, int], tuple[int, int]],
        goal: tuple[int, int],
        z: float,
    ) -> list[Vec3]:
        path = []
        current = goal
        while current in came_from:
            path.append(self._grid_to_world(current, z))
            current = came_from[current]
        path.reverse()
        return path


# ──────────────────────────────────────────────
# RRT Planner (3D continuous space)
# ──────────────────────────────────────────────

class RRTPlanner:
    """
    Rapidly-exploring Random Tree path planner (3D).

    Better suited for high DOF / continuous space planning.
    Probabilistically complete — will find a path if one exists,
    given enough iterations.
    """

    def __init__(
        self,
        bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] = (
            (-200, 200), (-200, 200), (5, 100)
        ),
        step_size: float = 10.0,
        max_iterations: int = 2000,
        goal_threshold: float = 10.0,
    ) -> None:
        self.x_bounds, self.y_bounds, self.z_bounds = bounds
        self.step_size = step_size
        self.max_iterations = max_iterations
        self.goal_threshold = goal_threshold

    def plan(
        self,
        start: Vec3,
        goal: Vec3,
        obstacles: list[Obstacle],
    ) -> list[Vec3]:
        """
        Find a collision-free path from start to goal.

        Returns:
            List of Vec3 waypoints, or empty list if no path found.
        """
        tree: dict[int, Vec3] = {0: start}
        parents: dict[int, int] = {}
        node_count = 1

        for _ in range(self.max_iterations):
            # Bias toward goal 10% of the time
            if random.random() < 0.1:
                rand_point = goal
            else:
                rand_point = self._random_point()

            # Find nearest node in tree
            nearest_idx = self._nearest(tree, rand_point)
            nearest = tree[nearest_idx]

            # Steer toward random point
            new_point = self._steer(nearest, rand_point)

            # Check collision
            if self._collision_free(nearest, new_point, obstacles):
                tree[node_count] = new_point
                parents[node_count] = nearest_idx

                # Check if we reached the goal
                if new_point.distance_to(goal) < self.goal_threshold:
                    # Add goal as final node
                    tree[node_count + 1] = goal
                    parents[node_count + 1] = node_count
                    return self._extract_path(tree, parents, node_count + 1)

                node_count += 1

        return []  # No path found within iteration limit

    def _random_point(self) -> Vec3:
        return Vec3(
            random.uniform(*self.x_bounds),
            random.uniform(*self.y_bounds),
            random.uniform(*self.z_bounds),
        )

    def _nearest(self, tree: dict[int, Vec3], point: Vec3) -> int:
        return min(tree, key=lambda idx: tree[idx].distance_to(point))

    def _steer(self, from_point: Vec3, to_point: Vec3) -> Vec3:
        direction = to_point - from_point
        dist = direction.magnitude()
        if dist < self.step_size:
            return to_point
        return from_point + direction.normalized() * self.step_size

    def _collision_free(
        self, from_point: Vec3, to_point: Vec3, obstacles: list[Obstacle],
        num_checks: int = 5,
    ) -> bool:
        """Check if path segment is collision-free via interpolation."""
        for i in range(num_checks + 1):
            t = i / num_checks
            point = Vec3(
                from_point.x + t * (to_point.x - from_point.x),
                from_point.y + t * (to_point.y - from_point.y),
                from_point.z + t * (to_point.z - from_point.z),
            )
            for obs in obstacles:
                if obs.contains(point):
                    return False
        return True

    def _extract_path(
        self, tree: dict[int, Vec3], parents: dict[int, int], goal_idx: int
    ) -> list[Vec3]:
        path = []
        current = goal_idx
        while current in parents:
            path.append(tree[current])
            current = parents[current]
        path.append(tree[0])
        path.reverse()
        return path
