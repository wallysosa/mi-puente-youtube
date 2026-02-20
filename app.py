from flask import Flask, Response
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "SERVIDOR DE RADIOS URUGUAYAS ACTIVO. Usa /radios.m3u en tu reproductor.", 200

@app.route('/radios.m3u')
def generar_lista():
    # Nombre, URL del streaming, URL del logo
    radios = [
        ("Radio Carve 850 AM", "https://vencat-carve.fing.edu.uy/hls/carve.m3u8", "https://www.carve850.com.uy/wp-content/uploads/2018/05/logo-carve.png"),
        ("Radio Sarandí 690 AM", "https://vencat-sarandi.fing.edu.uy/hls/sarandi.m3u8", "https://www.sarandi690.com.uy/wp-content/themes/sarandi/img/logo-sarandi.png"),
        ("Sport 890 AM", "https://vencat-sport890.fing.edu.uy/hls/sport890.m3u8", "https://www.sport890.com.uy/wp-content/uploads/2018/05/logo-sport.png"),
        ("Del Sol 99.5 FM", "https://vencat-delsol.fing.edu.uy/hls/delsol.m3u8", "https://delsol.uy/img/logo-delsol.png"),
        ("Océano FM 93.9", "https://vencat-oceano.fing.edu.uy/hls/oceano.m3u8", "https://oceano.uy/img/logo-oceano.png"),
        ("Metrópolis FM 104.9", "https://vencat-metropolis.fing.edu.uy/hls/metropolis.m3u8", "https://metropolis.com.uy/img/logo.png"),
        ("Radio Uruguay 1050 AM", "https://vencat-radiouruguay.fing.edu.uy/hls/radiouruguay.m3u8", "https://mediospublicos.uy/wp-content/uploads/2020/09/Logo-Radio-Uruguay.png")
    ]

    m3u = "#EXTM3U\r\n"
    for nombre, url, logo in radios:
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="RADIOS UY", {nombre}\r\n{url}\r\n'
    
    return Response(m3u, mimetype='application/x-mpegurl')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
