"""Design and save 32x32 player sprite base JSON files."""
import json, os

W, H = 32, 32

COLORS = {
    'O': '#0A0A0E', 'A': '#3A4045', 'a': '#505860', 'd': '#23282C',
    'U': '#16161A', 'V': '#00D9FF', 'X': '#FF6B00', 'W': '#FFFFFF',
    's': '#2A2F33',
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

front = [
    "..............OOOO..............",  # 0
    ".............OaaaaO..............",  # 1
    "............OaAAAAaO..............",  # 2
    "............OAAAAAAO.............",  # 3
    "............OAAVVVVAAO...........",  # 4 visor
    "............OAAVVVVAAO...........",  # 5 visor
    "............OAAAAAAAO............",  # 6
    ".............OAAAAAO.............",  # 7
    ".............OOssOO..............",  # 8 neck
    "........OaaAAAAAAAAAAaO..........",  # 9 pauldrons
    ".......OaaAAAAAAAAAAAAAAaO.......",  # 10
    ".......OaAAAXXXXXXXXAAAaO.......",  # 11 stripe
    ".......OaAAAXXXXXXXXAAAaO.......",  # 12 stripe
    ".......OAAAAAAAAAAAAAAAaO........",  # 13
    ".......OAUUUUUUUUUUUUAaO........",  # 14 belt
    ".......OOddUUUUUUUUUUddO........",  # 15
    ".......OaUUUUWWWWUUUUadO........",  # 16 rifle
    ".......OaUUUUWWWWUUUUadO........",  # 17 rifle
    "........OUUUU....UUUUO..........",  # 18 legs
    "........OUUUU....UUUUO..........",  # 19
    "........OaUUU....UUUaO..........",  # 20 knee
    "........OddU.....UddO...........",  # 21
    "........OddU.....UddO...........",  # 22
    "........OddU.....UddO...........",  # 23
    "........OddU.....UddO...........",  # 24
    ".......OOddU.....UddOO..........",  # 25 boot
    ".......OdddU.....UdddO..........",  # 26
    ".......OdddU.....UdddO..........",  # 27
    "......OOddddO...OddddOO.........",  # 28 sole
    "......OOOOOOO...OOOOOOO.........",  # 29
    "................................",  # 30
    "................................",  # 31
]

right = [
    "..............OOOO..............",  # 0
    ".............OaaAO...............",  # 1
    "............OAAAAO...............",  # 2
    "............OAAAAO...............",  # 3
    "............OAAAAVO..............",  # 4 visor right
    "............OAAAAVO..............",  # 5
    "............OAAAAO...............",  # 6
    ".............OAAAO...............",  # 7
    ".............OsAAO...............",  # 8 neck
    "..........OaaAAAAAaO.............",  # 9 pauldron
    ".........OaaAXXXXAAaO...........",  # 10 stripe
    ".........OaAAAAAAAaO............",  # 11
    ".........OAAAAAAAAaO............",  # 12
    ".........OAUUUUUUAaO.............",  # 13 belt
    ".........OddUUUUUddO.............",  # 14
    "..........OaUUUUUUaOWWWWWWWWW...",  # 15 rifle extends RIGHT
    "..........OaUUUUUUaO.WWWWWWWWW..",  # 16 rifle extends RIGHT
    ".........OaUUUUUUaO.............",  # 17 thigh
    ".........OaUUUUUUaO.............",  # 18
    ".........OddUUUUUaO.............",  # 19 knee
    ".........OddUUUUUddO............",  # 20
    ".........OddUUUUUddO............",  # 21
    ".........OddUUUUUddO............",  # 22
    ".........OddUUUUUddO............",  # 23
    ".........OddUUUUUddO............",  # 24
    "........OdddUUUUUddO.............",  # 25 boot
    "........OddddUUUUddO.............",  # 26
    "........OddddUUUUddO.............",  # 27
    ".......OOddddUUUdddO.............",  # 28 sole
    ".......OOOOOOOUUOOO..............",  # 29
    "................................",  # 30
    "................................",  # 31
]

back = [
    "..............OOOO..............",  # 0
    ".............OaaAO...............",  # 1
    "............OAAAAO...............",  # 2
    "............OAAAAO...............",  # 3 no visor
    "............OAAAAO...............",  # 4
    "............OAAAAO...............",  # 5
    "............OAAAAO...............",  # 6
    ".............OAAAO...............",  # 7
    ".............OsAAO...............",  # 8 neck
    "........OaaAAXXAAAAaO............",  # 9 backpack light
    ".......OaaAAAAAXXAAAaO..........",  # 10 backpack
    ".......OaAAAAAAAAAAAaO..........",  # 11
    ".......OaAAAAAAAAAAAaO..........",  # 12
    ".......OAAAAAAAAAAAAAaO.........",  # 13
    ".......OAUUUUUUUUUUUAaO.........",  # 14 belt
    ".......OOddUUUUUUUUUddO.........",  # 15
    "........OUUUU....UUUUO..........",  # 16 legs
    "........OUUUU....UUUUO..........",  # 17
    "........OaUUU....UUUaO..........",  # 18 knee
    "........OddU.....UddO...........",  # 19
    "........OddU.....UddO...........",  # 20
    "........OddU.....UddO...........",  # 21
    "........OddU.....UddO...........",  # 22
    ".......OOddU.....UddOO..........",  # 23 boot
    ".......OdddU.....UdddO..........",  # 24
    ".......OdddU.....UdddO..........",  # 25
    "......OOddddO...OddddOO.........",  # 26 sole
    "......OOOOOOO...OOOOOOO.........",  # 27
    "................................",  # 28
    "................................",  # 29
    "................................",  # 30
    "................................",  # 31
]

sprite_dir = r"C:\Users\sydne\xeno_shooter\sprites_json"
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
