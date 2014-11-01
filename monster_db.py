import libtcodpy as libtcod


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
            't_zombie':['tiny zombie', 1, 12, 3, 2, 30, 0, 'z', 5, libtcod.Color(110, 124, 110), 12, None],
            's_zombie':['small zombie', 1, 15, 3, 3, 30, 0, 'z', 6, libtcod.Color(57, 72, 57), 15, None],
            'r_zombie':['zombie', 1, 20, 4, 3, 40, 0, 'Z', 8, libtcod.Color(57, 72, 57), 20, None],
            'b_alien':['baby alien', 1, 10, 5, 1, 60, 5, 'a', 10, libtcod.Color(139, 124, 132), 15, None],
            'r_alien':['alien', 1, 15, 6, 2, 60, 10, 'A', 12, libtcod.Color(157, 140, 144), 22, None],
            'x_zombie':['X-formation zombies', 4, 120, 12, 1, 40, 5, 'X', 7, libtcod.Color(144, 250, 133), 250, None]
        }