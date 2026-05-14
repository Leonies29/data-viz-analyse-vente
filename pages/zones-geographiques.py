import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

@st.cache_data
def load_data():
    np.random.seed(42)
    villes = {
        "Paris":       {"lat": 48.8566, "lon": 2.3522},
        "Lyon":        {"lat": 45.7640, "lon": 4.8357},
        "Marseille":   {"lat": 43.2965, "lon": 5.3698},
        "Toulouse":    {"lat": 43.6047, "lon": 1.4442},
        "Nice":        {"lat": 43.7102, "lon": 7.2620},
        "Nantes":      {"lat": 47.2184, "lon": -1.5536},
        "Strasbourg":  {"lat": 48.5734, "lon": 7.7521},
        "Montpellier": {"lat": 43.6108, "lon": 3.8767},
        "Bordeaux":    {"lat": 44.8378, "lon": -0.5792},
        "Lille":       {"lat": 50.6292, "lon": 3.0573},
    }
    categories = ["Électronique", "Mobilier", "Accessoires", "Vêtements", "Alimentation"]
    canaux     = ["Magasin", "En ligne", "Téléphone"]
    produits   = {
        "Électronique": ["Smartphone", "Laptop", "Tablette", "Casque Audio", "TV"],
        "Mobilier":     ["Canapé", "Bureau", "Chaise", "Armoire", "Lit"],
        "Accessoires":  ["Sac", "Montre", "Ceinture", "Lunettes", "Bijou"],
        "Vêtements":    ["Manteau", "Jean", "Robe", "Chemise", "Chaussures"],
        "Alimentation": ["Café Premium", "Chocolat", "Huile d'Olive", "Thé", "Vin"],
    }
    prix = {
        "Électronique": (150, 1200),
        "Mobilier":     (80, 800),
        "Accessoires":  (20, 300),
        "Vêtements":    (15, 200),
        "Alimentation": (5, 60),
    }

    rows = []
    for _ in range(3000):
        ville  = np.random.choice(list(villes.keys()),
                                  p=[0.28,0.12,0.11,0.09,0.07,0.08,0.07,0.07,0.06,0.05])
        cat    = np.random.choice(categories)
        produit= np.random.choice(produits[cat])
        canal  = np.random.choice(canaux, p=[0.45, 0.40, 0.15])
        pmin, pmax = prix[cat]
        prix_u = round(np.random.uniform(pmin, pmax), 2)
        qte    = np.random.randint(1, 6)
        mois   = np.random.randint(1, 13)
        jour   = np.random.randint(1, 29)
        rows.append({
            "Date de vente":  pd.Timestamp(f"2024-{mois:02d}-{jour:02d}"),
            "Ville":          ville,
            "Catégorie":      cat,
            "Nom du produit": produit,
            "Canal de vente": canal,
            "Prix unitaire":  prix_u,
            "Quantité":       qte,
            "CA":             round(prix_u * qte, 2),
            "Latitude":       villes[ville]["lat"],
            "Longitude":      villes[ville]["lon"],
        })
    df = pd.DataFrame(rows)
    df["Mois"] = df["Date de vente"].dt.month
    return df, villes

df, villes_meta = load_data()

# SIDEBAR Filtres

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

mois_noms = {
    1:"Janvier", 2:"Février", 3:"Mars", 4:"Avril",
    5:"Mai", 6:"Juin", 7:"Juillet", 8:"Août",
    9:"Septembre", 10:"Octobre", 11:"Novembre", 12:"Décembre"
}
mois_sel = st.sidebar.selectbox(
    "Mois",
    options=["Tous"] + list(mois_noms.values())
)

st.sidebar.write("---")
st.sidebar.caption("Données simulées – France 2024")

# Application des filtres
mask = (
    df["Ville"].isin(villes_sel) &
    df["Catégorie"].isin(cats_sel) &
    df["Canal de vente"].isin(canaux_sel)
)
if mois_sel != "Tous":
    mois_num = {v: k for k, v in mois_noms.items()}[mois_sel]
    mask = mask & (df["Mois"] == mois_num)

dff = df[mask]

# titre page
st.title("Zones Géographiques – Rentabilité par ville")
st.caption("Analyse du chiffre d'affaires, du panier moyen et des canaux de vente par ville")
st.write("---")

