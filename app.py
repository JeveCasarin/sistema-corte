import streamlit as st
import pandas as pd
import os

# ================= CAMINHOS =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ESTOQUE = os.path.join(BASE_DIR, "estoque.xlsx")
CAMINHO_PEDIDOS = os.path.join(BASE_DIR, "pedidos.xlsx")
CAMINHO_ALERTA = os.path.join(BASE_DIR, "ALERTA_COMPRA.xlsx")

st.markdown("<h1 style='text-align: center;'>Sistema de Corte</h1>", unsafe_allow_html=True)

# ================= ALERTA DE COMPRA =================
st.markdown("<h2 style='color:red; text-align: center;'>⚠️ ALERTA DE COMPRA</h2>", unsafe_allow_html=True)

CAMINHO_ALERTA = os.path.join(BASE_DIR, "ALERTA_COMPRA.xlsx")

if os.path.exists(CAMINHO_ESTOQUE):
    df_alerta = pd.read_excel(CAMINHO_ESTOQUE)

    # garante que quantidade é número
    df_alerta["Quantidade"] = pd.to_numeric(df_alerta["Quantidade"], errors="coerce")

    # 🔥 FILTRO PRINCIPAL
    alerta = df_alerta[df_alerta["Quantidade"] <= 2]

    if not alerta.empty:
        st.warning("Itens com estoque baixo!")
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

    st.success("Todos os itens marcados como comprados!")
    st.rerun()

        # ordena
        alerta = alerta.sort_values(by="Quantidade", ascending=True)

        # 🔥 FUNÇÃO DE COR (CORRETA INDENTAÇÃO)
        def cor_linha(row):
            if row["Quantidade"] == 0:
                return ["background-color: red; color: white"] * len(row)
            elif row["Quantidade"] == 1:
                return ["background-color: orange"] * len(row)
            elif row["Quantidade"] == 2:
                return ["background-color: yellow"] * len(row)
            else:
                return [""] * len(row)

        # 🔥 APLICA COR
        st.dataframe(alerta.style.apply(cor_linha, axis=1))

        # salva alerta
        alerta.to_excel(CAMINHO_ALERTA, index=False)

    else:
        st.success("Estoque saudável 👍")
# ================= PEDIDOS =================
st.markdown("<h2 style='text-align: center;'>Cadastro de Pedido</h2>", unsafe_allow_html=True)

cliente = st.text_input("Cliente")
modelo = st.text_input("Modelo")
quantidade = st.number_input("Quantidade de Peças", min_value=1)

if st.button("Salvar Pedido"):
    novo = pd.DataFrame({
        "Cliente": [cliente],
        "Modelo": [modelo],
        "Quantidade": [quantidade]
    })

    if os.path.exists(CAMINHO_PEDIDOS):
        df = pd.read_excel(CAMINHO_PEDIDOS)
        df = pd.concat([df, novo], ignore_index=True)
    else:
        df = novo

    df.to_excel(CAMINHO_PEDIDOS, index=False)
    st.success("Pedido salvo!")

# ================= ESTOQUE =================
st.markdown("<h2 style='text-align: center;'>Cadastro de Estoque</h2>", unsafe_allow_html=True)

referencia = st.text_input("Referência")
cod_cores = st.text_input("Códigos das Cores (ex: 11053,18018)")
cores = st.text_input("Cores (ex: AREIA,CINZA)")
quantidades = st.text_input("Volumes (ex: 4,4)")

if st.button("Adicionar/Atualizar Estoque"):

    if not referencia or not cod_cores or not cores or not quantidades:
        st.warning("Preencha tudo antes de salvar")
        st.stop()

    if os.path.exists(CAMINHO_ESTOQUE):
        df = pd.read_excel(CAMINHO_ESTOQUE)
    else:
        df = pd.DataFrame(columns=["Referencia", "CodCor", "Cor", "Quantidade", "CompraRealizada"])

    # garante coluna
    if "CompraRealizada" not in df.columns:
        df["CompraRealizada"] = False

    lista_cod = [c.strip() for c in cod_cores.split(",")]
    lista_cores = [c.strip() for c in cores.split(",")]
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
                df.loc[filtro, "CompraRealizada"] = False  # 🔥 reset
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
        st.success("Estoque atualizado!")
        
# ================= BAIXA NO ESTOQUE =================
st.markdown("<h2 style='text-align: center;'>Dar Baixa no Estoque</h2>", unsafe_allow_html=True)

