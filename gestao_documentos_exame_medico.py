import sys
import subprocess
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path, PureWindowsPath
import itertools
from requests_oauthlib import OAuth2Session
import time
import requests


modulos_dir = Path(__file__).parent / "Modulos"

# Se o diretório ainda não existir, faz o clone direto do GitHub
if not modulos_dir.exists():
    print("📥 Clonando repositório Modulos do GitHub...")
    subprocess.run([
        "git", "clone",
        "https://github.com/DellaVolpe69/Modulos.git",
        str(modulos_dir)
    ], check=True)

# Garante que o diretório está no caminho de importação
if str(modulos_dir) not in sys.path:
    sys.path.insert(0, str(modulos_dir))

# Agora importa o módulo normalmente
# from Modulos import AzureLogin 
from Modulos import ConectionSupaBase
###################################
# from Modulos.Minio.examples.MinIO import read_file  # ajuste o caminho se necessário 


# ---------------------------------------------------
# IMPORTA CONEXÃO SUPABASE
# ---------------------------------------------------
sys.path.append(PureWindowsPath(r'\\tableau\Central_de_Performance\BI\Cloud\Scripts\Modulos').as_posix())
import ConectionSupaBase

supabase = ConectionSupaBase.conexao()

# ---------------------------------------------------
# FUNÇÕES DE BANCO
# ---------------------------------------------------
def carregar_dados():
    data = supabase.table("Gestao_documentos").select("*").execute()
    return pd.DataFrame(data.data)

def adicionar_registro(bp_motorista, nome_motorista, numero_agregado, placa, operacao, data_vencimento, status):
    supabase.table("Gestao_documentos").insert({
        "BP_MOTORISTA": bp_motorista,
        "NOME_MOTORISTA": nome_motorista,
        "NUMERO_AGREGADO": numero_agregado,
        "PLACA": placa,
        "OPERACAO": operacao,
        "DATA_VENCIMENTO": data_vencimento,
        "STATUS": status
    }).execute()

    st.success("✅ Registro adicionado com sucesso!")

def bp_existe(bp_motorista):
    result = supabase.table("Gestao_documentos") \
        .select("BP_MOTORISTA") \
        .eq("BP_MOTORISTA", bp_motorista) \
        .execute()
    
    return len(result.data) > 0

def buscar_por_bp(bp_motorista):
    result = supabase.table("Gestao_documentos") \
        .select("*") \
        .eq("BP_MOTORISTA", bp_motorista) \
        .execute()

    if result.data:
        return result.data[0]
    return None

def atualizar_registro_por_bp(bp_original, bp, nome, agregado, placa, operacao, venc, status):
    supabase.table("Gestao_documentos").update({
        "BP_MOTORISTA": bp,
        "NOME_MOTORISTA": nome,
        "NUMERO_AGREGADO": agregado,
        "PLACA": placa,
        "OPERACAO": operacao,
        "DATA_VENCIMENTO": venc,
        "STATUS": status
    }).eq("BP_MOTORISTA", bp_original).execute()

    st.success("✏️ Registro atualizado com sucesso!")

def deletar_registro_por_bp(bp_motorista):
    supabase.table("Gestao_documentos").delete().eq("BP_MOTORISTA", bp_motorista).execute()
    st.success("🗑️ Registro deletado com sucesso!")

# ---------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# ---------------------------------------------------
st.set_page_config(
    page_title="Gestão de Documentos",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# CSS
# ---------------------------------------------------
st.markdown("""
    <style>
    section[data-testid="stSidebar"] h1 {
        text-align: center;
        color: orange;
    }
    <meta name="google" content="notranslate">  
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# STATE DA NAVEGAÇÃO
# ---------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "add"

if "show_table" not in st.session_state:
    st.session_state.show_table = False

def go(page):
    st.session_state.page = page

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
with st.sidebar:
    st.title('Gestão de Documentos')
    st.markdown("Adicione, edite ou pesquise seus documentos!")
    st.button("➕ Adicionar", on_click=go, args=("add",))
    st.button("✏️ Editar / Excluir ", on_click=go, args=("edit",))


# ===================================================
# ===================== ADICIONAR ===================
# ===================================================
if st.session_state.page == "add":
    st.subheader("Cadastrar novo motorista")

    bp_motorista = st.text_input("BP do Motorista")
    nome_motorista = st.text_input("Nome do Motorista")
    numero_agregado = st.text_input("Número do Agregado")
    placa = st.text_input("Placa")
    operacao = st.text_input("Operação")
    data_venc = st.date_input("Data de Vencimento")
    status = st.selectbox("Status", ["CONCLUIDO", "VENCIDO"])

    if st.button("Salvar"):
        if not (bp_motorista and nome_motorista and numero_agregado and placa and operacao and data_venc and status):
            st.warning("⚠️ Preencha todos os campos antes de salvar.")
        
        else:
            if not numero_agregado.isdigit():
                st.warning("⚠️ O número do agregado deve conter apenas números.")

            elif bp_existe(bp_motorista):
                st.error("⚠️ Esse BP já existe! Vá na aba EDITAR para alterá-lo")
            
            else:
                adicionar_registro(
                    bp_motorista,
                    nome_motorista,
                    numero_agregado,
                    placa,
                    operacao,
                    data_venc.isoformat(),
                    status
                )


# ===================================================
# ====================== EDITAR =====================
# ===================================================
if st.session_state.page == "edit":
    st.subheader("🔍 Buscar motorista por BP")

    bp_busca = st.text_input("Digite o BP do motorista")

    colA, colB = st.columns(2)

    with colA:
        if st.button("📋 Exibir todos os cadastros"):
            st.session_state.show_table = True

    with colB:
        if st.button("❌ Ocultar lista"):
            st.session_state.show_table = False

    if st.session_state.show_table:
        df = carregar_dados()
        if df.empty:
            st.info("Nenhum registro encontrado no banco.")
        else:
            st.dataframe(df, use_container_width=True)

    if st.button("Buscar"):
        registro = buscar_por_bp(bp_busca)
        st.session_state.registro_encontrado = registro

        if not registro:
            st.error("BP não encontrado.")

    if "registro_encontrado" in st.session_state and st.session_state.registro_encontrado:
        r = st.session_state.registro_encontrado

        st.subheader("✏️ Editar informações")

        bp_original = r["BP_MOTORISTA"]

        new_bp = st.text_input("BP do Motorista", r["BP_MOTORISTA"])
        new_nome = st.text_input("Nome do Motorista", r["NOME_MOTORISTA"])
        new_agregado = st.text_input("Número do Agregado", r["NUMERO_AGREGADO"])
        new_placa = st.text_input("Placa", r["PLACA"])
        new_operacao = st.text_input("Operação", r["OPERACAO"])
        new_venc = st.date_input("Data de Vencimento", value=pd.to_datetime(r["DATA_VENCIMENTO"]))
        new_status = st.selectbox("Status", ["CONCLUIDO", "VENCIDO"], index=["CONCLUIDO","VENCIDO"].index(r["STATUS"]))

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Salvar alterações"):
                atualizar_registro_por_bp(
                    bp_original,
                    new_bp,
                    new_nome,
                    new_agregado,
                    new_placa,
                    new_operacao,
                    new_venc.isoformat(),
                    new_status
                )
                st.session_state.registro_encontrado = None

        with col2:
            if st.button("Excluir registro"):
                deletar_registro_por_bp(bp_original)
                st.session_state.registro_encontrado = None
