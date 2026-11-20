#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un mundo SDF 1.10 (Gazebo Harmonic) con un laberinto para probar
SLAM (rtabmap RGB-D) y Nav2 con un robot de 0.80 x 0.66 m.

Uso:
    python3 generar_laberinto.py --base delorian.sdf --salida laberinto.sdf \
        [--filas 6 --columnas 6 --celda 2.5 --semilla 7 --lazos 0.15]
"""

import argparse
import random
import math
import xml.etree.ElementTree as ET


# ---------------------------------------------------------------------------
# Paleta de 12 colores saturados y variados (RGBA)
# ---------------------------------------------------------------------------
PALETA = [
    (0.90, 0.10, 0.10, 1.0),  # rojo
    (0.10, 0.70, 0.10, 1.0),  # verde
    (0.10, 0.20, 0.90, 1.0),  # azul
    (0.95, 0.85, 0.10, 1.0),  # amarillo
    (0.90, 0.45, 0.05, 1.0),  # naranja
    (0.60, 0.10, 0.80, 1.0),  # violeta
    (0.05, 0.80, 0.80, 1.0),  # cian
    (0.90, 0.20, 0.60, 1.0),  # magenta
    (0.40, 0.70, 0.10, 1.0),  # verde lima
    (0.20, 0.40, 0.70, 1.0),  # azul acero
    (0.70, 0.35, 0.15, 1.0),  # marrón anaranjado
    (0.55, 0.55, 0.10, 1.0),  # oliva
]


# ---------------------------------------------------------------------------
# Generación del laberinto (backtracking iterativo)
# ---------------------------------------------------------------------------
def generar_laberinto(filas, columnas, rng):
    """
    Devuelve (paredes_h, paredes_v) donde:
      paredes_h[f][c] = True si hay pared horizontal entre (f-1,c) y (f,c)
                        (es decir, en el borde superior de la celda (f,c))
      paredes_v[f][c] = True si hay pared vertical entre (f,c-1) y (f,c)
                        (borde izquierdo de la celda (f,c))
    Se usan matrices de tamaño (filas+1) x columnas y filas x (columnas+1).
    """
    # Paredes horizontales: (filas+1) x columnas
    ph = [[True] * columnas for _ in range(filas + 1)]
    # Paredes verticales: filas x (columnas+1)
    pv = [[True] * (columnas + 1) for _ in range(filas)]

    visitado = [[False] * columnas for _ in range(filas)]

    # Backtracking iterativo con pila
    inicio = (0, 0)
    visitado[0][0] = True
    pila = [inicio]

    while pila:
        f, c = pila[-1]
        # Vecinos no visitados
        vecinos = []
        if f > 0 and not visitado[f - 1][c]:
            vecinos.append((f - 1, c, 'N'))
        if f < filas - 1 and not visitado[f + 1][c]:
            vecinos.append((f + 1, c, 'S'))
        if c > 0 and not visitado[f][c - 1]:
            vecinos.append((f, c - 1, 'O'))
        if c < columnas - 1 and not visitado[f][c + 1]:
            vecinos.append((f, c + 1, 'E'))

        if not vecinos:
            pila.pop()
            continue

        nf, nc, dir_ = rng.choice(vecinos)
        # Quitar la pared correspondiente
        if dir_ == 'N':
            ph[f][c] = False          # pared entre (f-1,c) y (f,c)
        elif dir_ == 'S':
            ph[f + 1][c] = False      # pared entre (f,c) y (f+1,c)
        elif dir_ == 'O':
            pv[f][c] = False          # pared entre (f,c-1) y (f,c)
        elif dir_ == 'E':
            pv[f][c + 1] = False      # pared entre (f,c) y (f,c+1)

        visitado[nf][nc] = True
        pila.append((nf, nc))

    return ph, pv


def abrir_lazos(ph, pv, filas, columnas, fraccion, rng):
    """Quita aleatoriamente una fracción de las paredes interiores restantes."""
    interiores = []
    # Paredes horizontales interiores: f en 1..filas-1
    for f in range(1, filas):
        for c in range(columnas):
            if ph[f][c]:
                interiores.append(('H', f, c))
    # Paredes verticales interiores: c en 1..columnas-1
    for f in range(filas):
        for c in range(1, columnas):
            if pv[f][c]:
                interiores.append(('V', f, c))

    n_quitar = int(round(fraccion * len(interiores)))
    if n_quitar <= 0:
        return
    elegidas = rng.sample(interiores, n_quitar)
    for tipo, f, c in elegidas:
        if tipo == 'H':
            ph[f][c] = False
        else:
            pv[f][c] = False


# ---------------------------------------------------------------------------
# Utilidades SDF
# ---------------------------------------------------------------------------
def crear_material(color):
    mat = ET.Element('material')
    amb = ET.SubElement(mat, 'ambient')
    amb.text = ' '.join(f'{v:.3f}' for v in color)
    dif = ET.SubElement(mat, 'diffuse')
    dif.text = ' '.join(f'{v:.3f}' for v in color)
    spec = ET.SubElement(mat, 'specular')
    spec.text = '0.1 0.1 0.1 1'
    return mat


def crear_visual(nombre, tam, pose, color):
    """Crea un <visual> con geometría de caja."""
    vis = ET.Element('visual', {'name': nombre})
    pose_el = ET.SubElement(vis, 'pose')
    pose_el.text = ' '.join(f'{v:.4f}' for v in pose)
    geom = ET.SubElement(vis, 'geometry')
    box = ET.SubElement(geom, 'box')
    size = ET.SubElement(box, 'size')
    size.text = f'{tam[0]:.4f} {tam[1]:.4f} {tam[2]:.4f}'
    vis.append(crear_material(color))
    return vis


def crear_collision(nombre, tam, pose):
    col = ET.Element('collision', {'name': nombre})
    pose_el = ET.SubElement(col, 'pose')
    pose_el.text = ' '.join(f'{v:.4f}' for v in pose)
    geom = ET.SubElement(col, 'geometry')
    box = ET.SubElement(geom, 'box')
    size = ET.SubElement(box, 'size')
    size.text = f'{tam[0]:.4f} {tam[1]:.4f} {tam[2]:.4f}'
    return col


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description='Genera un laberinto SDF para Gazebo Harmonic.')
    ap.add_argument('--base', required=True, help='SDF base (p.ej. delorian.sdf)')
    ap.add_argument('--salida', required=True, help='SDF de salida')
    ap.add_argument('--filas', type=int, default=6)
    ap.add_argument('--columnas', type=int, default=6)
    ap.add_argument('--celda', type=float, default=2.5)
    ap.add_argument('--semilla', type=int, default=7)
    ap.add_argument('--lazos', type=float, default=0.15)
    args = ap.parse_args()

    rng = random.Random(args.semilla)

    # --- 1. Leer SDF base y limpiar el world --------------------------------
    tree = ET.parse(args.base)
    root = tree.getroot()

    world = root.find('world')
    if world is None:
        raise SystemExit('El SDF base no contiene <world>.')

    world.set('name', 'laberinto')

    # Eliminar <include>
    for inc in list(world.findall('include')):
        world.remove(inc)

    # Eliminar <model> cuyo name no sea 'ground_plane'
    for mod in list(world.findall('model')):
        if mod.get('name') != 'ground_plane':
            world.remove(mod)

    # --- 2. Generar laberinto ----------------------------------------------
    filas, columnas = args.filas, args.columnas
    celda = args.celda
    ph, pv = generar_laberinto(filas, columnas, rng)
    abrir_lazos(ph, pv, filas, columnas, args.lazos, rng)

    # --- 3. Geometría de paredes -------------------------------------------
    ALTURA = 1.2
    ESPESOR = 0.15
    Z_CENTRO = ALTURA / 2.0
    LONGITUD = celda + ESPESOR  # para cerrar esquinas

    # Abertura de salida: lado exterior +x de la celda (filas-1, columnas-1)
    # Esa pared es la vertical derecha de la celda (filas-1, columnas-1),
    # es decir pv[filas-1][columnas] (borde derecho de la última columna).
    pv[filas - 1][columnas] = False

    # --- 5. Crear el modelo 'laberinto' ------------------------------------
    modelo = ET.Element('model', {'name': 'laberinto'})
    ET.SubElement(modelo, 'static').text = 'true'
    ET.SubElement(modelo, 'pose').text = '0 0 0 0 0 0'
    link = ET.SubElement(modelo, 'link', {'name': 'link_laberinto'})

    n_paredes = 0
    n_carteles = 0

    def agregar_pared(px, py, sx, sy, idx):
        """Añade una pared (collision + visual) y sus carteles."""
        nonlocal n_paredes, n_carteles
        n_paredes += 1
        nombre = f'pared_{idx}'
        tam = (sx, sy, ALTURA)
        pose = (px, py, Z_CENTRO, 0, 0, 0)

        # Color de la pared
        color_pared = rng.choice(PALETA)

        link.append(crear_collision(f'col_{nombre}', tam, pose))
        link.append(crear_visual(nombre, tam, pose, color_pared))

        # --- Carteles (2 por pared, en ambas caras) ------------------------
        # Determinar orientación: pared horizontal (sx > sy) o vertical
        if sx >= sy:
            # Pared a lo largo de X: caras en ±Y
            largo = sx
            for cara_signo in (+1, -1):
                # Posición aleatoria a lo largo de la pared
                offset = rng.uniform(-largo / 2.0 + 0.15, largo / 2.0 - 0.15)
                lado = rng.uniform(0.3, 0.7)
                alto = rng.uniform(0.3, 1.0)
                z = rng.uniform(0.3, 1.0)
                # Espesor 0.02 en Y, pegado a la cara
                y_cartel = py + cara_signo * (sy / 2.0 + 0.01)
                x_cartel = px + offset
                # Color distinto al de la pared
                color_cartel = rng.choice([c for c in PALETA if c != color_pared])
                n_carteles += 1
                nombre_c = f'cartel_{idx}_{"p" if cara_signo > 0 else "n"}'
                tam_c = (lado, 0.02, alto)
                pose_c = (x_cartel, y_cartel, z, 0, 0, 0)
                link.append(crear_visual(nombre_c, tam_c, pose_c, color_cartel))
        else:
            # Pared a lo largo de Y: caras en ±X
            largo = sy
            for cara_signo in (+1, -1):
                offset = rng.uniform(-largo / 2.0 + 0.15, largo / 2.0 - 0.15)
                lado = rng.uniform(0.3, 0.7)
                alto = rng.uniform(0.3, 1.0)
                z = rng.uniform(0.3, 1.0)
                x_cartel = px + cara_signo * (sx / 2.0 + 0.01)
                y_cartel = py + offset
                color_cartel = rng.choice([c for c in PALETA if c != color_pared])
                n_carteles += 1
                nombre_c = f'cartel_{idx}_{"p" if cara_signo > 0 else "n"}'
                tam_c = (0.02, lado, alto)
                pose_c = (x_cartel, y_cartel, z, 0, 0, 0)
                link.append(crear_visual(nombre_c, tam_c, pose_c, color_cartel))

    idx = 0

    # Paredes horizontales: ph[f][c] con f en 0..filas, c en 0..columnas-1
    # Centro de la pared: x = c*celda, y = (f - 0.5)*celda
    for f in range(filas + 1):
        for c in range(columnas):
            if ph[f][c]:
                px = c * celda
                py = (f - 0.5) * celda
                agregar_pared(px, py, LONGITUD, ESPESOR, idx)
                idx += 1

    # Paredes verticales: pv[f][c] con f en 0..filas-1, c en 0..columnas
    # Centro: x = (c - 0.5)*celda, y = f*celda
    for f in range(filas):
        for c in range(columnas + 1):
            if pv[f][c]:
                px = (c - 0.5) * celda
                py = f * celda
                agregar_pared(px, py, ESPESOR, LONGITUD, idx)
                idx += 1

    world.append(modelo)

    # --- 6. Conos en dead ends ---------------------------------------------
    # Un dead end es una celda con exactamente 3 paredes (1 sola salida).
    dead_ends = []
    for f in range(filas):
        for c in range(columnas):
            if (f, c) == (0, 0):
                continue
            # Paredes alrededor de la celda (f,c):
            #   arriba: ph[f][c], abajo: ph[f+1][c]
            #   izquierda: pv[f][c], derecha: pv[f][c+1]
            n_paredes_celda = sum([
                ph[f][c],
                ph[f + 1][c],
                pv[f][c],
                pv[f][c + 1],
            ])
            if n_paredes_celda == 3:
                dead_ends.append((f, c))

    rng.shuffle(dead_ends)
    celdas_conos = dead_ends[:4]

    for i, (f, c) in enumerate(celdas_conos):
        inc = ET.SubElement(world, 'include')
        uri = ET.SubElement(inc, 'uri')
        uri.text = 'https://fuel.gazebosim.org/1.0/OpenRobotics/models/Construction Cone'
        name = ET.SubElement(inc, 'name')
        name.text = f'cono_{i}'
        pose = ET.SubElement(inc, 'pose')
        pose.text = f'{c * celda:.4f} {f * celda:.4f} 0 0 0 0'

    # --- 7. Escribir SDF ---------------------------------------------------
    ET.indent(tree, space='  ')
    tree.write(args.salida, encoding='utf-8', xml_declaration=True)

    # --- Resumen -----------------------------------------------------------
    ancho = columnas * celda
    alto = filas * celda
    salida_x = (columnas - 0.5) * celda + ESPESOR / 2.0
    salida_y = (filas - 1) * celda

    print('=== Laberinto generado ===')
    print(f'Archivo: {args.salida}')
    print(f'Tamaño total: {ancho:.2f} m x {alto:.2f} m (filas={filas}, columnas={columnas}, celda={celda} m)')
    print(f'Número de paredes: {n_paredes}')
    print(f'Número de carteles: {n_carteles}')
    print(f'Celdas con conos: {celdas_conos}')
    print(f'Salida (abertura en +x): x={salida_x:.2f}, y={salida_y:.2f}')


if __name__ == '__main__':
    main()
