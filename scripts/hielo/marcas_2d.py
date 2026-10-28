# Posición en pantalla de cada marca de impacto, cuadro por cuadro: la marca está en la cara de arriba del pedazo
# que contiene el punto del golpe y viaja con él al romperse. Sirve para suavizar esas marcas en 2D exactamente
# donde están (suavizar_marcas.py), también cuando quedan pegadas a un borde.
# Uso: bpy-env/bin/python marcas_2d.py escena.blend escena.json SALIDA.json escala_%
import sys, json, math
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
blend, ej, out, esc = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene; cam = scn.camera
info = json.load(open(ej)); golpes = info["golpes"]; FIN = info["fin"]
W = int(scn.render.resolution_x * esc / 100); H = int(scn.render.resolution_y * esc / 100)
BZ = 0.19
pedazos = [o for o in scn.objects if o.name.startswith("pedazo")]
scn.frame_set(0)
dueños = []
for (f, x, y, rc, rm) in golpes:
    mejor = None
    for p in pedazos:
        M = p.matrix_world.inverted(); o = M @ Vector((x, y, BZ + 0.05)); d = (M.to_3x3() @ Vector((0, 0, -1))).normalized()
        ok, loc, nor, idx = p.ray_cast(o, d, distance=0.2)
        if ok:
            zw = (p.matrix_world @ loc).z
            if mejor is None or zw > mejor[2]: mejor = (p, loc.copy(), zw)
    dueños.append(mejor)
res = {}
for fr in range(0, FIN + 1):
    scn.frame_set(fr); lst = []
    for (f, x, y, rc, rm), d in zip(golpes, dueños):
        if d is None or fr < f: continue
        p, loc, _ = d
        w0 = p.matrix_world @ loc
        w1 = p.matrix_world @ (loc + Vector((rm * 1.9, 0, 0)))
        c0 = world_to_camera_view(scn, cam, w0); c1 = world_to_camera_view(scn, cam, w1)
        if c0.z <= 0: continue
        px, py = c0.x * W, (1 - c0.y) * H
        rad = math.hypot((c1.x - c0.x) * W, (c1.y - c0.y) * H)
        lst.append([round(px, 1), round(py, 1), round(rad, 1)])
    res[fr] = lst
json.dump(res, open(out, "w"))
print("marcas:", sum(len(v) for v in res.values()), "posiciones en", len(res), "cuadros")
