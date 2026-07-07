"""Spider procedural animation component.

Renders a spider with 8 IK-driven legs using second-order dynamics.
Designed as a component that an enemy class can own and update.

Usage:
    spider = SpiderComponent(world_pos=(x, y))
    spider.update(dt, world_pos, angle)
    spider.draw(screen, camera_offset)
"""
import math
import pygame
from pygame.math import Vector2
from second_order_dynamics import SecondOrderDynamics

# ---- Colors ----
BODY_COLOR = (80, 30, 100)
BODY_HIGHLIGHT = (120, 50, 140)
LEG_COLOR = (60, 20, 80)
LEG_JOINT = (100, 40, 120)
FOOT_COLOR = (180, 60, 200)
EYE_COLOR = (255, 50, 50)
HEAD_COLOR = (60, 20, 80)


class SpiderLeg:
    """One leg with 2-segment IK and second-order foot dynamics."""

    def __init__(self, body_offset, seg_lengths, ground_pos):
        self.body_offset = Vector2(body_offset)     # offset from body center
        self.seg1_len = seg_lengths[0]               # upper leg
        self.seg2_len = seg_lengths[1]               # lower leg
        self.ground_pos = Vector2(ground_pos)         # current foot ground pos
        self.stepping = False
        self.step_t = 0.0
        self.step_from = Vector2(0, 0)
        self.step_to = Vector2(0, 0)

        # Second-order dynamics for foot position
        self.foot_dyn = SecondOrderDynamics(f=8.0, z=0.8, r=1.0, x0=Vector2(ground_pos))

    def update(self, dt, body_pos, body_angle, move_dir, speed):
        """Update leg: check if it needs to step, then step."""
        facing = Vector2(math.cos(body_angle), math.sin(body_angle))
        perp = Vector2(-facing.y, facing.x)
        offset_world = facing * self.body_offset.x + perp * self.body_offset.y
        ideal_pos = body_pos + offset_world + facing * self.seg1_len * 0.8

        if not self.stepping:
            dist = (self.ground_pos - ideal_pos).length()
            if dist > 40:
                self.stepping = True
                self.step_t = 0.0
                self.step_from = self.ground_pos.copy()
                self.step_to = ideal_pos + move_dir * 20

        if self.stepping:
            self.step_t += dt * 6.0
            if self.step_t >= 1.0:
                self.step_t = 1.0
                self.stepping = False
                self.ground_pos = self.step_to.copy()
            else:
                t = self.step_t
                forward = self.step_from.lerp(self.step_to, t)
                lift = math.sin(t * math.pi) * 25
                self.ground_pos = Vector2(forward.x, forward.y - lift)

        self.foot_dyn.update(dt, self.ground_pos)

    def get_joints(self, body_pos, body_angle):
        """Compute hip, knee, foot positions using 2-bone IK."""
        facing = Vector2(math.cos(body_angle), math.sin(body_angle))
        perp = Vector2(-facing.y, facing.x)
        hip = body_pos + facing * self.body_offset.x + perp * self.body_offset.y
        foot = Vector2(self.foot_dyn.y)

        d = (foot - hip).length()
        max_reach = self.seg1_len + self.seg2_len - 1
        d = min(d, max_reach)
        if d < 0.001:
            d = 0.001

        a = self.seg1_len
        b = self.seg2_len
        cos_angle = (a * a + d * d - b * b) / (2 * a * d)
        cos_angle = max(-1, min(1, cos_angle))
        angle = math.acos(cos_angle)

        dir_to_foot = foot - hip
        if dir_to_foot.length() > 0.001:
            dir_to_foot = dir_to_foot.normalize()
        else:
            dir_to_foot = Vector2(0, 1)

        side = self.body_offset.y
        knee_dir = dir_to_foot.rotate_rad(angle if side < 0 else -angle)
        knee = hip + knee_dir * a
        return hip, knee, foot

    def draw(self, screen, body_pos, body_angle, cam_x, cam_y):
        hip, knee, foot = self.get_joints(body_pos, body_angle)
        # Apply camera offset
        h = (int(hip.x - cam_x), int(hip.y - cam_y))
        k = (int(knee.x - cam_x), int(knee.y - cam_y))
        f = (int(foot.x - cam_x), int(foot.y - cam_y))
        pygame.draw.line(screen, LEG_COLOR, h, k, 4)
        pygame.draw.line(screen, LEG_COLOR, k, f, 3)
        pygame.draw.circle(screen, LEG_JOINT, h, 3)
        pygame.draw.circle(screen, LEG_JOINT, k, 2)
        pygame.draw.circle(screen, FOOT_COLOR, f, 4)
        pygame.draw.circle(screen, (255, 200, 255), f, 2)


