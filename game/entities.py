from __future__ import annotations

from dataclasses import dataclass, field
import random

import pygame

from game import settings


@dataclass
class Player:
    rect: pygame.Rect
    skin: dict[str, object]
    velocity_y: float = 0.0
    bob_phase: float = 0.0

    def update(self, dt: float, flap: bool) -> None:
        if flap:
            self.velocity_y = -settings.PLAYER_FLAP_FORCE

        self.velocity_y += settings.PLAYER_GRAVITY * dt
        self.rect.y += int(self.velocity_y * dt)
        self.bob_phase += dt * 8

        ceiling = 20
        floor = settings.SCREEN_HEIGHT - settings.GROUND_HEIGHT - self.rect.height
        if self.rect.y < ceiling:
            self.rect.y = ceiling
            self.velocity_y = 0
        if self.rect.y > floor:
            self.rect.y = floor
            self.velocity_y = 0

    def draw(self, surface: pygame.Surface) -> None:
        tilt = max(-18, min(18, int(self.velocity_y * 0.03)))
        plane_surface = pygame.Surface((self.rect.width + 84, self.rect.height + 48), pygame.SRCALPHA)

        body_main = (246, 248, 251)
        body_shadow = (222, 228, 236)
        wing_tint = (210, 217, 226)
        outline = (160, 170, 182)
        accent = self.skin["body"]
        accent_soft = self.skin["wing"]
        accent_dark = self.skin["beak"]

        fuselage_rect = pygame.Rect(36, 28, self.rect.width + 28, 20)
        shadow_rect = fuselage_rect.move(0, 3)
        nose_tip = (fuselage_rect.right + 20, fuselage_rect.centery - 1)
        tail_base_x = fuselage_rect.x + 6

        pygame.draw.ellipse(plane_surface, body_shadow, shadow_rect)
        pygame.draw.ellipse(plane_surface, body_main, fuselage_rect)
        pygame.draw.polygon(
            plane_surface,
            body_main,
            [
                (fuselage_rect.right - 8, fuselage_rect.y + 4),
                nose_tip,
                (fuselage_rect.right - 8, fuselage_rect.bottom - 4),
            ],
        )
        pygame.draw.polygon(
            plane_surface,
            body_shadow,
            [
                (tail_base_x, fuselage_rect.y + 5),
                (tail_base_x - 18, fuselage_rect.y + 11),
                (tail_base_x, fuselage_rect.bottom - 3),
            ],
        )

        tail_wing = [(tail_base_x - 14, 36), (tail_base_x - 28, 33), (tail_base_x - 10, 41), (tail_base_x + 4, 39)]
        tail_fin = [(tail_base_x - 6, 31), (tail_base_x - 2, 2), (tail_base_x + 13, 31)]
        main_wing = [(100, 36), (132, 24), (172, 26), (126, 42)]
        flap_layer = [(116, 40), (145, 33), (170, 34), (136, 46)]
        engine = pygame.Rect(129, 43, 28, 20)
        engine_shadow = engine.move(2, 3)
        door_a = pygame.Rect(84, 28, 8, 16)
        door_b = pygame.Rect(fuselage_rect.right - 36, 28, 8, 16)
        cockpit = [(fuselage_rect.right - 2, 26), (fuselage_rect.right + 12, 29), (fuselage_rect.right + 6, 35), (fuselage_rect.right - 6, 35)]
        stripe = [(58, 34), (tail_base_x + 6, 34), (tail_base_x + 22, 29), (68, 29)]

        pygame.draw.polygon(plane_surface, accent_soft, tail_wing)
        pygame.draw.polygon(plane_surface, accent, tail_fin)
        pygame.draw.polygon(plane_surface, wing_tint, main_wing)
        pygame.draw.polygon(plane_surface, accent_soft, flap_layer)
        pygame.draw.polygon(plane_surface, accent_dark, stripe)
        pygame.draw.rect(plane_surface, body_shadow, engine_shadow, border_radius=6)
        pygame.draw.rect(plane_surface, body_main, engine, border_radius=6)
        pygame.draw.rect(plane_surface, body_shadow, door_a, border_radius=4)
        pygame.draw.rect(plane_surface, body_shadow, door_b, border_radius=4)
        pygame.draw.polygon(plane_surface, (35, 42, 74), cockpit)

        window_y = fuselage_rect.y + 8
        for window_x in range(58, fuselage_rect.right - 44, 7):
            pygame.draw.circle(plane_surface, outline, (window_x, window_y + 4), 2)

        pygame.draw.ellipse(plane_surface, outline, fuselage_rect, 1)
        pygame.draw.polygon(
            plane_surface,
            outline,
            [
                (fuselage_rect.right - 8, fuselage_rect.y + 4),
                nose_tip,
                (fuselage_rect.right - 8, fuselage_rect.bottom - 4),
            ],
            1,
        )
        pygame.draw.polygon(plane_surface, outline, tail_wing, 1)
        pygame.draw.polygon(plane_surface, outline, tail_fin, 1)
        pygame.draw.polygon(plane_surface, outline, main_wing, 1)
        pygame.draw.polygon(plane_surface, outline, flap_layer, 1)
        pygame.draw.rect(plane_surface, outline, engine, width=1, border_radius=6)
        pygame.draw.line(plane_surface, outline, (98, 39), (167, 31), 1)

        rotated = pygame.transform.rotate(plane_surface, -tilt)
        rotated_rect = rotated.get_rect(center=self.rect.center)
        surface.blit(rotated, rotated_rect)


