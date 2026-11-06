// "Dejá de procrastinar" — escena 3D original de Roccé (three.js, render cuadro a cuadro en Chromium).
// Mecanismo (método apuesta → pregunta → giro → reenganche): mismo plazo y misma pared para dos personas;
// el CONSTRUCTOR pone un ladrillo por día; el PROCRASTINADOR está sentado sobre sus ladrillos con el celular
// ("mañana…"). A 1 día, pánico y pared torcida. Giro 1: MISMA PARED. Giro 2: DISTINTO MES (él queda destruido,
// a su pared se le cae un ladrillo; el otro ya sube un piso más). Vuelve a 30 días y él agarra el celular.
// window.iniciar(assets) arma la escena y devuelve la línea de tiempo; window.dibujar(t) dibuja el cuadro t
// (función pura del tiempo: el mismo t da siempre la misma imagen).
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const W = 1080, H = 1920, D2R = Math.PI / 180;
const COL = { noche: '#0A1424', humo: '#CDDDE5', celeste: '#9CC8EC', azul: '#233A55', rojo: '#E5484D', blanco: '#F4F6F8' };

// ---------------- línea de tiempo (segundos) ----------------
const TL = {
  d0: 0.40, paso: 0.178,          // 30 → 29 a los 0,40 s; un día cada 0,178 s hasta "2 DÍAS"
  unDia: 5.35, hoy: 6.70,         // 1 DÍA (rojo, noche, pánico) · HOY
  misma: 7.20, distinto: 8.70,    // textos de los giros
  cae: 9.20,                      // se cae un ladrillo de la pared torcida
  reset: 9.60,                    // vuelve a 30 DÍAS (pilas nuevas)
  dur: 11.60,
  manana: [[1.15, 1.75], [2.55, 3.15], [3.95, 4.55], [10.75, 11.90]],
};
const N = 24;                                   // ladrillos por torre (2 × 12)
const tC = i => TL.d0 + i * TL.paso;            // el constructor coloca el ladrillo i
const tP = i => TL.unDia + 0.35 + i * 0.040;    // el procrastinador, todos de golpe la última noche
function restan(t) {
  if (t >= TL.reset) return 30;
  if (t >= TL.hoy) return 0;
  if (t >= TL.unDia) return 1;
  if (t < TL.d0) return 30;
  return Math.max(2, 30 - (Math.floor((t - TL.d0) / TL.paso) + 1));
}
function cambioDia(t) {           // momento del último cambio de la tarjeta
  const r = restan(t);
  if (r === 30) return t >= TL.reset ? TL.reset : -9;
  if (r === 0) return TL.hoy;
  if (r === 1) return TL.unDia;
  return TL.d0 + (30 - r - 1) * TL.paso;
}

// ---------------- utilidades ----------------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, u) => a + (b - a) * u;
const suave = u => { u = clamp(u); return u * u * (3 - 2 * u); };
const tramo = (t, a, b) => suave((t - a) / (b - a));
const rebote = u => { u = clamp(u); return 1 + 2.2 * Math.pow(u - 1, 3) + 1.2 * Math.pow(u - 1, 2); }; // pasa de 1 y vuelve
function azar(sem) { let s = sem >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

// ---------------- escena ----------------
let renderer, scene, camera, composer, bloom, sal, ctx, fondo;
let P, C, zonaP, zonaC, nube, lluvia = [], celu, luzCelu, luzLlave, luzLuna, focoP, focoC, hemi;
const ladP = [], ladC = [], ladC2 = [], pilaP = [], pilaC = [], pilaNuevaP = [], pilaNuevaC = [], fantasmasP = [], fantasmasC = [], fantasmasC2 = [];
let fuentes = {};

const LAD = { L: 0.26, A: 0.12, P: 0.13, g: 0.012 };
function mat(c, r = 0.6, extra = {}) { return new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: 0, ...extra }); }

function zona(cx, interior) {     // marco local: x positivo = hacia el centro de la imagen
  const g = new THREE.Group(); g.position.x = cx; g.userData.s = interior; scene.add(g); return g;
}
const enZona = (z, x, y, zz) => new THREE.Vector3(z.position.x + z.userData.s * x, y, zz);

