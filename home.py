import streamlit as st
import pandas as pd
from pathlib import Path

st.title("Page principale")
st.write("Présentation de la base de données")


data_file = Path(__file__).resolve().parent / "data" / "dataset_ventes_magasin.xlsx"
df = pd.read_excel(data_file)
st.dataframe(df)