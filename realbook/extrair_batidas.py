#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para extrair batidas (BPM e tempos) de ficheiros de áudio usando librosa.

Este script lê ficheiros de áudio de uma pasta de entrada, analisa-os com
librosa.beat.beat_track() e salva os resultados (BPM e lista de tempos)
em ficheiros .txt numa pasta de saída.

Dependências:
- librosa
- numpy
(Instale com: pip install librosa numpy)
"""

import librosa
import numpy as np
import os
import sys

# ===================================================================
# --- CONFIGURAÇÃO DE PASTAS ---
# (A única coisa que você precisa alterar)
# ===================================================================

# 1. Coloque aqui o caminho para a pasta que contém os áudios

PASTA_DE_AUDIOS = "musicas_com_boa_similaridade"
PASTA_DE_RESULTADOS_TXT = "resultados_batidas/batidas_boa_similaridade"

#PASTA_DE_AUDIOS = "audios_mauro"
#PASTA_DE_RESULTADOS_TXT = "resultados_batidas/audios_mauro"

# ===================================================================
# --- FUNÇÃO DE ANÁLISE (Do seu notebook) ---
# ===================================================================

def analisar_batidas_do_audio(caminho_do_arquivo):
    """
    Analisa um ficheiro de áudio para extrair o BPM e os tempos das batidas.
    """
    print(f"Analisando o ficheiro: {caminho_do_arquivo}...")

    try:
        y, sr = librosa.load(caminho_do_arquivo, sr=None)
    except Exception as e:
        print(f"Erro ao carregar o áudio: {e}")
        return None, None, None, None # Retorna None para tudo

    print("Calculando batidas (isso pode demorar um pouco)...")

    # Esta função é a mesma
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    # --- INÍCIO DA CORREÇÃO ---
    # Verificamos se 'tempo' é um array ou lista (ex: [178.20])
    # Se for, e se não estiver vazio, pegamos o primeiro elemento.
    if isinstance(tempo, (np.ndarray, list)) and len(tempo) > 0:
        tempo = tempo[0]
    # --- FIM DA CORREÇÃO ---

    # Converte frames para segundos
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    print("Análise concluída!")

    return tempo, beat_times, y, sr

# ===================================================================
# --- LÓGICA PRINCIPAL (MAIN) ---
# ===================================================================

def main():
    """
    Função principal que executa o loop de processamento.
    """
    
    # --- 1. CONFIGURAR PASTAS ---
    # Cria a pasta de resultados se ela não existir
    os.makedirs(PASTA_DE_RESULTADOS_TXT, exist_ok=True)
    print(f"Resultados de texto (.txt) serão salvos em: {PASTA_DE_RESULTADOS_TXT}")

    # --- 2. VERIFICAR PASTA DE ENTRADA ---
    if not os.path.isdir(PASTA_DE_AUDIOS):
        print(f"ERRO: Pasta de áudios não encontrada em '{PASTA_DE_AUDIOS}'")
        print("Por favor, verifique a variável 'PASTA_DE_AUDIOS' no início do script.")
        sys.exit(1) # Termina o script se a pasta de entrada não existir

    # --- 3. LER ARQUIVOS DE ÁUDIO ---
    arquivos_na_pasta = os.listdir(PASTA_DE_AUDIOS)
    arquivos_audio = [f for f in arquivos_na_pasta if f.endswith(('.mp3', '.wav', '.ogg', '.flac'))]

    if not arquivos_audio:
        print(f"Nenhum arquivo de áudio (mp3, wav, etc.) encontrado na pasta: '{PASTA_DE_AUDIOS}'")
        return

    print(f"\nEncontrados {len(arquivos_audio)} arquivos de áudio na pasta.")

    # --- 4. LOOP DE PROCESSAMENTO ---
    for nome_arquivo in arquivos_audio:
        
        # --- 4.1. VERIFICAR SE JÁ EXISTE (Requisito) ---
        nome_base = os.path.splitext(nome_arquivo)[0]
        nome_arquivo_txt = f"{nome_base}.txt"
        caminho_arquivo_resultado = os.path.join(PASTA_DE_RESULTADOS_TXT, nome_arquivo_txt)

        # Verifica se o ficheiro de resultado já existe
        if os.path.exists(caminho_arquivo_resultado):
            print(f"\n--- Pulando {nome_arquivo}: Resultados já existem em '{nome_arquivo_txt}' ---")
            continue # Pula para o próximo arquivo

        # --- 4.2. PROCESSAR O ARQUIVO ---
        caminho_completo_audio = os.path.join(PASTA_DE_AUDIOS, nome_arquivo)
        print(f"\n{'='*50}")
        print(f"PROCESSANDO: {nome_arquivo}")
        print(f"{'='*50}")

        # Chama a função de análise
        bpm_estimado, tempos_das_batidas, onda_sonora, taxa_amostragem = analisar_batidas_do_audio(caminho_completo_audio)

        if tempos_das_batidas is not None:

            # --- 4.3. IMPRIMIR RESULTADOS (Opcional, mas útil) ---
            print("\n" + "="*30)
            print("--- RESULTADOS DA ANÁLISE ---")
            print(f"Arquivo: {nome_arquivo}")

            bpm_valido = False
            if bpm_estimado is not None and isinstance(bpm_estimado, (int, float, np.number)) and not np.isnan(bpm_estimado):
                print(f"BPM Estimado (Batidas Por Minuto): {bpm_estimado:.2f}")
                bpm_valido = True
            else:
                print(f"Não foi possível determinar um BPM único (valor retornado: {bpm_estimado}).")

            if len(tempos_das_batidas) > 0:
                print("\nTempos das Batidas (em segundos):")
                print(np.round(tempos_das_batidas[:10], 2))
                if len(tempos_das_batidas) > 10:
                    print(f"...e mais {len(tempos_das_batidas) - 10} batidas.")
            else:
                print("\nNenhuma batida detectada.")
            print("="*30)

            # --- 4.4. SALVAR RESULTADOS EM .TXT ---
            try:
                # Abrir e escrever no ficheiro
                with open(caminho_arquivo_resultado, 'w', encoding='utf-8') as f:
                    f.write(f"Arquivo: {nome_arquivo}\n")

                    if bpm_valido:
                        f.write(f"BPM Estimado: {bpm_estimado:.2f}\n")
                    else:
                        f.write(f"BPM Estimado: N/D\n")

                    f.write("="*30 + "\n")
                    f.write("Tempos das Batidas (em segundos):\n")

                    # Escrever cada tempo de batida numa linha nova
                    for tempo in tempos_das_batidas:
                        f.write(f"{tempo:.4f}\n") # Salva com 4 casas decimais para mais precisão

                print(f"-> Resultados salvos com sucesso em: {nome_arquivo_txt}")

            except Exception as e:
                print(f"ERRO AO SALVAR O FICHEIRO .txt: {e}")

        else:
            print(f"Não foi possível analisar o arquivo (erro no carregamento): {nome_arquivo}")
            
    print("\nProcessamento concluído!")

# ===================================================================
# --- PONTO DE ENTRADA DO SCRIPT ---
# ===================================================================

if __name__ == "__main__":
    main()