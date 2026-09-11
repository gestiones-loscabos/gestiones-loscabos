import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(
    page_title="Cuarto de Guerra Digital - Baja California Sur",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    div.stButton > button:first-child { 
        background: linear-gradient(135deg, #0b2d54 0%, #1e3a8a 100%); 
        color: white; 
        border-radius: 8px; 
        font-weight: bold; 
        font-size: 15px;
        border: 1px solid #38bdf8;
    }
    .caja-bloque { 
        background-color: #111827; 
        border-left: 5px solid #38bdf8; 
        padding: 12px 16px; 
        margin-top: 10px; 
        margin-bottom: 10px; 
        border-radius: 8px; 
    }
    .titulo-caja { color: #38bdf8; font-weight: bold; font-size: 1.15rem; margin-bottom: 6px; }
    .stat-box { 
        background-color: #111827; 
        padding: 16px; 
        border-radius: 10px; 
        text-align: center; 
        border: 1px solid #1f2937; 
    }
    .stat-num { font-size: 24px; font-weight: bold; color: #38bdf8; margin-top: 6px; }
    .stat-label { font-size: 12px; color: #9ca3af; text-transform: uppercase; font-weight: 600; }
    .mobile-simulator {
        background-color: #0f172a;
        border: 14px solid #1e293b;
        border-radius: 40px;
        padding: 20px;
        min-height: 740px;
    }
</style>
""", unsafe_allow_html=True)

if "autenticado" not in st.session_state: 
    st.session_state.autenticado = False
if "rol_usuario" not in st.session_state:
    st.session_state.rol_usuario = "GENESIS"

if not st.session_state.autenticado:
    st.markdown("<br><br><h1 style='text-align: center; color: #38bdf8; font-size: 2.8rem;'>🛡️ Cuarto de Guerra Digital</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        pin_input = st.text_input("Ingrese Clave de Acceso (PIN):", type="password", key="login_pin")
        if st.button("🔐 Ingresar al Sistema", use_container_width=True):
            if pin_input == "4521" or pin_input == "1234":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("❌ Clave no válida. (PIN: 4521)")
    st.stop()

if "seccion_activa" not in st.session_state:
    st.session_state.seccion_activa = "TABLERO"

with st.sidebar:
    st.markdown("### 🧭 Navegación Táctica")
    if st.button("📊 Tablero de Control", use_container_width=True):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()
    if st.button("📱 Simulador Tracking Poll", use_container_width=True):
        st.session_state.seccion_activa = "SIMULADOR"
        st.rerun()
    st.markdown("---")
    if st.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

st.markdown("<h1 style='color: #38bdf8; margin-top: 5px; font-size: 1.8rem;'>🚀 Cuarto de Guerra Digital: Panel Central</h1>", unsafe_allow_html=True)
st.markdown("---")

if st.session_state.seccion_activa == "TABLERO":
    col_sel_distrito, col_ano_eleccion = st.columns([3, 1])
    with col_sel_distrito:
        st.selectbox("📍 Selector de Distrito Electoral (BCS):", ["Distrito 16 (Cabo San Lucas - Principal)", "Distrito 1 (Los Cabos)"])
    with col_ano_eleccion:
        st.markdown("<div class='stat-box' style='padding: 6px;'><div class='stat-label'>📅 Año Elección</div><div class='stat-num' style='font-size: 18px;'>2027</div></div>", unsafe_allow_html=True)

    col_izq_1, col_der_1 = st.columns(2)
    with col_izq_1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>⏱️ Relojes Operativos y Metas Distritales</div></div>", unsafe_allow_html=True)
        vm_1, vm_2 = st.columns(2)
        with vm_1:
            st.markdown("<div class='stat-box'><div class='stat-label'>🗳️ Votos / Contabilidad</div><div class='stat-num'>9,315</div></div>", unsafe_allow_html=True)
        with vm_2:
            st.markdown("<div class='stat-box'><div class='stat-label'>🏠 Meta Casas (M/CA)</div><div class='stat-num'>115 / 159</div></div>", unsafe_allow_html=True)

    with col_der_1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>🗺️ Mapa INE / Cartografía Táctica BCS</div></div>", unsafe_allow_html=True)
        df_t_mapa = pd.DataFrame([{"lat": 22.8905, "lon": -109.9167}, {"lat": 24.1426, "lon": -110.3128}])
        st.map(df_t_mapa, zoom=8, use_container_width=True)

elif st.session_state.seccion_activa == "SIMULADOR":
    st.markdown("## 📱 Simulador Móvil: Formato Oficial de Encuesta (Tracking Poll)")
    if st.button("⬅️ Volver al Tablero", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    col_sim_izq, col_sim_cen, col_sim_der = st.columns([1, 2, 1])
    with col_sim_cen:
        st.markdown("<div class='mobile-simulator'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#38bdf8; margin:0;'>📊 Tracking Poll</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:10px; color:#9ca3af; margin:0;'>Estudio de Opinión Pública BCS 2027</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        with st.form("form_tracking_poll_oficial"):
            st.text_input("Brigadista Encuestador:", value="Carlos Mendoza")
            st.text_input("Seccional Electoral (Ej: 400):")
            st.radio("1. Sabe usted que este año hay elecciones en BCS?", ["Sí", "No"], horizontal=True)
            st.radio("2. Conoce usted al candidato?", ["Sí", "No"], horizontal=True)
            st.radio("3. Votaría por nuestro candidato?", ["Sí", "No", "Tiene duda"], horizontal=True)
            
            if st.form_submit_button("🚀 Enviar Encuesta"):
                st.success("✅ ¡Encuesta aplicada con éxito!")
        st.markdown("</div>", unsafe_allow_html=True)