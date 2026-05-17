import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Tendances commerciales",
    page_icon="📈",
    layout="wide"
)

st.title("Analyse des tendances commerciales")

st.markdown(
    "Cette application analyse l'évolution des ventes à partir du chiffre d'affaires, "
    "des quantités vendues, des canaux de vente et des catégories de produits."
)

@st.cache_data
def load_data():
    df = pd.read_excel("data/dataset_ventes_magasin.xlsx")

    df["Date de vente"] = pd.to_datetime(df["Date de vente"], errors="coerce", dayfirst=True)
    df["Quantité vendue"] = pd.to_numeric(df["Quantité vendue"], errors="coerce")
    df["Prix unitaire"] = pd.to_numeric(df["Prix unitaire"], errors="coerce")

    df = df.dropna(subset=["Date de vente", "Quantité vendue", "Prix unitaire"])

    df["Chiffre d'affaires"] = df["Quantité vendue"] * df["Prix unitaire"]
    df["Mois"] = df["Date de vente"].dt.to_period("M").astype(str)

    return df

df = load_data()

st.sidebar.header("Filtres")

categories = st.sidebar.multiselect(
    "Catégorie",
    sorted(df["Catégorie"].dropna().unique()),
    default=sorted(df["Catégorie"].dropna().unique())
)

canaux = st.sidebar.multiselect(
    "Canal de vente",
    sorted(df["Canal de vente"].dropna().unique()),
    default=sorted(df["Canal de vente"].dropna().unique())
)

villes = st.sidebar.multiselect(
    "Ville",
    sorted(df["Ville"].dropna().unique()),
    default=sorted(df["Ville"].dropna().unique())
)

df_filtre = df[
    (df["Catégorie"].isin(categories)) &
    (df["Canal de vente"].isin(canaux)) &
    (df["Ville"].isin(villes))
]

ca_total = df_filtre["Chiffre d'affaires"].sum()
quantite_totale = df_filtre["Quantité vendue"].sum()
nombre_transactions = len(df_filtre)
prix_moyen = ca_total / quantite_totale if quantite_totale > 0 else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Chiffre d'affaires total", f"{ca_total:,.2f} €")
col2.metric("Quantité totale vendue", f"{quantite_totale:,.0f}")
col3.metric("Nombre de transactions", f"{nombre_transactions}")
col4.metric("Prix moyen par unité", f"{prix_moyen:,.2f} €")

st.divider()

ventes_mensuelles = (
    df_filtre
    .groupby("Mois", as_index=False)
    .agg({
        "Chiffre d'affaires": "sum",
        "Quantité vendue": "sum"
    })
    .sort_values("Mois")
)

fig_ca = px.line(
    ventes_mensuelles,
    x="Mois",
    y="Chiffre d'affaires",
    markers=True,
    title="Évolution mensuelle du chiffre d'affaires"
)
fig_ca.update_layout(xaxis_title="Mois", yaxis_title="Chiffre d'affaires (€)")
st.plotly_chart(fig_ca, use_container_width=True)

col_gauche, col_droite = st.columns(2)

fig_quantite = px.bar(
    ventes_mensuelles,
    x="Mois",
    y="Quantité vendue",
    title="Quantités vendues par mois"
)
fig_quantite.update_layout(xaxis_title="Mois", yaxis_title="Quantité vendue")
col_gauche.plotly_chart(fig_quantite, use_container_width=True)

ca_canal = (
    df_filtre
    .groupby(["Mois", "Canal de vente"], as_index=False)["Chiffre d'affaires"]
    .sum()
    .sort_values("Mois")
)

fig_canal = px.bar(
    ca_canal,
    x="Mois",
    y="Chiffre d'affaires",
    color="Canal de vente",
    title="Chiffre d'affaires par canal de vente",
    barmode="stack"
)
fig_canal.update_layout(xaxis_title="Mois", yaxis_title="Chiffre d'affaires (€)")
col_droite.plotly_chart(fig_canal, use_container_width=True)

ca_categorie = (
    df_filtre
    .groupby(["Mois", "Catégorie"], as_index=False)["Chiffre d'affaires"]
    .sum()
    .sort_values("Mois")
)

fig_categorie = px.bar(
    ca_categorie,
    x="Mois",
    y="Chiffre d'affaires",
    color="Catégorie",
    title="Chiffre d'affaires par catégorie",
    barmode="group"
)
fig_categorie.update_layout(xaxis_title="Mois", yaxis_title="Chiffre d'affaires (€)")
st.plotly_chart(fig_categorie, use_container_width=True)

st.subheader("Conclusion")

st.markdown(
    """
    Le chiffre d'affaires atteint son niveau le plus élevé en février, puis diminue progressivement jusqu'en avril.
    Les quantités vendues suivent une tendance proche, ce qui montre que la baisse du chiffre d'affaires est liée en partie
    à une baisse du volume vendu.

    L'analyse par canal permet d'identifier les modes de vente les plus contributeurs.
    L'analyse par catégorie permet de comprendre quelles familles de produits soutiennent principalement la performance commerciale.
    """
)