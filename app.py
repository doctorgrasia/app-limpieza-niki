import streamlit as st
import pandas as pd
import datetime
import gspread
import json
import plotly.express as px  # Importamos Plotly aquí arriba, es más seguro

# 1. Configuración de la página
st.set_page_config(page_title="Finanzas App - Niki", page_icon="📱", layout="centered")

# --- BÓVEDA SECRETA DE ESTILOS CSS (DISEÑO FINTECH DARKS) ---
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
    h1 { color: var(--accent-green) !important; text-align: center; margin-bottom: 30px;}
    label { color: var(--text-secondary) !important; }
    .stAlert p { color: #1a1a1a !important; } /* Parche para alertas legibles */

    /* 3. ESTILO DE BOTONES PRIMARIOS (VERDE NEÓN) */
    div.stButton > button:first-child {
        background-color: var(--accent-green); color: #111111;
        border-radius: 50px; border: none; font-weight: bold;
        transition: transform 150ms ease, box-shadow 150ms ease;
        padding: 10px 25px;
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
    .metric-card-container { display: flex; gap: 1rem; margin-bottom: 2rem; justify-content: space-between; flex-wrap: wrap;}
    .fintech-card {
        background: var(--bg-card); border-radius: var(--radius-card);
        padding: 20px; flex: 1 1 calc(50% - 1rem); min-width: 150px;
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
    button[data-baseweb="tab"] { background-color: transparent !important; color: var(--text-secondary) !important; border-bottom: none !important;}
    button[data-baseweb="tab"][aria-selected="true"] { color: var(--accent-green) !important; font-weight: bold; border-bottom: 2px solid var(--accent-green) !important; }
    div[data-baseweb="tab-highlight"] { background-color: var(--accent-green) !important; }
    div[data-baseweb="tabpanel"] { padding-top: 20px; }

    /* 7. ESTILO DE DATAFRAME (TABLAS) */
    [data-testid="stDataFrame"] { background-color: var(--bg-card); border-radius: 10px; border: 1px solid #333;}
    </style>
    """, unsafe_allow_html=True)

# 2. TU CATÁLOGO (¡ASEGÚRATE DE QUE ESTÉ INCLUIDO!)
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

# --- CONEXIÓN SEGURA A GOOGLE SHEETS DESDE LA NUBE ---
@st.cache_resource
def conectar_google():
    try:
        # Esto lee directamente de la configuración secreta de Streamlit (la bóveda)
        credenciales_dict = json.loads(st.secrets["google_credentials"])
        cuenta = gspread.service_account_from_dict(credenciales_dict)
        hoja = cuenta.open("Base_Datos_Niki")
        return hoja
    except Exception as e:
        st.error(f"⚠️ Error de conexión a Google: {e}")
        st.stop()

doc_google = conectar_google()

# Conectamos a las pestañas específicas
pestana_ventas = doc_google.get_worksheet(0) # Asumimos que Ventas es la primera hoja

try:
    pestana_gastos = doc_google.worksheet("Gastos")
except:
    st.error("⚠️ No se encontró la pestaña 'Gastos' en tu Google Sheets. Créala primero.")
    st.stop()

# Funciones para leer y guardar datos (idénticas a las anteriores)
def cargar_datos(pestana, columnas_default):
    datos = pestana.get_all_records()
    if datos:
        return pd.DataFrame(datos)
    return pd.DataFrame(columns=columnas_default)

def guardar_datos(pestana, df_a_guardar):
    pestana.clear()
    lista_datos = [df_a_guardar.columns.values.tolist()] + df_a_guardar.values.tolist()
    pestana.update(lista_datos)

# --- LA "MEMORIA" DE TU APLICACIÓN (Manejo de Estado) ---
if 'historial_ventas' not in st.session_state:
    st.session_state.historial_ventas = cargar_datos(pestana_ventas, ["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"])

if 'historial_gastos' not in st.session_state:
    st.session_state.historial_gastos = cargar_datos(pestana_gastos, ["Fecha", "Concepto", "Monto ($)", "Categoria"])

# --- MOTOR DE CÁLCULO ---
df_ventas = st.session_state.historial_ventas.copy()
df_gastos = st.session_state.historial_gastos.copy()

# Nos aseguramos de que las columnas numéricas sean números reales y manejamos nulos
if not df_ventas.empty:
    df_ventas["Litros"] = pd.to_numeric(df_ventas["Litros"], errors='coerce').fillna(0)
    # Calculamos ingresos y ganancias basándonos en el catálogo
    df_ventas["Precio"] = df_ventas["Producto"].map(lambda x: catalogo[x]["precio"] if x in catalogo else 0)
    df_ventas["Costo"] = df_ventas["Producto"].map(lambda x: catalogo[x]["costo"] if x in catalogo else 0)
    df_ventas["Ingreso ($)"] = df_ventas["Litros"] * df_ventas["Precio"]
    df_ventas["Ganancia ($)"] = df_ventas["Litros"] * (df_ventas["Precio"] - df_ventas["Costo"])
else:
    df_ventas = pd.DataFrame(columns=["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"])

if not df_gastos.empty:
    df_gastos["Monto ($)"] = pd.to_numeric(df_gastos["Monto ($)"], errors='coerce').fillna(0)
else:
    df_gastos = pd.DataFrame(columns=["Fecha", "Concepto", "Monto ($)", "Categoria"])

# Calculamos los totales
ingresos_totales = df_ventas["Ingreso ($)"].sum()
ganancias_totales = df_ventas["Ganancia ($)"].sum()
gastos_totales = df_gastos["Monto ($)"].sum()

# LÓGICA DE CAJA: Todo lo que entró de ventas MENOS todo lo que salió de gastos
dinero_en_caja = ingresos_totales - gastos_totales

# --- INTERFAZ VISUAL: DASHBOARD PRINCIPAL ---
st.title("📱 Productos de Limpieza Niki")

# Módulo 1: Flujo de Efectivo (Dinero en Caja y Gastos Totales)
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

# Módulo 2: Estadísticas de Negocio (Ingresos Ventas, Ganancia Neta, Inversión)
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
        <div class="fintech-card">
            <div class="label">Inversión a Recuperar</div>
            <div class="value neutral">${inversion_total:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- MÓDULOS DE REGISTRO (Tabs) CON LÓGICA CORREGIDA Y TOASTS ---
tab_ventas, tab_gastos = st.tabs(["🛒 Registrar Venta", "💸 Registrar Salida de Efectivo"])

with tab_ventas:
    fecha_venta = st.date_input("Fecha de la venta", datetime.date.today(), key='date_venta_styled')
    col_prod, col_litros = st.columns(2)
    with col_prod:
        producto_seleccionado = st.selectbox("¿Qué vendiste?", list(catalogo.keys()), key='prod_venta_styled')
    with col_litros:
        litros = st.number_input("Litros vendidos", min_value=0.01, value=1.00, step=0.50, format="%.2f", key='litros_venta_styled')

    if st.button("Registrar Venta", type="primary", key='btn_venta_styled'):
        nueva_venta = pd.DataFrame([{
            "Fecha": fecha_venta.strftime("%d/%m/%Y"),
            "Producto": producto_seleccionado,
            "Litros": litros,
            "Ingreso ($)": "", # Dejamos vacío, el motor de cálculo lo llena
            "Ganancia ($)": ""
        }])
        st.session_state.historial_ventas = pd.concat([st.session_state.historial_ventas, nueva_venta], ignore_index=True)
        guardar_datos(pestana_ventas, st.session_state.historial_ventas)
        st.toast(f"✅ Venta de {producto_seleccionado} registrada exitosamente.")
        st.rerun() 

with tab_gastos:
    st.markdown("Registra aquí compras de envases, pasajes, material u otros.")
    fecha_gasto = st.date_input("Fecha del gasto", datetime.date.today(), key='date_gasto_styled')
    concepto = st.text_input("Concepto (Ej. Compra de botellas)", key='concept_gasto_styled')
    col_monto, col_cat = st.columns(2)
    with col_monto:
        monto_gasto = st.number_input("Monto gastado ($)", min_value=1.0, value=50.0, step=10.0, format="%.2f", key='monto_gasto_styled')
    with col_cat:
        categoria = st.selectbox("Categoría", ["Operativo", "Proveedor", "Servicio", "Pasajes", "Otro"], key='cat_gasto_styled')

    if st.button("Registrar Gasto", type="primary", key='btn_gasto_styled'):
        if concepto.strip() == "":
            st.warning("⚠️ Por favor escribe un concepto para el gasto.")
        else:
            # LÓGICA DE GUARDADO DE GASTOS REAL Y CORREGIDA
            nuevo_gasto = pd.DataFrame([{
                "Fecha": fecha_gasto.strftime("%d/%m/%Y"),
                "Concepto": concepto,
                "Monto ($)": monto_gasto,
                "Categoria": categoria
            }])
            # 1. Actualizamos el historial en memoria (Session State)
            st.session_state.historial_gastos = pd.concat([st.session_state.historial_gastos, nuevo_gasto], ignore_index=True)
            # 2. Guardamos el historial completo en Google Sheets
            guardar_datos(pestana_gastos, st.session_state.historial_gastos)
            # 3. Notificación flotante (Toast)
            st.toast(f"💸 Gasto de ${monto_gasto} por '{concepto}' registrado exitosamente.")
            # 4. Forzamos recarga para actualizar Dinero en Caja
            st.rerun()

# --- MÓDULO: GRÁFICA DE DONA (PRODUCTOS MÁS VENDIDOS) ---
st.divider()
st.subheader("📊 Análisis Visual")

if not df_ventas.empty:
    # Agrupamos las ventas por producto y sumamos los litros
    ventas_agrupadas = df_ventas.groupby("Producto")["Litros"].sum().reset_index()
    # Ordenamos de mayor a menor para que la leyenda se vea mejor
    ventas_agrupadas = ventas_agrupadas.sort_values(by="Litros", ascending=False)

    # Creamos la gráfica de dona (hole=0.65) estilo Fintech
    fig_ventas = px.pie(
        ventas_agrupadas, 
        names="Producto", 
        values="Litros", 
        hole=0.65, # El centro estará vacío
        color_discrete_sequence=["#c8ff00", "#5bc8fa", "#6c63ff", "#ff6b6b", "#ff9f43"], # Colores del tema
        labels={"Litros": "Total Vendido (Lt)"}
    )

    # Ajustamos el diseño (transparencia y fuente) para combinar perfectamente con el fondo oscuro
    fig_ventas.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff", family="Inter, sans-serif"),
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=-0.2),
        margin=dict(t=30, b=0, l=0, r=0)
    )
    
    # Añadimos hover custom para ver el dato exacto
    fig_ventas.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="%{label}<br>%{value} litros (%{percent})")

    # Mostramos la gráfica interactiva en Streamlit
    st.plotly_chart(fig_ventas, use_container_width=True)
else:
    st.info("Registra algunas ventas para ver la gráfica de productos más vendidos.")

# --- SECCIÓN: CONSULTAS RÁPIDAS (DATAFRAMES RE-ESTILIZADOS) ---
st.divider()
st.subheader("📋 Consultas Rápidas")
tab_tabla_ventas, tab_tabla_gastos = st.tabs(["Agenda de Ventas", "Historial de Gastos"])

with tab_tabla_ventas:
    if not df_ventas.empty:
        # Mostramos la tabla solo con las columnas importantes
        st.dataframe(df_ventas[["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"]], use_container_width=True)
    else:
        st.info("Aún no hay ventas registradas.")

with tab_tabla_gastos:
    if not df_gastos.empty:
        st.dataframe(df_gastos[["Fecha", "Concepto", "Monto ($)", "Categoria"]], use_container_width=True)
    else:
        st.info("Aún no hay gastos registrados.")
