from flask import Flask, redirect, Response, request
import requests
import re
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>SERVIDOR SIGLO XX - YANDEX MODE</h1><p>Lista: <b>/lista.m3u</b></p>", 200

@app.route('/lista.m3u')
def generar_lista():
    host = request.host_url.rstrip('/')
    m3u = "#EXTM3U\r\n"
    
    # Película: Una noche en Casablanca
    img = "https://2000peliculassigloxx.com/wp-content/uploads/una-noche-en-casablanca.jpg"
    
    m3u += f'#EXTINF:-1 tvg-logo="{img}" group-title="Cine Siglo XX", Una noche en Casablanca\r\n'
    m3u += f'{host}/video/una-noche-en-casablanca\r\n'
    
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/video/<slug>')
def get_video(slug):
    # Intentamos entrar al embed para buscar el link de Yandex
    embed_url = f"https://videos.2000peliculassigloxx.com/{slug}/embed/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://videos.2000peliculassigloxx.com/{slug}/'
    }

    try:
        # 1. Obtenemos el código del embed
        r = requests.get(embed_url, headers=headers, timeout=10)
        
        # 2. Buscamos específicamente links de Yandex Storage o archivos MP4
        # Esta expresión busca el link largo que me pasaste
        match = re.search(r'(https?://[^\s"\']+\.yandex\.net/[^\s"\']+)', r.text)
        
        if match:
            # Limpiamos el link por si tiene comillas
            link_directo = match.group(1).replace('&amp;', '&')
            return redirect(link_directo, code=302)
        
        # Si no lo encuentra, intentamos buscar cualquier MP4
        match_mp4 = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', r.text)
        if match_mp4:
            return redirect(match_mp4.group(1), code=302)

        return "No se pudo extraer el link de Yandex. Puede que haya expirado.", 404
    except:
        return "Error de conexión", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