function ladrillo(semilla) {
  const r = azar(semilla)();
  const geo = new RoundedBoxGeometry(LAD.L, LAD.A, LAD.P, 2, 0.014);
  const c = new THREE.Color('#B4593B').offsetHSL((r - 0.5) * 0.03, 0, (r - 0.5) * 0.08);
  const m = new THREE.Mesh(geo, mat(c, 0.85));
  m.castShadow = true; m.receiveShadow = true; scene.add(m); return m;
}
function ranura(z, i, base = 0) {   // posición del ladrillo i de la torre (2 por hilada, trabados)
  const fila = Math.floor(i / 2) + base, col = i % 2;
  const off = (fila % 2) * (LAD.L / 2) - LAD.L / 4;
  const x = 0.32 + (col - 0.5) * (LAD.L + LAD.g) + off;
  return enZona(z, x, LAD.A / 2 + fila * (LAD.A + LAD.g), -0.30);
}
function enPila(z, i, base = 0) {   // pila sobre el pallet: 8 por capa (2 × 4), 3 capas
  const capa = Math.floor(i / 8), k = i % 8, a = k % 2, b = Math.floor(k / 2);
  return enZona(z, -0.30 + (a - 0.5) * (LAD.L + 0.01), 0.11 + LAD.A / 2 + capa * (LAD.A + 0.005) + base, -0.52 + (b - 1.5) * (LAD.P + 0.01));
}
function fantasma(p) {
  const e = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(LAD.L - 0.01, LAD.A - 0.01, LAD.P - 0.01)),
    new THREE.LineBasicMaterial({ color: COL.celeste, transparent: true, opacity: 0.28 }));
  e.position.copy(p); scene.add(e); return e;
}
function pallet(z) {
  const g = new THREE.Group(), m = mat('#7A5A3A', 0.9);
  for (let k = 0; k < 4; k++) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.025, 0.11), m); b.position.set(0, 0.095, -0.21 + k * 0.14); b.castShadow = b.receiveShadow = true; g.add(b); }
  for (let k = 0; k < 3; k++) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.07, 0.58), m); b.position.set(-0.25 + k * 0.25, 0.04, 0); b.castShadow = b.receiveShadow = true; g.add(b); }
  const p = enZona(z, -0.30, 0, -0.52); g.position.copy(p); scene.add(g);
}

// ---------------- personaje con articulaciones ----------------
function persona(o) {
  const piel = mat(o.piel, 0.55), ropa = mat(o.remera, o.remeraR ?? 0.7), pant = mat(o.pantalon, 0.8), zap = mat(o.zapas, 0.6), pelo = mat(o.pelo, 0.8);
  const cap = (r, l, m) => { const x = new THREE.Mesh(new THREE.CapsuleGeometry(r, l, 6, 16), m); x.castShadow = true; x.receiveShadow = true; return x; };
  const raiz = new THREE.Group(); raiz.scale.setScalar(0.86); scene.add(raiz);
  const pelvis = new THREE.Group(); pelvis.position.y = 0.88; raiz.add(pelvis);
  const cadera = cap(0.14, 0.06, pant); cadera.rotation.z = Math.PI / 2; cadera.scale.set(1, 1, 0.8); pelvis.add(cadera);
  const col = new THREE.Group(); pelvis.add(col);
  const torso = cap(0.155, 0.30, ropa); torso.position.y = 0.30; torso.scale.set(1, 1, 0.72); col.add(torso);
  if (o.buzo) { const capucha = new THREE.Mesh(new THREE.TorusGeometry(0.11, 0.045, 10, 20, Math.PI * 1.2), ropa); capucha.position.set(0, 0.56, -0.06); capucha.rotation.set(-0.5, 0, -Math.PI * 0.1 + Math.PI); capucha.castShadow = true; col.add(capucha); }
  if (o.estampado) {
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(0.11, 0.11 * o.estampado.image.height / o.estampado.image.width),
      new THREE.MeshStandardMaterial({ map: o.estampado, transparent: true, roughness: 0.8, depthWrite: false }));
    pl.position.set(0.065, 0.43, 0.113); pl.rotation.y = 0.25; col.add(pl);
  }
  const cuello = new THREE.Group(); cuello.position.y = 0.62; col.add(cuello);
  const cabeza = new THREE.Mesh(new THREE.SphereGeometry(0.155, 28, 20), piel); cabeza.position.y = 0.17; cabeza.castShadow = true; cuello.add(cabeza);
  const pel = new THREE.Mesh(new THREE.SphereGeometry(0.163, 28, 16, 0, Math.PI * 2, 0, Math.PI * 0.52), pelo); pel.position.set(0, 0.185, -0.012); pel.rotation.x = -0.25; pel.castShadow = true; cuello.add(pel);
  for (const sx of [-1, 1]) { const ojo = new THREE.Mesh(new THREE.SphereGeometry(0.017, 10, 8), mat('#141414', 0.4)); ojo.position.set(sx * 0.052, 0.18, 0.142); ojo.scale.y = 1.25; cuello.add(ojo); }
  const brazo = (sx) => {
    const h = new THREE.Group(); h.position.set(sx * 0.2, 0.53, 0); col.add(h);
    const manga = cap(0.062, 0.10, ropa); manga.position.y = -0.07; h.add(manga);
    const sup = cap(0.052, 0.17, piel); sup.position.y = -0.15; h.add(sup);
    const c = new THREE.Group(); c.position.y = -0.29; h.add(c);
    const ant = cap(0.048, 0.17, piel); ant.position.y = -0.13; c.add(ant);
    const mano = new THREE.Mesh(new THREE.SphereGeometry(0.056, 14, 10), piel); mano.position.y = -0.29; mano.castShadow = true; c.add(mano);
    return { h, c, mano };
  };
  const pierna = (sx) => {
    const h = new THREE.Group(); h.position.set(sx * 0.085, -0.02, 0); pelvis.add(h);
    const mus = cap(0.078, 0.25, pant); mus.position.y = -0.2; h.add(mus);
    const r = new THREE.Group(); r.position.y = -0.41; h.add(r);
    const pan = cap(0.066, 0.27, pant); pan.position.y = -0.2; r.add(pan);
    const pie = new THREE.Mesh(new RoundedBoxGeometry(0.11, 0.07, 0.22, 2, 0.03), zap); pie.position.set(0, -0.43, 0.05); pie.castShadow = true; r.add(pie);
    return { h, r };
  };
  return { raiz, pelvis, col, cuello, bI: brazo(1), bD: brazo(-1), pI: pierna(1), pD: pierna(-1) };
}
// pose: grados. bI/bD = hombro [x,y,z] + codo; pI/pD = cadera [x,z] + rodilla. I = izquierda del personaje (+x).
function posar(p, q, z) {
  const s = z.userData.s;
  const pos = enZona(z, q.x, q.y ?? 0, q.z);
  p.raiz.position.copy(pos); p.raiz.rotation.y = (q.ry ?? 0) * D2R * s;
  p.pelvis.position.y = q.cad ?? 0.88;
  p.pelvis.rotation.set((q.pel?.[0] ?? 0) * D2R, 0, (q.pel?.[2] ?? 0) * D2R);
  p.col.rotation.set((q.col?.[0] ?? 0) * D2R, (q.col?.[1] ?? 0) * D2R * s, (q.col?.[2] ?? 0) * D2R * s);
  p.cuello.rotation.set((q.cab?.[0] ?? 0) * D2R, (q.cab?.[1] ?? 0) * D2R * s, (q.cab?.[2] ?? 0) * D2R * s);
  // con s = −1 el marco está espejado: el brazo "interior" sigue siendo el que mira al centro
  const [bInt, bExt] = s > 0 ? [p.bI, p.bD] : [p.bD, p.bI];
  const [pInt, pExt] = s > 0 ? [p.pI, p.pD] : [p.pD, p.pI];
  const brazo = (b, a, signo) => { b.h.rotation.set((a?.[0] ?? 0) * D2R, (a?.[1] ?? 0) * D2R * signo, (a?.[2] ?? 0) * D2R * signo); b.c.rotation.set((a?.[3] ?? 0) * D2R, 0, 0); };
  brazo(bInt, q.bInt, s); brazo(bExt, q.bExt, -s);
  const pierna = (pp, a, signo) => { pp.h.rotation.set((a?.[0] ?? 0) * D2R, 0, (a?.[1] ?? 0) * D2R * signo); pp.r.rotation.set((a?.[2] ?? 0) * D2R, 0, 0); };
  pierna(pInt, q.pInt, s); pierna(pExt, q.pExt, -s);
}
function mezclar(a, b, u) {        // interpola dos poses (números y listas)
  const r = {};
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const va = a[k], vb = b[k];
    if (Array.isArray(va) || Array.isArray(vb)) { const A = va || [], B = vb || []; r[k] = Array.from({ length: Math.max(A.length, B.length) }, (_, i) => lerp(A[i] ?? 0, B[i] ?? 0, u)); }
    else r[k] = lerp(va ?? 0, vb ?? 0, u);
  }
  return r;
}

