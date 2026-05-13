import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Analyse des ventes — Tableau de bord",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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


@st.cache_data
def load_sales():
    path = Path(__file__).resolve().parent / "data" / "dataset_ventes_magasin.xlsx"
    raw = pd.read_excel(path)
    mapping = {
        find_column(raw, "Date de vente"): "date_vente",
        find_column(raw, "Nom du produit"): "produit",
        find_column(raw, "Categorie"): "categorie",
        find_column(raw, "Quantite vendue"): "quantite",
        find_column(raw, "Prix unitaire"): "prix_unitaire",
        find_column(raw, "Ville"): "ville",
        find_column(raw, "Canal de vente"): "canal",
        find_column(raw, "Client"): "client",
    }
    df = raw.rename(columns=mapping)
    df["date_vente"] = pd.to_datetime(df["date_vente"], errors="coerce")
    df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce")
    df["prix_unitaire"] = pd.to_numeric(df["prix_unitaire"], errors="coerce")
    df = df.dropna(subset=["date_vente", "quantite", "prix_unitaire"]).copy()
    df["ca"] = df["quantite"] * df["prix_unitaire"]
    df["mois"] = df["date_vente"].dt.to_period("M").astype(str)
    return df


df = load_sales()

st.title("Tableau de bord — Analyse des ventes")
st.markdown(
    "**Contexte (projet DataViz).** Une entreprise multi-canaux (magasin, en ligne, téléphone) "
    "souhaite suivre ses performances sur plusieurs villes. Ce tableau de bord résume les ventes "
    "et renvoie vers les pages thématiques pour approfondir : **tendances**, **produits**, "
    "**zones géographiques**, **habitudes d’achat**."
)

with st.sidebar:
    st.markdown("### Filtres (vue d’ensemble)")
    periodes = sorted(df["mois"].unique())
    mois_debut, mois_fin = st.select_slider(
        "Période (mois)",
        options=periodes,
        value=(periodes[0], periodes[-1]),
    )
    canaux_all = sorted(df["canal"].dropna().astype(str).unique())
    canaux_sel = st.multiselect(
        "Canaux",
        options=canaux_all,
        default=canaux_all,
    )
    st.caption(
        "Les graphiques ci-dessous se mettent à jour selon ces filtres. "
        "Le menu de gauche permet d’ouvrir chaque thème sur une page dédiée, "
        "comme demandé dans le cahier des charges."
    )

if not canaux_sel:
    st.warning("Sélectionnez au moins un canal.")
    st.stop()

df_v = df[(df["mois"] >= mois_debut) & (df["mois"] <= mois_fin) & (df["canal"].isin(canaux_sel))]

if df_v.empty:
    st.warning("Aucune donnée pour cette combinaison de filtres.")
    st.stop()

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Chiffre d’affaires", f"{df_v['ca'].sum():,.0f} €".replace(",", " "))
with m2:
    st.metric("Transactions", f"{len(df_v):,}".replace(",", " "))
with m3:
    st.metric("Clients distincts", f"{df_v['client'].nunique():,}".replace(",", " "))
with m4:
    st.metric("Produits distincts", f"{df_v['produit'].nunique():,}".replace(",", " "))

st.divider()

st.subheader("Synthèse visuelle")
c_left, c_right = st.columns(2)
with c_left:
    st.markdown("**CA par canal de vente**")
    ca_canal = df_v.groupby("canal", as_index=True)["ca"].sum().sort_values(ascending=False)
    st.bar_chart(ca_canal)
    st.caption(
        "Lecture rapide : quel canal pèse le plus dans le CA sur la période et les canaux choisis."
    )
with c_right:
    st.markdown("**Top villes par CA**")
    top_villes = df_v.groupby("ville", as_index=True)["ca"].sum().sort_values(ascending=False).head(8)
    st.bar_chart(top_villes)
    st.caption(
        "Lecture rapide : quelles zones tirent le plus le chiffre d’affaires (à croiser avec la page zones)."
    )

st.markdown("**Évolution mensuelle du CA**")
ca_mois = df_v.groupby("mois", as_index=True)["ca"].sum().sort_index()
st.line_chart(ca_mois)
st.caption(
    "Tendance globale : repérer les mois forts ou faibles avant d’aller sur la page tendances commerciales."
)

st.divider()

st.subheader("Navigation par thème (cahier des charges)")
st.info(
    "Utilisez le **menu des pages** (barre latérale Streamlit) : "
    "**Habitudes d’achat** et **Produits** pour des analyses détaillées et plusieurs visualisations par thème. "
    "Le rapport oral et écrit doit **interpréter** ces graphiques et proposer des **stratégies** à partir des résultats."
)

with st.expander("Aperçu des données brutes (échantillon)"):
    st.dataframe(
        df_v.head(50),
        use_container_width=True,
        hide_index=True,
    )
