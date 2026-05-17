import streamlit as st
import pandas as pd
from pathlib import Path
import unicodedata


def normalize_name(name: str) -> str:
    txt = unicodedata.normalize("NFKD", str(name))
    txt = txt.encode("ascii", "ignore").decode("ascii")
    return txt.strip().lower()


def find_column(df: pd.DataFrame, target: str) -> str:
    target_norm = normalize_name(target)
    for col in df.columns:
        if normalize_name(col) == target_norm:
            return col
    raise ValueError(f"Colonne introuvable: {target}")


st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 16px;
    }
    .story-lead {
        font-size: 1.05rem;
        line-height: 1.65;
        color: #334155;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

data_file = Path(__file__).resolve().parents[1] / "data" / "dataset_ventes_magasin.xlsx"
df_raw = pd.read_excel(data_file)

date_col = find_column(df_raw, "Date de vente")
qte_col = find_column(df_raw, "Quantite vendue")
prix_col = find_column(df_raw, "Prix unitaire")
canal_col = find_column(df_raw, "Canal de vente")
client_col = find_column(df_raw, "Client")
ville_col = find_column(df_raw, "Ville")

df_raw[date_col] = pd.to_datetime(df_raw[date_col], errors="coerce")
df_raw = df_raw.dropna(subset=[date_col]).copy()
df_raw["CA"] = df_raw[qte_col] * df_raw[prix_col]
df_raw["Mois"] = df_raw[date_col].dt.to_period("M").astype(str)

with st.sidebar:
    st.markdown("### Filtres")
    st.caption("Affinez l’analyse pour votre argumentaire oral.")
    villes = ["Toutes les villes"] + sorted(
        df_raw[ville_col].dropna().astype(str).unique().tolist()
    )
    ville_selectionnee = st.selectbox("Ville", villes)
    st.divider()
    st.caption(
        "Les graphiques et indicateurs se mettent à jour automatiquement."
    )

if ville_selectionnee != "Toutes les villes":
    df = df_raw[df_raw[ville_col].astype(str) == ville_selectionnee].copy()
else:
    df = df_raw.copy()

st.title("Habitudes d’achat")
if df.empty:
    st.warning("Aucune transaction pour cette sélection. Choisissez une autre ville.")
    st.stop()

st.markdown(
    '<p class="story-lead">Cette page répond à une question simple : '
    "<strong>comment et quand les clients achètent-ils ?</strong> "
    "Elle structure votre storytelling en trois temps : le canal, le rythme dans le temps, "
    "puis les clients les plus engagés.</p>",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Transactions", f"{len(df):,}".replace(",", " "))
with c2:
    st.metric("Chiffre d’affaires", f"{df['CA'].sum():,.0f} €".replace(",", " "))
with c3:
    st.metric("Clients distincts", f"{df[client_col].nunique():,}".replace(",", " "))
with c4:
    st.metric(
        "Panier moyen (CA / achat)",
        f"{df['CA'].mean():,.0f} €".replace(",", " ") if len(df) else "—",
    )

st.divider()

st.markdown("#### 1 · Par quel canal les clients préfèrent-ils acheter ?")
col_chart, col_txt = st.columns([1.1, 1])
with col_chart:
    canal_count = df[canal_col].value_counts()
    st.bar_chart(canal_count)
with col_txt:
    if not canal_count.empty:
        top_canal = canal_count.index[0]
        part = 100 * canal_count.iloc[0] / canal_count.sum()
        st.markdown(
            f"**Lecture :** le canal **{top_canal}** concentre environ "
            f"**{part:.0f} %** des transactions sur la sélection actuelle."
        )
        st.markdown(
            "_À l’oral : expliquez pourquoi ce canal peut refléter des habitudes "
            "(confort, confiance, urgence, etc.)._"
        )
    else:
        st.info("Pas de données pour cette sélection.")

st.divider()

st.markdown("#### 2 · Le rythme des achats dans le temps")
ca_mensuel = df.groupby("Mois", as_index=True)["CA"].sum().sort_index()
st.line_chart(ca_mensuel)
st.markdown(
    "**Lecture :** repérez les mois en surperformance ou en creux pour relier "
    "éventuellement à une saisonnalité ou à des campagnes."
)
st.caption(
    "À l’oral : annoncez 1–2 pics ou baisses marquants et proposez une hypothèse prudente "
    "(sans affirmer une cause si les données ne la contiennent pas)."
)

st.divider()

st.markdown("#### 3 · Qui achète le plus souvent et génère le plus de CA ?")
top_clients = (
    df.groupby(client_col, as_index=False)
    .agg(
        nb_achats=(client_col, "count"),
        quantite_totale=(qte_col, "sum"),
        ca_total=("CA", "sum"),
    )
    .sort_values(["nb_achats", "ca_total"], ascending=False)
    .head(10)
)
st.dataframe(
    top_clients.rename(
        columns={
            client_col: "Client",
            "nb_achats": "Nb d’achats",
            "quantite_totale": "Quantité totale",
            "ca_total": "CA total (€)",
        }
    ),
    use_container_width=True,
    hide_index=True,
)
st.markdown(
    "**Lecture :** distinguez la **fréquence** (nombre d’achats) du **volume économique** (CA). "
    "Un client peut acheter souvent sans être le plus rentable, et inversement."
)

st.divider()

st.markdown("#### Synthèse")
canal_top = canal_count.index[0] if not canal_count.empty else "—"
st.success(
    f"Sur cette vue, le canal dominant est **{canal_top}**."
)