// ---------------- poses ----------------
// Marco local: x positivo = hacia la pared (centro de la imagen); el ángulo positivo de col/cab gira hacia la pared.
const SENTADO_CELU = { x: -0.30, z: -0.33, cad: 0.68, col: [26, 0, 0], cab: [32, 0, 0],
  bInt: [-38, 0, -14, -100], bExt: [-38, 0, -14, -100], pInt: [-86, 6, 88], pExt: [-86, 6, 88] };
const PARADO = { x: 0.0, z: 0.25, cad: 0.88, col: [4, 0, 0], cab: [4, 0, 0], bInt: [0, 0, 6, -8], bExt: [0, 0, 6, -8], pInt: [0, 2, 0], pExt: [0, 2, 0] };
const A_LA_PILA = { x: -0.10, z: 0.10, ry: -26, cad: 0.80, col: [34, -48, 0], cab: [18, -10, 0],
  bInt: [-55, 0, 8, -30], bExt: [-62, 0, 10, -25], pInt: [-22, 4, 28], pExt: [-12, 4, 14] };
const A_LA_PARED = { x: -0.06, z: 0.10, ry: 22, cad: 0.86, col: [14, 32, 0], cab: [6, 12, 0],
  bInt: [-78, 0, 4, -45], bExt: [-70, 0, 12, -50], pInt: [-6, 4, 6], pExt: [-14, 4, 18] };
const RELAJADO = { x: -0.10, z: 0.14, ry: 14, cad: 0.88, col: [-7, 8, 0], cab: [-10, 10, 0],
  bInt: [-35, 0, 150, -128], bExt: [-35, 0, 150, -128], pInt: [0, 6, 0], pExt: [-4, -4, 6] };
const PANICO = { x: -0.04, z: 0.10, ry: 30, cad: 0.84, col: [24, 26, 0], cab: [12, 10, 0],
  bInt: [-90, 0, 10, -40], bExt: [-60, 0, 14, -30], pInt: [-16, 6, 18], pExt: [-6, 6, 10] };
const FESTEJO = { x: -0.06, z: 0.14, ry: 6, cad: 0.88, col: [-8, 0, 0], cab: [-14, 0, 0],
  bInt: [-10, 0, 150, -12], bExt: [-10, 0, 150, -12], pInt: [0, 6, 0], pExt: [0, 6, 0] };
const DESPLOMADO = { x: -0.22, z: -0.12, ry: 8, cad: 0.17, pel: [-6, 0, 0], col: [-22, 0, 10], cab: [38, 8, 22],
  bInt: [-6, 0, 14, -8], bExt: [-14, 0, 22, -14], pInt: [-82, 10, 8], pExt: [-78, 14, 16] };
