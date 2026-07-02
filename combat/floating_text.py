"""Floating text system — damage numbers, pickup notifications, combo popups."""
import math
import pygame
from config import DANGER, WARNING, ACID, ADRENALINE, ON_PRIMARY


class FloatingText:
    def __init__(self, x, y, text, color, life=0.8, vy=-40, size=14):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = life
        self.max_life = life
        self.vy = vy
        self.size = size

    def update(self, dt):
        self.y += self.vy * dt
        self.vy *= 0.95
        self.life -= dt

    @property
    def dead(self):
        return self.life <= 0

    def draw(self, screen, cam_x, cam_y):
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        font = pygame.font.SysFont("Consolas", self.size, bold=True)
        surf = font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        screen.blit(surf, (sx - surf.get_width() // 2, sy))


class FloatingTextSystem:
    def __init__(self):
        self.texts = []

    def add(self, x, y, text, color, life=0.8, vy=-40, size=14):
        self.texts.append(FloatingText(x, y, text, color, life, vy, size))

    def add_damage(self, x, y, damage, crit=False):
        color = DANGER if not crit else (255, 200, 0)
        size = 16 if crit else 13
        self.add(x, y - 10, str(int(damage)), color, life=0.6, vy=-50, size=size)

    def add_pickup(self, x, y, text):
        self.add(x, y - 10, text, ACID, life=1.2, vy=-30, size=12)

    def add_combo(self, x, y, combo):
        if combo < 3:
            return
        text = f"x{combo} COMBO"
        color = WARNING if combo < 5 else ADRENALINE
        self.add(x, y - 20, text, color, life=1.0, vy=-35, size=15)

    def update(self, dt):
        self.texts = [t for t in self.texts if not t.dead]
        for t in self.texts:
            t.update(dt)

    def draw(self, screen, cam_x, cam_y):
        for t in self.texts:
            t.draw(screen, cam_x, cam_y)
