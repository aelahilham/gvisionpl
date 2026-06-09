from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    # --- MASUKIN LINK PLAYLIST LO DI BAWAH INI ---
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
    # -------------------------------------------------

    merged_content = "#EXTM3U\n"
    seen_urls = set()  # ---> UBAHAN: Variabel buat nginget URL yang udah masuk
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*"
    }
    
    for pl in playlists:
        try:
            response = requests.get(pl["url"], headers=headers, timeout=10)
            
            if response.status_code == 200:
                response.encoding = 'utf-8'
                lines = response.text.splitlines()
                
                current_extinf = ""
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith("#EXTM3U"):
                        continue
                    
                    # Simpan metadata channel sementara
                    if line.startswith("#EXTINF"):
                        if "group-title=" not in line:
                            line = line.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{pl["group"]}"')
                        current_extinf = line
                            
                    # Kalau nemu baris URL Streaming
                    elif not line.startswith("#"):
                        stream_url = line # Ini adalah link streamingnya
                        
                        # Cek apakah URL udah pernah direkam
                        if current_extinf and stream_url not in seen_urls:
                            seen_urls.add(stream_url)
                            merged_content += current_extinf + "\n" + stream_url + "\n"
                        
                        # Reset untuk channel berikutnya
                        current_extinf = ""
                        
                    # Handle tag tambahan IPTV (misal: #EXTVLCOPT)
                    elif line.startswith("#") and current_extinf:
                        current_extinf += "\n" + line
                        
        except Exception:
            pass 

    return Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')
