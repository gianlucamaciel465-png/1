#!/usr/bin/env python3
"""Prepara evidencia audiovisual local. No califica creatividad ni edita reels.

Requiere FFmpeg/ffprobe y Pillow. yt-dlp es opcional para --descargar.
No instala paquetes, no accede a cookies ni descarga modelos de voz.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont, ImageOps


def ejecutar(args: list[str], timeout: int = 60) -> str:
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout or "Error sin detalle")[-3000:])
    return p.stdout


def guardar_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def comprobar_referencia(ref: dict) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", ref["id"]):
        raise ValueError("ID de referencia inválido")
    nombre = ref["archivo_esperado"]
    if Path(nombre).name != nombre or Path(nombre).suffix.lower() != ".mp4":
        raise ValueError("archivo_esperado debe ser un nombre MP4 sin carpetas")
    if ref.get("url"):
        parsed = urlparse(ref["url"])
        if parsed.scheme != "https" or parsed.hostname not in {"instagram.com", "www.instagram.com"}:
            raise ValueError("El importador solo admite enlaces HTTPS de Instagram")


def importar_publico(ref: dict, destino: Path) -> dict:
    if not ref.get("url"):
        return {"estado": "sin_enlace"}
    if importlib.util.find_spec("yt_dlp") is None:
        return {"estado": "falta_yt_dlp", "accion": "Usar MP4 local o instalar yt-dlp desde su distribución oficial."}
    log_path = destino.with_suffix(".descarga.log")
    args = [sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-playlist",
            "--retries", "0", "--fragment-retries", "0", "--socket-timeout", "15",
            "--max-filesize", "150M", "--no-overwrites", "--merge-output-format", "mp4",
            "--remux-video", "mp4", "-f", "bv*+ba/b", "-o",
            str(destino.with_suffix(".%(ext)s")), "--", ref["url"]]
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=60)
        log = (p.stdout or "") + "\n" + (p.stderr or "")
        log_path.write_text(log, encoding="utf-8")
        return {"estado": "descargado" if p.returncode == 0 and destino.exists() else "no_descargado",
                "codigo_salida": p.returncode, "log": str(log_path)}
    except subprocess.TimeoutExpired as exc:
        partes = []
        for value in [exc.stdout, exc.stderr]:
            if value:
                partes.append(value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value)
        log_path.write_text("\n".join(partes) + "\nTiempo máximo de 60 s alcanzado.", encoding="utf-8")
        return {"estado": "tiempo_agotado", "log": str(log_path)}


def contacto(items: list[tuple[Path, float]], destino: Path, titulo: str) -> None:
    cols, cell_w, cell_h = 4, 240, 456
    rows = math.ceil(len(items) / cols)
    canvas = Image.new("RGB", (cols * cell_w, rows * cell_h + 48), "#eceef0")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    draw.text((12, 14), titulo, fill="#151515", font=font)
    for n, (path, tiempo) in enumerate(items):
        x, y = (n % cols) * cell_w, (n // cols) * cell_h + 48
        draw.text((x + 8, y + 4), f"{tiempo:.2f} s", fill="#151515", font=font)
        with Image.open(path) as im:
            im = ImageOps.contain(im.convert("RGB"), (224, 418))
            canvas.paste(im, (x + (cell_w - im.width) // 2, y + 29))
    canvas.save(destino)


def extraer_muestras(video: Path, carpeta: Path, tiempos: list[float], nombre: str) -> list[tuple[Path, float]]:
    carpeta.mkdir(parents=True)
    items = []
    for n, tiempo in enumerate(tiempos):
        path = carpeta / f"{n:03d}_{tiempo:06.2f}s.jpg"
        ejecutar(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                  "-ss", f"{tiempo:.6f}", "-i", str(video), "-map", "0:v:0",
                  "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "3", str(path)])
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"No se pudo obtener el fotograma de {tiempo:.2f} s")
        items.append((path, tiempo))
    contacto(items, carpeta.parent / f"{nombre}.png", nombre)
    return items


def preparar(video: Path, ref: dict, salida: Path, modelo: str | None) -> dict:
    salida.mkdir(parents=True)
    raw = json.loads(ejecutar(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                              "-of", "json", str(video)]))
    stream = next((s for s in raw.get("streams", []) if s.get("codec_type") == "video"), None)
    if not stream:
        raise ValueError("El archivo no tiene una pista de video")
    dur = float(raw.get("format", {}).get("duration") or stream.get("duration") or 0)
    if not math.isfinite(dur) or not 0.05 < dur <= 90:
        raise ValueError("Duración fuera del rango de este preparador de reels: 0,05–90 s")
    rate = stream.get("avg_frame_rate", "30/1").split("/")
    fps = float(rate[0]) / float(rate[1]) if len(rate) == 2 and float(rate[1]) else 30
    margen = max(0.06, 2 / max(fps, 1))
    fin = max(0, dur - margen)
    inicio = sorted(set(round(min(n / 4, fin), 6) for n in range(13)))
    total = [round(fin * n / 19, 6) for n in range(20)]
    extraer_muestras(video, salida / "frames_hook", inicio, "01_hook_0_a_3s")
    extraer_muestras(video, salida / "frames_reel", total, "02_reel_completo_muestras")
    tiene_audio = any(s.get("codec_type") == "audio" for s in raw.get("streams", []))
    audio = salida / "audio_16k_mono.wav"
    if tiene_audio:
        ejecutar(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                  "-i", str(video), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", str(audio)])
    h = hashlib.sha256()
    with video.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    resultado = {"id": ref["id"], "estado": "preparado", "archivo": str(video),
                 "sha256": h.hexdigest(), "duracion_s": dur, "fps_medio": fps,
                 "ancho": stream.get("width"), "alto": stream.get("height"),
                 "tiene_audio": tiene_audio, "audio_escuchado": False,
                 "analisis_creativo_realizado_por_script": False,
                 "muestreo": "Búsqueda temporal con FFmpeg; confirmar cortes exactos en el MP4.",
                 "hoja_hook": str(salida / "01_hook_0_a_3s.png"),
                 "hoja_general": str(salida / "02_reel_completo_muestras.png")}
    if tiene_audio:
        resultado["audio_extraido"] = str(audio)
    if modelo and tiene_audio:
        try:
            from faster_whisper import WhisperModel
            motor = WhisperModel(modelo, device="cpu", compute_type="int8", local_files_only=True)
            segmentos, info = motor.transcribe(str(audio), beam_size=3, vad_filter=True)
            transcripcion = {"idioma_detectado": info.language, "segmentos":
                             [{"inicio": s.start, "fin": s.end, "texto": s.text} for s in segmentos],
                             "aviso": "ASR automático: corregir nombres y voseo. No equivale a audición."}
            guardar_json(salida / "transcripcion_automatica.json", transcripcion)
            resultado["transcripcion"] = "generada"
        except Exception as exc:
            resultado["transcripcion"] = "no_generada"
            resultado["detalle_transcripcion"] = str(exc)
    guardar_json(salida / "metadatos_ffprobe.json", raw)
    guardar_json(salida / "resultado.json", resultado)
    guardar_json(salida / "ficha_para_completar.json", {
        "id": ref["id"], "estado": "pendiente_de_revision_por_Claude",
        "observaciones_preliminares": ref.get("observado", []),
        "campos_a_completar_con_evidencia": {
            "primer_fotograma": None, "pregunta_del_hook": None,
            "cambio_visual_y_tiempo": None, "desenlace": None,
            "aporte_para_Rocce": None, "adaptacion_propuesta": None,
            "audio_realmente_revisado": False, "limitaciones": []}})
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).resolve().parent
    parser.add_argument("--manifest", type=Path, default=base / "referencias.json")
    parser.add_argument("--videos", type=Path, default=base / "VIDEOS")
    parser.add_argument("--salida", type=Path, default=base / "ANALISIS")
    parser.add_argument("--solo", nargs="+", help="IDs a preparar, por ejemplo R1 R4")
    parser.add_argument("--descargar", action="store_true", help="Intento público, sin credenciales ni cookies")
    parser.add_argument("--modelo-whisper", help="Modelo ya disponible en caché o carpeta local; nunca se descarga")
    args = parser.parse_args()
    for tool in ["ffmpeg", "ffprobe"]:
        if not shutil.which(tool):
            parser.error(f"Falta {tool}; instalarlo en el entorno antes de ejecutar")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    referencias = manifest["referencias"]
    for ref in referencias:
        comprobar_referencia(ref)
    if args.solo:
        desconocidos = set(args.solo) - {r["id"] for r in referencias}
        if desconocidos:
            parser.error("IDs desconocidos: " + ", ".join(sorted(desconocidos)))
        referencias = [r for r in referencias if r["id"] in args.solo]
    args.videos = args.videos.resolve()
    args.videos.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    corrida = args.salida.resolve() / stamp
    corrida.mkdir(parents=True)
    resultados = []
    for ref in referencias:
        video = args.videos / ref["archivo_esperado"]
        descarga = None
        if not video.is_file() and args.descargar:
            descarga = importar_publico(ref, video)
        if not video.is_file():
            r = {"id": ref["id"], "estado": "falta_mp4", "ruta_esperada": str(video),
                 "accion": "Aportar MP4 o grabación de pantalla; no inferir el contenido desde el título."}
        else:
            try:
                r = preparar(video, ref, corrida / ref["id"], args.modelo_whisper)
            except Exception as exc:
                r = {"id": ref["id"], "estado": "error_preparacion", "detalle": str(exc)}
        if descarga:
            r["descarga"] = descarga
        resultados.append(r)
        print(f"{ref['id']}: {r['estado']}", flush=True)
        guardar_json(corrida / "indice.json", {"corrida": stamp, "resultados": resultados})
    print("Índice: " + str(corrida / "indice.json"))
    return 0 if all(r["estado"] == "preparado" for r in resultados) else 2


if __name__ == "__main__":
    raise SystemExit(main())
