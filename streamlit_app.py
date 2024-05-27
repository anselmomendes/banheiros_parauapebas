import streamlit as st
import requests
import folium
from folium.plugins import Draw
from streamlit_geolocation import streamlit_geolocation
from streamlit_star_rating import st_star_rating
from streamlit_folium import st_folium
import json
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import psycopg2
load_dotenv()

st.set_page_config(page_title="Page Title", layout="wide")

st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

st.title("Banheiros de Parauapebas")
st.image("imagens\Imagem2.png", width=200)

#print(location)

def get_location():
  location = streamlit_geolocation()
  if location['latitude'] == None:
    st.write("Clique aqui para ativar a sua localização e habilite a localização no seu navegador.")
    return None
  else:
    st.session_state.locale = {"latitude": location['latitude'], "longitude": location['longitude']}
    return location

def conecta_db():
  con = psycopg2.connect(host='postgres.contovisual.com.br', 
                         database='postgres',
                         user='postgres', 
                         password='postgres')
  return con

def criar_db(sql):
  con = conecta_db()
  cur = con.cursor()
  cur.execute(sql)
  con.commit()
  con.close()

def inserir_db(sql):
    con = conecta_db()
    cur = con.cursor()
    try:
        cur.execute(sql)
        con.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        con.rollback()
        cur.close()
        return 1
    cur.close()

@st.experimental_dialog("Cast your vote")
def vote():
    st.write("Qual a sua avaliação para esses critérios do local visitado?")
    estabelecimentos = st.text_area("Qual é o nome do local?", max_chars=200)
    insumos = st_star_rating("Insumos", 5, 3, 40)
    cheiro = st_star_rating("cheiro", 5, 3, 40)
    estrutura = st_star_rating("estrutura", 5, 3, 40)
    limpeza = st_star_rating("limpeza", 5, 3, 40)
    descricao = st.text_area("Deixe um comentário sobre o local", max_chars=200)

    if st.button("Enviar avaliação"):
        st.session_state.stars = {"estabelecimentos": estabelecimentos, "descricao": descricao, "insumos": insumos, "cheiro": cheiro, \
          "estrutura": estrutura, "limpeza": limpeza, "insumos": insumos, "media_final": (insumos + cheiro + estrutura + limpeza) / 4}
        st.rerun()

#Code starts hare

col1, col2 = st.columns(2)

with col1:
  location = get_location()
      
  if "locale" not in st.session_state:
    st.write("no location")
  else:
    latitude = st.session_state.locale['latitude']
    longitude = st.session_state.locale['longitude']

    m = folium.Map(location=[latitude, longitude], zoom_start=18)
    folium.Marker([latitude, longitude], popup="Minha Localização", tooltip="Minha Localização").add_to(m)

    select = pd.read_sql("SELECT * FROM banheiro.vote", conecta_db())

    for index, row in select.iterrows():
      folium.Marker([row['latitude'], row['longitude']], popup=f"{row['estabelecimentos']}", \
        tooltip=f"{row['estabelecimentos']}").add_to(m)

    output = st_folium(m, width=800, height=400, returned_objects=["last_object_clicked_tooltip"])

    if st.button("Avaliar"):
      vote()

    if "stars" in st.session_state:
      st.write("Avaliação enviada com sucesso!")

    if "stars" in st.session_state and "locale" in st.session_state:
      stars = pd.DataFrame([st.session_state.stars])
      locale = pd.DataFrame([st.session_state.locale])
      df = pd.concat([stars, locale], axis=1)
      

      for i in df.index:
          sql = """
          INSERT into banheiro.vote (estabelecimentos, insumos, cheiro, estrutura, limpeza, descricao, latitude, longitude, media_final) 
          values('%s','%s','%s','%s','%s','%s','%s','%s','%s');
          """ % (df['estabelecimentos'][i], df['insumos'][i], df['cheiro'][i], df['estrutura'][i], df['limpeza'][i], df['descricao'][i], df['latitude'][i], df['longitude'][i], df['media_final'][i])
          inserir_db(sql)

with col2:
   if len(output) > 0:
    select = pd.read_sql(f"""SELECT estabelecimentos, 
    avg(insumos) insumos, 
    avg(cheiro) cheiro, 
    avg(estrutura) estrutura, 
    avg(limpeza) limpeza, 
    avg(media_final) media_final 
    FROM banheiro.vote
    where estabelecimentos = '{output['last_object_clicked_tooltip']}'
    group by estabelecimentos
    limit 1
    """, conecta_db())

    st.write("Informações sobre o estabelecimento")
    st.write(f"Estabelecimento: {select['estabelecimentos'][0]}")
    st.write(f"Insumos: {select['insumos'][0]}")
    st.write(f"Cheiro: {select['cheiro'][0]}")
    st.write(f"Estrutura: {select['estrutura'][0]}")
    st.write(f"Limpeza: {select['limpeza'][0]}")
    st.write(f"Media Final: {select['media_final'][0]}")