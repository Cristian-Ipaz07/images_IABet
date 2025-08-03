import argparse
import json
from collections import defaultdict
from pathlib import Path

PLAYERS_FILE = Path('data/players_id.json')
TEAMS_FILE = Path('data/teams_id.json')


def normalizar_entrada(entrada):
    """Normaliza y devuelve (equipo, jugador)"""
    equipo = entrada.get('equipo') or entrada.get('team')
    if not equipo:
        raise ValueError('Entrada sin equipo: %s' % entrada)

    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

    jugador = {
        'id': _to_int(entrada.get('id')),
        'nombre': str(entrada.get('nombre', '')).strip(),
        'dorsal': _to_int(entrada.get('dorsal')),
        'posicion': str(entrada.get('posicion', '')).strip(),
    }

    novato = entrada.get('novato', False)
    if isinstance(novato, str):
        novato = novato.lower() in ('true', '1', 'si', 'sí')

    return equipo, jugador, novato


def cargar_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def guardar_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def remover_jugador(data, jugador_id):
    for equipo, info in data.items():
        jugadores = info.get('jugadores', [])
        info['jugadores'] = [j for j in jugadores if int(j.get('id')) != jugador_id]


def insertar_jugador(data, equipo, jugador):
    if equipo not in data:
        equipos = cargar_json(TEAMS_FILE)
        nombre = equipos.get(equipo, {}).get('nombre', equipo)
        data[equipo] = {'nombre_completo': nombre, 'jugadores': []}
    data[equipo].setdefault('jugadores', []).append(jugador)


def buscar_duplicados(data):
    ids = defaultdict(list)
    for equipo, info in data.items():
        for j in info.get('jugadores', []):
            ids[int(j['id'])].append(equipo)
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
        equipo, jugador, _novato = normalizar_entrada(entrada)
        remover_jugador(jugadores_data, int(jugador['id']))
        insertar_jugador(jugadores_data, equipo, jugador)

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
