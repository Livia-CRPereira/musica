import os
import pandas as pd
import glob
from collections import defaultdict

# --- CONFIGURAÇÃO ---
# Coloque aqui as mesmas pastas que você usa no script de download
BUSCA_COMPLETA_FOLDER = 'busca_completa'
BUSCA_POR_TITULO_FOLDER = 'busca_por_titulo'
RELATORIO_CSV = 'MusicaStudyGroup/realbook/relatorio_downloads.csv'

def limpar_duplicatas_e_coletar_sucessos(pastas):
    """
    Procura por arquivos 'temp_*', remove duplicatas não-mp3 e retorna
    uma lista com os nomes base dos arquivos mp3 encontrados.
    """
    arquivos_encontrados = []
    for pasta in pastas:
        # Usamos glob para encontrar todos os arquivos que começam com 'temp_' na pasta
        caminho_busca = os.path.join(pasta, 'temp_*')
        arquivos_encontrados.extend(glob.glob(caminho_busca))

    if not arquivos_encontrados:
        print("Nenhum arquivo 'temp_' encontrado para processar.")
        return []

    # Agrupa os arquivos pelo nome base (sem a extensão)
    arquivos_agrupados = defaultdict(list)
    for caminho_completo in arquivos_encontrados:
        # Ex: de 'busca_completa/temp_My Song - Keith Jarrett.mp3'
        # -> extrai 'busca_completa/temp_My Song - Keith Jarrett'
        nome_base, extensao = os.path.splitext(caminho_completo)
        arquivos_agrupados[nome_base].append(caminho_completo)

    nomes_de_sucesso = []
    for nome_base, caminhos in arquivos_agrupados.items():
        # Se existe mais de um arquivo com o mesmo nome (ex: .mp3, .webm)
        if len(caminhos) > 1:
            print(f"Encontrado grupo de arquivos para '{os.path.basename(nome_base)}':")
            caminho_mp3 = None
            for c in caminhos:
                if c.endswith('.mp3'):
                    caminho_mp3 = c
                    break # Encontramos o mp3, podemos parar de procurar

            # Se um .mp3 foi encontrado no grupo, apaga os outros
            if caminho_mp3:
                print(f"  - Mantendo: {os.path.basename(caminho_mp3)}")
                for c in caminhos:
                    if c != caminho_mp3:
                        try:
                            os.remove(c)
                            print(f"  - Removendo duplicata: {os.path.basename(c)}")
                        except OSError as e:
                            print(f"  - ERRO ao remover {os.path.basename(c)}: {e}")
                # Adiciona o nome do arquivo (sem 'temp_') à lista de sucessos
                nomes_de_sucesso.append(os.path.basename(nome_base).replace('temp_', ''))

        # Se só existe um arquivo e ele é .mp3
        elif len(caminhos) == 1 and caminhos[0].endswith('.mp3'):
             nomes_de_sucesso.append(os.path.basename(nome_base).replace('temp_', ''))

    return nomes_de_sucesso

def atualizar_relatorio(nomes_de_sucesso):
    """
    Atualiza o arquivo CSV, mudando o status para 'Sucesso' para as músicas
    cujos arquivos 'temp_*.mp3' foram encontrados.
    """
    if not nomes_de_sucesso:
        print("\nNenhuma música para atualizar no relatório.")
        return

    try:
        df = pd.read_csv(RELATORIO_CSV)
    except FileNotFoundError:
        print(f"ERRO: Arquivo de relatório '{RELATORIO_CSV}' não encontrado.")
        return

    print(f"\nAtualizando o relatório '{RELATORIO_CSV}'...")
    
    # Criamos um "mapeamento" para tentar encontrar a música no CSV
    # Ex: 'My Song - Keith Jarrett' (do nome do arquivo) -> 'My Song Keith Jarrett' (possível busca)
    mapa_busca = {nome.replace(' - ', ' '): nome for nome in nomes_de_sucesso}
    
    # Encontra as linhas cujo valor em 'musica_buscada' corresponde a uma chave do nosso mapa
    linhas_para_atualizar = df['musica_buscada'].isin(mapa_busca.keys())
    
    if not linhas_para_atualizar.any():
        print("Nenhuma correspondência encontrada entre os arquivos e o relatório.")
        return

    # Atualiza a coluna 'status' para essas linhas
    df.loc[linhas_para_atualizar, 'status'] = 'Sucesso (Verificado)'
    
    # Salva o arquivo CSV de volta no disco
    df.to_csv(RELATORIO_CSV, index=False, encoding='utf-8')
    
    num_atualizados = linhas_para_atualizar.sum()
    print(f"Relatório atualizado com sucesso! {num_atualizados} linhas marcadas como 'Sucesso (Verificado)'.")


def main():
    """Função principal que orquestra o processo."""
    print("--- Iniciando Ferramenta de Pós-Processamento ---")
    pastas_alvo = [BUSCA_COMPLETA_FOLDER, BUSCA_POR_TITULO_FOLDER]
    
    # Passo 1: Limpa duplicatas e pega a lista de arquivos que são sucesso
    sucessos = limpar_duplicatas_e_coletar_sucessos(pastas_alvo)
    
    # Passo 2: Usa a lista de sucessos para atualizar o relatório
    atualizar_relatorio(sucessos)
    
    print("\n--- Processo Concluído! ---")


if __name__ == "__main__":
    main()