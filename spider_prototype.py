"""Procedural spider enemy prototype with second-order dynamics legs.

The spider has:
- A body that tracks its movement target with springy second-order dynamics
- 8 legs that each use IK (2-bone) + second-order dynamics for the foot tip
- Legs that step forward alternately (tetrapod gait) when the body moves
- Each leg foot lifts off the ground during a step, creating realistic walking

Run standalone to see the spider walk across the screen.
"""
import math
import random
import pygame
from pygame.math import Vector2
from second_order_dynamics import SecondOrderDynamics

# ---- Colors ----
BG = (15, 18, 24)
BODY_COLOR = (80, 30, 100)        # dark purple
BODY_HIGHLIGHT = (120, 50, 140)
LEG_COLOR = (60, 20, 80)
LEG_JOINT = (100, 40, 120)
FOOT_COLOR = (180, 60, 200)
TARGET_COLOR = (200, 200, 80)
EYE_COLOR = (255, 50, 50)

SCREEN_W = 1280
SCREEN_H = 720


class SpiderLeg:
    """One leg with 2-segment IK and second-order foot dynamics."""

    def __init__(self, rest_angle, body_offset, seg_lengths, ground_pos):
        self.rest_angle = rest_angle        # preferred angle relative to body facing
        self.body_offset = body_offset      # Vector2 offset from body center
        self.seg1_len = seg_lengths[0]      # upper leg
        self.seg2_len = seg_lengths[1]      # lower leg
        self.ground_pos = ground_pos.copy()  # current foot ground position
        self.target_pos = ground_pos.copy() # where the foot wants to be
        self.stepping = False
        self.step_t = 0.0                   # step progress 0-1
        self.step_from = Vector2(0, 0)
        self.step_to = Vector2(0, 0)

        # Second-order dynamics for foot position (springy settling)
        self.foot_dyn = SecondOrderDynamics(f=8.0, z=0.8, r=1.0, x0=ground_pos)

    def update(self, dt, body_pos, body_angle, move_dir, speed):
        """Update leg: check if it needs to step, then step."""
        # Compute ideal rest position for this foot
        facing = Vector2(math.cos(body_angle), math.sin(body_angle))
        perp = Vector2(-facing.y, facing.x)
        offset_world = facing * self.body_offset.x + perp * self.body_offset.y
        ideal_pos = body_pos + offset_world + facing * self.seg1_len * 0.8

        # If not stepping, check if foot is too far from ideal
        if not self.stepping:
            dist = (self.ground_pos - ideal_pos).length()
            if dist > 40:  # step threshold
                self.stepping = True
                self.step_t = 0.0
                self.step_from = self.ground_pos.copy()
                self.step_to = ideal_pos + move_dir * 20

        # If stepping, animate the foot
        if self.stepping:
            self.step_t += dt * 6.0  # step speed
            if self.step_t >= 1.0:
                self.step_t = 1.0
                self.stepping = False
                self.ground_pos = self.step_to.copy()
            else:
                # Arc interpolation: lift foot in the middle of the step
                t = self.step_t
                # Forward position
                forward = self.step_from.lerp(self.step_to, t)
                # Lift height (parabolic arc)
                lift = math.sin(t * math.pi) * 25
                self.ground_pos = Vector2(forward.x, forward.y - lift)

        # Smooth the foot position with second-order dynamics
        self.foot_dyn.update(dt, self.ground_pos)

    def get_joints(self, body_pos, body_angle):
        """Compute knee and foot joint positions using 2-bone IK."""
        facing = Vector2(math.cos(body_angle), math.sin(body_angle))
        perp = Vector2(-facing.y, facing.x)
        hip = body_pos + facing * self.body_offset.x + perp * self.body_offset.y

        foot = Vector2(self.foot_dyn.y)  # smoothed foot position

        # 2-bone IK: solve for knee position
        d = (foot - hip).length()
        max_reach = self.seg1_len + self.seg2_len - 1
        d = min(d, max_reach)

        # Law of cosines
        if d < 0.001:
            d = 0.001
        a = self.seg1_len
        b = self.seg2_len
        cos_angle = (a * a + d * d - b * b) / (2 * a * d)
        cos_angle = max(-1, min(1, cos_angle))
        angle = math.acos(cos_angle)

        # Direction from hip to foot
        dir_to_foot = (foot - hip)
        if dir_to_foot.length() > 0.001:
            dir_to_foot = dir_to_foot.normalize()
        else:
            dir_to_foot = Vector2(0, 1)

        # Knee is perpendicular to hip-foot line, offset by angle
        perp_dir = Vector2(-dir_to_foot.y, dir_to_foot.x)
        # Bend backward (knees point away from body center)
        # Determine which side the leg is on
        side = self.body_offset.y
        if side < 0:
            perp_dir = -perp_dir

        knee_angle = angle
        knee_dir = dir_to_foot.rotate_rad(knee_angle if side < 0 else -knee_angle)
        knee = hip + knee_dir * a

        return hip, knee, foot

    def draw(self, screen, body_pos, body_angle):
        hip, knee, foot = self.get_joints(body_pos, body_angle)

        # Draw leg segments (thick lines)
        pygame.draw.line(screen, LEG_COLOR, hip, knee, 4)
        pygame.draw.line(screen, LEG_COLOR, knee, foot, 3)
        # Joints
        pygame.draw.circle(screen, LEG_JOINT, (int(hip.x), int(hip.y)), 3)
        pygame.draw.circle(screen, LEG_JOINT, (int(knee.x), int(knee.y)), 2)
        # Foot
        pygame.draw.circle(screen, FOOT_COLOR, (int(foot.x), int(foot.y)), 4)
        pygame.draw.circle(screen, (255, 200, 255), (int(foot.x), int(foot.y)), 2)


