import json
from rapidfuzz import fuzz, process  # pip install rapidfuzz

# Archivos
json_base_path = "data/players_id copy.json"
jugadores_txt_path = "scripts/jugadores.txt"
salida_path = "data/players_id.json"

# Cargar JSON base
with open(json_base_path, "r", encoding="utf-8") as f:
    json_base = json.load(f)

# Cargar jugadores.txt
with open(jugadores_txt_path, "r", encoding="utf-8") as f:
    jugadores_txt = json.load(f)

# Diccionario de referencia {nombre_lower: (id, nombre_correcto)}
referencia = {}
nombres_lista = []
for jugador in jugadores_txt:
    jugador_id = jugador[0]
    apellido = jugador[1]
    nombre = jugador[2]
    nombre_completo = f"{nombre} {apellido}".strip()
    referencia[nombre_completo.lower()] = (jugador_id, nombre_completo)
    nombres_lista.append(nombre_completo)

correcciones = 0
no_encontrados = []

# Comparar y corregir
for equipo, datos in json_base.items():
    for jugador in datos["jugadores"]:
        nombre_jugador = jugador["nombre"].strip()
        nombre_lower = nombre_jugador.lower()

        if nombre_lower in referencia:
            id_correcto, nombre_correcto = referencia[nombre_lower]
            if jugador["id"] != id_correcto:
                jugador["id"] = id_correcto
                correcciones += 1
            jugador["nombre"] = nombre_correcto
        else:
            # Buscar coincidencia aproximada
            mejor_match, score, _ = process.extractOne(nombre_jugador, nombres_lista, scorer=fuzz.token_sort_ratio)
            if score >= 85:  # Umbral de similitud
                id_correcto, nombre_correcto = referencia[mejor_match.lower()]
                jugador["id"] = id_correcto
                jugador["nombre"] = nombre_correcto
                correcciones += 1
            else:
                no_encontrados.append(nombre_jugador)

# Guardar en formato horizontal por jugador
with open(salida_path, "w", encoding="utf-8") as f:
    f.write("{\n")
    for equipo, datos in json_base.items():
        f.write(f'  "{equipo}": {{\n')
        f.write(f'    "nombre_completo": "{datos["nombre_completo"]}",\n')
        f.write(f'    "jugadores": [\n')
        jugadores_linea = [
            f'      {{ "id": {j["id"]}, "nombre": "{j["nombre"]}" }}'
            for j in datos["jugadores"]
        ]
        f.write(",\n".join(jugadores_linea))
        f.write("\n    ]\n")
        f.write("  },\n")
    f.write("}\n")

# Resumen
print(f"Correcciones realizadas: {correcciones}")
if no_encontrados:
    print("Jugadores no encontrados en jugadores.txt:")
    for nombre in no_encontrados:
        print(f" - {nombre}")
