import libtcodpy as libtcod


class Character():
    def __init__(self, hp, atk, df, acc, avo, char, vis, col, xp, drop=None, death_func=None):
        self.hp = hp
        self.mhp = hp
        self.atk = atk
        self.df = df
        self.acc = acc
        self.avo = avo
        self.char = char
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