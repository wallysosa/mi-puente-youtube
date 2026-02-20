import os
from flask import Flask, Response

app = Flask(__name__)

# Lista de radios con sus URLs REALES que funcionan directo en PotPlayer
RADIOS_LISTA = [
    ("Azul FM 101.9", "https://vencat.fing.edu.uy:8000/azul.mp3", "azul"),
    ("Océano FM 93.9", "https://oceano-2.nty.uy/stream", "oceano-fm"),
    ("El Espectador 810 AM", "https://vencat.fing.edu.uy:8000/espectador.mp3", "radio-el-espectador"),
    ("Metrópolis FM 104.9", "https://vencat.fing.edu.uy:8000/metropolis.mp3", "metropolis-fm"),
    ("Radio Cero 104.3", "https://icecast2.innovanexo.com:9000/radiocero.mp3", "radio-cero"),
    ("Sport 890 AM", "https://vencat.fing.edu.uy:8000/sport890.mp3", "sport-890"),
    ("Radio Universal 970 AM", "https://vencat.fing.edu.uy:8000/universal.mp3", "universal-montevideo"),
    ("Del Sol 99.5 FM", "https://vencat.fing.edu.uy:8000/delsol.mp3", "del-sol-montevideo"),
    ("Radio Monte Carlo 930", "https://icecast2.innovanexo.com:9000/montecarlo.mp3", "monte-carlo"),
    ("Radio Carve 850 AM", "https://vencat.fing.edu.uy:8000/carve.mp3", "radio-carve"),
    ("Radio Sarandí 690 AM", "https://vencat.fing.edu.uy:8000/sarandi.mp3", "sarandi"),
    ("M24 97.9 FM", "https://vencat.fing.edu.uy:8000/m24.mp3", "m24-montevideo"),
    ("Radio Clarín AM", "https://vencat.fing.edu.uy:8000/clarin.mp3", "clarin"),
    ("Emisora del Sur", "https://vencat.fing.edu.uy:8000/emisora-del-sur.mp3", "sur"),
    ("Radio Babel", "https://vencat.fing.edu.uy:8000/babel.mp3", "babel"),
    ("Radio Clásica 650 AM", "https://vencat.fing.edu.uy:8000/radio-clasica.mp3", "clasica"),
    ("La Voz de Melo", "https://vencat.fing.edu.uy:8000/vozdemelo.mp3", "voz-de-melo"),
    ("Radio Tacuarembó", "https://vencat.fing.edu.uy:8000/radiotacuarembo.mp3", "1280-am-tacuarembo"),
    ("Radio María", "https://vencat.fing.edu.uy:8000/radiomaria.mp3", "radio-maria-uruguay")
]

@app.route('/')
def home():
    # Esta vez, generamos la lista al instante sin esperar a nadie
    m3u = "#EXTM3U\r\n"
    # User-Agent para que el reproductor se salte bloqueos
    ua = "|User-Agent=Mozilla/5.0"

    for nombre, url, slug in RADIOS_LISTA:
        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
        m3u += f'{url}{ua}\r\n'
    
    return Response(m3u, mimetype='text/plain')

if __name__ == "__main__":
    # Render usa el puerto 10000 por defecto
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
