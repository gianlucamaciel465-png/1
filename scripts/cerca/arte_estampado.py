# Extrae el estampado real del frente blanco (ROCCÉ / so f★cking close.) desde la macro de PRODUCTO/,
# como "albedo": color de la tinta relativo a la tela (tela = 1). Se compone multiplicando sobre la tela
# de la toma, así hereda su luz y sus pliegues. Alfa = cuánto se aparta de la tela (letras negras y estrella).
# Fondo = tela estimada con máximo local (borra las letras) + desenfoque.
# Uso: python arte_estampado.py SALIDA.png
import sys, cv2, numpy as np
im = cv2.imread("PRODUCTO/blanca_frente_detalle_estampado.jpg").astype(np.float32) / 255
x0, y0, x1, y1 = 170, 850, 1470, 1460
u8 = (im * 255).astype(np.uint8)
bg = cv2.GaussianBlur(cv2.dilate(u8, np.ones((71, 71), np.uint8)), (0, 0), 25).astype(np.float32) / 255 * 0.97
c, bg = im[y0:y1, x0:x1], bg[y0:y1, x0:x1]
alb = np.clip(c / np.maximum(bg, 1e-3), 0, 1)
oscuro = 1 - alb.mean(2)
azul = (c[..., 0] - c[..., 2]) - (bg[..., 0] - bg[..., 2])
a_neg = np.clip((oscuro - 0.30) / 0.40, 0, 1)
a_est = cv2.GaussianBlur(np.clip((azul - 0.06) / 0.05, 0, 1), (0, 0), 1.5)
a = np.maximum(a_neg, a_est)
tinta = alb.copy()
est = a_est > 0.5
tinta[est] = (0.92, 0.80, 0.68)   # estrella pareja (BGR): celeste de la macro (B/R ≈ 1,25) aclarado; la macro está subexpuesta
neg = (a_neg > 0.5) & ~est
tinta[neg] = np.minimum(tinta[neg], np.median(alb[a_neg > 0.9], 0) + 0.04)
out = (np.dstack([tinta, a]) * 255 + .5).astype(np.uint8)
ys, xs = np.nonzero(out[..., 3] > 20)
out = out[max(ys.min() - 6, 0):ys.max() + 7, max(xs.min() - 6, 0):xs.max() + 7]
cv2.imwrite(sys.argv[1], out)
print(out.shape, "estrella BGR", np.median(alb[est], 0).round(3), "negro", np.median(alb[a_neg > 0.9], 0).round(3))
