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

col1, col2, col3, col4, col5 = st.columns([2,2,2,1,2])

col1.markdown("**Referencia**")
col2.markdown("**CodCor**")
col3.markdown("**Cor**")
col4.markdown("**Qtd**")
col5.markdown("**Status**")

for _, row in df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([2,2,2,1,2])

    col1.write(row["Referencia"])
    col2.write(row["CodCor"])
    col3.write(row["Cor"])
    col4.write(row["Quantidade"])

    if row["CompraRealizada"] == 1:
        col5.markdown("✅ Comprado")
    else:
        col5.markdown("❌ Pendente")

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
