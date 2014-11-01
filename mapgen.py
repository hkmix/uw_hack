import libtcodpy as libtcod


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