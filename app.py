import requests
import re
import subprocess
import time

def obtener_link_subrayado():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.subrayado.com.uy/",
            "Origin": "https://www.subrayado.com.uy"
        }
        url = f"https://www.subrayado.com.uy/resources/_post/subrayado/get-vivo.php?t={int(time.time() * 1000)}"
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            match = re.search(r'(https?:\\?/\\?/[^"\s\']+?\.m3u8\?token=[^"\s\']+)', r.text)
            if match:
                return match.group(1).replace('\\/', '/').replace('\\u0026', '&')
            match_alt = re.search(r'(https?:\\?/\\?/[^"\s\']+?\.m3u8[^\s"\']*)', r.text)
            if match_alt:
                return match_alt.group(1).replace('\\/', '/').replace('\\u0026', '&')
        return None
    except:
        return None

def main():
    print("🎬 Iniciando generación de lista M3U...")
    res = "#EXTM3U\n"
    
    # 1. Extraer Subrayado RAW
    link_raw = obtener_link_subrayado()
    if link_raw:
        res += '#EXTINF:-1 tvg-logo="https://www.subrayado.com.uy/favicon.ico" group-title="URUGUAY", Subrayado HD (RAW)\n'
        res += '#EXTVLCOPT:http-referrer=https://www.subrayado.com.uy/\n'
        res += '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n'
        res += f'{link_raw}\n'
        print("✅ Subrayado RAW agregado.")
    else:
        print("⚠️ No se pudo obtener Subrayado.")

   
    # Guardar archivo físico
    with open("lista.m3u", "w", encoding="utf-8") as f:
        f.write(res)
    print("💾 Archivo lista.m3u guardado con éxito.")

if __name__ == "__main__":
    main()
