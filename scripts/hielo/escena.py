# ROCCE_01_HIELO_REVELACION — escena 3D (Blender 5.0 como módulo de Python, Cycles en CPU).
# Bloque de hielo sobre cemento, visto desde arriba, con la remera negra real adentro (textura recortada de la foto
# de espalda: Founders Privée + ROCCÉ tono sobre tono). Un hacha golpea cuatro veces: cada golpe abre grietas
# (planos internos que se vuelven visibles alrededor del impacto), deja una marca blanca de hielo molido y suelta
# esquirlas y polvo; el cuarto parte el bloque en pedazos (fractura de Voronoi calculada acá) que salen despedidos y
# se deslizan, y la remera queda libre e intacta. Al final la cámara se acerca a la espalda de la remera.
#
# Uso:  bpy-env/bin/python escena.py TEXTURA_PNG SALIDA_DIR [desde hasta] [escala_%] [muestras]
#       (sin rango: arma la escena, guarda escena.blend y no renderiza)
import sys, os, math, random, json
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, Euler

TEX, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
RANGO = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else None
ESCALA = int(sys.argv[5]) if len(sys.argv) > 5 else 100
MUESTRAS = int(sys.argv[6]) if len(sys.argv) > 6 else 128
os.makedirs(OUT, exist_ok=True)
random.seed(7); rng = np.random.default_rng(7)

FPS = 30
# tiempos (cuadros, 0 = primer cuadro del video)
GOLPES = [  # (cuadro de impacto, punto x, y sobre la cara de arriba, radio de grietas, radio de marca)
    (6, 0.13, 0.10, 0.20, 0.020),
    (26, -0.12, -0.09, 0.24, 0.022),
    (45, 0.05, -0.17, 0.30, 0.025),
    (66, -0.02, 0.02, 0.60, 0.032),     # el último parte el bloque
]
F_ROTURA = GOLPES[-1][0]
F_FIN = 140                             # último cuadro de la escena (4,67 s)

# medidas (m)
BX, BY, BZ = 0.80, 0.76, 0.19           # bloque
TEE_W = 0.64                            # ancho de la remera (manga a manga)
TEE_Z = 0.014                           # altura de la remera dentro del bloque (congelada cerca del fondo)

# ---------------------------------------------------------------- escena base
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = "CYCLES"
scn.cycles.device = "CPU"
scn.cycles.samples = MUESTRAS
scn.cycles.use_adaptive_sampling = True
scn.cycles.adaptive_threshold = 0.025
scn.render.use_persistent_data = True
scn.cycles.use_denoising = True
scn.cycles.denoiser = "OPENIMAGEDENOISE"
scn.cycles.max_bounces = 10
scn.cycles.transmission_bounces = 10
scn.cycles.transparent_max_bounces = 24
scn.cycles.glossy_bounces = 4
scn.cycles.diffuse_bounces = 2
scn.cycles.volume_bounces = 0
scn.cycles.caustics_reflective = False
scn.cycles.caustics_refractive = False
scn.cycles.blur_glossy = 1.0
scn.cycles.sample_clamp_direct = 12.0
scn.cycles.sample_clamp_indirect = 3.0
scn.render.resolution_x, scn.render.resolution_y = 1080, 1920
scn.render.resolution_percentage = ESCALA
scn.render.fps = FPS
scn.render.use_motion_blur = True
scn.render.motion_blur_shutter = 0.45
scn.frame_start, scn.frame_end = 0, F_FIN
scn.view_settings.view_transform = "AgX"
try: scn.view_settings.look = "AgX - Punchy"
except Exception: pass
scn.view_settings.exposure = -0.6
scn.render.image_settings.file_format = "PNG"
scn.render.image_settings.color_depth = "8"
scn.render.threads_mode = "AUTO"

def nodos(mat):
    mat.use_nodes = True; nt = mat.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    return nt, nt.nodes, nt.links

def nodo(nodes, tipo, **kw):
    n = nodes.new(tipo)
    for k, v in kw.items():
        if k in n.inputs: n.inputs[k].default_value = v
        else: setattr(n, k, v)
    return n

