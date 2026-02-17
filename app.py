from flask import Flask, redirect, Response, request
import requests
import re
import os

app = Flask(__name__)

# Intentamos imitar a un navegador real al 100%
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Referer': 'https://videos.2000peliculassigloxx.com/',
    'Connection': 'keep-alive'
}

@app.route('/')
def home():
    return "Servidor activo. Usa /lista.m3u en PotPlayer", 200

@app.route('/lista.m3u')
def generar_lista():
    host = request.host_url.rstrip('/')
    # Solo una película para probar que funcione el motor
    m3u = "#EXTM3U\r\n"
    m3u += '#EXTINF:-1, Una noche en Casablanca\r\n'
    m3u += f'{host}/video/nFSeFHQcutFp3g\r\n'
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/video/<v_id>')
def get_real_video(v_id):
    # Esta es la URL de la página que me pasaste
    web_url = f"https://streaming.2000peliculassigloxx.com/yandex/yadisk.html?v={v_id}"
    
    try:
        # El servidor entra a la página web por ti
        session = requests.Session()
        r = session.get(web_url, headers=HEADERS, timeout=10)
        
        # BUSQUEDA DEL VIDEO REAL (.mp4)
        # Buscamos dentro del código HTML el enlace que termina en .mp4 o tiene la firma de Yandex Storage
        # Intentamos varios patrones comunes en Yandex Disk
        links = re.findall(r'(https?://[^\s"\'\\]+(?:\.mp4|storage\.yandex\.net)[^\s"\'\\]+)', r.text)
        
        if links:
            # Limpiamos el link de caracteres raros de programación (\u0026 -> &)
            video_directo = links[0].replace('\\u0026', '&').replace('&amp;', '&')
            # Redirigimos a PotPlayer al archivo real
            return redirect(video_directo, code=302)
        
        # Si no lo encuentra, intentamos buscar el "src" de la etiqueta video
        src_match = re.search(r'src=["\'](https?://.*?)["\']', r.text)
        if src_match:
            return redirect(src_match.group(1), code=302)

        return "No se pudo extraer el archivo de video. Yandex bloqueó la conexión.", 403
        
    except Exception as e:
        return f"Error de conexión: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
