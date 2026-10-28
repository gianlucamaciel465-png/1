# Planos de la referencia de escalada (Neuron Visuals), cuadros 1-based a 30 fps del recorte 1080×1920
# (grabación de pantalla 1170×2532 → recorte 1170×2080 desde y=203 → 1080×1920).
# Cortes medidos por diferencia entre cuadros. Rótulos: cajas (x, y, ancho, alto) de las letras en el cuadro "ref".
ROT = ["SUCCESS", "BUILD AN", "EMPIRE", "START A", "BUSINESS", "DREAM", "WORK"]
def _c(*cajas): return dict(zip(ROT, cajas))
PLANOS = {
    "A_general":      {"cuadros": (1, 72), "ref": 36, "rotulos": _c((748, 376, 182, 25), (763, 530, 192, 25), (763, 569, 147, 25),
                                                                    (772, 699, 171, 25), (772, 738, 202, 25), (765, 868, 129, 25), (758, 1037, 106, 25))},
    "B_grupo":        {"cuadros": (73, 123)},
    "C_escalador":    {"cuadros": (124, 186), "ref": 124, "rotulos": _c((665, 494, 240, 33), (691, 765, 237, 33), (691, 815, 193, 33),
                                                                        (707, 1060, 224, 33), (707, 1111, 265, 32), (695, 1356, 170, 33), (682, 1651, 140, 33))},
    "D_general":      {"cuadros": (187, 222), "ref": 205, "rotulos": _c((732, 468, 195, 26), (748, 633, 206, 27), (748, 674, 157, 27),
                                                                        (757, 814, 183, 27), (757, 855, 217, 27), (750, 995, 139, 26), (742, 1175, 114, 27))},
    "E_cima":         {"cuadros": (223, 302), "ref": 262, "rotulos": _c((542, 865, 239, 32), (565, 1096, 233, 33), (565, 1146, 192, 33),
                                                                        (578, 1349, 224, 32), (578, 1399, 265, 32), (567, 1601, 170, 33), (557, 1853, 139, 33))},
    "F_general_cima": {"cuadros": (303, 372), "ref": 340, "rotulos": _c((758, 544, 176, 24), (772, 693, 186, 24), (772, 730, 142, 24),
                                                                        (781, 856, 165, 24), (781, 893, 195, 24), (774, 1019, 125, 24), (767, 1182, 103, 24))},
    "G_grupo_idea":   {"cuadros": (373, 477)},
}
FIN_ANIM = 475          # último cuadro usado (15,80 s): el fundido a negro termina en 474
