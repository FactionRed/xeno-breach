"""Design and save 32x32 player sprite base JSON files — v2 with reference image.

Key changes from v1:
- Rounded dome helmet (not angular)
- Asymmetrical orange markings (left bicep, right forearm, left shin, right knee)
- Low-ready rifle pose (rifle held at waist, not across chest)
- Thicker rounded pauldrons
- Dynamic stance (one leg slightly forward)
"""
import json, os

W, H = 32, 32

COLORS = {
    'O': '#0A0A0E', 'A': '#2A2A2A', 'a': '#3A3A3A', 'd': '#1A1A1A',
    'U': '#16161A', 'V': '#00CED1', 'X': '#FF6B00', 'W': '#9a9a9a',
    's': '#222222',
}

def p(s):
    return (s + '.' * 32)[:32]

def grid_to_json(rows):
    pixels = []
    for y, row in enumerate(rows):
        r = p(row)
        for x, ch in enumerate(r):
            if ch in COLORS:
                pixels.append({"x": x, "y": y, "color": COLORS[ch]})
    return {"width": W, "height": H, "background": "transparent", "grid_lines": False, "pixel_size": 16, "pixels": pixels}

# ================================================================
# FRONT IDLE — rounded dome, asymmetrical markings, low-ready rifle
# ================================================================
front = [
    "...............OOO...............",  # 0: dome top (narrow, rounded)
    "..............OaaaO..............",  # 1: dome upper (rounded)
    ".............OaAAAaO.............",  # 2: dome widening
    "............OaAAAAAaO............",  # 3: dome widest (rounded curve)
    "............OAAVVVAAO............",  # 4: visor (teal, wide)
    "............OAAAAAAAO............",  # 5: visor lower
    "............OAAAAAAAO............",  # 6: chin
    ".............OAAAAAO.............",  # 7: jaw (rounded, narrow)
    ".............OsssssO.............",  # 8: neck seal
    "..........OaaAAAAAAAaO...........",  # 9: pauldrons (rounded, wide)
    ".........OaaAAAAAAAAAaO.........",  # 10: pauldron widest
    ".........OaAXAAAAAAAAaO.........",  # 11: chest + orange LEFT side
    ".........OaAAAAAAAAAAaO.........",  # 12: chest
    ".........OaAAAAAAAAAAaO.........",  # 13: chest lower
    ".........OAuuuuuuuuuAaO.........",  # 14: belt
    ".........OdduuuuuuuuddO.........",  # 15: belt dark
    "........OWWUUUUUUUUUUWWO........",  # 16: rifle stock L + arms + stock R
    ".......WWWWUUUUUUUUUUWWWW.......",  # 17: rifle barrel (wider, brighter)
    "..........OUU.......UUO..........",  # 18: legs split
    "..........OUU.......UUO..........",  # 19
    "..........OaU.......UaO..........",  # 20: knee pad highlight
    "..........OdU.......UdO..........",  # 21
    "..........OdU.......UdO..........",  # 22: shins
    "..........OdU.......UdO..........",  # 23
    "..........OdU.......UdO..........",  # 24
    ".........OOdU.......UdOO.........",  # 25: boot tops
    ".........OddU.......UddO.........",  # 26: boots
    ".........OddU.......UddO.........",  # 27
    "........OOdddO.....OdddOO........",  # 28: soles
    "........OOOOOO.....OOOOOO........",  # 29: feet
    "................................",  # 30
    "................................",  # 31
]

