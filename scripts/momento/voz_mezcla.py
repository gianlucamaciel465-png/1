#!/usr/bin/env python3
"""MARCA_momento · locución Firme 04 como pista parámetro + mezcla con sidechain (LIB-1 y LIB-2). Pedro, 25/11/2026.

Voz (receta de .claude/skills/rocce-voz y scripts/voz/BANCO_VOCAL.md):
  GUION.tsv  id<TAB>texto a sintetizar («Royé» por Roccé, «fáunders» por founders; {APELLIDO} y otras llaves se
             reemplazan antes de sintetizar) → scripts/proxima/locucion.py (edge-tts es-AR-ElenaNeural +11 % / −20 Hz
             + tratamiento_firme.py) → scripts/proxima/palabras.py (tiempos por palabra, faster-whisper small).
  PLAN (voz_*_ubicacion.tsv)  id<TAB>entra<TAB>tope[<TAB>alternativa] (cuadros a 30 fps, guion 12 de Fede): resolver()
             mide la duración real (locucion.json) contra el tope y escribe ubicacion_resuelta.tsv (id<TAB>cuadro):
             si la frase pasa el tope, primero se adelanta la entrada dentro de la ventana (≥ 3 cuadros después del golpe
             anterior, después del tramo prohibido o de la frase anterior); si igual no entra, va la alternativa «b».
             Nunca se mueve un corte ni un golpe. Ninguna frase termina a menos de 3 cuadros del golpe siguiente.
  UBICACION resuelta  id<TAB>cuadro de entrada [<TAB>palabra<TAB>cuadro]: con palabra y cuadro, la frase se corre para
             que esa palabra empiece en ese cuadro (palabras.py).
Mezcla: la voz (locución + voz original de Muslera) maneja tres sidechaincompress (música, ambiente, golpes), con
apad=whole_dur en la señal que los maneja (si no, el compresor se corta cuando termina la voz). Ganancia a −14 LUFS y
alimiter level=false. Voz contra fondo frase por frase: se apaga la voz que se oye, no la que maneja el sidechain.
No se escucha nada: todo es medición (niveles, ebur128, transcripción).
"""
import json, math, os, subprocess, sys
from pathlib import Path
import numpy as np

R = Path('/home/user/1')
ENT = R / 'TRABAJO/entornos'
SR, FPS = 48000, 30
AF = 'aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo'


def sh(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], check=True, stdin=subprocess.DEVNULL, **kw)


# ---------------------------------------------------------------------------------------------- voz
def generar(tsv, salida, reemplazos=None, palabras=True):
    """Sintetiza el guion con Firme 04. Devuelve locucion.json (con palabras si palabras=True)."""
    salida = Path(salida); salida.mkdir(parents=True, exist_ok=True)
    lineas = []
    for l in open(tsv, encoding='utf-8'):
        if not l.strip() or l.startswith('#'):
            continue
        for k, v in (reemplazos or {}).items():
            l = l.replace('{' + k + '}', v)
        if '{' in l:
            raise ValueError(f'llave sin reemplazar: {l.strip()}')
        lineas.append(l.rstrip('\n'))
    g = salida / 'guion_sintesis.tsv'
    previo = {}
    if (salida / 'textos_sintetizados.json').exists():
        previo = json.load(open(salida / 'textos_sintetizados.json'))
    elif (salida / 'locucion.json').exists():
        previo = {f['id']: f['texto_sintetizado'] for f in json.load(open(salida / 'locucion.json'))['frases']}
    actual = dict(l.split('\t', 1) for l in lineas)
    for fid, texto in actual.items():     # locucion.py reutiliza <id>_base.mp3 por id: si el texto cambió, se borra
        if previo.get(fid) != texto:
            for suf in ('_base.mp3', '_tratada.wav', '.wav'):
                (salida / f'{fid}{suf}').unlink(missing_ok=True)
    json.dump(actual, open(salida / 'textos_sintetizados.json', 'w'), ensure_ascii=False, indent=1)
    g.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    env = dict(os.environ, VOZ_PY=str(ENT / 'voz-env/bin/python'))
    sh(['python3', R / 'scripts/proxima/locucion.py', g, salida], env=env)
    if palabras:
        sh([ENT / 'whisper-env/bin/python', '-I', R / 'scripts/proxima/palabras.py', salida])
    return json.load(open(salida / 'locucion.json'))


