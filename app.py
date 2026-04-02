import streamlit as st
import pandas as pd
import os
import io

# 🔥 ADICIONE AQUI
import gspread
from google.oauth2.service_account import Credentials

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
    aba = planilha.worksheet(st.secrets["google_sheet"]["worksheet_name"])

    return aba

def carregar_dados():
    aba = conectar_planilha()
    dados = aba.get_all_records()
    df = pd.DataFrame(dados)

    if df.empty:
        df = pd.DataFrame(columns=[
            "id", "Referencia", "CodCor", "Cor", "Quantidade", "CompraRealizada"
        ])

    return df

# ================= IMAGENS =================
CAMINHO_IMAGENS = "imagens"

if not os.path.exists(CAMINHO_IMAGENS):
    os.makedirs(CAMINHO_IMAGENS)

# ================= CONEXÃO =================
df_alerta = carregar_dados()

# ================= CRIAR TABELA =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS estoque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Referencia TEXT NOT NULL,
    CodCor TEXT NOT NULL,
    Cor TEXT NOT NULL,
    Quantidade INTEGER NOT NULL DEFAULT 0,
    CompraRealizada INTEGER NOT NULL DEFAULT 0
)
""")
conn.commit()

st.markdown("<h1 style='text-align: center;'>Estoque NPC</h1>", unsafe_allow_html=True)

# ================= ALERTA =================
st.markdown("<h2 style='color:red; text-align: center;'>⚠️ ALERTA DE COMPRA</h2>", unsafe_allow_html=True)

df_alerta = pd.read_sql("SELECT * FROM estoque", conn)

alerta = df_alerta[
    (df_alerta["Quantidade"] <= 2) &
    (df_alerta["CompraRealizada"] == 0)
].copy()

alerta = alerta.sort_values(by=["Referencia", "CodCor"])

if "imagem_alerta_selecionada" not in st.session_state:
    st.session_state.imagem_alerta_selecionada = None

if not alerta.empty:
    st.warning("⚠️ Fazer pedido desses itens AGORA")

    # Cabeçalhos
    col1, col2, col3, col4, col5, col6 = st.columns([2.8, 2, 3, 2, 1, 2.5])
    col1.markdown("**Referencia**")
    col2.markdown("**CodCor**")
    col3.markdown("**Cor**")
    col4.markdown("**Imagem**")
    col5.markdown("<div style='text-align:center; font-weight:bold;'>Qtd</div>", unsafe_allow_html=True)
    col6.markdown("**Ação**")

    st.markdown("<hr style='margin: 6px 0; border: 1px solid #666;'>", unsafe_allow_html=True)

    ref_anterior_alerta = ""

    for _, row in alerta.iterrows():
        ref_atual_alerta = str(row["Referencia"]).strip()

        if ref_anterior_alerta != "" and ref_anterior_alerta != ref_atual_alerta:
            st.markdown("<hr style='margin: 2px 0; border: 1px solid #555;'>", unsafe_allow_html=True)

        col1, col2, col3, col4, col5, col6 = st.columns([2.8, 2, 3, 2, 1, 2.5])

        col1.write(row["Referencia"])
        col2.write(row["CodCor"])
        col3.write(row["Cor"])

        # IMAGEM
        extensoes = ["jpg", "jpeg", "png", "JPG", "JPEG", "PNG"]
        caminho_img_alerta = None

        for ext in extensoes:
            caminho_teste = os.path.join(CAMINHO_IMAGENS, f"{row['Referencia']}.{ext}")
            if os.path.exists(caminho_teste):
                caminho_img_alerta = caminho_teste
                break

        if caminho_img_alerta:
            if col4.button("👁 Ver", key=f"ver_img_alerta_{row['id']}"):
                if st.session_state.imagem_alerta_selecionada == row["id"]:
                    st.session_state.imagem_alerta_selecionada = None
                else:
                    st.session_state.imagem_alerta_selecionada = row["id"]
                st.rerun()
        else:
            col4.markdown("<div style='text-align:center;'>—</div>", unsafe_allow_html=True)

        # QTD
        qtd_alerta = int(row["Quantidade"])
        cor_qtd_alerta = "#dc2626" if qtd_alerta == 0 else "#f59e0b"

        col5.markdown(
            f"""
            <div style='
                display:flex;
                justify-content:center;
                align-items:center;
                width:100%;
            '>
                <div style='
                    font-size:18px;
                    font-weight:bold;
                    color:white;
                    background-color:{cor_qtd_alerta};
                    border-radius:6px;
                    width:40px;
                    height:30px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    margin:auto;
                '>
                    {qtd_alerta}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # AÇÃO
        if col6.button("OC Realizada", key=f"buy_{row['id']}"):
            cursor.execute("""
                UPDATE estoque
                SET CompraRealizada = 1
                WHERE id = ?
            """, (row["id"],))
            conn.commit()
            st.rerun()

        # IMAGEM ABAIXO DA LINHA CLICADA
        if st.session_state.imagem_alerta_selecionada == row["id"] and caminho_img_alerta:
            st.markdown(
                "<div style='background-color:#111827; padding:12px; border-radius:10px; margin:8px 0 14px 0;'>",
                unsafe_allow_html=True
            )

            st.image(
                caminho_img_alerta,
                caption=f"Referência: {row['Referencia']}",
                use_container_width=True
            )

            st.markdown("</div>", unsafe_allow_html=True)

        ref_anterior_alerta = ref_atual_alerta

    if st.button("✔️ Marcar todos como comprados", key="buy_all_alerta"):
        cursor.execute("""
            UPDATE estoque
            SET CompraRealizada = 1
            WHERE Quantidade <= 2 AND CompraRealizada = 0
        """)
        conn.commit()
        st.rerun()

