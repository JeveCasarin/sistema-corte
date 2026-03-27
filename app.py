import streamlit as st
import pandas as pd
import sqlite3
import os
import io

# ================= CONFIG =================
st.set_page_config(
    page_title="Estoque NPC",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= CAMINHOS =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
CAMINHO_BANCO = os.path.join(BASE_DIR, "estoque.db")
CAMINHO_IMAGENS = os.path.join(BASE_DIR, "imagens")

if not os.path.exists(CAMINHO_IMAGENS):
    os.makedirs(CAMINHO_IMAGENS)

# ================= CSS =================
st.markdown("""
<style>
/* ===== CONTAINER GERAL ===== */
.block-container{
    padding-top: 1rem;
    padding-bottom: 2rem;
    padding-left: 0.8rem;
    padding-right: 0.8rem;
    max-width: 1250px;
}

/* ===== INPUTS ===== */
input, textarea {
    font-size: 16px !important; /* evita zoom no iPhone/Safari */
}

/* ===== BOTÕES ===== */
.stButton > button,
.stDownloadButton > button {
    width: 100%;
    min-height: 42px;
    border-radius: 10px;
    font-weight: 600;
}

/* ===== CARDS MOBILE ===== */
.npc-card {
    background: #111827;
    border: 1px solid #374151;
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 12px;
}

.npc-card-alerta {
    background: #1f2937;
    border: 1px solid #7f1d1d;
    border-left: 5px solid #dc2626;
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 12px;
}

.npc-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 8px;
    word-break: break-word;
}

.npc-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 12px;
    margin-bottom: 10px;
}

.npc-item {
    background: #0f172a;
    border-radius: 10px;
    padding: 8px 10px;
}

.npc-label {
    font-size: 12px;
    color: #9ca3af;
    margin-bottom: 2px;
}

.npc-value {
    font-size: 15px;
    font-weight: 600;
    word-break: break-word;
}

.npc-qtd {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 42px;
    height: 32px;
    padding: 0 10px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 700;
    color: white;
}

.npc-sep {
    margin: 10px 0 18px 0;
    border: none;
    border-top: 1px solid #374151;
}

/* ===== CONTROLE PC / MOBILE ===== */
.st-key-mobile_alerta,
.st-key-mobile_lista {
    display: none;
}

.st-key-desktop_alerta,
.st-key-desktop_lista {
    display: block;
}

@media (max-width: 768px) {
    .block-container{
        padding-left: 0.55rem;
        padding-right: 0.55rem;
    }

    .st-key-desktop_alerta,
    .st-key-desktop_lista {
        display: none !important;
    }

    .st-key-mobile_alerta,
    .st-key-mobile_lista {
        display: block !important;
    }

    .npc-grid {
        grid-template-columns: 1fr;
        gap: 8px;
    }

    h1, h2, h3 {
        text-align: center !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ================= CONEXÃO =================
def conectar():
    return sqlite3.connect(CAMINHO_BANCO, check_same_thread=False)

conn = conectar()
cursor = conn.cursor()

# ================= TABELA =================
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

# ================= FUNÇÕES =================
def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()

def get_quantidade(row):
    valor = row.get("Quantidade", 0)
    if pd.isna(valor):
        return 0
    try:
        return int(valor)
    except:
        return 0

def get_compra_realizada(row):
    valor = row.get("CompraRealizada", 0)
    try:
        return int(valor)
    except:
        return 0

def get_caminho_imagem(referencia):
    referencia = normalizar_texto(referencia)
    extensoes = ["jpg", "jpeg", "png", "JPG", "JPEG", "PNG", "webp", "WEBP"]

    for ext in extensoes:
        caminho = os.path.join(CAMINHO_IMAGENS, f"{referencia}.{ext}")
        if os.path.exists(caminho):
            return caminho

    return None

def badge_qtd(qtd):
    if qtd == 0:
        cor = "#dc2626"
    elif qtd <= 2:
        cor = "#f59e0b"
    else:
        cor = "#16a34a"

    return f"<span class='npc-qtd' style='background:{cor};'>{qtd}</span>"

def status_texto(qtd, compra_realizada):
    if qtd <= 2:
        return "🟡 OC REALIZADA" if int(compra_realizada) == 1 else "🔴 FAZER OC"
    return "🟢 OK"

def carregar_dataframe():
    df = pd.read_sql("SELECT * FROM estoque", conn)
    if not df.empty:
        df["Referencia"] = df["Referencia"].astype(str)
        df["CodCor"] = df["CodCor"].astype(str)
        df["Cor"] = df["Cor"].astype(str)
        df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)
        df["CompraRealizada"] = pd.to_numeric(df["CompraRealizada"], errors="coerce").fillna(0).astype(int)
    return df

# ================= SESSION =================
if "imagem_alerta_selecionada" not in st.session_state:
    st.session_state.imagem_alerta_selecionada = None

if "imagem_selecionada" not in st.session_state:
    st.session_state.imagem_selecionada = None

# ================= TÍTULO =================
st.markdown("<h1 style='text-align: center;'>Estoque NPC</h1>", unsafe_allow_html=True)

# ================= ALERTA DE COMPRA =================
st.markdown("<h2 style='color:red; text-align: center;'>⚠️ ALERTA DE COMPRA</h2>", unsafe_allow_html=True)

df_alerta = carregar_dataframe()

alerta = df_alerta[
    (df_alerta["Quantidade"] <= 2) &
    (df_alerta["CompraRealizada"] == 0)
].copy()

if not alerta.empty:
    alerta = alerta.sort_values(by=["Referencia", "CodCor"])
    st.warning("⚠️ Fazer pedido desses itens AGORA")

    # ===== DESKTOP =====
    with st.container(key="desktop_alerta"):
        h1, h2, h3, h4, h5, h6 = st.columns([2, 2, 2, 1, 2, 2])
        h1.markdown("**Referência**")
        h2.markdown("**CodCor**")
        h3.markdown("**Cor**")
        h4.markdown("**Qtd**")
        h5.markdown("**Imagem**")
        h6.markdown("**Ação**")

        ref_anterior_alerta = ""

        for _, row in alerta.iterrows():
            ref_atual_alerta = normalizar_texto(row["Referencia"])

            if ref_anterior_alerta != "" and ref_anterior_alerta != ref_atual_alerta:
                st.divider()

            qtd_alerta = get_quantidade(row)
            caminho_img_alerta = get_caminho_imagem(row["Referencia"])

            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 1, 2, 2])

            c1.write(normalizar_texto(row["Referencia"]))
            c2.write(normalizar_texto(row["CodCor"]))
            c3.write(normalizar_texto(row["Cor"]))
            c4.markdown(badge_qtd(qtd_alerta), unsafe_allow_html=True)

            if caminho_img_alerta:
                if c5.button("👁 Ver", key=f"ver_img_alerta_desktop_{row['id']}", use_container_width=True):
                    if st.session_state.imagem_alerta_selecionada == f"alerta_{row['id']}":
                        st.session_state.imagem_alerta_selecionada = None
                    else:
                        st.session_state.imagem_alerta_selecionada = f"alerta_{row['id']}"
                    st.rerun()
            else:
                c5.write("-")

            if c6.button("✔ OC", key=f"buy_desktop_{row['id']}", use_container_width=True):
                cursor.execute("""
                    UPDATE estoque
                    SET CompraRealizada = 1
                    WHERE id = ?
                """, (int(row["id"]),))
                conn.commit()
                st.rerun()

            if st.session_state.imagem_alerta_selecionada == f"alerta_{row['id']}" and caminho_img_alerta:
                st.image(
                    caminho_img_alerta,
                    caption=f"Referência: {normalizar_texto(row['Referencia'])}",
                    use_container_width=True
                )

            ref_anterior_alerta = ref_atual_alerta

    # ===== MOBILE =====
    with st.container(key="mobile_alerta"):
        ref_anterior_alerta = ""

        for _, row in alerta.iterrows():
            ref_atual_alerta = normalizar_texto(row["Referencia"])

            if ref_anterior_alerta != "" and ref_anterior_alerta != ref_atual_alerta:
                st.markdown("<hr class='npc-sep'>", unsafe_allow_html=True)

            qtd_alerta = get_quantidade(row)
            caminho_img_alerta = get_caminho_imagem(row["Referencia"])

            st.markdown(f"""
            <div class="npc-card-alerta">
                <div class="npc-title">Referência: {normalizar_texto(row['Referencia'])}</div>
                <div class="npc-grid">
                    <div class="npc-item">
                        <div class="npc-label">Código da Cor</div>
                        <div class="npc-value">{normalizar_texto(row['CodCor'])}</div>
                    </div>
                    <div class="npc-item">
                        <div class="npc-label">Cor</div>
                        <div class="npc-value">{normalizar_texto(row['Cor'])}</div>
                    </div>
                    <div class="npc-item">
                        <div class="npc-label">Quantidade</div>
                        <div class="npc-value">{badge_qtd(qtd_alerta)}</div>
                    </div>
                    <div class="npc-item">
                        <div class="npc-label">Status</div>
                        <div class="npc-value">🔴 FAZER OC</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            ac1, ac2 = st.columns(2)

            if caminho_img_alerta:
                if ac1.button("👁 Ver imagem", key=f"ver_img_alerta_mobile_{row['id']}", use_container_width=True):
                    if st.session_state.imagem_alerta_selecionada == f"alerta_{row['id']}":
                        st.session_state.imagem_alerta_selecionada = None
                    else:
                        st.session_state.imagem_alerta_selecionada = f"alerta_{row['id']}"
                    st.rerun()
            else:
                ac1.write("")

            if ac2.button("✔️ OC Realizada", key=f"buy_mobile_{row['id']}", use_container_width=True):
                cursor.execute("""
                    UPDATE estoque
                    SET CompraRealizada = 1
                    WHERE id = ?
                """, (int(row["id"]),))
                conn.commit()
                st.rerun()

            if st.session_state.imagem_alerta_selecionada == f"alerta_{row['id']}" and caminho_img_alerta:
                st.image(
                    caminho_img_alerta,
                    caption=f"Referência: {normalizar_texto(row['Referencia'])}",
                    use_container_width=True
                )

            ref_anterior_alerta = ref_atual_alerta

    if st.button("✔️ Marcar todos como comprados", key="buy_all_alerta", use_container_width=True):
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

df = carregar_dataframe()

if not df.empty:
    df = df.sort_values(by=["Referencia", "CodCor"])

busca = st.text_input("🔎 Buscar por Referência ou Cor")

if busca:
    df = df[
        df["Referencia"].astype(str).str.contains(busca, case=False, na=False) |
        df["Cor"].astype(str).str.contains(busca, case=False, na=False)
    ]

if df.empty:
    st.info("Nenhum item encontrado.")
else:
    # ===== DESKTOP =====
    with st.container(key="desktop_lista"):
        h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([2, 2, 2, 1, 2, 2, 1.2, 1.5])
        h1.markdown("**Referência**")
        h2.markdown("**CodCor**")
        h3.markdown("**Cor**")
        h4.markdown("**Qtd**")
        h5.markdown("**Status**")
        h6.markdown("**Imagem**")
        h7.markdown("**Nova Qtd**")
        h8.markdown("**Atualizar**")

        ref_anterior = ""

        for _, row in df.iterrows():
            ref_atual = normalizar_texto(row["Referencia"])

            if ref_anterior != "" and ref_anterior != ref_atual:
                st.divider()

            qtd = get_quantidade(row)
            compra_realizada = get_compra_realizada(row)
            caminho_img = get_caminho_imagem(row["Referencia"])
            status = status_texto(qtd, compra_realizada)

            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2, 2, 2, 1, 2, 2, 1.2, 1.5])

            c1.write(normalizar_texto(row["Referencia"]))
            c2.write(normalizar_texto(row["CodCor"]))
            c3.write(normalizar_texto(row["Cor"]))
            c4.markdown(badge_qtd(qtd), unsafe_allow_html=True)
            c5.write(status)

            if caminho_img:
                if c6.button("👁 Ver", key=f"ver_img_desktop_{row['id']}", use_container_width=True):
                    if st.session_state.imagem_selecionada == f"lista_{row['id']}":
                        st.session_state.imagem_selecionada = None
                    else:
                        st.session_state.imagem_selecionada = f"lista_{row['id']}"
                    st.rerun()
            else:
                c6.write("-")

            nova_qtd_desktop = c7.number_input(
                "Nova quantidade",
                min_value=0,
                max_value=999,
                value=qtd,
                key=f"qtd_desktop_{row['id']}",
                label_visibility="collapsed"
            )

            if c8.button("✔ Atualizar", key=f"save_desktop_{row['id']}", use_container_width=True):
                cursor.execute("""
                    UPDATE estoque
                    SET Quantidade = ?, CompraRealizada = 0
                    WHERE id = ?
                """, (int(nova_qtd_desktop), int(row["id"])))
                conn.commit()
                st.rerun()

            if st.session_state.imagem_selecionada == f"lista_{row['id']}" and caminho_img:
                st.image(
                    caminho_img,
                    caption=f"Referência: {normalizar_texto(row['Referencia'])}",
                    use_container_width=True
                )

            ref_anterior = ref_atual

    # ===== MOBILE =====
    with st.container(key="mobile_lista"):
        ref_anterior = ""

        for _, row in df.iterrows():
            ref_atual = normalizar_texto(row["Referencia"])

            if ref_anterior != "" and ref_anterior != ref_atual:
                st.markdown("<hr class='npc-sep'>", unsafe_allow_html=True)

            qtd = get_quantidade(row)
            compra_realizada = get_compra_realizada(row)
            caminho_img = get_caminho_imagem(row["Referencia"])
            status = status_texto(qtd, compra_realizada)

            st.markdown(f"""
            <div class="npc-card">
                <div class="npc-title">Referência: {normalizar_texto(row['Referencia'])}</div>
                <div class="npc-grid">
                    <div class="npc-item">
                        <div class="npc-label">Código da Cor</div>
                        <div class="npc-value">{normalizar_texto(row['CodCor'])}</div>
                    </div>
                    <div class="npc-item">
                        <div class="npc-label">Cor</div>
                        <div class="npc-value">{normalizar_texto(row['Cor'])}</div>
                    </div>
                    <div class="npc-item">
                        <div class="npc-label">Quantidade Atual</div>
                        <div class="npc-value">{badge_qtd(qtd)}</div>
                    </div>
                    <div class="npc-item">
                        <div class="npc-label">Status</div>
                        <div class="npc-value">{status}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            mc1, mc2 = st.columns(2)

            if caminho_img:
                if mc1.button("👁 Ver imagem", key=f"ver_img_mobile_{row['id']}", use_container_width=True):
                    if st.session_state.imagem_selecionada == f"lista_{row['id']}":
                        st.session_state.imagem_selecionada = None
                    else:
                        st.session_state.imagem_selecionada = f"lista_{row['id']}"
                    st.rerun()
            else:
                mc1.write("")

            nova_qtd_mobile = mc2.number_input(
                "Nova quantidade",
                min_value=0,
                max_value=999,
                value=qtd,
                key=f"qtd_mobile_{row['id']}"
            )

            if st.button("✔ Atualizar quantidade", key=f"save_mobile_{row['id']}", use_container_width=True):
                cursor.execute("""
                    UPDATE estoque
                    SET Quantidade = ?, CompraRealizada = 0
                    WHERE id = ?
                """, (int(nova_qtd_mobile), int(row["id"])))
                conn.commit()
                st.rerun()

            if st.session_state.imagem_selecionada == f"lista_{row['id']}" and caminho_img:
                st.image(
                    caminho_img,
                    caption=f"Referência: {normalizar_texto(row['Referencia'])}",
                    use_container_width=True
                )

            ref_anterior = ref_atual

st.divider()

# ================= BACKUP =================
st.markdown("<h3 style='text-align: center;'>📥 Backup</h3>", unsafe_allow_html=True)

df_backup = carregar_dataframe()

buffer = io.BytesIO()
df_backup.to_excel(buffer, index=False)
buffer.seek(0)

st.download_button(
    "📥 Baixar Backup",
    buffer,
    "estoque_backup.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

st.divider()

# ================= RESTAURAR BACKUP =================
st.markdown("<h3 style='text-align: center;'>🔄 Restaurar Backup</h3>", unsafe_allow_html=True)

arquivo_backup = st.file_uploader("Enviar arquivo .xlsx", type=["xlsx"])

if arquivo_backup is not None:
    if st.button("Restaurar Backup", use_container_width=True):
        try:
            df_restaurar = pd.read_excel(arquivo_backup)

            colunas_obrigatorias = ["Referencia", "CodCor", "Cor", "Quantidade"]

            if not all(col in df_restaurar.columns for col in colunas_obrigatorias):
                st.error("Arquivo inválido. As colunas obrigatórias são: Referencia, CodCor, Cor, Quantidade.")
            else:
                cursor.execute("DELETE FROM estoque")

                for _, row in df_restaurar.iterrows():
                    referencia = normalizar_texto(row["Referencia"])
                    codcor = normalizar_texto(row["CodCor"])
                    cor = normalizar_texto(row["Cor"])

                    try:
                        quantidade = int(float(row["Quantidade"]))
                    except:
                        quantidade = 0

                    compra_realizada = 0
                    if "CompraRealizada" in df_restaurar.columns:
                        try:
                            compra_realizada = int(bool(row["CompraRealizada"]))
                        except:
                            compra_realizada = 0

                    cursor.execute("""
                        INSERT INTO estoque (Referencia, CodCor, Cor, Quantidade, CompraRealizada)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        referencia,
                        codcor,
                        cor,
                        quantidade,
                        compra_realizada
                    ))

                conn.commit()
                st.success("Backup restaurado com sucesso!")
                st.rerun()

        except Exception as e:
            st.error(f"Erro ao restaurar backup: {e}")

