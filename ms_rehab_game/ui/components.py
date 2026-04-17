from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from ms_rehab_game.settings import BG_CARD, CYAN, DARK_GRAY, LIGHT_GRAY, TEXT_MUTED, WHITE, get_font


def draw_text(
    surface: pygame.Surface,
    text: str,
    size: int,
    color: tuple[int, int, int],
    pos: tuple[int, int],
    center: bool = False,
    bold: bool = False,
) -> pygame.Rect:
    font = get_font(size, bold=bold)
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=pos) if center else rendered.get_rect(topleft=pos)
    surface.blit(rendered, rect)
    return rect


@dataclass
class Button:
    rect: pygame.Rect
    text: str
    callback: Callable[[], None]
    enabled: bool = True
    accent: tuple[int, int, int] = CYAN

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.callback()

    def draw(self, surface: pygame.Surface, hand_pos: tuple[int, int] | None = None) -> None:
        mouse_hover = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        hand_hover = self.enabled and hand_pos is not None and self.rect.collidepoint(hand_pos)
        hovered = mouse_hover or hand_hover
        fill = self.accent if hovered else BG_CARD
        border = tuple(min(255, value + 50) for value in self.accent) if hovered else self.accent
        if not self.enabled:
            fill = DARK_GRAY
            border = LIGHT_GRAY
        pygame.draw.rect(surface, fill, self.rect, border_radius=12)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=12)
        draw_text(surface, self.text, 24, WHITE if self.enabled else TEXT_MUTED, self.rect.center, center=True, bold=True)


@dataclass
class TextInput:
    rect: pygame.Rect
    placeholder: str
    text: str = ""
    active: bool = False
    password: bool = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif len(event.unicode) == 1 and event.unicode.isprintable():
                self.text += event.unicode

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (18, 23, 33), self.rect, border_radius=8)
        pygame.draw.rect(surface, CYAN if self.active else DARK_GRAY, self.rect, width=2, border_radius=8)
        display = ("*" * len(self.text)) if self.password and self.text else self.text or self.placeholder
        color = WHITE if self.text else TEXT_MUTED
        draw_text(surface, display, 24, color, (self.rect.x + 12, self.rect.y + 11))


@dataclass
class ToggleSwitch:
    rect: pygame.Rect
    value: bool
    label: str

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.value = not self.value

    def draw(self, surface: pygame.Surface) -> None:
        draw_text(surface, self.label, 22, WHITE, (self.rect.x, self.rect.y - 30))
        pygame.draw.rect(surface, CYAN if self.value else DARK_GRAY, self.rect, border_radius=self.rect.height // 2)
        knob = pygame.Rect(self.rect.x, self.rect.y, self.rect.height, self.rect.height)
        if self.value:
            knob.x = self.rect.right - self.rect.height
        pygame.draw.ellipse(surface, WHITE, knob)


@dataclass
class Slider:
    rect: pygame.Rect
    min_value: int
    max_value: int
    value: int
    step: int = 1
    dragging: bool = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.dragging = True
            self._set_from_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(event.pos[0])

    def _set_from_x(self, x_pos: int) -> None:
        ratio = max(0.0, min(1.0, (x_pos - self.rect.x) / self.rect.width))
        raw = self.min_value + ratio * (self.max_value - self.min_value)
        stepped = round(raw / self.step) * self.step
        self.value = max(self.min_value, min(self.max_value, stepped))

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.line(surface, LIGHT_GRAY, self.rect.midleft, self.rect.midright, 6)
        ratio = (self.value - self.min_value) / max(1, self.max_value - self.min_value)
        knob_x = int(self.rect.x + ratio * self.rect.width)
        pygame.draw.line(surface, CYAN, self.rect.midleft, (knob_x, self.rect.centery), 6)
        pygame.draw.circle(surface, WHITE, (knob_x, self.rect.centery), 11)


class ToastManager:
    def __init__(self) -> None:
        self.toasts: list[dict] = []

    def push(self, title: str, color: tuple[int, int, int] = CYAN) -> None:
        self.toasts.append({"title": title, "timer": 0.0, "color": color})

    def update(self, dt: float) -> None:
        for toast in self.toasts:
            toast["timer"] += dt
        self.toasts = [toast for toast in self.toasts if toast["timer"] < 3.0]

    def draw(self, surface: pygame.Surface) -> None:
        for idx, toast in enumerate(self.toasts):
            timer = toast["timer"]
            if timer < 0.4:
                top = -70 + int((timer / 0.4) * 95)
            elif timer > 2.4:
                top = 25 - int(((timer - 2.4) / 0.6) * 95)
            else:
                top = 25
            rect = pygame.Rect(surface.get_width() - 360, top + idx * 70, 320, 52)
            pygame.draw.rect(surface, (18, 23, 33), rect, border_radius=10)
            pygame.draw.rect(surface, toast["color"], rect, width=2, border_radius=10)
            pygame.draw.circle(surface, toast["color"], (rect.x + 24, rect.centery), 12)
            draw_text(surface, toast["title"], 21, WHITE, (rect.x + 45, rect.y + 14), bold=True)


def draw_progress_bar(surface: pygame.Surface, rect: pygame.Rect, ratio: float, color: tuple[int, int, int]) -> None:
    pygame.draw.rect(surface, DARK_GRAY, rect, border_radius=8)
    fill = rect.copy()
    fill.width = int(rect.width * max(0.0, min(1.0, ratio)))
    pygame.draw.rect(surface, color, fill, border_radius=8)
    pygame.draw.rect(surface, LIGHT_GRAY, rect, width=2, border_radius=8)


def draw_checkbox(surface: pygame.Surface, rect: pygame.Rect, checked: bool, label: str) -> None:
    pygame.draw.rect(surface, BG_CARD, rect, border_radius=4)
    pygame.draw.rect(surface, CYAN, rect, width=2, border_radius=4)
    if checked:
        pygame.draw.line(surface, CYAN, (rect.x + 4, rect.centery), (rect.centerx, rect.bottom - 4), 3)
        pygame.draw.line(surface, CYAN, (rect.centerx, rect.bottom - 4), (rect.right - 4, rect.y + 4), 3)
    draw_text(surface, label, 20, WHITE, (rect.right + 10, rect.y - 2))