def leer_ubicacion(tsv):
    u = {}
    for l in open(tsv, encoding='utf-8'):
        if not l.strip() or l.startswith('#'):
            continue
        c = l.rstrip('\n').split('\t')
        u[c[0]] = dict(f0=int(c[1]), palabra=(c[2] if len(c) > 2 and c[2] else None),
                       f_palabra=(int(c[3]) if len(c) > 3 and c[3] else None))
    return u


def leer_plan(tsv):
    plan = []
    for l in open(tsv, encoding='utf-8'):
        if not l.strip() or l.startswith('#'):
            continue
        c = l.rstrip('\n').split('\t')
        plan.append(dict(id=c[0], entra=int(c[1]), tope=int(c[2]), alt=(c[3] if len(c) > 3 and c[3] else None)))
    return plan


def resolver(loc_dir, plan_tsv, golpes, prohibidas=(), salida=None, margen=3, forzar=None, topes='guion', nf=None):
    """Entrada, tope y alternativa de cada frase según la duración real. golpes = cuadros de los golpes (no se mueven);
    prohibidas = [(f0, f1, nombre)] con f1 exclusivo (voz de Muslera, giro, S4…). forzar = {id: id_elegido} para una
    alternativa decidida por otro motivo (p. ej. inscripción ilegible). topes='guion' usa el tope de cada frase (regla
    del guion 12); topes='duros', o un conjunto de ids (decisión 14 de Roma), usa solo los límites duros: golpe siguiente − 3, voz o tramo
    prohibido − 3, entrada de la frase siguiente − 1 y final del video − 3. Devuelve (decisiones, avisos)."""
    loc = {f['id']: f for f in json.load(open(Path(loc_dir) / 'locucion.json'))['frases']}
    golpes = sorted(set(golpes)); dec, avisos, fin_prev = [], [], 0
    plan_l = leer_plan(plan_tsv)
    for k_p, p in enumerate(plan_l):
        e = p['entra']
        g_ant = [g for g in golpes if g <= e]; g_sig = [g for g in golpes if g > e]
        wmin = max([fin_prev] + [g + margen for g in g_ant] + [x[1] for x in prohibidas if x[1] <= e])
        # (f0, f1, nombre[, guarda]): guarda = cuadros libres antes del tramo (3 antes de una voz, 0 antes de un silencio)
        duros = [g - margen for g in g_sig] + [x[0] - (x[3] if len(x) > 3 else 0) for x in prohibidas if x[0] > e]
        if topes == 'duros' or (not isinstance(topes, str) and p['id'] in topes):
            duros += ([plan_l[k_p + 1]['entra'] - 1] if k_p + 1 < len(plan_l) else []) + ([nf - margen] if nf else [])
            tmax = min(duros)
        else:
            tmax = min([p['tope']] + duros)
        cands = [p['id']] + ([p['alt']] if p['alt'] else [])
        if forzar and p['id'] in forzar:
            cands = [forzar[p['id']]]
        d = None
        for fid in cands:
            durf = loc[fid]['duracion'] * FPS
            f0 = e
            if f0 < wmin:
                avisos.append(f"{p['id']}: el guion la hace entrar en f{e}, a menos de {margen} cuadros del golpe o "
                              f"tramo anterior; entra en f{wmin} (no se mueve el golpe)")
                f0 = wmin
            if f0 + durf <= tmax:
                acc = 'entra en su cuadro' if f0 == e else f'se atrasa {f0 - e} cuadro(s) por la ventana'
            elif math.floor(tmax - durf) >= wmin:
                f0 = math.floor(tmax - durf); acc = f'pasa el tope: se adelanta {e - f0} cuadro(s)'
            else:
                continue
            d = dict(plan=p['id'], id=fid, alternativa=fid != p['id'], entra_guion=e, tope=p['tope'], ventana=[wmin, tmax],
                     f0=f0, fin_f=round(f0 + durf, 1), dur_s=loc[fid]['duracion'], dur_f=round(durf, 1), accion=acc)
            break
        if d is None:      # no entra ni adelantada ni con la alternativa: BLOQUEO, no se coloca (corte parcial) y se informa
            fid = cands[-1]; durf = loc[fid]['duracion'] * FPS; f0 = max(e, wmin)
            d = dict(plan=p['id'], id=fid, alternativa=fid != p['id'], entra_guion=e, tope=p['tope'], ventana=[wmin, tmax],
                     f0=None, fin_f=None, dur_s=loc[fid]['duracion'], dur_f=round(durf, 1), bloqueada=True,
                     disponible_f=tmax - wmin, falta_f=round(durf - (tmax - wmin), 1),
                     accion=f'BLOQUEO: dura {durf:.1f} cuadros y la ventana f{wmin}–f{tmax} tiene {tmax - wmin}; no se coloca')
            avisos.append(f"{p['id']}: {d['accion']}")
            dec.append(d); continue
        if d['alternativa']:
            d['accion'] += f" · alternativa {d['id']}"
        dec.append(d); fin_prev = math.ceil(d['fin_f'])
    if salida:
        Path(salida).write_text('# id\tcuadro de entrada (resuelto por voz_mezcla.resolver)\n' +
                                ''.join(f"{d['id']}\t{d['f0']}\n" for d in dec if not d.get('bloqueada')), encoding='utf-8')
    return dec, avisos


