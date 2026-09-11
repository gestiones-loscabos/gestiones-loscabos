import streamlit as st
import pandas as pd
import urllib.parse
import os
import subprocess
import platform

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO TÁCTICO OSCURO (ALTO CONTRASTE) ---
st.set_page_config(
    page_title="Cuarto de Guerra Digital - Baja California Sur",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    div.stButton > button:first-child { 
        background: linear-gradient(135deg, #0b2d54 0%, #1e3a8a 100%); 
        color: white; 
        border-radius: 8px; 
        font-weight: bold; 
        font-size: 15px;
        border: 1px solid #38bdf8;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    div.stButton > button:first-child:hover { background: linear-gradient(135deg, #15457a 0%, #2563eb 100%); border-color: #38bdf8; }
    .caja-bloque { 
        background-color: #111827; 
        border-left: 5px solid #38bdf8; 
        padding: 14px 18px; 
        margin-top: 10px; 
        margin-bottom: 10px; 
        border-radius: 8px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .titulo-caja { color: #38bdf8; font-weight: bold; font-size: 1.15rem; margin-bottom: 8px; letter-spacing: 0.3px; }
    .stat-box { 
        background-color: #111827; 
        padding: 16px; 
        border-radius: 10px; 
        text-align: center; 
        border: 1px solid #1f2937; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .stat-num { font-size: 24px; font-weight: bold; color: #38bdf8; margin-top: 6px; }
    .stat-label { font-size: 12px; color: #cbd5e1; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
    .mobile-simulator {
        background-color: #020617;
        border: 14px solid #1e293b;
        border-radius: 40px;
        padding: 24px;
        min-height: 780px;
        color: #ffffff;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.8);
    }
    /* Textos claros garantizados para legibilidad móvil */
    .mobile-simulator p, .mobile-simulator label, .mobile-simulator span, .mobile-simulator div {
        color: #f8fafc !important;
    }
</style>
""", unsafe_allow_html=True)

# --- AUTENTICACIÓN DINÁMICA ---
if "autenticado" not in st.session_state: 
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None
if "rol_usuario" not in st.session_state:
    st.session_state.rol_usuario = None

if not st.session_state.autenticado:
    st.markdown("<br><br><h1 style='text-align: center; color: #38bdf8; font-size: 2.8rem;'>🛡️ Cuarto de Guerra Digital</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 1.1rem;'>Plataforma Electoral Táctica - Baja California Sur (Versión 15.0)</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        pin_input = st.text_input("Ingrese Clave de Acceso (PIN):", type="password", key="login_pin")
        if st.button("🔐 Ingresar al Sistema", use_container_width=True):
            if pin_input == "4521" or pin_input == "1234":
                st.session_state.autenticado = True
                st.session_state.usuario_actual = "Roberto Hernández"
                st.session_state.rol_usuario = "GENESIS"
                st.rerun()
            else:
                st.error("❌ Clave no válida. (Prueba con PIN: 4521)")
    st.stop()

# --- ESTADOS DE NAVEGACIÓN ---
if "ver_modal_brigadistas" not in st.session_state:
    st.session_state.ver_modal_brigadistas = False
if "seccion_activa" not in st.session_state:
    st.session_state.seccion_activa = "TABLERO"

# ==========================================
# MENÚ LATERAL (SIDEBAR) - NAVEGACIÓN COMPLETA
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 Usuario: {st.session_state.usuario_actual}")
    st.markdown(f"🛡️ **Rol:** `{st.session_state.rol_usuario}`")
    st.markdown("---")
    
    st.markdown("### 🧭 Navegación Táctica")
    if st.button("📊 Tablero de Control", use_container_width=True):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()
    if st.button("👥 Módulo Territorial (CA)", use_container_width=True):
        st.session_state.seccion_activa = "TERRITORIAL"
        st.rerun()
    if st.button("🎪 Evento Masivo / Cierre", use_container_width=True):
        st.session_state.seccion_activa = "EVENTO"
        st.rerun()
    if st.button("🚨 Operación Día D", use_container_width=True):
        st.session_state.seccion_activa = "DIA_D"
        st.rerun()
    if st.button("📱 Redes y Difusión", use_container_width=True):
        st.session_state.seccion_activa = "REDES"
        st.rerun()
    if st.button("📱 Simulador Tracking Poll", use_container_width=True):
        st.session_state.seccion_activa = "SIMULADOR"
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔗 Central de Envíos de Enlaces")
    opciones_links = [
        "[1] Voto de Aire (Público)",
        "[2] Voto Seguro (Estructura)",
        "[3] Tracking Poll (Encuestas)",
        "[4] Alta Casa Amiga (GPS)",
        "[5] Alta Coanfitrión",
        "[6] Alta Simpatizante"
    ]
    link_seleccionado = st.selectbox("Seleccionar Vínculo:", opciones_links)
    celular_hub = st.text_input("Celular Destinatario:", "6240000000")
    msg_hub = f"Hola, te comparto el enlace operativo: {link_seleccionado}"
    link_w_hub = f"https://wa.me/52{celular_hub}?text={urllib.parse.quote(msg_hub)}"
    st.markdown(f'<a href="{link_w_hub}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: bold;">📲 Enviar Link por WhatsApp</a>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# ==========================================
# CABECERA SUPERIOR
# ==========================================
st.markdown("<h1 style='color: #38bdf8; margin-top: 5px; font-size: 1.8rem;'>🚀 Cuarto de Guerra Digital: Panel Central</h1>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# VISTA 1: TABLERO DE CONTROL COMPLETO
# ==========================================
if st.session_state.seccion_activa == "TABLERO":
    col_sel_distrito, col_ano_eleccion = st.columns([3, 1])
    with col_sel_distrito:
        distritos_bcs = [
            "Distrito 1 (Los Cabos - Cabecera)", "Distrito 2 (La Paz)", "Distrito 3 (La Paz)", "Distrito 4 (La Paz)",
            "Distrito 5 (La Paz)", "Distrito 6 (La Paz)", "Distrito 7 (San José del Cabo)", "Distrito 8 (Cabo San Lucas)",
            "Distrito 9 (Loreto/Comondú)", "Distrito 10 (Mulegé)", "Distrito 11 (La Paz)", "Distrito 12 (Los Cabos)",
            "Distrito 13 (La Paz)", "Distrito 14 (La Paz)", "Distrito 15 (La Paz)", "Distrito 16 (Cabo San Lucas - Principal)"
        ]
        distrito_seleccionado = st.selectbox("📍 Selector de Distrito Electoral (BCS - Catálogo INE):", options=distritos_bcs, index=15)
    with col_ano_eleccion:
        st.markdown("<div class='stat-box' style='padding: 6px;'><div class='stat-label'>📅 Año Elección</div><div class='stat-num' style='font-size: 18px;'>2027</div></div>", unsafe_allow_html=True)

    col_izq_1, col_der_1 = st.columns(2)
    with col_izq_1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>⏱️ Relojes Operativos y Metas Distritales</div></div>", unsafe_allow_html=True)
        c_rp, c_rce = st.columns(2)
        with c_rp:
            st.markdown("<div class='stat-box'><div class='stat-label'>RP (Precampaña)</div><div class='stat-num' style='font-size: 16px;'>Activo</div></div>", unsafe_allow_html=True)
        with c_rce:
            st.markdown("<div class='stat-box'><div class='stat-label'>RCE (Proceso Elecc.)</div><div class='stat-num' style='font-size: 16px;'>En Curso</div></div>", unsafe_allow_html=True)

        vm_1, vm_2 = st.columns(2)
        with vm_1:
            st.markdown("<div class='stat-box'><div class='stat-label'>🗳️ Votos / Contabilidad</div><div class='stat-num'>9,315</div><div style='font-size: 10px; color: #cbd5e1;'>Meta: 14,204</div></div>", unsafe_allow_html=True)
        with vm_2:
            st.markdown("<div class='stat-box'><div class='stat-label'>🏠 Meta Casas (M/CA)</div><div class='stat-num'>115 / 159</div><div style='font-size: 10px; color: #38bdf8;'>72.3% Células</div></div>", unsafe_allow_html=True)

    with col_der_1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>🗺️ Mapa INE / Cartografía Táctica BCS</div></div>", unsafe_allow_html=True)
        df_t_mapa = pd.DataFrame([{"lat": 22.8905, "lon": -109.9167}, {"lat": 24.1426, "lon": -110.3128}])
        st.map(df_t_mapa, zoom=8, use_container_width=True)

    col_izq_2, col_der_2 = st.columns(2)
    with col_izq_2:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📈 Enlace Encuesta Estadística de Campo (Tracking Poll)</div></div>", unsafe_allow_html=True)
        df_tendencia = pd.DataFrame({
            'Mes': ['Oct 2026', 'Nov 2026', 'Dic 2026', 'Ene 2027', 'Feb 2027', 'Mar 2027', 'Abr 2027', 'May 2027', 'Jun 2027'],
            'Conocimiento (%)': [15, 22, 30, 42, 55, 68, 76, 84, 92],
            'Aceptación (%)': [10, 16, 25, 35, 48, 60, 69, 78, 88]
        }).set_index('Mes')
        st.line_chart(df_tendencia, height=140)

    with col_der_2:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>⚖️ Legislación y Asistente Gemini</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-box' style='padding: 26px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Blindaje Normativo Electoral</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 15px;'>Repositorio y Consultas Activas</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Panel Desplegable de Brigadistas
    st.markdown("<div class='caja-bloque' style='margin-top: 12px;'><div class='titulo-caja'>📋 Cédulas, Criterios de Campo & Gestión de Brigadistas</div></div>", unsafe_allow_html=True)
    if st.button("👥 Abrir / Cerrar Panel de Alta y Asignación de Brigadistas", use_container_width=True):
        st.session_state.ver_modal_brigadistas = not st.session_state.ver_modal_brigadistas

    if st.session_state.ver_modal_brigadistas:
        st.markdown("<div style='background-color:#111827; padding:18px; border-radius:10px; border:1px solid #38bdf8; margin-top:12px;'>", unsafe_allow_html=True)
        st.markdown("##### ➕ Alta, Registro y Asignación de Tareas a Brigadistas")
        with st.form("form_alta_brigadista_desplegable"):
            b_nom = st.text_input("Nombre del Brigadista / Encuestador:")
            b_cel = st.text_input("Celular / WhatsApp del Brigadista:")
            b_sec = st.text_input("Seccionales Asignadas:")
            link_w_brig = f"https://wa.me/52{b_cel}?text=Hola%20{urllib.parse.quote(b_nom)},%20tu%20tarea%20de%20campo%20está%20lista." if b_cel else "#"
            st.markdown(f'<a href="{link_w_brig}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: bold; margin-bottom: 10px;">📲 Enviar Tarea por WhatsApp</a>', unsafe_allow_html=True)
            st.form_submit_button("💾 Guardar Brigadista")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# VISTA 2: MÓDULO TERRITORIAL (COMPLETO)
# ==========================================
elif st.session_state.seccion_activa == "TERRITORIAL":
    st.markdown("## 👥 Módulo de Estructura Territorial: Casas Amigas (CA) y Redes")
    if st.button("⬅️ Volver al Tablero", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    tab_t1, tab_t2, tab_t3 = st.tabs(["🏠 Registro Casas Amigas (CA)", "🤝 Coanfitriones (C1-C5)", "👥 Registro Simpatizantes"])
    
    with tab_t1:
        with st.form("form_anfitrion_principal"):
            st.markdown("### 🏠 Alta y Catálogo de Casas Amigas")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Nombre Completo del Anfitrión (CA)")
                st.text_input("Teléfono Celular / WhatsApp")
                st.text_input("Seccional Electoral")
            with c2:
                st.text_input("Domicilio / Calle y Número")
                st.text_input("Ubicación GPS (Enlace Google Maps)")
                st.selectbox("Capacidad Estimada de Reunión:", ["10 a 20 personas", "20 a 50 personas", "Más de 50 personas"])
            st.form_submit_button("💾 Guardar Casa Amiga en Sistema")

    with tab_t2:
        with st.form("form_coanfitriones"):
            st.markdown("### 🤝 Registro de Coanfitriones por Célula")
            cc1, cc2 = st.columns(2)
            with cc1:
                st.text_input("Nombre del Coanfitrión (C1, C2, C3, C4 o C5)")
                st.text_input("Celular de Contacto")
            with cc2:
                st.text_input("Asociado a Casa Amiga (Anfitrión Principal)")
                st.selectbox("Nivel de Operación Celular:", ["C1 - Enlace Directo", "C2 - Movilización", "C3 - Promoción", "C4 - Logística", "C5 - Redes"])
            st.form_submit_button("💾 Guardar Coanfitrión")

    with tab_t3:
        with st.form("form_simpatizantes_terr"):
            st.markdown("### 👥 Registro Exprés de Simpatizantes de Base")
            s1, s2 = st.columns(2)
            with s1:
                st.text_input("Nombre Completo del Simpatizante")
                st.text_input("Teléfono Celular / WhatsApp")
            with s2:
                st.text_input("Seccional / Manzana")
                st.selectbox("Compromiso de Voto:", ["Seguro / Duro", "Dudoso / Persuasión", "Estructura Operativa"])
            st.form_submit_button("💾 Registrar Simpatizante")

# ==========================================
# VISTA 3: EVENTO MASIVO (COMPLETO)
# ==========================================
elif st.session_state.seccion_activa == "EVENTO":
    st.markdown("## 🎪 Centro de Control: Evento Masivo y Cierre de Campaña")
    if st.button("⬅️ Volver al Tablero", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📍 Configuración de Sede, Logística y Acarreo</div></div>", unsafe_allow_html=True)
    ev_1, ev_2 = st.columns(2)
    with ev_1:
        st.text_input("Nombre del Evento Masivo", "Gran Cierre de Campaña Distrital")
        st.text_input("Ubicación GPS / Enlace Google Maps", "https://maps.google.com")
        st.text_input("Meta de Asistencia Estimada", "3,500 asistentes")
    with ev_2:
        st.text_input("Responsable de Logística y Audio", "Comisión Operativa")
        st.text_input("Coordinador de Transporte / Unidades", "Ruta Sur / Norte")
        st.selectbox("Estatus del Permiso Municipal", ["Tramitado", "Aprobado", "Pendiente de Notificación"])

    if st.button("🚀 Sincronizar Logística de Evento Masivo", use_container_width=True):
        st.success("✅ ¡Parámetros de evento masivo guardados y distribuidos al Cuarto de Guerra!")

# ==========================================
# VISTA 4: DÍA D (COMPLETO CON RGS, RCS Y BOTÓN DE PÁNICO)
# ==========================================
elif st.session_state.seccion_activa == "DIA_D":
    st.markdown("## 🚨 Operación Día D: Monitoreo, Casillas y Defensa del Voto")
    if st.button("⬅️ Volver al Tablero", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    tab_1, tab_2, tab_3 = st.tabs(["🏛️ Monitoreo de Casillas", "🛡️ RGs y RCs (Estructura)", "🚨 Botón de Pánico y Alertas"])
    with tab_1:
        st.markdown("### 🏛️ Reporte de Instalación y Votación en Casillas")
        st.markdown("Control en tiempo real de apertura de paquetes electorales, incidentes de casilla y conteo preliminar.")
        st.selectbox("Filtrar por Tipo de Casilla:", ["Todas las Casillas", "Básicas", "Contiguas", "Extraordinarias", "Especiales"])
        st.markdown("<div class='stat-box'>📊 Estatus General: <b>0 de 184 Casillas Instaladas oficialmente (Simulador en espera de apertura)</b></div>", unsafe_allow_html=True)

    with tab_2:
        st.markdown("### 🛡️ Directorio y Asignación de RGs (Representantes Generales) y RCs (Casilla)")
        with st.form("form_rg_rc"):
            rc1, rc2 = st.columns(2)
            with rc1:
                st.text_input("Nombre del Representante (RG o RC)")
                st.text_input("Celular de Enlace Operativo")
            with rc2:
                st.text_input("Seccional Asignada / Casilla")
                st.selectbox("Rol Asignado:", ["Representante General (RG)", "Representante de Casilla Propietario (RC)", "Suplente"])
            st.form_submit_button("💾 Guardar Enlace en Estructura Día D")

    with tab_3:
        st.markdown("<div style='background-color:#450a0a; padding:20px; border-radius:10px; border: 1px solid #dc2626;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#fca5a5; margin-top:0;'>🚨 Botón de Pánico Estratégico (Emergencia 911 / Jurídico)</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#f8fafc;'>Utilice este módulo únicamente ante incidentes graves, detenciones arbitrarias o coacción en casilla que requiera intervención jurídica inmediata del Cuarto de Guerra.</p>", unsafe_allow_html=True)
        cel_emergencia = st.text_input("Celular de Enlace Jurídico / Emergencia:", "6240000000")
        incidencia_reporte = st.text_area("Descripción Breve del Incidente en Casilla:")
        
        msg_panico = f"¡EMERGENCIA EN CASILLA! Incidente reportado: {incidencia_reporte}"
        link_panico = f"https://wa.me/52{cel_emergencia}?text={urllib.parse.quote(msg_panico)}"
        st.markdown(f'<a href="{link_panico}" target="_blank" style="display: block; text-align: center; background-color: #dc2626; color: white; padding: 12px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 16px; margin-top: 10px;">🚨 ACTIVAR ALERTA URGENTE POR WHATSAPP</a>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# VISTA 5: REDES SOCIALES (COMPLETO)
# ==========================================
elif st.session_state.seccion_activa == "REDES":
    st.markdown("## 📱 Módulo de Redes Sociales, Difusión y Cascada Operativa")
    if st.button("⬅️ Volver al Tablero", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📡 Canales Oficiales Conectados</div></div>", unsafe_allow_html=True)
    st.markdown("* 📘 **Facebook Oficial:** Sincronizado (Monitoreo de impresiones y alcance)")
    st.markdown("* 📸 **Instagram:** Sincronizado (Campañas visuales de territorio)")
    st.markdown("* 🎵 **TikTok:** Sincronizado (Contenido dinámico y juventud)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📤 Envío Masivo de Mensajes en Cascada (WhatsApp)")
    with st.form("form_difusion_masiva"):
        grupo_destino = st.selectbox("Grupo de Difusión Destino:", ["Estructura General (C1-C5)", "Casas Amigas", "Brigadistas Activos", "Simpatizantes"])
        texto_difusion = st.text_area("Mensaje Operativo a Difundir:", "Compañeros, iniciamos la jornada de movilización territorial. ¡A ganar!")
        cel_prueba_dif = st.text_input("Celular de Prueba:", "6240000000")
        link_w_dif = f"https://wa.me/52{cel_prueba_dif}?text={urllib.parse.quote(texto_difusion)}"
        st.markdown(f'<a href="{link_w_dif}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-bottom: 10px;">📲 Enviar Mensaje de Prueba por WhatsApp</a>', unsafe_allow_html=True)
        st.form_submit_button("🚀 Programar Difusión en Cascada")

# ==========================================
# VISTA 6: SIMULADOR DE ENCUESTAS (TRACKING POLL - MÓVIL ALTO CONTRASTE)
# ==========================================
elif st.session_state.seccion_activa == "SIMULADOR":
    st.markdown("## 📱 Simulador Móvil: Formato Oficial de Encuesta (Tracking Poll)")
    if st.button("⬅️ Volver al Tablero", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    col_sim_izq, col_sim_cen, col_sim_der = st.columns([1, 2, 1])
    with col_sim_cen:
        st.markdown("<div class='mobile-simulator'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#38bdf8; margin:0; text-align:center;'>📊 Tracking Poll</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:11px; color:#cbd5e1; text-align:center; margin-bottom:15px;'>Estudio de Opinión Pública BCS 2027</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
        
        with st.form("form_tracking_poll_oficial"):
            st.markdown("<p style='color:#f8fafc; font-weight:bold;'>Brigadista Encuestador:</p>", unsafe_allow_html=True)
            brig_input = st.text_input("Brigadista Encuestador:", value="Carlos Mendoza", label_visibility="collapsed")
            
            st.markdown("<p style='color:#f8fafc; font-weight:bold; margin-top:8px;'>Seccional Electoral (Ej: 400):</p>", unsafe_allow_html=True)
            secc_input = st.text_input("Seccional Electoral (Ej: 400):", value="400", label_visibility="collapsed")
            
            st.markdown("<p style='color:#f8fafc; font-weight:bold; margin-top:10px;'>1. Sabe usted que este año hay elecciones en BCS?</p>", unsafe_allow_html=True)
            p1 = st.radio("1. Sabe usted que este año hay elecciones en BCS?", ["Sí", "No"], horizontal=True, label_visibility="collapsed")
            
            st.markdown("<p style='color:#f8fafc; font-weight:bold; margin-top:10px;'>2. Conoce usted al candidato?</p>", unsafe_allow_html=True)
            p2 = st.radio("2. Conoce usted al candidato?", ["Sí", "No"], horizontal=True, label_visibility="collapsed")
            
            st.markdown("<p style='color:#f8fafc; font-weight:bold; margin-top:10px;'>3. Conoce el partido que representa?</p>", unsafe_allow_html=True)
            p3 = st.radio("3. Conoce el partido que representa?", ["Sí", "No"], horizontal=True, label_visibility="collapsed")
            
            st.markdown("<p style='color:#f8fafc; font-weight:bold; margin-top:10px;'>4. Si hoy fuera la elección, votaría por nuestro candidato?</p>", unsafe_allow_html=True)
            p4 = st.radio("4. Si hoy fuera la elección, votaría por nuestro candidato?", ["Sí", "No", "Tiene duda"], horizontal=True, label_visibility="collapsed")
            
            st.markdown("<p style='color:#f8fafc; font-weight:bold; margin-top:10px;'>5. Votaría usted por el partido político en esta elección?</p>", unsafe_allow_html=True)
            p5 = st.radio("5. Votaría usted por el partido político en esta elección?", ["Sí", "No", "Tiene duda"], horizontal=True, label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            btn_env = st.form_submit_button("🚀 Enviar Encuesta a la Nube", use_container_width=True)
            if btn_env:
                st.success("✅ ¡Encuesta aplicada con éxito! Datos sincronizados.")

        st.markdown("</div>", unsafe_allow_html=True)