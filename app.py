from flask import Flask, Response, request, abort
import requests
import re
import base64
import time
from urllib.parse import quote, unquote

app = Flask(__name__)

SOURCE_CACHE = {}
CACHE_TTL = 300 

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
		{"url": "http://liveloveyou.my.id/97b9ac12/ux.html", "group": "LIVE TV NEW"},
        {"url": "http://liveloveyou.my.id/97b9ac12/pelme1.html", "group": "LIVE TV"},
        {"url": "http://liveloveyou.my.id/97b9ac12/lv.txt", "group": "LIVE EVENT AUTO"},
        {"url": "https://gvision-web.vercel.app/nw/piIdun.html", "group": "PIALA DUNIA 2026"},
        {"url": "http://liveloveyou.my.id/tesr/belum.html", "group": "JADWAL EVENT AUTO"},
        {"url": "http://liveloveyou.my.id/97b9ac12/pelme2.html", "group": "LIVE EVENT MANUAL"},
        {"url": "http://liveloveyou.my.id/97b9ac12/pelme3.html", "group": "SPORTS"},
        {"url": "http://liveloveyou.my.id/97b9ac12/pelme4.html", "group": "TV LUAR NEGERI"},
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
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#EXTM3U"):
                continue
            
            if line.startswith("#EXTINF"):
                duration_match = re.search(r'^(#EXTINF:\s*[-0-9]+)', line)
                duration = duration_match.group(1) if duration_match else "#EXTINF:-1"
                rest_of_line = line[len(duration):]
                
                attr_dict = {}
                def extract_attr(match):
                    attr_dict[match.group(1)] = match.group(2)
                    return "" 
                    
                rest_of_line = re.sub(r'([a-zA-Z0-9_-]+)=["\']([^"\']*)["\']', extract_attr, rest_of_line)
                
                channel_name_clean = rest_of_line.replace(',', ' ').strip()
                
                # ---> FIX BLANK CHARACTERS (SURGICAL STRIKE): 
                # \uE000-\uF8FF = Karakter PUA (Logo font aneh yang sering jadi kotak)
                # \u200B\u200C\uFEFF = Zero-width space (Spasi siluman)
                # \u200E\u200F\u202A-\u202E = LTR/RTL formatting marks
                bad_chars = r'[\u200B\u200C\u200E\u200F\u202A-\u202E\u2060-\u2064\uFEFF\uE000-\uF8FF]'
                channel_name_clean = re.sub(bad_chars, '', channel_name_clean)
                
                channel_name_clean = re.sub(r'\s+', ' ', channel_name_clean).strip() 
                channel_name_clean = channel_name_clean.upper() 
                
                channel_name_for_check = channel_name_clean.lower()
                
                group_val = attr_dict.pop("group-title", None)
                if not group_val:
                    group_val = pl["group"].upper()
                else:
                    # Bersihin group title juga biar aman
                    group_val = re.sub(bad_chars, '', group_val)
                    group_val = re.sub(r'\s+', ' ', group_val).strip().upper()
                    
                if "tvg-logo" in attr_dict and attr_dict["tvg-logo"].lower().startswith("data:image/"):
                    safe_url = quote(pl["url"])
                    safe_ch = quote(channel_name_for_check)
                    new_logo_url = f"{request.host_url}logo?pl_url={safe_url}&ch={safe_ch}"
                    attr_dict["tvg-logo"] = new_logo_url
                    
                new_attrs = f'group-title="{group_val}"'
                for k, v in attr_dict.items():
                    new_attrs += f' {k}="{v}"'
                    
                current_extinf = f"{duration} {new_attrs} , {channel_name_clean}"
                
            elif line.startswith("#EXTGRP"):
                continue
                    
            elif not line.startswith("#"):
                stream_url = line 
                if current_extinf and stream_url not in seen_urls:
                    seen_urls.add(stream_url)
                    merged_content += current_extinf + "\n" + stream_url + "\n"
                
                current_extinf = ""
                
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
            duration_match = re.search(r'^(#EXTINF:\s*[-0-9]+)', line)
            duration = duration_match.group(1) if duration_match else "#EXTINF:-1"
            rest_of_line = line[len(duration):]
            
            attr_dict = {}
            def extract_attr(match):
                attr_dict[match.group(1)] = match.group(2)
                return ""
                
            rest_of_line = re.sub(r'([a-zA-Z0-9_-]+)=["\']([^"\']*)["\']', extract_attr, rest_of_line)
            
            channel_name_clean = rest_of_line.replace(',', ' ').strip()
            
            # Terapin Regex Surgical di Endpoint Logo juga
            bad_chars = r'[\u200B\u200C\u200E\u200F\u202A-\u202E\u2060-\u2064\uFEFF\uE000-\uF8FF]'
            channel_name_clean = re.sub(bad_chars, '', channel_name_clean)
            channel_name_clean = re.sub(r'\s+', ' ', channel_name_clean).strip()
            
            current_ch = channel_name_clean.lower()
            
            if current_ch == channel_name.lower():
                if "tvg-logo" in attr_dict and attr_dict["tvg-logo"].lower().startswith("data:image/"):
                    match = re.search(r'data:image/([^;]+);base64,(.+)', attr_dict["tvg-logo"], flags=re.IGNORECASE)
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
