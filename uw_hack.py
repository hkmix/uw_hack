import libtcodpy as libtcod
from map import Map
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
        if not the_map[self.x + dx][self.y + dy].block:
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
    def __init__(self, block, block_vision=None):
        self.block = block
        self.seen = False
        #Blocked tiles hinder sight
        if block_vision is None:
            block_vision = block
        self.block_vision = block_vision


class Msg(object):
    HIT_WALL = "You knowingly walk into a wall. What are you thinking?!"
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
            'player': ['engineer', 0, 100, 9, 4, 90, 10, '@', 10, libtcod.white, 0, None],
            't_zombie': ['zombie trainee', 1, 12, 3, 2, 30, 0, 'z', 5, libtcod.Color(110, 124, 110), 12, None],
            's_zombie': ['small zombie', 1, 15, 3, 3, 30, 0, 'z', 6, libtcod.Color(57, 72, 57), 15, None],
            'r_zombie': ['zombie', 1, 20, 4, 3, 40, 0, 'Z', 8, libtcod.Color(57, 72, 57), 20, None],
            'b_alien': ['unfriendly alien', 1, 10, 5, 1, 60, 5, 'a', 10, libtcod.Color(139, 124, 132), 15, None],
            'r_alien': ['xenophobic alien', 1, 15, 6, 2, 60, 10, 'A', 12, libtcod.Color(157, 140, 144), 22, None],
            'edcom': ['scary ED-COM', 2, 90, 12, 1, 40, 5, 'E', 7, libtcod.Color(129, 138, 128), 250, None],
            'x_zombie': ['X-formation zombies', 4, 120, 12, 1, 40, 5, 'X', 7, libtcod.Color(144, 250, 133), 250, None],
            'f_geese': ['flock of geese', 10, 200, 30, 20, 85, 20, 'G', 12, libtcod.Color(157, 140, 144), 22, None]
        }


class Monster(object):
    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(the_map, monster.x, monster.y):
            if monster.distance_to(player) > 1:
                monster.move_towards(player)
            else:
                monster.character.attack(player)


