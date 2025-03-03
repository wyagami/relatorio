import streamlit as st
import pandas as pd
import json
import requests
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

def gerar_relatorio_pdf(df, titulo, resumo, descricao_graficos, imagens_graficos):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, titulo, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, "Resumo da IA:", ln=True)
    pdf.multi_cell(0, 10, resumo)
    pdf.ln(10)
    
    pdf.cell(200, 10, "Descrição dos Gráficos:", ln=True)
    pdf.multi_cell(0, 10, descricao_graficos)
    pdf.ln(10)
    
    pdf.cell(200, 10, "Dados:", ln=True)
    for col in df.columns:
        pdf.cell(40, 10, str(col), border=1)
    pdf.ln()
    
    for _, row in df.iterrows():
        for val in row:
            pdf.cell(40, 10, str(val), border=1)
        pdf.ln()
    
    pdf.ln(10)
    pdf.cell(200, 10, "Gráficos:", ln=True)
    for img_path in imagens_graficos:
        if os.path.exists(img_path):  # Garante que o arquivo existe antes de adicioná-lo
            pdf.add_page()
            pdf.image(img_path, x=10, y=20, w=180)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        return tmpfile.name

def obter_resposta_ia(mensagem):
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + st.secrets["qwen_key"],
            "Content-Type": "application/json",
            "HTTP-Referer": "https://seu-dominio.com",
            "X-Title": "RimaBot",
        },
        data=json.dumps({
            "model": "qwen/qwen2.5-vl-72b-instruct:free",
            "messages": [
                {"role": "system", "content": "Você é um assistente que gera gráficos e resumos baseados em dados carregados."},
                {"role": "user", "content": mensagem},
            ],
        })
    )
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "Erro ao obter resposta da IA")

st.set_page_config(page_title="Gerador de Relatórios PDF", layout="wide")
st.title("📄 Gerador de Relatórios Automáticos")

uploaded_file = st.file_uploader("Carregar arquivo CSV ou Excel", type=["csv", "xlsx"])

titulo = st.text_input("Título do Relatório", "Relatório de Análise de Dados")

if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1]
    if file_extension == "csv":
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.subheader("📊 Visualização dos Dados")
    st.dataframe(df)
    
    descricao_graficos = obter_resposta_ia(f"Gere gráficos baseados nos seguintes dados:\n{df.to_string()}")
    resumo = obter_resposta_ia(f"Resuma os seguintes dados:\n{df.to_string()}")
    
    st.subheader("📊 Painel de Gráficos")
    colunas_numericas = df.select_dtypes(include=['number']).columns
    imagens_graficos = []
    
    if not colunas_numericas.empty:
        colunas_disponiveis = colunas_numericas[:6]
        fig, axes = plt.subplots(2, 3, figsize=(12, 8))  # Criando painel 2x3
        tipos_graficos = ["hist", "pie", "line", "barh", "bar", "area"]
        
        for i, (col, ax, tipo) in enumerate(zip(colunas_disponiveis, axes.flatten(), tipos_graficos)):
            if tipo == "hist":
                df[col].hist(ax=ax, bins=20)
                ax.set_title(f"Histograma de {col}")
            elif tipo == "pie" and df[col].nunique() < 10:
                df[col].value_counts().plot(kind="pie", ax=ax, autopct='%1.1f%%')
                ax.set_title(f"Pizza de {col}")
            elif tipo == "line":
                df[col].plot(kind="line", ax=ax)
                ax.set_title(f"Linha de {col}")
            elif tipo == "barh":
                df[col].value_counts().plot(kind="barh", ax=ax)
                ax.set_title(f"Barras Horizontais de {col}")
            elif tipo == "bar":
                df[col].value_counts().plot(kind="bar", ax=ax)
                ax.set_title(f"Barras Verticais de {col}")
            elif tipo == "area":
                df[col].plot(kind="area", ax=ax)
                ax.set_title(f"Área de {col}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                plt.savefig(tmpfile.name)
                imagens_graficos.append(tmpfile.name)
        
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.write("Não há colunas numéricas adequadas para gerar gráficos.")
    
    st.subheader("🤖 Resumo da IA")
    st.write(resumo)
    
    pdf_path = gerar_relatorio_pdf(df.astype(str), titulo, resumo, descricao_graficos, imagens_graficos)
    with open(pdf_path, "rb") as file:
        st.download_button("📥 Baixar Relatório PDF", file, file_name="relatorio.pdf", mime="application/pdf")
    
    for img_path in imagens_graficos:
        if os.path.exists(img_path):
            os.remove(img_path)
