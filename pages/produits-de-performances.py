import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


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


st.title("🏆 Les produits les plus performants")
st.markdown(
    "Quels produits font tourner le magasin ? Cette analyse retrace, en cinq étapes, "
    "comment se construit la performance produit : du palmarès brut jusqu'aux recommandations."
)

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

if df_filtre.empty:
    st.warning("Aucune donnée pour cette combinaison de filtres.")
    st.stop()

agg_produit = (
    df_filtre.groupby("Nom du produit")
    .agg(
        CA=("Chiffre d'affaires", "sum"),
        Quantite=("Quantité vendue", "sum"),
        Transactions=("Client", "count"),
        Prix_moyen=("Prix unitaire", "mean")
    )
    .reset_index()
)
agg_produit["Part_CA"] = agg_produit["CA"] / agg_produit["CA"].sum() * 100
agg_produit["Panier_moyen"] = agg_produit["CA"] / agg_produit["Transactions"]

st.divider()

# =====================================================
# ACTE 1 — LE PALMARÈS
# =====================================================
st.header("1. Le palmarès : qui tire le chiffre d'affaires ?")

top1 = agg_produit.nlargest(1, "CA").iloc[0]
top3 = agg_produit.nlargest(3, "CA")
part_top3 = top3["Part_CA"].sum()
nb_produits = len(agg_produit)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Produit champion", top1["Nom du produit"], f"{top1['CA']:,.0f} €")
col2.metric("Part CA du Top 3", f"{part_top3:.1f} %")
col3.metric("Nombre de produits", f"{nb_produits}")
col4.metric("CA total analysé", f"{agg_produit['CA'].sum():,.0f} €")

st.markdown(
    f"**Lecture :** le Top 3 représente **{part_top3:.0f}%** du chiffre d'affaires sur **{nb_produits} produits**, "
    "soit une concentration modérée. La performance n'est portée par aucun produit dominant, "
    "elle est mieux répartie qu'on ne pourrait l'imaginer."
)

col_g, col_d = st.columns(2)

fig_ca = px.bar(
    agg_produit.sort_values("CA", ascending=True),
    x="CA", y="Nom du produit",
    orientation="h",
    text="CA",
    title="Classement par chiffre d'affaires (€)",
    color="CA",
    color_continuous_scale="Blues"
)
fig_ca.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
fig_ca.update_layout(showlegend=False, coloraxis_showscale=False, yaxis_title="", xaxis_title="Chiffre d'affaires (€)")
col_g.plotly_chart(fig_ca, use_container_width=True)

fig_qte = px.bar(
    agg_produit.sort_values("Quantite", ascending=True),
    x="Quantite", y="Nom du produit",
    orientation="h",
    text="Quantite",
    title="Classement par quantité vendue",
    color="Quantite",
    color_continuous_scale="Greens"
)
fig_qte.update_traces(texttemplate="%{text}", textposition="outside")
fig_qte.update_layout(showlegend=False, coloraxis_showscale=False, yaxis_title="", xaxis_title="Quantité")
col_d.plotly_chart(fig_qte, use_container_width=True)

st.divider()

# =====================================================
# ACTE 2 — VOLUME ≠ VALEUR
# =====================================================
st.header("2. Volume ≠ valeur : démasquer les pépites cachées")

st.markdown(
    "Un produit peut vendre **beaucoup en quantité** sans rapporter gros, ou l'inverse : "
    "vendre **peu mais cher**. Le quadrant ci-dessous croise ces deux dimensions pour révéler "
    "le profil réel de chaque produit."
)

mediane_qte = agg_produit["Quantite"].median()
mediane_ca = agg_produit["CA"].median()

fig_quad = px.scatter(
    agg_produit,
    x="Quantite", y="CA",
    size="Panier_moyen",
    color="Prix_moyen",
    text="Nom du produit",
    color_continuous_scale="Viridis",
    size_max=50,
    title="Quadrant Volume × Valeur (taille = panier moyen, couleur = prix moyen)"
)
fig_quad.update_traces(textposition="top center")
fig_quad.add_hline(y=mediane_ca, line_dash="dash", line_color="grey", annotation_text="CA médian")
fig_quad.add_vline(x=mediane_qte, line_dash="dash", line_color="grey", annotation_text="Quantité médiane")
fig_quad.update_layout(xaxis_title="Quantité vendue", yaxis_title="Chiffre d'affaires (€)")
st.plotly_chart(fig_quad, use_container_width=True)

