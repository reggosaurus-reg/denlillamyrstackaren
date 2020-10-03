from ribs import *
from dataclasses import dataclass

# Asset dictionary for holding all your assets.
assets = {}


def clamp(val, low, high):
    return min(max(val, low), high)


@dataclass
class Player:
    centerx = 0
    centery = 0
    width = 40
    height = 40

    velocity = (0, 0)

    walk_acc = 1000.0
    max_walk_speed = 100
    slow_down = 0.01


def update_player(player, delta):
    (left, right) = (key_down("a") or key_down(pg.K_RIGHT),
                     key_down("d") or key_down(pg.K_LEFT))

    if left and not right:
        player.velocity = (player.velocity[0] + player.walk_acc * delta,
                           player.velocity[1])
    elif right and not left:
        player.velocity = (player.velocity[0] - player.walk_acc * delta,
                           player.velocity[1])
    else:
        # Yes, this is supposed to be an exponent.
        player.velocity = (player.velocity[0] * (player.slow_down ** delta),
                           player.velocity[1])

    # Gravity
    player.velocity = (player.velocity[0], player.velocity[1] + 100 * delta)

    max_speed = player.max_walk_speed
    clamped_horizontal_speed = clamp(player.velocity[0], -max_speed, max_speed)
    player.velocity = (clamped_horizontal_speed, player.velocity[1])

    player.centerx += player.velocity[0] * delta
    player.centery += player.velocity[1] * delta


def draw_player(player):
    window = pg.display.get_surface()
    draw_transformed(assets["myra"], (player.centerx, player.centery), (0.1, 0.1))


levels = [
"""
##########
#        #
#        #
#        #
# S B  E #
##########
""",
"""
##########
#        #
# S      #
####     #
####   E #
##########
""",
"""
##########
#      S #
####     #
##       #
##E      #
##########
""",
]


def parse_level(level_string):
    GRID_SIZE = 40

    walls = []
    goals = []
    barrs = []
    start = None

    level_lines = level_string.strip().split("\n")
    for tile_y, line in enumerate(level_lines):
        y = tile_y * GRID_SIZE
        for tile_x, c in enumerate(line):
            x = tile_x * GRID_SIZE
            r = pg.Rect(x, y, GRID_SIZE, GRID_SIZE)
            if c == "#":
                # It's a wall
                walls.append(r)
            elif c == "E":
                # It's a goal
                goals.append(r)
            elif c == "B":
                # It's a Barr
                k = (r[0], r[1]+GRID_SIZE*0.85, r[2], r[3])
                barrs.append(k)
            elif c == "S":
                # It's the start
                start = (x, y)

    return walls, goals, start, barrs


def init():
    """ A function for loading all your assets.
        (Audio assets can at their earliest be loaded here.)
    """
    # Load images here
    assets["teapot"] = pg.image.load("res/teapot.png")
    
    assets["barr"] = pg.image.load("res/barr.png")

    assets["myra"] = pg.image.load("res/myra.png")

    # Load sounds here
    assets["plong"] = pg.mixer.Sound("res/plong.wav")


current_level = 0
def update():
    """The program starts here"""
    global current_level
    # Initialization (only runs on start/restart)
    player = Player()

    walls, goals, start, barrs = parse_level(levels[current_level])
    player.centerx = start[0]
    player.centery = start[1]

    # Main update loop
    while True:
        clear_screen(pg.Color(170, 180, 255))
        update_player(player, delta())
        draw_player(player)

        for wall in walls:
            window = pg.display.get_surface()
            pg.draw.rect(window, pg.Color(100, 100, 100), wall)

            player_vel, wall_vel, overlap = solve_rect_overlap(player,
                                                               wall,
                                                               player.velocity,
                                                               mass_b=0,
                                                               bounce=0.1)
            player.velocity = player_vel

        for barr in barrs:
            window = pg.display.get_surface()
            draw_transformed(assets["barr"], barr, (0.1, 0.1))


        for goal in goals:
            window = pg.display.get_surface()
            pg.draw.rect(window, pg.Color(20, 100, 20), goal)

            normal, depth = overlap_data(player, goal)
            if depth > 0:
                current_level = (current_level + 1) % len(levels)
                restart()

        draw_text(f"Level: {current_level + 1}", (0, 0))

        # Main loop ends here, put your code above this line
        yield


# This has to be at the bottom, because of python reasons.
if __name__ == "__main__":
   start_game(init, update)
