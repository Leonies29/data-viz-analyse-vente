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


st.title("Habitudes d'achat des clients")
st.write("Analyse des comportements d'achat.")

data_file = Path(__file__).resolve().parents[1] / "data" / "dataset_ventes_magasin.xlsx"
df = pd.read_excel(data_file)

date_col = find_column(df, "Date de vente")
qte_col = find_column(df, "Quantite vendue")
prix_col = find_column(df, "Prix unitaire")
canal_col = find_column(df, "Canal de vente")
client_col = find_column(df, "Client")
ville_col = find_column(df, "Ville")

df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col]).copy()
df["CA"] = df[qte_col] * df[prix_col]
df["Mois"] = df[date_col].dt.to_period("M").astype(str)

st.subheader("Filtre")
villes = ["Toutes"] + sorted(df[ville_col].dropna().astype(str).unique().tolist())
ville_selectionnee = st.selectbox("Choisir une ville", villes)
if ville_selectionnee != "Toutes":
    df = df[df[ville_col].astype(str) == ville_selectionnee].copy()

st.subheader("1) Canal de vente prefere")
canal_count = df[canal_col].value_counts()
st.bar_chart(canal_count)
st.caption("Ce graphique montre le canal le plus utilise par les clients pour acheter.")

st.subheader("2) Evolution des achats par mois (CA)")
ca_mensuel = df.groupby("Mois", as_index=True)["CA"].sum().sort_index()
st.line_chart(ca_mensuel)
st.caption("Cette courbe montre les mois ou le chiffre d'affaires est plus fort ou plus faible.")

st.subheader("3) Top 10 clients les plus actifs")
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
st.dataframe(top_clients, use_container_width=True)
st.caption("Ce tableau presente les clients qui achetent le plus et ceux qui rapportent le plus de CA.")

st.subheader("Interpretation")
canal_top = canal_count.index[0] if not canal_count.empty else "N/A"
st.write(f"Observation: le canal le plus utilisé est **{canal_top}**.")
st.write("Action recommandée: renforcer les offres sur ce canal et tester des promotions sur les canaux moins utilises.")
