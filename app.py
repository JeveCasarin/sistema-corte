import streamlit as st
import pandas as pd
import os
import io
import gspread
from google.oauth2.service_account import Credentials

# ================= GOOGLE SHEETS =================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def conectar_planilha():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    gc = gspread.authorize(creds)

    planilha = gc.open_by_url(st.secrets["google_sheet"]["spreadsheet_url"])
    aba = planilha.worksheet(st.secrets["google_sheet"]["worksheet_name"].strip())
    
    return aba

def carregar_dados():
    aba = conectar_planilha()
    dados = aba.get_all_records()
    df = pd.DataFrame(dados)

    if df.empty:
        df = pd.DataFrame(columns=[
            "id", "Referencia", "CodCor", "Cor", "Quantidade", "CompraRealizada"
        ])

    for col in ["id", "Referencia", "CodCor", "Cor", "Quantidade", "CompraRealizada"]:
        if col not in df.columns:
            df[col] = ""

    if not df.empty:
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
        df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)
        df["CompraRealizada"] = pd.to_numeric(df["CompraRealizada"], errors="coerce").fillna(0).astype(int)

    return df

def salvar_dados(df):
    aba = conectar_planilha()

    colunas = ["id", "Referencia", "CodCor", "Cor", "Quantidade", "CompraRealizada"]

    for col in colunas:
        if col not in df.columns:
            df[col] = ""

    df = df[colunas].fillna("")
    dados = [colunas] + df.astype(str).values.tolist()

    aba.clear()
    aba.update(dados)

def proximo_id(df):
    if df.empty:
        return 1
    return int(pd.to_numeric(df["id"], errors="coerce").fillna(0).max()) + 1

# ================= IMAGENS =================
CAMINHO_IMAGENS = "imagens"

if not os.path.exists(CAMINHO_IMAGENS):
    os.makedirs(CAMINHO_IMAGENS)

# ================= UI =================
st.markdown("<h1 style='text-align: center;'>Estoque NPC</h1>", unsafe_allow_html=True)

# ================= ALERTA =================
st.markdown("<h2 style='color:red; text-align: center;'>⚠️ ALERTA DE COMPRA</h2>", unsafe_allow_html=True)

df_alerta = carregar_dados()

alerta = df_alerta[
    (df_alerta["Quantidade"] <= 2) &
    (df_alerta["CompraRealizada"] == 0)
].copy()

alerta = alerta.sort_values(by=["Referencia", "CodCor"])

if "imagem_alerta_selecionada" not in st.session_state:
    st.session_state.imagem_alerta_selecionada = None

if not alerta.empty:
    st.warning("⚠️ Fazer pedido desses itens AGORA")

    col1, col2, col3, col4, col5, col6 = st.columns([2.8, 2, 3, 2, 1, 2.5])
    col1.markdown("**Referencia**")
    col2.markdown("**CodCor**")
    col3.markdown("**Cor**")
    col4.markdown("**Imagem**")
    col5.markdown("**Qtd**")
    col6.markdown("**Ação**")

    for _, row in alerta.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([2.8, 2, 3, 2, 1, 2.5])

        col1.write(row["Referencia"])
        col2.write(row["CodCor"])
        col3.write(row["Cor"])

        col5.write(row["Quantidade"])

        if col6.button("OC Realizada", key=f"buy_{row['id']}"):
            df_edit = carregar_dados()
            df_edit.loc[df_edit["id"] == int(row["id"]), "CompraRealizada"] = 1
            salvar_dados(df_edit)
            st.rerun()

    if st.button("✔️ Marcar todos como comprados"):
        df_edit = carregar_dados()
        mask = (df_edit["Quantidade"] <= 2) & (df_edit["CompraRealizada"] == 0)
        df_edit.loc[mask, "CompraRealizada"] = 1
        salvar_dados(df_edit)
        st.rerun()

else:
    st.success("Estoque saudável 👍")

st.divider()

# ================= LISTA =================
st.markdown("<h3 style='text-align: center;'>📦 Estoque Atual</h3>", unsafe_allow_html=True)

df = carregar_dados()

busca = st.text_input("🔎 Buscar")

if busca:
    df = df[df["Referencia"].astype(str).str.contains(busca, case=False)]

for _, row in df.iterrows():
    col1, col2, col3, col4 = st.columns(4)

    col1.write(row["Referencia"])
    col2.write(row["CodCor"])
    col3.write(row["Cor"])

    nova_qtd = col4.number_input(
        "Qtd",
        value=int(row["Quantidade"]),
        key=f"qtd_{row['id']}"
    )

    if st.button("Atualizar", key=f"upd_{row['id']}"):
        df_edit = carregar_dados()
        df_edit.loc[df_edit["id"] == int(row["id"]), "Quantidade"] = int(nova_qtd)
        df_edit.loc[df_edit["id"] == int(row["id"]), "CompraRealizada"] = 0
        salvar_dados(df_edit)
        st.rerun()

# ================= BACKUP =================
df_backup = carregar_dados()
buffer = io.BytesIO()
df_backup.to_excel(buffer, index=False)
buffer.seek(0)

st.download_button("📥 Backup", buffer, "backup.xlsx")

# ================= RESTAURAR =================
arquivo_backup = st.file_uploader("Restaurar backup")

if arquivo_backup and st.button("Restaurar"):
    df_backup = pd.read_excel(arquivo_backup)

    df_edit = pd.DataFrame()

    for _, row in df_backup.iterrows():
        novo = {
            "id": proximo_id(df_edit),
            "Referencia": row["Referencia"],
            "CodCor": row["CodCor"],
            "Cor": row["Cor"],
            "Quantidade": int(row["Quantidade"]),
            "CompraRealizada": int(bool(row.get("CompraRealizada", False)))
        }
        df_edit = pd.concat([df_edit, pd.DataFrame([novo])], ignore_index=True)

    salvar_dados(df_edit)
    st.success("Restaurado!")
    st.rerun()

# ================= CADASTRO =================
st.markdown("## Cadastro")

referencia = st.text_input("Referencia")
cod = st.text_input("CodCor")
cor = st.text_input("Cor")
qtd = st.number_input("Quantidade", min_value=0)

if st.button("Adicionar"):
    df_edit = carregar_dados()

    novo = {
        "id": proximo_id(df_edit),
        "Referencia": referencia,
        "CodCor": cod,
        "Cor": cor,
        "Quantidade": int(qtd),
        "CompraRealizada": 0
    }

    df_edit = pd.concat([df_edit, pd.DataFrame([novo])], ignore_index=True)
    salvar_dados(df_edit)
    st.success("Adicionado!")
    st.rerun()

# ================= EXCLUIR =================
ref_del = st.text_input("Ref excluir")
cod_del = st.text_input("Cod excluir")

if st.button("Excluir"):
    df_edit = carregar_dados()
    df_edit = df_edit[~(
        (df_edit["Referencia"] == ref_del) &
        (df_edit["CodCor"] == cod_del)
    )]
    salvar_dados(df_edit)
    st.success("Excluído!")
    st.rerun()
