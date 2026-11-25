"""V5 · salto de nivel en la banda de cada golpe, medido sobre el audio decodificado del MP4 (no sobre las pistas).
Uso: python life_v5_golpes.py máster.mp4 eventos.json salida.json [carpeta_de_pistas prefijo]
Banda por tipo: sello 45–200 Hz (golpe grave) y 700–3200 Hz (palmada); obturador 2–8 kHz; impacto 30–150 Hz;
barrido 1–6 kHz. Ventana: 100 ms antes (terminando 15 ms antes del evento) contra 80 ms desde el evento (obturador: 25 ms;
el barrido sube hacia el corte: se compara el pico de 50 ms en ±150 ms contra 100 ms 300 ms antes).
Con las pistas (WAV por pista que escribe la mezcla, ya con el hueco y los despejes), cada obturador se mide además
contra la suma del resto de las pistas en su misma ventana (2–8 kHz y 4–10 kHz, 30 ms y 10 ms)."""
import json, subprocess, sys
import numpy as np
from scipy.signal import butter, sosfiltfilt

SR = 48000
BANDAS = {'sello': [(45, 200), (700, 3200)], 'obturador': [(2000, 8000)], 'impacto': [(30, 150)], 'barrido': [(1000, 6000)]}


def audio(mp4):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-i', mp4, '-map', '0:a:0', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).astype(np.float64)


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def main(mp4, ev_json, out):
    x = audio(mp4)
    ev = [e for e in json.load(open(ev_json))['eventos'] if e['evento'] in BANDAS]
    filas = []
    for e in sorted(ev, key=lambda e: e['t']):
        for lo, hi in BANDAS[e['evento']]:
            y = sosfiltfilt(butter(4, [lo, hi], 'band', fs=SR, output='sos'), x)
            n = int(round(e['t'] * SR))
            if e['evento'] == 'barrido':
                antes = y[max(0, n - int(.40 * SR)):n - int(.30 * SR)]
                seg = [rms_db(y[k:k + int(.05 * SR)]) for k in range(n - int(.15 * SR), n + int(.10 * SR), int(.01 * SR))]
                k = int(np.argmax(seg)); despues_db = seg[k]; pico_ms = -150 + 10 * k
            else:
                antes = y[max(0, n - int(.115 * SR)):n - int(.015 * SR)]
                despues_db = rms_db(y[n:n + int((.025 if e['evento'] == 'obturador' else .08) * SR)]); pico_ms = None
            filas.append(dict(t=e['t'], cuadro=e['cuadro'], evento=e['evento'], banda_hz=[lo, hi],
                              antes_db=round(rms_db(antes), 1), despues_db=round(despues_db, 1),
                              salto_db=round(despues_db - rms_db(antes), 1), pico_barrido_ms=pico_ms))
    obt = []
    if len(sys.argv) > 5:
        import os
        import soundfile as sf
        car, pre = sys.argv[4], sys.argv[5]
        P = {}
        for p_ in ('fx', 'amb', 'mus', 'bombo'):
            f = os.path.join(car, f'{pre}_{p_}.wav')
            if os.path.exists(f):
                a, _ = sf.read(f); P[p_] = a.mean(1) if a.ndim > 1 else a
        for lo, hi in ((2000, 8000), (4000, 10000)):
            sos = butter(4, [lo, hi], 'band', fs=SR, output='sos')
            Q = {k: sosfiltfilt(sos, v) for k, v in P.items()}
            fondo = sum(v for k, v in Q.items() if k != 'fx')
            for e in sorted(ev, key=lambda e: e['t']):
                if e['evento'] != 'obturador':
                    continue
                n = int(round(e['t'] * SR))
                fila = dict(t=e['t'], cuadro=e['cuadro'], banda_hz=[lo, hi])
                for w in (30, 10):
                    k = int(w / 1000 * SR)
                    fila[f'obturador_db_{w}ms'] = round(rms_db(Q['fx'][n:n + k]), 1)
                    fila[f'resto_db_{w}ms'] = round(rms_db(fondo[n:n + k]), 1)
                    fila[f'margen_db_{w}ms'] = round(fila[f'obturador_db_{w}ms'] - fila[f'resto_db_{w}ms'], 1)
                obt.append(fila)
    json.dump(dict(archivo=mp4, metodo=__doc__, golpes=filas, obturador_contra_resto=obt), open(out, 'w'), indent=1,
              ensure_ascii=False)
    for f in obt:
        print(f"obturador {f['t']:.3f} c{f['cuadro']} {f['banda_hz']} margen 30 ms {f['margen_db_30ms']:+.1f} · 10 ms {f['margen_db_10ms']:+.1f} dB")
    for f in filas:
        print(f"{f['t']:.3f} c{f['cuadro']} {f['evento']:9s} {f['banda_hz']} salto {f['salto_db']:+.1f} dB"
              + (f" pico {f['pico_barrido_ms']} ms" if f['pico_barrido_ms'] is not None else ''))


if __name__ == '__main__':
    main(*sys.argv[1:4])
