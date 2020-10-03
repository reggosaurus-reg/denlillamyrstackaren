#
# The offical LiTHe kod code skeleton for PyGame development.
# 2020 by Edvard Thörnros
#
# The aim of this file is to give a collection of usable functions
# and structures to be used as a jumping off point. Feel free
# to change and distribute!
#
# Functions that start with an underscore, are probably not
# interesting to read, they are functions that build other
# more usable functions.
#
# Then again, the implementations in this file are not nessecary
# for understanding how to use them. There's some nice documentation
# if you'd rather read that! :D
#

import pygame as pg
# For smaller cheat sheet see:
#   https://www.lithekod.se/pygame.html
# For official pygame documentation see:
#   https://www.pygame.org/docs/

# math has sin, cos and other interesting things.
import math

#
# Input handling
#

def _event_is(event: pg.event, kind: str) -> bool:
    """Internal function to check the kind of pygame event"""
    return pg.event.event_name(event.type) == kind


current_frame_held_buttons = set()
last_frame_held_buttons = None
def process_events():
    """Tells the game what buttons are pressed."""
    running = True
    global last_frame_held_buttons
    last_frame_held_buttons = current_frame_held_buttons.copy()
    for event in pg.event.get():
        if _event_is(event, "Quit"):
            running = False
        elif _event_is(event, "KeyDown"):
            current_frame_held_buttons.add(event.key)
        elif _event_is(event, "KeyUp"):
            if event.key in current_frame_held_buttons:
                current_frame_held_buttons.remove(event.key)
    return running


def _to_keycode(key):
    """
        Takes a keycode or a character and converts it to a keycode

        A keycode is a number that uniquely identifies a keyboard key.
        And a character is what you get when typing that key on the keyboard.
    """
    if type(key) == str:
        if len(key) != 1:
            raise "error"
        return ord(key.lower())
    return key


def key_down(key):
    """
        Takes a key, that's either a keycode or a character,
        returns True if the corresponding key is pressed.
    """
    keycode = _to_keycode(key)
    return keycode in current_frame_held_buttons


def key_released(key):
    """
        Takes a key, that's either a keycode or a character,
        and says if it was released this frame.
    """
    keycode = _to_keycode(key)
    return (keycode not in current_frame_held_buttons) and \
           (keycode in last_frame_held_buttons)


def key_pressed(key):
    """
        Takes a key, that's either a keycode or a character,
        and says if it was pressed down this frame.
    """
    keycode = _to_keycode(key)
    return (keycode in current_frame_held_buttons) and \
           (keycode not in last_frame_held_buttons)


#
# Simple sprite drawing
#

def draw_transformed(img, position, scale=(1., 1.), degrees=0):
    """
        Draw img centered at position, scale the image and then rotate it in
        degrees before drawing.
    """
    if scale[0] != 1. or scale[1] != 1.:
        w, h = img.get_size()
        w = int(w * scale[0])
        h = int(h * scale[1])
        img = pg.transform.scale(img, (w, h))
    if degrees:
        # Pygame rotates CCW in degrees, for some reason.
        img = pg.transform.rotate(img, -degrees)
    w, h = img.get_size()
    window = pg.display.get_surface()
    window.blit(img, (int(position[0] - w / 2.0), int(position[1] - h / 2.0)))


def clear_screen(color):
    """Fill the screen with color"""
    window = pg.display.get_surface()
    top_left = (0, 0)
    bottom_right = pg.display.get_surface().get_size()
    pg.draw.rect(window, color, (top_left, bottom_right))

#
# Text drawing
#

LOADED_FONTS = {}
def draw_text(text, position, size=32, color=pg.Color(255, 255, 255), font=None):
    """
        Draw text at given position.
        The position is in pixels from the top left of the window.
        Optional arguments include size, color and font.
    """
    global LOADED_FONTS

    # Keep used fonts in memory.
    # This is not a good solution if many different font sizes are used,
    # but i cannot find a better way to do it...
    if (font, size) not in LOADED_FONTS:
        if len(LOADED_FONTS) > 100:
            LOADED_FONTS.popitem()
        LOADED_FONTS[(font, size)] = pg.font.SysFont(font, size)

    font_obj = LOADED_FONTS[(font, size)]

    rendered_text = font_obj.render(text, True, color)

    window = pg.display.get_surface()
    window.blit(rendered_text, position)

#
# Simple physics and collision
#

