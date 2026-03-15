import os
import requests
from flask import Flask, Response, request

app = Flask(__name__)

# URL del canales.m3u generado por GitHub Actions (rama streams)
GITHUB_USER = os.environ.get('GITHUB_USER', 'wallysosa')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'mi-puente-youtube')
M3U_URL     = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/streams/canales.m3u"

@app.route('/')
def home():
    return (
        f"<h2>📺 Canales Latinos YouTube</h2>"
        f"<ul>"
        f"<li><a href='/canales.m3u'>/canales.m3u</a> — Lista para VLC/OTT/TiviMate</li>"
        f"<li><a href='/lista'>/lista</a> — Ver canales disponibles</li>"
        f"</ul>"
        f"<p><small>Streams actualizados cada hora via GitHub Actions</small></p>"
    )

@app.route('/canales.m3u')
def canales_m3u():
    """Sirve el canales.m3u generado por GitHub Actions."""
    try:
        r = requests.get(M3U_URL, timeout=15)
        r.raise_for_status()
        return Response(r.text, mimetype='application/x-mpegurl')
    except Exception as e:
        return f"Error obteniendo lista: {e}", 502

@app.route('/lista')
def lista():
    """Muestra los canales disponibles en HTML."""
    try:
        r = requests.get(M3U_URL, timeout=15)
        r.raise_for_status()
        lineas  = r.text.splitlines()
        canales = []
        for i, linea in enumerate(lineas):
            if linea.startswith('#EXTINF'):
                nombre = linea.split(',')[-1].strip()
                pais   = ''
                grupo  = ''
                if 'tvg-country="' in linea:
                    pais  = linea.split('tvg-country="')[1].split('"')[0]
                if 'group-title="' in linea:
                    grupo = linea.split('group-title="')[1].split('"')[0]
                canales.append((nombre, pais, grupo))

        filas = ''.join(
            f"<tr><td>{n}</td><td>{p}</td><td>{g}</td></tr>"
            for n, p, g in canales
        )
        return f"""
        <html><head><meta charset='utf-8'>
        <style>body{{font-family:sans-serif;padding:20px}}
        table{{border-collapse:collapse;width:100%}}
        th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
        th{{background:#333;color:white}}</style></head>
        <body>
        <h2>📺 Canales Latinos ({len(canales)})</h2>
        <table><tr><th>Canal</th><th>País</th><th>Grupo</th></tr>
        {filas}
        </table>
        </body></html>
        """
    except Exception as e:
        return f"Error: {e}", 502

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
