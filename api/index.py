from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    # --- MASUKIN LINK HTTP TOOLKIT LO DI BAWAH INI ---
    playlists = [
        {"url": "http://liveloveyou.my.id/ec147502/ux.html", "group": "LIVE TV NEW"},
        {"url": "http://liveloveyou.my.id/ec147502/pelme1.html", "group": "LIVE TV"},
        {"url": "http://liveloveyou.my.id/ec147502/lv.txt", "group": "LIVE EVENT AUTO"},
        {"url": "http://liveloveyou.my.id/ec147502/belum.html", "group": "JADWAL EVENT AUTO"},
        {"url": "http://liveloveyou.my.id/ec147502/pelme2.html", "group": "LIVE EVENT MANUAL"},
        {"url": "http://liveloveyou.my.id/ec147502/pelme3.html", "group": "SPORTS"},
        {"url": "http://liveloveyou.my.id/ec147502/pelme4.html", "group": "TV LUAR NEGERI"},
        {"url": "http://gvision-web.vercel.app/dio.txt", "group": "RADIO"}
    ]
    # -------------------------------------------------

    merged_content = "#EXTM3U\n"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*"
    }
    
    for pl in playlists:
        try:
            response = requests.get(pl["url"], headers=headers, timeout=10)
            
            if response.status_code == 200:
                # ---> FIX 1: Paksa Python baca hasil tarikan sebagai UTF-8
                response.encoding = 'utf-8'
                
                lines = response.text.splitlines()
                for line in lines:
                    if line.startswith("#EXTM3U"):
                        continue
                    
                    if line.startswith("#EXTINF"):
                        if "group-title=" not in line:
                            line = line.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{pl["group"]}"')
                    
                    merged_content += line + "\n"
        except Exception:
            pass 

    # ---> FIX 2: Kasih tau aplikasi IPTV lo kalo output ini formatnya UTF-8
    return Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')
