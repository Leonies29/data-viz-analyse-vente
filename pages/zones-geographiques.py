import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Chargement du dataset
@st.cache_data
def load_data():
    # Coordonnées GPS des 5 villes du dataset
    coords = {
        "Paris":     {"lat": 48.8566, "lon": 2.3522},
        "Lyon":      {"lat": 45.7640, "lon": 4.8357},
        "Marseille": {"lat": 43.2965, "lon": 5.3698},
        "Toulouse":  {"lat": 43.6047, "lon": 1.4442},
        "Nice":      {"lat": 43.7102, "lon": 7.2620},
    }

    df = pd.read_excel("data/dataset_ventes_magasin.xlsx")

    # Nettoyage et enrichissement
    df["Date de vente"] = pd.to_datetime(df["Date de vente"])
    df["Mois"]          = df["Date de vente"].dt.month
    df["CA"]            = df["Prix unitaire"] * df["Quantité vendue"]
    df["Latitude"]      = df["Ville"].map(lambda v: coords[v]["lat"])
    df["Longitude"]     = df["Ville"].map(lambda v: coords[v]["lon"])

    return df

df = load_data()

mois_noms = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai",     6: "Juin",    7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}

# sidebar – Filtres
st.sidebar.header("Filtres")

villes_sel = st.sidebar.multiselect(
    "Villes",
    options=sorted(df["Ville"].unique()),
    default=list(df["Ville"].unique())
)

cats_sel = st.sidebar.multiselect(
    "Catégories de produit",
    options=sorted(df["Catégorie"].unique()),
    default=list(df["Catégorie"].unique())
)

canaux_sel = st.sidebar.multiselect(
    "Canaux de vente",
    options=sorted(df["Canal de vente"].unique()),
    default=list(df["Canal de vente"].unique())
)

# mois
mois_dispo = sorted(df["Mois"].unique())
mois_sel = st.sidebar.selectbox(
    "Mois",
    options=["Tous"] + [mois_noms[m] for m in mois_dispo]
)

# Filtrage 
mask = (
    df["Ville"].isin(villes_sel) &
    df["Catégorie"].isin(cats_sel) &
    df["Canal de vente"].isin(canaux_sel)
)
if mois_sel != "Tous":
    mois_num = {v: k for k, v in mois_noms.items()}[mois_sel]
    mask = mask & (df["Mois"] == mois_num)

dff = df[mask]

if dff.empty:
    st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
    st.stop()

# Agrégation par ville
agg = dff.groupby("Ville").agg(
    CA_total      = ("CA", "sum"),
    Nb_commandes  = ("CA", "count"),
    Panier_moyen  = ("CA", "mean"),
    Qte_totale    = ("Quantité vendue", "sum"),
).reset_index().sort_values("CA_total", ascending=False)

ville_top      = agg.iloc[0]["Ville"]
ca_top         = agg.iloc[0]["CA_total"]
part_top       = ca_top / agg["CA_total"].sum() * 100
panier_max_v   = agg.loc[agg["Panier_moyen"].idxmax(), "Ville"]
panier_max     = agg["Panier_moyen"].max()
panier_min_v   = agg.loc[agg["Panier_moyen"].idxmin(), "Ville"]
panier_min     = agg["Panier_moyen"].min()
ca_total_all   = dff["CA"].sum()
nb_villes      = len(agg)
villes_faibles = agg.tail(2)["Ville"].tolist()

# Intro et KPIs
st.title("🗺️ Zones Géographiques")
st.markdown(
    "Dans cette analyse, nous allons répondre à une question centrale : "
    "**quelles villes génèrent le plus de valeur pour l'entreprise, "
    "et comment mieux y concentrer nos efforts commerciaux ?**"
)
st.write("---")

st.subheader("Étape 1 – Vue d'ensemble : combien et où ?")
st.write(
    "Avant d'entrer dans le détail, posons les chiffres clés de la période analysée. "
    "Ces indicateurs donnent une première lecture de la performance géographique globale."
)

col1, col2, col3, col4 = st.columns(4)

