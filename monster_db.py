import libtcodpy as libtcod
import math


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
            'player':['engineer', 0, 100, 9, 4, 90, 10, '@', 10, libtcod.Color(99, 95, 106), 0, None],
            't_zombie':['zombie trainee', 1, 12, 3, 2, 30, 0, 'z', 5, libtcod.Color(110, 124, 110), 12, None],
            's_zombie':['small zombie', 1, 15, 3, 3, 30, 0, 'z', 6, libtcod.Color(57, 72, 57), 15, None],
            'r_zombie':['zombie', 1, 20, 4, 3, 40, 0, 'Z', 8, libtcod.Color(57, 72, 57), 20, None],
            'b_alien':['unfriendly alien', 1, 10, 5, 1, 60, 5, 'a', 10, libtcod.Color(139, 124, 132), 15, None],
            'r_alien':['xenophobic alien', 1, 15, 6, 2, 60, 10, 'A', 12, libtcod.Color(157, 140, 144), 22, None],
            'edcom':['scary ED-COM', 2, 90, 12, 1, 40, 5, 'E', 7, libtcod.Color(129, 138, 128), 250, None],
            'x_zombie':['X-formation zombies', 4, 120, 12, 1, 40, 5, 'X', 7, libtcod.Color(144, 250, 133), 250, None],
            'f_geese':['flock of geese', 10, 500, 20, 20, 85, 20, 'G', 12, libtcod.Color(157, 140, 144), 22, None]
        }


class Monster():
    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(the_map, monster.x, monster.y):
            if monster.distance_to(player) > 1:
                monster.move_towards(player)
            else:
                monster.character.attack(player)


class Object():
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