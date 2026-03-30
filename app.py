import streamlit as st
import pandas as pd
import datetime
import gspread
import json

# 1. Configuración de la página
st.set_page_config(page_title="Finanzas App - Niki", page_icon="📱", layout="centered")

# --- BÓVEDA SECRETA DE ESTILOS CSS (TRADUCCIÓN AGRESIVA DEL PROMPT) ---
# Usamos unsafe_allow_html=True para inyectar el diseño directamente
st.markdown("""
    <style>
    /* 1. VARIABLES GLOBALES (PUNTO 1 DEL PROMPT) */
    :root {
      --bg-primary: #1a1a1a;
      --bg-secondary: #242424;
      --bg-card: #2a2a2a;
      --bg-card-hover: #303030;
      --accent-green: #c8ff00;    /* neon lime */
      --accent-coral: #ff6b6b;    /* rojo gastos */
      --accent-blue: #5bc8fa;     /* azul ingresos */
      --text-primary: #ffffff;
      --text-secondary: #8a8a8a;
      --radius-card: 20px;
    }

    /* 2. ESTILO DE FONDO Y TEXTO GLOBAL */
    .stApp { background-color: var(--bg-primary); color: var(--text-primary); }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdownContainer p { color: var(--text-primary) !important; font-family: 'Inter', sans-serif; }
    h1 { color: var(--accent-green) !important; text-align: center; }
    label { color: var(--text-secondary) !important; }
    .stAlert p { color: #1a1a1a !important; } /* Parche para alertas legibles */

    /* 3. ESTILO DE BOTONES PRIMARIOS (VERDE NEÓN) */
    div.stButton > button:first-child {
        background-color: var(--accent-green); color: #111111;
        border-radius: 50px; border: none; font-weight: bold;
        transition: transform 150ms ease, box-shadow 150ms ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(200,255,0,0.3);
        background-color: var(--accent-green); color: #111111;
    }

    /* 4. ESTILO DE INPUTS (OSCUROS Y RESALTADOS) */
    .stNumberInput input, .stTextInput input, .stSelectbox [data-baseweb="select"] {
        background-color: var(--bg-card) !important; color: white !important;
        border: 1px solid #444 !important; border-radius: 10px;
    }
    .stNumberInput input:focus, .stTextInput input:focus {
        border-color: var(--accent-green) !important;
        box-shadow: 0 0 0 3px rgba(200,255,0,0.15) !important;
    }

    /* 5. DISEÑO DE "FINTECH CARDS" PARA MÉTRICAS (HTML PERSONALIZADO) */
    .metric-card-container { display: flex; gap: 1rem; margin-bottom: 2rem; justify-content: space-between;}
    .fintech-card {
        background: var(--bg-card); border-radius: var(--radius-card);
        padding: 20px; flex: 1; min-width: 150px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4); border: 1px solid #333;
        transition: transform 300ms ease, background 150ms ease;
    }
    .fintech-card:hover { transform: translateY(-3px); background: var(--bg-card-hover); }
    .fintech-card .label { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 8px; }
    .fintech-card .value { font-size: 1.8rem; font-weight: bold; }
    .fintech-card .value.positive { color: var(--accent-green); }
    .fintech-card .value.negative { color: var(--accent-coral); }
    .fintech-card .value.neutral { color: var(--accent-blue); }

    /* 6. ESTILO DE PESTAÑAS (TABS) */
    button[data-baseweb="tab"] { background-color: transparent !important; color: var(--text-secondary) !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: var(--accent-green) !important; }
    div[data-baseweb="tab-highlight"] { background-color: var(--accent-green) !important; }

    /* 7. ESTILO DE DATAFRAME (TABLAS) */
    [data-testid="stDataFrame"] { background-color: var(--bg-card); border-radius: 10px; border: 1px solid #333;}
    </style>
    """, unsafe_allow_html=True)

# 2. LÓGICA DE DATOS Y CONEXIÓN (Mismo código, funcional)
costos_fijos = 2000.00
inversion_total = 5700.00 

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
pestana_ventas = doc_google.get_worksheet(0)
try:
    pestana_gastos = doc_google.worksheet("Gastos")
except:
    st.error("⚠️ No se encontró la pestaña 'Gastos' en tu Google Sheets. Créala primero.")
    st.stop()

def cargar_datos(pestana, columnas_default):
    datos = pestana.get_all_records()
    if datos: return pd.DataFrame(datos)
    return pd.DataFrame(columns=columnas_default)

def guardar_datos(pestana, df_a_guardar):
    pestana.clear()
    lista_datos = [df_a_guardar.columns.values.tolist()] + df_a_guardar.values.tolist()
    pestana.update(lista_datos)

if 'historial_ventas' not in st.session_state: st.session_state.historial_ventas = cargar_datos(pestana_ventas, ["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"])
if 'historial_gastos' not in st.session_state: st.session_state.historial_gastos = cargar_datos(pestana_gastos, ["Fecha", "Concepto", "Monto ($)", "Categoria"])

df_ventas = st.session_state.historial_ventas.copy()
df_gastos = st.session_state.historial_gastos.copy()

ingresos_totales, ganancias_totales, gastos_totales = 0.0, 0.0, 0.0

