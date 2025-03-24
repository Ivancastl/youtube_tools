import json
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build

# Configuración básica
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Archivo para guardar credenciales
CREDENTIALS_FILE = "youtube_cli_credentials.json"

class YouTubeCLI:
    def __init__(self):
        self.credentials = {}
        self.load_credentials()

    def load_credentials(self):
        """Carga las credenciales desde el archivo"""
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, 'r') as f:
                    self.credentials = json.load(f)
            except Exception as e:
                logger.error(f"Error cargando credenciales: {e}")

    def save_credentials(self):
        """Guarda las credenciales en el archivo"""
        try:
            with open(CREDENTIALS_FILE, 'w') as f:
                json.dump(self.credentials, f)
            return True
        except Exception as e:
            logger.error(f"Error guardando credenciales: {e}")
            return False

    def setup_credentials(self):
        """Configura las credenciales necesarias"""
        print("\n🛠️ Configuración inicial del sistema 🛠️")
        
        # API Key de YouTube
        if not self.credentials.get('youtube_api_key'):
            print("\n🔹 Paso 1/1: API Key de YouTube")
            print("Obtén tu API key en: https://console.cloud.google.com/apis/credentials")
            self.credentials['youtube_api_key'] = input("Ingresa tu API Key de YouTube: ").strip()
        
        return self.save_credentials()

    def extract_video_id(self, url: str) -> str:
        """Extrae el ID de un video de YouTube desde la URL"""
        patterns = [
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
            r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def search_keywords(self):
        """Busca palabras clave en los subtítulos"""
        print("\n🔍 Buscar palabras en subtítulos de YouTube")
        print("Ejemplo: https://youtu.be/ejemplo palabra1, palabra2")
        
        user_input = input("\nIngresa URL y palabras clave: ").split()
        
        if len(user_input) < 2:
            print("⚠️ Formato incorrecto. Por favor envía el enlace seguido de las palabras clave.")
            return
        
        url = user_input[0]
        keywords = " ".join(user_input[1:]).split(",")
        keywords = [kw.strip() for kw in keywords if kw.strip()]
        
        video_id = self.extract_video_id(url)
        
        if not video_id:
            print("❌ Enlace de YouTube no válido.")
            return
        
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
            results = []
            
            for entry in transcript:
                for keyword in keywords:
                    if keyword.lower() in entry['text'].lower():
                        start_time = int(entry['start'])
                        minutes = start_time // 60
                        seconds = start_time % 60
                        timestamp = f"{minutes:02d}:{seconds:02d}"
                        results.append(f"⏱️ {timestamp} - {entry['text']}")
            
            if results:
                response = (
                    f"\n🎥 Video: {url}\n"
                    f"🔍 Palabras buscadas: {', '.join(keywords)}\n"
                    f"📊 Resultados encontrados: {len(results)}\n\n" +
                    "\n".join(results[:50])
                )
                
                if len(results) > 50:
                    response += f"\n\n⚠️ Mostrando 50 de {len(results)} resultados totales"
                
                print(response)
            else:
                print("🔍 No se encontraron resultados para las palabras clave especificadas.")
        
        except Exception as e:
            print(f"❌ Error al procesar el video: {str(e)}")

    def get_full_transcript(self):
        """Obtiene la transcripción completa de un video"""
        print("\n📜 Obtener transcripción completa de video de YouTube")
        url = input("Ingresa la URL del video: ")
        
        video_id = self.extract_video_id(url)
        
        if not video_id:
            print("❌ Enlace de YouTube no válido.")
            return
        
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
            transcript_text = ""
            
            for entry in transcript:
                start_time = int(entry['start'])
                minutes = start_time // 60
                seconds = start_time % 60
                timestamp = f"{minutes:02d}:{seconds:02d}"
                transcript_text += f"[{timestamp}] {entry['text']}\n"
            
            filename = f"transcripcion_{video_id}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            
            print(f"\n✅ Transcripción guardada en: {filename}")
            print(f"📜 Total de líneas: {len(transcript)}")
        
        except Exception as e:
            print(f"❌ Error al obtener la transcripción: {str(e)}")

    def get_trending_videos(self):
        """Obtiene videos en tendencia en México"""
        if not self.credentials.get('youtube_api_key'):
            print("❌ API Key de YouTube no configurada.")
            return
        
        try:
            print("\n📈 Obteniendo videos en tendencia en México...")
            
            youtube = build('youtube', 'v3', developerKey=self.credentials['youtube_api_key'])
            response = youtube.videos().list(
                part='snippet,statistics',
                chart='mostPopular',
                regionCode='MX',
                maxResults=15
            ).execute()
            
            videos = []
            for item in response['items']:
                title = item['snippet']['title']
                video_id = item['id']
                views = int(item['statistics'].get('viewCount', 0))
                url = f"https://youtu.be/{video_id}"
                videos.append((title, views, url))
            
            videos.sort(key=lambda x: x[1], reverse=True)
            
            print("\n📈 Videos en tendencia en México:\n")
            for i, (title, views, url) in enumerate(videos[:10], 1):
                print(
                    f"{i}. {title}\n"
                    f"   👀 {views:,} vistas\n"
                    f"   🔗 {url}\n"
                )
        
        except Exception as e:
            print(f"❌ Error al obtener tendencias: {str(e)}")

    def search_videos(self):
        """Busca videos por palabra clave"""
        if not self.credentials.get('youtube_api_key'):
            print("❌ API Key de YouTube no configurada.")
            return
        
        query = input("\n🔎 Ingresa palabras clave para buscar videos: ")
        
        try:
            print(f"\nBuscando videos para: '{query}'...")
            
            youtube = build('youtube', 'v3', developerKey=self.credentials['youtube_api_key'])
            response = youtube.search().list(
                q=query,
                part='snippet',
                type='video',
                maxResults=10,
                order='relevance'
            ).execute()
            
            print(f"\n🔍 Resultados para '{query}':\n")
            
            for i, item in enumerate(response['items'], 1):
                title = item['snippet']['title']
                video_id = item['id']['videoId']
                url = f"https://youtu.be/{video_id}"
                print(f"{i}. {title}\n   🔗 {url}\n")
        
        except Exception as e:
            print(f"❌ Error en la búsqueda: {str(e)}")

    def show_menu(self):
        """Muestra el menú principal"""
        print("\n🎬 YouTube Tools CLI 🎬")
        print("1. 🔍 Buscar en subtítulos")
        print("2. 📜 Obtener transcripción completa")
        print("3. 📈 Ver tendencias MX")
        print("4. 🎥 Buscar videos")
        print("5. ⚙️ Configurar API Key")
        print("6. 🚪 Salir")

    def run(self):
        """Ejecuta la aplicación CLI"""
        if not self.credentials.get('youtube_api_key'):
            print("\n⚠️ API Key de YouTube no configurada")
            self.setup_credentials()
        
        while True:
            self.show_menu()
            choice = input("\nSelecciona una opción (1-6): ")
            
            try:
                if choice == '1':
                    self.search_keywords()
                elif choice == '2':
                    self.get_full_transcript()
                elif choice == '3':
                    self.get_trending_videos()
                elif choice == '4':
                    self.search_videos()
                elif choice == '5':
                    self.setup_credentials()
                elif choice == '6':
                    print("\n👋 ¡Hasta luego!")
                    break
                else:
                    print("❌ Opción no válida. Por favor selecciona 1-6.")
            except KeyboardInterrupt:
                print("\n⏹️ Operación cancelada por el usuario")
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

def main():
    cli = YouTubeCLI()
    cli.run()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Aplicación terminada por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")