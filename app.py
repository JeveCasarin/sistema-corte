import streamlit as st
import pandas as pd
import sqlite3

# ================= CONEXÃO =================
def conectar():
    return sqlite3.connect("estoque.db", check_same_thread=False)

conn = conectar()
cursor = conn.cursor()

# ================= TABELA =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS estoque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Referencia TEXT,
    CodCor TEXT,
    Cor TEXT,
    Quantidade INTEGER,
    CompraRealizada INTEGER
)
""")
conn.commit()

st.markdown("<h1 style='text-align: center;'>Sistema de Corte</h1>", unsafe_allow_html=True)

# ================= ALERTA =================
st.markdown("<h2 style='color:red; text-align: center;'>⚠️ ALERTA DE COMPRA</h2>", unsafe_allow_html=True)

df_alerta = pd.read_sql("SELECT * FROM estoque", conn)

alerta = df_alerta[
    (df_alerta["Quantidade"] <= 2) &
    (df_alerta["CompraRealizada"] == 0)
]

if not alerta.empty:
    st.warning("⚠️ Fazer pedido desses itens AGORA")

    col1, col2, col3, col4, col5 = st.columns([2,2,2,1,2])

    col1.markdown("**Referencia**")
    col2.markdown("**CodCor**")
    col3.markdown("**Cor**")
    col4.markdown("**Qtd**")
    col5.markdown("**Ação**")

    for _, row in alerta.iterrows():
        col1, col2, col3, col4, col5 = st.columns([2,2,2,1,2])

        col1.write(row["Referencia"])
        col2.write(row["CodCor"])
        col3.write(row["Cor"])
        col4.write(row["Quantidade"])

        if col5.button("OC Realizada", key=f"buy_{row['id']}"):
            cursor.execute("""
            UPDATE estoque
            SET CompraRealizada = 1
            WHERE id = ?
            """, (row["id"],))
            conn.commit()
            st.rerun()

    if st.button("✔️ Marcar todos como comprados"):
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
# ================= BUSCA =================
busca = st.text_input("🔎 Buscar por Referência")

if busca:
    df = df[
        df["Referencia"].astype(str).str.contains(busca, case=False) |
        df["Cor"].astype(str).str.contains(busca, case=False)
    ]
    
st.divider()

col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,1,2,2])

col1.markdown("**Referencia**")
col2.markdown("**CodCor**")
col3.markdown("**Cor**")
col4.markdown("**Qtd**")
col5.markdown("**Status**")
col6.markdown("**Atualizar**")
    
for _, row in df.iterrows():
    col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,1,2,2])

    col1.write(row["Referencia"])
    col2.write(row["CodCor"])
    col3.write(row["Cor"])
    col4.write(row["Quantidade"])

    # STATUS
    if row["Quantidade"] <= 2:
        if row["CompraRealizada"] == 1:
            col5.markdown("🟡 OC REALIZADA")
        else:
            col5.markdown("🔴 FAZER OC")
    else:
        col5.markdown("🟢 OK")

    # ATUALIZAR QTD
    nova_qtd = col6.number_input(
        "",
        min_value=0,
        max_value=99,
        value=int(row["Quantidade"]),
        key=f"qtd_{row['id']}",
        label_visibility="collapsed"
    )
    col_btn, col_input = col6.columns([1,1])

    with col_input:
        nova_qtd = st.number_input(
            "",
            min_value=0,
            max_value=99,
            value=int(row["Quantidade"]),
            key=f"qtd_{row['id']}",
            label_visibility="collapsed"
        )
    
    with col_btn:
        salvar = st.button("✔", key=f"save_{row['id']}")
    
    if salvar:
        cursor.execute("""
        UPDATE estoque
        SET Quantidade = ?, CompraRealizada = 0
        WHERE id = ?
        """, (nova_qtd, row["id"]))
    
        conn.commit()
        st.rerun()
            
# 🔥 ADICIONA AQUI
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