const PISO_CELU = { x: -0.22, z: -0.12, ry: 8, cad: 0.17, pel: [-6, 0, 0], col: [6, 0, 0], cab: [30, 0, 0],
  bInt: [-40, 0, -12, -98], bExt: [-40, 0, -12, -98], pInt: [-82, 10, 8], pExt: [-78, 14, 16] };

// ---------------- armado ----------------
async function cargarTextura(url) { const t = await new THREE.TextureLoader().loadAsync(url); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; }
window.iniciar = async (assets) => {
  for (const [k, url] of Object.entries(assets.fuentes)) { const f = new FontFace(k, `url(${url})`); await f.load(); document.fonts.add(f); fuentes[k] = k; }
  sal = document.getElementById('sal'); ctx = sal.getContext('2d');
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); renderer.setSize(W, H, false);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
  scene = new THREE.Scene();
  const g = document.createElement('canvas'); g.width = 4; g.height = 256; const gc = g.getContext('2d');
  const gr = gc.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#060D18'); gr.addColorStop(0.55, '#0E1E36'); gr.addColorStop(1, '#0A1628');
  gc.fillStyle = gr; gc.fillRect(0, 0, 4, 256); fondo = new THREE.CanvasTexture(g); fondo.colorSpace = THREE.SRGBColorSpace; scene.background = fondo;
  scene.fog = new THREE.Fog('#0B1729', 11, 20);
  camera = new THREE.PerspectiveCamera(34, W / H, 0.1, 60);
  camera.position.set(0, 2.55, 8.2); camera.lookAt(0, 1.50, 0);

  const piso = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), mat('#142338', 0.92)); piso.rotation.x = -Math.PI / 2; piso.receiveShadow = true; scene.add(piso);
  hemi = new THREE.HemisphereLight('#9CC8EC', '#0B1424', 0.55); scene.add(hemi);
  luzLlave = new THREE.DirectionalLight('#FFF2E0', 1.6); luzLlave.position.set(-3.5, 6, 5); luzLlave.castShadow = true;
  luzLlave.shadow.mapSize.set(2048, 2048); Object.assign(luzLlave.shadow.camera, { left: -4, right: 4, top: 4, bottom: -2, near: 1, far: 20 }); luzLlave.shadow.bias = -0.0004; luzLlave.shadow.radius = 4; scene.add(luzLlave);
  const contra = new THREE.DirectionalLight('#9CC8EC', 1.1); contra.position.set(2, 3.5, -6); scene.add(contra);
  luzLuna = new THREE.DirectionalLight('#7FA6E0', 0.0); luzLuna.position.set(3, 7, 3); scene.add(luzLuna);
  focoP = new THREE.SpotLight('#FFE9D2', 9, 9, 0.42, 0.7, 1.6); focoP.position.set(-0.8, 5.5, 1.8); focoC = focoP.clone();
  focoC.position.set(0.8, 5.5, 1.8);
  for (const f of [focoP, focoC]) { scene.add(f); scene.add(f.target); }
  focoP.target.position.set(-0.8, 0, -0.2); focoC.target.position.set(0.8, 0, -0.2);

  zonaP = zona(-0.80, 1); zonaC = zona(0.80, -1);
  pallet(zonaP); pallet(zonaC);
  // marca del piso de cada zona
  for (const z of [zonaP, zonaC]) { const d = new THREE.Mesh(new THREE.CircleGeometry(0.78, 48), mat('#1A2D48', 0.95)); d.rotation.x = -Math.PI / 2; d.position.set(z.position.x, 0.002, -0.15); d.receiveShadow = true; scene.add(d); }
  for (let i = 0; i < N; i++) {
    ladP.push(ladrillo(100 + i)); ladC.push(ladrillo(200 + i));
    fantasmasP.push(fantasma(ranura(zonaP, i))); fantasmasC.push(fantasma(ranura(zonaC, i)));
  }
  for (let i = 0; i < 6; i++) { ladC2.push(ladrillo(300 + i)); fantasmasC2.push(fantasma(ranura(zonaC, i, 12))); pilaNuevaC.push(ladrillo(400 + i)); }
  for (let i = 0; i < 6; i++) pilaNuevaP.push(ladrillo(500 + i));

  const est = await cargarTextura(assets.estampado);
  P = persona({ piel: '#C99A74', pelo: '#2A1D15', remera: '#2E333B', pantalon: '#4B525C', zapas: '#E9E9E9', buzo: true });
  C = persona({ piel: '#B9845E', pelo: '#1C130E', remera: '#EEF0F1', remeraR: 0.75, pantalon: '#1F2C45', zapas: '#202020', estampado: est });

  // celular del procrastinador
  celu = new THREE.Group();
  const cuerpo = new THREE.Mesh(new RoundedBoxGeometry(0.085, 0.16, 0.014, 2, 0.006), mat('#15171B', 0.4)); celu.add(cuerpo);
  const pant = new THREE.Mesh(new THREE.PlaneGeometry(0.074, 0.145), new THREE.MeshStandardMaterial({ color: '#000', emissive: '#BFE2FF', emissiveIntensity: 0.7 }));
  pant.position.z = 0.0075; celu.add(pant); scene.add(celu);
  luzCelu = new THREE.PointLight('#A9D8FF', 0.8, 1.2, 2); scene.add(luzCelu);
  // nube y lluvia
  nube = new THREE.Group(); const mn = mat('#4E5664', 1.0);
  [[0, 0, 0, 0.26], [0.24, -0.04, 0, 0.2], [-0.24, -0.05, 0.02, 0.19], [0.12, 0.12, -0.02, 0.2], [-0.12, 0.1, 0, 0.18], [0.38, -0.08, -0.03, 0.13], [-0.37, -0.09, 0, 0.13]]
    .forEach(([x, y, z, r]) => { const s = new THREE.Mesh(new THREE.SphereGeometry(r, 18, 12), mn); s.position.set(x, y, z); s.castShadow = true; nube.add(s); });
  scene.add(nube);
  const mg = new THREE.MeshBasicMaterial({ color: '#B8DAF5', transparent: true, opacity: 0.8 });
  for (let i = 0; i < 34; i++) { const d = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.13, 5), mg); scene.add(d); lluvia.push(d); }

  composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 0.42, 0.5, 0.9); composer.addPass(bloom);
  composer.addPass(new OutputPass());
  return { TL, N, tC: Array.from({ length: N }, (_, i) => tC(i)), tP: Array.from({ length: N }, (_, i) => tP(i)) };
};

