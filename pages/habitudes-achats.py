import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "dataset_ventes_magasin.xlsx"


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
def load_data():
    raw = pd.read_excel(DATA_FILE)
    df = raw.rename(
        columns={
            find_column(raw, "Date de vente"): "date",
            find_column(raw, "Nom du produit"): "produit",
            find_column(raw, "Categorie"): "categorie",
            find_column(raw, "Quantite vendue"): "quantite",
            find_column(raw, "Prix unitaire"): "prix",
            find_column(raw, "Ville"): "ville",
            find_column(raw, "Canal de vente"): "canal",
            find_column(raw, "Client"): "client",
        }
    )
    # Ne pas utiliser dayfirst=True : les dates ISO (2024-02-03) deviennent invalides.
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce")
    df["prix"] = pd.to_numeric(df["prix"], errors="coerce")
    df = df.dropna(subset=["date", "quantite", "prix"]).copy()
    df["ca"] = df["quantite"] * df["prix"]
    df["mois"] = df["date"].dt.to_period("M").astype(str)
    return df


st.title("👥 Habitudes d'achat des clients")
st.markdown(
    "Comment et quand les clients achètent-ils ? Cette page analyse les **canaux** privilégiés, "
    "le **rythme** des achats dans le temps et les **clients** les plus actifs."
)

if not DATA_FILE.exists():
    st.error(f"Fichier introuvable : {DATA_FILE}")
    st.stop()

try:
    df = load_data()
except Exception as err:
    st.error(f"Erreur de chargement des données : {err}")
    st.stop()

if df.empty:
    st.warning("Le fichier Excel ne contient aucune ligne exploitable après nettoyage.")
    st.stop()

st.sidebar.header("Filtres")
categories = st.sidebar.multiselect(
    "Catégorie",
    sorted(df["categorie"].dropna().astype(str).unique()),
    default=sorted(df["categorie"].dropna().astype(str).unique()),
)
canaux = st.sidebar.multiselect(
    "Canal de vente",
    sorted(df["canal"].dropna().astype(str).unique()),
    default=sorted(df["canal"].dropna().astype(str).unique()),
)
villes = st.sidebar.multiselect(
    "Ville",
    sorted(df["ville"].dropna().astype(str).unique()),
    default=sorted(df["ville"].dropna().astype(str).unique()),
)

if not categories or not canaux or not villes:
    st.warning(
        "Sélectionnez au moins une valeur dans chaque filtre (Catégorie, Canal, Ville) "
        "pour afficher les graphiques."
    )
    st.stop()

df_filtre = df[
    df["categorie"].isin(categories)
    & df["canal"].isin(canaux)
    & df["ville"].isin(villes)
]

if df_filtre.empty:
    st.warning("Aucune donnée pour cette combinaison de filtres.")
    st.stop()

st.divider()

# =====================================================
# ÉTAPE 1 — CANAUX D'ACHAT
# =====================================================
st.header("1. Par quel canal les clients achètent-ils ?")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Transactions", f"{len(df_filtre):,}".replace(",", " "))
col2.metric("Chiffre d'affaires", f"{df_filtre['ca'].sum():,.0f} €".replace(",", " "))
col3.metric("Clients distincts", f"{df_filtre['client'].nunique():,}".replace(",", " "))
col4.metric("Panier moyen", f"{df_filtre['ca'].mean():,.0f} €".replace(",", " "))

canal_tx = df_filtre["canal"].value_counts().reset_index()
canal_tx.columns = ["canal", "transactions"]

canal_ca = df_filtre.groupby("canal", as_index=False)["ca"].sum()

col_g, col_d = st.columns(2)

fig_tx = px.bar(
    canal_tx.sort_values("transactions", ascending=True),
    x="transactions",
    y="canal",
    orientation="h",
    text="transactions",
    title="Nombre de transactions par canal",
    color="transactions",
    color_continuous_scale="Greens",
)
fig_tx.update_traces(textposition="outside")
fig_tx.update_layout(showlegend=False, coloraxis_showscale=False, yaxis_title="", xaxis_title="")
col_g.plotly_chart(fig_tx, use_container_width=True)

fig_ca = px.bar(
    canal_ca.sort_values("ca", ascending=True),
    x="ca",
    y="canal",
    orientation="h",
    text="ca",
    title="Chiffre d'affaires par canal (€)",
    color="ca",
    color_continuous_scale="Blues",
)
fig_ca.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
fig_ca.update_layout(
    showlegend=False,
    coloraxis_showscale=False,
    yaxis_title="",
    xaxis_title="Chiffre d'affaires (€)",
)
col_d.plotly_chart(fig_ca, use_container_width=True)