else:
    st.success("Estoque saudável 👍")
st.divider()

# ================= LISTA =================
st.markdown("<h3 style='text-align: center;'>📦 Estoque Atual</h3>", unsafe_allow_html=True)

df = pd.read_sql("SELECT * FROM estoque", conn)
df = df.sort_values(by=["Referencia", "CodCor"])

# ================= BUSCA =================
busca = st.text_input("🔎 Buscar por Referência")

if busca:
    df = df[
        df["Referencia"].astype(str).str.contains(busca, case=False, na=False) |
        df["Cor"].astype(str).str.contains(busca, case=False, na=False)
    ]

def get_quantidade(row):
    valor = row.get("Quantidade", 0)
    if pd.isna(valor):
        return 0
    try:
        return int(valor)
    except:
        return 0

if "imagem_selecionada" not in st.session_state:
    st.session_state.imagem_selecionada = None

# Cabeçalhos
col1, col2, col3, col4, col5, col6, col7 = st.columns([2.8, 2, 3, 2, 1, 2.5, 4])
col1.markdown("**Referencia**")
col2.markdown("**CodCor**")
col3.markdown("**Cor**")
col4.markdown("**Imagem**")
col5.markdown("<div style='text-align:center; font-weight:bold;'>Qtd</div>", unsafe_allow_html=True)
col6.markdown("**Status**")
col7.markdown("**Atualizar**")

st.markdown("<hr style='margin: 2px 0; border: 1px solid #888;'>", unsafe_allow_html=True)

ref_anterior = ""

