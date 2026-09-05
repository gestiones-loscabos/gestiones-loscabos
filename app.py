import streamlit as st
import pandas as pd
import psycopg2

# --- CONEXIÓN A LA BASE DE DATOS ÚNICA (NEON.TECH) ---
DATABASE_URL = "postgresql://neondb_owner:npg_Y6RvW8yqBGjH@ep-lingering-thunder-ar76lrca-pooler.c-4.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

@st.cache_resource
def obtener_conexion():
    return psycopg2.connect(DATABASE_URL, client_encoding='utf8')

st.set_page_config(page_title="Archivero Histórico - Gestión Municipal", layout="wide")

st.markdown("<h1 style='text-align: center; color: #0b2d54;'>🗄️ Archivero Histórico - Gestión Municipal</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555;'>Panel de Administración y Clasificación de Expedientes</p>", unsafe_allow_html=True)

# Función para cargar los datos de la nube
def cargar_datos():
    try:
        con = obtener_conexion()
        query = "SELECT id, folio, tipo as tramite_y_giro, contribuyente, dato_actualizado as detalles_y_documentos, observaciones FROM tramites ORDER BY id DESC"
        df = pd.read_sql_query(query, con)
        return df
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.info("No hay trámites registrados todavía en la base de datos.")
else:
    # --- FILTROS LATERALES ---
    st.sidebar.header("🔍 Buscador Rápido")
    busqueda = st.sidebar.text_input("Buscar por Nombre del Propietario o Folio:")

    if busqueda:
        df = df[df['contribuyente'].str.contains(busqueda, case=False, na=False) | 
                df['folio'].str.contains(busqueda, case=False, na=False)]

    # --- PESTAÑAS (CARPETAS ORGANIZADORAS) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📁 Todos los Registros", 
        "🟢 Licencias Nuevas", 
        "🔄 Refrendos Anuales", 
        "⏸️ Actividad / Inactividad", 
        "📂 Gestiones Diversas y Otros"
    ])

    # Carpeta 1: Todos
    with tab1:
        st.write("### Historial Completo")
        st.dataframe(df, use_container_width=True)
        
    # Carpeta 2: Licencias Nuevas
    with tab2:
        st.write("### Expedientes de Licencias Nuevas")
        df_nuevas = df[df['tramite_y_giro'].str.contains('Licencia Nueva', case=False, na=False)]
        st.dataframe(df_nuevas, use_container_width=True)

    # Carpeta 3: Refrendos
    with tab3:
        st.write("### Expedientes de Refrendos Anuales")
        df_refrendos = df[df['tramite_y_giro'].str.contains('Refrendo', case=False, na=False)]
        st.dataframe(df_refrendos, use_container_width=True)

    # Carpeta 4: Inactividades / Clausuras
    with tab4:
        st.write("### Avisos de Actividad, Inactividad o Clausura")
        df_inactividad = df[df['tramite_y_giro'].str.contains('Actividad o Inactividad|Clausura', case=False, na=False, regex=True)]
        st.dataframe(df_inactividad, use_container_width=True)

    # Carpeta 5: Gestiones Diversas
    with tab5:
        st.write("### Gestiones Diversas, Cambios y Anexos")
        df_diversas = df[df['tramite_y_giro'].str.contains('Gestión Diversa|Cambio|Anexo', case=False, na=False, regex=True)]
        st.dataframe(df_diversas, use_container_width=True)