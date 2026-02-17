from flask import Flask, redirect, Response, request
import requests
import re
import os

app = Flask(__name__)

# Configuración de URLs
STREAM_SERVER = "https://streaming.2000peliculassigloxx.com/yandex/yadisk.html?v="

@app.route('/')
def index():
    return "Servidor Siglo XX Activo. Prueba con /video/nFSeFHQcutFp3g", 200

@app.route('/lista.m3u')
def m3u_gen():
    host = request.host_url.rstrip('/')
    m3u = "#EXTM3U\n"
    # Película de prueba con el ID que pasaste
    m3u += '#EXTINF:-1 group-title="Cine Siglo XX", Una noche en Casablanca\n'
    m3u += f'{host}/video/nFSeFHQcutFp3g\n'
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/video/<v_id>')
def get_stream(v_id):
    # 1. Construimos la URL de streaming que pasaste
    target_url = f"{STREAM_SERVER}{v_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://videos.2000peliculassigloxx.com/'
    }
    
    try:
        # 2. Entramos a la página de streaming para buscar el MP4 real
        r = requests.get(target_url, headers=headers, timeout=10)
        
        # 3. Buscamos el enlace al archivo .mp4 (Yandex suele ponerlo en una variable o etiqueta source)
        # Buscamos patrones como: "file":"http..." o src="http..."
        video_match = re.search(r'(https?://[^\s"\']+\.(?:mp4|m3u8)[^\s"\']*)', r.text)
        
        if video_match:
            video_url = video_match.group(1).replace('\\/', '/')
            # 4. Redirigimos a PotPlayer al archivo de video real
            return redirect(video_url, code=302)
        
        # Si no lo encontramos, intentamos devolver la página de streaming (a veces PotPlayer la abre)
        return redirect(target_url, code=302)
            
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
