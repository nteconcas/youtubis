"""
NTEtube - YouTube Downloader Web
Aplicativo web em Flask para baixar musicas e videos do YouTube
Usando Jinja2, Font Awesome e yt-dlp

Para rodar:
    python app.py
Ou em producao:
    gunicorn -w 4 -b 0.0.0.0:5540 app:app

Requisitos: pip install -r requirements.txt
"""

import os
import re
import json
import hashlib
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from yt_dlp import YoutubeDL

# Configuracoes
BASE_DIR = Path(__file__).parent.resolve()
DOWNLOAD_DIR = BASE_DIR / "downloads"
HISTORY_FILE = BASE_DIR / ".download_history.json"
MAX_HISTORY = 100
CLEANUP_INTERVAL_HOURS = 24

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ntetube-secret-key-2026")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["DOWNLOAD_FOLDER"] = str(DOWNLOAD_DIR)

DOWNLOAD_DIR.mkdir(exist_ok=True)
download_locks = {}


# Filtros Jinja2
@app.template_filter("filesize")
def format_filesize_filter(value):
    """Filtro Jinja2 para formatar tamanho de arquivo."""
    if not value:
        return "N/A"
    try:
        bytes_size = int(value)
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"
    except (ValueError, TypeError):
        return "N/A"


# Utilitarios
def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'[\x00-\x1f]', '', filename)
    filename = filename.strip().rstrip('.')
    if len(filename) > 150:
        filename = filename[:150]
    return filename or "download"


def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "N/A"
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def is_valid_youtube_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'^https?://youtu\.be/[\w-]+',
        r'^https?://(www\.)?youtube\.com/shorts/[\w-]+',
        r'^https?://(www\.)?youtube\.com/live/[\w-]+',
        r'^https?://music\.youtube\.com/watch\?v=[\w-]+',
    ]
    return any(re.match(pattern, url.strip()) for pattern in patterns)


