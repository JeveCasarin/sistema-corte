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
        st.warning("Itens com estoque baixo!")

        alerta = alerta.sort_values(by="Quantidade")

        def cor_linha(row):
            if row["CompraRealizada"]:
                return ["background-color: #2ecc71; color: white"] * len(row)
            if row["Quantidade"] == 0:
                return ["background-color: red; color: white"] * len(row)
            elif row["Quantidade"] == 1:
                return ["background-color: orange"] * len(row)
            elif row["Quantidade"] == 2:
                return ["background-color: yellow"] * len(row)
            return [""] * len(row)

        # 🔥 estilo no original
        styled = alerta.style.apply(cor_linha, axis=1)

        st.dataframe(styled)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("✔️ Todas ordens de compra feitas"):
                df = pd.read_excel(CAMINHO_ESTOQUE)

                if "CompraRealizada" not in df.columns:
                    df["CompraRealizada"] = False

                filtro = (
                    (df["Quantidade"] <= 2) &
                    (df["CompraRealizada"] == False)
                )

                df.loc[filtro, "CompraRealizada"] = True
                df.to_excel(CAMINHO_ESTOQUE, index=False)

                st.success("Todos marcados como comprados!")
                st.rerun()

        alerta.to_excel(CAMINHO_ALERTA, index=False)
    else:
        st.success("Estoque saudável 👍")

# ================= CADASTRO =================
st.markdown("<h2 style='text-align: center;'>Cadastro de Estoque</h2>", unsafe_allow_html=True)

referencia = st.text_input("Referência")
cod_cores = st.text_input("Códigos das Cores")
cores = st.text_input("Cores")
quantidades = st.text_input("Volumes")

if st.button("Adicionar/Atualizar Estoque"):

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
    lista_qtd = [int(q.strip()) for q in quantidades.split(",")]

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
        shutil.copy(CAMINHO_ESTOQUE, os.path.join(BASE_DIR, "backup_estoque.xlsx"))

        st.success("Estoque atualizado!")
        st.rerun()

# ================= LISTA =================
st.markdown("<h3 style='text-align: center;'>📦 Estoque Atual</h3>", unsafe_allow_html=True)

if os.path.exists(CAMINHO_ESTOQUE):
    df = pd.read_excel(CAMINHO_ESTOQUE)

    df["Referencia"] = df["Referencia"].astype(str).str.strip()
    df["CodCor"] = df["CodCor"].astype(str).str.strip()

    df = df.sort_values(by=["Referencia", "CodCor"])

    df_view = df.copy()
    df_view.rename(columns={"CompraRealizada": "OC REALIZADA"}, inplace=True)

    st.dataframe(df_view)

    with open(CAMINHO_ESTOQUE, "rb") as file:
        st.download_button("📥 Baixar Backup", file, "estoque_backup.xlsx")

else:
    st.info("Nenhum estoque cadastrado")

# ================= RESTAURAR =================
st.markdown("### 🔄 Restaurar Backup")

arquivo_backup = st.file_uploader("Enviar backup", type=["xlsx"])

if arquivo_backup is not None:
    if st.button("Restaurar"):
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