# ---------------------------------------------------------------- mundo y luces
w = bpy.data.worlds.new("cielo"); scn.world = w
nt, N, L = nodos(w)
tc = nodo(N, "ShaderNodeTexCoord"); sep = nodo(N, "ShaderNodeSeparateXYZ")
L.new(tc.outputs["Generated"], sep.inputs[0])
ramp = nodo(N, "ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.5; ramp.color_ramp.elements[0].color = (0.75, 0.78, 0.82, 1)
ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (0.10, 0.105, 0.11, 1)   # cenit oscuro: el hielo no refleja un cielo blanco
L.new(sep.outputs["Z"], ramp.inputs[0])
bg = nodo(N, "ShaderNodeBackground", Strength=0.45); L.new(ramp.outputs[0], bg.inputs["Color"])
out = nodo(N, "ShaderNodeOutputWorld"); L.new(bg.outputs[0], out.inputs[0])

def luz_area(nombre, loc, size, power, rot=(0, 0, 0)):
    d = bpy.data.lights.new(nombre, "AREA"); d.size = size; d.energy = power; d.shape = "DISK"
    o = bpy.data.objects.new(nombre, d); o.location = loc; o.rotation_euler = rot; scn.collection.objects.link(o)
    return o
def apuntar(o, tgt=(0, 0, 0.08)):
    d = Vector(tgt) - o.location; o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
apuntar(luz_area("principal", (1.55, 1.25, 1.25), 1.6, 330))     # lateral: su reflejo en la cara de arriba no llega a la cámara
apuntar(luz_area("relleno", (-1.6, -0.7, 1.35), 1.4, 120))
apuntar(luz_area("borde", (-0.3, 1.8, 0.55), 0.9, 70))

# ---------------------------------------------------------------- materiales
def mat_cemento():
    m = bpy.data.materials.new("cemento"); nt, N, L = nodos(m)
    tc = nodo(N, "ShaderNodeTexCoord")
    n1 = nodo(N, "ShaderNodeTexNoise", Scale=9.0, Detail=8.0, Roughness=0.62); L.new(tc.outputs["Object"], n1.inputs["Vector"])
    n2 = nodo(N, "ShaderNodeTexNoise", Scale=140.0, Detail=4.0, Roughness=0.5); L.new(tc.outputs["Object"], n2.inputs["Vector"])
    vor = nodo(N, "ShaderNodeTexVoronoi", Scale=90.0); L.new(tc.outputs["Object"], vor.inputs["Vector"])
    r1 = nodo(N, "ShaderNodeValToRGB"); r1.color_ramp.elements[0].color = (0.205, 0.205, 0.2, 1); r1.color_ramp.elements[1].color = (0.30, 0.30, 0.292, 1)
    r1.color_ramp.elements[0].position = 0.35; r1.color_ramp.elements[1].position = 0.65

    L.new(n1.outputs["Fac"], r1.inputs[0])
    # grano fino del cemento
    ng = nodo(N, "ShaderNodeTexNoise", Scale=420.0, Detail=2.0); L.new(tc.outputs["Object"], ng.inputs["Vector"])
    gm_ = nodo(N, "ShaderNodeMix", data_type="RGBA", blend_type="OVERLAY"); gm_.inputs["Factor"].default_value = 0.35
    L.new(r1.outputs[0], gm_.inputs[6]); L.new(ng.outputs["Color"], gm_.inputs[7])
    # poros oscuros
    rp = nodo(N, "ShaderNodeMath", operation="LESS_THAN"); rp.inputs[1].default_value = 0.06; L.new(vor.outputs["Distance"], rp.inputs[0])
    mixp = nodo(N, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY"); mixp.inputs["Factor"].default_value = 0.0
    L.new(rp.outputs[0], mixp.inputs["Factor"]); L.new(gm_.outputs[2], mixp.inputs[6]); mixp.inputs[7].default_value = (0.55, 0.55, 0.55, 1)
    # zona mojada alrededor del bloque (rectángulo redondeado algo más grande que el bloque)
    sx = nodo(N, "ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    def absx(c, half):
        a = nodo(N, "ShaderNodeMath", operation="ABSOLUTE"); L.new(sx.outputs[c], a.inputs[0])
        s = nodo(N, "ShaderNodeMath", operation="SUBTRACT"); L.new(a.outputs[0], s.inputs[0]); s.inputs[1].default_value = half
        mx = nodo(N, "ShaderNodeMath", operation="MAXIMUM"); L.new(s.outputs[0], mx.inputs[0]); mx.inputs[1].default_value = 0.0
        return mx
    ax, ay = absx("X", BX / 2 - 0.03), absx("Y", BY / 2 - 0.03)
    cx = nodo(N, "ShaderNodeCombineXYZ"); L.new(ax.outputs[0], cx.inputs["X"]); L.new(ay.outputs[0], cx.inputs["Y"])
    ln = nodo(N, "ShaderNodeVectorMath", operation="LENGTH"); L.new(cx.outputs[0], ln.inputs[0])
    nw = nodo(N, "ShaderNodeTexNoise", Scale=6.0, Detail=3.0); L.new(tc.outputs["Object"], nw.inputs["Vector"])
    addn = nodo(N, "ShaderNodeMath", operation="MULTIPLY_ADD"); L.new(nw.outputs["Fac"], addn.inputs[0]); addn.inputs[1].default_value = 0.09; L.new(ln.outputs[0], addn.inputs[2])
    wet = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(addn.outputs[0], wet.inputs["Value"])
    wet.inputs["From Min"].default_value = 0.10; wet.inputs["From Max"].default_value = 0.06
    mixw = nodo(N, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY"); L.new(wet.outputs[0], mixw.inputs["Factor"])
    L.new(mixp.outputs[2], mixw.inputs[6]); mixw.inputs[7].default_value = (0.62, 0.62, 0.64, 1)
    rough = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(wet.outputs[0], rough.inputs["Value"])
    rough.inputs["To Min"].default_value = 0.86; rough.inputs["To Max"].default_value = 0.32
    bump = nodo(N, "ShaderNodeBump", Strength=0.5, Distance=0.002); L.new(n2.outputs["Fac"], bump.inputs["Height"])
    bsdf = nodo(N, "ShaderNodeBsdfPrincipled"); L.new(mixw.outputs[2], bsdf.inputs["Base Color"]); L.new(rough.outputs[0], bsdf.inputs["Roughness"])
    L.new(bump.outputs[0], bsdf.inputs["Normal"])
    o = nodo(N, "ShaderNodeOutputMaterial"); L.new(bsdf.outputs[0], o.inputs["Surface"])
    return m

VALORES = {}   # nodos Value animados (radios de grietas y marcas)
def valor(N, nombre, v=0.0):
    n = nodo(N, "ShaderNodeValue"); n.outputs[0].default_value = v; n.label = nombre
    VALORES.setdefault(nombre, []).append(n); return n

def distancia_a(N, L, pos, x, y, z):
    d = nodo(N, "ShaderNodeVectorMath", operation="DISTANCE"); L.new(pos, d.inputs[0]); d.inputs[1].default_value = (x, y, z)
    return d

def volumen_hielo(N, L):
    tc = nodo(N, "ShaderNodeTexCoord")
    nz = nodo(N, "ShaderNodeTexNoise", Scale=7.0, Detail=6.0, Roughness=0.6); L.new(tc.outputs["Object"], nz.inputs["Vector"])
    rr = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(nz.outputs["Fac"], rr.inputs["Value"])
    rr.inputs["From Min"].default_value = 0.52; rr.inputs["From Max"].default_value = 0.75
    rr.inputs["To Min"].default_value = 0.6; rr.inputs["To Max"].default_value = 9.0
    vol = nodo(N, "ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (0.93, 0.96, 1.0, 1)
    vol.inputs["Absorption Color"].default_value = (0.86, 0.93, 0.97, 1); vol.inputs["Anisotropy"].default_value = 0.35
    L.new(rr.outputs[0], vol.inputs["Density"])
    return vol

def sombra_parcial(N, L, sup, paso=0.65):
    """Sin cáusticas: para los rayos de sombra el hielo deja pasar parte de la luz (sombra suave, no negra)."""
    lp = nodo(N, "ShaderNodeLightPath"); f = nodo(N, "ShaderNodeMath", operation="MULTIPLY"); f.inputs[1].default_value = paso
    L.new(lp.outputs["Is Shadow Ray"], f.inputs[0])
    tr = nodo(N, "ShaderNodeBsdfTransparent"); m = nodo(N, "ShaderNodeMixShader")
    L.new(f.outputs[0], m.inputs[0]); L.new(sup, m.inputs[1]); L.new(tr.outputs[0], m.inputs[2]); return m.outputs[0]

def pos0(N, L):
    """Posición original (en el bloque entero) guardada en cada vértice: las texturas quedan pegadas a cada pedazo."""
    a = nodo(N, "ShaderNodeAttribute"); a.attribute_type = "GEOMETRY"; a.attribute_name = "pos0"
    return a.outputs["Vector"]

def gen0(N, L):
    v = nodo(N, "ShaderNodeVectorMath", operation="MULTIPLY_ADD"); L.new(pos0(N, L), v.inputs[0])
    v.inputs[1].default_value = (1 / BX, 1 / BY, 1 / BZ); v.inputs[2].default_value = (0.5, 0.5, 0.0)
    return v.outputs[0]

def mat_hielo(nombre="hielo"):
    m = bpy.data.materials.new(nombre); nt, N, L = nodos(m)
    geo = nodo(N, "ShaderNodeNewGeometry"); tc = nodo(N, "ShaderNodeTexCoord")
    # escarcha: más cerca de los bordes del bloque y en manchas
    g = nodo(N, "ShaderNodeSeparateXYZ"); L.new(gen0(N, L), g.inputs[0])
    def borde(c):
        a = nodo(N, "ShaderNodeMath", operation="SUBTRACT"); a.inputs[0].default_value = 0.5; L.new(g.outputs[c], a.inputs[1])
        b = nodo(N, "ShaderNodeMath", operation="ABSOLUTE"); L.new(a.outputs[0], b.inputs[0]); return b
    mxb = nodo(N, "ShaderNodeMath", operation="MAXIMUM"); L.new(borde("X").outputs[0], mxb.inputs[0]); L.new(borde("Y").outputs[0], mxb.inputs[1])
    nf = nodo(N, "ShaderNodeTexNoise", Scale=11.0, Detail=10.0, Roughness=0.68); L.new(pos0(N, L), nf.inputs["Vector"])
    ad = nodo(N, "ShaderNodeMath", operation="MULTIPLY_ADD"); L.new(nf.outputs["Fac"], ad.inputs[0]); ad.inputs[1].default_value = 0.32; L.new(mxb.outputs[0], ad.inputs[2])
    frost = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(ad.outputs[0], frost.inputs["Value"])
    frost.inputs["From Min"].default_value = 0.60; frost.inputs["From Max"].default_value = 0.80
    # marcas blancas de los golpes (hielo molido): estrella irregular con rayos (grietas finas) y grano
    marca = None
    for i, (f, x, y, rc, rm) in enumerate(GOLPES):
        rel = nodo(N, "ShaderNodeVectorMath", operation="SUBTRACT"); L.new(pos0(N, L), rel.inputs[0]); rel.inputs[1].default_value = (x, y, BZ)
        sp = nodo(N, "ShaderNodeSeparateXYZ"); L.new(rel.outputs[0], sp.inputs[0])
        ang = nodo(N, "ShaderNodeMath", operation="ARCTAN2"); L.new(sp.outputs["Y"], ang.inputs[0]); L.new(sp.outputs["X"], ang.inputs[1])
        d = nodo(N, "ShaderNodeVectorMath", operation="LENGTH"); L.new(rel.outputs[0], d.inputs[0])
        ray = nodo(N, "ShaderNodeTexNoise", noise_dimensions="1D", Scale=2.6, Detail=4.0, Roughness=0.75); ray.inputs["W"].default_value = 0.0
        aw = nodo(N, "ShaderNodeMath", operation="MULTIPLY_ADD"); L.new(ang.outputs[0], aw.inputs[0]); aw.inputs[1].default_value = 1.0; aw.inputs[2].default_value = 17.3 * i
        L.new(aw.outputs[0], ray.inputs["W"])
        spike = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(ray.outputs["Fac"], spike.inputs["Value"])
        spike.inputs["From Min"].default_value = 0.35; spike.inputs["From Max"].default_value = 0.75
        spike.inputs["To Min"].default_value = 0.45; spike.inputs["To Max"].default_value = 1.9
        r = valor(N, f"marca{i}")
        rr = nodo(N, "ShaderNodeMath", operation="MULTIPLY"); L.new(r.outputs[0], rr.inputs[0]); L.new(spike.outputs[0], rr.inputs[1])
        diff = nodo(N, "ShaderNodeMath", operation="SUBTRACT"); L.new(rr.outputs[0], diff.inputs[0]); L.new(d.outputs["Value"], diff.inputs[1])
        soft = nodo(N, "ShaderNodeMath", operation="DIVIDE"); L.new(diff.outputs[0], soft.inputs[0]); soft.inputs[1].default_value = 0.012
        cl = nodo(N, "ShaderNodeClamp"); L.new(soft.outputs[0], cl.inputs["Value"])
        gr = nodo(N, "ShaderNodeTexNoise", Scale=260.0, Detail=2.0); L.new(pos0(N, L), gr.inputs["Vector"])
        grm = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(gr.outputs["Fac"], grm.inputs["Value"])
        grm.inputs["To Min"].default_value = 0.45; grm.inputs["To Max"].default_value = 1.0
        mm = nodo(N, "ShaderNodeMath", operation="MULTIPLY"); L.new(cl.outputs[0], mm.inputs[0]); L.new(grm.outputs[0], mm.inputs[1])
        if marca is None: marca = mm
        else:
            mx = nodo(N, "ShaderNodeMath", operation="MAXIMUM"); L.new(marca.outputs[0], mx.inputs[0]); L.new(mm.outputs[0], mx.inputs[1]); marca = mx
    rough = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(frost.outputs[0], rough.inputs["Value"])
    rough.inputs["To Min"].default_value = 0.0; rough.inputs["To Max"].default_value = 0.45
    tw = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(frost.outputs[0], tw.inputs["Value"])
    tw.inputs["To Min"].default_value = 1.0; tw.inputs["To Max"].default_value = 0.55
    nbump = nodo(N, "ShaderNodeTexNoise", Scale=38.0, Detail=8.0, Roughness=0.7); L.new(pos0(N, L), nbump.inputs["Vector"])
    bump = nodo(N, "ShaderNodeBump", Strength=0.07, Distance=0.004); L.new(nbump.outputs["Fac"], bump.inputs["Height"])
    bsdf = nodo(N, "ShaderNodeBsdfPrincipled", IOR=1.31)
    bsdf.inputs["Base Color"].default_value = (0.94, 0.97, 1.0, 1)
    L.new(rough.outputs[0], bsdf.inputs["Roughness"]); L.new(tw.outputs[0], bsdf.inputs["Transmission Weight"]); L.new(bump.outputs[0], bsdf.inputs["Normal"])
    blanco = nodo(N, "ShaderNodeBsdfDiffuse"); blanco.inputs["Color"].default_value = (0.92, 0.94, 0.96, 1); blanco.inputs["Roughness"].default_value = 0.6
    mix = nodo(N, "ShaderNodeMixShader"); L.new(marca.outputs[0], mix.inputs[0]); L.new(bsdf.outputs[0], mix.inputs[1]); L.new(blanco.outputs[0], mix.inputs[2])
    o = nodo(N, "ShaderNodeOutputMaterial"); L.new(sombra_parcial(N, L, mix.outputs[0]), o.inputs["Surface"])
    return m

def mat_grieta():
    # caras internas de la fractura: invisibles hasta que la grieta llega (radio animado por golpe); después,
    # planos plateados/blancos parciales (reflexión interna) con bordes irregulares
    m = bpy.data.materials.new("grieta"); nt, N, L = nodos(m)
    geo = nodo(N, "ShaderNodeNewGeometry"); tc = nodo(N, "ShaderNodeTexCoord")
    vis = None
    for i, (f, x, y, rc, rm) in enumerate(GOLPES):
        d = distancia_a(N, L, pos0(N, L), x, y, BZ)
        r = valor(N, f"grieta{i}")
        mm = nodo(N, "ShaderNodeMath", operation="LESS_THAN"); L.new(d.outputs["Value"], mm.inputs[0]); L.new(r.outputs[0], mm.inputs[1])
        if vis is None: vis = mm
        else:
            mx = nodo(N, "ShaderNodeMath", operation="MAXIMUM"); L.new(vis.outputs[0], mx.inputs[0]); L.new(mm.outputs[0], mx.inputs[1]); vis = mx
    tot = valor(N, "grieta_total")          # después de la rotura todas las caras son superficie de hielo partido
    mx = nodo(N, "ShaderNodeMath", operation="MAXIMUM"); L.new(vis.outputs[0], mx.inputs[0]); L.new(tot.outputs[0], mx.inputs[1]); vis = mx
    nz = nodo(N, "ShaderNodeTexNoise", Scale=24.0, Detail=9.0, Roughness=0.7); L.new(pos0(N, L), nz.inputs["Vector"])
    patch = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(nz.outputs["Fac"], patch.inputs["Value"])
    patch.inputs["From Min"].default_value = 0.40; patch.inputs["From Max"].default_value = 0.62
    patch.inputs["To Min"].default_value = 0.08; patch.inputs["To Max"].default_value = 0.55
    fac = nodo(N, "ShaderNodeMath", operation="MULTIPLY"); L.new(vis.outputs[0], fac.inputs[0]); L.new(patch.outputs[0], fac.inputs[1])
    # cuando está suelta (pedazo), la cara de corte es hielo áspero: superficie refractiva + escarcha
    trans = nodo(N, "ShaderNodeBsdfTransparent")
    gl = nodo(N, "ShaderNodeBsdfGlossy"); gl.inputs["Color"].default_value = (0.95, 0.97, 1.0, 1); gl.inputs["Roughness"].default_value = 0.04
    dif = nodo(N, "ShaderNodeBsdfDiffuse"); dif.inputs["Color"].default_value = (0.9, 0.93, 0.96, 1)
    mixc = nodo(N, "ShaderNodeMixShader"); mixc.inputs[0].default_value = 0.22; L.new(gl.outputs[0], mixc.inputs[1]); L.new(dif.outputs[0], mixc.inputs[2])
    mix = nodo(N, "ShaderNodeMixShader"); L.new(fac.outputs[0], mix.inputs[0]); L.new(trans.outputs[0], mix.inputs[1]); L.new(mixc.outputs[0], mix.inputs[2])
    # superficie de pedazo suelto
    sep = valor(N, "suelto")
    ice = nodo(N, "ShaderNodeBsdfPrincipled", IOR=1.31); ice.inputs["Transmission Weight"].default_value = 0.8
    ice.inputs["Base Color"].default_value = (0.94, 0.97, 1.0, 1)
    rgh = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(nz.outputs["Fac"], rgh.inputs["Value"])
    rgh.inputs["To Min"].default_value = 0.12; rgh.inputs["To Max"].default_value = 0.5; L.new(rgh.outputs[0], ice.inputs["Roughness"])
    bump = nodo(N, "ShaderNodeBump", Strength=0.45, Distance=0.004); L.new(nz.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs[0], ice.inputs["Normal"])
    blanc = nodo(N, "ShaderNodeBsdfDiffuse"); blanc.inputs["Color"].default_value = (0.9, 0.92, 0.95, 1)
    wm = nodo(N, "ShaderNodeMapRange", clamp=True); L.new(nz.outputs["Fac"], wm.inputs["Value"])
    wm.inputs["From Min"].default_value = 0.5; wm.inputs["From Max"].default_value = 0.7; wm.inputs["To Max"].default_value = 0.45
    icem = nodo(N, "ShaderNodeMixShader"); L.new(wm.outputs[0], icem.inputs[0]); L.new(ice.outputs[0], icem.inputs[1]); L.new(blanc.outputs[0], icem.inputs[2])
    mixs = nodo(N, "ShaderNodeMixShader"); L.new(sep.outputs[0], mixs.inputs[0]); L.new(mix.outputs[0], mixs.inputs[1]); L.new(icem.outputs[0], mixs.inputs[2])
    o = nodo(N, "ShaderNodeOutputMaterial"); L.new(sombra_parcial(N, L, mixs.outputs[0]), o.inputs["Surface"])
    return m

def mat_burbuja():
    m = bpy.data.materials.new("burbuja"); nt, N, L = nodos(m)
    b = nodo(N, "ShaderNodeBsdfPrincipled", IOR=0.77, Roughness=0.0); b.inputs["Transmission Weight"].default_value = 1.0
    o = nodo(N, "ShaderNodeOutputMaterial"); L.new(b.outputs[0], o.inputs["Surface"]); return m

def mat_remera():
    m = bpy.data.materials.new("remera"); nt, N, L = nodos(m)
    img = bpy.data.images.load(TEX); img.colorspace_settings.name = "sRGB"
    t = nodo(N, "ShaderNodeTexImage"); t.image = img; t.interpolation = "Cubic"
    gm = nodo(N, "ShaderNodeGamma", Gamma=1.25); L.new(t.outputs["Color"], gm.inputs["Color"])
    b = nodo(N, "ShaderNodeBsdfPrincipled", Roughness=0.78); L.new(gm.outputs[0], b.inputs["Base Color"])
    b.inputs["Sheen Weight"].default_value = 0.12; b.inputs["Sheen Roughness"].default_value = 0.6
    tr = nodo(N, "ShaderNodeBsdfTransparent")
    mix = nodo(N, "ShaderNodeMixShader"); L.new(t.outputs["Alpha"], mix.inputs[0]); L.new(tr.outputs[0], mix.inputs[1]); L.new(b.outputs[0], mix.inputs[2])
    o = nodo(N, "ShaderNodeOutputMaterial"); L.new(mix.outputs[0], o.inputs["Surface"])
    return m, img

def mat_simple(nombre, color, metal=0.0, rough=0.5, trans=0.0, ior=1.45):
    m = bpy.data.materials.new(nombre); nt, N, L = nodos(m)
    b = nodo(N, "ShaderNodeBsdfPrincipled", Metallic=metal, Roughness=rough, IOR=ior)
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Transmission Weight"].default_value = trans
    o = nodo(N, "ShaderNodeOutputMaterial"); L.new(b.outputs[0], o.inputs["Surface"]); return m

M_CEM, M_HIELO, M_GRIETA, M_BURB = mat_cemento(), mat_hielo(), mat_grieta(), mat_burbuja()
M_REM, IMG = mat_remera()
M_ACERO = mat_simple("acero", (0.025, 0.025, 0.027), 1.0, 0.33)
M_FILO = mat_simple("filo", (0.62, 0.63, 0.65), 1.0, 0.18)
M_MANGO = mat_simple("mango", (0.012, 0.012, 0.013), 0.0, 0.8)
M_ESQ = mat_simple("esquirla", (0.9, 0.92, 0.95), 0.0, 0.45, 0.0, 1.31)   # hielo molido: blanco, sin transmisión (evita destellos)
M_POLVO = mat_simple("polvo", (0.93, 0.95, 0.97), 0.0, 0.7)
_b = M_POLVO.node_tree.nodes["Principled BSDF"]; _b.inputs["Emission Color"].default_value = (1, 1, 1, 1); _b.inputs["Emission Strength"].default_value = 0.35

def objeto(nombre, me, mats=()):
    o = bpy.data.objects.new(nombre, me); scn.collection.objects.link(o)
    for m in mats: o.data.materials.append(m)
    return o

# ---------------------------------------------------------------- piso
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3.0)
me = bpy.data.meshes.new("piso"); bm.to_mesh(me); bm.free()
piso = objeto("piso", me, [M_CEM])

# ---------------------------------------------------------------- remera (plano subdividido con el contorno real)
aspect = IMG.size[1] / IMG.size[0]
TEE_H = TEE_W * aspect
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=160, y_segments=int(160 * aspect), size=0.5)
uv = bm.loops.layers.uv.new("UVMap")
for f in bm.faces:
    for lo in f.loops:
        co = lo.vert.co; lo[uv].uv = (co.x + 0.5, co.y + 0.5)
for v in bm.verts:
    u, vv = v.co.x + 0.5, v.co.y + 0.5
    v.co.x, v.co.y = (u - 0.5) * TEE_W, (vv - 0.5) * TEE_H
me = bpy.data.meshes.new("remera"); bm.to_mesh(me); bm.free()
remera = objeto("remera", me, [M_REM])
remera.location = (0.0, -0.005, TEE_Z); remera.rotation_euler = (0, 0, math.radians(-2.0))
# relieve suave: arrugas (ruido) + el propio sombreado de la foto (los pliegues reales)
tex_n = bpy.data.textures.new("arrugas", "CLOUDS"); tex_n.noise_scale = 0.09; tex_n.noise_depth = 2
dm = remera.modifiers.new("arrugas", "DISPLACE"); dm.texture = tex_n; dm.strength = 0.003; dm.mid_level = 0.5; dm.texture_coords = "LOCAL"


# ---------------------------------------------------------------- bloque (redondeado, apenas irregular)
def bloque_mesh():
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * BX, v.co.y * BY, (v.co.z + 0.5) * BZ))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.028, segments=5, profile=0.5, affect="EDGES")
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=2, use_grid_fill=True)
    for v in bm.verts:   # ondulación leve (hielo de molde, no un vidrio perfecto)
        p = v.co
        if p.z > 0.004:
            p.z += 0.004 * math.sin(p.x * 13 + 1.3) * math.sin(p.y * 11 + 0.4) * (p.z / BZ)
            p.x += 0.003 * math.sin(p.y * 9 + p.z * 20)
            p.y += 0.003 * math.sin(p.x * 8 + 2.0)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new("bloque"); bm.to_mesh(me); bm.free(); return me

