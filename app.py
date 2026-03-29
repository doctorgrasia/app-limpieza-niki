import streamlit as st
import pandas as pd
import datetime
import gspread

# 1. Configuración de la página y Estilo
st.set_page_config(page_title="Finanzas App", page_icon="📱", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    .stApp, h1, h2, h3, p, span, label, div[data-testid="stMarkdownContainer"] { color: #FFFFFF !important; }
    div[data-testid="metric-container"] {
        background-color: #1E1E1E; border-radius: 15px; padding: 15px; border: 1px solid #333333;
    }
    div[data-testid="metric-container"] > div { color: #CCCCCC !important; }
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
        cuenta = gspread.service_account(filename="credenciales.json")
        hoja = cuenta.open("Base_Datos_Niki")
        return hoja.sheet1
    except Exception as e:
        st.error("⚠️ Error conectando a Google. Revisa que tu archivo se llame credenciales.json.")
        st.stop()

pestana = conectar_google()

def cargar_datos_nube():
    datos = pestana.get_all_records()
    if datos:
        return pd.DataFrame(datos)
    return pd.DataFrame(columns=["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"])

def guardar_datos_nube(df_a_guardar):
    pestana.clear()
    lista_datos = [df_a_guardar.columns.values.tolist()] + df_a_guardar.values.tolist()
    pestana.update(lista_datos)

# 3. LA "MEMORIA" DE TU APLICACIÓN
if 'historial_ventas' not in st.session_state:
    st.session_state.historial_ventas = cargar_datos_nube()

# --- MOTOR DE CÁLCULO ---
df = st.session_state.historial_ventas.copy()
ingresos_totales = 0.0
ganancias_totales = 0.0

if not df.empty:
    df["Precio"] = df["Producto"].map(lambda x: catalogo[x]["precio"] if x in catalogo else 0)
    df["Costo"] = df["Producto"].map(lambda x: catalogo[x]["costo"] if x in catalogo else 0)

    # Convertimos las columnas a números por si vienen como texto desde Google
    df["Litros"] = pd.to_numeric(df["Litros"], errors='coerce').fillna(0)
    df["Ingreso ($)"] = df["Litros"] * df["Precio"]
    df["Ganancia ($)"] = df["Litros"] * (df["Precio"] - df["Costo"])

    ingresos_totales = df["Ingreso ($)"].sum()
    ganancias_totales = df["Ganancia ($)"].sum()

# 4. INTERFAZ VISUAL: MÉTRICAS
st.title("📱 Mi Negocio - Productos de limpieza niki")

st.subheader("Estadísticas Acumuladas")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Ingresos Totales", value=f"${ingresos_totales:,.2f}")
with col2:
    st.metric(label="Ganancia Neta", value=f"${ganancias_totales:,.2f}")
with col3:
    st.metric(label="Inversión a Recuperar", value=f"${inversion_total:,.2f}")

st.divider()
st.subheader("📊 Análisis y Salud del Negocio")

st.write(f"**1. Meta Mensual (Costos Fijos: ${costos_fijos:,.2f})**")
progreso_mes = ganancias_totales / costos_fijos if costos_fijos > 0 else 0
st.progress(min(progreso_mes, 1.0))

st.write(f"**2. Recuperación de Inversión (Total: ${inversion_total:,.2f})**")
progreso_inversion = ganancias_totales / inversion_total if inversion_total > 0 else 0
st.progress(min(progreso_inversion, 1.0))

# 5. REGISTRO DE VENTAS
st.divider()
st.subheader("🛒 Registro de Ventas")

fecha_venta = st.date_input("Fecha de la venta", datetime.date.today())

col_prod, col_litros = st.columns(2)
with col_prod:
    producto_seleccionado = st.selectbox("¿Qué vendiste?", list(catalogo.keys()))
with col_litros:
    litros = st.number_input("Litros vendidos", min_value=0.01, value=1.00, step=0.50, format="%.2f")

if st.button("Registrar Venta"):
    # Guardamos sin calcular ingresos aquí, el Motor de Cálculo lo hará en la siguiente recarga
    nueva_venta = pd.DataFrame([{
        "Fecha": fecha_venta.strftime("%d/%m/%Y"),
        "Producto": producto_seleccionado,
        "Litros": litros,
        "Ingreso ($)": "",
        "Ganancia ($)": ""
    }])
    st.session_state.historial_ventas = pd.concat([st.session_state.historial_ventas, nueva_venta], ignore_index=True)
    guardar_datos_nube(st.session_state.historial_ventas)
    st.rerun() 

# 6. TABLA MÁGICA EDITABLE
if not df.empty:
    st.divider()
    st.subheader("📋 Tu Agenda de Ventas")
    
    columnas_mostrar = ["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"]

    df_editado = st.data_editor(
        df[columnas_mostrar],
        column_config={
            "Producto": st.column_config.SelectboxColumn("Producto", options=list(catalogo.keys()), required=True),
            "Litros": st.column_config.NumberColumn("Litros", min_value=0.01, step=0.50, format="%.2f", required=True),
            "Ingreso ($)": st.column_config.NumberColumn("Ingreso ($)", disabled=True), 
            "Ganancia ($)": st.column_config.NumberColumn("Ganancia ($)", disabled=True)
        },
        num_rows="dynamic",
        use_container_width=True
    )

    df_base_editado = df_editado[["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"]]
    if not df_base_editado.equals(st.session_state.historial_ventas):
        st.session_state.historial_ventas = df_base_editado
        guardar_datos_nube(st.session_state.historial_ventas)
        st.rerun()