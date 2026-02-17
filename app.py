from flask import Flask, redirect, Response, request
import requests
import os
import re

app = Flask(__name__)

# CONFIGURACIÓN
WEB_SXX_HOME = "https://2000peliculassigloxx.com"
WEB_SXX_VIDEO = "https://videos.2000peliculassigloxx.com"

@app.route('/')
def home():
    return "<h1>SERVIDOR SIGLO XX ACTIVO</h1><p>Lista M3U: /lista.m3u</p>", 200

@app.route('/lista.m3u')
def generar_lista():
    host = request.host_url.rstrip('/')
    m3u = "#EXTM3U\r\n"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # Descargamos el código fuente puro
        r = requests.get(WEB_SXX_HOME, headers=headers, timeout=15)
        html = r.text

        # BUSCADOR POR EXPRESIONES REGULARES (Ignora etiquetas, busca patrones)
        # Este patrón busca links que terminan en slugs de películas
        patron = re.findall(r'href="https://2000peliculassigloxx\.com/([^"/]+)/"', html)
        
        encontrados = set() # Para evitar duplicados
        for slug in patron:
            # Filtramos palabras que sabemos que NO son películas
            if slug in ['decadas', 'biografias', 'sagas', 'contacto', 'aplicacion', 'politica-de-privacidad']:
                continue
            
            if slug not in encontrados:
                titulo = slug.replace('-', ' ').title()
                # Intentamos adivinar la imagen (la mayoría usa el slug como nombre de archivo)
                foto = f"https://2000peliculassigloxx.com/wp-content/uploads/{slug}.jpg"
                
                m3u += f'#EXTINF:-1 tvg-logo="{foto}" group-title="Cine Siglo XX", {titulo}\r\n'
                m3u += f'{host}/video/{slug}\r\n'
                encontrados.add(slug)

        if not encontrados:
            m3u += "# La web no respondio con peliculas. Probando metodo alternativo...\n"
            # Metodo alternativo: buscar cualquier link interno
            patron_alt = re.findall(r'https://2000peliculassigloxx\.com/([a-z0-9\-]+)', html)
            for slug in patron_alt:
                if len(slug) > 5 and slug not in encontrados:
                    m3u += f'#EXTINF:-1 group-title="Cine Siglo XX", {slug.replace("-", " ").title()}\r\n'
                    m3u += f'{host}/video/{slug}\r\n'
                    encontrados.add(slug)

    except Exception as e:
        m3u += f"# ERROR: {str(e)}\n"

    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/video/<slug>')
def get_video(slug):
    # Intentamos forzar el link de video
    headers = {"User-Agent": "Mozilla/5.0", "Referer": f"{WEB_SXX_VIDEO}/{slug}/"}
    try:
        # Buscamos en la zona de videos
        r = requests.get(f"{WEB_SXX_VIDEO}/{slug}/embed/", headers=headers, timeout=10)
        # Buscamos archivos de video reales en el texto
        v_links = re.findall(r'https?://[^\s"\']+\.(?:mp4|m3u8|m4v)', r.text)
        if v_links:
            return redirect(v_links[0], code=302)
        
        # Si falla el anterior, intentamos una redireccion directa comun en estos sitios
        return redirect(f"https://videos.2000peliculassigloxx.com/uploads/videos/{slug}.mp4", code=302)
    except:
        return "Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