class MapGen(object):
    @staticmethod
    def generate_map(width, height):
        new_map = [[Tile(False) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]
        for x in range(width):
            for y in range(height):
                if Map.MAP[y][x] == '#':
                    new_map[x][y].gnd = '#'
                    new_map[x][y].block = True
                    new_map[x][y].block_vision = True
                else:
                    new_map[x][y].gnd = ' '
                    new_map[x][y].block = False
                    new_map[x][y].block_vision = False
        return new_map


# Global constants
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 54

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

P_X = 10
P_Y = 10

FOV_LIGHT_WALLS = True
FOV_ALG = 0

MSG_HISTORY_MAX = 100
MSG_DISPLAY = 8

HP_THRESHOLD_GOOD = 0.8
HP_THRESHOLD_OKAY = 0.3

M = Mons

# Global variables
global_state = STATE_PLAY
msg_history = []
objects = []
p_fov_recalc = True
p_vision = M.M['player'][M.VIS]
p_turn = 0
p_time = 0

# Keys
KEY_UP = libtcod.KEY_UP
KEY_DOWN = libtcod.KEY_DOWN
KEY_LEFT = libtcod.KEY_LEFT
KEY_RIGHT = libtcod.KEY_RIGHT

# Colours
colour_default = libtcod.white
colour_wall_dark = libtcod.black
colour_wall_seen = libtcod.Color(66, 69, 77)
colour_wall_bright = libtcod.Color(125, 129, 136)
colour_ground_dark = libtcod.black
colour_ground_seen = libtcod.Color(21, 26, 36)
colour_ground_bright = libtcod.Color(33, 35, 40)
colour_hp_good = libtcod.Color(102, 255, 51)
colour_hp_okay = libtcod.Color(255, 204, 51)
colour_hp_bad = libtcod.Color(255, 51, 102)


def legal_move(x, y):
    if the_map[x][y].block or x >= MAP_WIDTH or x < 0 or y >= MAP_HEIGHT or y < 0:
        return MV_BLOCK
    for obj in objects:
        if obj.x == x and obj.y == y and obj.blocks:
            return MV_OBJ
    return MV_OKAY


def msg_add(msg):
    if msg == "":
        return
    if len(msg_history) >= MSG_HISTORY_MAX:
        del msg_history[0]
    msg_history.insert(0, msg)


def player_death(obj):
    global global_state
    global_state = STATE_DEAD
    msg_add(Msg.DEAD)
    objects.remove(obj)


def player_move(d_x, d_y):
    if d_x != 0 or d_y != 0:
        global global_state
        global_state = STATE_PLAY
        move_result = legal_move(player.x + d_x, player.y + d_y)
        target = None
        if move_result == MV_OKAY:
            player.move(d_x, d_y)
            global p_fov_recalc
            p_fov_recalc = True
        elif move_result == MV_OBJ:
            for obj in objects:
                if obj.x == player.x + d_x and obj.y == player.y + d_y:
                    target = obj
                    break
        else:
            msg_add(Msg.HIT_WALL)
        if (not target is None) and target.align == Object.ALIGN_ENEMY:
            player.character.attack(target)
    handle_enemies()
    global p_turn, p_time
    p_turn += 1
    p_time += 1


def handle_keys():
    global global_state
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_ESCAPE:
        return STATE_EXIT
    if global_state == STATE_PLAY:
        if libtcod.console_is_key_pressed(KEY_UP):
            player_move(0, -1)
        elif libtcod.console_is_key_pressed(KEY_DOWN):
            player_move(0, 1)
        elif libtcod.console_is_key_pressed(KEY_LEFT):
            player_move(-1, 0)
        elif libtcod.console_is_key_pressed(KEY_RIGHT):
            player_move(1, 0)
        else:
            return STATE_WAIT


def make_map():
    global the_map, fov_map
    the_map = MapGen.generate_map(MAP_WIDTH, MAP_HEIGHT)
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            libtcod.map_set_properties(fov_map, x, y, not the_map[x][y].block_vision, not the_map[x][y].block)
    libtcod.map_compute_fov(fov_map, player.x, player.y, p_vision, FOV_LIGHT_WALLS, FOV_ALG)


def handle_enemies():
    for obj in objects:
        if obj.align == Object.ALIGN_ENEMY:
            if obj.ai:
                obj.ai.take_turn()


def get_colour_hp():
    if player.character.hp / player.character.mhp > HP_THRESHOLD_GOOD:
        return colour_hp_good
    elif player.character.hp / player.character.mhp > HP_THRESHOLD_OKAY:
        return colour_hp_okay
    else:
        return colour_hp_bad


def render_all():
    libtcod.console_clear(buf)
    # FOV
    global p_fov_recalc
    if p_fov_recalc:
        p_fov_recalc = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, p_vision, FOV_LIGHT_WALLS, FOV_ALG)
    # Map
    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            if libtcod.map_is_in_fov(fov_map, x, y):
                if the_map[x][y].block_vision:
                    libtcod.console_set_char_background(buf, x, y, colour_wall_bright, libtcod.BKGND_SET)
                    the_map[x][y].seen = True
                else:
                    libtcod.console_set_char_background(buf, x, y, colour_ground_bright, libtcod.BKGND_SET)
                    the_map[x][y].seen = True
            elif the_map[x][y].seen:
                if the_map[x][y].block_vision:
                    libtcod.console_set_char_background(buf, x, y, colour_wall_seen, libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(buf, x, y, colour_ground_seen, libtcod.BKGND_SET)
            else:
                if the_map[x][y].block_vision:
                    libtcod.console_set_char_background(buf, x, y, colour_wall_dark, libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(buf, x, y, colour_ground_dark, libtcod.BKGND_SET)
    # Objects
    if global_state == STATE_PLAY:
        global objects
        objects.remove(player)
        objects.insert(0, player)
    for obj in objects:
        if libtcod.map_is_in_fov(fov_map, obj.x, obj.y):
            obj.draw()
    # Messages
    for i in range(MSG_DISPLAY):
        if i >= len(msg_history):
            break
        libtcod.console_set_default_foreground(msg, libtcod.Color(255-255/MSG_DISPLAY*i,
                                                                  255-255/MSG_DISPLAY*i,
                                                                  255-255/MSG_DISPLAY*i))
        libtcod.console_print(msg, 0, i, msg_history[i])
    # HUD
    libtcod.console_set_default_foreground(msg, colour_default)
    libtcod.console_print(msg, 0, SCREEN_HEIGHT - 2, "HP ")
    libtcod.console_set_default_foreground(msg, get_colour_hp())
    libtcod.console_print(msg, 3, SCREEN_HEIGHT - 2, str(player.character.hp))
    libtcod.console_set_default_foreground(msg, colour_default)
    libtcod.console_print(msg, 3 + len(str(player.character.hp)), SCREEN_HEIGHT - 2, "/" + str(player.character.mhp))
    libtcod.console_print(msg, 0, SCREEN_HEIGHT - 1, "Turn " + str(p_turn))
    # Draw
    libtcod.console_blit(blank, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
    libtcod.console_blit(buf, player.x - SCREEN_WIDTH/2, player.y - SCREEN_HEIGHT/2, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
    libtcod.console_blit(msg, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0, 1, 0)


libtcod.console_set_custom_font("terminal8x8_gs_ro.png", libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, "UW @ ENGHack 2014", False)
libtcod.console_set_keyboard_repeat(KBD_RPT_INIT_DELAY, KBD_RPT_INTERVAL_DELAY)
buf = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
blank = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
msg = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

player_char = Character(M.M['player'][M.HP], M.M['player'][M.ATK], M.M['player'][M.DEF], M.M['player'][M.ACC],
                        M.M['player'][M.AVO], M.M['player'][M.VIS], M.M['player'][M.COL], M.M['player'][M.EXP],
                        death_func=player_death)
player = Object(P_X, P_Y, M.M['player'][M.NAME], M.M['player'][M.CHAR], M.M['player'][M.COL], True, Object.ALIGN_ALLY,
                character=player_char)
objects.append(player)
make_map()

# Main loop
while not libtcod.console_is_window_closed():
    # Output
    render_all()
    libtcod.console_flush()
    # Input
    do_exit = handle_keys()
    # Processing
    if do_exit == STATE_EXIT:
        break
    elif do_exit == STATE_PLAY:
        handle_enemies()