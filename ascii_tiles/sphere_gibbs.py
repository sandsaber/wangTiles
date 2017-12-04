import numpy as np
import time

from extract_tiles import *
from potentials import *
from create_sphere import *
from display import *
from constants import *
import random


# np.random.seed(0)

spherehood_relative_array = []
for i in range(SPHERE_WIDTH):
    for j in range(SPHERE_WIDTH):
        loc = (i - SPHERE_WIDTH / 2, j - SPHERE_WIDTH / 2)
        if loc != (0, 0):
            spherehood_relative_array.append(loc)
spherehood_relative_array = np.array(spherehood_relative_array)

def spherehood(i,j):
    hood = spherehood_relative_array + np.array([i,j])
    condition = np.logical_and(
                np.logical_and(hood[:,0] >= 0,
                hood[:,1] >= 0),
                np.logical_and(
                hood[:,0] < SPHERE_WIDTH,
                hood[:,1] < SPHERE_WIDTH))
    return hood[condition]

def normalize_probmap(probmap):
    s = np.sum(probmap, axis = -1)
    # s[s==0]=1
    probmap[s==0,:]=1
    s = np.sum(probmap, axis = -1)

    probmap /= s.reshape(WORLD_WIDTH, WORLD_WIDTH, 1)
    return probmap

def place(i, j, tile_index):
    decided[i,j] = 1
    global probmap
    probmap[max(0, i - SPHERE_WIDTH / 2): min(WORLD_WIDTH, i + SPHERE_WIDTH / 2 + 1),
            max(0, j - SPHERE_WIDTH / 2): min(WORLD_WIDTH, j + SPHERE_WIDTH / 2 + 1)]\
        *= spheres[tile_index,
                   max(0, -(i-SPHERE_WIDTH / 2)) : SPHERE_WIDTH - max(0, i + SPHERE_WIDTH / 2 + 1 - WORLD_WIDTH),
                   max(0, -(j-SPHERE_WIDTH / 2)) : SPHERE_WIDTH - max(0, j + SPHERE_WIDTH / 2 + 1 - WORLD_WIDTH)]

    probmap = normalize_probmap(probmap)
    world[i,j] = tile_index

def unplace(i, j):
    decided[i,j] = 0
    global probmap
    # print world[i,j], i, j
    s = spheres[world[i,j],
                   max(0, -(i-SPHERE_WIDTH / 2)) : SPHERE_WIDTH - max(0, i + SPHERE_WIDTH / 2 + 1 - WORLD_WIDTH),
                   max(0, -(j-SPHERE_WIDTH / 2)) : SPHERE_WIDTH - max(0, j + SPHERE_WIDTH / 2 + 1 - WORLD_WIDTH)]
    probmap[max(0, i - SPHERE_WIDTH / 2): min(WORLD_WIDTH, i + SPHERE_WIDTH / 2 + 1),
            max(0, j - SPHERE_WIDTH / 2): min(WORLD_WIDTH, j + SPHERE_WIDTH / 2 + 1)]\
        /= s + np.ones_like(s) * (s==0)

    probmap = normalize_probmap(probmap)
    world[i,j] = 0


def get_all_valid(i,j):
    result = []
    for t in range(len(tiles)):
        ismatch = True
        for ni, nj in neighbors(i,j):
            ismatch = ismatch and match(tiles[t], tiles[world[ni,nj]], ni - i, nj - j)
        if ismatch:
            result.append(t)
    return result


            # else:
            #     world[i,j] = random.choice(tiles)



def logp(world):
    logp = 0
    for i in range(world.shape[0]):
        for j in range(world.shape[1]):
            logp += np.log(p(i,j,tiles[world[i,j]]))
    print logp





tile_file_content = get_lines("tiles.txt")
tile_file_content = np.array(tile_file_content)


print "===="
tiles = get_tiles(tile_file_content)
# random.shuffle(tiles)
tile_index_to_prior = np.ones(len(tiles)) / len(tiles)
build_transition_matrices(tiles)
import time
t1 = time.time()

