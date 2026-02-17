from flask import Flask, redirect, Response, request
import requests
from bs4 import BeautifulSoup
import uuid
import os
import re

app = Flask(__name__)

# --- CONFIGURACIÓN DE RUTAS ---
WEB_ORIGINAL_SXX = "https://2000peliculassigloxx.com"
WEB_VIDEOS_SXX = "https://videos.2000peliculassigloxx.com"

@app.route('/')
def home():
    return "<h1>Servidor Unificado Activo</h1><p>Tu lista M3U está en: <b>/lista.m3u</b></p>", 200

@app.route('/lista.m3u')
def generar_lista():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    host = request.host_url.rstrip('/')
    m3u = "#EXTM3U\n"

    # --- CATEGORÍA 1: PLUTO TV (Tus favoritas) ---
    # Formato: ("Nombre", "ID", "Categoría")
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
        poster = f"https://images.pluto.tv/movies/{vid}/poster.jpg?h=900&w=600"
        m3u += f'#EXTINF:-1 tvg-logo="{poster}" group-title="{cat}", {nombre}\n'
        m3u += f'{host}/pluto/{vid}\n'

    # --- CATEGORÍA 2: SIGLO XX (Escaneo Automático) ---
    try:
        r = requests.get(WEB_ORIGINAL_SXX, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        articulos = soup.find_all('article')
        
        for peli in articulos:
            try:
                titulo = peli.find('h2').text.strip()
                link_peli = peli.find('a')['href']
                slug = link_peli.strip('/').split('/')[-1]
                img = peli.find('img')['src']
                
                m3u += f'#EXTINF:-1 tvg-logo="{img}" group-title="Cine Siglo XX (Auto)", {titulo}\n'
                m3u += f'{host}/sigloxx/{slug}\n'
            except:
                continue
    except:
        pass 

    return Response(m3u, mimetype='application/x-mpegurl')

# --- MANEJADORES DE VIDEO ---

@app.route('/pluto/<video_id>')
def get_pluto(video_id):
    sid = str(uuid.uuid4())
    url = f"https://stitcher.pluto.tv/stitch/hls/episode/{video_id}/master.m3u8?deviceMake=Chrome&deviceType=web&sid={sid}"
    return redirect(url, code=302)

@app.route('/sigloxx/<slug>')
def get_sigloxx(slug):
    embed_url = f"{WEB_VIDEOS_SXX}/{slug}/embed/"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": f"{WEB_VIDEOS_SXX}/{slug}/"}
    try:
        r = requests.get(embed_url, headers=headers)
        video_links = re.findall(r'(https?://[^\s"\']+\.(?:mp4|m3u8|m4v)[^\s"\']*)', r.text)
        if video_links:
            return redirect(video_links[0], code=302)
        return "Video no encontrado", 404
    except:
        return "Error", 500

if __name__ == "__main__":
    # Render asigna un puerto en la variable de entorno PORT
    # Si no existe, usa el 10000 por defecto
    port = int(os.environ.get("PORT", 10000))
    # Es VITAL usar host='0.0.0.0' para que sea visible fuera del contenedor
    app.run(host='0.0.0.0', port=port)