def extract_video_id(url: str) -> Optional[str]:
    patterns = [
        r'(?:v=|/)([\w-]{11})(?:[?&]|$)',
        r'youtu\.be/([\w-]{11})',
        r'shorts/([\w-]{11})',
        r'live/([\w-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def generate_download_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def load_history() -> List[Dict]:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [h for h in data if h.get('file_exists', True)]
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_history(history: List[Dict]):
    try:
        history = history[-MAX_HISTORY:]
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError:
        pass


def add_to_history(entry: Dict):
    history = load_history()
    history.append(entry)
    save_history(history)


def cleanup_old_files():
    try:
        cutoff = datetime.now() - timedelta(hours=CLEANUP_INTERVAL_HOURS)
        for file_path in DOWNLOAD_DIR.iterdir():
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff:
                    file_path.unlink()
                    print(f"[CLEANUP] Removido: {file_path.name}")
    except Exception as e:
        print(f"[CLEANUP] Erro: {e}")


def start_cleanup_thread():
    def cleanup_loop():
        while True:
            time.sleep(CLEANUP_INTERVAL_HOURS * 3600)
            cleanup_old_files()
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()


# YT-DLP Manager
class YTDLManager:
    @staticmethod
    def get_info(url: str) -> Optional[Dict]:
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            print(f"[INFO] Erro: {e}")
            return None

    @staticmethod
    def list_formats(url: str) -> Optional[List[Dict]]:
        info = YTDLManager.get_info(url)
        if not info or 'formats' not in info:
            return None

        formats = []
        for f in info['formats']:
            formats.append({
                'format_id': f.get('format_id', 'N/A'),
                'ext': f.get('ext', 'N/A'),
                'resolution': f.get('resolution', 'audio only'),
                'fps': f.get('fps', 'N/A'),
                'filesize': f.get('filesize') or f.get('filesize_approx', 0),
                'vcodec': f.get('vcodec', 'none')[:20] if f.get('vcodec') != 'none' else '-',
                'acodec': f.get('acodec', 'none')[:20] if f.get('acodec') != 'none' else '-',
                'abr': f.get('abr', 'N/A'),
                'vbr': f.get('vbr', 'N/A'),
                'asr': f.get('asr', 'N/A'),
                'audio_channels': f.get('audio_channels', 'N/A'),
                'quality': f.get('quality', 'N/A'),
                'note': f.get('format_note', ''),
            })
        return formats

    @staticmethod
    def download_video(url: str, quality: str = "best", output_dir: str = None) -> Dict:
        output_dir = output_dir or str(DOWNLOAD_DIR)
        download_id = generate_download_id(url + quality + "video")

        if download_id in download_locks:
            return {"success": False, "error": "Download ja em andamento"}

        download_locks[download_id] = True

        try:
            if quality == "best":
                format_str = "bestvideo+bestaudio/best"
            elif quality == "worst":
                format_str = "worstvideo+worstaudio/worst"
            elif quality.endswith('p'):
                height = quality.replace('p', '')
                format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
            else:
                format_str = quality

            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s [%(id)s].%(ext)s'),
                'format': format_str,
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                }],
                'writethumbnail': True,
                'embedthumbnail': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if not os.path.exists(filename):
                    base = os.path.splitext(filename)[0]
                    for ext in ['.mp4', '.webm', '.mkv']:
                        if os.path.exists(base + ext):
                            filename = base + ext
                            break

                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    entry = {
                        "id": download_id,
                        "url": url,
                        "title": info.get('title', 'Desconhecido'),
                        "channel": info.get('uploader', 'Desconhecido'),
                        "mode": "video",
                        "quality": quality,
                        "format": "mp4",
                        "filename": os.path.basename(filename),
                        "filepath": filename,
                        "filesize": file_size,
                        "duration": info.get('duration'),
                        "thumbnail": info.get('thumbnail', ''),
                        "date": datetime.now().isoformat(),
                        "file_exists": True
                    }
                    add_to_history(entry)
                    return {"success": True, "data": entry}
                else:
                    return {"success": False, "error": "Arquivo nao encontrado apos download"}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            download_locks.pop(download_id, None)

    @staticmethod
    def download_audio(url: str, audio_format: str = "mp3", quality: str = "best", output_dir: str = None) -> Dict:
        output_dir = output_dir or str(DOWNLOAD_DIR)
        download_id = generate_download_id(url + audio_format + quality + "audio")

        if download_id in download_locks:
            return {"success": False, "error": "Download ja em andamento"}

        download_locks[download_id] = True

        try:
            if quality == "best":
                abr = "320"
            elif quality == "worst":
                abr = "96"
            elif quality.endswith('k'):
                abr = quality.replace('k', '')
            else:
                abr = "192"

            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s [%(id)s].%(ext)s'),
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': audio_format,
                        'preferredquality': abr,
                    },
                    {
                        'key': 'FFmpegMetadata',
                        'add_metadata': True,
                    },
                    {
                        'key': 'EmbedThumbnail',
                    }
                ],
                'writethumbnail': True,
                'embedthumbnail': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base = os.path.splitext(filename)[0]

                actual_file = base + "." + audio_format
                if not os.path.exists(actual_file):
                    for ext in [audio_format, 'm4a', 'mp3', 'webm', 'opus']:
                        test = base + "." + ext
                        if os.path.exists(test):
                            actual_file = test
                            break

                if os.path.exists(actual_file):
                    file_size = os.path.getsize(actual_file)
                    entry = {
                        "id": download_id,
                        "url": url,
                        "title": info.get('title', 'Desconhecido'),
                        "channel": info.get('uploader', 'Desconhecido'),
                        "mode": "audio",
                        "quality": f"{abr}k",
                        "format": audio_format,
                        "filename": os.path.basename(actual_file),
                        "filepath": actual_file,
                        "filesize": file_size,
                        "duration": info.get('duration'),
                        "thumbnail": info.get('thumbnail', ''),
                        "date": datetime.now().isoformat(),
                        "file_exists": True
                    }
                    add_to_history(entry)
                    return {"success": True, "data": entry}
                else:
                    return {"success": False, "error": "Arquivo nao encontrado apos download"}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            download_locks.pop(download_id, None)


