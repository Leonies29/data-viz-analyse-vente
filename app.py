import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Analyse des ventes — Accueil",
    page_icon="🏠",
    layout="wide"
)

# =====================================================
# CHARGEMENT DES DONNÉES
# =====================================================
@st.cache_data
def load_data():
    df = pd.read_excel("data/dataset_ventes_magasin.xlsx")
    df["Date de vente"] = pd.to_datetime(df["Date de vente"], errors="coerce")
    df["Quantité vendue"] = pd.to_numeric(df["Quantité vendue"], errors="coerce")
    df["Prix unitaire"] = pd.to_numeric(df["Prix unitaire"], errors="coerce")
    df = df.dropna(subset=["Date de vente", "Quantité vendue", "Prix unitaire"])
    df["Chiffre d'affaires"] = df["Quantité vendue"] * df["Prix unitaire"]
    df["Mois"] = df["Date de vente"].dt.to_period("M").astype(str)
    return df

df = load_data()

# =====================================================
# EN-TÊTE : LOGO + TITRE PROJET
# =====================================================
col_logo, col_titre = st.columns([1, 4])

with col_logo:
    logo_path = Path("assets/logo_esme.png")
    if logo_path.exists():
        st.image(str(logo_path), width=140)
    else:
        st.markdown(
            """
            <div style="background-color:#0a8045; color:white; padding:20px; 
                        text-align:center; border-radius:8px; font-weight:bold;">
                ESME<br>
                <span style="font-size:0.7em; font-weight:normal;">
                    INNOVATIVE ENGINEERING
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

with col_titre:
    st.markdown("### Majeure Big Data et Digital Marketing — ING2")
    st.title("📊 Analyse des ventes d'un magasin")
    st.caption("Projet Data Visualization • Dr. Kenza Kellou-Menouer")

st.divider()

# =====================================================
# INTRODUCTION DU PROJET
# =====================================================
st.markdown(
    """
    ### 🎯 Contexte du projet

    Une entreprise de vente de produits (électronique, mobilier, accessoires…) souhaite mieux 
    comprendre ses performances commerciales. Les ventes sont réalisées à travers **trois canaux** 
    (magasin, en ligne, téléphone) dans **cinq villes de France**.

    Ce tableau de bord interactif permet d'identifier les **tendances commerciales**, les **produits 
    les plus performants**, les **zones géographiques les plus rentables** et les **habitudes 
    d'achat des clients**.
    """
)

# =====================================================
# KPIs GLOBAUX
# =====================================================
st.subheader("📈 Chiffres clés")

ca_total = df["Chiffre d'affaires"].sum()
quantite_totale = df["Quantité vendue"].sum()
nb_transactions = len(df)
nb_clients = df["Client"].nunique()
nb_produits = df["Nom du produit"].nunique()
nb_villes = df["Ville"].nunique()
panier_moyen = ca_total / nb_transactions if nb_transactions > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Chiffre d'affaires", f"{ca_total:,.0f} €")
col2.metric("📦 Quantité vendue", f"{quantite_totale:,.0f}")
col3.metric("🛒 Transactions", f"{nb_transactions}")
col4.metric("🎯 Panier moyen", f"{panier_moyen:,.0f} €")

col5, col6, col7, col8 = st.columns(4)
col5.metric("👥 Clients uniques", f"{nb_clients}")
col6.metric("🏷️ Produits", f"{nb_produits}")
col7.metric("📍 Villes", f"{nb_villes}")
col8.metric(
    "📅 Période",
    f"{df['Date de vente'].min().strftime('%b %Y')} → {df['Date de vente'].max().strftime('%b %Y')}"
)

st.divider()

# =====================================================
# APERÇU VISUEL — ÉVOLUTION MENSUELLE
# =====================================================
st.subheader("📊 Aperçu de l'évolution du CA")

ca_mensuel = df.groupby("Mois", as_index=False)["Chiffre d'affaires"].sum().sort_values("Mois")
fig_evo = px.area(
    ca_mensuel,
    x="Mois", y="Chiffre d'affaires",
    title="",
    markers=True,
    color_discrete_sequence=["#0a8045"]
)
fig_evo.update_layout(
    xaxis_title="Mois",
    yaxis_title="Chiffre d'affaires (€)",
    height=300,
    margin=dict(l=0, r=0, t=10, b=0)
)
st.plotly_chart(fig_evo, use_container_width=True)

st.divider()

# =====================================================
# HUB DE NAVIGATION : LES 4 PAGES
# =====================================================
st.subheader("🧭 Naviguez dans l'analyse")
st.caption("Chaque page approfondit un thème spécifique. Cliquez pour explorer.")

# Préparer les chiffres clés à afficher dans les cartes
top_produit = df.groupby("Nom du produit")["Chiffre d'affaires"].sum().idxmax()
top_ville = df.groupby("Ville")["Chiffre d'affaires"].sum().idxmax()
top_canal = df.groupby("Canal de vente")["Chiffre d'affaires"].sum().idxmax()
mois_max = ca_mensuel.loc[ca_mensuel["Chiffre d'affaires"].idxmax(), "Mois"]

card_style = """
<div style="
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 20px;
    height: 220px;
    background-color: {bg};
    margin-bottom: 10px;
">
    <h4 style="margin-top:0; color:{color};">{emoji} {titre}</h4>
    <p style="font-size:0.9em; color:#444;">{desc}</p>
    <p style="font-size:0.85em; color:{color}; font-weight:bold; margin-top:10px;">
        💡 {teaser}
    </p>
</div>
"""

col_a, col_b = st.columns(2)

with col_a:
    st.markdown(card_style.format(
        bg="#f0f8ff",
        color="#1f77b4",
        emoji="📈",
        titre="Tendances commerciales",
        desc="Évolution du CA, des quantités et de l'activité dans le temps, par canal et catégorie.",
        teaser=f"Mois le plus actif : {mois_max}"
    ), unsafe_allow_html=True)
    if st.button("Explorer les tendances →", use_container_width=True, key="btn_tendances"):
        st.switch_page("pages/tendances-commercial.py")

    st.markdown(card_style.format(
        bg="#fff8f0",
        color="#d97706",
        emoji="📍",
        titre="Zones géographiques",
        desc="Performance par ville, cartographie des ventes et identification des marchés porteurs.",
        teaser=f"Ville n°1 : {top_ville}"
    ), unsafe_allow_html=True)
    if st.button("Explorer les zones →", use_container_width=True, key="btn_zones"):
        st.switch_page("pages/zones-geographiques.py")

with col_b:
    st.markdown(card_style.format(
        bg="#fef7ff",
        color="#9333ea",
        emoji="🏆",
        titre="Produits performants",
        desc="Palmarès, volume vs valeur, pépites cachées et trajectoires des top produits.",
        teaser=f"Produit champion : {top_produit}"
    ), unsafe_allow_html=True)
    if st.button("Explorer les produits →", use_container_width=True, key="btn_produits"):
        st.switch_page("pages/produits-de-performances.py")

    st.markdown(card_style.format(
        bg="#f0fdf4",
        color="#16a34a",
        emoji="🛍️",
        titre="Habitudes d'achat",
        desc="Comportement client, canaux préférés, fréquence d'achat et profils types.",
        teaser=f"Canal préféré : {top_canal}"
    ), unsafe_allow_html=True)
    if st.button("Explorer les habitudes →", use_container_width=True, key="btn_habitudes"):
        st.switch_page("pages/habitudes-achats.py")

st.divider()

# =====================================================
# PIED DE PAGE
# =====================================================
st.caption(
    "📚 Projet réalisé dans le cadre de la Majeure Big Data et Digital Marketing — ESME Sudria • ING2 • "
    "Encadrement : Dr. Kenza Kellou-Menouer"
)