import streamlit as st
import pandas as pd

uploaded_file = st.file_uploader('excel',type=['xlsx'])

if uploaded_file is None:
    st.stop()

@st.cache_data
def load_data(file):
    print('Loading data')
    return pd.read_excel(file, None)

dfs = pd.read_excel(uploaded_file, None)

names = list(dfs.keys())
sheet_selects = st.multiselect('Sheet',names,[])

if len(sheet_selects) == 0:
    st.stop()

tabs = st.tabs(sheet_selects)

for tab, name in zip(tabs, sheet_selects):
    with tab:
        df = dfs[name]
        st.dataframe(df)