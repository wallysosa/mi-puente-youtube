from flask import Flask, redirect, Response, request
import requests
import re
import os

app = Flask(__name__)

# CONFIGURACIÓN
WEB_SXX_HOME = "https://2000peliculassigloxx.com"
WEB_SXX_VIDEO = "https://videos.2000peliculassigloxx.com"

@app.route('/')
def home():
    return "<h1>SERVIDOR SIGLO XX - MODO STREAMING</h1><p>Lista M3U: <b>/lista.m3u</b></p>", 200

@app.route('/lista.m3u')
def generar_lista():
    host = request.host_url.rstrip('/')
    m3u = "#EXTM3U\r\n"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        # 1. Escaneamos la web principal para sacar las películas
        r = requests.get(WEB_SXX_HOME, headers=headers, timeout=15)
        # Buscamos los slugs de las películas y sus nombres
        # Este regex captura el enlace y el título de los artículos
        patron = re.findall(r'href="https://2000peliculassigloxx\.com/([^"/]+)/".*?>(.*?)</a>', r.text, re.DOTALL)
        
        encontrados = set()
        for slug, titulo_sucia in patron:
            titulo = re.sub('<[^<]+?>', '', titulo_sucia).strip() # Limpiamos HTML del título
            
            if slug in ['decadas', 'biografias', 'sagas', 'contacto', 'aplicacion'] or len(titulo) < 3:
                continue
            
            if slug not in encontrados:
                foto = f"https://2000peliculassigloxx.com/wp-content/uploads/{slug}.jpg"
                m3u += f'#EXTINF:-1 tvg-logo="{foto}" group-title="Cine Siglo XX", {titulo}\r\n'
                m3u += f'{host}/video/{slug}\r\n'
                encontrados.add(slug)
    except:
        m3u += "# ERROR AL CARGAR LISTA\n"

    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/video/<slug>')
def get_video(slug):
    # Intentamos encontrar el código de Yandex (ej: nFSeFHQcutFp3g)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://videos.2000peliculassigloxx.com/{slug}/'
    }
    
    try:
        # Entramos al embed oficial de la película
        r = requests.get(f"https://videos.2000peliculassigloxx.com/{slug}/embed/", headers=headers, timeout=10)
        
        # Buscamos el ID del video que va después de ?v=
        id_video = re.search(r'yadisk\.html\?v=([a-zA-Z0-9_-]+)', r.text)
        
        if id_video:
            # Construimos el link de streaming directo que me pasaste
            direct_stream = f"https://streaming.2000peliculassigloxx.com/yandex/yadisk.html?v={id_video.group(1)}"
            return redirect(direct_stream, code=302)
            
        # Si no lo encuentra por ID, intentamos redirigir al embed normal
        return redirect(f"https://videos.2000peliculassigloxx.com/{slug}/embed/", code=302)
    except:
        return "Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