# semillas de la fractura: más densas cerca de los impactos
semillas = []
for (f, x, y, rc, rm) in GOLPES:
    k = 5 if f != F_ROTURA else 11
    for j in range(k):
        ang = 2 * math.pi * j / k + rng.uniform(-0.3, 0.3); r = rng.uniform(0.04, rc * (0.55 if f != F_ROTURA else 0.4))
        semillas.append((x + r * math.cos(ang), y + r * math.sin(ang), BZ / 2 + rng.uniform(-0.012, 0.012)))   # planos de grieta casi verticales
for j in range(10):
    semillas.append((rng.uniform(-BX / 2 + 0.05, BX / 2 - 0.05), rng.uniform(-BY / 2 + 0.05, BY / 2 - 0.05), BZ / 2 + rng.uniform(-0.015, 0.015)))
semillas = [Vector(s) for s in semillas]
semillas = [s for s in semillas if abs(s.x) < BX / 2 - 0.02 and abs(s.y) < BY / 2 - 0.02]

def celda(i):
    s = semillas[i]
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * (BX + 0.2), v.co.y * (BY + 0.2), v.co.z * (BZ + 0.2) + BZ / 2))
    for j, o in enumerate(semillas):
        if j == i: continue
        n = (o - s).normalized(); mid = (o + s) / 2
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=mid, plane_no=n, clear_outer=True)
        bordes = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if bordes:
            try: bmesh.ops.holes_fill(bm, edges=bordes, sides=0)
            except Exception: pass
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new(f"celda{i}"); bm.to_mesh(me); bm.free(); return me

