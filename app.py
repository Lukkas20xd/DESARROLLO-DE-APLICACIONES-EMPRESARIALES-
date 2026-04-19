import sqlite3
import streamlit as st
import pandas as pd
import re
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Clientes PRO", layout="wide")

# --- CREDENCIALES ---
CREDENTIALS = {
    "admin": {"password": "admin123", "role": "admin"},
    "cliente": {"password": "cliente123", "role": "cliente"}
}

# --- AUTENTICACIÓN ---
def login():
    st.title("Acceso al Sistema")
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Nombre de Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")
        
        if submit:
            if username in CREDENTIALS and CREDENTIALS[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = CREDENTIALS[username]["role"] 
                st.success("Acceso concedido!")
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- VERIFICAR AUTENTICACIÓN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

# --- DISEÑO CSS PERSONALIZADO DARK MODE AVANZADO ---
st.markdown("""
    <style>
    /* Fondo general con gradiente animado */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        color: #f8fafc;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Personalización del Sidebar con glow */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
        border-right: 2px solid #6366f1;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
    }
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label {
        color: #a855f7 !important;
        font-weight: bold;
    }

    /* Estilo de Tarjetas avanzado con hover */
    .main-card {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        padding: 2.5rem;
        border-radius: 20px;
        border: 1px solid #475569;
        box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(99, 102, 241, 0.1);
        margin-bottom: 2rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .main-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(168, 85, 247, 0.1), transparent);
        transition: left 0.5s;
    }
    .main-card:hover::before {
        left: 100%;
    }
    .main-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px -5px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(168, 85, 247, 0.2);
    }

    /* Inputs con efectos de foco */
    .stTextInput>div>div>input {
        background: linear-gradient(145deg, #334155 0%, #475569 100%);
        color: white;
        border: 2px solid #6366f1;
        border-radius: 10px;
        padding: 0.8rem;
        transition: all 0.3s ease;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .stTextInput>div>div>input:focus {
        border-color: #a855f7;
        box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.2);
        transform: scale(1.02);
    }
    
    /* Botones con animación y glow */
    .stButton>button {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #6366f1 100%);
        background-size: 200% 200%;
        animation: buttonGlow 3s ease infinite;
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
    @keyframes buttonGlow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    .stButton>button:hover {
        transform: translateY(-2px) scale(1.05);
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.6);
    }

    /* Métricas con estilo */
    .metric-card {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #475569;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #a855f7;
    }
    .metric-label {
        color: #cbd5e1;
        font-size: 0.9rem;
    }

    /* Títulos y textos con gradiente */
    h1, h2, h3 {
        background: linear-gradient(90deg, #f1f5f9 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
    }
    p, label {
        color: #e2e8f0 !important;
    }
    
    /* Líneas divisorias con estilo */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #6366f1 50%, transparent 100%);
        margin: 2rem 0;
    }

    /* DataFrame con estilo */
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }
    .stDataFrame thead th {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        color: white;
        font-weight: bold;
    }
    .stDataFrame tbody tr:nth-child(even) {
        background-color: rgba(71, 85, 105, 0.3);
    }
    .stDataFrame tbody tr:hover {
        background-color: rgba(168, 85, 247, 0.1);
    }

    /* Expander con estilo */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #334155 0%, #475569 100%);
        border-radius: 10px;
        color: #f1f5f9 !important;
        font-weight: bold;
    }
    .streamlit-expanderContent {
        background-color: #1e293b;
        border-radius: 0 0 10px 10px;
        border: 1px solid #475569;
    }

    /* Scrollbar personalizado */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0f172a;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #6366f1 0%, #a855f7 100%);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #a855f7 0%, #6366f1 100%);
    }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
DB_PATH = "clientes.db"

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT NOT NULL UNIQUE,
            correo TEXT,
            telefono TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

conn = get_connection()

conn = get_connection()

# --- SIDEBAR CON INFO DE USUARIO ---
with st.sidebar:
    st.markdown("## Información de Sesión")
    st.write(f"**Usuario:** {st.session_state.username}")
    st.write(f"**Rol:** {st.session_state.role.title()}")
    st.write(f"**Fecha:** {datetime.now().strftime('%d/%m/%Y')}")
    st.divider()
    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

# --- DEFINIR FUNCIONES PARA CADA SECCIÓN ---
def registro_clientes():
    st.title("Registro de Clientes")
    st.markdown("### Ingrese la información del nuevo contacto")
    
    with st.container():
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        with st.form("form_nuevo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre Completo")
                rut = st.text_input("RUT (Sin puntos y con guion)")
            with col2:
                correo = st.text_input("Correo Electrónico")
                telefono = st.text_input("Teléfono de Contacto")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Registrar Cliente")
            
            if submit:
                if not nombre or not rut:
                    st.warning("Los campos Nombre y RUT son obligatorios.")
                else:
                    try:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO clientes (nombre, rut, correo, telefono) VALUES (?, ?, ?, ?)",
                                   (nombre.strip(), rut.strip(), correo.strip(), telefono.strip()))
                        conn.commit()
                        st.success(f"¡Excelente! {nombre} ha sido registrado.")
                        st.balloons()
                    except sqlite3.IntegrityError:
                        st.error("Error: Este RUT ya existe en el sistema.")
        st.markdown('</div>', unsafe_allow_html=True)

def reportes_lista():
    st.title("Base de Datos de Clientes")
    
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    
    if not df.empty:
        # Métricas rápidas con diseño avanzado
        st.markdown("### Estadísticas del Sistema")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(df)}</div>
                <div class="metric-label">Total Clientes</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            ultimo = df['nombre'].iloc[-1] if not df.empty else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{ultimo}</div>
                <div class="metric-label">Último Registro</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">Online</div>
                <div class="metric-label">Estado DB</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.dataframe(df.drop(columns=['id']), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar a Excel (CSV)", data=csv, file_name="clientes_pro.csv")
    else:
        st.info("Aún no hay datos para mostrar.")

def administrar_datos():
    st.title("Mantenimiento")
    st.write("Seleccione una acción para gestionar la base de datos.")
    
    with st.expander("Borrar un Cliente"):
        rut_borrar = st.text_input("Ingrese RUT para eliminar")
        if st.button("Confirmar Eliminación"):
            cur = conn.cursor()
            cur.execute("DELETE FROM clientes WHERE rut=?", (rut_borrar,))
            conn.commit()
            st.success("Registro eliminado.")

# --- PESTAÑAS BASADAS EN ROL ---
if st.session_state.role == "cliente":
    tab1 = st.tabs(["Registro de Clientes"])[0]
    with tab1:
        registro_clientes()
elif st.session_state.role == "admin":
    tab1, tab2, tab3 = st.tabs(["Registro de Clientes", "Reportes y Lista", "Administrar Datos"])
    with tab1:
        registro_clientes()
    with tab2:
        reportes_lista()
    with tab3:
        administrar_datos()

