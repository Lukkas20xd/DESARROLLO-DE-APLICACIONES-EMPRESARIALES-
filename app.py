import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

DB_PATH = "clientes.db"

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Aseguramos que la tabla tenga todos los campos necesarios
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT NOT NULL UNIQUE,
            correo TEXT,
            telefono TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn

conn = get_connection()

st.set_page_config(page_title="Registro de Clientes", layout="wide")
st.title("Gestión de Registro de Clientes")

# --- FORMULARIO DE ENTRADA ---
with st.form("form_agregar", clear_on_submit=True):
    st.subheader("Agregar nuevo cliente")
    col1, col2 = st.columns(2)
    
    with col1:
        nombre = st.text_input("Nombre Completo")
        rut = st.text_input("RUT / ID")
    
    with col2:
        correo = st.text_input("Correo Electrónico")
        telefono = st.text_input("Teléfono")
        
    submitted = st.form_submit_button("Guardar cliente")

    if submitted:
        # 1. Validación de campos vacíos
        if not nombre.strip() or not rut.strip():
            st.error("Nombre y RUT/ID son obligatorios.")
        
        # 2. Validación de Correo (Nueva decisión de desarrollo)
        elif correo and "@" not in correo:
            st.error("Por favor, ingrese un correo electrónico válido (debe contener '@').")
            
        # 3. Validación de RUT (Simple: mínimo de caracteres)
        elif len(rut.strip()) < 8:
            st.error("El RUT/ID parece demasiado corto. Verifíquelo.")
            
        else:
            try:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO clientes (nombre, rut, correo, telefono, creado_en) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (nombre.strip(), rut.strip(), correo.strip(), telefono.strip(), datetime.now()),
                )
                conn.commit()
                st.success(f"Cliente {nombre} guardado correctamente.")
                st.balloons()
            except sqlite3.IntegrityError:
                # Esto evita duplicados en la base de datos
                st.error("Error: Ya existe un cliente con ese RUT/ID.")
            except Exception as e:
                st.error(f"Error inesperado: {e}")

# --- VISUALIZACIÓN DE DATOS ---
st.divider()
st.subheader("Lista de Clientes Registrados")

# Consulta para mostrar los datos
query = "SELECT nombre as 'Nombre', rut as 'RUT/ID', correo as 'Correo', telefono as 'Teléfono', creado_en as 'Fecha Registro' FROM clientes ORDER BY id DESC"
df = pd.read_sql_query(query, conn)

if not df.empty:
    # Mostramos la tabla con un buscador integrado de Streamlit
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Opción para descargar los datos en CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar reporte (CSV)",
        data=csv,
        file_name="clientes_registrados.csv",
        mime="text/csv",
    )
else:
    st.info("Aún no hay clientes registrados.")
