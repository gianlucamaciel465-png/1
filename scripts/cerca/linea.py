# Línea de tiempo de "ESTUVISTE CERCA" (segundos del reel) y audio de voz por toma para la sincronía labial.
# Uso: python linea.py VOZ_DIR SALIDA_DIR
import sys, json, numpy as np, soundfile as sf
VOZ = {  # frase: inicio en el reel
 "c1": 0.25, "a1": 3.30,
 "c2a": 5.30, "c2b": 8.60, "c2c": 11.50, "c2d": 14.00, "c2e": 15.60,
 "a2": 17.40,
 "c3a": 20.10, "c3b": 22.00, "c3c": 23.60,
 "a3": 27.20, "c4": 31.40,
 "a4a": 35.10, "a4b": 37.30,
}
TOMAS = [  # nombre, inicio, fin usado, duración generada (s enteros)
 ("S1_general", 0.0, 5.0, 5), ("S2_chico", 5.0, 17.0, 12), ("S3_abuela", 17.0, 19.8, 3),
 ("S4_chico_mar", 19.8, 25.8, 6), ("S5_agua", 25.8, 27.0, 2), ("S6_abuela", 27.0, 30.4, 4),
 ("S7_chico_si", 30.4, 32.2, 3), ("G1_entrega", 32.2, 34.8, 5), ("G2_frente", 34.8, 39.0, 5),
 ("G3_correa", 39.0, 40.0, 5), ("placa", 40.0, 44.0, 0)]
SR = 48000
if __name__ == "__main__":
    vd, out = sys.argv[1], sys.argv[2]
    voz = {k: sf.read(f"{vd}/{k}.wav")[0] for k in VOZ}
    for n, t0, t1, d in TOMAS:
        if not d: continue
        buf = np.zeros(int(d * SR))
        hay = False
        for k, t in VOZ.items():
            o = int(round((t - t0) * SR)); x = voz[k]
            if 0 <= o < len(buf) and t < t1:
                buf[o:o + len(x)] += x[:len(buf) - o]; hay = True
        if hay: sf.write(f"{out}/{n}.wav", buf.astype(np.float32), SR); print(n, d, "s con voz")
    json.dump({"voz": VOZ, "tomas": TOMAS}, open(f"{out}/linea.json", "w"), indent=1)
