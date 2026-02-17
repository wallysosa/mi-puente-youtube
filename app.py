from flask import Flask, redirect, Response, request
import requests
from bs4 import BeautifulSoup
import uuid
import os
import re

app = Flask(__name__)

# CONFIGURACIÓN
# IMPORTANTE: Cambia esta URL por la tuya actual de Render
BASE_URL = "https://cine-unificado-m3u.onrender.com" 
WEB_SXX_HOME = "https://2000peliculassigloxx.com"
WEB_SXX_VIDEO = "https://videos.2000peliculassigloxx.com"

@app.route('/')
def home():
    return "<h1>SERVIDOR UNIFICADO ACTIVO</h1><p>Lista M3U: /cine.m3u</p>", 200

@app.route('/cine.m3u')
def generar_lista():
    host = request.host_url.rstrip('/')
    m3u = "#EXTM3U\r\n"

    # --- SECCIÓN 1: PLUTO TV (MANUAL) ---
    peliculas_pluto = [
        ("El Redentor", "5efca13459900d0014d5857e", "Pluto Acción"),
        ("Inmortales", "697b59d471e7de966ec5cbe4", "Pluto Fantasía"),
        ("Equilibrium", "680650caa21058b98fb1ca89", "Pluto Sci-Fi"),
        ("Ultima Pelea", "64d3e39a85e5ff00132a4eb5", "Pluto Acción"),
        ("La Bruja de Cabellos Blancos", "62fff9d642b796001bc271fb", "Pluto Fantasía"),
        ("El Viajero", "62ffea63362313001aaa8f3d", "Pluto Acción"),
        ("Paladin II", "62fe9a5320b977001eedd4a8", "Pluto Fantasía"),
        ("Estado de Fuga", "62d6ff37d7fb2b001382bc3b", "Pluto Suspenso")
    ]

    for nombre, vid, cat in peliculas_pluto:
        # Imagen formato póster (se ve mejor en PotPlayer)
        img = f"https://images.pluto.tv/movies/{vid}/poster.jpg?w=400"
        m3u += f'#EXTINF:-1 tvg-logo="{img}" group-title="{cat}", {nombre}\r\n'
        m3u += f'{host}/pluto/{vid}\r\n'

    # --- SECCIÓN 2: SIGLO XX (AUTOMÁTICO) ---
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(WEB_SXX_HOME, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for peli in soup.find_all('article'):
            try:
                titulo = peli.find('h2').text.strip()
                link = peli.find('a')['href']
                slug = link.rstrip('/').split('/')[-1]
                foto = peli.find('img')['src']
                
                m3u += f'#EXTINF:-1 tvg-logo="{foto}" group-title="Cine Siglo XX", {titulo}\r\n'
                m3u += f'{host}/sigloxx/{slug}\r\n'
            except: continue
    except: pass

    return Response(m3u, mimetype='application/x-mpegurl')

# --- MANEJADORES DE VIDEO ---

@app.route('/pluto/<video_id>')
def get_pluto(video_id):
    sid = str(uuid.uuid4())
    url = f"https://stitcher.pluto.tv/stitch/hls/episode/{video_id}/master.m3u8?sid={sid}&deviceType=web&deviceMake=Chrome"
    return redirect(url, code=302)

@app.route('/sigloxx/<slug>')
def get_sigloxx(slug):
    headers = {"User-Agent": "Mozilla/5.0", "Referer": f"{WEB_SXX_VIDEO}/{slug}/"}
    try:
        r = requests.get(f"{WEB_SXX_VIDEO}/{slug}/embed/", headers=headers, timeout=10)
        # Buscamos el link del video MP4 o M3U8 escondido
        video_links = re.findall(r'(https?://[^\s"\']+\.(?:mp4|m3u8|m4v)[^\s"\']*)', r.text)
        if video_links:
            return redirect(video_links[0], code=302)
    except: pass
    return "No encontrado", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
