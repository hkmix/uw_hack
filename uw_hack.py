import libtcodpy as libtcod
import math


class Object:
    ALIGN_ALLY = 0
    ALIGN_ENEMY = 1
    ALIGN_NEUTRAL = 2

    def __init__(self, x, y, name, char, colour, blocks, align, character=None, behaviour=None):
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.colour = colour
        self.blocks = blocks
        self.align = align
        if character:
            self.character = character
            self.character.owner = self
        if behaviour:
            self.behaviour = behaviour
            self.behaviour.owner = self


    def move(self, dx, dy):
        if not map[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy

    def draw(self):
        libtcod.console_set_default_foreground(buf, self.colour)
        libtcod.console_put_char(buf, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def distance_to(self, target):
        return math.sqrt((target.x - self.x) ** 2 + (target.y - self.x) ** 2)

    def move_towards(self, target):
        d_x = target.x - self.x
        d_y = target.y - self.y
        if d_x > 0:
            d_x /= abs(d_x)
        if d_y > 0:
            d_y /= abs(d_y)
        if d_x != 0 and d_y != 0:
            if libtcod.random_get_int(0, 0, 1) == 0:
                self.move(d_x, 0)
            else:
                self.move(0, d_y)
        else:
            self.move(d_x, d_y)


class Tile:
    def __init__(self, block, block_sight=None):
        self.blocked = block

        #Blocked tiles hinder sight
        if block_sight is None:
            block_sight = block
        self.block_sight = block_sight


class Msg(object):
    HIT_WALL = "You knowingly walk into a wall."
    DEAD = "The little engineer is no more."


class Character():
    def __init__(self, hp, atk, df, acc, avo, vis, col, xp, drop=None, death_func=None):
        self.hp = hp
        self.mhp = hp
        self.atk = atk
        self.df = df
        self.acc = acc
        self.avo = avo
        self.vis = vis
        self.col = col
        self.xp = xp
        if drop:
            self.drop = drop
        if death_func:
            self.death_func = death_func

    def take_dmg(self, damage):
        self.hp -= damage
        if self.hp > self.mhp:
            self.hp = self.mhp
        if self.hp <= 0:
            if self.death_func is not None:
                self.death_func(self.owner)

    def attack(self, target):
        max_dmg = Character.damage_formula(self.atk, target.character.df)
        does_hit = libtcod.random_get_int(0, 0, 100)
        if does_hit > self.acc:
            # Miss
            msg_add("The " + self.owner.name + " swings at the " + target.name + " and misses!")
        elif does_hit <= round(self.acc / 15):
            # Critical chance: ACC / 15
            dmg = libtcod.random_get_int(0, max_dmg, max_dmg * 2)
            msg_add("The " + self.owner.name + " brutally hits the " + target.name + " for " + str(dmg) + " damage!")
            target.character.take_dmg(dmg)
        else:
            # Regular hit
            dmg = libtcod.random_get_int(0, 0, max_dmg)
            msg_add("The " + self.owner.name + " hits the " + target.name + " for " + str(dmg) + "damage.")
            target.character.take_dmg(dmg)

    @staticmethod
    def damage_formula(atk, df):
        return round(max(atk - df) + atk / 4)


class Mons(object):
    # Formula: max(ATK - DEF) + ATK/4
    NAME = 0
    LVL = 1
    HP = 2
    ATK = 3
    DEF = 4
    ACC = 5
    AVO = 6
    CHAR = 7
    VIS = 8
    COL = 9
    EXP = 10
    DROP = 11

    M = \
        {
            'player': ['engineer', 0, 100, 9, 4, 90, 10, '@', 10, libtcod.Color(99, 95, 106), 0, None],
            't_zombie': ['zombie trainee', 1, 12, 3, 2, 30, 0, 'z', 5, libtcod.Color(110, 124, 110), 12, None],
            's_zombie': ['small zombie', 1, 15, 3, 3, 30, 0, 'z', 6, libtcod.Color(57, 72, 57), 15, None],
            'r_zombie': ['zombie', 1, 20, 4, 3, 40, 0, 'Z', 8, libtcod.Color(57, 72, 57), 20, None],
            'b_alien': ['unfriendly alien', 1, 10, 5, 1, 60, 5, 'a', 10, libtcod.Color(139, 124, 132), 15, None],
            'r_alien': ['xenophobic alien', 1, 15, 6, 2, 60, 10, 'A', 12, libtcod.Color(157, 140, 144), 22, None],
            'edcom': ['scary ED-COM', 2, 90, 12, 1, 40, 5, 'E', 7, libtcod.Color(129, 138, 128), 250, None],
            'x_zombie': ['X-formation zombies', 4, 120, 12, 1, 40, 5, 'X', 7, libtcod.Color(144, 250, 133), 250, None],
            'f_geese': ['flock of geese', 10, 200, 30, 20, 85, 20, 'G', 12, libtcod.Color(157, 140, 144), 22, None]
        }


class Monster():
    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(the_map, monster.x, monster.y):
            if monster.distance_to(player) > 1:
                monster.move_towards(player)
            else:
                monster.character.attack(player)


class MapGen(object):
    STAGE = [[]]

    @staticmethod
    def generate_map(width, height):
        new_map = libtcod.map_new(width, height)
        for x in range(width):
            for y in range(height):
                if MapGen.STAGE[y][x] == '#':
                    new_map[x][y].type = '#'
                    new_map[x][y].block = True
                    new_map[x][y].block_vision = True
                else:
                    new_map[x][y].type = ' '
                    new_map[x][y].block = False
                    new_map[x][y].block_vision = False
        return new_map


# Global constants
SCREEN_WIDTH = 116
SCREEN_HEIGHT = 40

MAP_WIDTH = 200
MAP_HEIGHT = 255

DIALOG_HEIGHT = 6

KBD_RPT_INIT_DELAY = 500
KBD_RPT_INTERVAL_DELAY = 100

STATE_PLAY = 0
STATE_WAIT = 1
STATE_DEAD = 2
STATE_EXIT = 99

MV_OKAY = 0
MV_OBJ = 1
MV_BLOCK = 2

P_X = 100
P_Y = 100

MSG_HISTORY_MAX = 100
M = Mons

# Global variables
global_state = STATE_PLAY
msg_history = []
objects = []

# Keys
KEY_UP = libtcod.KEY_UP
KEY_DOWN = libtcod.KEY_DOWN
KEY_LEFT = libtcod.KEY_LEFT
KEY_RIGHT = libtcod.KEY_RIGHT

# Colours
colour_wall = libtcod.Color(0, 0, 100)
colour_ground = libtcod.Color(50, 50, 150)


def msg_add(msg):
    if len(msg_history) >= MSG_HISTORY_MAX:
        del msg_history[0]
    msg_history.insert(0, msg)


def player_death(obj):
    msg_add(Msg.DEAD)
    objects.remove(obj)


def handle_keys():
    global global_state
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_ESCAPE:
        global_state = STATE_EXIT

    if global_state == STATE_PLAY:
        if libtcod.console_is_key_pressed(KEY_UP):
            player.move(0, -1)
        elif libtcod.console_is_key_pressed(KEY_DOWN):
            player.move(0, 1)
        elif libtcod.console_is_key_pressed(KEY_LEFT):
            player.move(-1, 0)
        elif libtcod.console_is_key_pressed(KEY_RIGHT):
            player.move(1, 0)
        else:
            global_state = STATE_WAIT


def make_map():
    global the_map
    the_map = MapGen.generate_map(MAP_WIDTH, MAP_HEIGHT)


def render_all():
    libtcod.console_clear(buf)
    # Map
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            wall = the_map[x][y].block_sight
            if wall:
                libtcod.console_set_char_background(buf, x, y, colour_wall, libtcod.BKGND_SET)
            else:
                libtcod.console_set_char_background(buf, x, y, colour_ground, libtcod.BKGND_SET)
    # Objects
    player.draw()
    libtcod.console_blit(buf, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)


libtcod.console_set_custom_font('terminal8x8_gs_ro.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'UW Hack', False)
libtcod.console_set_keyboard_repeat(KBD_RPT_INIT_DELAY, KBD_RPT_INTERVAL_DELAY)
buf = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

player_char = Character(M.M['player'][M.HP], M.M['player'][M.ATK], M.M['player'][M.DF], M.M['player'][M.ACC],
                        M.M['player'][M.AVO], M.M['player'][M.VIS], M.M['player'][M.COL], M.M['player'][M.EXP],
                        death_func=player_death)
player = Object(P_X, P_Y, M.M['player'][M.NAME], M.M['player'][M.CHAR], M.M['player'][M.COL], True, Object.ALIGN_ALLY,
                character=player_char)
objects.append(player)
make_map()

# Main loop
while not libtcod.console_is_window_closed():
    render_all()
    libtcod.console_flush()

    handle_keys()
    if global_state == STATE_EXIT:
        break