# Identifier les quadrants
champions = agg_produit[(agg_produit["Quantite"] >= mediane_qte) & (agg_produit["CA"] >= mediane_ca)]
pepites = agg_produit[(agg_produit["Quantite"] < mediane_qte) & (agg_produit["CA"] >= mediane_ca)]
populaires = agg_produit[(agg_produit["Quantite"] >= mediane_qte) & (agg_produit["CA"] < mediane_ca)]
faibles = agg_produit[(agg_produit["Quantite"] < mediane_qte) & (agg_produit["CA"] < mediane_ca)]

c1, c2 = st.columns(2)
with c1:
    st.markdown("**⭐ Champions** _(gros volume + gros CA)_")
    st.write(", ".join(champions["Nom du produit"].tolist()) or "—")
    st.markdown("**💎 Pépites premium** _(peu vendus mais chers)_")
    st.write(", ".join(pepites["Nom du produit"].tolist()) or "—")
with c2:
    st.markdown("**📦 Best-sellers à faible marge** _(beaucoup vendus, CA modeste)_")
    st.write(", ".join(populaires["Nom du produit"].tolist()) or "—")
    st.markdown("**⚠️ Sous-performants** _(faibles sur les deux axes)_")
    st.write(", ".join(faibles["Nom du produit"].tolist()) or "—")

st.divider()

# =====================================================
# ACTE 3 — OÙ ILS PERFORMENT
# =====================================================
st.header("3. Où et comment ils performent ?")

st.markdown(
    "Un produit n'a pas la même performance partout. Les heatmaps suivantes révèlent "
    "les couples produit × ville et produit × canal les plus rentables — utile pour ajuster "
    "le stock et l'effort commercial."
)

col_g2, col_d2 = st.columns(2)

ca_prod_ville = df_filtre.pivot_table(
    index="Nom du produit", columns="Ville",
    values="Chiffre d'affaires", aggfunc="sum", fill_value=0
)
fig_hm_ville = px.imshow(
    ca_prod_ville,
    text_auto=".0f",
    aspect="auto",
    color_continuous_scale="Blues",
    title="CA par produit et par ville (€)"
)
fig_hm_ville.update_layout(xaxis_title="", yaxis_title="")
col_g2.plotly_chart(fig_hm_ville, use_container_width=True)

ca_prod_canal = df_filtre.pivot_table(
    index="Nom du produit", columns="Canal de vente",
    values="Chiffre d'affaires", aggfunc="sum", fill_value=0
)
fig_hm_canal = px.imshow(
    ca_prod_canal,
    text_auto=".0f",
    aspect="auto",
    color_continuous_scale="Oranges",
    title="CA par produit et par canal de vente (€)"
)
fig_hm_canal.update_layout(xaxis_title="", yaxis_title="")
col_d2.plotly_chart(fig_hm_canal, use_container_width=True)

# Insights dynamiques
top_couple_ville = ca_prod_ville.stack().idxmax()
top_couple_canal = ca_prod_canal.stack().idxmax()
st.info(
    f"💡 **Combo le plus rentable (produit × ville) :** {top_couple_ville[0]} à {top_couple_ville[1]} "
    f"— {ca_prod_ville.stack().max():,.0f} €  \n"
    f"💡 **Combo le plus rentable (produit × canal) :** {top_couple_canal[0]} via {top_couple_canal[1]} "
    f"— {ca_prod_canal.stack().max():,.0f} €"
)

st.divider()

# =====================================================
# ACTE 4 — ÉVOLUTION DANS LE TEMPS
# =====================================================
st.header("4. Comment évoluent les meilleurs ?")

