# Escribe FUENTES.md: qué archivo original, qué tramo y con qué función aparece en cada lámina.
# Uso: python3 ficha.py   (después de construir.py, que deja capas/clips_usados.json con los tramos exactos)
import os, sys, json
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
from proyecto import FIJAS, PAGINAS, FUNCION
usados = json.load(open(os.path.join(AQUI, "capas", "clips_usados.json")))
L = ["# Ficha de fuentes — carrusel de prelanzamiento v02 (mixto)", "",
     "Todo es material existente de Roccé. Videos: tramos reales que se reproducen dentro de cada ventana (sin cámara lenta, reversa ni zoom agregado).",
     "Ubicación: las tomas del 11 y 12/10/2026 tienen GPS de la costa de Mar del Plata en sus metadatos; las exportaciones no lo llevan.", "",
     "| Lámina | Tipo | Archivo original | Tramo / zona | Función |", "|---|---|---|---|---|"]
usos = {}
for nombre, (orig, caja, salida, uso) in FIJAS.items(): usos.setdefault(nombre[1:3], []).append((orig, caja, uso))
for n, pag in PAGINAS.items():
    tipo = "MP4" if pag["tipo"] == "mp4" else "PNG"
    for c in usados.get(n, []):
        toma = os.path.basename(c["toma"]).replace(".mov", "")
        L.append(f"| {n} | {tipo} · ventana {c['ventana']} | `{c['toma']}` | {c['desde']:.2f}–{c['hasta']:.2f} s ({c['cuadros']} cuadros) | {FUNCION.get(toma, 'video')} |")
    for orig, caja, uso in usos.get(n, []):
        zona = f"fotograma {orig.split('@')[1]} s, zona {caja}" if "@" in orig else f"zona {caja}"
        L.append(f"| {n} | {tipo} · foto fija | `{orig.split('@')[0]}` | {zona} | {uso} |")
    if n == "08": L.append("| 08 | PNG · logo | `LOGO/rocce_logo.png` | archivo completo, sin cambios | Logo original sobre su mismo fondo (#FEFEFE). |")
open(os.path.join(AQUI, "FUENTES.md"), "w").write("\n".join(L) + "\n"); print("FUENTES.md:", len(L) - 7, "filas")
