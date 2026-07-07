"""
Second-Order Dynamics for procedural animation.
Reference: t3ssel8r "Giving Personality to Procedural Animations using Math"
           https://youtu.be/KPoeNZZ6H4s
Constants and update step verbatim from:
           https://gist.github.com/Andicraft/ab605dda924a0321e755abf8f573ebd7

Works with scalars (float), pygame.math.Vector2, pygame.math.Vector3, or any
type supporting +, -, *, / by a scalar. Drop into your pygame-ce game loop.

Usage:
    dyn = SecondOrderDynamics(f=3.0, z=0.5, r=1.0, x0=Vector2(0, 0))
    # in your update loop:
    smoothed = dyn.update(dt, target_vector2)
"""
import math

try:
    from pygame.math import Vector2, Vector3
    _HAS_PYGAME = True
except ImportError:  # pragma: no cover - self-test runs without pygame
    Vector2 = Vector3 = None
    _HAS_PYGAME = False


class SecondOrderDynamics:
    """Single-channel second-order smoother. Instantiate per value."""

    __slots__ = ("xp", "y", "yd", "k1", "k2", "k3")

    def __init__(self, f: float, z: float, r: float, x0):
        """
        f  - frequency in Hz (response speed; does not change shape)
        z  - damping: 0 undamped, <1 underdamped (springy), 1 critical, >1 slow
        r  - initial response: <0 anticipates, 0 slow start, 1 immediate,
             >1 overshoots, 2 typical for mechanical links
        x0 - initial value (scalar, Vector2, Vector3)
        """
        self.xp = x0
        self.y = x0
        # yd (velocity) starts at the zero of whatever type x0 is.
        # For pygame Vectors, x0 * 0 works; for floats, just 0.0.
        try:
            self.yd = x0 * 0  # works for Vector2/3 and numbers
        except TypeError:
            self.yd = 0.0

        w = 2.0 * math.pi * f
        self.k1 = z / (math.pi * f)
        self.k2 = 1.0 / (w * w)
        self.k3 = r * z / (2.0 * math.pi * f)

    def update(self, dt: float, x, xdot=None):
        """
        Advance one frame. Returns the new smoothed value y.

        dt   - frame delta seconds (use the REAL measured delta, not a fixed
               value — the stability clamp needs the real number)
        x    - current target value
        xdot - optional explicit input velocity. If None, estimated as
               (x - xp) / dt (the standard case for most game inputs).
        """
        if xdot is None:
            if dt <= 0.0:
                xdot = type(self.yd)() if hasattr(self.yd, "__call__") else (self.yd * 0)
            else:
                xdot = (x - self.xp) / dt
            self.xp = x

        # Stability clamp — keeps the system from exploding on large dt.
        # Verbatim from the reference port.
        k2_stable = max(self.k2, max(dt * dt / 2.0 + dt * self.k1 / 2.0,
                                     dt * self.k1))

        # Semi-implicit Euler integration
        self.y = self.y + self.yd * dt
        self.yd = self.yd + (x + xdot * self.k3 - self.y - self.yd * self.k1) * (dt / k2_stable)
        return self.y


def _self_test():
    """Feed a unit step (0 -> 1) and report overshoot + settled value."""
    dyn = SecondOrderDynamics(f=2.0, z=0.5, r=1.0, x0=0.0)
    dt = 1.0 / 60.0
    peak = 0.0
    settled = 0.0
    for i in range(180):  # 3 seconds at 60fps
        y = dyn.update(dt, 1.0)
        if i < 120:
            peak = max(peak, y)
        if i == 179:
            settled = y
    print(f"step response over 3s @60Hz (f=2, z=0.5, r=1, x0=0, target=1):")
    print(f"  peak y     = {peak:.4f}   (expect ~1.0-1.4)")
    print(f"  settled y  = {settled:.4f}   (expect ~1.0)")
    assert peak < 2.0, f"UNSTABLE: peak {peak} exceeded safe range"
    assert abs(settled - 1.0) < 0.1, f"FAILED to settle: {settled}"
    print("  OK — system stable and converged.")


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        _self_test()
    else:
        print("second_order_dynamics.py — drop-in procedural smoother.")
        print("Run with --self-test to verify stability.")