def _wav(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def _rms_db(a):
    return 20 * np.log10(np.sqrt(np.mean(np.square(a, dtype=np.float64))) + 1e-12)


def pista(loc_dir, ubic_tsv, nf, prohibidas=(), nivel_db=-18.0, ganancias=None, solo=None):
    """Coloca cada frase en su cuadro. prohibidas = [(f0, f1, nombre)] tramos que la locución no puede pisar
    (voz de Muslera). Devuelve (estéreo float32, frases, avisos)."""
    loc = json.load(open(Path(loc_dir) / 'locucion.json'))
    ub = leer_ubicacion(ubic_tsv)
    N = int(round(nf / FPS * SR)); out = np.zeros((N, 2), np.float32)
    frases, avisos = [], []
    for f in loc['frases']:
        if solo is not None and f['id'] not in solo:      # alternativa no elegida
            continue
        if f['id'] not in ub:
            avisos.append(f"{f['id']}: sin ubicación, no se coloca"); continue
        u = ub[f['id']]
        a = _wav(Path(loc_dir) / f"{f['id']}.wav")
        a = a * 10 ** ((nivel_db + (ganancias or {}).get(f['id'], 0.0) - _rms_db(a)) / 20)
        t0 = u['f0'] / FPS
        if u['palabra']:
            w = next((w for w in f.get('palabras', []) if u['palabra'].lower() in w[0].lower()), None)
            if w is None:
                avisos.append(f"{f['id']}: no encontré «{u['palabra']}» en las palabras; queda en f{u['f0']}")
            else:
                t0 = u['f_palabra'] / FPS - w[1]
        i = int(round(t0 * SR)); j = min(N, i + len(a))
        if i < 0 or i + len(a) > N:
            avisos.append(f"{f['id']}: se sale del video ({t0:.2f}–{t0 + len(a) / SR:.2f} s)")
        out[max(0, i):j] += a[max(0, -i):j - i]
        t1 = t0 + len(a) / SR
        for (p0, p1, nom, *_) in prohibidas:
            if t0 < p1 / FPS and t1 > p0 / FPS:
                avisos.append(f"{f['id']}: pisa {nom} (f{p0}–{p1 - 1}): {t0:.2f}–{t1:.2f} s")
        frases.append(dict(id=f['id'], texto=f['texto_sintetizado'], t0=round(t0, 3), t1=round(t1, 3),
                           f0=int(round(t0 * FPS)), f1=int(round(t1 * FPS)), dur=f['duracion'],
                           palabras=[[w[0], round(t0 + w[1], 2), round(t0 + w[2], 2)] for w in f.get('palabras', [])]))
    frases.sort(key=lambda x: x['t0'])
    for x, y in zip(frases, frases[1:]):
        if y['t0'] < x['t1']:
            avisos.append(f"{x['id']} y {y['id']} se superponen ({y['t0']:.2f} < {x['t1']:.2f} s)")
    return out, frases, avisos


# ---------------------------------------------------------------------------------------------- mezcla
def escribir(a, p):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a',
                    'pcm_f32le', str(p)], input=np.ascontiguousarray(a, np.float32).tobytes(), check=True)
    return p


