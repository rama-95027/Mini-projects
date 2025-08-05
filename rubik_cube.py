import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import time
import math
import numpy as np
import os
import random

# --- Constants ---
CUBE_SIZE = 1
ROTATION_SPEED = 180

face_colors = {
    'U': (1, 1, 1),     # white
    'D': (1, 1, 0),     # yellow
    'F': (0, 1, 0),     # green
    'B': (0, 0, 1),     # blue
    'L': (1, 0.5, 0),   # orange
    'R': (1, 0, 0)      # red
}

face_vectors = {
    'U': (0, 1, 0), 'D': (0, -1, 0),
    'F': (0, 0, 1), 'B': (0, 0, -1),
    'L': (-1, 0, 0), 'R': (1, 0, 0)
}

axis_map = {'U': 1, 'D': 1, 'F': 2, 'B': 2, 'L': 0, 'R': 0}
layer_map = {'U': 1, 'D': -1, 'F': 1, 'B': -1, 'L': -1, 'R': 1}

# --- Cubelet Functions ---
def create_cubelet(x, y, z):
    faces = {}
    if y == 1: faces['U'] = face_colors['U']
    if y == -1: faces['D'] = face_colors['D']
    if z == 1: faces['F'] = face_colors['F']
    if z == -1: faces['B'] = face_colors['B']
    if x == -1: faces['L'] = face_colors['L']
    if x == 1: faces['R'] = face_colors['R']
    return {'pos': [x, y, z], 'faces': faces}

def draw_face(center, normal, color):
    size = 0.8
    u = np.cross(normal, [0.1, 1, 0.3])
    v = np.cross(normal, u)
    u = u / np.linalg.norm(u) * size / 2
    v = v / np.linalg.norm(v) * size / 2
    corners = [
        center + u + v,
        center + u - v,
        center - u - v,
        center - u + v
    ]

    glColor3fv(color)
    glBegin(GL_QUADS)
    for corner in corners:
        glVertex3fv(corner)
    glEnd()

    glColor3fv((0, 0, 0))
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    for corner in corners:
        glVertex3fv(corner)
    glEnd()

def draw_cubelet(cubelet):
    glPushMatrix()
    glTranslatef(*[coord * 1.05 for coord in cubelet['pos']])
    for face, color in cubelet['faces'].items():
        normal = np.array(face_vectors[face])
        center = normal * 0.51
        draw_face(center, normal, color)
    glPopMatrix()

def generate_cube():
    return [create_cubelet(x, y, z)
            for x in [-1, 0, 1]
            for y in [-1, 0, 1]
            for z in [-1, 0, 1]]

# --- Rotation Functions ---
def rotate_vec(vec, axis, angle_deg):
    angle_rad = math.radians(angle_deg)
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    x, y, z = vec

    if axis == 0:
        rot = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    elif axis == 1:
        rot = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    else:
        rot = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    new_vec = np.dot(rot, np.array(vec))
    return [int(round(val)) for val in new_vec]

def rotate_faces(face_map, axis, angle):
    new_map = {}
    for face, color in face_map.items():
        vec = rotate_vec(face_vectors[face], axis, angle)
        for k, v in face_vectors.items():
            if list(vec) == list(v):
                new_map[k] = color
                break
    return new_map

def rotate_layer(cube, face, direction):
    axis = axis_map[face]
    layer_val = layer_map[face]
    angle = direction * 90

    for cubelet in cube:
        if cubelet['pos'][axis] == layer_val:
            cubelet['pos'] = rotate_vec(cubelet['pos'], axis, angle)
            cubelet['faces'] = rotate_faces(cubelet['faces'], axis, angle)

def animate_rotation(cube, face, direction):
    axis = axis_map[face]
    layer_val = layer_map[face]
    angle = direction * 90
    step_angle = angle / 10

    for step in range(10):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        for cubelet in cube:
            glPushMatrix()
            if cubelet['pos'][axis] == layer_val:
                glTranslatef(*[coord * 1.05 for coord in cubelet['pos']])
                glRotatef(step_angle * (step + 1), *(1 if i == axis else 0 for i in range(3)))
                glTranslatef(*[-coord * 1.05 for coord in cubelet['pos']])
            draw_cubelet(cubelet)
            glPopMatrix()
        pygame.display.flip()
        time.sleep(0.03)

    rotate_layer(cube, face, direction)

# --- Main Loop ---
def main(move_sequence):
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Rubik's Cube Visualizer")

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.2, 0.2, 0.2, 1)
    gluPerspective(45, (display[0] / display[1]), 0.1, 100.0)
    glTranslatef(0, 0, -10)
    glRotatef(25, 1, 1, 0)

    cube = generate_cube()
    clock = pygame.time.Clock()
    move_index = 0
    last_time = time.time()

    while True:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        if move_index < len(move_sequence) and time.time() - last_time > 1:
            move = move_sequence[move_index]
            print("Move:", move)
            face = move[0]
            direction = -1 if "'" in move else 1
            animate_rotation(cube, face, direction)
            move_index += 1
            last_time = time.time()

        for cubelet in cube:
            draw_cubelet(cubelet)

        pygame.display.flip()
        clock.tick(60)

# --- Scramble & Solve Logic ---
def invert_move(move):
    return move[:-1] if "'" in move else move + "'"

def generate_scramble(num_moves=20):
    faces = ['U', 'D', 'F', 'B', 'L', 'R']
    modifiers = ['', "'"]
    scramble = []

    last_face = ""
    for _ in range(num_moves):
        face = random.choice(faces)
        while face == last_face:
            face = random.choice(faces)
        last_face = face
        move = face + random.choice(modifiers)
        scramble.append(move)
    return scramble

# --- Run Program ---
if __name__ == "__main__":
    scramble_moves = generate_scramble()
    print("Scramble:", " ".join(scramble_moves))

    with open("moves.txt", "w") as f:
        f.write("Scramble: " + " ".join(scramble_moves) + "\n")

    solving_moves = [invert_move(move) for move in reversed(scramble_moves)]
    full_sequence = scramble_moves + solving_moves

    main(full_sequence)