// ---------------- estado por cuadro ----------------
function arco(a, b, u, alto) { const p = a.clone().lerp(b, u); p.y += Math.sin(Math.PI * u) * alto; return p; }
function ponerLadrillos(t) {
  const rP = azar(77);
  for (let i = 0; i < N; i++) {
    // constructor: de su pila a la pared, un ladrillo por día
    const c = ladC[i], s0 = enPila(zonaC, N - 1 - i), s1 = ranura(zonaC, i), u = (t - tC(i)) / 0.16;
    c.visible = true; c.rotation.set(0, 0, 0);
    if (u <= 0) c.position.copy(s0); else if (u >= 1) c.position.copy(s1); else { c.position.copy(arco(s0, s1, suave(u), 0.45)); c.rotation.y = Math.sin(Math.PI * u) * 0.6; }
    fantasmasC[i].visible = u < 1;
    // procrastinador: todos de golpe y torcidos la última noche
    const p = ladP[i], q0 = enPila(zonaP, N - 1 - i), q1 = ranura(zonaP, i), v = (t - tP(i)) / 0.13;
    const fila = Math.floor(i / 2), dx = (rP() - 0.5) * 0.05 + fila * 0.007, ry = (rP() - 0.5) * 0.30, rz = (rP() - 0.5) * 0.14 - fila * 0.004;
    p.visible = true; p.rotation.set(0, 0, 0);
    if (v <= 0) p.position.copy(q0);
    else if (v >= 1) { p.position.copy(q1); p.position.x += dx * zonaP.userData.s; p.rotation.set(0, ry, rz); p.userData.fin = p.position.clone(); }
    else { p.position.copy(arco(q0, q1, suave(v), 0.6)); p.position.x += dx * v; p.rotation.set(v * 4, ry * v, rz * v); }
    fantasmasP[i].visible = v < 1;
  }
  // se cae el último ladrillo de su pared
  const ult = ladP[N - 1];
  if (t > TL.cae) {
    const u = clamp((t - TL.cae) / 0.55), base = ladP[N - 1].userData.fin || ranura(zonaP, N - 1);
    const fin = enZona(zonaP, 0.62, LAD.A / 2, 0.20);
    ult.position.set(lerp(base.x, fin.x, u), lerp(base.y, fin.y, u * u) + Math.sin(Math.PI * u) * 0.12, lerp(base.z, fin.z, u));
    ult.rotation.set(u * 2.2, 0.2, u * 1.4);
    if (u >= 1) ult.rotation.set(0, 0.5, 0);
  }
  // pilas nuevas al volver a 30, y el constructor sigue subiendo un piso
  for (let i = 0; i < 6; i++) {
    const u = clamp((t - TL.reset - i * 0.035) / 0.22);
    for (const [arr, z] of [[pilaNuevaP, zonaP], [pilaNuevaC, zonaC]]) {
      const b = arr[i], p = enPila(z, 5 - i);
      b.visible = u > 0; b.position.set(p.x, p.y + (1 - u) * 1.8, p.z); b.rotation.set(0, 0, 0);
    }
    const t2 = TL.reset + 0.45 + i * TL.paso, w = (t - t2) / 0.16, c2 = ladC2[i];
    fantasmasC2[i].visible = t > TL.reset + 0.1 && w < 1;
    if (w > 0) { pilaNuevaC[i].visible = false; c2.visible = true; c2.position.copy(w >= 1 ? ranura(zonaC, i, 12) : arco(enPila(zonaC, 5 - i), ranura(zonaC, i, 12), suave(w), 0.45)); }
    else c2.visible = false;
  }
}