if not canal_tx.empty:
    top_tx = canal_tx.loc[canal_tx["transactions"].idxmax(), "canal"]
    top_ca = canal_ca.loc[canal_ca["ca"].idxmax(), "canal"]
    part_tx = 100 * canal_tx["transactions"].max() / canal_tx["transactions"].sum()
    part_ca = 100 * canal_ca["ca"].max() / canal_ca["ca"].sum()
    st.markdown(
        f"**Lecture :** **{top_tx}** mène en volume ({part_tx:.0f} % des transactions). "
        f"En CA, le leader est **{top_ca}** ({part_ca:.0f} % du total). "
        + (
            "Volume et valeur vont dans le même sens."
            if top_tx == top_ca
            else "Le canal le plus utilisé n'est pas forcément le plus rentable."
        )
    )

st.divider()

# =====================================================
# ÉTAPE 2 — RYTHME DANS LE TEMPS
# =====================================================
st.header("2. Le rythme des achats dans le temps")

ca_mensuel = df_filtre.groupby("mois", as_index=False)["ca"].sum().sort_values("mois")

fig_evo = px.line(
    ca_mensuel,
    x="mois",
    y="ca",
    markers=True,
    title="Évolution mensuelle du chiffre d'affaires",
)
fig_evo.update_layout(xaxis_title="Mois", yaxis_title="Chiffre d'affaires (€)")
st.plotly_chart(fig_evo, use_container_width=True)

if len(ca_mensuel) >= 1:
    row_max = ca_mensuel.loc[ca_mensuel["ca"].idxmax()]
    row_min = ca_mensuel.loc[ca_mensuel["ca"].idxmin()]
    st.markdown(
        f"**Lecture :** pic en **{row_max['mois']}** ({row_max['ca']:,.0f} €), "
        f"creux en **{row_min['mois']}** ({row_min['ca']:,.0f} €)."
    )

st.divider()

# =====================================================
# ÉTAPE 3 — CLIENTS LES PLUS ACTIFS
# =====================================================
st.header("3. Qui achète le plus souvent et génère le plus de CA ?")

top_clients = (
    df_filtre.groupby("client", as_index=False)
    .agg(nb_achats=("client", "count"), quantite=("quantite", "sum"), ca=("ca", "sum"))
    .sort_values(["nb_achats", "ca"], ascending=False)
    .head(10)
)

col_chart, col_table = st.columns([1.4, 1])

fig_clients = px.bar(
    top_clients.sort_values("ca", ascending=True),
    x="ca",
    y="client",
    orientation="h",
    text="ca",
    title="Top 10 — CA par client (€)",
    color="ca",
    color_continuous_scale="Blues",
)
fig_clients.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
fig_clients.update_layout(
    showlegend=False,
    coloraxis_showscale=False,
    yaxis_title="",
    xaxis_title="Chiffre d'affaires (€)",
)
col_chart.plotly_chart(fig_clients, use_container_width=True)

with col_table:
    st.dataframe(
        top_clients.rename(
            columns={
                "nb_achats": "Nb d'achats",
                "quantite": "Quantité",
                "ca": "CA total (€)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

if len(top_clients) >= 2:
    top_freq = top_clients.iloc[0]["client"]
    top_ca_client = top_clients.sort_values("ca", ascending=False).iloc[0]["client"]
    if top_freq != top_ca_client:
        st.markdown(
            f"**Lecture :** **{top_freq}** achète le plus souvent, "
            f"mais **{top_ca_client}** génère le plus de CA."
        )
    else:
        st.markdown(f"**Lecture :** **{top_freq}** est le plus actif et le plus rentable.")

st.divider()

# =====================================================
# ÉTAPE 4 — SYNTHÈSE
# =====================================================
st.header("4. Synthèse et pistes d'action")

canal_top = canal_tx.loc[canal_tx["transactions"].idxmax(), "canal"] if not canal_tx.empty else "—"
clients_recurrents = int((df_filtre.groupby("client").size() > 1).sum())
nb_clients = df_filtre["client"].nunique()

st.markdown(
    f"""
    Canal dominant (transactions) : **{canal_top}**.  
    **{clients_recurrents}** clients sur **{nb_clients}** ont acheté plus d'une fois.

    **Pistes :** renforcer le canal leader, adapter par ville, fidéliser les clients à fort CA.
    """
)
