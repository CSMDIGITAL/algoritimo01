from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import random

# =========================
# PALETA "SMART FIT"
# =========================
SF_BLACK   = "#0B0B0B"
SF_DARK    = "#141414"
SF_TEXT    = "#F2F2F2"
SF_YELLOW  = "#FFD400"
SF_YELLOW2 = "#FFB800"
SF_GRAY    = "#2A2A2A"

st.set_page_config(page_title="IMC • Academia", page_icon="🏋️", layout="wide")

# ---- CSS
st.markdown(
    f"""
    <style>
        .stApp {{ background: linear-gradient(180deg, {SF_BLACK} 0%, {SF_DARK} 100%); color:{SF_TEXT}; }}
        .stButton>button {{
            background:{SF_YELLOW}; color:#000; font-weight:800; border:0; border-radius:10px; padding:.6rem 1rem;
            box-shadow:0 6px 20px rgba(255,212,0,.35);
        }}
        .stButton>button:hover {{ background:{SF_YELLOW2}; transform: translateY(-1px); }}
        .stMetric {{ background:{SF_GRAY}; border-radius:14px; padding:12px; }}
        section[data-testid="stSidebar"] {{ background:#000; border-right:1px solid {SF_GRAY}; }}
        h1,h2,h3 {{ color:{SF_YELLOW}; text-transform:uppercase; letter-spacing:.5px; }}
        .highlight {{ background:{SF_YELLOW}; color:#000; padding:.15rem .45rem; border-radius:.35rem; font-weight:900; }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# Cabeçalho
# =========================
st.markdown("## 🏋️ IMC • <span class='highlight'>ACADEMIA</span>", unsafe_allow_html=True)
st.caption("Calcule IMC individualmente, gere dados de demonstração ou processe via CSV — com filtros por sexo, idade, categoria e **raça/cor**.")

# =========================
# Funções de IMC
# =========================
def classificar_imc(imc: float) -> str:
    if pd.isna(imc): return "—"
    if imc < 18.5:   return "Abaixo do peso"
    if imc < 25:     return "Peso normal"
    if imc < 30:     return "Sobrepeso"
    if imc < 35:     return "Obesidade I"
    if imc < 40:     return "Obesidade II"
    return "Obesidade III"

def calcula_imc(peso_kg: float, altura_m: float) -> float:
    return round(peso_kg / (altura_m ** 2), 2) if altura_m and altura_m > 0 else np.nan

def montar_kpis(df: pd.DataFrame):
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Pessoas", len(df) if not df.empty else 0)
    with col2: st.metric("IMC médio", f"{df['IMC'].mean():.2f}" if not df.empty else "—")
    with col3:
        pct = (df['Categoria'].isin(["Sobrepeso","Obesidade I","Obesidade II","Obesidade III"]).mean()*100) if not df.empty else 0
        st.metric("% Sobrepeso/Obesidade", f"{pct:.0f}%")
    with col4: st.metric("Peso médio (kg)", f"{df['peso_kg'].mean():.1f}" if 'peso_kg' in df and not df.empty else "—")

# =========================
# Gerador de dados DEMO (30 nomes + raca_cor)
# =========================
NOMES = [
    "Ana Silva","Bruno Souza","Carla Fernandes","Diego Santos","Eduarda Lima",
    "Felipe Alves","Gabriela Rocha","Henrique Moreira","Isabela Martins","João Pedro",
    "Karina Oliveira","Lucas Pereira","Mariana Costa","Natan Ribeiro","Olívia Nunes",
    "Paulo Sérgio","Quésia Dias","Rafael Cardoso","Sabrina Melo","Tiago Azevedo",
    "Úrsula Pinto","Victor Hugo","Wesley Freitas","Xênia Barbosa","Yasmin Duarte",
    "Zeca Andrade","Bianca Torres","Caio Menezes","Dennis Oliveira","Elisa Castro"
]
RACAS = ["Branca", "Parda", "Preta", "Amarela", "Indígena"]

def gerar_dados_demo(qtd: int = 30, seed: int | None = 42) -> pd.DataFrame:
    if seed is not None:
        np.random.seed(seed); random.seed(seed)

    nomes = NOMES[:qtd] if qtd <= len(NOMES) else random.choices(NOMES, k=qtd)
    sexos = np.random.choice(["Feminino","Masculino"], size=qtd)
    idades = np.clip(np.random.normal(32, 9, size=qtd).round().astype(int), 16, 65)

    # Altura média por sexo (realista)
    alturas = []
    for s in sexos:
        media = 1.73 if s == "Masculino" else 1.62
        alturas.append(np.clip(np.random.normal(media, 0.07), 1.48, 2.05))
    alturas = np.array(alturas).round(2)

    # Peso correlacionado com altura + ruído
    pesos = (alturas * 100 * 0.45 + np.random.normal(0, 8, size=qtd) + 55).clip(45, 140).round(1)

    # Raça/cor distribuída aleatoriamente
    raca_cor = np.random.choice(RACAS, size=qtd, p=[0.42, 0.43, 0.12, 0.02, 0.01])  # proporção aproximada

    df = pd.DataFrame({
        "nome": nomes,
        "sexo": sexos,
        "idade": idades,
        "altura_m": alturas,
        "peso_kg": pesos,
        "raca_cor": raca_cor
    })
    df["IMC"] = np.vectorize(calcula_imc)(df["peso_kg"], df["altura_m"])
    df["Categoria"] = df["IMC"].apply(classificar_imc)
    return df

# =========================================
# DASH DE GRÁFICOS
# =========================================
def dashboard_graficos(df: pd.DataFrame):
    if df.empty:
        st.info("Carregue um CSV, gere dados de demonstração ou use a calculadora para ver os gráficos.")
        return

    st.markdown("## 📊 Visualizações avançadas")

    # Filtros
    colf1, colf2, colf3, colf4 = st.columns(4)
    with colf1:
        faixa_idade = st.slider("Idade (mín–máx)", 0, 100, (0, 100))
    with colf2:
        sexo_sel = "Todos"
        if "sexo" in df.columns:
            sexos = ["Todos"] + sorted([s for s in df["sexo"].dropna().astype(str).unique()])
            sexo_sel = st.selectbox("Sexo", sexos, index=0)
    with colf3:
        cat_opts = ["Todos"] + ["Abaixo do peso","Peso normal","Sobrepeso","Obesidade I","Obesidade II","Obesidade III"]
        cat_sel = st.selectbox("Categoria IMC", cat_opts, index=0)
    with colf4:
        raca_sel = "Todos"
        if "raca_cor" in df.columns:
            racas = ["Todos"] + list(RACAS)
            raca_sel = st.selectbox("Raça/Cor", racas, index=0)

    df_plot = df.copy()
    if "idade" in df_plot.columns:
        df_plot = df_plot[(df_plot["idade"].fillna(0) >= faixa_idade[0]) & (df_plot["idade"].fillna(0) <= faixa_idade[1])]
    if sexo_sel != "Todos" and "sexo" in df_plot.columns:
        df_plot = df_plot[df_plot["sexo"].astype(str) == sexo_sel]
    if cat_sel != "Todos" and "Categoria" in df_plot.columns:
        df_plot = df_plot[df_plot["Categoria"] == cat_sel]
    if raca_sel != "Todos" and "raca_cor" in df_plot.columns:
        df_plot = df_plot[df_plot["raca_cor"] == raca_sel]

    if df_plot.empty:
        st.warning("Nenhum dado após filtros.")
        return

    montar_kpis(df_plot)

    # 1) Histograma IMC + faixas
    st.markdown("### 1) Distribuição do IMC (com faixas)")
    bins = st.slider("Número de bins", 5, 50, 20, key="bins_hist")

    base_hist = alt.Chart(df_plot)
    hist = (
        base_hist.transform_bin("bin_imc", field="IMC", bin=alt.Bin(maxbins=bins))
        .transform_aggregate(count="count()", groupby=["bin_imc"])
        .mark_bar(color=SF_YELLOW)
        .encode(
            x=alt.X("bin_imc:Q", title="IMC", axis=alt.Axis(labelColor=SF_TEXT, titleColor=SF_TEXT)),
            y=alt.Y("count:Q", title="Pessoas", axis=alt.Axis(labelColor=SF_TEXT, titleColor=SF_TEXT)),
            tooltip=["bin_imc:Q","count:Q"],
        ).properties(height=280)
    )
    rules = alt.Chart(pd.DataFrame({"x":[18.5,25,30,35,40]})).mark_rule(
        color=SF_YELLOW2, strokeDash=[4,4]
    ).encode(x="x:Q")
    st.altair_chart((hist + rules).properties(background=SF_DARK), use_container_width=True)

    # 2) Donut por Categoria
    st.markdown("### 2) Composição por Categoria (donut)")
    cat_counts = df_plot["Categoria"].value_counts(dropna=False).rename_axis("Categoria").reset_index(name="Qtd")
    donut = (
        alt.Chart(cat_counts)
        .mark_arc(innerRadius=70)
        .encode(
            theta="Qtd:Q",
            color=alt.Color(
                "Categoria:N",
                scale=alt.Scale(range=[SF_YELLOW, "#FFF06A", "#FFC700", "#FF9F00", "#FF6D00", "#FF3B00"]),
                legend=alt.Legend(labelColor=SF_TEXT, titleColor=SF_TEXT),
            ),
            tooltip=["Categoria","Qtd"]
        )
        .properties(height=320, background=SF_DARK)
    )
    st.altair_chart(donut, use_container_width=True)

    # 3) Barras por Raça/Cor
    if "raca_cor" in df_plot.columns:
        st.markdown("### 3) Distribuição por Raça/Cor")
        raca_counts = df_plot["raca_cor"].value_counts().reindex(RACAS, fill_value=0).rename_axis("raça/cor").reset_index(name="Qtd")
        barras_raca = (
            alt.Chart(raca_counts)
            .mark_bar()
            .encode(
                x=alt.X("raça/cor:N", axis=alt.Axis(labelColor=SF_TEXT, titleColor=SF_TEXT)),
                y=alt.Y("Qtd:Q", axis=alt.Axis(labelColor=SF_TEXT, titleColor=SF_TEXT)),
                color=alt.value(SF_YELLOW),
                tooltip=["raça/cor","Qtd"]
            ).properties(height=300, background=SF_DARK)
        )
        st.altair_chart(barras_raca, use_container_width=True)

    # 4) Dispersão altura x peso + regressão
    st.markdown("### 4) Altura × Peso com tendência")
    if {"altura_m","peso_kg"}.issubset(df_plot.columns):
        base = alt.Chart(df_plot)
        color_encoding = alt.Color("raca_cor:N", legend=alt.Legend(labelColor=SF_TEXT, titleColor=SF_TEXT)) if "raca_cor" in df_plot.columns else alt.value(SF_YELLOW)
        pts = base.mark_circle(size=85, opacity=0.85).encode(
            x=alt.X("altura_m:Q", title="Altura (m)", axis=alt.Axis(labelColor=SF_TEXT, titleColor=SF_TEXT)),
            y=alt.Y("peso_kg:Q", title="Peso (kg)", axis=alt.Axis(labelColor=SF_TEXT, titleColor=SF_TEXT)),
            color=color_encoding,
            tooltip=["nome","sexo","raca_cor","idade","altura_m","peso_kg","IMC","Categoria"]
        ).properties(height=360)
        reg = base.transform_regression("altura_m", "peso_kg").mark_line(color="#FFFFFF")
        st.altair_chart((pts + reg).properties(background=SF_DARK), use_container_width=True)
    else:
        st.info("Para esta visualização, inclua as colunas altura_m e peso_kg.")

    # 5) Boxplot IMC por sexo
    st.markdown("### 5) IMC por sexo (boxplot)")
    if "sexo" in df_plot.columns:
        box = (
            alt.Chart(df_plot)
            .mark_boxplot(color=SF_YELLOW)
            .encode(
                x=alt.X("sexo:N", axis=alt.Axis(labelColor=SF_TEXT, titleColor=SF_TEXT)),
                y=alt.Y("IMC:Q", axis=alt.Axis(labelColor=SF_TEXT, titleColor=SF_TEXT)),
                tooltip=["sexo","IMC"]
            )
            .properties(height=320, background=SF_DARK)
        )
        st.altair_chart(box, use_container_width=True)
    else:
        st.info("Adicione a coluna 'sexo' para ver o boxplot.")

# =========================
# Sidebar — Calculadora Rápida (individual)
# =========================
st.sidebar.header("⚙️ Calculadora Rápida")
nome  = st.sidebar.text_input("Nome", "")
sexo  = st.sidebar.selectbox("Sexo", ["Não informado", "Feminino", "Masculino", "Outro"], index=0)
raca  = st.sidebar.selectbox("Raça/Cor", RACAS, index=1)  # default Parda
idade = st.sidebar.number_input("Idade", 0, 120, 30, 1)
altura = st.sidebar.number_input("Altura (m)", 0.5, 2.5, 1.70, 0.01, format="%.2f")
peso   = st.sidebar.number_input("Peso (kg)", 10.0, 350.0, 70.0, 0.1, format="%.1f")

if "historico" not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=["nome","sexo","raca_cor","idade","altura_m","peso_kg","IMC","Categoria"])

if st.sidebar.button("Calcular IMC ✅", use_container_width=True):
    imc_val = calcula_imc(peso, altura)
    cat = classificar_imc(imc_val)
    st.sidebar.success(f"IMC: {imc_val} • {cat}")
    novo = pd.DataFrame([{
        "nome":nome,"sexo":sexo,"raca_cor":raca,"idade":idade,
        "altura_m":altura,"peso_kg":peso,"IMC":imc_val,"Categoria":cat
    }])
    st.session_state.historico = pd.concat([st.session_state.historico, novo], ignore_index=True)

if not st.session_state.historico.empty:
    with st.expander("📒 Histórico (sessão)"):
        st.dataframe(st.session_state.historico, use_container_width=True)
        st.download_button("⬇️ Baixar histórico (CSV)",
                           data=st.session_state.historico.to_csv(index=False).encode("utf-8"),
                           file_name="historico_imc.csv", mime="text/csv")

# =========================
# Lote por CSV + DEMO
# =========================
st.subheader("📥 Lote por CSV (ou gere um conjunto DEMO)")

col_demo = st.columns(2)
with col_demo[0]:
    arquivo = st.file_uploader("CSV com: nome,sexo,idade,altura_m,peso_kg[,raca_cor]", type="csv")
with col_demo[1]:
    seed = st.number_input("Seed (reprodutível)", value=42, step=1)
    gerar_btn = st.button("✨ Gerar dados de demonstração (30)")

df_lote = pd.DataFrame()

# DEMO:
if gerar_btn:
    df_lote = gerar_dados_demo(30, seed=int(seed))
    st.success("Dados de demonstração gerados!")
    st.dataframe(df_lote, use_container_width=True)
    montar_kpis(df_lote)
    st.download_button("⬇️ Baixar DEMO (CSV)",
                       data=df_lote.to_csv(index=False).encode("utf-8"),
                       file_name="demo_imc_30.csv", mime="text/csv")

# CSV:
elif arquivo is not None:
    try:
        df_lote = pd.read_csv(arquivo)
        df_lote.columns = [c.strip().lower() for c in df_lote.columns]
        # Normaliza nome da coluna raca_cor se vier 'raça' etc.
        if "raca" in df_lote.columns and "raca_cor" not in df_lote.columns:
            df_lote.rename(columns={"raca":"raca_cor"}, inplace=True)

        req = {"altura_m","peso_kg"}
        if not req.issubset(df_lote.columns):
            st.error("CSV inválido. Precisa ter: altura_m, peso_kg. (Opcional: nome, sexo, idade, raca_cor)")
        else:
            df_lote["IMC"] = np.vectorize(calcula_imc)(df_lote["peso_kg"], df_lote["altura_m"])
            df_lote["Categoria"] = df_lote["IMC"].apply(classificar_imc)
            st.success("CSV processado!")
            st.dataframe(df_lote, use_container_width=True)
            montar_kpis(df_lote)
            st.download_button("⬇️ Baixar resultados (CSV)",
                               data=df_lote.to_csv(index=False).encode("utf-8"),
                               file_name="resultado_imc.csv", mime="text/csv")
    except Exception as e:
        st.error(f"Erro ao ler/processar o CSV: {e}")

# =========================
# Gráficos (prioriza CSV/DEMO, senão histórico)
# =========================
if not df_lote.empty:
    dashboard_graficos(df_lote)
elif not st.session_state.historico.empty:
    dashboard_graficos(st.session_state.historico)

# =========================
# Observações
# =========================
with st.expander("ℹ️ Observações"):
    st.write("- IMC = peso (kg) ÷ altura² (m). Classificação para **adultos**. Não substitui avaliação clínica.")