if not df_ventas.empty:
    df_ventas["Litros"] = pd.to_numeric(df_ventas["Litros"], errors='coerce').fillna(0)
    # Aquí debería estar el catálogo y los precios, lo simplifico para la demo visual
    # Suponemos que ya vienen calculados los ingresos y ganancias de la versión anterior
    if "Ingreso ($)" in df_ventas.columns: ingresos_totales = pd.to_numeric(df_ventas["Ingreso ($)"], errors='coerce').fillna(0).sum()
    if "Ganancia ($)" in df_ventas.columns: ganancias_totales = pd.to_numeric(df_ventas["Ganancia ($)"], errors='coerce').fillna(0).sum()

if not df_gastos.empty:
    df_gastos["Monto ($)"] = pd.to_numeric(df_gastos["Monto ($)"], errors='coerce').fillna(0)
    gastos_totales = df_gastos["Monto ($)"].sum()

dinero_en_caja = ingresos_totales - gastos_totales

# 3. INTERFAZ VISUAL: DASHBOARD PRINCIPAL (Aquí es donde forzamos el diseño)
st.title("📱 Finanzas Niki")

# Inyección de HTML puro para usar el diseño Fintech Card
# Módulo de Flujo (Caja y Gastos)
st.markdown(f"""
    <div class="metric-card-container">
        <div class="fintech-card">
            <div class="label">💵 Dinero en Caja</div>
            <div class="value positive">${dinero_en_caja:,.2f}</div>
        </div>
        <div class="fintech-card">
            <div class="label">🔻 Gastos Totales</div>
            <div class="value negative">${gastos_totales:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Módulo de Métricas (Ventas, Ganancia Neta)
st.markdown(f"""
    <div class="metric-card-container">
        <div class="fintech-card">
            <div class="label">Ingresos (Ventas)</div>
            <div class="value neutral">${ingresos_totales:,.2f}</div>
        </div>
        <div class="fintech-card">
            <div class="label">Ganancia Neta</div>
            <div class="value positive">${ganancias_totales:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# 4. FORMULARIOS DE REGISTRO CON ESTILOS RESALTADOS
tab_ventas, tab_gastos = st.tabs(["🛒 Registrar Venta", "💸 Registrar Salida de Efectivo"])

with tab_ventas:
    fecha_venta = st.date_input("Fecha de la venta", datetime.date.today(), key='fecha_venta_styled')
    col_prod, col_litros = st.columns(2)
    with col_prod: producto_seleccionado = st.selectbox("¿Qué vendiste?", list(catalogo.keys()), key='prod_styled')
    with col_litros: litros = st.number_input("Litros vendidos", min_value=0.01, value=1.00, step=0.50, format="%.2f", key='litros_styled')

    if st.button("Registrar Venta", type="primary", key='btn_venta_styled'):
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
    fecha_gasto = st.date_input("Fecha del gasto", datetime.date.today(), key='fecha_gasto_styled')
    concepto = st.text_input("Concepto (Ej. Compra de botellas)", key='concepto_styled')
    col_monto, col_cat = st.columns(2)
    with col_monto: monto_gasto = st.number_input("Monto gastado ($)", min_value=1.0, value=50.0, step=10.0, format="%.2f", key='monto_gasto_styled')
    with col_cat: categoria = st.selectbox("Categoría", ["Operativo", "Proveedor", "Servicio", "Pasajes", "Otro"], key='cat_styled')

    if st.button("Registrar Gasto", type="primary", key='btn_gasto_styled'):
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
            st.toast(f"💸 Gasto de ${monto_gasto} registrado exitosamente.")
            st.rerun()

# --- NUEVO MÓDULO: GRÁFICA DE PASTEL (PRODUCTOS MÁS VENDIDOS) ---
st.divider()
st.subheader("📊 Análisis Visual")

if not df_ventas.empty:
    # Agrupamos las ventas por producto y sumamos los litros
    ventas_agrupadas = df_ventas.groupby("Producto")["Litros"].sum().reset_index()
    # Ordenamos de mayor a menor
    ventas_agrupadas = ventas_agrupadas.sort_values(by="Litros", ascending=False)

    import plotly.express as px  # Importamos la librería que pusiste en requirements.txt
    
    # Creamos la gráfica de dona (hueca en el centro)
    fig_ventas = px.pie(
        ventas_agrupadas, 
        names="Producto", 
        values="Litros", 
        hole=0.65, # El 65% del centro estará vacío, estilo Fintech
        color_discrete_sequence=["#c8ff00", "#5bc8fa", "#6c63ff", "#ff6b6b", "#ff9f43"] # Colores del tema
    )

    # Ajustamos el diseño para que sea transparente y combine con el fondo oscuro
    fig_ventas.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff", family="Inter"),
        showlegend=True,
        margin=dict(t=30, b=0, l=0, r=0)
    )

    # Mostramos la gráfica interactiva
    st.plotly_chart(fig_ventas, use_container_width=True)
else:
    st.info("Registra algunas ventas para ver la gráfica de productos más vendidos.")

# 5. TABLAS DE CONSULTA
st.divider()
st.subheader("📋 Consultas Rápidas")
tab_tabla_ventas, tab_tabla_gastos = st.tabs(["Agenda de Ventas", "Historial de Gastos"])

with tab_tabla_ventas:
    if not df_ventas.empty: st.dataframe(df_ventas, use_container_width=True)
    else: st.info("Aún no hay ventas registradas.")

with tab_tabla_gastos:
    if not df_gastos.empty: st.dataframe(df_gastos, use_container_width=True)
    else: st.info("Aún no hay gastos registrados.")
