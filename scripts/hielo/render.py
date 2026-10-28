# Renderiza la escena guardada por escena.py, cuadro por cuadro (saltea los que ya existen: se puede retomar).
# Uso: bpy-env/bin/python render.py escena.blend SALIDA_DIR desde hasta escala_% muestras
import sys, os, time, bpy
blend, out, f0, f1, esc, mu = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scn = bpy.context.scene; scn.render.resolution_percentage = esc; scn.cycles.samples = mu
os.makedirs(out, exist_ok=True)
for f in range(f0, f1 + 1):
    p = os.path.join(os.path.abspath(out), f"{f:04d}.png")
    if os.path.exists(p): continue
    scn.frame_set(f); scn.render.filepath = p
    t0 = time.time(); bpy.ops.render.render(write_still=True); print(f"cuadro {f}: {time.time() - t0:.1f} s", flush=True)
