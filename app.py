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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        # Intentamos obtener la web
        r = requests.get(WEB_SXX_HOME, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # BUSCADOR DINÁMICO: Buscamos todos los enlaces que contengan el dominio o sean de películas
        enlaces = soup.find_all('a', href=True)
        
        encontradas = 0
        for link in enlaces:
            url_peli = link['href']
            # Filtramos links que no son de películas
            if "pelicula" in url_peli or "2000peliculassigloxx.com/" in url_peli:
                # Intentamos sacar el título del texto del link o del atributo title
                titulo = link.get_text().strip()
                if not titulo or len(titulo) < 3:
                    titulo = url_peli.rstrip('/').split('/')[-1].replace('-', ' ').title()
                
                # Evitamos duplicados y links vacíos como 'Home'
                if titulo.lower() in ['home', 'inicio', 'películas', 'contacto']: continue
                
                slug = url_peli.rstrip('/').split('/')[-1]
                
                # Buscamos imagen cercana
                img_tag = link.find('img')
                foto = img_tag['src'] if img_tag else "https://via.placeholder.com/400x600.png?text=Sin+Poster"
                
                m3u += f'#EXTINF:-1 tvg-logo="{foto}" group-title="Cine Siglo XX", {titulo}\r\n'
                m3u += f'{host}/video/{slug}\r\n'
                encontradas += 1
        
        if encontradas == 0:
            m3u += "# ERROR: La web no entrego peliculas. Revisa la URL o el bloqueo.\n"

    except Exception as e:
        m3u += f"# ERROR DE CONEXION: {str(e)}\n"

    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/video/<slug>')
def get_video(slug):
    target_url = f"{WEB_SXX_VIDEO}/{slug}/embed/"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": f"{WEB_SXX_VIDEO}/{slug}/"}
    try:
        r = requests.get(target_url, headers=headers, timeout=10)
        # Buscamos enlaces de video MP4 o M3U8
        video_links = re.findall(r'(https?://[^\s"\']+\.(?:mp4|m3u8|m4v)[^\s"\']*)', r.text)
        if video_links:
            return redirect(video_links[0], code=302)
        return "Video no encontrado", 404
    except:
        return "Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
