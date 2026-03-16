import requests, json

def run():
    url = "https://cdn-us-east-1.v4.pluto.tv/v4/lineup-explore/sections/6335a98317c95e00075e714b?appName=web&deviceType=web"
    try:
        data = requests.get(url).json()
        items = data.get('items', [])
        pilis = []
        for i in items:
            pilis.append({
                "id": i.get('_id'),
                "nombre": i.get('name'),
                "poster": i.get('featuredImage', {}).get('path', '')
            })
        with open('vod.json', 'w') as f:
            json.dump(pilis, f)
        print(f"Generado con {len(pilis)} peliculas")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