function poseC(t) {
  const fin = tC(N - 1) + 0.16;
  if (t < fin) {                               // un ciclo pila → pared por ladrillo
    const k = (t - TL.d0) / TL.paso, ph = k - Math.floor(k);
    if (t < TL.d0) return mezclar(PARADO, A_LA_PILA, tramo(t, 0, TL.d0));
    return ph < 0.45 ? mezclar(A_LA_PARED, A_LA_PILA, suave(ph / 0.45)) : mezclar(A_LA_PILA, A_LA_PARED, suave((ph - 0.45) / 0.55));
  }
  if (t < TL.reset + 0.25) {                   // termina y descansa
    let q = mezclar(A_LA_PARED, RELAJADO, tramo(t, fin, fin + 0.35));
    q.col = [...q.col]; q.col[0] += Math.sin(t * 2.2) * 1.5;
    return q;
  }
  const t2 = TL.reset + 0.45;                  // nuevo mes: sigue, tranquilo
  if (t < t2) return mezclar(RELAJADO, A_LA_PILA, tramo(t, TL.reset + 0.25, t2));
  const k = (t - t2) / TL.paso, ph = k - Math.floor(k);
  return ph < 0.45 ? mezclar(A_LA_PARED, A_LA_PILA, suave(ph / 0.45)) : mezclar(A_LA_PILA, A_LA_PARED, suave((ph - 0.45) / 0.55));
}
function poseP(t) {
  if (t < TL.unDia + 0.12) {                   // sentado sobre sus ladrillos, con el celular
    const q = mezclar(SENTADO_CELU, SENTADO_CELU, 0);
    q.bExt = [...q.bExt]; q.bExt[3] += Math.sin(t * 13) * 5;    // desliza el dedo
    q.cab = [...q.cab]; q.cab[1] += Math.sin(t * 1.7) * 4;
    const enc = clamp((t - 2.0) / 3.3); q.col = [q.col[0] + enc * 10, 0, 0];   // cada día más encorvado
    return q;
  }
  if (t < TL.unDia + 0.35) return mezclar(SENTADO_CELU, PANICO, tramo(t, TL.unDia + 0.12, TL.unDia + 0.35));
  if (t < TL.hoy + 0.05) {                     // pánico: brazos a toda velocidad
    const q = mezclar(PANICO, PANICO, 0), w = Math.sin(t * 34);
    q.bInt = [-90 + w * 45, 0, 10, -40 - w * 20]; q.bExt = [-60 - w * 45, 0, 14, -30 + w * 20];
    q.col = [24 + Math.sin(t * 17) * 6, 26 + Math.sin(t * 23) * 10, 0]; q.cad = 0.84 + Math.abs(Math.sin(t * 17)) * 0.03;
    return q;
  }
  if (t < TL.distinto) {                       // festeja: llegó
    const q = mezclar(PANICO, FESTEJO, tramo(t, TL.hoy + 0.05, TL.hoy + 0.3));
    q.cad = (q.cad ?? 0.88) + Math.max(0, Math.sin((t - TL.hoy) * 9)) * 0.05 * (1 - tramo(t, TL.misma + 0.6, TL.distinto));
    return q;
  }
  if (t < TL.reset + 0.6) return mezclar(FESTEJO, DESPLOMADO, tramo(t, TL.distinto, TL.distinto + 0.45));
  if (t < TL.reset + 0.95) return mezclar(DESPLOMADO, PISO_CELU, tramo(t, TL.reset + 0.6, TL.reset + 0.95));
  const q = mezclar(PISO_CELU, PISO_CELU, 0); q.bExt = [...q.bExt]; q.bExt[3] += Math.sin(t * 13) * 5; return q;
}

function luces(t) {
  const noche = tramo(t, TL.unDia - 0.15, TL.unDia + 0.2) * (1 - tramo(t, TL.hoy + 0.2, TL.hoy + 0.6));
  const dia = t < TL.unDia ? 0.5 + 0.5 * Math.cos(2 * Math.PI * (t - TL.d0) / TL.paso) : 1;   // parpadeo día/noche de cada día
  const k = (TL.d0 < t && t < TL.unDia) ? 0.82 + 0.18 * dia : 1;
  luzLlave.intensity = 1.6 * k * (1 - 0.8 * noche);
  focoP.intensity = 9 * k * (1 - 0.55 * noche); focoC.intensity = 9 * k * (1 - 0.55 * noche);
  luzLuna.intensity = 1.2 * noche; hemi.intensity = 0.55 * (1 - 0.4 * noche);
  // si se desploma, la luz sobre él baja (el otro sigue con la suya)
  focoP.intensity *= 1 - 0.45 * tramo(t, TL.distinto, TL.distinto + 0.5);
}

function nubeYLluvia(t) {
  const crece = tramo(t, 1.4, TL.unDia), cae = tramo(t, TL.hoy, TL.hoy + 0.35), vuelve = tramo(t, TL.distinto + 0.2, TL.distinto + 0.8);
  const k = crece * (1 - cae) + vuelve * 0.85;
  const cab = P.cuello.getWorldPosition(new THREE.Vector3());
  nube.position.set(cab.x, cab.y + 0.55 + Math.sin(t * 2) * 0.02, cab.z - 0.05);
  nube.scale.setScalar(Math.max(0.001, k * (0.85 + 0.25 * tramo(t, TL.unDia, TL.hoy))));
  nube.visible = k > 0.01;
  const llueve = (t > TL.unDia && t < TL.hoy) || (t > TL.distinto + 0.5 && t < TL.reset);
  lluvia.forEach((d, i) => {
    const r = azar(900 + i), ox = (r() - 0.5) * 0.7, ph = r(), vel = 2.2 + r();
    const y = 0.1 - ((t * vel + ph) % 1) * 1.0;
    d.position.set(nube.position.x + ox * nube.scale.x, nube.position.y - 0.15 + y * nube.scale.x, nube.position.z + (r() - 0.5) * 0.2);
    d.visible = llueve && k > 0.3;
  });
}

