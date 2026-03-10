from __future__ import annotations

import sys
from dataclasses import dataclass

import pygame

from game import settings
from game.entities import Cloud, Coin, ObstaclePair, make_cloud, make_coin, make_obstacle, make_player
from game.save_data import load_save, save_save


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    variant: str = "secondary"

    def contains(self, position: tuple[int, int]) -> bool:
        return self.rect.collidepoint(position)


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(settings.TITLE)
        self.scale = 1.0
        self.configure_display()
        self.clock = pygame.time.Clock()
        self.mouse_pos = (0, 0)
        self.pause_buttons: dict[str, Button] = {}
        self.game_over_buttons: dict[str, Button] = {}
        self.menu_buttons: dict[str, Button] = {}
        self.shop_cards: list[tuple[pygame.Rect, dict[str, object]]] = []
        self.city_layers = self.build_city_layers()
        self.city_offsets = [0.0 for _ in self.city_layers]
        self.static_background = self.build_static_background()

        self.font_large = pygame.font.SysFont("Avenir Next", self.sc(42), bold=True)
        self.font_medium = pygame.font.SysFont("Avenir Next", self.sc(28))
        self.font_small = pygame.font.SysFont("Menlo", self.sc(18))
        self.font_tiny = pygame.font.SysFont("Menlo", self.sc(14))

        self.obstacle_event = pygame.event.custom_type()
        self.coin_event = pygame.event.custom_type()
        pygame.time.set_timer(self.obstacle_event, settings.OBSTACLE_SPAWN_MS)
        pygame.time.set_timer(self.coin_event, settings.COIN_SPAWN_MS)

        self.skin_by_id = {skin["id"]: skin for skin in settings.SKINS}
        self.save_data = load_save()
        self.total_coins = int(self.save_data["coins"])
        self.best_score = int(self.save_data["best_score"])
        self.unlocked_skins = set(self.save_data["unlocked_skins"])
        self.selected_skin_id = str(self.save_data["selected_skin"])
        self.state = "menu"
        self.play_button = Button(self.top_right_button_rect(), "Pause", "secondary")

        self.reset()

    def configure_display(self) -> None:
        info = pygame.display.Info()
        screen_width = info.current_w or settings.BASE_SCREEN_WIDTH
        screen_height = info.current_h or settings.BASE_SCREEN_HEIGHT

        if pygame.display.get_driver() == "dummy":
            screen_width = settings.BASE_SCREEN_WIDTH
            screen_height = settings.BASE_SCREEN_HEIGHT
            flags = 0
        else:
            flags = pygame.FULLSCREEN

        self.scale = min(screen_width / settings.BASE_SCREEN_WIDTH, screen_height / settings.BASE_SCREEN_HEIGHT)
        self.scale = max(1.0, min(self.scale, 2.2))

        settings.SCREEN_WIDTH = screen_width
        settings.SCREEN_HEIGHT = screen_height
        settings.GROUND_HEIGHT = int(86 * self.scale)
        settings.PLAYER_START_X = int(170 * self.scale)
        settings.PLAYER_START_Y = int(screen_height * 0.57)
        settings.PLAYER_SIZE = (int(92 * self.scale), int(40 * self.scale))
        settings.OBSTACLE_WIDTH = int(42 * self.scale)
        settings.OBSTACLE_GAP = int(170 * self.scale)
        settings.COIN_RADIUS = max(12, int(14 * self.scale))

        self.screen = pygame.display.set_mode((screen_width, screen_height), flags)

    def sc(self, value: int) -> int:
        return max(value, int(value * self.scale))

    def r(self, x: int, y: int, w: int, h: int) -> pygame.Rect:
        return pygame.Rect(int(x), int(y), int(w), int(h))

    def top_right_button_rect(self) -> pygame.Rect:
        return self.r(settings.SCREEN_WIDTH - self.sc(170), self.sc(24), self.sc(140), self.sc(46))

    def reset(self) -> None:
        self.player = make_player(self.skin_by_id[self.selected_skin_id])
        self.obstacles: list[ObstaclePair] = []
        self.clouds: list[Cloud] = [make_cloud(x * int(240 * self.scale)) for x in range(6)]
        self.coins: list[Coin] = []
        self.score = 0
        self.run_coins = 0
        self.game_over = False
        self.paused = False
        self.pause_buttons = {}
        self.game_over_buttons = {}

    def run(self) -> None:
        while True:
            dt = self.clock.tick(settings.FPS) / 1000.0
            flap = False
            self.mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if event.type == pygame.KEYDOWN:
                    flap = self.handle_keydown(event.key) or flap
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    flap = self.handle_click(event.pos) or flap
                if event.type == self.obstacle_event and self.state == "playing" and not self.game_over and not self.paused:
                    self.obstacles.append(make_obstacle())
                if event.type == self.coin_event and self.state == "playing" and not self.game_over and not self.paused:
                    self.coins.append(make_coin())

            if self.state == "playing" and not self.game_over and not self.paused:
                self.update(dt, flap)
            else:
                self.update_menu_scene(dt)

            self.draw()

    def handle_keydown(self, key: int) -> bool:
        if self.state == "menu":
            if key == pygame.K_RETURN:
                self.start_run()
            elif key == pygame.K_SPACE:
                self.start_run(initial_flap=True)
            elif key == pygame.K_s:
                self.state = "shop"
            return False

        if self.state == "shop":
            if key in (pygame.K_ESCAPE, pygame.K_m):
                self.state = "menu"
            return False

        if self.state != "playing":
            return False

        if self.paused:
            if key == pygame.K_ESCAPE:
                self.paused = False
            return False

        if key == pygame.K_ESCAPE:
            if self.game_over:
                self.return_to_menu()
            else:
                self.paused = True
            return False
        if key == pygame.K_m and self.game_over:
            self.return_to_menu()
            return False
        if key == pygame.K_r and self.game_over:
            self.start_run()
            return False
        if key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
            if self.game_over:
                self.start_run(initial_flap=True)
                return False
            return True
        return False

    def handle_click(self, position: tuple[int, int]) -> bool:
        if self.state == "menu":
            for action, button in self.menu_buttons.items():
                if button.contains(position):
                    if action == "play":
                        self.start_run()
                    elif action == "shop":
                        self.state = "shop"
                    elif action == "quit":
                        pygame.quit()
                        sys.exit(0)
            return False

        if self.state == "shop":
            for rect, skin in self.shop_cards:
                if rect.collidepoint(position):
                    self.buy_or_select_skin(str(skin["id"]))
                    return False
            if self.get_back_button().contains(position):
                self.state = "menu"
            return False

        if self.state == "playing":
            if self.paused:
                if not self.pause_buttons:
                    self.build_pause_buttons()
                for action, button in self.pause_buttons.items():
                    if button.contains(position):
                        if action == "resume":
                            self.paused = False
                        elif action == "menu":
                            self.return_to_menu()
                        return False
                return False
            if self.play_button.contains(position):
                self.paused = True
                return False
            if self.game_over:
                if not self.game_over_buttons:
                    self.build_game_over_buttons()
                for action, button in self.game_over_buttons.items():
                    if button.contains(position):
                        if action == "restart":
                            self.start_run(initial_flap=True)
                        elif action == "menu":
                            self.return_to_menu()
                        return False
                self.start_run(initial_flap=True)
                return False
            return True

        return False

    def update_menu_scene(self, dt: float) -> None:
        self.update_city(dt, playing=False)
        for cloud in self.clouds:
            cloud.update(dt)
            if cloud.x < -90 * self.scale:
                cloud.x = settings.SCREEN_WIDTH + 40 * self.scale

    def update(self, dt: float, flap: bool) -> None:
        self.player.update(dt, flap)
        self.update_city(dt, playing=True)

        for obstacle in self.obstacles:
            obstacle.update(dt)
            if not obstacle.passed and obstacle.x + settings.OBSTACLE_WIDTH < self.player.rect.x:
                obstacle.passed = True
                self.score += 1
                self.best_score = max(self.best_score, self.score)

        for cloud in self.clouds:
            cloud.update(dt)
            if cloud.x < -90 * self.scale:
                cloud.x = settings.SCREEN_WIDTH + 40 * self.scale

        for coin in self.coins:
            coin.update(dt)

        self.obstacles = [obstacle for obstacle in self.obstacles if obstacle.x + settings.OBSTACLE_WIDTH > -10]
        self.coins = [coin for coin in self.coins if coin.x > -30]
        self.check_collisions()

    def check_collisions(self) -> None:
        if self.player.rect.bottom >= settings.SCREEN_HEIGHT - settings.GROUND_HEIGHT:
            self.game_over = True

        for obstacle in self.obstacles:
            if obstacle.collides(self.player.rect):
                self.game_over = True
                return

        remaining_coins: list[Coin] = []
        for coin in self.coins:
            if coin.rect.colliderect(self.player.rect):
                self.score += 3
                self.run_coins += 1
                self.best_score = max(self.best_score, self.score)
            else:
                remaining_coins.append(coin)
        self.coins = remaining_coins

    def draw(self) -> None:
        self.draw_background()

        for cloud in self.clouds:
            cloud.draw(self.screen)

        if self.state == "menu":
            self.draw_menu()
        elif self.state == "shop":
            self.draw_shop()
        else:
            for coin in self.coins:
                coin.draw(self.screen)
            for obstacle in self.obstacles:
                obstacle.draw(self.screen)
            self.player.draw(self.screen)
            self.draw_hud()
            if self.paused:
                self.draw_pause_overlay()
            if self.game_over:
                self.draw_game_over()

        pygame.display.flip()

    def draw_background(self) -> None:
        self.screen.blit(self.static_background, (0, 0))
        self.draw_city_background()

    def draw_background_glow(self) -> None:
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (*settings.SKY_GLOW, 90), (int(settings.SCREEN_WIDTH * 0.78), int(settings.SCREEN_HEIGHT * 0.18)), self.sc(140))
        pygame.draw.circle(overlay, settings.MENU_GLOW, (int(settings.SCREEN_WIDTH * 0.2), int(settings.SCREEN_HEIGHT * 0.28)), self.sc(220))
        pygame.draw.circle(overlay, (255, 255, 255, 35), (int(settings.SCREEN_WIDTH * 0.55), int(settings.SCREEN_HEIGHT * 0.62)), self.sc(180))
        return overlay

    def build_static_background(self) -> pygame.Surface:
        background = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        for y in range(settings.SCREEN_HEIGHT):
            progress = y / settings.SCREEN_HEIGHT
            color = (
                int(settings.SKY_TOP[0] * (1 - progress) + settings.SKY_BOTTOM[0] * progress),
                int(settings.SKY_TOP[1] * (1 - progress) + settings.SKY_BOTTOM[1] * progress),
                int(settings.SKY_TOP[2] * (1 - progress) + settings.SKY_BOTTOM[2] * progress),
            )
            pygame.draw.line(background, color, (0, y), (settings.SCREEN_WIDTH, y))

        background.blit(self.draw_background_glow(), (0, 0))

        ground_y = settings.SCREEN_HEIGHT - settings.GROUND_HEIGHT
        pygame.draw.rect(background, settings.GROUND, (0, ground_y, settings.SCREEN_WIDTH, settings.GROUND_HEIGHT))
        pygame.draw.rect(background, settings.GROUND_LINE, (0, ground_y, settings.SCREEN_WIDTH, max(8, self.sc(8))))

        stripe_step = max(48, int(48 * self.scale))
        stripe_width = max(24, int(24 * self.scale))
        stripe_height = max(40, int(40 * self.scale))
        stripe_y = ground_y + max(22, int(22 * self.scale))
        for stripe_x in range(-20, settings.SCREEN_WIDTH + stripe_step, stripe_step):
            pygame.draw.rect(background, (61, 109, 73), (stripe_x, stripe_y, stripe_width, stripe_height), border_radius=max(8, self.sc(8)))

        return background.convert()

    def update_city(self, dt: float, playing: bool) -> None:
        speed_factor = 1.0 if playing else 0.45
        for index, layer in enumerate(self.city_layers):
            self.city_offsets[index] = (self.city_offsets[index] + layer["speed"] * speed_factor * dt) % layer["width"]

    def build_city_layers(self) -> list[dict[str, object]]:
        layers = [
            {
                "color": settings.CITY_FAR,
                "speed": settings.OBSTACLE_SPEED * 0.28,
                "base_y": int(settings.SCREEN_HEIGHT * 0.70),
                "buildings": self.generate_buildings(self.sc(110), self.sc(14), self.sc(60), self.sc(160)),
            },
            {
                "color": settings.CITY_MID,
                "speed": settings.OBSTACLE_SPEED * 0.48,
                "base_y": int(settings.SCREEN_HEIGHT * 0.77),
                "buildings": self.generate_buildings(self.sc(130), self.sc(12), self.sc(90), self.sc(210)),
            },
            {
                "color": settings.CITY_NEAR,
                "speed": settings.OBSTACLE_SPEED * 0.68,
                "base_y": int(settings.SCREEN_HEIGHT * 0.84),
                "buildings": self.generate_buildings(self.sc(160), self.sc(10), self.sc(110), self.sc(250)),
            },
        ]
        for layer in layers:
            layer["width"] = max(building["x"] + building["width"] for building in layer["buildings"]) + self.sc(40)
            layer["surface"] = self.build_city_layer_surface(layer)
        return layers

    def generate_buildings(self, target_width: int, gap: int, min_height: int, max_height: int) -> list[dict[str, int]]:
        buildings: list[dict[str, int]] = []
        x = 0
        heights = [min_height, max_height, int((min_height + max_height) * 0.72), int((min_height + max_height) * 0.58)]
        widths = [self.sc(48), self.sc(62), self.sc(84), self.sc(72), self.sc(56)]
        roof_types = [0, 1, 2, 1, 0]
        index = 0
        while x < target_width:
            width = widths[index % len(widths)]
            height = heights[index % len(heights)]
            buildings.append(
                {
                    "x": x,
                    "width": width,
                    "height": height,
                    "roof": roof_types[index % len(roof_types)],
                }
            )
            x += width + gap
            index += 1
        return buildings

    def draw_city_background(self) -> None:
        for index, layer in enumerate(self.city_layers):
            layer_width = int(layer["width"])
            offset = int(self.city_offsets[index])
            start_x = -offset
            while start_x < settings.SCREEN_WIDTH + layer_width:
                self.screen.blit(layer["surface"], (start_x, 0))
                start_x += layer_width

    def build_city_layer_surface(self, layer: dict[str, object]) -> pygame.Surface:
        layer_width = int(layer["width"])
        layer_surface = pygame.Surface((layer_width, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        color = layer["color"]
        base_y = int(layer["base_y"])
        for building in layer["buildings"]:
            x = int(building["x"])
            width = int(building["width"])
            height = int(building["height"])
            rect = pygame.Rect(x, base_y - height, width, height)
            pygame.draw.rect(layer_surface, color, rect, border_radius=self.sc(3))
            self.draw_building_roof(layer_surface, rect, int(building["roof"]), color)
            self.draw_building_windows(layer_surface, rect)
        return layer_surface

    def draw_building_roof(self, target: pygame.Surface, rect: pygame.Rect, roof_type: int, color: tuple[int, int, int]) -> None:
        if roof_type == 1:
            pygame.draw.rect(target, color, (rect.x + rect.width // 3, rect.y - self.sc(18), self.sc(10), self.sc(18)), border_radius=3)
        elif roof_type == 2:
            pygame.draw.polygon(
                target,
                color,
                [(rect.x + self.sc(8), rect.y), (rect.centerx, rect.y - self.sc(12)), (rect.right - self.sc(8), rect.y)],
            )

    def draw_building_windows(self, target: pygame.Surface, rect: pygame.Rect) -> None:
        window_w = max(3, self.sc(4))
        window_h = max(5, self.sc(6))
        gap_x = max(6, self.sc(8))
        gap_y = max(8, self.sc(10))
        for x in range(rect.x + self.sc(8), rect.right - window_w - self.sc(4), gap_x):
            for y in range(rect.y + self.sc(10), rect.bottom - window_h - self.sc(8), gap_y):
                if ((x + y) // gap_x) % 3 != 0:
                    pygame.draw.rect(target, settings.CITY_WINDOW, (x, y, window_w, window_h), border_radius=2)

    def draw_hud(self) -> None:
        score_panel = pygame.Rect(self.sc(22), self.sc(18), self.sc(176), self.sc(88))
        panel_surface = pygame.Surface(score_panel.size, pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, settings.HUD_PANEL, panel_surface.get_rect(), border_radius=self.sc(18))
        self.screen.blit(panel_surface, score_panel.topleft)
        pygame.draw.rect(self.screen, settings.HUD_STROKE, score_panel, width=2, border_radius=self.sc(18))

        score_label = self.font_tiny.render("Score", True, settings.HUD_ACCENT)
        score_value = self.font_large.render(str(self.score), True, settings.WHITE)
        self.screen.blit(score_label, (score_panel.x + self.sc(16), score_panel.y + self.sc(10)))
        self.screen.blit(score_value, (score_panel.x + self.sc(16), score_panel.y + self.sc(26)))

        coins_text = self.font_small.render(f"Coins {self.total_coins + self.run_coins}", True, settings.WHITE)
        self.screen.blit(coins_text, (score_panel.x + self.sc(92), score_panel.y + self.sc(48)))

        hint = self.font_small.render("SPACE / CLICK to fly", True, settings.WHITE)
        self.screen.blit(hint, (self.sc(24), settings.SCREEN_HEIGHT - settings.GROUND_HEIGHT + self.sc(28)))

        self.play_button = Button(self.top_right_button_rect(), "Pause", "hud")
        self.draw_button(self.play_button)

    def draw_game_over(self) -> None:
        panel = pygame.Rect(0, 0, self.sc(420), self.sc(250))
        panel.center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        self.draw_panel(panel, radius=self.sc(22))

        title = self.font_large.render("Crash!", True, settings.TEXT)
        subtitle = self.font_medium.render(f"Score: {self.score}   Best: {self.best_score}", True, settings.TEXT)
        reward = self.font_small.render(f"Coins earned this run: {self.run_coins}", True, settings.TEXT)
        retry = self.font_small.render("Press R/Space to restart or M/Esc for menu", True, settings.TEXT)

        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + self.sc(50))))
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.y + self.sc(96))))
        self.screen.blit(reward, reward.get_rect(center=(panel.centerx, panel.y + self.sc(132))))
        self.screen.blit(retry, retry.get_rect(center=(panel.centerx, panel.y + self.sc(166))))

        self.build_game_over_buttons(panel)
        for button in self.game_over_buttons.values():
            self.draw_button(button)

    def draw_menu(self) -> None:
        content_width = min(self.sc(1080), settings.SCREEN_WIDTH - self.sc(140))
        content_height = min(self.sc(500), settings.SCREEN_HEIGHT - self.sc(120))
        content_rect = pygame.Rect(0, 0, content_width, content_height)
        content_rect.center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)

        left_width = int(content_rect.width * 0.48)
        gap = self.sc(24)
        left_panel = pygame.Rect(content_rect.x, content_rect.y, left_width, content_rect.height)
        right_panel = pygame.Rect(left_panel.right + gap, content_rect.y, content_rect.width - left_width - gap, content_rect.height)
        preview_panel = pygame.Rect(right_panel.x, right_panel.y, right_panel.width, int(right_panel.height * 0.52))
        stats_panel = pygame.Rect(right_panel.x, preview_panel.bottom + gap, right_panel.width, right_panel.bottom - preview_panel.bottom - gap)

        self.draw_panel(left_panel, radius=self.sc(28))
        self.draw_panel(preview_panel, radius=self.sc(24), alpha=208)
        self.draw_panel(stats_panel, radius=self.sc(24), alpha=214)

        top = left_panel.y + self.sc(28)
        left_text_x = left_panel.x + self.sc(28)
        available_text_width = left_panel.width - self.sc(56)
        self.screen.blit(self.font_tiny.render("FULLSCREEN ARCADE", True, settings.ACCENT_DARK), (left_text_x, top))
        self.screen.blit(self.font_large.render(settings.TITLE, True, settings.TEXT), (left_text_x, top + self.sc(30)))
        self.draw_wrapped_text(
            "Pilot a plane, grab coins and unlock new skins.",
            self.font_medium,
            settings.TEXT,
            left_text_x,
            top + self.sc(86),
            available_text_width,
            self.sc(34),
        )
        self.draw_wrapped_text(
            "Esc during flight opens pause instead of throwing you straight back to the menu.",
            self.font_small,
            settings.TEXT,
            left_text_x,
            top + self.sc(160),
            available_text_width,
            self.sc(26),
        )

        button_x = left_panel.x + self.sc(28)
        button_y = top + self.sc(252)
        button_width = min(self.sc(320), left_panel.width - self.sc(56))
        button_height = self.sc(58)
        button_gap = self.sc(18)
        self.menu_buttons = {
            "play": Button(pygame.Rect(button_x, button_y, button_width, button_height), "Start Run", "primary"),
            "shop": Button(pygame.Rect(button_x, button_y + button_height + button_gap, button_width, button_height), "Skin Shop", "secondary"),
            "quit": Button(pygame.Rect(button_x, button_y + (button_height + button_gap) * 2, button_width, button_height), "Quit", "ghost"),
        }
        for button in self.menu_buttons.values():
            self.draw_button(button)

        preview_rect = pygame.Rect(0, 0, self.sc(220), self.sc(110))
        preview_rect.center = preview_panel.center
        preview_plane = make_player(self.skin_by_id[self.selected_skin_id])
        preview_plane.rect.center = preview_rect.center
        preview_plane.bob_phase = pygame.time.get_ticks() / 180
        preview_plane.draw(self.screen)
        caption = self.font_small.render("Current plane skin", True, settings.TEXT)
        name = self.font_medium.render(self.skin_by_id[self.selected_skin_id]["name"], True, settings.TEXT)
        self.screen.blit(caption, caption.get_rect(center=(preview_panel.centerx, preview_panel.y + self.sc(44))))
        self.screen.blit(name, name.get_rect(center=(preview_panel.centerx, preview_panel.bottom - self.sc(36))))

        stats = [
            f"Coins: {self.total_coins}",
            f"Best score: {self.best_score}",
            f"Equipped: {self.skin_by_id[self.selected_skin_id]['name']}",
            "Enter to start, S to open shop",
        ]
        for index, line in enumerate(stats):
            text = self.font_small.render(line, True, settings.TEXT)
            self.screen.blit(text, (stats_panel.x + self.sc(22), stats_panel.y + self.sc(24 + index * 32)))

    def draw_shop(self) -> None:
        header_panel = pygame.Rect(self.sc(46), self.sc(34), settings.SCREEN_WIDTH - self.sc(92), self.sc(104))
        self.draw_panel(header_panel, radius=self.sc(24), alpha=215)
        self.screen.blit(self.font_large.render("Skin Shop", True, settings.TEXT), (header_panel.x + self.sc(18), header_panel.y + self.sc(18)))
        self.screen.blit(self.font_small.render(f"Balance: {self.total_coins} coins", True, settings.TEXT), (header_panel.x + self.sc(20), header_panel.y + self.sc(64)))
        self.screen.blit(self.font_small.render("Click a card to buy or equip.", True, settings.TEXT), (header_panel.x + self.sc(260), header_panel.y + self.sc(64)))

        self.shop_cards = []
        card_width = self.sc(162)
        card_height = self.sc(212)
        gap = self.sc(18)
        total_width = len(settings.SKINS) * card_width + (len(settings.SKINS) - 1) * gap
        start_x = max(self.sc(40), (settings.SCREEN_WIDTH - total_width) // 2)
        start_y = self.sc(170)

        for index, skin in enumerate(settings.SKINS):
            x = start_x + index * (card_width + gap)
            rect = pygame.Rect(x, start_y, card_width, card_height)
            self.shop_cards.append((rect, skin))
            self.draw_skin_card(rect, skin)

        self.draw_button(self.get_back_button())

    def draw_skin_card(self, rect: pygame.Rect, skin: dict[str, object]) -> None:
        hovered = rect.collidepoint(self.mouse_pos)
        lift = self.sc(8) if hovered else 0
        draw_rect = rect.move(0, -lift)
        fill = settings.CARD_HOVER if hovered else settings.PANEL
        self.draw_panel(draw_rect, radius=self.sc(20), alpha=232 if hovered else 216, fill=fill)

        preview = make_player(skin)
        preview.rect.center = (draw_rect.centerx, draw_rect.y + self.sc(74))
        preview.bob_phase = pygame.time.get_ticks() / 170
        preview.draw(self.screen)

        name = self.font_small.render(str(skin["name"]), True, settings.TEXT)
        self.screen.blit(name, name.get_rect(center=(draw_rect.centerx, draw_rect.y + self.sc(128))))

        cost_label = "Free" if int(skin["cost"]) == 0 else f"{skin['cost']} coins"
        cost_surface = self.font_tiny.render(cost_label, True, settings.TEXT)
        self.screen.blit(cost_surface, cost_surface.get_rect(center=(draw_rect.centerx, draw_rect.y + self.sc(156))))

        status, color = self.get_skin_status(str(skin["id"]), int(skin["cost"]))
        status_surface = self.font_tiny.render(status, True, color)
        self.screen.blit(status_surface, status_surface.get_rect(center=(draw_rect.centerx, draw_rect.y + self.sc(186))))

        border_color = settings.ACCENT if self.selected_skin_id == skin["id"] else (settings.BUTTON_HOVER if hovered else settings.PANEL_STROKE)
        pygame.draw.rect(self.screen, border_color, draw_rect, width=3, border_radius=self.sc(20))

    def draw_pause_overlay(self) -> None:
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 28, 36, 110))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(0, 0, self.sc(380), self.sc(220))
        panel.center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        self.draw_panel(panel, radius=self.sc(24))

        title = self.font_large.render("Paused", True, settings.TEXT)
        subtitle = self.font_small.render("Esc to resume or choose an action.", True, settings.TEXT)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + self.sc(48))))
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.y + self.sc(88))))

        self.build_pause_buttons(panel)
        for button in self.pause_buttons.values():
            self.draw_button(button)

    def get_skin_status(self, skin_id: str, cost: int) -> tuple[str, tuple[int, int, int]]:
        if skin_id == self.selected_skin_id:
            return "Equipped", settings.SUCCESS
        if skin_id in self.unlocked_skins:
            return "Owned - click to equip", settings.TEXT
        if self.total_coins >= cost:
            return "Affordable - click to buy", settings.ACCENT_DARK
        return "Locked", settings.LOCKED

    def buy_or_select_skin(self, skin_id: str) -> None:
        skin = self.skin_by_id[skin_id]
        if skin_id not in self.unlocked_skins:
            cost = int(skin["cost"])
            if self.total_coins < cost:
                return
            self.total_coins -= cost
            self.unlocked_skins.add(skin_id)

        self.selected_skin_id = skin_id
        self.persist_progress()

    def start_run(self, initial_flap: bool = False) -> None:
        if self.state == "playing" and (self.run_coins or self.score):
            self.persist_progress()
        self.reset()
        if initial_flap:
            self.player.velocity_y = -settings.PLAYER_FLAP_FORCE
        self.state = "playing"

    def return_to_menu(self) -> None:
        if self.run_coins or self.score:
            self.persist_progress()
        self.state = "menu"
        self.obstacles.clear()
        self.coins.clear()
        self.paused = False
        self.game_over = False
        self.pause_buttons = {}
        self.game_over_buttons = {}

    def persist_progress(self) -> None:
        if self.run_coins:
            self.total_coins += self.run_coins
            self.run_coins = 0
        self.best_score = max(self.best_score, self.score)
        save_save(
            {
                "coins": self.total_coins,
                "best_score": self.best_score,
                "selected_skin": self.selected_skin_id,
                "unlocked_skins": sorted(self.unlocked_skins),
            }
        )

    def get_back_button(self) -> Button:
        return Button(pygame.Rect(settings.SCREEN_WIDTH - self.sc(174), self.sc(34), self.sc(140), self.sc(42)), "Back", "secondary")

    def draw_panel(
        self,
        rect: pygame.Rect,
        radius: int,
        alpha: int = 220,
        fill: tuple[int, ...] = settings.PANEL,
    ) -> None:
        panel_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        color = fill if len(fill) == 4 else (*fill, alpha)
        pygame.draw.rect(panel_surface, color, panel_surface.get_rect(), border_radius=radius)
        self.screen.blit(panel_surface, rect.topleft)
        pygame.draw.rect(self.screen, settings.PANEL_STROKE, rect, width=2, border_radius=radius)

    def draw_button(self, button: Button) -> None:
        hovered = button.contains(self.mouse_pos)
        draw_rect = button.rect.move(0, -self.sc(4) if hovered else 0)

        if button.variant == "primary":
            fill = settings.BUTTON_HOVER if hovered else settings.ACCENT
            stroke = settings.ACCENT_DARK
            text_color = settings.WHITE
        elif button.variant == "ghost":
            fill = settings.BUTTON_HOVER if hovered else settings.BUTTON_SOFT
            stroke = settings.PANEL_STROKE
            text_color = settings.TEXT
        elif button.variant == "hud":
            fill = settings.HUD_PAUSE_HOVER if hovered else settings.HUD_PAUSE
            stroke = settings.HUD_STROKE
            text_color = settings.WHITE
        else:
            fill = (255, 246, 228) if hovered else settings.BUTTON_SOFT
            stroke = settings.BUTTON_HOVER if hovered else settings.PANEL_STROKE
            text_color = settings.TEXT

        base_rect = draw_rect.inflate(self.sc(10), self.sc(10))
        glow = pygame.Surface(base_rect.size, pygame.SRCALPHA)
        if button.variant == "hud":
            glow.fill((110, 160, 205, 70) if hovered else (70, 110, 150, 42))
        else:
            glow.fill(settings.BUTTON_GLOW if hovered else (255, 255, 255, 36))
        self.screen.blit(glow, base_rect.topleft)
        pygame.draw.rect(self.screen, fill, draw_rect, border_radius=self.sc(16))
        pygame.draw.rect(self.screen, stroke, draw_rect, width=2, border_radius=self.sc(16))
        label = self.font_small.render(button.label, True, text_color)
        self.screen.blit(label, label.get_rect(center=draw_rect.center))

    def build_pause_buttons(self, panel: pygame.Rect | None = None) -> None:
        if panel is None:
            panel = pygame.Rect(0, 0, self.sc(380), self.sc(220))
            panel.center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        button_width = self.sc(150)
        button_height = self.sc(52)
        gap = self.sc(18)
        left = panel.centerx - button_width - gap // 2
        top = panel.y + self.sc(132)
        self.pause_buttons = {
            "resume": Button(pygame.Rect(left, top, button_width, button_height), "Resume", "primary"),
            "menu": Button(pygame.Rect(left + button_width + gap, top, button_width, button_height), "Main Menu", "secondary"),
        }

    def build_game_over_buttons(self, panel: pygame.Rect | None = None) -> None:
        if panel is None:
            panel = pygame.Rect(0, 0, self.sc(420), self.sc(250))
            panel.center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        button_width = self.sc(152)
        button_height = self.sc(48)
        gap = self.sc(18)
        left = panel.centerx - button_width - gap // 2
        top = panel.y + self.sc(188)
        self.game_over_buttons = {
            "restart": Button(pygame.Rect(left, top, button_width, button_height), "Restart", "primary"),
            "menu": Button(pygame.Rect(left + button_width + gap, top, button_width, button_height), "Main Menu", "secondary"),
        }

    def draw_wrapped_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        x: int,
        y: int,
        max_width: int,
        line_height: int,
    ) -> int:
        words = text.split()
        line_words: list[str] = []
        current_y = y

        for word in words:
            trial_words = line_words + [word]
            trial_line = " ".join(trial_words)
            if font.size(trial_line)[0] <= max_width:
                line_words = trial_words
                continue

            if line_words:
                rendered = font.render(" ".join(line_words), True, color)
                self.screen.blit(rendered, (x, current_y))
                current_y += line_height
            line_words = [word]

        if line_words:
            rendered = font.render(" ".join(line_words), True, color)
            self.screen.blit(rendered, (x, current_y))
            current_y += line_height

        return current_y


def main() -> None:
    Game().run()