class Spider:
    """Procedural spider with 8 legs and second-order body dynamics."""

    def __init__(self, pos):
        self.pos = Vector2(pos)
        self.target = Vector2(pos)
        self.angle = 0.0

        # Body dynamics — springy with anticipation
        self.body_dyn = SecondOrderDynamics(f=4.0, z=0.5, r=-1.0, x0=Vector2(pos))
        self.angle_dyn = SecondOrderDynamics(f=6.0, z=1.0, r=0.0, x0=0.0)

        # 8 legs: 4 left, 4 right
        leg_cfg = [
            # (body_offset_x, body_offset_y, seg1_len, seg2_len)
            (-12, -8, 28, 32),   # front-left
            (-12, 8, 28, 32),    # front-right
            (-4, -12, 30, 34),   # mid-front-left
            (-4, 12, 30, 34),    # mid-front-right
            (6, -12, 30, 34),    # mid-back-left
            (6, 12, 30, 34),     # mid-back-right
            (14, -8, 28, 32),    # back-left
            (14, 8, 28, 32),     # back-right
        ]

        self.legs = []
        for i, (ox, oy, s1, s2) in enumerate(leg_cfg):
            rest_angle = math.atan2(oy, ox + 20)
            offset = Vector2(ox, oy)
            ground = Vector2(pos) + Vector2(ox + 30 if ox >= 0 else ox - 30, oy * 3)
            leg = SpiderLeg(rest_angle, offset, (s1, s2), ground)
            self.legs.append(leg)

        # Step group alternation (tetrapod gait)
        # Group A: legs 0, 3, 4, 7  (front-left, mid-front-right, mid-back-left, back-right)
        # Group B: legs 1, 2, 5, 6  (front-right, mid-front-left, mid-back-right, back-left)
        self.step_group = 0  # 0 = group A stepping, 1 = group B

    def update(self, dt, target):
        self.target = Vector2(target)
        to_target = self.target - self.pos

        # Update body position with second-order dynamics
        self.body_dyn.update(dt, self.target)
        self.pos = Vector2(self.body_dyn.y)

        # Update facing angle
        if to_target.length() > 5:
            target_angle = math.atan2(to_target.y, to_target.x)
            self.angle_dyn.update(dt, target_angle)
            self.angle = self.angle_dyn.y

        # Compute movement direction for leg stepping
        move_dir = to_target.normalize() if to_target.length() > 1 else Vector2(0, 0)
        speed = to_target.length()

        # Update legs
        for leg in self.legs:
            leg.update(dt, self.pos, self.angle, move_dir, speed)

    def draw(self, screen):
        # Draw legs first (behind body)
        for leg in self.legs:
            leg.draw(screen, self.pos, self.angle)

        # Draw body (oval)
        facing = Vector2(math.cos(self.angle), math.sin(self.angle))
        perp = Vector2(-facing.y, facing.x)
        body_size = (22, 16)
        # Body is an ellipse rotated to facing
        body_surf = pygame.Surface((body_size[0] * 2, body_size[1] * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(body_surf, BODY_COLOR, (0, 0, body_size[0] * 2, body_size[1] * 2))
        pygame.draw.ellipse(body_surf, BODY_HIGHLIGHT, (0, 0, body_size[0] * 2, body_size[1] * 2), 2)
        # Rotate to facing angle
        angle_deg = -math.degrees(self.angle)
        rotated = pygame.transform.rotate(body_surf, angle_deg)
        rect = rotated.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(rotated, rect)

        # Eyes (two red dots at front of body)
        eye_offset = 18
        eye_spread = 6
        eye1 = self.pos + facing * eye_offset + perp * eye_spread
        eye2 = self.pos + facing * eye_offset - perp * eye_spread
        pygame.draw.circle(screen, EYE_COLOR, (int(eye1.x), int(eye1.y)), 3)
        pygame.draw.circle(screen, EYE_COLOR, (int(eye2.x), int(eye2.y)), 3)

        # Head (smaller ellipse at front)
        head_pos = self.pos + facing * 20
        head_surf = pygame.Surface((24, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(head_surf, (60, 20, 80), (0, 0, 24, 20))
        rotated_head = pygame.transform.rotate(head_surf, angle_deg)
        head_rect = rotated_head.get_rect(center=(int(head_pos.x), int(head_pos.y)))
        screen.blit(rotated_head, head_rect)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Procedural Spider Prototype")
    clock = pygame.time.Clock()

    spider = Spider((SCREEN_W // 2, SCREEN_H // 2))
    target = Vector2(SCREEN_W // 2, SCREEN_H // 2)

    trail = []
    time_elapsed = 0.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        time_elapsed += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                target = Vector2(event.pos)

        # Auto-walk: spider follows a moving target in a figure-8
        if not pygame.mouse.get_pressed()[0]:
            t = time_elapsed * 0.5
            target = Vector2(
                SCREEN_W // 2 + math.sin(t) * 350,
                SCREEN_H // 2 + math.sin(t * 2) * 150
            )

        spider.update(dt, target)

        # Trail
        trail.append(Vector2(spider.pos))
        if len(trail) > 60:
            trail.pop(0)

        # Draw
        screen.fill(BG)

        # Draw trail
        for i, p in enumerate(trail):
            alpha = int(255 * (i / len(trail)))
            r = max(1, int(3 * (i / len(trail))))
            pygame.draw.circle(screen, (40, 40, 60), (int(p.x), int(p.y)), r)

        # Draw target
        pygame.draw.circle(screen, TARGET_COLOR, (int(target.x), int(target.y)), 8, 2)
        pygame.draw.line(screen, TARGET_COLOR, (int(target.x) - 12, int(target.y)),
                        (int(target.x) + 12, int(target.y)), 1)
        pygame.draw.line(screen, TARGET_COLOR, (int(target.x), int(target.y) - 12),
                        (int(target.x), int(target.y) + 12), 1)

        # Draw spider
        spider.draw(screen)

        # Info text
        font = pygame.font.SysFont("consolas", 14)
        info = [
            f"FPS: {clock.get_fps():.0f}",
            f"Spider pos: ({spider.pos.x:.0f}, {spider.pos.y:.0f})",
            f"Angle: {math.degrees(spider.angle):.0f}°",
            f"Legs stepping: {sum(1 for l in spider.legs if l.stepping)}/{len(spider.legs)}",
            "",
            "Mouse click to move target, or let auto-walk run",
            "ESC to quit",
        ]
        for i, line in enumerate(info):
            txt = font.render(line, True, (120, 130, 140))
            screen.blit(txt, (12, 12 + i * 16))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