st.markdown(
    "Les champions d'aujourd'hui sont-ils stables, en hausse, ou en train de décrocher ? "
    "Le graphique ci-dessous suit le CA mensuel des **5 produits leaders** sur la période."
)

top5_noms = agg_produit.nlargest(5, "CA")["Nom du produit"].tolist()
evolution = (
    df_filtre[df_filtre["Nom du produit"].isin(top5_noms)]
    .groupby(["Mois", "Nom du produit"], as_index=False)["Chiffre d'affaires"].sum()
    .sort_values("Mois")
)

fig_evo = px.line(
    evolution,
    x="Mois", y="Chiffre d'affaires",
    color="Nom du produit",
    markers=True,
    title="Évolution mensuelle du CA — Top 5 produits"
)
fig_evo.update_layout(xaxis_title="Mois", yaxis_title="Chiffre d'affaires (€)")
st.plotly_chart(fig_evo, use_container_width=True)

# Calcul de la dynamique : moyenne 1ʳᵉ moitié vs 2ᵉ moitié de la période
mois_tries = sorted(evolution["Mois"].unique())
mi = len(mois_tries) // 2 or 1
mois_debut = mois_tries[:mi]
mois_fin = mois_tries[mi:]

pivot_evo = evolution.pivot(index="Nom du produit", columns="Mois", values="Chiffre d'affaires").fillna(0)
ca_debut = pivot_evo[mois_debut].mean(axis=1)
ca_fin = pivot_evo[mois_fin].mean(axis=1)
dynamique = ((ca_fin - ca_debut) / ca_debut.replace(0, pd.NA) * 100).dropna().sort_values(ascending=False)

st.markdown(
    f"**Dynamique : moyenne mensuelle CA sur `{', '.join(mois_fin)}` "
    f"vs `{', '.join(mois_debut)}`**"
)
for produit, var in dynamique.items():
    fleche = "📈" if var > 5 else "📉" if var < -5 else "➡️"
    st.write(f"{fleche} **{produit}** : {var:+.1f} %")

st.divider()

# =====================================================
# ACTE 5 — RECOMMANDATIONS
# =====================================================
st.header("5. Stratégies à activer")

st.markdown(
    """
    Sur la base des observations précédentes, voici les axes prioritaires :

    **🎯 Capitaliser sur les champions**  
    Les produits du Top 3 portent une part significative du CA. Sécuriser leur stock,
    négocier de meilleures conditions d'achat et les mettre en avant en page d'accueil
    sont des leviers immédiats.

    **💎 Valoriser les pépites premium**  
    Les produits à faible volume mais fort prix méritent une stratégie distincte : 
    contenu éditorial (fiches produit enrichies), bundling avec un accessoire,
    ou ciblage publicitaire haut de gamme. Leur panier moyen élevé en fait des leviers de marge.

    **📍 Localiser l'effort commercial**  
    Les heatmaps révèlent des affinités produit × ville et produit × canal très marquées. 
    Pousser un produit performant sur son canal natif (et inversement, comprendre 
    pourquoi il sous-performe ailleurs) permet d'optimiser les budgets marketing.

    **⚠️ Décider pour les sous-performants**  
    Les produits faibles sur les deux axes (volume et CA) doivent être réévalués : 
    repositionnement prix, refonte de la fiche produit, ou retrait du catalogue 
    si la tendance ne s'inverse pas sur le trimestre suivant.

    **📈 Surveiller la dynamique**  
    Au-delà du classement statique, la tendance mensuelle est le vrai signal. 
    Un champion qui décroche est plus urgent à traiter qu'un produit moyen stable.
    """
)

with st.expander("📊 Voir le tableau détaillé par produit"):
    st.dataframe(
        agg_produit.sort_values("CA", ascending=False).style.format({
            "CA": "{:,.2f} €",
            "Quantite": "{:,.0f}",
            "Transactions": "{:,.0f}",
            "Prix_moyen": "{:,.2f} €",
            "Part_CA": "{:.1f} %",
            "Panier_moyen": "{:,.2f} €"
        }),
        use_container_width=True,
        hide_index=True
    )