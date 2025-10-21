<h1 align="center"> 🎵 Grupo de Estudos de Música 🎵 </h1>

<p>Esse repositório possui dados e códigos referentes ao grupo de estudos e de extensão de músicas, onde analisamos o cenário musical atual e buscamos ideias para utilizar de ferramentas computacionais no auxílio aos criadores musicais. .</p>

 ![Badge Em Desenvolvido](https://img.shields.io/badge/STATUS-EmDesenvolvimento-orange)

# 🔨 Funcionalidades do projeto

- `Aprendizado`: Desenvolvido para aprimorar habilidades como cientista de dados
- `Organização de dados`: Organiza sistemas de músicas mais ouvidas
- `Análise de dados`: Analisamos dados culturais acerca do povo brasileiro
- `Aprendizado de máquina`: Envolve partes do processo da criação de um modelo de IA capaz de auxiliar na criação de músicas. 
- `Discussões`: Leva a discussões sobre quais condições históricas influenciam o gosto brasileiro

# 👀 Objetivos

- Desenvolver aprendizados adquiridos no curso de ciência de dados, analisar dados culturais do Brasil e entender melhor o que eles dizem sobre nosso povo. 
- Criar um software guiado por Inteligência Artificial capaz de ajudar na criação e inovação de músicas.

# ✔️ Tecnologias Utilizadas

- `Python`
- `Notebook Python`
- `Pandas, Babypandas, Matplotlib, youtube-search-python`

# ❗ Observações importantes
## Observação 1
A pasta billboard possui códigos para baixar áudios de músicas do youtube, mas os áudios não estão disponíveis aqui. Porém, sintam-se livres para utilizar o código. O objetivo final do grupo de estudos eram análises, então não foi necessário manter os aúdios baixados. a pasta realbook, por outro lado, tem códigos sobre as músicas do realbook.com, sendo utilizados para baixar áudios a serem usados na criação de uma inteligência artificial. Esses áudios podem ser encontrados em sua pasta compactada no endereço: https://drive.google.com/drive/folders/1HTDx8bsA3QMDMmFCAXb_hK6tdj7Cf2vt?usp=sharing

Para mais dados baixados e outras informações do projeto, preça acesso à pasta do drive: https://drive.google.com/drive/folders/1RTFf38fDvN2lxUKc_EV9-gdgwUBCI6zV?usp=drive_link

## Observação 2
O pré-processamento dos dados de áudio seguiu um pipeline bem definido para transformar as músicas brutas em um formato adequado para análise e modelos de aprendizado de máquina. Abaixo estão as etapas principais:

**1. Segmentação dos Áudios com FFmpeg**

  - As músicas originais em formato `.mp3` foram divididas em clipes menores, com duração de 10 segundos cada.
  - Este processo foi automatizado via linha de comando utilizando o **FFmpeg**, garantindo que cada música gerasse múltiplos segmentos para aumentar a quantidade de dados.
  - Os comandos utilizados foram:
      - **Windows:**
        ```cmd
        for %a in (*.mp3) do ffmpeg -i "%a" -f segment -segment_time 10 -c copy "musicas_divididas\%~na_parte_%03d.mp3"
        ```
      - **macOS/Linux:**
        ```bash
        for a in *.mp3; do ffmpeg -i "$a" -f segment -segment_time 10 -c copy "musicas_divididas/${a%.*}_parte_%03d.mp3"; done
        ```

**2. Seleção e Limpeza dos Clipes**

  - O script `buscar_musicas.py` foi executado para selecionar, a partir de duas pastas de origem, os clipes que apresentavam boa similaridade.
  - Como parte da organização, foi necessário executar um comando para renomear arquivos em lote, removendo o prefixo `temp_` de seus nomes.

**3. Conversão para o Espaço Latente com Music2Latent**

  - Cada clipe de áudio de 10 segundos foi processado pela biblioteca `music2latent`.
  - O objetivo desta etapa foi converter a forma de onda do áudio em uma representação vetorial compacta, conhecida como **vetor latente**.
  - O resultado foi um conjunto de arquivos `.npy` (formato NumPy), onde cada arquivo corresponde à representação latente de um clipe de áudio.
  - **Observação:** Foi notado que o `music2latent` não conseguiu processar todos os clipes, resultando em alguns áudios não sendo convertidos para o formato latente.


# 👩 Autores

Grupo de Extensão de Música guiado pelo professor Flávio Figueiredo, com o auxílio de alunos do laboratório UAI e organizados no Departamento de Ciência da Computação, na Universidade Federa de Minas Gerais.





