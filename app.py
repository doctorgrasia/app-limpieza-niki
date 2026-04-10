import streamlit as st
import pandas as pd
import datetime
import gspread
import json
import plotly.express as px

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Finanzas App - Niki", page_icon="📱", layout="centered")

st.markdown("""
    <style>
    :root {
      --bg-primary: #1a1a1a; --bg-secondary: #242424; --bg-card: #2a2a2a; --bg-card-hover: #303030;
      --accent-green: #c8ff00; --accent-coral: #ff6b6b; --accent-blue: #5bc8fa;
      --text-primary: #ffffff; --text-secondary: #8a8a8a; --radius-card: 20px;
    }
    .stApp { background-color: var(--bg-primary); color: var(--text-primary); }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdownContainer p { color: var(--text-primary) !important; font-family: 'Inter', sans-serif; }
    h1 { color: var(--accent-green) !important; text-align: center; margin-bottom: 30px;}
    div.stButton > button:first-child {
        background-color: var(--accent-green); color: #111111;
        border-radius: 50px; border: none; font-weight: bold;
        transition: transform 150ms ease, box-shadow 150ms ease; padding: 10px 25px;
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

# --- 2. CATÁLOGO ---
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
    "Detercon": {"costo": 12.00, "precio": 22.00}, "Shampoo con cera": {"costo": 15.00, "precio": 25.00},
    "Ahuyenta perros": {"costo": 8.00, "precio": 16.00}
}
inversion_total = 5700.00

# --- 3. CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def conectar_google():
    try:
        credenciales_dict = json.loads(st.secrets["google_credentials"])
        cuenta = gspread.service_account_from_dict(credenciales_dict)
        return cuenta.open("Base_Datos_Niki")
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
        st.stop()

doc_google = conectar_google()
pestana_ventas = doc_google.get_worksheet(0)

try:
    pestana_gastos = doc_google.worksheet("Gastos")
    pestana_inventario = doc_google.worksheet("Inventario")
except:
    st.error("⚠️ Faltan pestañas en tu base de datos ('Gastos' o 'Inventario').")
    st.stop()

def cargar_datos(pestana, columnas):
    datos = pestana.get_all_records()
    return pd.DataFrame(datos) if datos else pd.DataFrame(columns=columnas)

def guardar_datos(pestana, df):
    pestana.clear()
    df_limpio = df.fillna("") 
    pestana.update([df_limpio.columns.values.tolist()] + df_limpio.values.tolist())

# --- 4. INICIALIZAR MEMORIA Y FUNCIONES ---
if 'ventas' not in st.session_state: st.session_state.ventas = cargar_datos(pestana_ventas, ["Fecha", "Producto", "Litros", "Ingreso ($)", "Ganancia ($)"])
if 'gastos' not in st.session_state: st.session_state.gastos = cargar_datos(pestana_gastos, ["Fecha", "Concepto", "Monto ($)", "Categoria"])
if 'inventario' not in st.session_state: st.session_state.inventario = cargar_datos(pestana_inventario, ["Producto", "Stock Actual (Lt)", "Stock Minimo (Lt)"])

def descontar_inventario(prod, litros):
    df = st.session_state.inventario
    if prod in df["Producto"].values:
        idx = df[df["Producto"] == prod].index[0]
        df.at[idx, "Stock Actual (Lt)"] = float(df.at[idx, "Stock Actual (Lt)"]) - float(litros)
        st.session_state.inventario = df
        guardar_datos(pestana_inventario, df)

# --- 5. CÁLCULOS DEL DASHBOARD ---
df_v = st.session_state.ventas.copy()
df_g = st.session_state.gastos.copy()
df_i = st.session_state.inventario.copy()

ingresos = pd.to_numeric(df_v["Ingreso ($)"], errors='coerce').sum() if not df_v.empty else 0
gastos = pd.to_numeric(df_g["Monto ($)"], errors='coerce').sum() if not df_g.empty else 0
ganancias = pd.to_numeric(df_v["Ganancia ($)"], errors='coerce').sum() if not df_v.empty else 0
caja = ingresos - gastos

# --- 6. INTERFAZ VISUAL ---
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

tab_v, tab_g, tab_i, tab_c = st.tabs(["🛒 Venta", "💸 Gasto", "📦 Inventario", "📋 Consultas"])

# TAB: VENTAS
with tab_v:
    with st.form("form_venta"):
        # --- SOLUCIÓN: AQUÍ ESTÁ EL CALENDARIO ---
        fecha_venta = st.date_input("📅 Fecha de Venta", datetime.date.today())
        
        prod = st.selectbox("Producto", list(catalogo.keys()))
        lits = st.number_input("Litros", min_value=0.1, value=1.0, step=0.5)
        
        if st.form_submit_button("Registrar Venta"):
            precio_unitario = catalogo[prod]["precio"]
            costo_unitario = catalogo[prod]["costo"]
            ingreso_real = float(lits) * float(precio_unitario)
            ganancia_real = float(lits) * (float(precio_unitario) - float(costo_unitario))

            nv = pd.DataFrame([{
                # --- SOLUCIÓN: CONECTAMOS LA FECHA ELEGIDA EN LUGAR DE LA FECHA DE HOY ---
                "Fecha": fecha_venta.strftime("%d/%m/%Y"), 
                "Producto": prod, 
                "Litros": float(lits),
                "Ingreso ($)": ingreso_real,
                "Ganancia ($)": ganancia_real
            }])
            
            st.session_state.ventas = pd.concat([st.session_state.ventas, nv], ignore_index=True)
            guardar_datos(pestana_ventas, st.session_state.ventas)
            descontar_inventario(prod, lits) 
            
            st.toast(f"✅ Vendido {lits}L de {prod}")
            st.rerun()

# TAB: GASTOS
with tab_g:
    with st.form("form_gasto"):
        fg = st.date_input("Fecha", datetime.date.today())
        con = st.text_input("Concepto")
        mon = st.number_input("Monto", min_value=1.0)
        cat = st.selectbox("Categoría", ["Operativo", "Pasajes", "Proveedor", "Otro"])
        
        if st.form_submit_button("Registrar Gasto"):
            ng = pd.DataFrame([{"Fecha": fg.strftime("%d/%m/%Y"), "Concepto": con, "Monto ($)": mon, "Categoria": cat}])
            st.session_state.gastos = pd.concat([st.session_state.gastos, ng], ignore_index=True)
            guardar_datos(pestana_gastos, st.session_state.gastos)
            st.toast("💸 Gasto guardado")
            st.rerun()

# TAB: INVENTARIO
with tab_i:
    st.subheader("Estado de Tambos (Litros)")
    if not df_i.empty:
        df_i["Estado"] = df_i.apply(lambda r: "BAJO" if float(r["Stock Actual (Lt)"]) <= float(r["Stock Minimo (Lt)"]) else "OK", axis=1)
        fig_i = px.bar(df_i, x="Producto", y="Stock Actual (Lt)", color="Estado", color_discrete_map={"BAJO": "#ff6b6b", "OK": "#5bc8fa"})
        fig_i.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
        st.plotly_chart(fig_i, use_container_width=True)
        
    st.info("🔄 Edita aquí para reabastecer tus tambos y presiona Guardar:")
    df_edit_i = st.data_editor(st.session_state.inventario, use_container_width=True)
    if st.button("📦 Guardar Cambios Inventario", type="primary"):
        st.session_state.inventario = df_edit_i
        guardar_datos(pestana_inventario, df_edit_i)
        st.success("Inventario actualizado")
        st.rerun()

# TAB: CONSULTAS Y EDICIÓN
with tab_c:
    st.info("💡 Haz doble clic en una celda para editar y luego guarda.")
    col_edit_v, col_edit_g = st.columns(2)
    
    with col_edit_v:
        st.write("🛒 **Agenda de Ventas**")
        df_edit_v = st.data_editor(st.session_state.ventas, use_container_width=True, num_rows="dynamic", key="ed_v")
        if st.button("💾 Guardar Ventas", type="primary"):
            st.session_state.ventas = df_edit_v
            guardar_datos(pestana_ventas, df_edit_v)
            st.success("Ventas actualizadas")
            st.rerun()

    with col_edit_g:
        st.write("💸 **Historial de Gastos**")
        df_edit_g = st.data_editor(st.session_state.gastos, use_container_width=True, num_rows="dynamic", key="ed_g")
        if st.button("💾 Guardar Gastos", type="primary"):
            st.session_state.gastos = df_edit_g
            guardar_datos(pestana_gastos, df_edit_g)
            st.success("Gastos actualizados")
            st.rerun()

# --- 7. GRÁFICA FINAL ---
if not df_v.empty:
    st.divider()
    st.subheader("📈 Popularidad de Jabones")
    va = df_v.groupby("Producto")["Litros"].sum().reset_index()
    fig = px.pie(va, names="Producto", values="Litros", hole=0.6, color_discrete_sequence=["#c8ff00", "#5bc8fa", "#ff6b6b", "#6c63ff"])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#fff"))
    st.plotly_chart(fig)