# CA total
with col1:
    st.write("**CA Total généré**")
    st.write(f"### {ca_total_all:,.0f} €")

with col2:
    st.metric(
        label="**Ville n°1**",
        value=ville_top,
        delta=f"{part_top:.1f} % du CA total"
    )

with col3:
    st.metric(
        label="**Villes analysées**",
        value=str(nb_villes)
    )

with col4:
    st.metric(
        label="**Meilleur panier moyen**",
        value=panier_max_v,
        delta=f"{panier_max:.0f} € / commande"
    )

st.info(
    f"Sur les **{len(dff)} transactions** analysées, l'entreprise a réalisé "
    f"**{ca_total_all:,.0f} €** de chiffre d'affaires sur {nb_villes} villes françaises. "
    f"**{ville_top}** se détache nettement avec **{part_top:.1f} %** du CA total, "
    f"tandis que **{panier_max_v}** affiche la valeur moyenne par commande la plus élevée "
    f"({panier_max:.0f} €)."
)

st.write("---")

# Ou se concentre le CA ?
st.subheader("Étape 2 – Où se concentre le chiffre d'affaires ?")
st.write(
    "La carte ci-dessous permet de visualiser immédiatement les zones à forte valeur. "
    "Plus la bulle est grande et foncée, plus la ville génère de revenus."
)

col_carte, col_donut = st.columns([1.4, 1])

with col_carte:
    agg_map = dff.groupby(["Ville", "Latitude", "Longitude"])["CA"].sum().reset_index()

    fig_carte = px.scatter_mapbox(
        agg_map,
        lat="Latitude", lon="Longitude",
        size="CA", color="CA",
        color_continuous_scale="Blues",
        size_max=55,
        hover_name="Ville",
        hover_data={"CA": ":,.0f", "Latitude": False, "Longitude": False},
        mapbox_style="open-street-map",
        zoom=4.5, center={"lat": 45.5, "lon": 3.5},
        height=400,
    )
    fig_carte.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_carte, use_container_width=True)

with col_donut:
    st.write("**Répartition du CA par ville**")
    fig_donut = px.pie(
        agg,
        values="CA_total", names="Ville",
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Set2,
        height=400,
    )
    fig_donut.update_traces(textfont_size=12)
    fig_donut.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_donut, use_container_width=True)

st.info(
    f"La carte confirme une **concentration géographique marquée** : "
    f"**{ville_top}** domine avec {part_top:.1f} % du CA. "
    "Le donut montre que les premières villes captent la majorité des revenus. "
    "Cette inégalité est un signal fort pour prioriser les ressources commerciales."
)

st.write("---")

# Classement : CA et volume de commandes
st.subheader("Étape 3 – Classement détaillé : CA et volume de commandes")
st.write(
    "Un CA élevé peut venir d'un grand nombre de commandes **ou** d'un panier moyen élevé. "
    "Le graphique suivant superpose ces deux dimensions pour chaque ville."
)

fig_class = make_subplots(specs=[[{"secondary_y": True}]])
fig_class.add_trace(go.Bar(
    x=agg["Ville"], y=agg["CA_total"],
    name="CA (€)", marker_color="#4C72B0", opacity=0.85
), secondary_y=False)
fig_class.add_trace(go.Scatter(
    x=agg["Ville"], y=agg["Nb_commandes"],
    name="Nb commandes", mode="lines+markers",
    marker=dict(color="#DD8452", size=9),
    line=dict(color="#DD8452", width=2)
), secondary_y=True)
fig_class.update_layout(
    height=360,
    legend=dict(orientation="h", y=-0.2),
    margin=dict(l=0, r=10, t=10, b=0),
    yaxis=dict(title="CA (€)"),
    yaxis2=dict(title="Nb commandes"),
    plot_bgcolor="white",
    xaxis=dict(categoryorder="array", categoryarray=agg["Ville"].tolist())
)
st.plotly_chart(fig_class, use_container_width=True)

