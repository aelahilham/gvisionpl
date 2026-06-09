from flask import Flask, Response, request, abort
import requests
import re
import base64
import time
from urllib.parse import quote, unquote

app = Flask(__name__)

SOURCE_CACHE = {}
CACHE_TTL = 300  # Cache 5 menit

def fetch_playlist(url):
    now = time.time()
    if url in SOURCE_CACHE and (now - SOURCE_CACHE[url]['time'] < CACHE_TTL):
        return SOURCE_CACHE[url]['data']
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
            "Accept": "*/*"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            resp.encoding = 'utf-8'
            SOURCE_CACHE[url] = {'data': resp.text, 'time': now}
            return resp.text
    except Exception:
        pass
    return None

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    playlists = [
        {"url": "http://liveloveyou.my.id/94e3c4af/ux.html", "group": "LIVE TV NEW"},
        {"url": "http://liveloveyou.my.id/94e3c4af/pelme1.html", "group": "LIVE TV"},
        {"url": "http://liveloveyou.my.id/94e3c4af/lv.txt", "group": "LIVE EVENT AUTO"},
        {"url": "https://gvision-web.vercel.app/nw/piIdun.html", "group": "PIALA DUNIA 2026"},
        {"url": "http://liveloveyou.my.id/tesr/belum.html", "group": "JADWAL EVENT AUTO"},
        {"url": "http://liveloveyou.my.id/94e3c4af/pelme2.html", "group": "LIVE EVENT MANUAL"},
        {"url": "http://liveloveyou.my.id/94e3c4af/pelme3.html", "group": "SPORTS"},
        {"url": "http://liveloveyou.my.id/94e3c4af/pelme4.html", "group": "TV LUAR NEGERI"},
        {"url": "http://gvision-web.vercel.app/dio.txt", "group": "RADIO"}
    ]

    merged_content = "#EXTM3U\n"
    seen_urls = set()
    
    for pl in playlists:
        playlist_text = fetch_playlist(pl["url"])
        if not playlist_text:
            continue
            
        lines = playlist_text.splitlines()
        current_extinf = ""
        channel_name = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#EXTM3U"):
                continue
            
            if line.startswith("#EXTINF"):
                # ---> FIX A: Inject group-title lebih aman dan dinamis (antisipasi spasi ilang)
                if "group-title=" not in line:
                    line = re.sub(r'^(#EXTINF:[-0-9]+)\s*', rf'\1 group-title="{pl["group"]}" ', line)
                
                # Ekstrak nama channel
                if "," in line:
                    channel_name = line.split(",")[-1].strip().lower()
                else:
                    channel_name = line.lower()
                
                # ---> FIX B: Deteksi Base64 sakti (Support Kutip 1, Kutip 2, huruf besar/kecil)
                if re.search(r'tvg-logo=["\']data:image/', line, flags=re.IGNORECASE):
                    safe_url = quote(pl["url"])
                    safe_ch = quote(channel_name)
                    new_logo_url = f"{request.host_url}logo?pl_url={safe_url}&ch={safe_ch}"
                    
                    # Hapus Base64 aslinya secara fleksibel
                    line = re.sub(r'tvg-logo=["\']data:image/[^"\']+["\']', f'tvg-logo="{new_logo_url}"', line, flags=re.IGNORECASE)

                current_extinf = line
                    
            elif not line.startswith("#"):
                stream_url = line 
                if current_extinf and stream_url not in seen_urls:
                    seen_urls.add(stream_url)
                    merged_content += current_extinf + "\n" + stream_url + "\n"
                
                current_extinf = ""
                channel_name = ""
                
            elif line.startswith("#") and current_extinf:
                current_extinf += "\n" + line

    return Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')

@app.route('/logo')
def serve_logo():
    pl_url = request.args.get('pl_url')
    channel_name = request.args.get('ch')
    
    if not pl_url or not channel_name:
        return abort(400)
        
    text = fetch_playlist(unquote(pl_url))
    if not text:
        return abort(404)
        
    lines = text.splitlines()
    for line in lines:
        if line.startswith("#EXTINF"):
            current_ch = line.split(",")[-1].strip().lower() if "," in line else line.lower()
            
            if current_ch == channel_name.lower():
                # ---> FIX C: Parser Endpoint Logo disesuaikan dengan Regex yang baru
                match = re.search(r'tvg-logo=["\']data:image/([^;]+);base64,([^"\']+)["\']', line, flags=re.IGNORECASE)
                if match:
                    img_format = match.group(1)
                    b64_data = match.group(2)
                    
                    try:
                        img_bytes = base64.b64decode(b64_data)
                        return Response(
                            img_bytes, 
                            mimetype=f'image/{img_format}',
                            headers={'Cache-Control': 'public, max-age=2592000, s-maxage=2592000'}
                        )
                    except Exception:
                        pass
                break
                
    return abort(404)