ref_saida = st.text_input("Referência", key="saida_ref")
cod_saida = st.text_input("Código da Cor", key="saida_cod")
pecas_saida = st.number_input("Peças do Pedido", min_value=1, key="saida_pecas")

if st.button("Dar Baixa"):
    if not ref_saida or not cod_saida or not pecas_saida:
        st.warning("Preencha tudo")
        st.stop()

    if os.path.exists(CAMINHO_ESTOQUE):
        df = pd.read_excel(CAMINHO_ESTOQUE)

        df["Referencia"] = df["Referencia"].astype(str).str.strip()
        df["CodCor"] = df["CodCor"].astype(str).str.strip()

        filtro = (
            (df["Referencia"] == ref_saida.strip()) &
            (df["CodCor"] == cod_saida.strip())
        )

        if not df[filtro].empty:

            # 🔥 CONVERSÃO
            volume_usado = round(pecas_saida / 60, 2)

            estoque_atual = df.loc[filtro, "Quantidade"].values[0]
            novo_estoque = estoque_atual - volume_usado

            if novo_estoque < 0:
                st.error("Estoque insuficiente!")
            else:
                df.loc[filtro, "Quantidade"] = novo_estoque
                df.to_excel(CAMINHO_ESTOQUE, index=False)

                st.success(f"Baixa realizada! (-{volume_usado} volumes)")

        else:
            st.warning("Item não encontrado")
            
# ================= BUSCA =================
st.markdown("<h2 style='text-align: center;'>Buscar Estoque</h2>", unsafe_allow_html=True)

busca = st.text_input("Digite a referência")

if st.button("Buscar"):
    if os.path.exists(CAMINHO_ESTOQUE):
        df = pd.read_excel(CAMINHO_ESTOQUE)
        resultado = df[df["Referencia"].astype(str).str.contains(busca, case=False)]

        if resultado.empty:
            st.warning("Não encontrado")
        else:
            st.dataframe(resultado)

# ================= ALERTA DE COMPRA =================
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

        alerta = alerta.sort_values(by="Quantidade", ascending=True)

        def cor_linha(row):
            if row["Quantidade"] == 0:
                return ["background-color: red; color: white"] * len(row)
            elif row["Quantidade"] == 1:
                return ["background-color: orange"] * len(row)
            elif row["Quantidade"] == 2:
                return ["background-color: yellow"] * len(row)
            else:
                return [""] * len(row)

        st.dataframe(alerta.style.apply(cor_linha, axis=1))

        # 🔥 BOTÕES POR ITEM
        st.markdown("### ✔️ Marcar como comprado")

        for i, row in alerta.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2,2,2,2,1])

            col1.write(row["Referencia"])
            col2.write(row["CodCor"])
            col3.write(row["Cor"])
            col4.write(row["Quantidade"])

            if col5.button("OK", key=f"btn_{i}"):
                df = pd.read_excel(CAMINHO_ESTOQUE)

                filtro = (
                    (df["Referencia"] == row["Referencia"]) &
                    (df["CodCor"] == row["CodCor"])
                )

                df.loc[filtro, "CompraRealizada"] = True
                df.to_excel(CAMINHO_ESTOQUE, index=False)

                st.success(f"{row['Referencia']} - {row['CodCor']} comprado")
                st.rerun()

    else:
        st.success("Estoque saudável 👍")

# ================= EXCLUIR ITEM =================
st.markdown("<h2 style='text-align: center;'>Excluir Item</h2>", unsafe_allow_html=True)

ref_del = st.text_input("Referência", key="ref_del")
codcor_del = st.text_input("Código da Cor", key="codcor_del")

if st.button("Excluir Item"):
    if os.path.exists(CAMINHO_ESTOQUE):
        df = pd.read_excel(CAMINHO_ESTOQUE)

        df["Referencia"] = df["Referencia"].astype(str).str.strip()
        df["CodCor"] = df["CodCor"].astype(str).str.strip()

        antes = len(df)

        df = df[~(
            (df["Referencia"] == ref_del.strip()) &
            (df["CodCor"] == codcor_del.strip())
        )]

        depois = len(df)

        df.to_excel(CAMINHO_ESTOQUE, index=False)

        if antes == depois:
            st.warning("Item não encontrado")
        else:
            st.success("Item excluído com sucesso!")
            st.rerun()