def overlap_data(a, b):
    """
        Given that a and b overlap, extracts the shortest direction to move
        along and the penetration.

        returns -> normal, depth
        (normal points from a)
    """
    # This code is based on SAT (the shortest distance is along one normal).
    delta = a.centerx - b.centerx, a.centery - b.centery
    span = (a.width + b.width) / 2, (a.height + b.height) / 2

    # Pick the smallest overlapping axis
    overlap = span[0] - abs(delta[0]), span[1] - abs(delta[1])
    depth = min(overlap)

    # Inline helper
    sign = lambda x: 1 if x > 0 else -1

    if abs(overlap[0]) < abs(overlap[1]):
        normal = sign(delta[0]), 0
    else:
        normal = 0, sign(delta[1])

    return normal, depth


def solve_rect_overlap(a, b, vel_a=(0, 0), vel_b=(0, 0), mass_a=1, mass_b=1, bounce=1):
    """
        Solves the collision between a and b, with the mass and velocity as specified.
        A solved collision has no overlap and velocities that do not point into eachother.

        vel  - is the velocity of the body, a direction and a speed.
        mass - is how much each body weighs, if set to 0 they cannot move.
        bounce - is how bouncy the collision is. (For "correct" behaviour > 0.0, < 1.0)
    """
    dot = lambda v, u: v[0] * u[0] + v[1] * u[1]
    add = lambda v, u: (v[0] + u[0], v[1] + u[1])
    scale = lambda v, s: (v[0] * s, v[1] * s)

    normal, depth = overlap_data(a, b)
    if depth < 0: return vel_a, vel_b, False

    # Positional correction
    total_mass = mass_a + mass_b
    if total_mass != 0:
        effect_a = mass_a / total_mass
        a.centerx = a.centerx + normal[0] * depth * effect_a
        a.centery = a.centery + normal[1] * depth * effect_a

        effect_b = mass_b / total_mass
        b.centerx = b.centerx - normal[0] * depth * effect_b
        b.centery = b.centery - normal[1] * depth * effect_b

    # Velocity correction
    relative_v = (1 + bounce) * (dot(vel_a, normal) - dot(vel_b, normal))
    if total_mass != 0 and relative_v < 0:
        vel_a = add(vel_a, scale(normal, -relative_v * mass_a / total_mass))
        vel_b = add(vel_b, scale(normal,  relative_v * mass_b / total_mass))

    return vel_a, vel_b, True


def damping(vel, damp=0.1):
    """Slows down an object by damp factor per second."""
    fac = damp ** DELTA
    return vel[0] * fac, vel[1] * fac

#
# Main loop
# (with global state needed for code to work)
#


UPDATE_FUNC = None
UPDATE_ITER = None

FRAMERATE = 60
DELTA = 1 / FRAMERATE
TIME = 0
FRAME_CLOCK = pg.time.Clock()

PYGAME_INITALIZED = False

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500


def set_screen_size(width, height):
    """Sets the screen size of the game to width and height passed in."""
    global SCREEN_WIDTH, SCREEN_HEIGHT, PYGAME_INITALIZED
    SCREEN_WIDTH = width
    SCREEN_HEIGHT = height
    if PYGAME_INITALIZED:
        pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


def set_frame_rate(fps):
    """Sets the framerate of the game to the given FPS."""
    global FRAMERATE, DELTA
    FRAMERATE = fps
    DELTA = 1 / FRAMERATE


def time():
    """Return the time since the program started."""
    return TIME


def delta():
    """Return the time passed from the previous frame to this frame."""
    if FRAMERATE:
        return DELTA
    # I know this looks wierd, but "get_time" returns the "delta",
    # really wierd.
    return FRAME_CLOCK.get_time() / 1000.0


def restart():
    """Reruns the initalization code of the game"""
    global UPDATE_FUNC, UPDATE_ITER, TIME
    UPDATE_ITER = UPDATE_FUNC()
    TIME = 0


def start_game(init, update):
    """The program starts here"""
    pg.init()
    pg.display.init()
    pg.mixer.init()

    global PYGAME_INITALIZED
    PYGAME_INITALIZED = True

    global FRAME_CLOCK
    FRAME_CLOCK = pg.time.Clock()

    # Let you do initalization
    init()

    # Sets the screen resolution.
    set_screen_size(SCREEN_WIDTH, SCREEN_HEIGHT)

    global UPDATE_FUNC, TIME
    UPDATE_FUNC = update
    # First start is a restart.
    restart()

    # See what buttons are pressed this frame, and continue if we haven't quit.
    while process_events():
        # Tell Pygame we're on a new frame, with the given framerate
        # set it to zero to unlimit.
        FRAME_CLOCK.tick(FRAMERATE)
        TIME += DELTA

        # Let you do what you need to do.
        try:
            next(UPDATE_ITER)
        except StopIteration:
            break

        # Update the display
        pg.display.flip()
        clear_screen(pg.Color(0, 0, 0))

    pg.mixer.quit()
    pg.display.quit()
    pg.quit()

