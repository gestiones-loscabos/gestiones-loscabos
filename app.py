import streamlit as st
import pandas as pd
import psycopg2

DATABASE_URL = "postgresql://neondb_owner:npg_Y6RvW8yqBGjH@ep-lingering-thunder-ar76lrca-pooler.c-4.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

@st.cache_resource
def obtener_conexion():
    return psycopg2.connect(DATABASE_URL, client_encoding='utf8')

st.set_page_config(page_title="Gestiones - Sistema Integral de Licencias (Nube)", layout="wide")

st.sidebar.markdown("### ⚙️ Configuración")
clave_num = st.sidebar.text_input("Actualizar Clave (Numérica)", type="password")
if st.sidebar.button("Guardar Clave"):
    st.sidebar.success("Clave actualizada correctamente")

st.sidebar.markdown("---")
st.sidebar.markdown("### ☁️ Conexión a la Nube")
st.sidebar.button("Abrir Sistema Maestro (Nube)")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Compartir por WhatsApp")
st.sidebar.button("Enviar Portal al Ciudadano")
st.sidebar.button("Enviar Acceso al Equipo")

st.markdown("<h1 style='color: #0b2d54;'>Gestiones - Sistema Integral de Licencias (Nube)</h1>", unsafe_allow_html=True)

menu_principal = st.radio("Seleccione la vista:", ["Panel Central de Gestión", "Archivero Histórico"], horizontal=True)

if menu_principal == "Panel Central de Gestión":
    st.markdown("### 📋 Panel Central de Gestión")
    st.write("Espacio operativo para altas directas y administración general de trámites.")
    
    with st.form("form_gestion_interna"):
        col1, col2 = st.columns(2)
        with col1:
            t_tramite = st.selectbox("Tipo de Trámite Interno", [
                "Licencia Nueva (Venta de Bebidas Alcohólicas)",
                "Refrendo Anual de Licencia",
                "Solicitud de Actividad o Inactividad",
                "Clausura Definitiva",
                "Cambio de Propietario / Traspaso",
                "Gestiones Diversas"
            ])
        with col2:
            contribuyente_int = st.text_input("Nombre del Contribuyente o Propietario")
        
        obs_int = st.text_area("Observaciones o notas internas:")
        guardar_int = st.form_submit_button("Registrar en el Sistema")
        
        if guardar_int:
            if contribuyente_int:
                try:
                    con = obtener_conexion()
                    cur = con.cursor()
                    cur.execute(
                        "INSERT INTO tramites (tipo, folio, contribuyente, dato_actualizado, observaciones) VALUES (%s, %s, %s, %s, %s)",
                        (t_tramite, "INT-001", contribuyente_int, "Registro interno de oficina", obs_int)
                    )
                    con.commit()
                    cur.close()
                    con.close()
                    st.success("¡Trámite interno registrado con éxito!")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning("Escribe el nombre del contribuyente.")

elif menu_principal == "Archivero Histórico":
    st.markdown("### 📂 Control de Registros Históricos (Nube)")
    
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
        busqueda = st.text_input("🔍 Buscar expediente (Nombre Comercial, Contribuyente, Folio o Giro):")

        if busqueda:
            df = df[df['contribuyente'].str.contains(busqueda, case=False, na=False) | 
                    df['folio'].str.contains(busqueda, case=False, na=False) |
                    df['tramite_y_giro'].str.contains(busqueda, case=False, na=False)]

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📁 Todos los Registros", 
            "🟢 Licencias Nuevas", 
            "🔄 Refrendos Anuales", 
            "⏸️ Actividad / Inactividad", 
            "📂 Gestiones Diversas y Otros"
        ])

        with tab1:
            st.write("### Historial Completo")
            st.dataframe(df, use_container_width=True)
            
        with tab2:
            st.write("### Expedientes de Licencias Nuevas")
            df_nuevas = df[df['tramite_y_giro'].str.contains('Licencia Nueva', case=False, na=False)]
            st.dataframe(df_nuevas, use_container_width=True)

        with tab3:
            st.write("### Expedientes de Refrendos Anuales")
            df_refrendos = df[df['tramite_y_giro'].str.contains('Refrendo', case=False, na=False)]
            st.dataframe(df_refrendos, use_container_width=True)

        with tab4:
            st.write("### Avisos de Actividad, Inactividad o Clausura")
            df_inactividad = df[df['tramite_y_giro'].str.contains('Actividad o Inactividad|Clausura', case=False, na=False, regex=True)]
            st.dataframe(df_inactividad, use_container_width=True)

        with tab5:
            st.write("### Gestiones Diversas, Cambios y Anexos")
            df_diversas = df[df['tramite_y_giro'].str.contains('Gestión Diversa|Cambio|Anexo', case=False, na=False, regex=True)]
            st.dataframe(df_diversas, use_container_width=True)