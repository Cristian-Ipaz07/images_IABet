import argparse
import json
from collections import defaultdict
from pathlib import Path

PLAYERS_FILE = Path('data/players_id.json')
TEAMS_FILE = Path('data/teams_id.json')


def normalizar_entrada(entrada):
    """Normaliza y devuelve (equipo, jugador_id, nombre)"""
    equipo = entrada.get('equipo') or entrada.get('team')
    if not equipo:
        raise ValueError('Entrada sin equipo: %s' % entrada)

    try:
        jugador_id = int(entrada.get('id'))
    except (TypeError, ValueError):
        raise ValueError('Entrada sin id válido: %s' % entrada)

    nombre = entrada.get('nombre') or entrada.get('name')

    return equipo, jugador_id, nombre


def cargar_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def guardar_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def remover_jugador(data, jugador_id):
    """Elimina al jugador y devuelve su nombre si existe."""
    for equipo, info in data.items():
        jugadores = info.get('jugadores', [])
        for idx, j in enumerate(list(jugadores)):
            jid = j.get('id') if isinstance(j, dict) else int(j)
            if int(jid) == jugador_id:
                nombre = j.get('nombre') if isinstance(j, dict) else None
                jugadores.pop(idx)
                return nombre
    return None


def insertar_jugador(data, equipo, jugador_id, nombre):
    if equipo not in data:
        equipos = cargar_json(TEAMS_FILE)
        nombre_equipo = equipos.get(equipo, {}).get('nombre', equipo)
        data[equipo] = {'nombre_completo': nombre_equipo, 'jugadores': []}
    jugadores = data[equipo].setdefault('jugadores', [])
    if not any(int(j.get('id')) == jugador_id for j in jugadores):
        jugadores.append({'id': jugador_id, 'nombre': nombre})


def buscar_duplicados(data):
    ids = defaultdict(list)
    for equipo, info in data.items():
        for j in info.get('jugadores', []):
            ids[int(j.get('id'))].append(equipo)
    return {i: e for i, e in ids.items() if len(e) > 1}


def main():
    parser = argparse.ArgumentParser(description='Aplica un diff al roster de jugadores')
    parser.add_argument('--diff', required=True, help='Archivo JSON con los cambios')
    parser.add_argument('--players-file', default=str(PLAYERS_FILE), help='Archivo JSON de jugadores existente')
    args = parser.parse_args()

    jugadores_data = cargar_json(args.players_file)

    with open(args.diff, encoding='utf-8') as f:
        diff_data = json.load(f)

    cambios = []
    if isinstance(diff_data, list):
        cambios = diff_data
    elif isinstance(diff_data, dict):
        for equipo, jugadores in diff_data.items():
            for j in jugadores:
                j['equipo'] = equipo
                cambios.append(j)
    else:
        raise ValueError('Formato de diff no soportado')

    for entrada in cambios:
        equipo, jugador_id, nombre = normalizar_entrada(entrada)
        previo = remover_jugador(jugadores_data, jugador_id)
        insertar_jugador(jugadores_data, equipo, jugador_id, nombre or previo or '')

    duplicados = buscar_duplicados(jugadores_data)
    if duplicados:
        print('IDs duplicados encontrados:')
        for i, equipos in duplicados.items():
            print(f'  {i}: {", ".join(equipos)}')
    else:
        print('No se encontraron IDs duplicados.')

    guardar_json(args.players_file, jugadores_data)


if __name__ == '__main__':
    main()