for _, row in df.iterrows():
    ref_atual = str(row["Referencia"]).strip()

    if ref_anterior != "" and ref_anterior != ref_atual:
        st.markdown("<hr style='margin: 2px 0; border: 1px solid #555;'>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6, col7 = st.columns([2.8, 2, 3, 2, 1, 2.5, 4])

    col1.write(row["Referencia"])
    col2.write(row["CodCor"])
    col3.write(row["Cor"])

    # IMAGEM
    extensoes = ["jpg", "jpeg", "png", "JPG", "JPEG", "PNG"]
    caminho_img = None

    for ext in extensoes:
        caminho_teste = os.path.join(CAMINHO_IMAGENS, f"{row['Referencia']}.{ext}")
        if os.path.exists(caminho_teste):
            caminho_img = caminho_teste
            break

    if caminho_img:
        if col4.button("👁 Ver", key=f"ver_img_{row['id']}"):
            if st.session_state.imagem_selecionada == row["id"]:
                st.session_state.imagem_selecionada = None
            else:
                st.session_state.imagem_selecionada = row["id"]
            st.rerun()
    else:
        col4.markdown("<div style='text-align:center;'>—</div>", unsafe_allow_html=True)

    # QTD
    qtd = get_quantidade(row)

    col5.markdown(
        f"""
        <div style='
            display:flex;
            justify-content:center;
            align-items:center;
            width:100%;
        '>
            <div style='
                font-size:18px;
                font-weight:bold;
                background-color:#1f2937;
                border-radius:6px;
                width:40px;
                height:30px;
                display:flex;
                align-items:center;
                justify-content:center;
                margin:auto;
            '>
                {qtd}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # STATUS
    if qtd <= 2:
        col6.markdown("🟡 OC REALIZADA" if row["CompraRealizada"] else "🔴 FAZER OC")
    else:
        col6.markdown("🟢 OK")

    # ATUALIZAR
    sub1, sub2 = col7.columns([3, 1])

    nova_qtd = sub1.number_input(
        "",
        min_value=0,
        max_value=999,
        value=qtd,
        key=f"qtd_{row['id']}",
        label_visibility="collapsed"
    )

    if sub2.button("✔", key=f"save_{row['id']}", use_container_width=True):
        cursor.execute("""
            UPDATE estoque
            SET Quantidade = ?, CompraRealizada = 0
            WHERE id = ?
        """, (nova_qtd, row["id"]))
        conn.commit()
        st.rerun()

    # IMAGEM ABAIXO DA LINHA CLICADA
    if st.session_state.imagem_selecionada == row["id"] and caminho_img:
        st.markdown(
            "<div style='background-color:#111827; padding:12px; border-radius:10px; margin:8px 0 14px 0;'>",
            unsafe_allow_html=True
        )

        st.image(
            caminho_img,
            caption=f"Referência: {row['Referencia']}",
            use_container_width=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    ref_anterior = ref_atual
        
# 🔥 Backup download
import io
df_backup = pd.read_sql("SELECT * FROM estoque", conn)
buffer = io.BytesIO()
df_backup.to_excel(buffer, index=False)
buffer.seek(0)

st.download_button(
    "📥 Baixar Backup",
    buffer,
    "estoque_backup.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.divider()
# ================= RESTAURAR BACKUP =================
st.markdown("<h3 style='text-align: center;'>🔄 Restaurar Backup</h3>", unsafe_allow_html=True)

arquivo_backup = st.file_uploader("Enviar arquivo .xlsx", type=["xlsx"])

if arquivo_backup is not None:
    if st.button("Restaurar Backup"):
        df_backup = pd.read_excel(arquivo_backup)

        colunas = ["Referencia", "CodCor", "Cor", "Quantidade"]

        if not all(col in df_backup.columns for col in colunas):
            st.error("Arquivo inválido")
        else:
            cursor.execute("DELETE FROM estoque")

            for _, row in df_backup.iterrows():
                cursor.execute("""
                INSERT INTO estoque (Referencia, CodCor, Cor, Quantidade, CompraRealizada)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    row["Referencia"],
                    row["CodCor"],
                    row["Cor"],
                    int(row["Quantidade"]),
                    int(bool(row.get("CompraRealizada", False)))
                ))

            conn.commit()

            st.success("Backup restaurado!")
            st.rerun()
            
st.divider()

# ================= CADASTRO =================
st.markdown("<h2 style='text-align: center;'>Cadastro de Estoque</h2>", unsafe_allow_html=True)

referencia = st.text_input("Referência")
cod_cores = st.text_input("Códigos das Cores")
cores = st.text_input("Cores")
quantidades = st.text_input("Volumes")

if st.button("Adicionar / Atualizar"):

    if not referencia or not cod_cores or not cores or not quantidades:
        st.warning("Preencha tudo")
        st.stop()

    lista_cod = [c.strip() for c in cod_cores.split(",")]
    lista_cores = [c.strip().upper() for c in cores.split(",")]

    try:
        lista_qtd = [int(q.strip()) for q in quantidades.split(",")]
    except:
        st.error("Quantidade inválida")
        st.stop()

    if any(q < 0 for q in lista_qtd):
        st.error("Quantidade inválida (não pode ser negativa)")
        st.stop()

    if not (len(lista_cod) == len(lista_cores) == len(lista_qtd)):
        st.error("Dados não batem!")
    else:
        for cod, cor, qtd in zip(lista_cod, lista_cores, lista_qtd):

            cursor.execute("""
            SELECT id FROM estoque
            WHERE Referencia = ? AND CodCor = ?
            """, (referencia, cod))

            existe = cursor.fetchone()

            if existe:
                cursor.execute("""
                UPDATE estoque
                SET Quantidade = ?, CompraRealizada = 0
                WHERE Referencia = ? AND CodCor = ?
                """, (qtd, referencia, cod))
            else:
                cursor.execute("""
                INSERT INTO estoque (Referencia, CodCor, Cor, Quantidade, CompraRealizada)
                VALUES (?, ?, ?, ?, 0)
                """, (referencia, cod, cor, qtd))

        conn.commit()
        st.success("Estoque atualizado!")
        st.rerun()

st.divider()

# ================= EXCLUIR =================
st.markdown("<h2 style='text-align: center;'>Excluir Item</h2>", unsafe_allow_html=True)

ref_del = st.text_input("Referência", key="del_ref")
cod_del = st.text_input("Código da Cor", key="del_cod")

if st.button("Excluir"):
    cursor.execute("""
    DELETE FROM estoque
    WHERE Referencia = ? AND CodCor = ?
    """, (ref_del, cod_del))

    conn.commit()
    st.success("Excluído!")
    st.rerun()