bloque_base = objeto("bloque_base", bloque_mesh(), [M_HIELO]); bloque_base.hide_render = True; bloque_base.hide_viewport = True
pedazos = []
for i in range(len(semillas)):
    c = objeto(f"pedazo{i:02d}", celda(i), [M_GRIETA])
    b = c.modifiers.new("corte", "BOOLEAN"); b.operation = "INTERSECT"; b.solver = "EXACT"; b.object = bloque_base
    try: b.material_mode = "TRANSFER"
    except Exception: pass
    bpy.context.view_layer.objects.active = c
    with bpy.context.temp_override(object=c, active_object=c):
        bpy.ops.object.modifier_apply(modifier=b.name)
    if len(c.data.vertices) < 4: bpy.data.objects.remove(c); continue
    at = c.data.attributes.new("pos0", "FLOAT_VECTOR", "POINT")
    at.data.foreach_set("vector", [q for v in c.data.vertices for q in v.co])
    # origen en el centro de masa aproximado (para girar bien)
    cen = sum((v.co for v in c.data.vertices), Vector()) / len(c.data.vertices)
    c.data.transform(Matrix.Translation(-cen)); c.location = cen
    c.data.shade_smooth() if False else None
    pedazos.append(c)
print("pedazos:", len(pedazos))