def _mezcla(st, dur, salida, voz_oir=0.0, mus_db=0.0, amb_db=0.0, fx_db=0.0, gan=0.0, limite=None):
    ins = []
    for k in ('loc', 'voz', 'mus', 'amb', 'fx'):
        ins += ['-i', str(st[k])]
    lim = f',alimiter=limit={limite}:attack=3:release=60:asc=1:level=false' if limite else ''
    fc = (f'[0:a]{AF}[l];[1:a]{AF}[o];[l][o]amix=inputs=2:normalize=0:duration=longest,apad=whole_dur={dur:.4f},'
          f'asplit=4[v0][sc1][sc2][sc3];[v0]volume={voz_oir}dB[voz];'
          f'[2:a]{AF},volume={mus_db}dB[m0];[m0][sc1]sidechaincompress=threshold=0.02:ratio=6:attack=10:release=260:makeup=1[mus];'
          f'[3:a]{AF},volume={amb_db}dB[a0];[a0][sc2]sidechaincompress=threshold=0.03:ratio=3:attack=10:release=250:makeup=1[amb];'
          f'[4:a]{AF},volume={fx_db}dB[f0];[f0][sc3]sidechaincompress=threshold=0.02:ratio=8:attack=5:release=200:makeup=1[fx];'
          f'[voz][mus][amb][fx]amix=inputs=4:normalize=0:duration=longest,atrim=0:{dur:.4f},volume={gan}dB{lim}[au]')
    sh(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', fc, '-map', '[au]', '-c:a', 'pcm_f32le', '-ar', SR,
        salida])
    d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                                       str(salida)]).decode())
    assert abs(d - dur) < 0.03, f'la mezcla dura {d:.3f} s y el video {dur:.3f} s'
    return salida


