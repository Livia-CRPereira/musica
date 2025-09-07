# musica_downloader.py
import pandas as pd
import os
import time
import re
import yt_dlp
import logging
from moviepy.editor import AudioFileClip
from youtubesearchpython import VideosSearch
import concurrent.futures
from tqdm import tqdm

# --- CONFIGURAÇÃO ---
INPUT_CSV_FILE = 'MusicaStudyGroup/realbook/musicas_realbook_completo_melhorado.csv'
OUTPUT_CSV_FILE = 'relatorio_downloads.csv' # <-- MUDANÇA: Nome do novo arquivo de relatório
BUSCA_COMPLETA_FOLDER = 'busca_completa'
BUSCA_POR_TITULO_FOLDER = 'busca_por_titulo'
LOG_FILE = 'erros.log'
MAX_WORKERS = 4
CLIP_DURATION = 40

# --- CONFIGURAÇÃO DO LOGGING ---
logging.basicConfig(level=logging.ERROR, 
                    filename=LOG_FILE, 
                    filemode='w', 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def sanitize_filename(filename):
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    return sanitized[:150]

def download_and_process_audio(video_url, output_path, filename):
    sanitized_filename = sanitize_filename(filename)
    final_audio_path = os.path.join(output_path, f"{sanitized_filename}.mp3")
    
    # Define um "molde" para o nome do arquivo temporário.
    # Usamos %(ext)s para deixar o yt-dlp controlar a extensão.
    temp_path_template = os.path.join(output_path, f"temp_{sanitized_filename}.%(ext)s")

    # Esta variável vai guardar o nome real do arquivo que o yt-dlp criar.
    actual_temp_path = None 
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_path_template, # Usa o molde que definimos
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
            # Em vez de ydl.download, usamos ydl.extract_info.
            # Ele baixa o vídeo E retorna um dicionário com todas as informações.
            info_dict = ydl.extract_info(video_url, download=True)
            
            # Pegamos o caminho exato do arquivo final que foi criado, pós-processado.
            # O yt-dlp nos informa isso na chave 'filepath'.
            actual_temp_path = info_dict.get('filepath')

        # Agora, a verificação é 100% confiável.
        if not actual_temp_path or not os.path.exists(actual_temp_path):
             logging.error(f"yt-dlp não retornou um caminho de arquivo válido para '{filename}'")
             return False

        with AudioFileClip(actual_temp_path) as audio:
            end_duration = min(audio.duration, CLIP_DURATION)
            if end_duration > 0:
                with audio.subclip(0, end_duration) as final_clip:
                    final_clip.write_audiofile(final_audio_path, logger=None, codec='libmpredlame')
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
        # Garantimos que vamos apagar o arquivo temporário correto.
        if actual_temp_path and os.path.exists(actual_temp_path):
            os.remove(actual_temp_path)
            
def search_youtube_link(query):
    # <-- MUDANÇA: Esta função agora retorna o link E o título do vídeo.
    try:
        search_query = f"{query} audio"
        videos_search = VideosSearch(search_query, limit=1)
        results = videos_search.result()
        
        video_result = None
        if results and results.get('result') and len(results['result']) > 0:
            video_result = results['result'][0]
        else:
            # Tenta a busca sem "audio" se a primeira falhar
            videos_search = VideosSearch(query, limit=1)
            results = videos_search.result()
            if results and results.get('result') and len(results['result']) > 0:
                 video_result = results['result'][0]

        if video_result:
            # Retorna uma tupla (link, titulo)
            return (video_result['link'], video_result['title'])
        
    except Exception as e:
        print(f"ERRO NA BUSCA por '{query}': {e}")
        logging.error(f"Erro ao buscar por '{query}': {e}")
        return (None, None) # Retorna None para ambos se houver erro
    
    return (None, None) # Retorna None para ambos se não encontrar nada

def process_song(row_tuple):
    # <-- MUDANÇA: Esta função agora retorna um dicionário com os resultados.
    index, row = row_tuple
    title = str(row.get('Titulo', '')).strip()
    author = str(row.get('Autor', '')).strip()

    if not title:
        return {
            "musica_buscada": "Título Vazio",
            "titulo_video_encontrado": None,
            "status": "Falha"
        }
    
    if pd.isna(row.get('Autor')) or author == '':
        query = title
        output_folder = BUSCA_POR_TITULO_FOLDER
        filename = title
    else:
        main_author = author.split('/')[0].strip()
        query = f"{title} {main_author}"
        output_folder = BUSCA_COMPLETA_FOLDER
        filename = f"{title} - {main_author}"

    time.sleep(0.1)
    
    video_url, video_title = search_youtube_link(query)
    
    if video_url:
        success = download_and_process_audio(video_url, output_folder, filename)
        if success:
            return {
                "musica_buscada": query,
                "titulo_video_encontrado": video_title,
                "status": "Sucesso"
            }
        else:
            return {
                "musica_buscada": query,
                "titulo_video_encontrado": video_title,
                "status": "Falha (erro no download)"
            }
    else:
        return {
            "musica_buscada": query,
            "titulo_video_encontrado": None,
            "status": "Falha (vídeo não encontrado)"
        }

def main():
    print("Iniciando o processo de download de áudios...")
    print(f"Erros detalhados serão salvos em '{LOG_FILE}'")

    if not os.path.exists(INPUT_CSV_FILE):
        print(f"ERRO: Arquivo de entrada '{INPUT_CSV_FILE}' não encontrado!")
        return

    os.makedirs(BUSCA_COMPLETA_FOLDER, exist_ok=True)
    os.makedirs(BUSCA_POR_TITULO_FOLDER, exist_ok=True)

    try:
        df = pd.read_csv(INPUT_CSV_FILE, encoding='utf-8')
    except Exception as e:
        print(f"ERRO ao ler o CSV: {e}. Verifique se o arquivo '{INPUT_CSV_FILE}' está salvo com a codificação correta (UTF-8).")
        return

    print(f"Encontradas {len(df)} músicas no arquivo CSV para processar.")

    tasks = list(df.iterrows())
    
    # A lista 'results' agora vai armazenar os dicionários retornados por 'process_song'
    results_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        with tqdm(total=len(tasks), desc="Baixando músicas") as pbar:
            futures = [executor.submit(process_song, task) for task in tasks]
            for future in concurrent.futures.as_completed(futures):
                results_data.append(future.result()) # <-- MUDANÇA: Renomeado para 'results_data'
                pbar.update(1)

    print("\n--- Processo de download concluído! ---")
    
    # <-- MUDANÇA: Toda esta seção foi adicionada para criar o CSV de relatório.
    print(f"\n📝 Gerando relatório de downloads...")
    if results_data:
        # Cria um DataFrame do pandas a partir da lista de dicionários
        results_df = pd.DataFrame(results_data)
        
        # Salva o DataFrame em um novo arquivo CSV
        results_df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8')
        print(f"Relatório salvo com sucesso em '{OUTPUT_CSV_FILE}'")
    else:
        print("Nenhum dado para gerar relatório.")

    # A contagem de sucessos e falhas agora é baseada nos dados do DataFrame
    sucessos = sum(1 for r in results_data if r['status'] == "Sucesso")
    falhas = len(results_data) - sucessos
    
    print(f"\n✅ Áudios baixados com sucesso: {sucessos}")
    print(f"❌ Falhas: {falhas}")
    print(f"Verifique as pastas '{BUSCA_COMPLETA_FOLDER}' e '{BUSCA_POR_TITULO_FOLDER}'.")
    if falhas > 0:
        print(f"👉 Detalhes sobre os erros foram salvos no arquivo '{LOG_FILE}'.")


if __name__ == "__main__":
    main()