@dataclass
class ObstaclePair:
    x: float
    gap_y: int
    passed: bool = False
    passed_players: set[int] = field(default_factory=set)

    @property
    def top_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), 0, settings.OBSTACLE_WIDTH, self.gap_y)

    @property
    def bottom_rect(self) -> pygame.Rect:
        gap_bottom = self.gap_y + settings.OBSTACLE_GAP
        height = settings.SCREEN_HEIGHT - settings.GROUND_HEIGHT - gap_bottom
        return pygame.Rect(int(self.x), gap_bottom, settings.OBSTACLE_WIDTH, height)

    def update(self, dt: float) -> None:
        self.x -= settings.OBSTACLE_SPEED * dt

    def collides(self, player_rect: pygame.Rect) -> bool:
        top_hitbox = self.top_rect.inflate(-12, -10)
        bottom_hitbox = self.bottom_rect.inflate(-12, -10)
        return top_hitbox.colliderect(player_rect) or bottom_hitbox.colliderect(player_rect)

    def draw(self, surface: pygame.Surface) -> None:
        for rect in (self.top_rect, self.bottom_rect):
            pygame.draw.rect(surface, (66, 136, 94), rect, border_radius=10)
            pygame.draw.rect(surface, (40, 88, 56), rect, width=4, border_radius=10)


@dataclass
class Cloud:
    x: float
    y: int
    speed_scale: float

    def update(self, dt: float) -> None:
        self.x -= settings.CLOUD_SPEED * self.speed_scale * dt

    def draw(self, surface: pygame.Surface) -> None:
        color = (255, 255, 255, 190)
        for offset_x, offset_y, radius in ((0, 6, 16), (20, 0, 20), (40, 8, 14)):
            pygame.draw.circle(surface, color, (int(self.x + offset_x), self.y + offset_y), radius)


@dataclass
class Coin:
    x: float
    y: float

    def update(self, dt: float) -> None:
        self.x -= settings.COIN_SPEED * dt

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - settings.COIN_RADIUS), int(self.y - settings.COIN_RADIUS), settings.COIN_RADIUS * 2, settings.COIN_RADIUS * 2)

    def draw(self, surface: pygame.Surface) -> None:
        center = (int(self.x), int(self.y))
        radius = settings.COIN_RADIUS
        pygame.draw.circle(surface, (255, 210, 72), center, radius)
        pygame.draw.circle(surface, (255, 243, 166), center, radius - 3)
        pygame.draw.circle(surface, (255, 255, 255), center, radius, width=2)
        pygame.draw.rect(surface, (255, 230, 130), (center[0] - 3, center[1] - radius + 4, 6, radius * 2 - 8), border_radius=4)


def make_player(skin: dict[str, object]) -> Player:
    rect = pygame.Rect(settings.PLAYER_START_X, settings.PLAYER_START_Y, *settings.PLAYER_SIZE)
    return Player(rect=rect, skin=skin)


def make_obstacle() -> ObstaclePair:
    min_gap_y = 70
    max_gap_y = settings.SCREEN_HEIGHT - settings.GROUND_HEIGHT - settings.OBSTACLE_GAP - 70
    return ObstaclePair(
        x=settings.SCREEN_WIDTH + 40,
        gap_y=random.randint(min_gap_y, max_gap_y),
    )


def make_cloud(x: float | None = None) -> Cloud:
    return Cloud(
        x=x if x is not None else random.randint(0, settings.SCREEN_WIDTH),
        y=random.randint(40, 180),
        speed_scale=random.uniform(0.8, 1.35),
    )


def make_coin() -> Coin:
    return Coin(
        x=settings.SCREEN_WIDTH + 80,
        y=random.randint(90, settings.SCREEN_HEIGHT - settings.GROUND_HEIGHT - 110),
    )