# (sin burbujas: a la resolución de salida no se distinguen y producían destellos)

# ---------------------------------------------------------------- hacha (cabeza negra con filo de acero, mango negro)
# Marco local: el mango va por +X (de la cabeza a la mano, 0,46 m); el filo apunta a -Z; el espesor de la cabeza va en Y.
def hacha():
    bm = bmesh.new()
    perfil = [(-0.032, 0.035), (0.030, 0.035), (0.034, -0.02), (0.052, -0.085), (0.060, -0.118),
              (-0.070, -0.118), (-0.060, -0.09), (-0.040, -0.03)]          # (x, z), filo abajo
    def esp(z):            # espesor: lleno en el ojo, cuña hacia el filo
        return 0.028 if z > -0.02 else max(0.0015, 0.028 * (z + 0.118) / 0.098)
    top = [bm.verts.new((x, esp(z) / 2, z)) for x, z in perfil]
    bot = [bm.verts.new((x, -esp(z) / 2, z)) for x, z in perfil]
    bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    n = len(perfil)
    for k in range(n): bm.faces.new((top[k], top[(k + 1) % n], bot[(k + 1) % n], bot[k]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new("cabeza"); bm.to_mesh(me); bm.free()
    cab = objeto("cabeza", me, [M_ACERO, M_FILO])
    for p in cab.data.polygons:
        if p.center.z < -0.095: p.material_index = 1
    bev = cab.modifiers.new("bisel", "BEVEL"); bev.width = 0.0025; bev.segments = 2
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.0155, radius2=0.018, depth=0.44)
    for v in bm.verts: v.co = Vector((v.co.z + 0.24, v.co.y, v.co.x * 1.15))     # a lo largo de +X, ovalado
    me = bpy.data.meshes.new("mango"); bm.to_mesh(me); bm.free()
    man = objeto("mango", me, [M_MANGO]); man.parent = cab
    man.data.shade_smooth()
    return cab
CAB = hacha()
GRIP = Vector((0.43, 0.0, 0.0))          # la mano (fuera de cuadro)

def matriz_contacto(ix, iy, yaw_deg, incl_deg, roll_deg):
    """Hacha apoyada con el filo en (ix, iy, BZ): mango hacia (yaw), subiendo (incl) hacia la mano, cabeza girada (roll)."""
    yaw, inc, rol = map(math.radians, (yaw_deg, incl_deg, roll_deg))
    X = Vector((math.cos(yaw) * math.cos(inc), math.sin(yaw) * math.cos(inc), math.sin(inc)))
    down = Vector((0, 0, -1)); Zn = -(down - X * down.dot(X)).normalized()      # +Z local hacia arriba (perpendicular al mango)
    Zn = (Matrix.Rotation(rol, 3, X) @ Zn).normalized(); Y = Zn.cross(X)
    R = Matrix((X, Y, Zn)).transposed()
    filo = Vector((-0.005, 0.0, -0.118))
    origen = Vector((ix, iy, BZ + 0.002)) - R @ filo
    return Matrix.Translation(origen) @ R.to_4x4()

PIV = bpy.data.objects.new("muñeca", None); scn.collection.objects.link(PIV); PIV.rotation_mode = "QUATERNION"
CAB.parent = PIV
def colocar_hacha(f, ix, iy, alzada, yaw=-52, incl=24, roll=-58):
    M0 = matriz_contacto(ix, iy, yaw, incl, roll)
    G = M0 @ GRIP
    X_ = M0.to_3x3() @ Vector((1, 0, 0)); eje = Vector((0, 0, 1)).cross(X_).normalized()   # giro vertical: sube y baja la cabeza
    q = Matrix.Rotation(alzada, 3, eje).to_quaternion()
    PIV.location = G; PIV.rotation_quaternion = q
    CAB.matrix_parent_inverse = Matrix.Identity(4)
    CAB.matrix_basis = Matrix.Translation(-G) @ M0
    PIV.keyframe_insert("location", frame=f); PIV.keyframe_insert("rotation_quaternion", frame=f)
    CAB.keyframe_insert("location", frame=f); CAB.keyframe_insert("rotation_euler", frame=f)

# golpe: alzada → contacto (con rebote) → alzada. alzada positiva = cabeza hacia arriba (hacia la cámara)
ALTO = 1.25
claves = []
for gi, (f, x, y, rc, rm) in enumerate(GOLPES):
    if gi == 0: claves += [(0, x, y, 0.95)]
    else: claves += [(f - 10, x, y, ALTO)]
    claves += [(f - 3, x, y, 0.55), (f - 1, x, y, 0.14), (f, x, y, 0.0), (f + 1, x, y, 0.035), (f + 3, x, y, 0.16)]
    if gi < len(GOLPES) - 1: claves += [(f + 9, x, y, ALTO * 0.97)]
    else: claves += [(f + 9, x, y, 0.75), (f + 18, x, y, 2.3)]
for (f, x, y, a) in claves: colocar_hacha(f, x, y, a)
_fx = GOLPES[-1][0]
PIV.location = PIV.location.copy(); PIV.keyframe_insert("location", frame=_fx + 18)
for (fk, dx) in ((_fx + 9, 0.0), (_fx + 22, 1.0)):
    scn.frame_set(fk)
_x = GOLPES[-1]
M0 = matriz_contacto(_x[1], _x[2], -52, 24, -58); G0 = M0 @ GRIP
PIV.location = G0; PIV.keyframe_insert("location", frame=_fx + 9)
PIV.location = G0 + Vector((0.75, -0.85, 0.35)); PIV.keyframe_insert("location", frame=_fx + 20)
def suavizar(o):
    ad = o.animation_data
    if not ad or not ad.action: return
    try:
        for lay in ad.action.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        for k in fc.keyframe_points: k.interpolation = "BEZIER"
    except Exception: pass
suavizar(PIV)

# ---------------------------------------------------------------- animación de grietas y marcas
def key_val(nombre, f, v):
    for n in VALORES.get(nombre, []):
        n.outputs[0].default_value = v; n.outputs[0].keyframe_insert("default_value", frame=f)
for nombre in VALORES:
    key_val(nombre, 0, 0.0)
for i, (f, x, y, rc, rm) in enumerate(GOLPES):
    key_val(f"grieta{i}", f - 1, 0.0); key_val(f"grieta{i}", f, rc * 0.45); key_val(f"grieta{i}", f + 2, rc * 0.85); key_val(f"grieta{i}", f + 5, rc)
    key_val(f"marca{i}", f - 1, 0.0); key_val(f"marca{i}", f, rm * 0.7); key_val(f"marca{i}", f + 2, rm)
key_val("grieta_total", F_ROTURA - 1, 0.0); key_val("grieta_total", F_ROTURA + 1, 1.0)
key_val("suelto", F_ROTURA + 2, 0.0); key_val("suelto", F_ROTURA + 8, 1.0)

# ---------------------------------------------------------------- rotura: los pedazos saltan, caen y se deslizan
# Cada pedazo recibe una velocidad que lo deja apoyado fuera del contorno de la remera (anillo de escombros alrededor),
# buscada por bisección con la misma simulación que después se graba: salto con gravedad, rebotes y roce con el piso.
(fR, xR, yR, _, _) = GOLPES[-1]
IMP = Vector((xR, yR, BZ))
g = 9.8; dt = 1.0 / FPS
def simular(c0, dirv, sp, vz, w0, half_h, n):
    vel = Vector((dirv.x * sp, dirv.y * sp, vz)); w_ = w0.copy(); pos = c0.copy(); rot = Vector((0, 0, 0)); tray = []
    for k in range(n):
        vel.z -= g * dt; pos = pos + vel * dt; rot = rot + w_ * dt
        piso_z = half_h * 0.78
        if pos.z < piso_z:
            pos.z = piso_z; vel.z = -vel.z * 0.2
            vel.x *= 0.78; vel.y *= 0.78; w_ = w_ * 0.55
            if abs(vel.z) < 0.18: vel.z = 0.0
        if pos.z <= piso_z + 1e-4 and vel.z == 0.0:
            spd = math.hypot(vel.x, vel.y); dec = 3.6 * dt
            if spd > dec: vel.x *= (spd - dec) / spd; vel.y *= (spd - dec) / spd
            else: vel.x = vel.y = 0.0
            for a in (0, 1):
                tgt = round(rot[a] / (math.pi / 2)) * (math.pi / 2); rot[a] += (tgt - rot[a]) * 0.3
            w_ = w_ * 0.8
        tray.append((pos.copy(), rot.copy()))
    return tray
TEE_R = 0.36
NF = F_FIN - F_ROTURA
for ped in pedazos:
    c0 = ped.location.copy()
    ped.keyframe_insert("location", frame=0); ped.keyframe_insert("rotation_euler", frame=0)
    ped.keyframe_insert("location", frame=F_ROTURA); ped.keyframe_insert("rotation_euler", frame=F_ROTURA)
    rel = c0 - IMP; rel.z = 0
    dirv = rel.normalized() if rel.length > 1e-3 else Vector((1, 0, 0))
    dirv = (Matrix.Rotation(rng.uniform(-0.25, 0.25), 3, "Z") @ dirv).normalized()
    radio = 0.5 * max(ped.dimensions.x, ped.dimensions.y)
    r0 = Vector((c0.x, c0.y, 0)).length
    # distancia a recorrer: que el pedazo termine fuera de la remera, sin irse lejos
    meta = max(0.06, TEE_R + 0.55 * radio + rng.uniform(0.0, 0.10) - r0 * max(0.0, dirv.dot(Vector((c0.x, c0.y, 0)).normalized() if r0 > 1e-3 else dirv)))
    meta = min(meta, 0.55)
    vz = rng.uniform(0.45, 1.0) * (1.0 if rel.length < 0.2 else 0.65)
    w0 = Vector((rng.normal(0, 3.5), rng.normal(0, 3.5), rng.normal(0, 2.5)))
    lo, hi = 0.0, 4.0
    for _ in range(22):
        mid = (lo + hi) / 2
        fin = simular(c0, dirv, mid, vz, w0, ped.dimensions.z / 2, NF)[-1][0]
        if math.hypot(fin.x - c0.x, fin.y - c0.y) < meta: lo = mid
        else: hi = mid
    tray = simular(c0, dirv, (lo + hi) / 2, vz, w0, ped.dimensions.z / 2, NF)
    for k, (p_, r_) in enumerate(tray):
        f = F_ROTURA + 1 + k
        ped.location = p_; ped.rotation_euler = Euler(r_)
        ped.keyframe_insert("location", frame=f); ped.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- esquirlas y polvo en cada golpe
def lanzar(nombre, n, f0, centro, vmax, tam, mat, vida=None):
    # cada partícula es un objeto (pocas por golpe): simple de animar con desenfoque de movimiento
    objs = []
    for k in range(n):
        bmk = bmesh.new(); r = tam * rng.uniform(0.5, 1.4)
        g_ = bmesh.ops.create_icosphere(bmk, subdivisions=1, radius=r)
        for v in g_["verts"]:
            v.co = Vector((v.co.x * rng.uniform(0.6, 1.5), v.co.y * rng.uniform(0.6, 1.5), v.co.z * rng.uniform(0.4, 1.0)))
        mk = bpy.data.meshes.new(f"{nombre}{k}"); bmk.to_mesh(mk); bmk.free()
        o = objeto(f"{nombre}{k:03d}", mk, [mat]); o.visible_shadow = True
        ang = rng.uniform(0, 2 * math.pi); sp = vmax * rng.uniform(0.25, 1.0)
        vel = Vector((math.cos(ang) * sp, math.sin(ang) * sp, rng.uniform(0.4, 1.0) * vmax * 0.9))
        pos = centro.copy() + Vector((rng.normal(0, 0.01), rng.normal(0, 0.01), 0.005)); w_ = Vector(rng.normal(0, 12, 3))
        rot = Vector((0, 0, 0))
        o.location = pos; o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=f0 - 1)
        o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=f0)
        fin = F_FIN if vida is None else min(F_FIN, f0 + vida)
        for f in range(f0, fin + 1):
            o.location = pos; o.rotation_euler = Euler(rot)
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
            vel.z -= g * dt * (0.35 if mat is M_POLVO else 1.0); pos = pos + vel * dt; rot += w_ * dt
            if mat is M_POLVO: vel.x *= 0.9; vel.y *= 0.9
            if pos.z < 0.003:
                pos.z = 0.003; vel.z = -vel.z * 0.25; vel.x *= 0.6; vel.y *= 0.6; w_ *= 0.5
        if vida is not None and fin < F_FIN:
            o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=fin - 3)
            o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=fin)
        objs.append(o)
    return objs
