"""
Assistente de Estudos Local com CodeLlama via Ollama
- Seleção de PDF via janela
- Extrai texto do PDF com pdfplumber
- Gera explicação e tópicos automáticos
- Cria mapa mental em PDF com Graphviz
"""

import pdfplumber
from graphviz import Digraph
import subprocess
import tkinter as tk
from tkinter import filedialog
import os
import shutil
import re

# -------------------------------
# 1️⃣ Função para escolher PDF via janela
# -------------------------------
def escolher_pdf():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal
    caminho_pdf = filedialog.askopenfilename(
        title="Selecione o PDF",
        filetypes=[("PDF files", "*.pdf")]
    )
    return caminho_pdf

# -------------------------------
# 2️⃣ Função para extrair texto de PDF com pdfplumber
# -------------------------------
def extrair_texto_pdf(caminho_pdf):
    texto = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            pagina_texto = pagina.extract_text()
            if pagina_texto:
                texto += pagina_texto + "\n"
    return texto

# -------------------------------
# 3️⃣ Função para gerar explicação e tópicos estruturados via Ollama
# -------------------------------
def gerar_topicos_ollama(texto, modelo="codellama"):
    prompt = f"""
Você é um assistente de estudos.
Leia o conteúdo abaixo e gere uma lista estruturada de tópicos e subtópicos
no seguinte formato:

* Tópico 1: Nome do tópico
    + Subtópico 1: Nome
    + Subtópico 2: Nome

* Tópico 2: Nome do tópico
    + Subtópico 1: Nome
    + Subtópico 2: Nome

Conteúdo:
{texto[:4000]}
"""
    try:
        resultado = subprocess.run(
            ["ollama", "run", modelo],
            input=prompt.encode("utf-8"),
            capture_output=True
        )
        resposta = resultado.stdout.decode("utf-8").strip()
        if not resposta:
            resposta = "⚠️ Nenhuma resposta foi gerada pelo Ollama."
    except FileNotFoundError:
        resposta = "❌ Ollama não encontrado. Certifique-se de que está instalado e no PATH."
    except Exception as e:
        resposta = f"❌ Erro ao chamar Ollama: {e}"
    return resposta

# -------------------------------
# 4️⃣ Função atualizada para parsear a resposta do Ollama
# -------------------------------
def parse_topicos(resposta):
    """
    Aceita o formato gerado pelo Ollama:
    * Tópico 1: Nome
        + Subtópico 1: Nome
        + Subtópico 2: Nome
    """
    topicos = {}
    current_topico = None
    linhas = resposta.splitlines()
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        # Detecta Tópico com *
        if linha.startswith("*") and "Tópico" in linha:
            current_topico = linha.split(":", 1)[1].strip()
            topicos[current_topico] = []
        # Detecta Subtópico com +
        elif linha.startswith("+") and current_topico:
            subt = linha.split(":", 1)[1].strip() if ":" in linha else linha[1:].strip()
            topicos[current_topico].append(subt)
    return topicos

# -------------------------------
# 5️⃣ Função para criar mapa mental com Graphviz
# -------------------------------
def criar_mapa_mental(titulo, topicos_dict):
    # Verifica se o executável dot do Graphviz está no PATH
    if not shutil.which("dot"):
        print("❌ Graphviz não encontrado. Instale Graphviz e adicione 'bin' ao PATH do Windows.")
        return

    dot = Digraph(comment=titulo)
    dot.node('A', titulo)
    for i, (topico, subtopicos) in enumerate(topicos_dict.items()):
        topico_id = f"T{i}"
        dot.node(topico_id, topico)
        dot.edge('A', topico_id)
        for j, subt in enumerate(subtopicos):
            sub_id = f"{topico_id}_{j}"
            dot.node(sub_id, subt)
            dot.edge(topico_id, sub_id)
    try:
        dot.render('mapa_mental', format='pdf', cleanup=True)
        print("✅ Mapa mental salvo como 'mapa_mental.pdf'")
    except Exception as e:
        print(f"❌ Erro ao gerar o mapa mental: {e}")

# -------------------------------
# 6️⃣ Pipeline principal
# -------------------------------
def main():
    caminho_pdf = escolher_pdf()
    if not caminho_pdf:
        print("⚠️ Nenhum PDF selecionado. Saindo...")
        return

    print(f"📄 PDF selecionado: {caminho_pdf}")
    print("🔍 Extraindo texto do PDF...")
    conteudo = extrair_texto_pdf(caminho_pdf)

    print("🤖 Gerando tópicos automáticos com CodeLlama via Ollama...")
    resposta_ollama = gerar_topicos_ollama(conteudo)
    print("\n=== Tópicos gerados ===\n")
    print(resposta_ollama)

    topicos_dict = parse_topicos(resposta_ollama)
    if topicos_dict:
        criar_mapa_mental("Meu Estudo", topicos_dict)
    else:
        print("⚠️ Não foi possível criar o mapa mental. Nenhum tópico detectado.")

if __name__ == "__main__":
    main()
