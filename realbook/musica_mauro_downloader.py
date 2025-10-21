# musica_downloader.py
import pandas as pd
import os
import time
import re
import yt_dlp
import logging
from moviepy.editor import AudioFileClip
# import concurrent.futures # <-- MUDANÇA: Removida a biblioteca de busca
import concurrent.futures
from tqdm import tqdm

# --- CONFIGURAÇÃO ---
# <-- MUDANÇA: Coloque aqui o nome do CSV que você baixou do Colab
INPUT_CSV_FILE = 'lista_completa_videos.csv' 
OUTPUT_CSV_FILE = 'relatorio_downloads.csv'
# <-- MUDANÇA: Criamos uma pasta única para os áudios
AUDIO_OUTPUT_FOLDER = 'audios_baixados' 
LOG_FILE = 'erros.log'
MAX_WORKERS = 4
CLIP_DURATION = 40

# --- CONFIGURAÇÃO DO LOGGING ---
logging.basicConfig(level=logging.ERROR, 
                    filename=LOG_FILE, 
                    filemode='w', 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def sanitize_filename(filename):
    """Função para limpar nomes de arquivos."""
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    return sanitized[:150]

def download_and_process_audio(video_url, output_path, filename):
    """
    Esta função baixa, converte para MP3 e corta o áudio.
    (Esta função está perfeita, não mudei nada nela)
    """
    sanitized_filename = sanitize_filename(filename)
    final_audio_path = os.path.join(output_path, f"{sanitized_filename}.mp3")
    
    temp_path_template = os.path.join(output_path, f"temp_{sanitized_filename}.%(ext)s")
    actual_temp_path = None 
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_path_template,
            'max_filesize': 50 * 1024 * 1024,
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            actual_temp_path = info_dict.get('filepath')

        if not actual_temp_path or not os.path.exists(actual_temp_path):
             logging.error(f"yt-dlp não retornou um caminho de arquivo válido para '{filename}'")
             return False

        with AudioFileClip(actual_temp_path) as audio:
            end_duration = min(audio.duration, CLIP_DURATION)
            if end_duration > 0:
                with audio.subclip(0, end_duration) as final_clip:
                    # Usamos 'libmp3lame' que é um codec comum para mp3
                    final_clip.write_audiofile(final_audio_path, logger=None, codec='libmp3lame')
            else:
                logging.error(f"Áudio com duração zero para '{filename}'")
                return False
        return True
        
    except Exception as e:
        print(f"\n--- ERRO DETALHADO para '{filename}' ---")
        print(f"URL do Vídeo: {video_url}")
        print(f"Tipo do Erro: {type(e).__name__}")
        print(f"Mensagem do Erro: {e}")
        print("-------------------------------------------\n")
        logging.error(f"Erro detalhado para '{filename}': {type(e).__name__} - {e}")
        return False

    finally:
        if actual_temp_path and os.path.exists(actual_temp_path):
            os.remove(actual_temp_path)
            
# <-- MUDANÇA: A função 'search_youtube_link' foi removida, pois não é mais necessária.

def process_song(row_tuple):
    """
    Esta é a função "trabalhadora" que cada thread vai executar.
    Ela foi modificada para ler as colunas 'url' e 'title' do seu CSV.
    """
    index, row = row_tuple
    
    # <-- MUDANÇA: Lemos as colunas 'url' e 'title' do CSV da playlist
    video_url = str(row.get('url', '')).strip()
    video_title = str(row.get('title', '')).strip() # Usamos o título do vídeo como nome do arquivo

    # Se a linha do CSV não tiver URL ou título, pulamos
    if not video_url or not video_title:
        return {
            "musica_buscada": video_title or "Título Vazio",
            "titulo_video_encontrado": video_title,
            "status": "Falha (URL ou Título vazio no CSV)"
        }
    
    # <-- MUDANÇA: Chamamos diretamente o download, sem pesquisar
    success = download_and_process_audio(video_url, AUDIO_OUTPUT_FOLDER, video_title)
    
    if success:
        return {
            "musica_buscada": video_title, # O nome do arquivo é o "item buscado"
            "titulo_video_encontrado": video_title,
            "status": "Sucesso"
        }
    else:
        return {
            "musica_buscada": video_title,
            "titulo_video_encontrado": video_title,
            "status": "Falha (erro no download)"
        }

def main():
    print("Iniciando o processo de download de áudios...")
    print(f"Erros detalhados serão salvos em '{LOG_FILE}'")

    if not os.path.exists(INPUT_CSV_FILE):
        print(f"ERRO: Arquivo de entrada '{INPUT_CSV_FILE}' não encontrado!")
        print("Verifique se o nome do arquivo está correto e na mesma pasta do script.")
        return

    # <-- MUDANÇA: Criamos a pasta de saída única
    os.makedirs(AUDIO_OUTPUT_FOLDER, exist_ok=True)

    try:
        df = pd.read_csv(INPUT_CSV_FILE, encoding='utf-8')
    except Exception as e:
        print(f"ERRO ao ler o CSV: {e}. Verifique se o arquivo '{INPUT_CSV_FILE}' está salvo com a codificação correta (UTF-8).")
        return

    print(f"Encontradas {len(df)} músicas no arquivo CSV para processar.")

    tasks = list(df.iterrows())
    
    results_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        with tqdm(total=len(tasks), desc="Baixando músicas") as pbar:
            futures = [executor.submit(process_song, task) for task in tasks]
            for future in concurrent.futures.as_completed(futures):
                results_data.append(future.result())
                pbar.update(1)

    print("\n--- Processo de download concluído! ---")
    
    # O seu código de relatório já estava perfeito para esta nova lógica.
    print(f"\n📝 Gerando relatório de downloads...")
    if results_data:
        results_df = pd.DataFrame(results_data)
        results_df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8')
        print(f"Relatório salvo com sucesso em '{OUTPUT_CSV_FILE}'")
    else:
        print("Nenhum dado para gerar relatório.")

    sucessos = sum(1 for r in results_data if r['status'] == "Sucesso")
    falhas = len(results_data) - sucessos
    
    print(f"\n✅ Áudios baixados com sucesso: {sucessos}")
    print(f"❌ Falhas: {falhas}")
    # <-- MUDANÇA: Atualizada a mensagem final
    print(f"Verifique a pasta '{AUDIO_OUTPUT_FOLDER}'.") 
    if falhas > 0:
        print(f"👉 Detalhes sobre os erros foram salvos no arquivo '{LOG_FILE}'.")


if __name__ == "__main__":
    main()