for i, (f, x, y, rc, rm) in enumerate(GOLPES):
    fuerte = (f == F_ROTURA)
    lanzar(f"esq{i}_", 26 if fuerte else 14, f, Vector((x, y, BZ)), 1.7 if fuerte else 1.2, 0.007, M_ESQ)
    lanzar(f"polvo{i}_", 70 if fuerte else 40, f, Vector((x, y, BZ)), 0.9 if fuerte else 0.7, 0.0018, M_POLVO, vida=26)

# ---------------------------------------------------------------- cámara: desde arriba; sacudón en cada golpe; acercamiento final
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 42; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36
cam_d.dof.use_dof = False
cam = bpy.data.objects.new("cam", cam_d); scn.collection.objects.link(cam); scn.camera = cam
BASE = Vector((0.0, -0.10, 2.05)); ROT0 = Euler((math.radians(4.0), 0, 0))
def cam_key(f, off=(0, 0, 0), rot_off=(0, 0, 0)):
    cam.location = BASE + Vector(off); cam.rotation_euler = Euler((ROT0.x + rot_off[0], ROT0.y + rot_off[1], ROT0.z + rot_off[2]))
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
cam_key(0)
for i, (f, x, y, rc, rm) in enumerate(GOLPES):
    a = 0.012 if f != F_ROTURA else 0.022
    cam_key(f - 1); cam_key(f + 1, (a, -a * 0.6, -a * 1.2), (0.004, -0.003, 0.002)); cam_key(f + 2, (-a * 0.7, a * 0.5, a * 0.4))
    cam_key(f + 4, (a * 0.25, -a * 0.2, 0)); cam_key(f + 6)
# acercamiento: lento desde ~3,3 s y rápido al final (transición al corte)
F_ACER = 100
cam_key(F_ACER)
cam_key(F_FIN - 6, (0.0, 0.03, -0.55))
cam_key(F_FIN, (0.0, 0.06, -1.25), (math.radians(-2.5), 0, 0))
for fc in (cam.animation_data.action.fcurves if hasattr(cam.animation_data.action, "fcurves") else []):
    for k in fc.keyframe_points: k.interpolation = "BEZIER"

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "escena.blend"))
info = {"pedazos": len(pedazos), "semillas": len(semillas), "golpes": GOLPES, "rotura": F_ROTURA, "fin": F_FIN}
json.dump(info, open(os.path.join(OUT, "escena.json"), "w"), indent=1)

if RANGO:
    import time
    for f in range(RANGO[0], RANGO[1] + 1):
        p = os.path.join(OUT, f"{f:04d}.png")
        if os.path.exists(p): continue
        scn.frame_set(f); scn.render.filepath = p
        t0 = time.time(); bpy.ops.render.render(write_still=True); print(f"cuadro {f}: {time.time() - t0:.1f} s", flush=True)
