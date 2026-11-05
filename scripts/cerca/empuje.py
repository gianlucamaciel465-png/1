# Acercamiento lento sobre el plano del frente (para que el estampado se lea mejor), con remuestreo subpíxel.
# El punto P (el estampado) queda fijo en pantalla; zoom de 1 a Z a lo largo de los cuadros.
# Uso: python empuje.py ENTRADA_DIR SALIDA_DIR Px,Py Z
import sys, os, glob, cv2, numpy as np
src, dst = sys.argv[1], sys.argv[2]; px, py = map(float, sys.argv[3].split(",")); Z = float(sys.argv[4])
os.makedirs(dst, exist_ok=True); fs = sorted(glob.glob(src + "/*.png")); n = len(fs)
for i, f in enumerate(fs):
    im = cv2.imread(f); u = i / max(1, n - 1); z = 1 + (Z - 1) * (u * u * (3 - 2 * u))   # suave al entrar y al salir
    M = np.array([[z, 0, px - z * px], [0, z, py - z * py]], np.float32)
    cv2.imwrite(f"{dst}/{i + 1:04d}.png", cv2.warpAffine(im, M, (im.shape[1], im.shape[0]), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT))
print(n, "cuadros")