# Rotas Flask
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/info", methods=["POST"])
def info():
    url = request.form.get("url", "").strip()

    if not is_valid_youtube_url(url):
        flash("URL invalida. Insira um link valido do YouTube.", "error")
        return redirect(url_for("index"))

    info_data = YTDLManager.get_info(url)
    if not info_data:
        flash("Nao foi possivel obter informacoes do video.", "error")
        return redirect(url_for("index"))

    video_info = {
        "title": info_data.get("title", "Desconhecido"),
        "channel": info_data.get("uploader", "Desconhecido"),
        "duration": format_duration(info_data.get("duration")),
        "duration_seconds": info_data.get("duration"),
        "views": info_data.get("view_count", 0),
        "likes": info_data.get("like_count", 0),
        "upload_date": info_data.get("upload_date", ""),
        "description": info_data.get("description", ""),
        "thumbnail": info_data.get("thumbnail", ""),
        "url": url,
        "video_id": extract_video_id(url),
        "is_playlist": "entries" in info_data,
        "playlist_count": len(info_data.get("entries", [])) if "entries" in info_data else 1,
    }

    return render_template("info.html", video=video_info)


@app.route("/formats", methods=["POST"])
def formats():
    url = request.form.get("url", "").strip()

    if not is_valid_youtube_url(url):
        flash("URL invalida.", "error")
        return redirect(url_for("index"))

    formats_data = YTDLManager.list_formats(url)
    if not formats_data:
        flash("Nao foi possivel listar os formatos.", "error")
        return redirect(url_for("index"))

    video_formats = [f for f in formats_data if f['vcodec'] != '-' and f['resolution'] != 'audio only']
    audio_formats = [f for f in formats_data if f['acodec'] != '-' and f['resolution'] == 'audio only']
    combined_formats = [f for f in formats_data if f['vcodec'] != '-' and f['acodec'] != '-']

    return render_template("formats.html",
                          url=url,
                          video_formats=video_formats,
                          audio_formats=audio_formats,
                          combined_formats=combined_formats)


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "").strip()
    mode = request.form.get("mode", "video")
    quality = request.form.get("quality", "best")
    audio_format = request.form.get("audio_format", "mp3")

    if not is_valid_youtube_url(url):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": "URL invalida"})
        flash("URL invalida.", "error")
        return redirect(url_for("index"))

    if mode == "video":
        result = YTDLManager.download_video(url, quality=quality)
    else:
        result = YTDLManager.download_audio(url, audio_format=audio_format, quality=quality)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(result)

    if result["success"]:
        flash(f"Download concluido: {result['data']['title']}", "success")
        return redirect(url_for("history"))
    else:
        flash(f"Erro no download: {result.get('error', 'Erro desconhecido')}", "error")
        return redirect(url_for("index"))


@app.route("/download-file/<filename>")
def download_file(filename):
    filepath = DOWNLOAD_DIR / filename
    if filepath.exists() and filepath.is_file():
        return send_file(filepath, as_attachment=True)
    flash("Arquivo nao encontrado.", "error")
    return redirect(url_for("history"))


@app.route("/history")
def history():
    history_data = load_history()
    for h in history_data:
        h['file_exists'] = os.path.exists(h.get('filepath', ''))
    save_history(history_data)
    return render_template("history.html", history=history_data)


@app.route("/api/history")
def api_history():
    return jsonify(load_history())


@app.route("/api/clear-history", methods=["POST"])
def clear_history():
    try:
        history = load_history()
        for h in history:
            fp = h.get('filepath')
            if fp and os.path.exists(fp):
                os.remove(fp)
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/delete-file/<file_id>", methods=["POST"])
def delete_file(file_id):
    history = load_history()
    for h in history:
        if h.get('id') == file_id:
            fp = h.get('filepath')
            if fp and os.path.exists(fp):
                os.remove(fp)
            h['file_exists'] = False
            break
    save_history(history)
    return jsonify({"success": True})


@app.route("/api/progress/<download_id>")
def progress(download_id):
    return jsonify({"status": "complete" if download_id not in download_locks else "downloading"})


# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Pagina nao encontrada"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Erro interno do servidor"), 500


# Main
if __name__ == "__main__":
    start_cleanup_thread()
    print("=" * 50)
    print("  NTEtube - YouTube Downloader Web")
    print("=" * 50)
    print(f"  Acesse: http://localhost:5540")
    print(f"  Pasta downloads: {DOWNLOAD_DIR}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5540, debug=True)