spheres = create_spheres(tiles)
print time.time() - t1, "to build tiles"
quit()
show_tiles(tiles)
report_on_sphere(0, spheres, tiles)
# quit()

# quit()
print "===SPHERES===="
print spheres.shape
print spheres[0,:,:,0]
print spheres[0,:,:,1]

print "===="
print spheres[1,:,:,0]
print spheres[1,:,:,1]

# show_tiles()
# print potential(tiles[1], tiles[1], 1,0)
# print potential(tiles[1], tiles[1], 0,1)
# print potential(tiles[0], tiles[1], 1,0)
# print potential(tiles[0], tiles[1], 0,1)
# quit()

world = np.zeros((WORLD_WIDTH,WORLD_WIDTH)).astype(np.int32)
probmap = np.ones((WORLD_WIDTH,WORLD_WIDTH, len(tiles))).astype(np.float32)
decided = np.zeros((WORLD_WIDTH,WORLD_WIDTH)).astype(np.int32)


all_coords = []

for i in range(world.shape[0]):
    for j in range(world.shape[1]):
        all_coords.append((i,j))

def report_on_probmap_location(i,j):
    print "=================================="
    print "reporting information about probmap at", i, j
    for tile, p in zip(tiles, probmap[i,j]):
        print tile
        print p
        print
    print "=================================="


# place(2,2, 1)
for _ in range(25):
    i = random.randint(0, WORLD_WIDTH - 1)
    j = random.randint(0, WORLD_WIDTH - 1)
    tile = random.choice(range(len(tiles)))
    place(i,j,tile)

draw_world(world, tiles, mask = decided)

report_on_sphere(2, spheres, tiles)
# print probmap[WORLD_WIDTH / 2,WORLD_WIDTH / 2 - 1]
report_on_probmap_location(WORLD_WIDTH / 2,WORLD_WIDTH / 2 - 1)
# quit()
print "=======START GENERATION=========="

def place_a_tile():
    entropy = np.exp(-np.sum((probmap * np.exp(probmap)) * (probmap > 0) * (decided == 0).reshape(WORLD_WIDTH,WORLD_WIDTH,1), axis = -1))
    entropy += (decided == 1) * np.max(entropy)
    entropy_argmin = np.unravel_index(np.argmin(entropy), entropy.shape)
    i,j = entropy_argmin
    # report_on_probmap_location(i,j)

    # print "entropy"
    # print entropy
    # print "argmin", i,j
    # print "world"
    # print world
    
    ts, ps = range(len(tiles)), probmap[i,j]
    # print "ps", ps
    to_place = np.random.choice(ts, 1, p=np.array(ps))[0]
    # print "placing", to_place, "at", i,j
    place(i,j, to_place)

step=0
while np.prod(decided.shape) - np.sum(decided) > 0:
    step += 1
    place_a_tile()

    # if step % (np.prod(world.shape) / 20) ==0:
    #     draw_world(world, tiles, mask = decided)
        # time.sleep(.3)
    # quit()


def remove_and_redo(k):
    for i in range(WORLD_WIDTH):
        for j in range(WORLD_WIDTH):
            if len(get_all_valid(i,j)) == 0:
                for i1 in range(i-k, i+k):
                    for j1 in range(j-k, j+k):
                        if i1 >= 0 and i1 < WORLD_WIDTH and j1 >=0 and j1 < WORLD_WIDTH:
                            unplace(i1, j1)

    step=0
    while np.prod(decided.shape) - np.sum(decided) > 0:
        step += 1
        place_a_tile()
draw_world(world, tiles, mask = decided)

remove_and_redo(4)

# # draw_world(world, tiles, mask = decided)

# remove_and_redo(10)

# # draw_world(world, tiles, mask = decided)

# remove_and_redo(10)

# # draw_world(world, tiles, mask = decided)

# remove_and_redo(2)
# remove_and_redo(1)
# print '=' * WORLD_WIDTH * 3
draw_world(world, tiles, mask = decided)