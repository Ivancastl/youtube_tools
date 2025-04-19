import json
import os
import re
import logging
from cryptography.fernet import Fernet
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
import pyfiglet

# Configuración de archivos
CREDENTIALS_FILE = "osintube_credentials.enc"
KEY_FILE = "osintube_key.key"

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OSINTube:
    def __init__(self):
        self.credentials = {}
        self.load_credentials()
        self.show_banner()

    def show_banner(self):
        """Muestra el banner ASCII art"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(pyfiglet.figlet_format("OSINTube", font="slant"))
        print("🔍 Herramienta OSINT para YouTube")
        print("👨💻 Creado por @ivancastl | Telegram: t.me/+_g4DIczsuI9hOWZh")
        print("="*50 + "\n")

    def get_encryption_key(self):
        """Genera o recupera la clave de encriptación"""
        if not os.path.exists(KEY_FILE):
            with open(KEY_FILE, "wb") as f:
                f.write(Fernet.generate_key())
        with open(KEY_FILE, "rb") as f:
            return f.read()

    def load_credentials(self):
        """Carga las credenciales encriptadas"""
        if os.path.exists(CREDENTIALS_FILE):
            try:
                cipher_suite = Fernet(self.get_encryption_key())
                with open(CREDENTIALS_FILE, "rb") as f:
                    encrypted_data = f.read()
                self.credentials = json.loads(cipher_suite.decrypt(encrypted_data).decode())
            except Exception as e:
                logger.error(f"Error cargando credenciales: {e}")
                self.credentials = {}

    def save_credentials(self):
        """Guarda las credenciales encriptadas"""
        try:
            cipher_suite = Fernet(self.get_encryption_key())
            encrypted_data = cipher_suite.encrypt(json.dumps(self.credentials).encode())
            with open(CREDENTIALS_FILE, "wb") as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            logger.error(f"Error guardando credenciales: {e}")
            return False

    def setup_credentials(self):
        """Configura las credenciales de API"""
        self.show_banner()
        print("⚙️ Configuración de API Key de YouTube\n")
        print("1. Obtén tu API key en: https://console.cloud.google.com/apis/credentials")
        print("2. Habilita la API de YouTube Data v3")
        print("3. Crea una credencial de tipo API Key\n")
        
        api_key = input("🔑 Ingresa tu API Key de YouTube: ").strip()
        self.credentials['youtube_api_key'] = api_key
        
        if self.save_credentials():
            print("\n✅ Credenciales guardadas de forma segura")
        else:
            print("\n❌ Error al guardar credenciales")
        input("\nPresiona Enter para continuar...")

    def extract_video_id(self, url: str) -> str:
        """Extrae el ID de video de una URL de YouTube"""
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

    def search_in_transcript(self):
        """Busca palabras clave en subtítulos"""
        self.show_banner()
        print("🔍 Buscar palabras en subtítulos\n")
        print("Ejemplo: https://youtu.be/ejemplo palabra1,palabra2\n")
        
        user_input = input("Ingresa URL y palabras clave: ").strip()
        
        if not user_input:
            print("\n❌ Debes ingresar una URL y palabras clave")
            input("\nPresiona Enter para continuar...")
            return
        
        parts = user_input.split()
        if len(parts) < 2:
            print("\n❌ Formato incorrecto. Ingresa URL seguida de palabras clave")
            input("\nPresiona Enter para continuar...")
            return
        
        url = parts[0]
        keywords = [kw.strip() for kw in " ".join(parts[1:]).split(",") if kw.strip()]
        
        video_id = self.extract_video_id(url)
        if not video_id:
            print("\n❌ URL de YouTube no válida")
            input("\nPresiona Enter para continuar...")
            return
        
        try:
            print("\n⏳ Obteniendo transcripción...")
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
            results = []
            
            for entry in transcript:
                text = entry['text'].lower()
                for keyword in keywords:
                    if keyword.lower() in text:
                        time_str = f"{int(entry['start'])//60:02d}:{int(entry['start'])%60:02d}"
                        results.append(f"⏱️ {time_str} - {entry['text']}")
            
            self.show_banner()
            print(f"🎥 Video: {url}")
            print(f"🔍 Palabras buscadas: {', '.join(keywords)}")
            print(f"📊 Coincidencias encontradas: {len(results)}\n")
            
            if results:
                for result in results[:50]:
                    print(result)
                if len(results) > 50:
                    print(f"\n⚠️ Mostrando 50 de {len(results)} resultados")
            else:
                print("🔍 No se encontraron coincidencias")
            
            input("\nPresiona Enter para continuar...")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            input("\nPresiona Enter para continuar...")

    def get_full_transcript(self):
        """Descarga la transcripción completa"""
        self.show_banner()
        print("📜 Descargar transcripción completa\n")
        url = input("Ingresa la URL del video: ").strip()
        
        video_id = self.extract_video_id(url)
        if not video_id:
            print("\n❌ URL de YouTube no válida")
            input("\nPresiona Enter para continuar...")
            return
        
        try:
            print("\n⏳ Obteniendo transcripción...")
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
            filename = f"transcripcion_{video_id}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                for entry in transcript:
                    time_str = f"{int(entry['start'])//60:02d}:{int(entry['start'])%60:02d}"
                    f.write(f"[{time_str}] {entry['text']}\n")
            
            self.show_banner()
            print(f"✅ Transcripción guardada en: {filename}")
            print(f"📝 Total de líneas: {len(transcript)}")
            input("\nPresiona Enter para continuar...")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            input("\nPresiona Enter para continuar...")

    def show_trending(self):
        """Muestra videos en tendencia"""
        if not self.credentials.get('youtube_api_key'):
            print("\n❌ API Key no configurada. Ve a Configuración")
            input("\nPresiona Enter para continuar...")
            return
        
        self.show_banner()
        print("📈 Videos en tendencia en México\n")
        print("⏳ Cargando...")
        
        try:
            youtube = build('youtube', 'v3', developerKey=self.credentials['youtube_api_key'])
            response = youtube.videos().list(
                part='snippet,statistics',
                chart='mostPopular',
                regionCode='MX',
                maxResults=15
            ).execute()
            
            videos = []
            for item in response['items']:
                vid = {
                    'title': item['snippet']['title'],
                    'id': item['id'],
                    'views': int(item['statistics'].get('viewCount', 0)),
                    'url': f"https://youtu.be/{item['id']}"
                }
                videos.append(vid)
            
            videos.sort(key=lambda x: x['views'], reverse=True)
            
            self.show_banner()
            print("📈 Top 10 videos en tendencia MX\n")
            
            for i, vid in enumerate(videos[:10], 1):
                print(f"{i}. {vid['title']}")
                print(f"   👀 {vid['views']:,} vistas")
                print(f"   🔗 {vid['url']}\n")
            
            input("\nPresiona Enter para continuar...")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            input("\nPresiona Enter para continuar...")

    def search_videos(self):
        """Busca videos por palabras clave"""
        if not self.credentials.get('youtube_api_key'):
            print("\n❌ API Key no configurada. Ve a Configuración")
            input("\nPresiona Enter para continuar...")
            return
        
        self.show_banner()
        print("🔎 Buscar videos en YouTube\n")
        query = input("Ingresa palabras clave: ").strip()
        
        if not query:
            print("\n❌ Debes ingresar palabras clave")
            input("\nPresiona Enter para continuar...")
            return
        
        try:
            print("\n⏳ Buscando videos...")
            youtube = build('youtube', 'v3', developerKey=self.credentials['youtube_api_key'])
            response = youtube.search().list(
                q=query,
                part='snippet',
                type='video',
                maxResults=10,
                order='relevance'
            ).execute()
            
            self.show_banner()
            print(f"🔎 Resultados para: '{query}'\n")
            
            for i, item in enumerate(response['items'], 1):
                print(f"{i}. {item['snippet']['title']}")
                print(f"   🔗 https://youtu.be/{item['id']['videoId']}\n")
            
            input("\nPresiona Enter para continuar...")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            input("\nPresiona Enter para continuar...")

    def show_menu(self):
        """Muestra el menú principal"""
        self.show_banner()
        print("1. 🔍 Buscar en subtítulos")
        print("2. 📜 Descargar transcripción")
        print("3. 📈 Videos en tendencia MX")
        print("4. 🔎 Buscar videos")
        print("5. ⚙️ Configurar API Key")
        print("6. 🚪 Salir\n")

    def run(self):
        """Ejecuta la aplicación"""
        if not self.credentials.get('youtube_api_key'):
            self.setup_credentials()
        
        while True:
            try:
                self.show_menu()
                choice = input("Selecciona una opción (1-6): ").strip()
                
                if choice == '1':
                    self.search_in_transcript()
                elif choice == '2':
                    self.get_full_transcript()
                elif choice == '3':
                    self.show_trending()
                elif choice == '4':
                    self.search_videos()
                elif choice == '5':
                    self.setup_credentials()
                elif choice == '6':
                    print("\n👋 ¡Hasta pronto!")
                    break
                else:
                    print("\n❌ Opción no válida")
                    input("\nPresiona Enter para continuar...")
                    
            except KeyboardInterrupt:
                print("\n⏹️ Operación cancelada")
                input("\nPresiona Enter para continuar...")
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                input("\nPresiona Enter para continuar...")

if __name__ == '__main__':
    try:
        app = OSINTube()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Aplicación terminada")
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")