if dff.empty:
    st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
    st.stop()

# AGRÉGATIONS
agg = dff.groupby("Ville").agg(
    CA_total      = ("CA", "sum"),
    Nb_commandes  = ("CA", "count"),
    Panier_moyen  = ("CA", "mean"),
    Qte_totale    = ("Quantité", "sum"),
).reset_index().sort_values("CA_total", ascending=False)

ville_top    = agg.iloc[0]["Ville"]
ca_top       = agg.iloc[0]["CA_total"]
panier_max_v = agg.loc[agg["Panier_moyen"].idxmax(), "Ville"]
ca_total_all = dff["CA"].sum()
nb_villes    = len(agg)

# KPIs st.metric() dans st.columns()
st.subheader("📊 Indicateurs clés")
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="CA Total",
    value=f"{ca_total_all:,.0f} €"
)
col2.metric(
    label="Ville n°1",
    value=ville_top,
    delta=f"{ca_top:,.0f} €"
)
col3.metric(
    label="Villes actives",
    value=str(nb_villes)
)
col4.metric(
    label="Meilleur panier moyen",
    value=panier_max_v,
    delta=f"{agg.loc[agg['Panier_moyen'].idxmax(), 'Panier_moyen']:.0f} €/cmd"
)

st.write("---")

# Carte + Classement
col_carte, col_bar = st.columns([1.3, 1])

with col_carte:
    st.subheader("Carte – CA par ville")

    agg_map = dff.groupby(["Ville", "Latitude", "Longitude"])["CA"].sum().reset_index()

    fig_carte = px.scatter_mapbox(
        agg_map,
        lat="Latitude", lon="Longitude",
        size="CA", color="CA",
        color_continuous_scale="Blues",
        size_max=50,
        hover_name="Ville",
        hover_data={"CA": ":,.0f", "Latitude": False, "Longitude": False},
        mapbox_style="open-street-map",
        zoom=4.5, center={"lat": 46.5, "lon": 2.5},
        height=380,
    )
    fig_carte.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_carte, use_container_width=True)

with col_bar:
    st.subheader("Classement des villes")

    fig_class = make_subplots(specs=[[{"secondary_y": True}]])
    fig_class.add_trace(go.Bar(
        x=agg["Ville"], y=agg["CA_total"],
        name="CA (€)", marker_color="#4C72B0", opacity=0.85
    ), secondary_y=False)
    fig_class.add_trace(go.Scatter(
        x=agg["Ville"], y=agg["Nb_commandes"],
        name="Nb commandes", mode="lines+markers",
        marker=dict(color="#DD8452", size=7),
        line=dict(color="#DD8452", width=2)
    ), secondary_y=True)
    fig_class.update_layout(
        height=380,
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=0, r=10, t=10, b=0),
        yaxis=dict(title="CA (€)"),
        yaxis2=dict(title="Commandes"),
        plot_bgcolor="white",
    )
    st.plotly_chart(fig_class, use_container_width=True)

st.write("---")

# Panier moyen + Part de CA
col_pm, col_donut = st.columns(2)

with col_pm:
    st.subheader("Panier moyen par ville")

    agg_pm = agg.sort_values("Panier_moyen", ascending=True)
    fig_pm = px.bar(
        agg_pm,
        x="Panier_moyen", y="Ville",
        orientation="h",
        text=agg_pm["Panier_moyen"].apply(lambda v: f"{v:.0f} €"),
        color="Panier_moyen",
        color_continuous_scale="Blues",
        labels={"Panier_moyen": "Panier moyen (€)"},
        height=360,
    )
    fig_pm.update_traces(textposition="outside")
    fig_pm.update_layout(
        margin=dict(l=0, r=60, t=10, b=0),
        coloraxis_showscale=False,
        plot_bgcolor="white",
    )
    st.plotly_chart(fig_pm, use_container_width=True)

with col_donut:
    st.subheader("Part de marché par ville")

    fig_donut = px.pie(
        agg,
        values="CA_total", names="Ville",
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Set2,
        height=360,
    )
    fig_donut.update_traces(textfont_size=11)
    fig_donut.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_donut, use_container_width=True)

st.write("---")

