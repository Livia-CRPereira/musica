import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import time
import os
import re

def get_all_song_links(base_url):
    """
    Varre a página principal para encontrar todos os links de músicas,
    procurando dentro das seções alfabéticas 'letter-section'.
    """
    try:
        print(f"Acessando a página principal: {base_url}")
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        letter_sections = soup.find_all('div', class_='letter-section')
        if not letter_sections:
            print("ERRO: Não foi possível encontrar nenhuma 'div' com a classe 'letter-section'.")
            return []

        song_links = []
        for section in letter_sections:
            links_in_section = section.find_all('a', href=True)
            for link in links_in_section:
                href = link['href']
                if href.startswith(base_url) or href.startswith('/'):
                    full_url = href if href.startswith('http') else f"{base_url.rstrip('/')}{href}"
                    song_links.append(full_url)

        song_links = sorted(list(set(song_links)))
        print(f"Encontrados {len(song_links)} links de músicas únicos.")
        return song_links

    except requests.exceptions.RequestException as e:
        print(f"Erro crítico ao acessar a página de índice {base_url}: {e}")
        return []

def extract_year_and_author(text):
    """
    Tenta extrair o ano e o autor de uma string de texto.
    Lida com os diferentes padrões encontrados no site.
    """
    # Padrão 1: "Ano – Autor / Autor"
    match = re.search(r'(\d{4}) – (.+)', text)
    if match:
        year = match.group(1).strip()
        author = match.group(2).strip()
        return year, author
    
    # Padrão 2: "Ano - Autor"
    match = re.search(r'(\d{4}) - (.+)', text)
    if match:
        year = match.group(1).strip()
        author = match.group(2).strip()
        return year, author
    
    # Padrão 3: Apenas "Autor"
    # Se não houver ano, assume que é apenas o autor.
    if re.search(r'(\d{4})', text) is None:
        return None, text.strip()

    return None, None

def get_song_details(song_url):
    """
    Melhorado para extrair título, ano e autor de forma mais robusta.
    """
    try:
        response = requests.get(song_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.find('h1', class_='entry-title')
        title = title_tag.text.strip() if title_tag else None

        if not title:
            return None

        year = None
        author = None
        
        # Procura em diferentes tags que podem conter ano e autor
        # Primeiro, o padrão que você identificou <p class="has-text-align-right">
        content_tag = soup.find(['p', 'div'], class_=['has-text-align-right', 'entry-content'])
        
        if content_tag:
            # Tenta encontrar a informação diretamente no texto da tag
            text_content = content_tag.get_text().strip()
            if text_content:
                # Usa a nova função auxiliar para tentar extrair ano e autor
                extracted_year, extracted_author = extract_year_and_author(text_content)
                if extracted_author:
                    author = extracted_author
                    year = extracted_year
        
        # Se ainda não encontramos o autor, tenta buscar em outras divs de metadados
        if not author:
            author_meta_tags = soup.find_all('div', class_='entry-meta')
            for meta_tag in author_meta_tags:
                meta_text = meta_tag.get_text().strip()
                if 'by' in meta_text.lower():
                    # Lógica para extrair de outros formatos, se necessário
                    # No momento, a busca por <p> já deve cobrir a maioria dos casos.
                    pass

        return {'Titulo': title, 'Ano': year, 'Autor': author}

    except requests.exceptions.RequestException:
        return None

def main():
    """Função principal para orquestrar o scraping."""
    BASE_URL = "https://realbook.site"
    OUTPUT_FILENAME = 'musicas_realbook_completo_melhorado.csv' # Novo nome para o arquivo de saída
    
    print("--- Iniciando o scraping do Real Book Site (Melhorado) ---")
    
    all_song_links = get_all_song_links(BASE_URL)
    
    if not all_song_links:
        print("\nNenhum link de música encontrado.")
        return

    all_songs_data = []
    failed_links = []
    
    for link in tqdm(all_song_links, desc="Extraindo dados das músicas"):
        details = get_song_details(link)
        if details:
            all_songs_data.append(details)
        else:
            failed_links.append(link)
        
        time.sleep(0.05)

    if not all_songs_data:
        print("\nERRO: Nenhum dado de música foi extraído.")
        return

    df = pd.DataFrame(all_songs_data)
    
    df.drop_duplicates(subset=['Titulo', 'Ano', 'Autor'], inplace=True)
    
    df = df[['Titulo', 'Autor', 'Ano']]
    
    df.to_csv(OUTPUT_FILENAME, index=False, encoding='utf-8')
    
    print(f"\n--- Scraping concluído! ---")
    print(f"-> {len(df)} músicas salvas com sucesso em '{OUTPUT_FILENAME}'.")
    
    if failed_links:
        print(f"-> {len(failed_links)} links não puderam ser processados (nenhum título encontrado ou erro de acesso).")

if __name__ == "__main__":
    main()
