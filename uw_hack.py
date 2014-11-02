import libtcodpy as libtcod
from map import Map
from signs import Signs
import math
import sys


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
        if legal_move(self.x + dx, self.y + dy) == MV_OKAY:
            self.x += dx
            self.y += dy

    def draw(self):
        libtcod.console_set_default_foreground(buf, self.colour)
        libtcod.console_put_char(buf, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def distance_to(self, target):
        return math.sqrt((target.x - self.x) ** 2 + (target.y - self.y) ** 2)

    def distance_to_coord(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move_towards(self, target):
        d_x = target.x - self.x
        d_y = target.y - self.y
        if d_x != 0:
            d_x /= abs(d_x)
        if d_y != 0:
            d_y /= abs(d_y)
        if d_x != 0 and d_y != 0:
            if libtcod.random_get_int(0, 0, 1) == 0:
                self.move(d_x, 0)
            else:
                self.move(0, d_y)
        else:
            self.move(d_x, d_y)


class Tile:
    def __init__(self, block, block_vision=None, gnd=None):
        self.block = block
        self.seen = False
        if block_vision:
            self.block_vision = block_vision
        if gnd:
            self.gnd = gnd


class Msg(object):
    HIT_WALL = "You knowingly walk into a wall. What are you thinking?!"
    HIT_EDGE = "Whoa, that's the edge of the world!"
    HIT_LAURIER = "Whoa, you are not a Laurier student!"
    NO_PICKUP = "You pick up mere air."
    DEAD = "The little engineer is no more."
    WATER = "The dihydrogen monoxide plays games with your lungs!"
    NO_ARMOUR = "Bare skin"
    NO_WEAPON = "Fists"
    ITM_SLEEP = "You finally get some sleep."
    ITM_VISION = "You gain vision."
    SPAWN_ECE = "It is now time for the ECE 105 midterm."
    SPAWN_COOP = "Hey look! A job interview!"
    SPAWN_FGEESE = "It's mating season!"
    SPAWN_TRAINS = "This was the wrong course to take."
    SPAWN_SCRIBBLER = "You never thought you'd see this guy again."
    SPAWN_IRONRING = "Five years later..."
    SPAWN_DATE = "Can't believe that pick-up line worked!"
    SPAWN_HEADCOM = "This is it! Go get the Tool!"
    TRAIN = "Choo choo!"


class Character():
    def __init__(self, hp, atk, df, acc, avo, vis, col, xp, rate, drop=None, death_func=None, speedy=False):
        self.hp = hp
        self.mhp = hp
        self.atk = atk
        self.df = df
        self.acc = acc
        self.avo = avo
        self.vis = vis
        self.col = col
        self.xp = xp
        self.rate = rate
        if drop:
            self.drop = drop
        if death_func:
            self.death_func = death_func
        if speedy:
            self.speedy = True

    def take_dmg(self, damage):
        self.hp -= damage
        if self.hp > self.mhp:
            self.hp = self.mhp
        if self.hp <= 0:
            if self.death_func is not None:
                self.death_func(self.owner)

    def attack(self, target):
        max_dmg = int(Character.damage_formula(self.atk, target.character.df))
        does_hit = libtcod.random_get_int(0, 0, 100)
        if does_hit > self.acc - target.character.avo:
            # Miss
            msg_add("The " + self.owner.name + " misses the " + target.name + "!")
        elif does_hit <= round((self.acc - target.character.avo) / 15):
            # Critical chance: ACC / 15
            dmg = max(libtcod.random_get_int(0, max_dmg, max_dmg * 2), 0)
            if target.name == M.M['edcom'][M.NAME]:
                msg_add("The " + self.owner.name + " seriously respects the " + target.name + " and is granted " + str(dmg) + " damage.")
            elif target.align == Object.ALIGN_ENEMY and has_weapon:
                msg_add("The " + self.owner.name + " brutally " + p_weapon.verb + " the " + target.name + " for " + str(dmg) + " damage!")
            else:
                msg_add("The " + self.owner.name + " brutally hits the " + target.name + " for " + str(dmg) + " damage!")
            target.character.take_dmg(dmg)
        else:
            # Regular hit
            dmg = max(libtcod.random_get_int(0, 0, max_dmg), 0)
            if target.name == M.M['edcom'][M.NAME]:
                msg_add("The " + self.owner.name + " respects the " + target.name + " and is granted " + str(dmg) + " damage.")
            elif target.align == Object.ALIGN_ENEMY and has_weapon:
                msg_add("The " + self.owner.name + " " + p_weapon.verb + " the " + target.name + " for " + str(dmg) + " damage!")
            else:
                msg_add("The " + self.owner.name + " hits the " + target.name + " for " + str(dmg) + " damage.")
            target.character.take_dmg(dmg)

    @staticmethod
    def damage_formula(atk, df):
        return round(max(atk - df, 1) + atk / 4)


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
    RATE = 12
    SPD = 13

    M = \
        {
            # Monsters
            'player': ['engineer', 999, 120, 9, 5, 90, 10, libtcod.CHAR_SMILIE, 20, libtcod.white, 0, None, 0, False],
            't_zombie': ['zombie trainee', 1, 12, 3, 2, 30, 0, 'z', 7, libtcod.Color(170, 184, 170), 15, 'o_shirt', 5, False],
            's_zombie': ['zombie', 1, 15, 3, 3, 30, 0, 'z', 6, libtcod.Color(127, 142, 127), 17,  'o_shirt', 5, False],
            'r_zombie': ['expert zombie', 1, 20, 4, 3, 40, 0, 'Z', 10, libtcod.Color(127, 142, 127), 19,  'o_shirt', 8, False],
            'b_alien': ['unfriendly alien', 1, 10, 5, 1, 60, 5, 'a', 15, libtcod.Color(189, 174, 182), 15, 'mtool', 6, False],
            'r_alien': ['xenophobic alien', 1, 15, 6, 2, 60, 10, 'A', 16, libtcod.Color(187, 180, 184), 20, 'mtool', 8, False],
            'edcom': ['scary ED-COM', 2, 75, 12, 1, 40, 5, 'E', 99, libtcod.Color(169, 178, 168), 99, 'mtool', 20, False],
            'goose': ['goose', 2, 10, 15, 0, 90, 15, 'g', 15, libtcod.white, 25, 'feather', 99, True],
            'assig': ['complicated assignment', 2, 60, 9, 8, 85, 25, libtcod.CHAR_DIVISION, 15, libtcod.Color(255, 235, 137), 50, 'sleep', 80, False],
            'alarm': ['dreaded alarm', 2, 50, 10, 10, 80, 35, libtcod.CHAR_EXCLAM_DOUBLE, 15, libtcod.Color(255, 178, 137), 60, 'sleep', 80, False],
            'phys_ta': ['teaching assistant', 3, 55, 14, 10, 80, 10, 'T', 99, libtcod.Color(195, 130, 231), 75, 'answers', 10, False],
            'angry': ['angry roommate', 3, 65, 18, 7, 90, 15, 'R', 99, libtcod.Color(245, 34, 23), 90, 'keys', 10, False],
            'ece_return': ['hallucinated ECE 105 midterm', 3, 20, 35, 2, 80, 0, 'x', 12, libtcod.Color(249, 41, 82), 110, 'deflation', 90, False],
            'thief': ['bike thief', 4, 70, 17, 23, 80, 15, 't', 99, libtcod.Color(249, 41, 82), 140, 'bicycle', 5, True],
            'laurier': ['Laurier student', 4, 75, 22, 21, 70, 10, 'L', 99, libtcod.Color(255, 215, 0), 165, 'pride', 5, False],
            'don': ['duty don', 4, 100, 7, 22, 80, 25, 'D', 99, libtcod.Color(61, 226, 0), 180, None, 0, False],
            # Bosses
            'ece': ['ECE 105 midterm', 99, 120, 15, 0, 90, 0, 'X', 99, libtcod.Color(249, 41, 82), 300, 'bell', 100, False],
            'scribbler': ['Scribbler Bot', 99, 200, 4, 40, 50, 0, 'S', 5, libtcod.Color(231, 0, 17), 450, 'fluke', 100, True],
            'coop': ['first co-op interview', 99, 80, 25, 0, 50, 15, 'C', 99, libtcod.Color(255, 193, 43), 600, 'job', 100, False],
            'f_geese': ['flock of geese', 99, 180, 35, 5, 85, 20, 'G', 99, libtcod.white, 700, 'babygoose', 100, True],
            'date': ['first date (ever)', 99, 250, 25, 25, 90, 20, 'D', 99, libtcod.Color(234, 63, 174), 850, 'peck', 100, True],
            'trains': ['real-time trains course', 99, 400, 30, 25, 85, 15, 'T', 99, libtcod.Color(113, 150, 236), 1200, 'vision', 100, False],
            'ironring': ['Iron Ring Ceremony', 99, 300, 30, 45, 85, 5, 'O', 99, libtcod.Color(192, 198, 175), 1800, 'iring', 100, False],
            'headcom': ['HEADCOM', 99, 500, 50, 40, 90, 15, 'H', 99, libtcod.white, 5000, 'tool', 100, False],
            'dragon': ['twenty-headed dragon', 99, 999, 99, 99, 100, 25, libtcod.CHAR_DIAMOND, 99, libtcod.white, 5000, None, 0, True]
        }


class Items(object):
    NAME = 0
    HP = 1
    ATK = 2
    DEF = 3
    ACC = 4
    AVO = 5
    TYPE = 6
    VERB = 7
    CHAR = 8
    COL = 9

    TYPE_WEAPON = 0
    TYPE_ARMOUR = 1
    TYPE_INSTANT = 2

    I = \
        {
            'o_shirt': ['light-red orientation shirt', 5, 0, 1, 0, 2, TYPE_ARMOUR, "", '[', libtcod.Color(255, 90, 90)],
            'bell': ['bell curve', 20, -5, 6, 0, 15, TYPE_ARMOUR, "", '[', libtcod.Color(255, 90, 90)],
            'mtool': ['somewhat functional multitool', 0, 1, 0, 5, 0, TYPE_WEAPON, "weakly prods", ')', libtcod.Color(255, 217, 0)],
            'sleep': ['good night\'s rest', 20, 0, 0, 0, 0, TYPE_INSTANT, "", '!', libtcod.Color(242, 101, 190)],
            'feather': ['feather', 0, 1, 0, -20, 0, TYPE_WEAPON, "tickles", ')', libtcod.white],
            'fluke': ['Fluke module', 0, 8, 8, -50, 10, TYPE_WEAPON, "poorly scans", libtcod.CHAR_BLOCK2, libtcod.Color(62, 232, 107)],
            'babygoose': ['baby goose', 0, 10, -3, 10, 10, TYPE_WEAPON, "squawks at", ')', libtcod.white],
            'answers': ['answer sheet', 0, 1, 1, 20, 20, TYPE_WEAPON, "examines", '?', libtcod.Color(195, 130, 231)],
            'job': ['mediocre job', 10, 3, 5, 0, 10, TYPE_ARMOUR, "", '[', libtcod.Color(255, 193, 43)],
            'keys': ['set of stolen keys', 0, 6, 0, 10, 10, TYPE_WEAPON, "keys", ')', libtcod.Color(252, 136, 55)],
            'deflation': ['case of grade deflation', -15, -15, -15, -50, 60, TYPE_ARMOUR, "", '[', libtcod.Color(255, 90, 90)],
            'bicycle': ['"second-hand" bicycle', 20, 5, 15, 0, 20, TYPE_WEAPON, "rides circles around", '[', libtcod.Color(137, 161, 232)],
            'pride': ['sense of pride', 20, 9, 9, 15, 15, TYPE_ARMOUR, "", '[', libtcod.Color(255, 215, 0)],
            'peck': ['peck on the cheek', 40, 5, 10, 10, 10, TYPE_WEAPON, "blushes at", libtcod.CHAR_HEART, libtcod.Color(234, 63, 174)],
            'vision': ['sense of vision', 150, 0, 0, 0, 0, TYPE_INSTANT, "", '!', libtcod.Color(255, 211, 0)],
            'iring': ['iron ring', 40, 0, 20, 20, -20, TYPE_ARMOUR, "", 'o', libtcod.Color(192, 198, 175)],
            'tool': ['Ridgid 60"', 250, 120, 120, 50, 50, TYPE_WEAPON, "brings divine justice on", '|', libtcod.Color(192, 192, 192)]
        }


class Monster(object):
    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            if monster.distance_to(player) > 1:
                monster.move_towards(player)
            else:
                monster.character.attack(player)
        else:
            # Roam
            d_x = libtcod.random_get_int(0, -1, 1)
            d_y = libtcod.random_get_int(0, -1, 1)
            if libtcod.random_get_int(0, 0, 1) == 1:
                d_x = 0
            else:
                d_y = 0
            monster.move(d_x, d_y)


class MonsterDouble(object):
    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            if monster.distance_to(player) > 1:
                monster.move_towards(player)
            else:
                monster.character.attack(player)
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
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
                if Map.MAP[y][x] == '\'':
                    new_map[x][y].gnd = '\''
                    new_map[x][y].block = False
                    new_map[x][y].block_vision = False
                elif Map.MAP[y][x] == '#':
                    new_map[x][y].gnd = '#'
                    new_map[x][y].block = True
                    new_map[x][y].block_vision = True
                elif Map.MAP[y][x] == '~':
                    new_map[x][y].gnd = '~'
                    new_map[x][y].block = False
                    new_map[x][y].block_vision = False
                elif Map.MAP[y][x] == '=':
                    new_map[x][y].gnd = '='
                    new_map[x][y].block = False
                    new_map[x][y].block_vision = False
                elif Map.MAP[y][x] == ',':
                    new_map[x][y].gnd = ','
                    new_map[x][y].block = False
                    new_map[x][y].block_vision = False
                else:
                    new_map[x][y].gnd = '.'
                    new_map[x][y].block = False
                    new_map[x][y].block_vision = False
        return new_map


class Item:
    def __init__(self, name, hp_bst, atk_bst, df_bst, acc_bst, avo_bst, item_type, is_held, verb, x, y,
                 char, colour):
        self.name = name
        self.hp_bst = hp_bst
        self.atk_bst = atk_bst
        self.df_bst = df_bst
        self.acc_bst = acc_bst
        self.avo_bst = avo_bst
        self.item_type = item_type
        self.is_held = is_held
        self.verb = verb
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour

    def draw(self):
        if not self.is_held:
            libtcod.console_set_default_foreground(buf, self.colour)
            libtcod.console_put_char(buf, self.x, self.y, self.char, libtcod.BKGND_NONE)


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
STATE_TITLE = 9
STATE_EXIT = 99

MV_OKAY = 0
MV_OBJ = 1
MV_BLOCK = 2
MV_EDGEWORLD = 3
MV_LAURIER = 4
MV_WATER = 5

WATER_DMG = 15

P_X = 101
P_Y = 51

FOV_LIGHT_WALLS = True
FOV_ALG = 0

MSG_HISTORY_MAX = 5
MSG_DISPLAY = 5

HP_THRESHOLD_GOOD = 50
HP_THRESHOLD_OKAY = 20

STARTING_CREATURES = 250

M = Mons
I = Items
S = Signs

# Global variables
global_state = STATE_TITLE
msg_history = []
objects = []
items = []
signs = []
p_fov_recalc = True
p_vision = M.M['player'][M.VIS]
p_turn = 0
p_level = 1
p_exp = 0
p_reqexp = 100
p_skillpoints = 4
p_hpup = 10
did_move = False

# Items
p_weapon = None
has_weapon = False
p_armour = None
SLEEP_RESTORE = 10
SLEEP_RESTORE_RAND = 40
SLEEP_RATE = 15
LEVEL_HITS = 20
VISION_BASE = 20

# Keys
KEY_ESCAPE = libtcod.KEY_ESCAPE
KEY_UP = libtcod.KEY_UP
KEY_DOWN = libtcod.KEY_DOWN
KEY_LEFT = libtcod.KEY_LEFT
KEY_RIGHT = libtcod.KEY_RIGHT
KEY_ENTER = libtcod.KEY_ENTER
KEY_C_GET = ord(',')

# Colours
colour_default = libtcod.white
colour_dark = libtcod.black
colour_wall_seen = libtcod.Color(66, 69, 77)
colour_wall_bright = libtcod.Color(125, 129, 136)
colour_ground_seen = libtcod.Color(21, 26, 36)
colour_ground_bright = libtcod.Color(33, 35, 40)
colour_road_seen = libtcod.Color(14, 16, 20)
colour_road_bright = libtcod.Color(20, 23, 28)
colour_grass_seen = libtcod.Color(1, 11, 1)
colour_grass_bright = libtcod.Color(5, 18, 5)
colour_water_seen = libtcod.Color(0, 4, 10)
colour_water_bright = libtcod.Color(0, 35, 60)
colour_train_seen = libtcod.Color(13, 6, 1)
colour_train_bright = libtcod.Color(26, 12, 0)
colour_hp_good = libtcod.Color(102, 255, 51)
colour_hp_okay = libtcod.Color(255, 204, 51)
colour_hp_bad = libtcod.Color(255, 51, 102)


def create_monster(out_of_view=False):
    # Create array of possible monsters
    possible = []
    for entry in M.M:
        if M.M[entry][M.LVL] <= p_level and p_level != 99:
            possible.append(entry)
        if p_level == 99 and M.M[entry][M.LVL] == p_level:
            possible.append(entry)
    r = possible[libtcod.random_get_int(0, 0, len(possible) - 1)]
    x = 0
    y = 0
    while True:
        x = libtcod.random_get_int(0, 1, MAP_WIDTH - 1)
        y = libtcod.random_get_int(0, 1, MAP_HEIGHT - 1)
        if legal_move(x, y) == MV_OKAY and not out_of_view:
            break
        if legal_move(x, y) == MV_OKAY and out_of_view and not libtcod.map_is_in_fov(fov_map, x, y):
            break
    new_mons_char = Character(M.M[r][M.HP], M.M[r][M.ATK], M.M[r][M.DEF], M.M[r][M.ACC], M.M[r][M.AVO], M.M[r][M.VIS],
                              M.M[r][M.COL], M.M[r][M.EXP], M.M[r][M.RATE], death_func=monster_death)
    if M.M[r][M.DROP] is not None:
        new_mons_char.drop = M.M[r][M.DROP]
    else:
        new_mons_char.drop = None
    new_mons_ai = Monster()
    if M.M[r][M.SPD]:
        new_mons_ai = MonsterDouble()
    new_mons = Object(x, y, M.M[r][M.NAME], M.M[r][M.CHAR], M.M[r][M.COL], True, Object.ALIGN_ENEMY,
                      character=new_mons_char, behaviour=new_mons_ai)
    return new_mons


def create_specific_monster(name, x, y):
    new_mons_char = Character(M.M[name][M.HP], M.M[name][M.ATK], M.M[name][M.DEF], M.M[name][M.ACC], M.M[name][M.AVO], M.M[name][M.VIS],
                              M.M[name][M.COL], M.M[name][M.EXP], M.M[name][M.RATE], death_func=monster_death)
    if M.M[name][M.DROP] is not None:
        new_mons_char.drop = M.M[name][M.DROP]
    else:
        new_mons_char.drop = None
    new_mons_ai = Monster()
    new_mons = Object(x, y, M.M[name][M.NAME], M.M[name][M.CHAR], M.M[name][M.COL], True, Object.ALIGN_ENEMY,
                      character=new_mons_char, behaviour=new_mons_ai)
    return new_mons


def legal_move(x, y):
    if x >= MAP_WIDTH:
        return MV_LAURIER
    elif x < 0 or y >= MAP_HEIGHT or y < 0:
        return MV_EDGEWORLD
    elif the_map[x][y].gnd == '~':
        return MV_WATER
    elif the_map[x][y].block:
        return MV_BLOCK
    for obj in objects:
        if obj.x == x and obj.y == y and obj.blocks:
            return MV_OBJ
    return MV_OKAY


def msg_add(new_msg):
    if new_msg == "":
        return
    if len(msg_history) >= MSG_HISTORY_MAX:
        del msg_history[0]
    msg_history.append(new_msg)


def player_death(obj):
    global global_state
    global_state = STATE_DEAD
    msg_add(Msg.DEAD)
    player.char = libtcod.CHAR_SMILIE_INV


def player_move(d_x, d_y):
    if d_x != 0 or d_y != 0:
        global global_state, p_weapon, p_armour, did_move
        global_state = STATE_PLAY
        move_result = legal_move(player.x + d_x, player.y + d_y)
        target = None
        if move_result == MV_OKAY or move_result == MV_WATER:
            player.x += d_x
            player.y += d_y
            did_move = True
            if p_weapon is not None:
                p_weapon.x = player.x
                p_weapon.y = player.y
            if p_armour is not None:
                p_armour.x = player.x
                p_armour.y = player.y
            # Check for water
            if the_map[player.x][player.y].gnd == '~':
                if player.character.hp > 0:
                    msg_add(Msg.WATER)
                    player.character.take_dmg(WATER_DMG)
            elif the_map[player.x][player.y].gnd == '=' and libtcod.random_get_int(0, 0, 10) == 0:
                msg_add(Msg.TRAIN)
            global p_fov_recalc
            p_fov_recalc = True
        elif move_result == MV_OBJ:
            for obj in objects:
                if obj.x == player.x + d_x and obj.y == player.y + d_y and obj.blocks:
                    target = obj
                    break
        elif move_result == MV_EDGEWORLD:
            msg_add(Msg.HIT_EDGE)
        elif move_result == MV_LAURIER:
            msg_add(Msg.HIT_LAURIER)
        else:
            msg_add(Msg.HIT_WALL)
        if (not target is None) and target.align == Object.ALIGN_ENEMY and target.blocks:
            player.character.attack(target)
    else:
        did_move = False
    handle_enemies()
    global p_turn
    p_turn += 1


def handle_keys():
    global global_state
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == KEY_ESCAPE:
        return STATE_EXIT
    if global_state == STATE_PLAY:
        if key.c == KEY_C_GET:
            player_pickup()
            return STATE_PLAY
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
    if global_state == STATE_TITLE:
        if key.vk == KEY_ENTER:
            return STATE_PLAY


def player_pickup():
    did_pickup = False
    global did_move
    did_move = False
    global p_armour, p_weapon
    for itm in items:
        if itm.x == player.x and itm.y == player.y and not itm.is_held:
            did_pickup = True
            if itm.item_type == I.TYPE_INSTANT:
                if itm.name == I.I['sleep'][I.NAME]:
                    msg_add(Msg.ITM_SLEEP)
                    heal = SLEEP_RESTORE + libtcod.random_get_int(0, 0, SLEEP_RESTORE_RAND)
                    player.character.take_dmg(-heal)
                    items.remove(itm)
                if itm.name == I.I['vision'][I.NAME]:
                    msg_add(Msg.ITM_VISION)
                    player.character.mhp += 100
                    items.remove(itm)
            else:
                msg_add("You pick up " + grammar_a(itm.name) + " " + itm.name + ".")
            # Pick it up
            if itm.item_type == I.TYPE_ARMOUR:
                if p_armour is None:
                    p_armour = itm
                    itm.is_held = True
                    player.character.atk += itm.atk_bst
                    player.character.df += itm.df_bst
                    player.character.acc += itm.acc_bst
                    player.character.avo += itm.avo_bst
                    player.character.mhp += itm.hp_bst
                else:
                    # Already an item, drop it
                    p_armour.is_held = False
                    itm.is_held = True
                    player.character.atk += itm.atk_bst
                    player.character.df += itm.df_bst
                    player.character.acc += itm.acc_bst
                    player.character.avo += itm.avo_bst
                    player.character.mhp += itm.hp_bst
                    player.character.atk -= p_armour.atk_bst
                    player.character.df -= p_armour.df_bst
                    player.character.acc -= p_armour.acc_bst
                    player.character.avo -= p_armour.avo_bst
                    player.character.mhp -= p_armour.hp_bst
                    p_armour = itm
            if itm.item_type == I.TYPE_WEAPON:
                global has_weapon
                has_weapon = True
                if p_weapon is None:
                    p_weapon = itm
                    itm.is_held = True
                    player.character.atk += itm.atk_bst
                    player.character.df += itm.df_bst
                    player.character.acc += itm.acc_bst
                    player.character.avo += itm.avo_bst
                    player.character.mhp += itm.hp_bst
                else:
                    # Already an item, drop it
                    p_weapon.is_held = False
                    itm.is_held = True
                    player.character.atk += itm.atk_bst
                    player.character.df += itm.df_bst
                    player.character.acc += itm.acc_bst
                    player.character.avo += itm.avo_bst
                    player.character.mhp += itm.hp_bst
                    player.character.atk -= p_weapon.atk_bst
                    player.character.df -= p_weapon.df_bst
                    player.character.acc -= p_weapon.acc_bst
                    player.character.avo -= p_weapon.avo_bst
                    player.character.mhp -= p_weapon.hp_bst
                    p_weapon = itm
            if did_pickup:
                if player.character.hp > player.character.mhp:
                    player.character.hp = player.character.mhp
                break
    if not did_pickup:
        msg_add(Msg.NO_PICKUP)
    global p_turn
    p_turn += 1


def create_sign(i):
    new_sign = Object(S.S[i][S.X], S.S[i][S.Y], S.S[i][S.MSG], '?', libtcod.white, False, Object.ALIGN_NEUTRAL)
    signs.append(new_sign)


def make_map():
    global the_map, fov_map
    the_map = MapGen.generate_map(MAP_WIDTH, MAP_HEIGHT)
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            libtcod.map_set_properties(fov_map, x, y, not the_map[x][y].block_vision, not the_map[x][y].block)
    libtcod.map_compute_fov(fov_map, player.x, player.y, p_vision, FOV_LIGHT_WALLS, FOV_ALG)
    for i in range(STARTING_CREATURES):
        objects.append(create_monster())
    for i in range(len(S.S)):
        create_sign(i)


def monster_death(monster):
    msg_add("The " + monster.name + " is no more.")
    global p_exp, p_reqexp, p_level, items
    p_exp += int(monster.character.xp)
    did_drop_item = False
    if monster.character.drop:
        if libtcod.random_get_int(0, 1, 100) <= monster.character.rate:
            do_drop = True
            did_drop_item = True
            i = -1
            for itm in items:
                if itm.x == monster.x and itm.y == monster.y and monster.character.rate < 100:
                    do_drop = False
                if itm.x == monster.x and itm.y == monster.y and monster.character.rate == 100:
                    do_drop = True
                    i = items.index(itm)
            if do_drop:
                if i >= 0:
                    del items[i]
                # Drop item
                n = monster.character.drop
                new_item = Item(I.I[n][I.NAME], I.I[n][I.HP], I.I[n][I.ATK], I.I[n][I.DEF], I.I[n][I.ACC], I.I[n][I.AVO],
                                I.I[n][I.TYPE], False, I.I[n][I.VERB], monster.x, monster.y, I.I[n][I.CHAR], I.I[n][I.COL])
                items.append(new_item)
                msg_add(grammar_a(new_item.name).capitalize() + " " + new_item.name + " drops from the " +
                        monster.name + ".")
    if not did_drop_item:
        if libtcod.random_get_int(0, 1, 100) <= SLEEP_RATE:
            do_drop = True
            for itm in items:
                if itm.x == monster.x and itm.y == monster.y:
                    do_drop = False
            if do_drop:
                # Drop item
                n = 'sleep'
                new_item = Item(I.I[n][I.NAME], I.I[n][I.HP], I.I[n][I.ATK], I.I[n][I.DEF], I.I[n][I.ACC], I.I[n][I.AVO],
                                I.I[n][I.TYPE], False, I.I[n][I.VERB], monster.x, monster.y, I.I[n][I.CHAR], I.I[n][I.COL])
                items.append(new_item)
                msg_add(grammar_a(new_item.name).capitalize() + " appears from the bowels of " +
                        monster.name + ".")
    if p_exp >= p_reqexp:
        p_exp -= p_reqexp
        # Formula: LVL^1.5 * 200 rounded to nearest 100
        p_level += 1
        p_reqexp = int(math.pow(p_level, 1.5) * 200) - int(math.pow(p_level, 1.5) * 200) % 100
        gain_atk = libtcod.random_get_int(0, 0, p_skillpoints)
        gain_def = p_skillpoints - gain_atk
        msg_add("Level up! You gain " + str(gain_atk) + " attack power and " + str(gain_def) + " defence power.")
        player.character.atk += gain_atk
        player.character.df += gain_def
        player.character.mhp += gain_def * p_hpup + LEVEL_HITS
        player.character.hp = player.character.mhp
        check_level()
    monster.blocks = False
    monster.character = None
    monster.behaviour = None
    monster.char = '%'


def check_level():
    if p_level == 2:
        objects.append(try_spawn('ece'))
        msg_add(Msg.SPAWN_ECE)
    if p_level == 3:
        objects.append(try_spawn('scribbler'))
        msg_add(Msg.SPAWN_SCRIBBLER)
    if p_level == 4:
        objects.append(try_spawn('coop'))
        msg_add(Msg.SPAWN_COOP)
    if p_level == 5:
        objects.append(try_spawn('f_geese'))
        msg_add(Msg.SPAWN_FGEESE)
    if p_level == 6:
        objects.append(try_spawn('date'))
        msg_add(Msg.SPAWN_DATE)
    if p_level == 7:
        objects.append(try_spawn('trains'))
        msg_add(Msg.SPAWN_TRAINS)
    if p_level == 8:
        objects.append(try_spawn('ironring'))
        msg_add(Msg.SPAWN_IRONRING)
    if p_level == 9:
        objects.append(try_spawn('headcom'))
        msg_add(Msg.SPAWN_HEADCOM)


def check_turn():
    if p_turn % max(12 - p_level, 1) == 0:
        mons = create_monster(True)
        objects.append(mons)


def try_spawn(name):
    if legal_move(player.x + 1, player.y) == MV_OKAY:
        return create_specific_monster(name, player.x + 1, player.y)
    if legal_move(player.x - 1, player.y) == MV_OKAY:
        return create_specific_monster(name, player.x - 1, player.y)
    if legal_move(player.x, player.y + 1) == MV_OKAY:
        return create_specific_monster(name, player.x, player.y + 1)
    if legal_move(player.x, player.y - 1) == MV_OKAY:
        return create_specific_monster(name, player.x, player.y - 1)


def handle_enemies():
    for obj in objects:
        if obj.align == Object.ALIGN_ENEMY:
            if obj.behaviour:
                obj.behaviour.take_turn()


def get_colour_hp():
    if player.character.hp * 100 / player.character.mhp > HP_THRESHOLD_GOOD:
        return colour_hp_good
    elif player.character.hp * 100 / player.character.mhp > HP_THRESHOLD_OKAY:
        return colour_hp_okay
    else:
        return colour_hp_bad


def grammar_a(name):
    if name[0] == 'a' or name[0] == 'e' or name[0] == 'i' or name[0] == 'o' or name[0] == 'u':
        return "an"
    else:
        return "a"


def render_all():
    libtcod.console_clear(buf)
    libtcod.console_clear(msg)
    # FOV
    global p_fov_recalc
    if p_fov_recalc:
        p_fov_recalc = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, p_vision, FOV_LIGHT_WALLS, FOV_ALG)
    # Map
    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            if libtcod.map_is_in_fov(fov_map, x, y):
                if the_map[x][y].gnd == '#':
                    libtcod.console_set_char_background(buf, x, y, colour_wall_bright, libtcod.BKGND_SET)
                elif the_map[x][y].gnd == '\'':
                    libtcod.console_set_char_background(buf, x, y, colour_road_bright, libtcod.BKGND_SET)
                elif the_map[x][y].gnd == '~':
                    libtcod.console_set_char_background(buf, x, y, colour_water_bright, libtcod.BKGND_SET)
                elif the_map[x][y].gnd == '=':
                    libtcod.console_set_char_background(buf, x, y, colour_train_bright, libtcod.BKGND_SET)
                elif the_map[x][y].gnd == ',':
                    libtcod.console_set_char_background(buf, x, y, colour_grass_bright, libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(buf, x, y, colour_ground_bright, libtcod.BKGND_SET)
                the_map[x][y].seen = True
            elif the_map[x][y].gnd == '#' and player.distance_to_coord(x, y) <= p_vision:
                libtcod.console_set_char_background(buf, x, y, colour_wall_bright, libtcod.BKGND_SET)
                the_map[x][y].seen = True
            elif the_map[x][y].gnd == '#' and the_map[x][y].seen and player.distance_to_coord(x, y) > p_vision:
                libtcod.console_set_char_background(buf, x, y, colour_wall_seen, libtcod.BKGND_SET)
                the_map[x][y].seen = True
            elif the_map[x][y].seen:
                if the_map[x][y].gnd == '\'':
                    libtcod.console_set_char_background(buf, x, y, colour_road_seen, libtcod.BKGND_SET)
                elif the_map[x][y].gnd == '~':
                    libtcod.console_set_char_background(buf, x, y, colour_water_seen, libtcod.BKGND_SET)
                elif the_map[x][y].gnd == '=':
                    libtcod.console_set_char_background(buf, x, y, colour_train_seen, libtcod.BKGND_SET)
                elif the_map[x][y].gnd == ',':
                    libtcod.console_set_char_background(buf, x, y, colour_grass_seen, libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(buf, x, y, colour_ground_seen, libtcod.BKGND_SET)
            else:
                libtcod.console_set_char_background(buf, x, y, colour_dark, libtcod.BKGND_SET)
    # Objects
    #   Signs
    for sign in signs:
        if libtcod.map_is_in_fov(fov_map, sign.x, sign.y):
            if sign.x == player.x and sign.y == player.y:
                libtcod.console_print(msg, SCREEN_WIDTH - len(sign.name), SCREEN_HEIGHT - 2, sign.name)
            sign.draw()
    #   Corpses
    for obj in objects:
        if libtcod.map_is_in_fov(fov_map, obj.x, obj.y):
            if obj.x == player.x and obj.y == player.y and obj.align == Object.ALIGN_ENEMY and did_move and not obj.blocks:
                if obj.name == M.M['edcom'][M.NAME]:
                    msg_add(grammar_a(obj.name).capitalize() + " " + obj.name + " is not entertained.")
                else:
                    msg_add(grammar_a(obj.name).capitalize() + " " + obj.name + " sleeps here forever.")
            obj.draw()
    #   Items
    for itm in items:
        if itm.x == player.x and itm.y == player.y and not itm.is_held and did_move:
            msg_add("There is " + grammar_a(itm.name) + " " + itm.name + " here.")
        if libtcod.map_is_in_fov(fov_map, itm.x, itm.y):
            if not itm.is_held:
                itm.draw()
    #   Monsters
    for obj in objects:
        if libtcod.map_is_in_fov(fov_map, obj.x, obj.y):
            if obj.blocks and obj.align == Object.ALIGN_ENEMY:
                if obj.align != Object.ALIGN_ALLY:
                    obj.draw()
    #   Player
    player.draw()
    # Signs
    for i in range(len(S.S)):
        if player.x == S.S[S.X] and player.y == S.S[S.Y]:
            msg_add(S.S[S.MSG])
    # Messages
    for i in range(MSG_DISPLAY):
        if i >= len(msg_history):
            break
        libtcod.console_set_default_foreground(msg, libtcod.Color(255-255/(MSG_DISPLAY + 1)*i,
                                                                  255-255/(MSG_DISPLAY + 1)*i,
                                                                  255-255/(MSG_DISPLAY + 1)*i))
        libtcod.console_print(msg, 0, i, msg_history[len(msg_history) - 1 - i])
    # HUD
    libtcod.console_set_default_foreground(msg, colour_default)
    equip_atk = 0
    equip_def = 0
    equip_acc = 0
    equip_avo = 0
    equip_hp = 0
    if p_weapon is not None:
        equip_atk += p_weapon.atk_bst
        equip_def += p_weapon.df_bst
        equip_acc += p_weapon.acc_bst
        equip_avo += p_weapon.avo_bst
        equip_hp += p_weapon.hp_bst
    if p_armour is not None:
        equip_atk += p_armour.atk_bst
        equip_def += p_armour.df_bst
        equip_acc += p_armour.acc_bst
        equip_avo += p_armour.avo_bst
        equip_hp += p_armour.hp_bst
    str_atk = ""
    str_def = ""
    str_acc = ""
    str_avo = ""
    str_hp = ""
    if equip_atk > 0:
        str_atk = " (+" + str(equip_atk) + ")"
    if equip_def > 0:
        str_def = " (+" + str(equip_def) + ")"
    if equip_acc > 0:
        str_acc = " (+" + str(equip_acc) + ")"
    if equip_avo > 0:
        str_avo = " (+" + str(equip_avo) + ")"
    if equip_hp > 0:
        str_hp = " (+" + str(equip_hp) + ")"
    if equip_atk < 0:
        str_atk = " (" + str(equip_atk) + ")"
    if equip_def < 0:
        str_def = " (" + str(equip_def) + ")"
    if equip_acc < 0:
        str_acc = " (" + str(equip_acc) + ")"
    if equip_avo < 0:
        str_avo = " (" + str(equip_avo) + ")"
    if equip_hp < 0:
        str_hp = " (" + str(equip_hp) + ")"
    libtcod.console_print(msg, 0, SCREEN_HEIGHT - 4, "ATK " + str(player.character.atk) + str(str_atk))
    libtcod.console_print(msg, 0, SCREEN_HEIGHT - 3, "DEF " + str(player.character.df) + str(str_def))
    libtcod.console_print(msg, 0, SCREEN_HEIGHT - 2, "ACC " + str(player.character.acc) + str(str_acc))
    libtcod.console_print(msg, 0, SCREEN_HEIGHT - 1, "AVO " + str(player.character.avo) + str(str_avo))
    libtcod.console_print(msg, 0, SCREEN_HEIGHT - 10, "VIT ")
    libtcod.console_set_default_foreground(msg, get_colour_hp())
    libtcod.console_print(msg, 4 + len(str(player.character.mhp)) - len(str(player.character.hp)), SCREEN_HEIGHT - 10,
                          str(player.character.hp))
    libtcod.console_set_default_foreground(msg, colour_default)
    libtcod.console_print(msg, 7, SCREEN_HEIGHT - 10, "/" + str(player.character.mhp) + str_hp)
    if p_weapon is not None and p_weapon.name == I.I['tool'][I.NAME]:
        libtcod.console_print(msg, 0, SCREEN_HEIGHT - 12, "LVL Graduated!")
        global p_level
        p_level = 99
    else:
        libtcod.console_print(msg, 0, SCREEN_HEIGHT - 12, "LVL " + str(p_level))
    libtcod.console_print(msg, 0, SCREEN_HEIGHT - 9, "EXP " + (len(str(p_reqexp)) - len(str(p_exp))) * ' ' +
                          str(p_exp) + "/" + str(p_reqexp))
    # Armour
    str_weapon = "WPN "
    str_armour = "ARM "
    if p_armour is not None:
        str_armour += p_armour.name.capitalize()
    else:
        str_armour += Msg.NO_ARMOUR
    if p_weapon is not None:
        str_weapon += p_weapon.name.capitalize()
    else:
        str_weapon += Msg.NO_WEAPON
    libtcod.console_print(msg, 0, SCREEN_HEIGHT - 7, str_weapon)
    libtcod.console_print(msg, 0, SCREEN_HEIGHT - 6, str_armour)
    turn_str = "Time " + str(p_turn)
    libtcod.console_print(msg, SCREEN_WIDTH - len(turn_str), SCREEN_HEIGHT - 1, turn_str)
    # Draw
    libtcod.console_blit(blank, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
    libtcod.console_blit(buf, player.x - SCREEN_WIDTH/2, player.y - SCREEN_HEIGHT/2, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
    libtcod.console_blit(msg, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0, 1, 0)


def make_title():
    libtcod.console_clear(buf)
    libtcod.console_clear(msg)
    libtcod.console_set_default_foreground(msg, colour_default)
    libtcod.console_print(msg, 4, SCREEN_HEIGHT - 18, "Controls:")
    libtcod.console_print(msg, 4, SCREEN_HEIGHT - 17, "   arrow keys - move & attack")
    libtcod.console_print(msg, 4, SCREEN_HEIGHT - 16, "   , (comma) - pick up")
    libtcod.console_print(msg, 4, SCREEN_HEIGHT - 10, "Press Enter to start")
    libtcod.console_print(msg, 4, SCREEN_HEIGHT - 4, "ENGHack 2014 @ University of Waterloo")
    bg = libtcod.image_load("bg.png")
    libtcod.image_blit_rect(bg, msg, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, libtcod.BKGND_ADD)
    libtcod.console_blit(blank, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
    libtcod.console_blit(msg, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0, 1, 1)
    libtcod.console_flush()


libtcod.console_set_custom_font("terminal12x12_gs_ro.png", libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, "Rogue@UW - ENGHack 2014", False)
libtcod.console_set_keyboard_repeat(KBD_RPT_INIT_DELAY, KBD_RPT_INTERVAL_DELAY)
buf = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
blank = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
msg = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

player_char = Character(M.M['player'][M.HP], M.M['player'][M.ATK], M.M['player'][M.DEF], M.M['player'][M.ACC],
                        M.M['player'][M.AVO], M.M['player'][M.VIS], M.M['player'][M.COL], M.M['player'][M.EXP],
                        M.M['player'][M.RATE], death_func=player_death)
player = Object(P_X, P_Y, M.M['player'][M.NAME], M.M['player'][M.CHAR], M.M['player'][M.COL], True, Object.ALIGN_ALLY,
                character=player_char)
objects.append(player)
make_map()

# Title loop
while not libtcod.console_is_window_closed():
    make_title()
    do_exit = handle_keys()
    if do_exit == STATE_EXIT:
        sys.exit(0)
    elif do_exit == STATE_PLAY:
        break


global_state = STATE_PLAY
# Main loop
while not libtcod.console_is_window_closed():
    # Output
    check_turn()
    render_all()
    libtcod.console_flush()
    # Input
    do_exit = handle_keys()
    # Processing
    if do_exit == STATE_EXIT:
        sys.exit(0)
    elif do_exit == STATE_PLAY:
        handle_enemies()