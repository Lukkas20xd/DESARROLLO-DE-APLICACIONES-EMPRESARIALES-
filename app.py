import sqlite3
import streamlit as st
import pandas as pd
import re
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


def safe_rerun():
    """Intentar forzar un rerun de Streamlit de forma segura.
    Usa `st.experimental_rerun()` si está disponible; si no, actualiza
    los query params para provocar un rerun y detiene la ejecución.
    """
    try:
        # Normalmente disponible en muchas versiones
        st.experimental_rerun()
    except Exception:
        try:
            # Forzar cambio en query params provoca rerun en la mayoría de casos
            st.experimental_set_query_params(_rerun=datetime.now().timestamp())
        except Exception:
            st.info("Por favor, recargue la página para ver los cambios.")
        finally:
            st.stop()


# --- VALIDACIÓN DE ENTRADA ---
def validate_email(email: str) -> bool:
    if not email:
        return False
    pattern = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def normalize_rut(rut: str) -> str | None:
    """Normaliza y valida RUT chileno. Devuelve '12345678-K' o None si es inválido."""
    if not rut or not isinstance(rut, str):
        return None
    s = re.sub(r"[^0-9kK]", "", rut)
    if len(s) < 2:
        return None
    dv = s[-1].upper()
    nums = s[:-1]
    try:
        reversed_digits = list(map(int, reversed(nums)))
    except ValueError:
        return None
    mult = 2
    total = 0
    for d in reversed_digits:
        total += d * mult
        mult += 1
        if mult > 7:
            mult = 2
    mod = 11 - (total % 11)
    if mod == 11:
        expected = '0'
    elif mod == 10:
        expected = 'K'
    else:
        expected = str(mod)
    if expected == dv:
        return f"{nums}-{dv}"
    return None


def normalize_phone(phone: str) -> str | None:
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7 or len(digits) > 15:
        return None
    return digits

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
        # 2. Validación de Correo y RUT usando funciones más robustas
        elif correo and not validate_email(correo.strip()):
            st.error("Por favor, ingrese un correo electrónico válido.")
        else:
            rut_norm = normalize_rut(rut.strip())
            if not rut_norm:
                st.error("RUT/ID inválido. Verifique el número y el dígito verificador.")
            else:
                telefono_norm = normalize_phone(telefono.strip())
                if telefono and telefono_norm is None:
                    st.error("Teléfono inválido. Ingrese entre 7 y 15 dígitos.")
                else:
                    try:
                        cur = conn.cursor()
                        cur.execute(
                            """INSERT INTO clientes (nombre, rut, correo, telefono, creado_en) 
                               VALUES (?, ?, ?, ?, ?)""",
                            (nombre.strip(), rut_norm, correo.strip(), telefono_norm or "", datetime.now()),
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

# --- EDICIÓN DE CLIENTES ---
st.divider()
st.subheader("Editar cliente o eliminar cliente")

cur = conn.cursor()
cur.execute("SELECT id, nombre, rut, correo, telefono FROM clientes ORDER BY id DESC")
rows = cur.fetchall()

if rows:
    # Construimos opciones legibles para selección
    opciones = [f"{r[2]} - {r[1]}" for r in rows]
    map_id = {f"{r[2]} - {r[1]}": r for r in rows}

    edit_col, delete_col = st.columns(2)

    with edit_col.expander("Editar cliente"):
        seleccionado = st.selectbox("Seleccionar cliente", opciones, key="edit_select")
        registro = map_id.get(seleccionado)
        if registro:
            id_sel, nombre_sel, rut_sel, correo_sel, telefono_sel = registro
        else:
            st.info("Seleccione un cliente para editar.")
            registro = None
        st.write("**Datos actuales**")
        st.write(f"Nombre: {nombre_sel}  \nRUT: {rut_sel}")
        if registro:
            with st.form("form_editar", clear_on_submit=False):
                nombre_e = st.text_input("Nombre", value=nombre_sel)
                rut_e = st.text_input("RUT / ID", value=rut_sel)
                correo_e = st.text_input("Correo", value=correo_sel or "")
                telefono_e = st.text_input("Teléfono", value=telefono_sel or "")
                submitted_e = st.form_submit_button("Guardar cambios")
                if submitted_e:
                    if not nombre_e.strip() or not rut_e.strip():
                        st.error("Nombre y RUT/ID son obligatorios.")
                    elif correo_e and not validate_email(correo_e.strip()):
                        st.error("Por favor, ingrese un correo electrónico válido.")
                    else:
                        rut_norm = normalize_rut(rut_e.strip())
                        if not rut_norm:
                            st.error("RUT/ID inválido. Verifique el número y el dígito verificador.")
                        else:
                            telefono_norm = normalize_phone(telefono_e.strip())
                            if telefono_e and telefono_norm is None:
                                st.error("Teléfono inválido. Ingrese entre 7 y 15 dígitos.")
                            else:
                                try:
                                    cur.execute(
                                        """UPDATE clientes SET nombre=?, rut=?, correo=?, telefono=? WHERE id=?""",
                                        (nombre_e.strip(), rut_norm, correo_e.strip(), telefono_norm or "", id_sel),
                                    )
                                    conn.commit()
                                    st.success("Cliente actualizado correctamente.")
                                    safe_rerun()
                                except sqlite3.IntegrityError:
                                    st.error("Error: Ya existe un cliente con ese RUT/ID.")
                                except Exception as e:
                                    st.error(f"Error inesperado: {e}")

    with delete_col.expander("Eliminar cliente"):
        seleccionado_del = st.selectbox("Seleccionar cliente", opciones, key="del_select_exp")
        registro_del = map_id.get(seleccionado_del)
        if not registro_del:
            st.info("Seleccione un cliente para eliminar.")
        else:
            confirmar = st.checkbox("Confirmar eliminación", key="confirm_del")
            if st.button("Eliminar", key="btn_del"):
                if not confirmar:
                    st.error("Debe confirmar antes de eliminar.")
                else:
                    id_del = registro_del[0]
                    try:
                        cur.execute("DELETE FROM clientes WHERE id=?", (id_del,))
                        conn.commit()
                        st.success("Cliente eliminado correctamente.")
                        safe_rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar cliente: {e}")
else:
    st.info("Aún no hay clientes para editar.")