st.divider()

# ================= CADASTRO =================
st.markdown("<h2 style='text-align: center;'>Cadastro de Estoque</h2>", unsafe_allow_html=True)

referencia = st.text_input("Referência")
cod_cores = st.text_input("Códigos das Cores")
cores = st.text_input("Cores")
quantidades = st.text_input("Volumes")

if st.button("Adicionar / Atualizar", use_container_width=True):
    referencia = normalizar_texto(referencia)

    if not referencia or not cod_cores or not cores or not quantidades:
        st.warning("Preencha tudo.")
        st.stop()

    lista_cod = [c.strip() for c in cod_cores.split(",") if c.strip()]
    lista_cores = [c.strip().upper() for c in cores.split(",") if c.strip()]

    try:
        lista_qtd = [int(q.strip()) for q in quantidades.split(",") if q.strip()]
    except:
        st.error("Quantidade inválida.")
        st.stop()

    if any(q < 0 for q in lista_qtd):
        st.error("Quantidade inválida. Não pode ser negativa.")
        st.stop()

    if not (len(lista_cod) == len(lista_cores) == len(lista_qtd)):
        st.error("Dados não batem. Verifique códigos, cores e volumes.")
        st.stop()

    for cod, cor, qtd in zip(lista_cod, lista_cores, lista_qtd):
        cursor.execute("""
            SELECT id FROM estoque
            WHERE Referencia = ? AND CodCor = ?
        """, (referencia, cod))

        existe = cursor.fetchone()

        if existe:
            cursor.execute("""
                UPDATE estoque
                SET Cor = ?, Quantidade = ?, CompraRealizada = 0
                WHERE Referencia = ? AND CodCor = ?
            """, (cor, int(qtd), referencia, cod))
        else:
            cursor.execute("""
                INSERT INTO estoque (Referencia, CodCor, Cor, Quantidade, CompraRealizada)
                VALUES (?, ?, ?, ?, 0)
            """, (referencia, cod, cor, int(qtd)))

    conn.commit()
    st.success("Estoque atualizado com sucesso!")
    st.rerun()

st.divider()

# ================= EXCLUIR =================
st.markdown("<h2 style='text-align: center;'>Excluir Item</h2>", unsafe_allow_html=True)

ref_del = st.text_input("Referência", key="del_ref")
cod_del = st.text_input("Código da Cor", key="del_cod")

if st.button("Excluir", use_container_width=True):
    ref_del = normalizar_texto(ref_del)
    cod_del = normalizar_texto(cod_del)

    if not ref_del or not cod_del:
        st.warning("Preencha a referência e o código da cor.")
    else:
        cursor.execute("""
            DELETE FROM estoque
            WHERE Referencia = ? AND CodCor = ?
        """, (ref_del, cod_del))

        conn.commit()

        if cursor.rowcount > 0:
            st.success("Item excluído com sucesso!")
        else:
            st.warning("Nenhum item encontrado com essa referência e código.")

        st.rerun()
