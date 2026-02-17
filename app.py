from flask import Flask, redirect, Response, request
import requests
import re
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>SERVIDOR SIGLO XX - MODO PRUEBA</h1><p>Lista: <b>/lista.m3u</b></p>", 200

@app.route('/lista.m3u')
def generar_lista():
    host = request.host_url.rstrip('/')
    m3u = "#EXTM3U\r\n"
    
    # Película de prueba: Una noche en Casablanca
    # He buscado la imagen real que suele usar esa web
    img = "https://2000peliculassigloxx.com/wp-content/uploads/una-noche-en-casablanca.jpg"
    
    m3u += f'#EXTINF:-1 tvg-logo="{img}" group-title="Cine Siglo XX", Una noche en Casablanca\r\n'
    m3u += f'{host}/video/una-noche-en-casablanca\r\n'
    
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/video/<slug>')
def get_video(slug):
    # Usamos la URL que venía en tu código de embed
    video_url = f"https://videos.2000peliculassigloxx.com/{slug}/embed/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://videos.2000peliculassigloxx.com/{slug}/'
    }

    try:
        r = requests.get(video_url, headers=headers, timeout=10)
        # Intentamos buscar un archivo MP4 o M3U8 escondido en el código
        match = re.search(r'(https?://[^\s"\']+\.(?:mp4|m3u8|m4v)[^\s"\']*)', r.text)
        
        if match:
            return redirect(match.group(1), code=302)
        
        # Si no encontramos el video dentro, no tenemos más remedio que enviar al embed
        # PotPlayer a veces puede "tragar" el embed si tiene los codecs instalados
        return redirect(video_url, code=302)
    except:
        return "Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
