from flask import Flask, Response, render_template_string, request
import os
import uuid
from functools import wraps

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN DE SEGURIDAD (Cámbialos aquí)
# ==========================================
USUARIO = "admin"
CLAVE = "1234"

def requiere_clave(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == USUARIO and auth.password == CLAVE):
            return Response(
                'Acceso denegado. Ingresa credenciales.', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )
        return f(*args, **kwargs)
    return decorated

# ==========================================
# PLANTILLA VISUAL (PANEL DE CONTROL)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Panel Seguro - Puente Antel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; display: flex; justify-content: center; }
        .card { background: #1e293b; border-radius: 16px; padding: 24px; max-width: 450px; width: 100%; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); border: 1px solid #334155; }
        h1 { color: #3b82f6; font-size: 1.5rem; margin-bottom: 10px; }
        .status-pill { background: #065f46; color: #34d399; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
        .url-section { background: #020617; padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px dashed #3b82f6; position: relative; }
        .url-text { font-family: 'Courier New', monospace; color: #60a5fa; font-size: 0.85rem; word-break: break-all; }
        .btn { display: block; background: #2563eb; color: white; text-align: center; padding: 12px; text-decoration: none; border-radius: 8px; font-weight: bold; transition: 0.3s; }
        .btn:hover { background: #1d4ed8; }
        .channels { text-align: left; font-size: 0.9rem; color: #94a3b8; margin-top: 20px; }
        ul { padding-left: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🚀 Puente Antel TV</h1>
        <span class="status-pill">● SERVIDOR ACTIVO</span>
        
        <div class="url-section">
            <p style="margin-top:0; font-size: 0.8rem; color: #64748b;">Enlace para tu App IPTV:</p>
            <div class="url-text">{{ url_m3u }}</div>
        </div>

        <a href="/antel.m3u" class="btn">Abrir Lista M3U</a>

        <div class="channels">
            <strong>Canales incluidos:</strong>
            <ul>
                <li>Vera+ (Antel)</li>
                <li>Canal 5, 10 y 4</li>
                <li>TV Ciudad</li>
                <li>Eventos 1, 2 y 3 (Automáticos)</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

# ==========================================
# RUTAS DEL SERVIDOR
# ==========================================

@app.route('/')
@requiere_clave
def home():
    # Obtiene la URL real del servidor en Render
    host = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'puente-antel.onrender.com')}/antel.m3u"
    return render_template_string(HTML_TEMPLATE, url_m3u=host)

@app.route('/antel.m3u')
def generar_lista():
    # Definición de canales y logos
    canales = [
        ("Vera+ (Antel)", "https://antel-veraplus-live.fing.edu.uy/hls/veraplus.m3u8", "https://upload.wikimedia.org/wikipedia/commons/4/40/Antel_logo.svg"),
        ("Canal 5 Uruguay", "https://vencat-canal5.fing.edu.uy/hls/canal5.m3u8", "https://www.gub.uy/ministerio-educacion-cultura/sites/ministerio-educacion-cultura/files/logo_canal5.png"),
        ("Canal 10", "https://vencat-canal10.fing.edu.uy/hls/canal10.m3u8", "https://upload.wikimedia.org/wikipedia/commons/f/fe/Canal_10_Uruguay_logo.png"),
        ("Canal 4", "https://vencat-canal4.fing.edu.uy/hls/canal4.m3u8", "https://es.wikipedia.org/wiki/Archivo:Canal_4_Uruguay_2022.png"),
        ("TV Ciudad", "https://streaming.tvciudad.uy/hls/tvciudad.m3u8", "https://www.tvciudad.uy/wp-content/uploads/2021/05/logo-tvciudad.png"),
        ("Antel Eventos 1", "https://antel-eventos1-live.fing.edu.uy/hls/eventos1.m3u8", "https://upload.wikimedia.org/wikipedia/commons/4/40/Antel_logo.svg"),
        ("Antel Eventos 2", "https://antel-eventos2-live.fing.edu.uy/hls/eventos2.m3u8", "https://upload.wikimedia.org/wikipedia/commons/4/40/Antel_logo.svg"),
        ("Antel Eventos 3", "https://antel-eventos3-live.fing.edu.uy/hls/eventos3.m3u8", "https://upload.wikimedia.org/wikipedia/commons/4/40/Antel_logo.svg")
    ]

    m3u = "#EXTM3U\r\n"
    for nombre, url, logo in canales:
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n{url}\r\n'
    
    return Response(m3u, mimetype='application/x-mpegurl')

if __name__ == "__main__":
    # Render asigna el puerto automáticamente
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
