from __future__ import annotations

import random
from typing import Any

import pygame

from ms_rehab_game.screens.base import BaseScreen
from ms_rehab_game.settings import BG_CARD, BG_GAME, CYAN, DARK_GRAY, GAME_COLORS, LIGHT_GRAY, RED, TEXT_MUTED, WEBCAM_PREVIEW_SIZE, WHITE, medal_for_score
from ms_rehab_game.ui.animations import Fireworks, ParticleSystem
from ms_rehab_game.ui.components import Button, draw_progress_bar, draw_text


class RehabGameBase(BaseScreen):
    def __init__(self, manager, game_name: str) -> None:
        super().__init__(manager)
        self.game_name = game_name
        self.settings: dict[str, Any] = {}
        self.level = 1
        self.score = 0
        self.correct_actions = 0
        self.total_actions = 0
        self.time_remaining = 180.0
        self.is_paused = False
        self.game_over = False
        self.new_high_score = False
        self.best_streak = 0
        self.streak = 0
        self.preview_timer = 10.0
        self.hint_timer = 0.0
        self.particles = ParticleSystem()
        self.fireworks = Fireworks(self.particles)
        self.finish_buttons: list[Button] = []
        self.pause_buttons: list[Button] = []
        self.unlocked_achievements: list[str] = []
        self.pause_ready_timer = 0.0
        self.pause_cooldown = 0.0
        # Virtual hand cursor state (updated by games that support it, e.g. MindfulTower)
        self.hand_cursor_pos: tuple[int, int] | None = None
        self.hand_cursor_pinching: bool = False
        self._hand_prev_pinching: bool = False
        self.pause_btn_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        # Subclasses can set this to False to disable swipe-to-pause (e.g. MindfulTower)
        self._swipe_pause_enabled: bool = True

    def on_enter(self, resume: bool = False, from_pause: bool = False, **kwargs) -> None:
        if from_pause:
            self.is_paused = False
            return
        if resume:
            paused = self.manager.database.get_paused_session(self.manager.current_user["id"], self.game_name)
            if paused:
                self._load_state(paused)
                self.is_paused = False
                return
        self.level = self.manager.selected_level
        self.settings = self.manager.database.get_user_game_settings(self.manager.current_user["id"], self.game_name)
        self.score = 0
        self.correct_actions = 0
        self.total_actions = 0
        self.time_remaining = float(self.settings["duration_minutes"] * 60)
        self.is_paused = False
        self.game_over = False
        self.new_high_score = False
        self.best_streak = 0
        self.streak = 0
        self.preview_timer = 10.0
        self.hint_timer = 0.0
        self.unlocked_achievements = []
        self.pause_ready_timer = 2.0
        self.pause_cooldown = 0.0
        self.particles = ParticleSystem()
        self.fireworks = Fireworks(self.particles)
        self.finish_buttons = [
            Button(pygame.Rect(415, 490, 180, 50), "NEXT LEVEL", self._next_level),
            Button(pygame.Rect(610, 490, 180, 50), "REPLAY", self._replay),
            Button(pygame.Rect(805, 490, 180, 50), "MENU", lambda: self.manager.go_to("game_menu")),
        ]
        self.pause_buttons = [
            Button(pygame.Rect(510, 385, 260, 50), "RESUME", self.resume_game),
            Button(pygame.Rect(510, 455, 260, 50), "EXIT TO MENU", self.exit_to_menu),
        ]
        self.reset_game_state()

    def reset_game_state(self) -> None:
        raise NotImplementedError

    def serialize_state(self) -> dict[str, Any]:
        raise NotImplementedError

    def restore_state(self, state: dict[str, Any]) -> None:
        raise NotImplementedError

    def handle_event(self, events, gesture_data) -> None:
        for event in events:
            if self.game_over:
                for button in self.finish_buttons:
                    button.handle_event(event)
            elif self.is_paused:
                for button in self.pause_buttons:
                    button.handle_event(event)
        if self._swipe_pause_enabled:
            if (
                not self.game_over
                and not self.is_paused
                and gesture_data.swipe == "right"
                and self.can_pause()
            ):
                self.pause_game()
            elif self.is_paused and gesture_data.swipe == "left":
                self.resume_game()
        # Virtual hand cursor click dispatch
        if self.hand_cursor_pos is not None:
            just_pinched = self.hand_cursor_pinching and not self._hand_prev_pinching
            if just_pinched:
                self._on_hand_click(self.hand_cursor_pos)
        self._hand_prev_pinching = self.hand_cursor_pinching if self.hand_cursor_pos is not None else False

    def update(self, dt: float, gesture_data) -> None:
        self.particles.update(dt)
        self.fireworks.update(dt, self.manager.screen.get_size())
        self.pause_ready_timer = max(0.0, self.pause_ready_timer - dt)
        self.pause_cooldown = max(0.0, self.pause_cooldown - dt)
        if self.game_over:
            return
        if self.hint_timer > 0:
            self.hint_timer = max(0.0, self.hint_timer - dt)
        if self.is_paused:
            return
        self.time_remaining = max(0.0, self.time_remaining - dt)
        if self.time_remaining <= 0:
            self.end_game()

    def can_pause(self) -> bool:
        has_started = self.score > 0 or self.total_actions > 0 or self.correct_actions > 0
        return has_started and self.pause_ready_timer <= 0 and self.pause_cooldown <= 0

    def _on_hand_click(self, pos: tuple[int, int]) -> None:
        """Dispatch a pinch-click from the virtual hand cursor to the appropriate button."""
        if self.game_over:
            for btn in self.finish_buttons:
                if btn.rect.collidepoint(pos):
                    btn.callback()
                    return
        elif self.is_paused:
            for btn in self.pause_buttons:
                if btn.rect.collidepoint(pos):
                    btn.callback()
                    return
        else:
            # Pause button in the HUD
            if self.pause_btn_rect.collidepoint(pos) and self.can_pause():
                self.pause_game()

    def add_result(self, success: bool, pos: tuple[float, float], finger_hint: str | None = None) -> None:
        self.total_actions += 1
        if success:
            self.correct_actions += 1
            self.score += 100
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            self.particles.emit(pos, random.choice(GAME_COLORS), count=16, speed=160)
            if self.settings.get("sound_enabled", True):
                self.manager.sound_bank.play_success()
            if self.streak > 0 and self.streak % 10 == 0:
                self.score += 500
                self.particles.emit((200, 80), CYAN, count=26, speed=220)
                if self.settings.get("sound_enabled", True):
                    self.manager.sound_bank.play_streak()
        else:
            self.score = max(0, self.score - 30)
            self.streak = 0
            self.particles.emit(pos, RED, count=10, speed=120)
            if self.settings.get("sound_enabled", True):
                self.manager.sound_bank.play_miss()

    def pause_game(self) -> None:
        if not self.can_pause():
            return
        self.is_paused = True
        self.pause_cooldown = 0.75
        self.manager.database.save_paused_session(
            self.manager.current_user["id"],
            self.game_name,
            self.level,
            self.settings["cognitive_mode"],
            self.score,
            int(self.time_remaining),
            self.serialize_state(),
        )

    def resume_game(self) -> None:
        self.is_paused = False
        self.pause_cooldown = 0.75

    def exit_to_menu(self) -> None:
        # Force-save state regardless of cooldown so progress is never lost.
        if self.score > 0 or self.total_actions > 0:
            self.manager.database.save_paused_session(
                self.manager.current_user["id"],
                self.game_name,
                self.level,
                self.settings["cognitive_mode"],
                self.score,
                int(self.time_remaining),
                self.serialize_state(),
            )
        self.manager.go_to("game_menu")

    def trigger_hint(self, duration: float) -> None:
        self.hint_timer = duration

    def end_game(self) -> None:
        if self.total_actions > 0 and self.correct_actions == self.total_actions:
            self.score += 10000
        previous_best = self.manager.database.get_best_score(self.manager.current_user["id"], self.game_name)
        accuracy = (self.correct_actions / self.total_actions * 100.0) if self.total_actions else 0.0
        _, achievements = self.manager.database.save_session(
            self.manager.current_user["id"],
            self.game_name,
            self.level,
            self.settings["cognitive_mode"],
            self.settings["controller_hand"],
            self.score,
            accuracy,
            int(self.settings["duration_minutes"] * 60 - self.time_remaining),
            self.correct_actions,
            self.total_actions,
            {"best_streak": self.best_streak},
        )
        self.unlocked_achievements = achievements
        for achievement in achievements:
            self.manager.push_toast(achievement.replace("_", " ").title())
            if self.settings.get("sound_enabled", True):
                self.manager.sound_bank.play_achievement()
        self.new_high_score = self.score > previous_best
        self.game_over = True
        if self.new_high_score:
            self.fireworks.start()
        if self.settings.get("sound_enabled", True):
            self.manager.sound_bank.play_end()

    def _next_level(self) -> None:
        self.manager.selected_level = min(3, self.level + 1)
        self.manager.go_to(self.game_name, resume=False)

    def _replay(self) -> None:
        self.manager.go_to(self.game_name, resume=False)

    def _load_state(self, paused: dict[str, Any]) -> None:
        self.level = paused["level"]
        self.settings = self.manager.database.get_user_game_settings(self.manager.current_user["id"], self.game_name)
        self.score = paused["score"]
        self.time_remaining = float(paused["time_remaining"])
        self.correct_actions = 0
        self.total_actions = 0
        self.game_over = False
        self.is_paused = False
        self.new_high_score = False
        self.best_streak = 0
        self.streak = 0
        self.preview_timer = 0.0
        self.hint_timer = 0.0
        self.unlocked_achievements = []
        self.pause_ready_timer = 0.0
        self.pause_cooldown = 0.75
        self.finish_buttons = [
            Button(pygame.Rect(415, 490, 180, 50), "NEXT LEVEL", self._next_level),
            Button(pygame.Rect(610, 490, 180, 50), "REPLAY", self._replay),
            Button(pygame.Rect(805, 490, 180, 50), "MENU", lambda: self.manager.go_to("game_menu")),
        ]
        self.pause_buttons = [
            Button(pygame.Rect(510, 385, 260, 50), "RESUME", self.resume_game),
            Button(pygame.Rect(510, 455, 260, 50), "EXIT TO MENU", self.exit_to_menu),
        ]
        self.restore_state(paused["state_json"])

    def draw_hud(self, surface: pygame.Surface, gesture_data) -> None:
        surface.fill(BG_GAME)
        # Left column: game name, level, mode
        draw_text(surface, self.game_name.replace("_", " ").title(), 28, WHITE, (30, 22), bold=True)
        draw_text(surface, f"Level {self.level}", 22, TEXT_MUTED, (30, 60))
        draw_text(surface, f"Mode: {self.settings.get('cognitive_mode', '')}", 20, TEXT_MUTED, (30, 90))
        # Centre column: score & accuracy — positioned to stay left of the timer bar
        draw_text(surface, f"Score: {self.score}", 26, WHITE, (640, 24), center=True, bold=True)
        acc = (self.correct_actions / self.total_actions * 100) if self.total_actions else 0
        draw_text(surface, f"Accuracy: {acc:.1f}%", 20, TEXT_MUTED, (640, 56), center=True)
        # Right column: timer bar + countdown
        sw = surface.get_width()
        bar_rect = pygame.Rect(sw - 350, 28, 280, 20)
        draw_progress_bar(surface, bar_rect, self.time_remaining / max(1, self.settings["duration_minutes"] * 60), CYAN)
        draw_text(surface, f"{int(self.time_remaining)}s", 20, WHITE, (sw - 60, 24))
        # Pause hint — only shown for games that use swipe-to-pause
        if self._swipe_pause_enabled:
            if self.score > 0 or self.total_actions > 0:
                pause_hint = "Swipe right to pause"
            else:
                pause_hint = "Complete one action to unlock pause"
            draw_text(surface, pause_hint, 16, TEXT_MUTED, (sw - 350, 54))
        # ── Hand-clickable PAUSE button ──────────────────────────────────────
        btn_w, btn_h = 130, 36
        self.pause_btn_rect = pygame.Rect(sw - btn_w - 14, 68, btn_w, btn_h)
        hand_hover = self.hand_cursor_pos is not None and self.pause_btn_rect.collidepoint(self.hand_cursor_pos)
        mouse_hover = self.pause_btn_rect.collidepoint(pygame.mouse.get_pos())
        hovered = hand_hover or mouse_hover
        if self.can_pause():
            btn_bg   = CYAN if hovered else BG_CARD
            btn_border = (min(255, CYAN[0] + 50), min(255, CYAN[1] + 50), min(255, CYAN[2] + 50)) if hovered else CYAN
            btn_label  = "\u23f8  PAUSE"
            lbl_color  = WHITE
        else:
            btn_bg     = (30, 40, 52)
            btn_border = DARK_GRAY
            btn_label  = "\u23f8  PAUSE"
            lbl_color  = TEXT_MUTED
        pygame.draw.rect(surface, btn_bg, self.pause_btn_rect, border_radius=8)
        pygame.draw.rect(surface, btn_border, self.pause_btn_rect, width=2, border_radius=8)
        draw_text(surface, btn_label, 15, lbl_color, self.pause_btn_rect.center, center=True, bold=True)
        if gesture_data.frame_surface:
            x = surface.get_width() - WEBCAM_PREVIEW_SIZE[0] - 18
            y = surface.get_height() - WEBCAM_PREVIEW_SIZE[1] - 18
            preview_bg = pygame.Rect(x - 4, y - 4, WEBCAM_PREVIEW_SIZE[0] + 8, WEBCAM_PREVIEW_SIZE[1] + 8)
            pygame.draw.rect(surface, BG_CARD, preview_bg, border_radius=8)
            pygame.draw.rect(surface, LIGHT_GRAY, preview_bg, width=2, border_radius=8)
            surface.blit(gesture_data.frame_surface, (x, y))

    def draw_pause_overlay(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))
        panel = pygame.Rect(surface.get_width() // 2 - 230, 220, 460, 340)
        pygame.draw.rect(surface, BG_CARD, panel, border_radius=12)
        pygame.draw.rect(surface, WHITE, panel, width=2, border_radius=12)
        draw_text(surface, "Game Paused", 36, WHITE, (panel.centerx, panel.y + 38), center=True, bold=True)
        draw_text(surface, f"Score: {self.score}", 24, WHITE, (panel.centerx, panel.y + 95), center=True)
        draw_text(surface, f"Time Remaining: {int(self.time_remaining)}s", 20, TEXT_MUTED, (panel.centerx, panel.y + 130), center=True)
        draw_text(surface, f"Level {self.level}", 20, TEXT_MUTED, (panel.centerx, panel.y + 158), center=True)
        if self._swipe_pause_enabled:
            draw_text(surface, "Swipe left to resume", 17, CYAN, (panel.centerx, panel.y + 188), center=True)
        for button in self.pause_buttons:
            button.draw(surface, hand_pos=self.hand_cursor_pos)

    def draw_finish_modal(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        surface.blit(overlay, (0, 0))
        panel = pygame.Rect(surface.get_width() // 2 - 340, 180, 680, 390)
        pygame.draw.rect(surface, BG_CARD, panel, border_radius=12)
        pygame.draw.rect(surface, CYAN, panel, width=2, border_radius=12)
        # Use a smaller font for the title so it always fits inside the 680px panel
        if self.new_high_score:
            title = "NEW HIGH SCORE!  🏆"
        else:
            title = "Good effort! Keep training!"
        draw_text(surface, title, 28, CYAN if self.new_high_score else WHITE, (panel.centerx, panel.y + 45), center=True, bold=True)
        draw_text(surface, f"Score: {self.score}", 46, WHITE, (panel.centerx, panel.y + 110), center=True, bold=True)
        draw_text(surface, f"Medal: {medal_for_score(self.game_name, self.score)}", 26, TEXT_MUTED, (panel.centerx, panel.y + 172), center=True)
        if self.unlocked_achievements:
            # Wrap long achievement lists to prevent overflow
            ach_text = ", ".join(a.replace("_", " ").title() for a in self.unlocked_achievements)
            draw_text(surface, ach_text, 17, TEXT_MUTED, (panel.centerx, panel.y + 210), center=True)
        for button in self.finish_buttons:
            button.draw(surface, hand_pos=self.hand_cursor_pos)
