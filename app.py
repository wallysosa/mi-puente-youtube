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
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        r = requests.get(WEB_SXX_HOME, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Filtramos solo los artículos de películas reales
        articulos = soup.find_all('article')
        
        for peli in articulos:
            try:
                # 1. Extraer Título (solo del H2 para evitar menús)
                titulo_tag = peli.find('h2')
                if not titulo_tag: continue
                titulo = titulo_tag.text.strip()
                
                # 2. Extraer Link y Slug
                a_tag = peli.find('a', href=True)
                link = a_tag['href']
                slug = link.rstrip('/').split('/')[-1]
                
                # Ignorar links que no son películas individuales
                if slug in ['decadas', 'biografias', 'sagas', 'contacto', 'aplicacion']: continue
                
                # 3. Extraer Imagen Real
                img_tag = peli.find('img')
                if img_tag:
                    # Buscamos la imagen real, a veces está en 'data-src' o 'src'
                    foto = img_tag.get('data-src') or img_tag.get('src')
                else:
                    foto = "https://via.placeholder.com/400x600.png?text=Cine+Clasico"
                
                m3u += f'#EXTINF:-1 tvg-logo="{foto}" group-title="Cine Siglo XX", {titulo}\r\n'
                m3u += f'{host}/video/{slug}\r\n'
            except:
                continue
    except:
        m3u += "# ERROR DE CONEXION\n"

    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/video/<slug>')
def get_video(slug):
    # Intentamos encontrar el video real dentro de la página de video
    video_page = f"{WEB_SXX_VIDEO}/{slug}/"
    embed_url = f"{WEB_SXX_VIDEO}/{slug}/embed/"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": video_page}
    
    try:
        # Primero probamos en la página de embed
        r = requests.get(embed_url, headers=headers, timeout=10)
        # Buscamos links que terminen en .mp4, .m3u8 o que contengan 'stream'
        video_links = re.findall(r'(https?://[^\s"\']+\.(?:mp4|m3u8|m4v|ts)[^\s"\']*)', r.text)
        
        if not video_links:
            # Si no hay suerte, probamos en la página normal
            r = requests.get(video_page, headers=headers, timeout=10)
            video_links = re.findall(r'(https?://[^\s"\']+\.(?:mp4|m3u8|m4v|ts)[^\s"\']*)', r.text)

        if video_links:
            # Filtramos para no redirigir a archivos CSS o JS por error
            final_link = [l for l in video_links if ".js" not in l and ".css" not in l][0]
            return redirect(final_link, code=302)
            
        return "Video no encontrado. Puede que sea un servidor externo no soportado.", 404
    except:
        return "Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