def ebur(p):
    r = subprocess.run(['ffmpeg', '-nostats', '-i', str(p), '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    g = lambda k: float([l for l in r.splitlines() if l.strip().startswith(k)][-1].split()[1])
    return dict(lufs_integrado=g('I:'), lra=g('LRA:'), pico_dbtp=g('Peak:'))


PICO_MAX = -1.5    # dBTP en la mezcla WAV, para que el MP4 (AAC sube ≈ 0,2 dB) quede ≤ −1,3 dBTP (decisión 14 de Roma)


def _una(st, dur, salida, nv, tramos_voz, objetivo):
    salida = Path(salida); pre = salida.with_name(salida.stem + '_pre.wav')
    _mezcla(st, dur, pre, **nv)
    m0 = ebur(pre); gan = objetivo - m0['lufs_integrado']; techo = -1.6
    for _ in range(6):
        _mezcla(st, dur, salida, gan=round(gan, 2), limite=round(10 ** (techo / 20), 4), **nv)
        m = ebur(salida)
        if abs(m['lufs_integrado'] - objetivo) <= 0.3 and m['pico_dbtp'] <= PICO_MAX:
            break
        gan += objetivo - m['lufs_integrado']
        if m['pico_dbtp'] > PICO_MAX:
            techo -= 0.4
    med = dict(sonoridad=m, ganancia_db=round(gan, 2), techo_dbfs=techo, niveles_fondo_db=nv, voz_vs_fondo=[])
    if tramos_voz:
        sv = salida.with_name(salida.stem + '_solo_voz.wav'); sf = salida.with_name(salida.stem + '_solo_fondo.wav')
        _mezcla(st, dur, sv, gan=round(gan, 2), **dict(nv, mus_db=-120, amb_db=-120, fx_db=-120))
        _mezcla(st, dur, sf, voz_oir=-120, gan=round(gan, 2), **nv)
        V, F = _wav(sv), _wav(sf)
        for nom, t0, t1 in tramos_voz:
            i, j = int(t0 * SR), int(t1 * SR)
            v, f = _rms_db(V[i:j]), _rms_db(F[i:j])
            med['voz_vs_fondo'].append(dict(tramo=nom, t0=round(t0, 2), t1=round(t1, 2), voz_db=round(v, 1),
                                            fondo_db=round(f, 1), diferencia_db=round(v - f, 1),
                                            ok=bool(10 <= v - f <= 15 or f < -80)))
        sv.unlink(); sf.unlink()
    pre.unlink()
    return med


def mezclar(st, dur, salida, niveles=None, tramos_voz=(), objetivo=-14.0, auto=True, meta=12.5, auto_claves=None):
    """st: dict de WAV {loc, voz, mus, amb, fx}. tramos_voz: [(nombre, t0, t1)] para medir voz contra fondo.
    auto: si la mediana voz−fondo cae fuera de 11–14 dB, corre el fondo entero (música, ambiente, golpes) hasta `meta`
    y vuelve a mezclar una vez (auto_claves limita qué capas se corren: en la mezcla sin música solo el ambiente, para
    no subir los golpes). Los golpes bajan con la voz con más fuerza (ratio 8) que la música y el ambiente. Devuelve medidas (sonoridad, ganancia, niveles y voz/fondo por tramo)."""
    nv = {**dict(mus_db=0.0, amb_db=0.0, fx_db=0.0), **(niveles or {})}
    med = _una(st, dur, salida, nv, tramos_voz, objetivo)
    difs = [t['diferencia_db'] for t in med['voz_vs_fondo'] if t['fondo_db'] > -80]   # sin fondo no cuenta
    if auto and difs and not 11 <= float(np.median(difs)) <= 14:
        d = max(-8.0, min(8.0, float(np.median(difs)) - meta))
        nv = {k: (v if v <= -100 or (auto_claves and k not in auto_claves) else round(v + d, 1)) for k, v in nv.items()}
        med = _una(st, dur, salida, nv, tramos_voz, objetivo)
        med['ajuste_fondo_db'] = round(d, 1)
    return med


def ganancias_frases(med, ids, meta=12.5, tope=4.0, fondo_min=None):
    """Corrección de nivel por frase (dB) para las que quedaron fuera de 10,5–14,5 dB sobre el fondo. fondo_min: con el
    fondo por debajo de ese nivel (silencio a propósito) no se corrige (se usa para la voz de Muslera)."""
    g = {}
    for t in med['voz_vs_fondo']:
        if fondo_min is not None and t['fondo_db'] < fondo_min:
            continue
        if t['tramo'] in ids and not 10.5 <= t['diferencia_db'] <= 14.5:
            g[t['tramo']] = round(max(-tope, min(tope, meta - t['diferencia_db'])), 1)
    return g


def escalar_tramos(src, tramos, salida, fundido=0.02):
    """Copia `src` con ganancia por tramo [(t0, t1, dB)] y fundidos de 20 ms (nivel de la voz de Muslera por tramo)."""
    a = _wav(src); env = np.ones(len(a), np.float32); nf = int(fundido * SR)
    for t0, t1, db in tramos:
        i, j = int(t0 * SR), min(len(a), int(t1 * SR)); g = 10 ** (db / 20)
        seg = np.full(j - i, g, np.float32)
        r = np.linspace(1, g, nf, dtype=np.float32); seg[:nf] = r[:j - i][:nf]; seg[-nf:] = r[::-1][-nf:] if j - i >= nf else seg[-nf:]
        env[i:j] = seg
    return escribir(a * env[:, None], salida)