function celular(t) {
  P.raiz.updateMatrixWorld(true);
  const enMano = t < TL.unDia + 0.15 || t > TL.reset + 0.75;
  const mI = P.bI.mano.getWorldPosition(new THREE.Vector3()), mD = P.bD.mano.getWorldPosition(new THREE.Vector3());
  if (enMano) {
    const m = mI.clone().lerp(mD, 0.5); celu.position.set(m.x, m.y + 0.05, m.z + 0.02);
    const cab = P.cuello.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.17, 0));
    celu.lookAt(cab); celu.rotateY(Math.PI);    // la pantalla mira a su cara
  } else {
    const u = clamp((t - TL.unDia - 0.15) / 0.3), piso = enZona(zonaP, -0.15, 0.012, 0.42);
    const ini = mI.clone().lerp(mD, 0.5);
    if (t < TL.reset) { celu.position.set(lerp(ini.x, piso.x, u), lerp(ini.y, piso.y, u * u) + Math.sin(Math.PI * u) * 0.2, lerp(ini.z, piso.z, u)); celu.rotation.set(-Math.PI / 2 * u, 0, u * 0.6); }
    else { celu.position.copy(piso); celu.rotation.set(-Math.PI / 2, 0, 0.6); }
  }
  luzCelu.position.copy(celu.position).add(new THREE.Vector3(0, 0.06, 0.12));
  const brillo = enMano ? 0.8 : (t > TL.distinto ? 0.35 : 0.2);
  luzCelu.intensity = brillo;
}

