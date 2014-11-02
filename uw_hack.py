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
        if legal_move(self.x + dx, self.y + dy) == MV_OKAY:
            self.x += dx
            self.y += dy

    def draw(self):
        libtcod.console_set_default_foreground(buf, self.colour)
        libtcod.console_put_char(buf, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def distance_to(self, target):
        return math.sqrt((target.x - self.x) ** 2 + (target.y - self.y) ** 2)

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


class Character():
    def __init__(self, hp, atk, df, acc, avo, vis, col, xp, rate, drop=None, death_func=None):
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
        if does_hit > self.acc:
            # Miss
            msg_add("The " + self.owner.name + " swings at the " + target.name + " and misses!")
        elif does_hit <= round(self.acc / 15):
            # Critical chance: ACC / 15
            dmg = libtcod.random_get_int(0, max_dmg, max_dmg * 2)
            if target.name == M.M['edcom'][M.NAME]:
                msg_add("The " + self.owner.name + " seriously respects the " + target.name + " and is granted " + str(dmg) + " damage.")
            elif target.align == Object.ALIGN_ENEMY and has_weapon:
                msg_add("The " + self.owner.name + " brutally " + p_weapon.verb + " the " + target.name + " for " + str(dmg) + " damage!")
            else:
                msg_add("The " + self.owner.name + " brutally hits the " + target.name + " for " + str(dmg) + " damage!")
            target.character.take_dmg(dmg)
        else:
            # Regular hit
            dmg = libtcod.random_get_int(0, 0, max_dmg)
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

    M = \
        {
            'player': ['engineer', 99, 100, 9, 4, 90, 10, libtcod.CHAR_SMILIE, 15, libtcod.white, 0, None, 0],
            't_zombie': ['zombie trainee', 1, 12, 3, 2, 30, 0, 'z', 5, libtcod.Color(170, 184, 170), 12, 'o_shirt', 3],
            's_zombie': ['zombie', 1, 15, 3, 3, 30, 0, 'z', 6, libtcod.Color(127, 142, 127), 15,  'o_shirt', 4],
            'r_zombie': ['expert zombie', 1, 20, 4, 3, 40, 0, 'Z', 8, libtcod.Color(127, 142, 127), 20,  'o_shirt', 5],
            'b_alien': ['unfriendly alien', 1, 10, 5, 1, 60, 5, 'a', 10, libtcod.Color(189, 174, 182), 15, 'mtool', 6],
            'r_alien': ['xenophobic alien', 1, 15, 6, 2, 60, 10, 'A', 12, libtcod.Color(187, 180, 184), 22, 'mtool', 8],
            'edcom': ['scary ED-COM', 2, 75, 12, 1, 40, 5, 'E', 7, libtcod.Color(169, 178, 168), 50, 'mtool', 20],
            'x_zombie': ['X-formation zombies', 99, 120, 12, 1, 40, 5, 'X', 7, libtcod.Color(144, 250, 133), 250, None, 0],
            'f_geese': ['flock of geese', 99, 200, 30, 20, 85, 20, 'G', 12, libtcod.Color(157, 140, 144), 22, None, 0]
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

    I = \
        {
            'o_shirt': ['light-red orientation shirt', 5, 0, 1, 0, 2, TYPE_ARMOUR, "", '[', libtcod.Color(255, 90, 90)],
            'mtool': ['somewhat functional multitool', 0, 1, 0, 5, 0, TYPE_WEAPON, "weakly prods", ')', libtcod.Color(255, 217, 0)]
        }


class Monster(object):
    def take_turn(self):
        monster = self.owner
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
                    new_map[x][y].block_vision = False
                elif Map.MAP[y][x] == '~':
                    new_map[x][y].gnd = '~'
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


class Signs(object):
    X = 0
    Y = 1
    MSG = 2

    S = \
        [
            [1, 2, "Message here"]
        ]


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
MV_EDGEWORLD = 3
MV_LAURIER = 4
MV_WATER = 5

WATER_DMG = 15

P_X = 20
P_Y = 75

FOV_LIGHT_WALLS = True
FOV_ALG = 0

MSG_HISTORY_MAX = 100
MSG_DISPLAY = 5

HP_THRESHOLD_GOOD = 80
HP_THRESHOLD_OKAY = 30

M = Mons
I = Items
S = Signs

# Global variables
global_state = STATE_PLAY
msg_history = []
objects = []
items = []
p_fov_recalc = True
p_vision = M.M['player'][M.VIS]
p_turn = 0
p_level = 1
p_exp = 0
p_reqexp = 100
p_skillpoints = 3
p_hpup = 5
did_move = False

# Items
p_weapon = None
has_weapon = False
p_armour = None

# Keys
KEY_ESCAPE = libtcod.KEY_ESCAPE
KEY_UP = libtcod.KEY_UP
KEY_DOWN = libtcod.KEY_DOWN
KEY_LEFT = libtcod.KEY_LEFT
KEY_RIGHT = libtcod.KEY_RIGHT
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
colour_hp_good = libtcod.Color(102, 255, 51)
colour_hp_okay = libtcod.Color(255, 204, 51)
colour_hp_bad = libtcod.Color(255, 51, 102)


def create_monster():
    # Create array of possible monsters
    possible = []
    for entry in M.M:
        if M.M[entry][M.LVL] - p_level <= 1:
            possible.append(entry)
    r = possible[libtcod.random_get_int(0, 0, len(possible) - 1)]
    x = 0
    y = 0
    while True:
        x = libtcod.random_get_int(0, 1, MAP_WIDTH - 1)
        y = libtcod.random_get_int(0, 1, MAP_HEIGHT - 1)
        if legal_move(x, y) == MV_OKAY:
            break
    new_mons_char = Character(M.M[r][M.HP], M.M[r][M.ATK], M.M[r][M.DEF], M.M[r][M.ACC], M.M[r][M.AVO], M.M[r][M.VIS],
                              M.M[r][M.COL], M.M[r][M.EXP], M.M[r][M.RATE], death_func=monster_death)
    if M.M[r][M.DROP] is not None:
        new_mons_char.drop = M.M[r][M.DROP]
    else:
        new_mons_char.drop = None
    new_mons_ai = Monster()
    new_mons = Object(x, y, M.M[r][M.NAME], M.M[r][M.CHAR], M.M[r][M.COL], True, Object.ALIGN_ENEMY,
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
    msg_history.insert(0, new_msg)


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
    if key.c == KEY_C_GET:
        player_pickup()
        return STATE_PLAY
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


def player_pickup():
    did_pickup = False
    global did_move
    did_move = False
    global p_armour, p_weapon
    for itm in items:
        if itm.x == player.x and itm.y == player.y and not itm.is_held:
            msg_add("You pick up " + grammar_a(itm.name) + " " + itm.name + ".")
            did_pickup = True
            # Pick it up
            if itm.item_type == Items.TYPE_ARMOUR:
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
            if itm.item_type == Items.TYPE_WEAPON:
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
    if not did_pickup:
        msg_add(Msg.NO_PICKUP)


def make_map():
    global the_map, fov_map
    the_map = MapGen.generate_map(MAP_WIDTH, MAP_HEIGHT)
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            libtcod.map_set_properties(fov_map, x, y, not the_map[x][y].block_vision, not the_map[x][y].block)
    libtcod.map_compute_fov(fov_map, player.x, player.y, p_vision, FOV_LIGHT_WALLS, FOV_ALG)
    for i in range(200):
        objects.append(create_monster())


def monster_death(monster):
    msg_add("The " + monster.name + " is no more.")
    global p_exp, p_reqexp, p_level, items
    p_exp += int(monster.character.xp)
    if monster.character.drop:
        if libtcod.random_get_int(0, 1, 100) <= monster.character.rate:
            do_drop = True
            for itm in items:
                if itm.x == monster.x and itm.y == monster.y:
                    do_drop = False
            if do_drop:
                # Drop item
                n = monster.character.drop
                new_item = Item(I.I[n][I.NAME], I.I[n][I.HP], I.I[n][I.ATK], I.I[n][I.DEF], I.I[n][I.ACC], I.I[n][I.AVO],
                                I.I[n][I.TYPE], False, I.I[n][I.VERB], monster.x, monster.y, I.I[n][I.CHAR], I.I[n][I.COL])
                items.append(new_item)
                msg_add(grammar_a(new_item.name).capitalize() + " " + new_item.name + " drops from the " + monster.name +
                        ".")
    if p_exp >= p_reqexp:
        p_exp -= p_reqexp
        # Formula: LVL^1.5 * 100 rounded to nearest 100
        p_level += 1
        p_reqexp = int(math.pow(p_level, 1.5) * 100) - int(math.pow(p_level, 1.5) * 200) % 100
        gain_atk = libtcod.random_get_int(0, 0, p_skillpoints)
        gain_def = p_skillpoints - gain_atk
        msg_add("Level up! You gain " + str(gain_atk) + " attack power and " + str(gain_def) + " defence power.")
        player.character.atk += gain_atk
        player.character.df += gain_def
        player.character.mhp += gain_def * p_hpup
        player.character.hp = player.character.mhp
    monster.blocks = False
    monster.character = None
    monster.behaviour = None
    monster.char = '%'


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
                elif the_map[x][y].gnd == ',':
                    libtcod.console_set_char_background(buf, x, y, colour_grass_bright, libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(buf, x, y, colour_ground_bright, libtcod.BKGND_SET)
                the_map[x][y].seen = True
            elif the_map[x][y].seen:
                if the_map[x][y].gnd == '#':
                    libtcod.console_set_char_background(buf, x, y, colour_wall_seen, libtcod.BKGND_SET)
                elif the_map[x][y].gnd == '\'':
                    libtcod.console_set_char_background(buf, x, y, colour_road_seen, libtcod.BKGND_SET)
                elif the_map[x][y].gnd == '~':
                    libtcod.console_set_char_background(buf, x, y, colour_water_seen, libtcod.BKGND_SET)
                elif the_map[x][y].gnd == ',':
                    libtcod.console_set_char_background(buf, x, y, colour_grass_seen, libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(buf, x, y, colour_ground_seen, libtcod.BKGND_SET)
            else:
                libtcod.console_set_char_background(buf, x, y, colour_dark, libtcod.BKGND_SET)
    # Objects
    #   Corpses
    for obj in objects:
        if libtcod.map_is_in_fov(fov_map, obj.x, obj.y):
            if obj.x == player.x and obj.y == player.y and obj.align == Object.ALIGN_ENEMY and did_move and not obj.blocks:
                if obj.name == M.M['edcom'][M.NAME]:
                    msg_add(grammar_a(obj.name).capitalize() + " " + obj.name + " is sleeping gracefully here.")
                else:
                    msg_add("The brutalized remains of " + grammar_a(obj.name) + " " + obj.name + " are here.")
            obj.draw()
    #   Items
    for itm in items:
        if itm.x == player.x and itm.y == player.y and not itm.is_held:
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
        libtcod.console_print(msg, 0, i, msg_history[i])
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
    turn_str = "Turn " + str(p_turn)
    libtcod.console_print(msg, SCREEN_WIDTH - len(turn_str), SCREEN_HEIGHT - 1, turn_str)
    # Draw
    libtcod.console_blit(blank, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
    libtcod.console_blit(buf, player.x - SCREEN_WIDTH/2, player.y - SCREEN_HEIGHT/2, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
    libtcod.console_blit(msg, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0, 1, 0)


libtcod.console_set_custom_font("terminal12x12_gs_ro.png", libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, "UW @ ENGHack 2014", False)
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