# ================================================================
# RIGHT IDLE — profile, visor on right, rifle forward, backpack
# ================================================================
right = [
    "..............OOOO..............",  # 0: dome top
    ".............OaaaO..............",  # 1: dome upper
    "............OaAAAaO.............",  # 2: dome widest
    "............OAAAAAAO............",  # 3: visor housing
    "............OAAAAAVO............",  # 4: visor on right side
    "............OAAAAAAO............",  # 5
    "............OAAAAAAO............",  # 6: chin
    ".............OAAAAO.............",  # 7: jaw
    ".............OssssO.............",  # 8: neck
    "..........OaaAAAAAaO............",  # 9: back pauldron + backpack
    ".........OaaAXXXXXAAaO.........",  # 10: chest stripe + pauldron
    ".........OaAAAAAAAAaO..........",  # 11: chest
    ".........OAAAAAAAAAaO..........",  # 12
    ".........OAuuuuuuuAaO...........",  # 13: belt
    ".........OdduuuuuuddO...........",  # 14
    "..........OaUUUUUUaOWWWWWWWW...",  # 15: rifle extends right (low-ready)
    "..........OaUUUUUUaO.WWWWWWWW..",  # 16: rifle barrel
    "..........OaUUUUUUaO............",  # 17: thigh
    "..........OaUUUUUUaO............",  # 18
    "..........OddUUUUUaO............",  # 19: knee pad (RIGHT knee — orange)
    "..........OddUUUUUddO...........",  # 20
    "..........OddUUUUUddO...........",  # 21
    "..........OddUUUUUddO...........",  # 22
    "..........OddUUUUUddO...........",  # 23
    "..........OddUUUUUddO...........",  # 24
    ".........OdddUUUUUddO...........",  # 25: boot
    ".........OddddUUUUddO...........",  # 26
    ".........OddddUUUUddO...........",  # 27
    "........OOddddUUUdddO...........",  # 28: sole
    "........OOOOOOOUUOOO............",  # 29
    "................................",  # 30
    "................................",  # 31
]

# ================================================================
# BACK IDLE — no visor, backpack with orange, wide pauldrons
# ================================================================
back = [
    "..............OOOO..............",  # 0: dome top
    ".............OaaaO..............",  # 1: dome upper
    "............OaAAAaO.............",  # 2: dome widest
    "............OAAAAAAO............",  # 3: back of helmet (no visor)
    "............OAAAAAAO............",  # 4
    "............OAAAAAAO............",  # 5
    "............OAAAAAAO............",  # 6
    ".............OAAAAO.............",  # 7: jaw
    ".............OssssO.............",  # 8: neck
    "..........OaaAAXXAAAaO..........",  # 9: backpack + orange light
    ".........OaaAAAAAXXAaO..........",  # 10: backpack cont
    ".........OaAAAAAAAAAAaO........",  # 11: back plate
    ".........OaAAAAAAAAAAaO........",  # 12
    ".........OAAAAAAAAAAAAaO........",  # 13
    ".........OAuuuuuuuuuuAaO.......",  # 14: belt
    ".........OdduuuuuuuuuddO.......",  # 15
    "..........OUUU.....UUUO..........",  # 16: legs
    "..........OUUU.....UUUO..........",  # 17
    "..........OaUU.....UUaO..........",  # 18: knee pad area
    "..........OddU.....UddO..........",  # 19
    "..........OddU.....UddO..........",  # 20
    "..........OddU.....UddO..........",  # 21
    "..........OddU.....UddO..........",  # 22
    ".........OOddU.....UddOO.........",  # 23: boot tops
    ".........OdddU.....UdddO.........",  # 24
    ".........OdddU.....UdddO.........",  # 25
    "........OOddddO...OddddOO........",  # 26: soles
    "........OOOOOOO...OOOOOOO........",  # 27
    "................................",  # 28
    "................................",  # 29
    "................................",  # 30
    "................................",  # 31
]

sprite_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sprites_json')
os.makedirs(sprite_dir, exist_ok=True)
for name, rows in [("front_idle32", front), ("right_idle32", right), ("back_idle32", back)]:
    data = grid_to_json(rows)
    path = os.path.join(sprite_dir, f"{name}.json")
    with open(path, 'w') as f:
        json.dump(data, f, indent=1)
    print(f"{name}: {len(data['pixels'])} pixels")

# Left = mirror of right
left = [r[::-1] for r in right]
data = grid_to_json(left)
path = os.path.join(sprite_dir, "left_idle32.json")
with open(path, 'w') as f:
    json.dump(data, f, indent=1)
print(f"left_idle32: {len(data['pixels'])} pixels (mirror)")
print("Done!")