ville_vol_max = agg.loc[agg["Nb_commandes"].idxmax(), "Ville"]
st.info(
    f"**{ville_top}** domine à la fois en CA et en volume de commandes. "
    f"On peut noter que **{ville_vol_max}** enregistre un fort volume de transactions, "
    "ce qui montre une clientèle active. Croiser ce chiffre avec le panier moyen "
    "nous donnera une image plus complète dans l'étape suivante."
)

st.write("---")

# Qualité des ventes : le panier moyen par ville
st.subheader("Étape 4 – Qualité des ventes : le panier moyen par ville")
st.write(
    "Le panier moyen révèle la **valeur unitaire** de chaque transaction. "
    "Une ville avec un panier élevé indique une clientèle plus aisée ou des produits premium vendus."
)

agg_pm = agg.sort_values("Panier_moyen", ascending=True)
fig_pm = px.bar(
    agg_pm,
    x="Panier_moyen", y="Ville",
    orientation="h",
    text=agg_pm["Panier_moyen"].apply(lambda v: f"{v:.0f} €"),
    color="Panier_moyen",
    color_continuous_scale="Blues",
    labels={"Panier_moyen": "Panier moyen (€)"},
    height=320,
)
fig_pm.update_traces(textposition="outside")
fig_pm.update_layout(
    margin=dict(l=0, r=70, t=10, b=0),
    coloraxis_showscale=False,
    plot_bgcolor="white",
)
st.plotly_chart(fig_pm, use_container_width=True)

st.info(
    f"**{panier_max_v}** affiche le panier moyen le plus élevé "
    f"({panier_max:.0f} €), signalant une clientèle à fort pouvoir d'achat. "
    f"À l'inverse, **{panier_min_v}** ({panier_min:.0f} €) présente des achats plus modestes. "
    "Ces écarts orientent les stratégies tarifaires et les actions de montée en gamme selon les zones."
)

st.write("---")

# Quels produits dans quelles villes ?
st.subheader("Étape 5 – Quels produits dans quelles villes ?")
st.write(
    "La heatmap croise les villes avec les catégories de produits. "
    "Elle permet d'identifier les **spécialités locales** et les catégories sous-exploitées."
)

pivot = dff.pivot_table(
    index="Ville", columns="Catégorie",
    values="CA", aggfunc="sum", fill_value=0
)
pivot = pivot.loc[[v for v in agg["Ville"] if v in pivot.index]]

fig_heat = px.imshow(
    pivot,
    color_continuous_scale="Blues",
    aspect="auto",
    text_auto=".0f",
    labels=dict(color="CA (€)"),
    height=300,
)
fig_heat.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(side="bottom"),
)
st.plotly_chart(fig_heat, use_container_width=True)

cat_totaux = dff.groupby("Catégorie")["CA"].sum()
cat_top    = cat_totaux.idxmax()
cat_top_val = cat_totaux.max()

st.info(
    f"La catégorie **{cat_top}** est la plus rentable globalement "
    f"({cat_top_val:,.0f} €). "
    f"On remarque que **{ville_top}** performe dans la plupart des catégories, "
    "mais certaines villes secondaires montrent des forces spécifiques, "
    "ce qui ouvre la porte à des **stratégies de spécialisation par zone géographique**."
)

st.write("---")

# Comment les clients achètent-ils par ville ?
st.subheader("Étape 6 – Comment les clients achètent-ils par ville ?")
st.write(
    "Le canal de vente (Magasin, En ligne, Téléphone) varie selon les villes. "
    "Cette analyse est clé pour **adapter les investissements commerciaux** à chaque zone."
)

col_canal, col_evo = st.columns(2)