class SpiderComponent:
    """Procedural spider with 8 legs and second-order body dynamics."""

    def __init__(self, world_pos):
        pos = Vector2(world_pos)
        self.pos = Vector2(pos)
        self.angle = 0.0
        self.body_tilt = 0.0  # for rearing animation

        # Body dynamics
        self.body_dyn = SecondOrderDynamics(f=4.0, z=0.5, r=-1.0, x0=Vector2(pos))
        self.angle_dyn = SecondOrderDynamics(f=6.0, z=1.0, r=0.0, x0=0.0)
        self.tilt_dyn = SecondOrderDynamics(f=5.0, z=0.3, r=0.5, x0=0.0)

        # 8 legs: 4 left, 4 right
        leg_cfg = [
            (-12, -8, 28, 32), (-12, 8, 28, 32),
            (-4, -12, 30, 34), (-4, 12, 30, 34),
            (6, -12, 30, 34), (6, 12, 30, 34),
            (14, -8, 28, 32), (14, 8, 28, 32),
        ]
        self.legs = []
        for ox, oy, s1, s2 in leg_cfg:
            offset = Vector2(ox, oy)
            ground = pos + Vector2(ox + 30 if ox >= 0 else ox - 30, oy * 3)
            self.legs.append(SpiderLeg(offset, (s1, s2), ground))

    def update(self, dt, world_pos, angle, tilt=0.0):
        """Update spider body + legs. world_pos and angle are the target."""
        self.body_dyn.update(dt, Vector2(world_pos))
        self.pos = Vector2(self.body_dyn.y)

        self.angle_dyn.update(dt, angle)
        self.angle = self.angle_dyn.y

        self.tilt_dyn.update(dt, tilt)
        self.body_tilt = self.tilt_dyn.y

        # Compute move direction for leg stepping
        facing = Vector2(math.cos(self.angle), math.sin(self.angle))
        move_dir = facing  # legs step in facing direction

        for leg in self.legs:
            leg.update(dt, self.pos, self.angle, move_dir, 1.0)

    def draw(self, screen, cam_x, cam_y):
        sx = self.pos.x - cam_x
        sy = self.pos.y - cam_y

        # Draw legs first (behind body)
        for leg in self.legs:
            leg.draw(screen, self.pos, self.angle, cam_x, cam_y)

        # Body ellipse
        facing = Vector2(math.cos(self.angle), math.sin(self.angle))
        perp = Vector2(-facing.y, facing.x)
        body_w = 22
        body_h = 16 + abs(self.body_tilt) * 8  # body compresses when rearing
        body_surf = pygame.Surface((body_w * 2, int(body_h * 2)), pygame.SRCALPHA)
        pygame.draw.ellipse(body_surf, BODY_COLOR, (0, 0, body_w * 2, int(body_h * 2)))
        pygame.draw.ellipse(body_surf, BODY_HIGHLIGHT, (0, 0, body_w * 2, int(body_h * 2)), 2)
        angle_deg = -math.degrees(self.angle)
        rotated = pygame.transform.rotate(body_surf, angle_deg)
        rect = rotated.get_rect(center=(int(sx), int(sy)))
        screen.blit(rotated, rect)

        # Head
        head_pos = self.pos + facing * 20
        head_h = 10 + self.body_tilt * 6
        head_surf = pygame.Surface((24, int(max(4, head_h * 2))), pygame.SRCALPHA)
        pygame.draw.ellipse(head_surf, HEAD_COLOR, (0, 0, 24, int(max(4, head_h * 2))))
        rotated_head = pygame.transform.rotate(head_surf, angle_deg)
        head_rect = rotated_head.get_rect(center=(int(head_pos.x - cam_x), int(head_pos.y - cam_y)))
        screen.blit(rotated_head, head_rect)

        # Eyes
        eye_offset = 18
        eye_spread = 6
        eye1 = self.pos + facing * eye_offset + perp * eye_spread
        eye2 = self.pos + facing * eye_offset - perp * eye_spread
        pygame.draw.circle(screen, EYE_COLOR,
                          (int(eye1.x - cam_x), int(eye1.y - cam_y)), 3)
        pygame.draw.circle(screen, EYE_COLOR,
                          (int(eye2.x - cam_x), int(eye2.y - cam_y)), 3)