# Heatmap Ville × Catégorie
st.subheader("Heatmap – CA par Ville et Catégorie")

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
    height=320,
)
fig_heat.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(side="bottom"),
)
st.plotly_chart(fig_heat, use_container_width=True)

st.write("---")

# Évolution mensuelle + Mix canaux
col_evo, col_canal = st.columns(2)

with col_evo:
    st.subheader("Évolution mensuelle – Top 5 villes")

    top5 = agg.head(5)["Ville"].tolist()
    df_top5 = df[df["Ville"].isin(top5)]  # données non filtrées par mois
    evo = df_top5.groupby(["Mois", "Ville"])["CA"].sum().reset_index()

    fig_evo = px.line(
        evo, x="Mois", y="CA", color="Ville",
        markers=True,
        color_discrete_sequence=px.colors.qualitative.Set1,
        labels={"CA": "CA (€)", "Mois": "Mois"},
        height=320,
    )
    fig_evo.update_xaxes(
        tickvals=list(mois_noms.keys()),
        ticktext=[v[:3] for v in mois_noms.values()]
    )
    fig_evo.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        legend=dict(orientation="h", y=-0.25),
    )
    st.plotly_chart(fig_evo, use_container_width=True)

with col_canal:
    st.subheader("Mix canal de vente par ville (%)")

    canal_city = dff.groupby(["Ville", "Canal de vente"])["CA"].sum().reset_index()
    totaux = canal_city.groupby("Ville")["CA"].transform("sum")
    canal_city["CA_pct"] = canal_city["CA"] / totaux * 100
    canal_city = canal_city[canal_city["Ville"].isin(agg["Ville"].tolist())]

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
        height=320,
    )
    fig_canal.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", y=-0.25),
        xaxis=dict(
            categoryorder="array",
            categoryarray=agg["Ville"].tolist()
        ),
    )
    st.plotly_chart(fig_canal, use_container_width=True)

st.write("---")

# insights st.write() + st.columns()
st.subheader("Analyse & Recommandations")

col_i1, col_i2, col_i3 = st.columns(3)

villes_faibles = agg.tail(3)["Ville"].tolist()

with col_i1:
    with st.container():
        st.markdown("**Ville dominante**")
        st.write(
            f"**{ville_top}** génère le CA le plus élevé avec **{ca_top:,.0f} €**. "
            "Renforcer les stocks et investir dans des actions marketing ciblées "
            "dans cette zone est une priorité stratégique."
        )

with col_i2:
    with st.container():
        st.markdown("**Potentiel premium**")
        st.write(
            f"**{panier_max_v}** affiche le panier moyen le plus élevé, "
            "ce qui indique une clientèle à fort pouvoir d'achat. "
            "Des offres de fidélité et des gammes premium y seraient particulièrement rentables."
        )

with col_i3:
    with st.container():
        st.markdown("**Zones à développer**")
        st.write(
            f"Les villes **{', '.join(villes_faibles)}** présentent un CA plus faible. "
            "Une campagne digitale via le canal **En ligne** pourrait y stimuler "
            "rapidement la croissance sans investissement physique."
        )

st.write("---")

# Tableau détaillé st.expander() + st.dataframe()
with st.expander("Voir le tableau détaillé par ville"):
    display = agg.copy()
    display["Part CA (%)"] = (display["CA_total"] / display["CA_total"].sum() * 100).round(1)
    display["CA_total"]    = display["CA_total"].apply(lambda v: f"{v:,.0f} €")
    display["Panier_moyen"]= display["Panier_moyen"].apply(lambda v: f"{v:.1f} €")
    display["Part CA (%)"] = display["Part CA (%)"].apply(lambda v: f"{v} %")
    display = display.rename(columns={
        "CA_total":     "CA Total",
        "Nb_commandes": "Nb Commandes",
        "Panier_moyen": "Panier Moyen",
        "Qte_totale":   "Quantité Totale",
    })
    st.dataframe(display.set_index("Ville"), use_container_width=True)

with st.expander("Télécharger les données filtrées"):
    csv_data = dff.drop(columns=["Latitude","Longitude","Mois"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇Télécharger le CSV",
        data=csv_data,
        file_name="ventes_geo_filtrees.csv",
        mime="text/csv"
    )