with col_canal:
    st.write("**Mix canal par ville (% du CA)**")
    canal_city = dff.groupby(["Ville", "Canal de vente"])["CA"].sum().reset_index()
    totaux = canal_city.groupby("Ville")["CA"].transform("sum")
    canal_city["CA_pct"] = canal_city["CA"] / totaux * 100

    fig_canal = px.bar(
        canal_city,
        x="Ville", y="CA_pct",
        color="Canal de vente",
        barmode="stack",
        color_discrete_map={
            "Magasin":   "#4C72B0",
            "En ligne":  "#55A868",
            "Téléphone": "#C44E52",
        },
        labels={"CA_pct": "% du CA", "Ville": ""},
        height=340,
    )
    fig_canal.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", y=-0.3),
        xaxis=dict(categoryorder="array", categoryarray=agg["Ville"].tolist()),
    )
    st.plotly_chart(fig_canal, use_container_width=True)

with col_evo:
    st.write("**Évolution mensuelle du CA par ville**")
    evo = dff.groupby(["Mois", "Ville"])["CA"].sum().reset_index()

    fig_evo = px.line(
        evo, x="Mois", y="CA", color="Ville",
        markers=True,
        color_discrete_sequence=px.colors.qualitative.Set1,
        labels={"CA": "CA (€)", "Mois": "Mois"},
        height=340,
    )
    mois_dispo_evo = sorted(evo["Mois"].unique())
    fig_evo.update_xaxes(
        tickvals=mois_dispo_evo,
        ticktext=[mois_noms[m][:3] for m in mois_dispo_evo]
    )
    fig_evo.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        legend=dict(orientation="h", y=-0.3),
    )
    st.plotly_chart(fig_evo, use_container_width=True)

st.info(
    "Le mix canal révèle des **comportements d'achat différents** selon les villes. "
    "Certaines sont fortement orientées magasin physique, d'autres vers le digital. "
    "L'évolution mensuelle permet d'identifier des tendances saisonnières sur les 4 mois disponibles, "
    "des variations utiles pour anticiper les besoins en stock et en promotions."
)

st.write("---")

# Synthèse et recommandations
st.subheader("Étape 7 – Synthèse et recommandations")
st.write(
    "En croisant toutes ces dimensions — volume, valeur, catégorie, canal — "
    "trois grandes orientations stratégiques se dégagent :"
)

col_r1, col_r2, col_r3 = st.columns(3)

with col_r1:
    st.success(
        f"**Consolider {ville_top}**\n\n"
        f"{ville_top} représente **{part_top:.1f} %** du CA total. "
        "Il faut maintenir cette position par des actions de fidélisation, "
        "un stock renforcé et des offres exclusives pour les clients réguliers."
    )

with col_r2:
    st.warning(
        f"**Capitaliser sur {panier_max_v}**\n\n"
        f"{panier_max_v} a le panier moyen le plus élevé ({panier_max:.0f} €). "
        "C'est la zone idéale pour tester des gammes premium "
        "et des programmes de fidélité haut de gamme."
    )

with col_r3:
    st.error(
        f"**Activer {' et '.join(villes_faibles)}**\n\n"
        "Ces villes sont en retrait. Une campagne digitale ciblée "
        "via le canal **En ligne** permettrait d'y accroître la présence "
        "sans coûts fixes supplémentaires."
    )

st.write("---")

# Annexes
with st.expander("Annexe – Tableau détaillé par ville"):
    display = agg.copy()
    display["Part CA (%)"]  = (display["CA_total"] / display["CA_total"].sum() * 100).round(1)
    display["CA_total"]     = display["CA_total"].apply(lambda v: f"{v:,.0f} €")
    display["Panier_moyen"] = display["Panier_moyen"].apply(lambda v: f"{v:.1f} €")
    display["Part CA (%)"]  = display["Part CA (%)"].apply(lambda v: f"{v} %")
    display = display.rename(columns={
        "CA_total":     "CA Total",
        "Nb_commandes": "Nb Commandes",
        "Panier_moyen": "Panier Moyen",
        "Qte_totale":   "Quantité Totale",
    })
    st.dataframe(display.set_index("Ville"), use_container_width=True)

with st.expander("Annexe – Télécharger les données filtrées"):
    csv_data = dff.drop(columns=["Latitude", "Longitude", "Mois"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇Télécharger le CSV filtré",
        data=csv_data,
        file_name="ventes_geo_filtrees.csv",
        mime="text/csv"
    )