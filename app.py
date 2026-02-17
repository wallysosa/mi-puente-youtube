from flask import Flask, redirect, Response, request
import requests
from bs4 import BeautifulSoup
import os
import re

app = Flask(__name__)

# CONFIGURACIÓN
WEB_SXX_HOME = "https://2000peliculassigloxx.com"
WEB_SXX_VIDEO = "https://videos.2000peliculassigloxx.com"

@app.route('/')
def home():
    return "<h1>SERVIDOR SIGLO XX ACTIVO</h1><p>Lista M3U en: <b>/lista.m3u</b></p>", 200

@app.route('/lista.m3u')
def generar_lista():
    host = request.host_url.rstrip('/')
    m3u = "#EXTM3U\r\n"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # 1. Obtenemos la página principal
        r = requests.get(WEB_SXX_HOME, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 2. Buscamos todas las películas (artículos)
        articulos = soup.find_all('article')
        
        for peli in articulos:
            try:
                # Extraer título
                titulo_tag = peli.find('h2')
                if not titulo_tag: continue
                titulo = titulo_tag.text.strip()
                
                # Extraer enlace y slug
                link_tag = peli.find('a')
                if not link_tag: continue
                link = link_tag['href']
                slug = link.rstrip('/').split('/')[-1]
                
                # Extraer imagen
                img_tag = peli.find('img')
                foto = img_tag['src'] if img_tag else ""
                
                # Añadir a la lista
                m3u += f'#EXTINF:-1 tvg-logo="{foto}" group-title="Cine Siglo XX", {titulo}\r\n'
                m3u += f'{host}/video/{slug}\r\n'
            except:
                continue
    except Exception as e:
        m3u += f"# ERROR AL CONECTAR CON SIGLO XX: {str(e)}\n"

    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/video/<slug>')
def get_video(slug):
    # Esta es la parte que "salta" el reproductor de la web para darte el video directo
    target_url = f"{WEB_SXX_VIDEO}/{slug}/embed/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"{WEB_SXX_VIDEO}/{slug}/"
    }
    
    try:
        r = requests.get(target_url, headers=headers, timeout=10)
        # Buscamos archivos .mp4 o .m3u8 en el código de la página
        video_links = re.findall(r'(https?://[^\s"\']+\.(?:mp4|m3u8|m4v)[^\s"\']*)', r.text)
        
        if video_links:
            # Redirigimos al primer link de video encontrado
            return redirect(video_links[0], code=302)
        return "Video no encontrado en el origen", 404
    except:
        return "Error de conexión", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
