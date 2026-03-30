import streamlit as st
import pandas as pd
import datetime
import gspread
import json

# 1. Configuración de la página y Estilo Dark Fintech
st.set_page_config(page_title="Finanzas App", page_icon="📱", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #1a1a1a; }
    .stApp, h1, h2, h3, p, span, label, div[data-testid="stMarkdownContainer"] { color: #ffffff !important; }
    div[data-testid="metric-container"] {
        background-color: #2a2a2a; border-radius: 20px; padding: 15px; border: 1px solid #303030;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    div[data-testid="metric-container"] label { color: #8a8a8a !important; }
    div[data-testid="metric-container"] div { color: #c8ff00 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. TU CATÁLOGO
catalogo = {
    "Cloro": {"costo": 3.50, "precio": 6.00},
    "Maestro limpio": {"costo": 5.00, "precio": 12.00},
    "Lavanda": {"costo": 5.00, "precio": 12.00},
    "Mar fresco": {"costo": 5.00, "precio": 12.00},
    "Menta": {"costo": 5.00, "precio": 12.00},
    "Violeta": {"costo": 5.00, "precio": 12.00},
    "Pino blanco": {"costo": 6.00, "precio": 12.00},
    "Fabuloso canela": {"costo": 5.00, "precio": 12.00},
    "Carisma": {"costo": 7.00, "precio": 18.00},
    "Primavera": {"costo": 7.00, "precio": 18.00},
    "Ensueño": {"costo": 7.00, "precio": 18.00},
    "Dawny azul": {"costo": 7.00, "precio": 18.00},
    "Lavanderia": {"costo": 7.00, "precio": 20.00},
    "Ariel doble poder": {"costo": 9.00, "precio": 20.00},
    "Roma": {"costo": 9.00, "precio": 20.00},
    "Mas color": {"costo": 9.00, "precio": 20.00},
    "Zote": {"costo": 9.00, "precio": 20.00},
    "Persil": {"costo": 9.00, "precio": 20.00},
    "Brazo": {"costo": 9.00, "precio": 20.00},
    "Mas negro": {"costo": 9.00, "precio": 20.00},
    "Vanish gel": {"costo": 9.00, "precio": 20.00},
    "Cereza manos": {"costo": 9.00, "precio": 20.00},
    "Salvo": {"costo": 12.00, "precio": 22.00},
    "Axion": {"costo": 12.00, "precio": 22.00},
    "Detercon": {"costo": 12.00, "precio": 22.00},
    "Shampoo con cera": {"costo": 15.00, "precio": 25.00}
}

costos_fijos = 2000.00
inversion_total = 5700.00 

# --- CONEXIÓN MÁGICA A GOOGLE SHEETS ---
@st.cache_resource
def conectar_google():
    try:
        credenciales_dict = json.loads(st.secrets["google_credentials"])
        cuenta = gspread.service_account_from_dict(credenciales_dict)
        doc = cuenta.open("Base_Datos_Niki")
        return doc
    except Exception as e:
        st.error(f"⚠️ Error de conexión a Google: {e}")
        st.stop()

doc_google = conectar_google()
# Conectamos a ambas pestañas
pestana_ventas = doc_google.get_worksheet(0) # La primera hoja (Ventas)
try:
    pestana_gastos = doc_google.worksheet("Gastos") # La nueva hoja
except:
    st.error("⚠️ No se encontró la pestaña 'Gastos' en tu Google Sheets. Créala primero.")
    st.stop()

def cargar_datos(pestana, columnas_default):
    datos = pestana.get_all_records()
    if datos:
        return pd.DataFrame(datos)
    return pd.DataFrame(columns=columnas_default)

def guardar_datos(pestana, df_a_guardar):
    pestana.clear()
    lista_datos = [df_a_guardar.columns.values.tolist()] + df_a_guardar.values.tolist()
    pestana.update(lista_datos)

# 3. LA "MEMORIA" DE TU APLICACIÓN
if 'historial_ventas' not in st.session_state:
    st.session_state.historial_ventas = cargar_datos(pestana_ventas, ["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"])
if 'historial_gastos' not in st.session_state:
    st.session_state.historial_gastos = cargar_datos(pestana_gastos, ["Fecha", "Concepto", "Monto ($)", "Categoria"])

# --- MOTOR DE CÁLCULO ---
df_ventas = st.session_state.historial_ventas.copy()
df_gastos = st.session_state.historial_gastos.copy()

ingresos_totales = 0.0
ganancias_totales = 0.0
gastos_totales = 0.0

if not df_ventas.empty:
    df_ventas["Precio"] = df_ventas["Producto"].map(lambda x: catalogo[x]["precio"] if x in catalogo else 0)
    df_ventas["Costo"] = df_ventas["Producto"].map(lambda x: catalogo[x]["costo"] if x in catalogo else 0)
    df_ventas["Litros"] = pd.to_numeric(df_ventas["Litros"], errors='coerce').fillna(0)
    df_ventas["Ingreso ($)"] = df_ventas["Litros"] * df_ventas["Precio"]
    df_ventas["Ganancia ($)"] = df_ventas["Litros"] * (df_ventas["Precio"] - df_ventas["Costo"])
    ingresos_totales = df_ventas["Ingreso ($)"].sum()
    ganancias_totales = df_ventas["Ganancia ($)"].sum()

if not df_gastos.empty:
    df_gastos["Monto ($)"] = pd.to_numeric(df_gastos["Monto ($)"], errors='coerce').fillna(0)
    gastos_totales = df_gastos["Monto ($)"].sum()

# LÓGICA DE CAJA: Todo lo que entró de ventas MENOS todo lo que salió de gastos
dinero_en_caja = ingresos_totales - gastos_totales

# 4. INTERFAZ VISUAL: DASHBOARD PRINCIPAL
st.title("📱 Productos de Limpieza Niki")

st.subheader("Flujo de Efectivo")
col_caja, col_gastos = st.columns(2)
with col_caja:
    st.metric(label="💵 Dinero en Caja", value=f"${dinero_en_caja:,.2f}")
with col_gastos:
    st.metric(label="🔻 Gastos Totales", value=f"${gastos_totales:,.2f}")

st.divider()

st.subheader("Métricas de Negocio")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Ingresos (Ventas)", value=f"${ingresos_totales:,.2f}")
with col2:
    st.metric(label="Ganancia Neta", value=f"${ganancias_totales:,.2f}")
with col3:
    st.metric(label="Inversión a Recuperar", value=f"${inversion_total:,.2f}")

# 5. MÓDULO DE VENTAS Y GASTOS (Pestañas)
st.divider()
tab_ventas, tab_gastos = st.tabs(["🛒 Registrar Venta", "💸 Registrar Salida de Efectivo"])

with tab_ventas:
    fecha_venta = st.date_input("Fecha de la venta", datetime.date.today())
    col_prod, col_litros = st.columns(2)
    with col_prod:
        producto_seleccionado = st.selectbox("¿Qué vendiste?", list(catalogo.keys()))
    with col_litros:
        litros = st.number_input("Litros vendidos", min_value=0.01, value=1.00, step=0.50, format="%.2f")

    if st.button("Registrar Venta", type="primary"):
        nueva_venta = pd.DataFrame([{
            "Fecha": fecha_venta.strftime("%d/%m/%Y"),
            "Producto": producto_seleccionado,
            "Litros": litros,
            "Ingreso ($)": "",
            "Ganancia ($)": ""
        }])
        st.session_state.historial_ventas = pd.concat([st.session_state.historial_ventas, nueva_venta], ignore_index=True)
        guardar_datos(pestana_ventas, st.session_state.historial_ventas)
        st.toast(f"✅ Venta de {producto_seleccionado} registrada correctamente.")
        st.rerun() 

with tab_gastos:
    st.markdown("Registra aquí compras de envases, pasajes, material u otros.")
    fecha_gasto = st.date_input("Fecha del gasto", datetime.date.today())
    concepto = st.text_input("Concepto (Ej. Compra de botellas de litro)")
    col_monto, col_cat = st.columns(2)
    with col_monto:
        monto_gasto = st.number_input("Monto gastado ($)", min_value=1.0, value=50.0, step=10.0, format="%.2f")
    with col_cat:
        categoria = st.selectbox("Categoría", ["Operativo", "Proveedor", "Servicio", "Pasajes", "Otro"])

    if st.button("Registrar Gasto", type="primary"):
        if concepto.strip() == "":
            st.warning("⚠️ Por favor escribe un concepto para el gasto.")
        else:
            nuevo_gasto = pd.DataFrame([{
                "Fecha": fecha_gasto.strftime("%d/%m/%Y"),
                "Concepto": concepto,
                "Monto ($)": monto_gasto,
                "Categoria": categoria
            }])
            st.session_state.historial_gastos = pd.concat([st.session_state.historial_gastos, nuevo_gasto], ignore_index=True)
            guardar_datos(pestana_gastos, st.session_state.historial_gastos)
            st.toast(f"💸 Gasto de ${monto_gasto} registrado.")
            st.rerun()

# 6. TABLAS DE CONSULTA
st.divider()
st.subheader("📋 Consultas Rápidas")
tab_tabla_ventas, tab_tabla_gastos = st.tabs(["Agenda de Ventas", "Historial de Gastos"])

with tab_tabla_ventas:
    if not df_ventas.empty:
        st.dataframe(df_ventas[["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"]], use_container_width=True)
    else:
        st.info("Aún no hay ventas registradas.")

with tab_tabla_gastos:
    if not df_gastos.empty:
        st.dataframe(df_gastos[["Fecha", "Concepto", "Monto ($)", "Categoria"]], use_container_width=True)
    else:
        st.info("Aún no hay gastos registrados.")
