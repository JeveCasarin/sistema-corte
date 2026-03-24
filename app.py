import streamlit as st
import pandas as pd
import os
import shutil

# ================= CAMINHOS =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ESTOQUE = os.path.join(BASE_DIR, "estoque.xlsx")
CAMINHO_ALERTA = os.path.join(BASE_DIR, "ALERTA_COMPRA.xlsx")

st.markdown("<h1 style='text-align: center;'>Sistema de Corte</h1>", unsafe_allow_html=True)

# ================= ALERTA =================
st.markdown("<h2 style='color:red; text-align: center;'>⚠️ ALERTA DE COMPRA</h2>", unsafe_allow_html=True)

if os.path.exists(CAMINHO_ESTOQUE):
    df_alerta = pd.read_excel(CAMINHO_ESTOQUE)

    if "CompraRealizada" not in df_alerta.columns:
        df_alerta["CompraRealizada"] = False

    df_alerta["Quantidade"] = pd.to_numeric(df_alerta["Quantidade"], errors="coerce")

    alerta = df_alerta[
        (df_alerta["Quantidade"] <= 2) &
        (df_alerta["CompraRealizada"] == False)
    ]

    if not alerta.empty:
        st.warning("⚠️ Fazer pedido desses itens AGORA")

        col1, col2, col3, col4, col5 = st.columns([2,2,2,1,2])

        col1.markdown("**Referencia**")
        col2.markdown("**CodCor**")
        col3.markdown("**Cor**")
        col4.markdown("**Qtd**")
        col5.markdown("**Ação**")
                
        for i, row in alerta.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2,2,2,1,2])
        
            col1.write(row["Referencia"])
            col2.write(row["CodCor"])
            col3.write(row["Cor"])
            col4.write(row["Quantidade"])
        
            if col5.button("Comprar", key=f"buy_{i}"):
                df_alerta.loc[i, "CompraRealizada"] = True
                df_alerta.to_excel(CAMINHO_ESTOQUE, index=False)
                st.rerun()
                
        if st.button("✔️ Marcar todos como comprados"):
            df_alerta.loc[
                (df_alerta["Quantidade"] <= 2) &
                (df_alerta["CompraRealizada"] == False),
                "CompraRealizada"
            ] = True

            df_alerta.to_excel(CAMINHO_ESTOQUE, index=False)
            st.success("Atualizado!")
            st.rerun()

        alerta.to_excel(CAMINHO_ALERTA, index=False)

    else:
        st.success("Estoque saudável 👍")

    st.divider()

# ================= LISTA =================
st.markdown("<h3 style='text-align: center;'>📦 Estoque Atual</h3>", unsafe_allow_html=True)

if os.path.exists(CAMINHO_ESTOQUE):
    df = pd.read_excel(CAMINHO_ESTOQUE)

    if "CompraRealizada" not in df.columns:
        df["CompraRealizada"] = False

    st.dataframe(df)

    with open(CAMINHO_ESTOQUE, "rb") as file:
        st.download_button("📥 Baixar Backup", file, "estoque_backup.xlsx")

else:
    st.info("Nenhum estoque cadastrado")

# ================= RESTAURAR BACKUP =================
st.markdown("<h3 style='text-align: center;'>### 🔄 Restaurar Backup</h3>", unsafe_allow_html=True)

arquivo_backup = st.file_uploader("Enviar arquivo .xlsx", type=["xlsx"])

if arquivo_backup is not None:
    if st.button("Restaurar Backup"):
        df_backup = pd.read_excel(arquivo_backup)

        colunas = ["Referencia", "CodCor", "Cor", "Quantidade"]

        if not all(col in df_backup.columns for col in colunas):
            st.error("Arquivo inválido")
        else:
            if "CompraRealizada" not in df_backup.columns:
                df_backup["CompraRealizada"] = False

            df_backup.to_excel(CAMINHO_ESTOQUE, index=False)

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

    if os.path.exists(CAMINHO_ESTOQUE):
        df = pd.read_excel(CAMINHO_ESTOQUE)
    else:
        df = pd.DataFrame(columns=["Referencia", "CodCor", "Cor", "Quantidade", "CompraRealizada"])

    if "CompraRealizada" not in df.columns:
        df["CompraRealizada"] = False

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

            filtro = (
                (df["Referencia"] == referencia) &
                (df["CodCor"] == cod)
            )

            if not df[filtro].empty:
                df.loc[filtro, "Quantidade"] = qtd
                df.loc[filtro, "CompraRealizada"] = False
            else:
                novo = pd.DataFrame({
                    "Referencia": [referencia],
                    "CodCor": [cod],
                    "Cor": [cor],
                    "Quantidade": [qtd],
                    "CompraRealizada": [False]
                })
                df = pd.concat([df, novo], ignore_index=True)

        df.to_excel(CAMINHO_ESTOQUE, index=False)

        # 🔥 backup automático
        shutil.copy(CAMINHO_ESTOQUE, os.path.join(BASE_DIR, "backup_estoque.xlsx"))

        st.success("Estoque atualizado!")
        st.rerun()
    st.divider()
# ================= EXCLUIR =================
st.markdown("<h2 style='text-align: center;'>Excluir Item</h2>", unsafe_allow_html=True)

ref_del = st.text_input("Referência", key="del_ref")
cod_del = st.text_input("Código da Cor", key="del_cod")

if st.button("Excluir"):
    if os.path.exists(CAMINHO_ESTOQUE):
        df = pd.read_excel(CAMINHO_ESTOQUE)

        antes = len(df)

        df = df[~(
            (df["Referencia"].astype(str).str.strip() == ref_del.strip()) &
            (df["CodCor"].astype(str).str.strip() == cod_del.strip())
        )]

        df.to_excel(CAMINHO_ESTOQUE, index=False)

        if len(df) == antes:
            st.warning("Item não encontrado")
        else:
            st.success("Excluído!")
            st.rerun()