// ---------------- capa 2D: textos de la historia ----------------
const aPantalla = v => { const p = v.clone().project(camera); return [(p.x + 1) / 2 * W, (1 - p.y) / 2 * H]; };
function texto(s, x, y, tam, color, peso = 'IDB', alin = 'center', track = 0, alfa = 1) {
  ctx.save(); ctx.globalAlpha = alfa; ctx.font = `${tam}px ${peso}`; ctx.fillStyle = color; ctx.textAlign = alin; ctx.textBaseline = 'alphabetic';
  if ('letterSpacing' in ctx) ctx.letterSpacing = `${track}px`;
  ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 12; ctx.fillText(s, x, y); ctx.restore();
}
function escribir(s, t0, t, x, y, tam, color) {   // aparece letra por letra
  if (t < t0) return; const n = Math.min(s.length, Math.floor((t - t0) / 0.028) + 1);
  const pop = rebote((t - t0) / 0.25);
  ctx.save(); ctx.translate(x, y); ctx.scale(lerp(0.9, 1, clamp(pop)), lerp(0.9, 1, clamp(pop)));
  texto(s.slice(0, n), 0, 0, tam, color, 'IDB', 'center', 3); ctx.restore();
}
function tarjeta(t) {                       // cuenta regresiva (una sola tarjeta: el plazo es el mismo)
  const r = restan(t), cx = W / 2, cy = 505, w = 250, h = 230;
  const roja = r <= 1 && t < TL.reset;
  const dibujar = (rr, esRoja, ang = 0, dy = 0, alfa = 1) => {
    ctx.save(); ctx.globalAlpha = alfa; ctx.translate(cx, cy + dy); ctx.rotate(ang);
    ctx.shadowColor = esRoja ? 'rgba(229,72,77,0.55)' : 'rgba(156,200,236,0.35)'; ctx.shadowBlur = 40;
    ctx.fillStyle = esRoja ? COL.rojo : COL.blanco; roundRect(-w / 2, -h / 2, w, h, 26); ctx.fill(); ctx.shadowBlur = 0;
    ctx.fillStyle = esRoja ? 'rgba(0,0,0,0.12)' : 'rgba(35,58,85,0.10)'; ctx.fillRect(-w / 2, -h / 2 + 52, w, 3);
    for (const sx of [-1, 1]) { ctx.fillStyle = esRoja ? '#8E1F24' : COL.azul; roundRect(sx * 60 - 9, -h / 2 - 16, 18, 40, 9); ctx.fill(); }
    const txt = rr === 0 ? 'HOY' : String(rr), sub = rr === 0 ? 'SE ENTREGA' : (rr === 1 ? 'DÍA' : 'DÍAS');
    texto(txt, 0, 46, rr === 0 ? 112 : 128, esRoja ? '#FFFFFF' : COL.azul, 'IDB', 'center', -2);
    texto(sub, 0, 92, 32, esRoja ? '#FFFFFF' : COL.azul, 'ISB', 'center', 6);
    ctx.restore();
  };
  const tc = cambioDia(t), u = (t - tc) / 0.16;
  dibujar(r, roja);
  if (u >= 0 && u < 1 && tc > 0) {            // la hoja anterior se arranca y cae
    const prev = restan(tc - 0.001);
    dibujar(prev, prev <= 1 && prev !== 30, (prev % 2 ? -1 : 1) * 0.5 * u, u * u * 220, 1 - u);
  }
  if (roja) { const k = 0.5 + 0.5 * Math.sin(t * 18); ctx.save(); ctx.globalAlpha = 0.18 * k; ctx.fillStyle = COL.rojo; ctx.fillRect(0, 0, W, H); ctx.restore(); }
}
function roundRect(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
function globo(s, ax, ay, t0, t1, t, tam = 40) {
  if (t < t0 || t > t1) return; const u = rebote((t - t0) / 0.18) * (1 - tramo(t, t1 - 0.1, t1));
  ctx.save(); ctx.translate(ax, ay); ctx.scale(u, u);
  ctx.font = `${tam}px ISB`; const w = ctx.measureText(s).width + 52, h = tam + 34;
  ctx.fillStyle = '#FFFFFF'; ctx.shadowColor = 'rgba(0,0,0,0.4)'; ctx.shadowBlur = 18; roundRect(-w / 2, -h - 22, w, h, h / 2); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-14, -24); ctx.lineTo(10, -24); ctx.lineTo(-8, 0); ctx.closePath(); ctx.fill(); ctx.shadowBlur = 0;
  ctx.fillStyle = COL.azul; ctx.textAlign = 'center'; ctx.fillText(s, 0, -22 - h / 2 + tam * 0.36); ctx.restore();
}
function insignia(ax, ay, t0, t, t1) {
  if (t < t0 || t > t1) return; const u = rebote((t - t0) / 0.22) * (1 - tramo(t, t1 - 0.12, t1));
  ctx.save(); ctx.translate(ax, ay); ctx.scale(u, u); ctx.shadowColor = 'rgba(156,200,236,0.8)'; ctx.shadowBlur = 30;
  ctx.fillStyle = COL.celeste; ctx.beginPath(); ctx.arc(0, 0, 46, 0, Math.PI * 2); ctx.fill(); ctx.shadowBlur = 0;
  ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 11; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(-19, 1); ctx.lineTo(-5, 16); ctx.lineTo(21, -14); ctx.stroke(); ctx.restore();
}
function capa(t) {
  // titulares (la historia se cuenta en tres renglones)
  texto('MISMO PLAZO.', W / 2, 190, 64, COL.blanco, 'IDB', 'center', 4);
  escribir('MISMA PARED.', TL.misma, t, W / 2, 262, 64, COL.celeste);
  escribir('DISTINTO MES.', TL.distinto, t, W / 2, 334, 64, COL.blanco);
  tarjeta(t);
  // rótulos de cada lado
  const yR = 705;
  texto('PROCRASTINADOR', W * 0.26, yR, 40, COL.humo, 'ISB', 'center', 3);
  texto('CONSTRUCTOR', W * 0.74, yR, 40, COL.humo, 'ISB', 'center', 3);
  // globos y señales sobre el procrastinador
  const cab = aPantalla(P.cuello.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.36, 0)));
  for (const [a, b] of TL.manana) globo('mañana…', cab[0] + 70, cab[1] - (nube.visible ? 70 : 0), a, b, t);
  if (t > TL.unDia + 0.02 && t < TL.unDia + 0.55) { const u = rebote((t - TL.unDia) / 0.15); ctx.save(); ctx.translate(cab[0], cab[1] - 30); ctx.scale(u, u); texto('!', 0, 0, 120, COL.rojo, 'IDB'); ctx.restore(); }
  if (t > TL.distinto + 0.35 && t < TL.reset + 0.7) { const k = (t - TL.distinto - 0.35); for (let i = 0; i < 3; i++) { const u = clamp(k * 1.6 - i * 0.35); if (u > 0) texto('z', cab[0] + 30 + i * 26 + u * 20, cab[1] + 20 - i * 34 - u * 30, 34 + i * 10, COL.humo, 'IDB', 'center', 0, 1 - tramo(t, TL.reset + 0.5, TL.reset + 0.7)); } }
  // insignias de "pared terminada" sobre las dos paredes
  const topeP = aPantalla(ranura(zonaP, N - 2).add(new THREE.Vector3(0, 0.38, 0))), topeC = aPantalla(ranura(zonaC, N - 2).add(new THREE.Vector3(0, 0.38, 0)));
  insignia(topeP[0], topeP[1], TL.hoy + 0.1, t, TL.reset); insignia(topeC[0], topeC[1], TL.hoy + 0.18, t, TL.reset);
}

function camara(t) {
  const cerca = tramo(t, TL.unDia, TL.hoy) * (1 - tramo(t, TL.distinto, TL.distinto + 0.6));
  const golpe = Math.exp(-Math.max(0, t - TL.hoy) * 9) * (t >= TL.hoy ? 1 : 0);
  const tiembla = (t > TL.unDia + 0.3 && t < TL.hoy) ? 0.018 : 0;
  camera.position.set(Math.sin(t * 41) * tiembla, 2.55 + Math.sin(t * 37) * tiembla - 0.12 * cerca, 8.2 - 0.6 * cerca + 0.25 * golpe);
  camera.lookAt(0, 1.50 - 0.05 * cerca, 0);
}
window.dibujar = (t) => {
  camara(t);
  ponerLadrillos(t);
  posar(C, poseC(t), zonaC); posar(P, poseP(t), zonaP);
  scene.updateMatrixWorld(true);
  celular(t); nubeYLluvia(t); luces(t);
  composer.render();
  ctx.clearRect(0, 0, W, H); ctx.drawImage(renderer.domElement, 0, 0);
  capa(t);
  return sal.toDataURL('image/png');
};
