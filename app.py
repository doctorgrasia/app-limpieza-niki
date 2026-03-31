import streamlit as st
import pandas as pd
import datetime
import gspread
import json
import plotly.express as px

# 1. Configuración y Estilos (Se mantienen igual para conservar tu diseño Fintech)
st.set_page_config(page_title="Finanzas App - Niki", page_icon="📱", layout="centered")

st.markdown("""
    <style>
    :root {
      --bg-primary: #1a1a1a;
      --bg-secondary: #242424;
      --bg-card: #2a2a2a;
      --bg-card-hover: #303030;
      --accent-green: #c8ff00;
      --accent-coral: #ff6b6b;
      --accent-blue: #5bc8fa;
      --text-primary: #ffffff;
      --text-secondary: #8a8a8a;
      --radius-card: 20px;
    }
    .stApp { background-color: var(--bg-primary); color: var(--text-primary); }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdownContainer p { color: var(--text-primary) !important; font-family: 'Inter', sans-serif; }
    h1 { color: var(--accent-green) !important; text-align: center; margin-bottom: 30px;}
    div.stButton > button:first-child {
        background-color: var(--accent-green); color: #111111;
        border-radius: 50px; border: none; font-weight: bold;
        transition: transform 150ms ease, box-shadow 150ms ease;
        padding: 10px 25px;
    }
    .metric-card-container { display: flex; gap: 1rem; margin-bottom: 2rem; justify-content: space-between; flex-wrap: wrap;}
    .fintech-card {
        background: var(--bg-card); border-radius: var(--radius-card);
        padding: 20px; flex: 1 1 calc(50% - 1rem); min-width: 150px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4); border: 1px solid #333;
    }
    .fintech-card .value.positive { color: var(--accent-green); font-size: 1.8rem; font-weight: bold; }
    .fintech-card .value.negative { color: var(--accent-coral); font-size: 1.8rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. Catálogo y Configuración
catalogo = {
    "Cloro": {"costo": 3.50, "precio": 6.00}, "Maestro limpio": {"costo": 5.00, "precio": 12.00},
    "Lavanda": {"costo": 5.00, "precio": 12.00}, "Mar fresco": {"costo": 5.00, "precio": 12.00},
    "Menta": {"costo": 5.00, "precio": 12.00}, "Violeta": {"costo": 5.00, "precio": 12.00},
    "Pino blanco": {"costo": 6.00, "precio": 12.00}, "Fabuloso canela": {"costo": 5.00, "precio": 12.00},
    "Carisma": {"costo": 7.00, "precio": 18.00}, "Primavera": {"costo": 7.00, "precio": 18.00},
    "Ensueño": {"costo": 7.00, "precio": 18.00}, "Dawny azul": {"costo": 7.00, "precio": 18.00},
    "Lavanderia": {"costo": 7.00, "precio": 20.00}, "Ariel doble poder": {"costo": 9.00, "precio": 20.00},
    "Roma": {"costo": 9.00, "precio": 20.00}, "Mas color": {"costo": 9.00, "precio": 20.00},
    "Zote": {"costo": 9.00, "precio": 20.00}, "Persil": {"costo": 9.00, "precio": 20.00},
    "Brazo": {"costo": 9.00, "precio": 20.00}, "Mas negro": {"costo": 9.00, "precio": 20.00},
    "Vanish gel": {"costo": 9.00, "precio": 20.00}, "Cereza manos": {"costo": 9.00, "precio": 20.00},
    "Salvo": {"costo": 12.00, "precio": 22.00}, "Axion": {"costo": 12.00, "precio": 22.00},
    "Detercon": {"costo": 12.00, "precio": 22.00}, "Shampoo con cera": {"costo": 15.00, "precio": 25.00}
}
inversion_total = 5700.00 

# 3. Conexión a Google Sheets
@st.cache_resource
def conectar_google():
    try:
        credenciales_dict = json.loads(st.secrets["google_credentials"])
        cuenta = gspread.service_account_from_dict(credenciales_dict)
        hoja = cuenta.open("Base_Datos_Niki")
        return hoja
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
        st.stop()

doc_google = conectar_google()
pestana_ventas = doc_google.get_worksheet(0)
try:
    pestana_gastos = doc_google.worksheet("Gastos")
except:
    st.error("⚠️ Crea la pestaña 'Gastos' en Drive.")
    st.stop()

def cargar_datos(pestana, columnas):
    datos = pestana.get_all_records()
    return pd.DataFrame(datos) if datos else pd.DataFrame(columns=columnas)

def guardar_datos(pestana, df):
    pestana.clear()
    pestana.update([df.columns.values.tolist()] + df.values.tolist())

# Cargar historial
if 'hist_v' not in st.session_state: st.session_state.hist_v = cargar_datos(pestana_ventas, ["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"])
if 'hist_g' not in st.session_state: st.session_state.hist_g = cargar_datos(pestana_gastos, ["Fecha", "Concepto", "Monto ($)", "Categoria"])

# Cálculos
df_v = st.session_state.hist_v.copy()
df_g = st.session_state.hist_g.copy()

if not df_v.empty:
    df_v["Litros"] = pd.to_numeric(df_v["Litros"], errors='coerce').fillna(0)
    df_v["Ingreso ($)"] = df_v.apply(lambda r: r["Litros"] * catalogo.get(r["Producto"], {}).get("precio", 0), axis=1)
    df_v["Ganancia ($)"] = df_v.apply(lambda r: r["Litros"] * (catalogo.get(r["Producto"], {}).get("precio", 0) - catalogo.get(r["Producto"], {}).get("costo", 0)), axis=1)

ingresos = df_v["Ingreso ($)"].sum() if not df_v.empty else 0
gastos = pd.to_numeric(df_g["Monto ($)"], errors='coerce').sum() if not df_g.empty else 0
ganancias = df_v["Ganancia ($)"].sum() if not df_v.empty else 0
caja = ingresos - gastos

# 4. Dashboard Visual
st.title("📱 Finanzas Productos Niki")

st.markdown(f"""
    <div class="metric-card-container">
        <div class="fintech-card"><div class="label">💵 Dinero en Caja</div><div class="value positive">${caja:,.2f}</div></div>
        <div class="fintech-card"><div class="label">🔻 Gastos Totales</div><div class="value negative">${gastos:,.2f}</div></div>
    </div>
    <div class="metric-card-container">
        <div class="fintech-card"><div class="label">Ganancia Neta</div><div class="value positive">${ganancias:,.2f}</div></div>
    </div>
    """, unsafe_allow_html=True)

# 5. Registro
tab_v, tab_g = st.tabs(["🛒 Venta", "💸 Gasto"])

with tab_v:
    with st.form("form_v"):
        f = st.date_input("Fecha", datetime.date.today())
        p = st.selectbox("Producto", list(catalogo.keys()))
        l = st.number_input("Litros", min_value=0.1, value=1.0)
        if st.form_submit_button("Registrar Venta"):
            nv = pd.DataFrame([{"Fecha": f.strftime("%d/%m/%Y"), "Producto": p, "Litros": l, "Ingreso ($)": 0, "Ganancia ($)": 0}])
            st.session_state.hist_v = pd.concat([st.session_state.hist_v, nv], ignore_index=True)
            guardar_datos(pestana_ventas, st.session_state.hist_v)
            st.toast("✅ Venta guardada")
            st.rerun()

with tab_g:
    with st.form("form_g"):
        fg = st.date_input("Fecha", datetime.date.today())
        con = st.text_input("Concepto")
        mon = st.number_input("Monto", min_value=1.0)
        cat = st.selectbox("Categoría", ["Operativo", "Pasajes", "Proveedor", "Otro"])
        if st.form_submit_button("Registrar Gasto"):
            ng = pd.DataFrame([{"Fecha": fg.strftime("%d/%m/%Y"), "Concepto": con, "Monto ($)": mon, "Categoria": cat}])
            st.session_state.hist_g = pd.concat([st.session_state.hist_g, ng], ignore_index=True)
            guardar_datos(pestana_gastos, st.session_state.hist_g)
            st.toast("💸 Gasto guardado")
            st.rerun()

# --- 6. SECCIÓN DE EDICIÓN (LO NUEVO) ---
st.divider()
st.subheader("📋 Edición y Consultas")
t_v, t_g = st.tabs(["Agenda de Ventas", "Editar Historial de Gastos"])

with t_v:
    st.dataframe(df_v, use_container_width=True)

with t_g:
    st.info("💡 Haz doble clic en una celda para editar. Al terminar, presiona el botón de abajo.")
    # El st.data_editor permite modificar la tabla directamente
    df_editado = st.data_editor(st.session_state.hist_g, use_container_width=True, num_rows="dynamic")
    
    if st.button("💾 Guardar cambios en Gastos", type="primary"):
        st.session_state.hist_g = df_editado
        guardar_datos(pestana_gastos, df_editado)
        st.success("✅ ¡Base de datos de Gastos actualizada en Drive!")
        st.rerun()

# 7. Gráfica
if not df_v.empty:
    st.divider()
    va = df_v.groupby("Producto")["Litros"].sum().reset_index()
    fig = px.pie(va, names="Producto", values="Litros", hole=0.6, color_discrete_sequence=["#c8ff00", "#5bc8fa", "#ff6b6b"])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#fff"))
    st.plotly_chart(fig)
