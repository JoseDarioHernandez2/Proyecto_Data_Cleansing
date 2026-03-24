import streamlit as st
import pandas as pd
import plotly.express as px
import joblib
from pathlib import Path
from sklearn.metrics import r2_score

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Dashboard Inmobiliario IA", layout="wide")

# Estilos para limpieza visual
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; border-radius: 10px; padding: 10px; border: 1px solid #e9ecef; }
    h1, h2, h3 { color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

LABELS_ORDENADOS = [
    'VIS (<280M)', 'Confort Medio (281M-460M)', 'Confort Familiar (461M-730M)', 
    'Alto Confort (731M-1.1B)', 'Confort Lujo (1.1B-1.8B)', 'Premium Confort Lujo (>1.8B)'
]

@st.cache_data
def load_data():
    path = Path(__file__).parent.parent / "data/data_procesada/dataset_avaluos_final.xlsx"
    if not path.exists(): return pd.DataFrame()
    
    df = pd.read_excel(path)
    
    # Limpieza crucial para que las gráficas de abajo no salgan en blanco (null)
    if 'Rango precios' in df.columns:
        df['Rango precios'] = df['Rango precios'].astype(str).str.strip()
        df['Rango precios'] = pd.Categorical(df['Rango precios'], categories=LABELS_ORDENADOS, ordered=True)
        
    df['Valor comercial M'] = df['Valor comercial'] / 1_000_000
    df['Valor Predicho IA M'] = df['Valor Predicho IA'] / 1_000_000
    df['Decada'] = (df['Año construccion'] // 10) * 10
    return df

df = load_data()

# --- TÍTULO ---
st.title("🏛️ Dashboard - control y predicción valor avalúo inmuebles")

# --- MÉTRICAS SUPERIORES ---
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Avalúos", f"{len(df):,}")
m2.metric("Mediana Valor Comercial", f"{df['Valor comercial M'].median():.1f}M COP")
r2 = r2_score(df['Valor comercial'], df['Valor Predicho IA']) * 100
m3.metric("Precisión Modelo ML", f"{r2:.1f}%")
m4.metric("Alertas Críticas", len(df[abs(df['Desviacion %']) > 15]))
m5.metric("Mediana Valor m²", f"{df['Valor m2'].median():,.0f} COP")

st.divider()

# --- BLOQUE 1: DISTRIBUCIONES (TUS GRÁFICAS ORIGINALES) ---
c1, c2 = st.columns(2)
with c1:
    st.subheader("⏳ Histórico: Año de Construcción")
    fig_ano = px.histogram(df, x='Año construccion', nbins=25, color_discrete_sequence=['#3b82f6'], template="plotly_white")
    st.plotly_chart(fig_ano, use_container_width=True)
with c2:
    st.subheader("💰 Distribución de Precios (Millones COP)")
    fig_price = px.histogram(df, x='Valor comercial M', nbins=40, color_discrete_sequence=['#10b981'], template="plotly_white")
    st.plotly_chart(fig_price, use_container_width=True)

# --- BLOQUE 2: ESTRATO Y ESTADO (TUS GRÁFICAS ORIGINALES) ---
c3, c4 = st.columns(2)
with c3:
    st.subheader("🏙️ Valor m² Promedio por Estrato")
    df_estrato = df.groupby('Estrato')['Valor m2'].mean().reset_index()
    fig_est = px.bar(df_estrato, x='Estrato', y='Valor m2', color='Valor m2', color_continuous_scale='Reds', template="plotly_white")
    fig_est.update_layout(xaxis=dict(type='category'))
    st.plotly_chart(fig_est, use_container_width=True)
with c4:
    st.subheader("💎 Valor Comercial por Estado (M COP)")
    fig_estado = px.box(df, x='Estado acabados', y='Valor comercial M', color='Estado acabados', 
                        color_discrete_map={'EXCELENTE': '#93c5fd', 'BUENO': '#f87171', 'REGULAR': '#fbbf24'}, template="plotly_white")
    st.plotly_chart(fig_estado, use_container_width=True)

st.divider()

# --- BLOQUE 3: COMPOSICIÓN Y VOLUMEN (MEJORADAS PARA STAKEHOLDERS) ---
c5, c6 = st.columns([0.4, 0.6])
with c5:
    st.subheader("🍰 Composición Jerárquica")
    paleta_viva = ['#FFF4E0', '#FFCC33', '#FF8C00', '#E34234', '#B22222', '#7B0000']
    fig_pie = px.pie(df.dropna(subset=['Rango precios']), names='Rango precios', hole=0.45, 
                     color_discrete_sequence=paleta_viva, category_orders={"Rango precios": LABELS_ORDENADOS})
    fig_pie.update_traces(textinfo='percent+label', pull=[0,0,0,0,0,0.2])
    st.plotly_chart(fig_pie, use_container_width=True)
with c6:
    st.subheader("📊 Volumen por Segmento")
    df_seg = df['Rango precios'].value_counts().reindex(LABELS_ORDENADOS).reset_index()
    df_seg.columns = ['Rango', 'Cantidad']
    fig_seg = px.bar(df_seg, x='Cantidad', y='Rango', orientation='h', color='Rango', 
                     color_discrete_sequence=['#D1E3F3', '#91B9D9', '#548DBB', '#2C5E85', '#153E5A', '#0D2535'], template="plotly_white")
    fig_seg.update_layout(showlegend=False)
    st.plotly_chart(fig_seg, use_container_width=True)

# --- VALIDACIÓN CON LÍNEA PUNTEADA ---
st.divider()
st.subheader("🎯 Validación: Real vs Predicción IA")
fig_val = px.scatter(df, x='Valor comercial M', y='Valor Predicho IA M', color='Desviacion %', 
                     color_continuous_scale='RdYlGn_r', template="plotly_white")
# Línea de referencia (Predicción Perfecta)
max_val = max(df['Valor comercial M'].max(), df['Valor Predicho IA M'].max())
fig_val.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="Gray", width=1, dash="dash"))
st.plotly_chart(fig_val, use_container_width=True)

# --- CALCULADORA CON SALIDA ESTÉTICA ---
st.divider()
st.header("🔮 Calculadora Predictiva")
with st.form("simulador_v1"):
    col_sim1, col_sim2, col_sim3, col_sim4 = st.columns(4)
    with col_sim1: area_in = st.number_input("Área m²", value=70.0); estrato_in = st.selectbox("Estrato", sorted(df['Estrato'].unique()), index=2)
    with col_sim2: hab_in = st.number_input("Habitaciones", value=3); banos_in = st.number_input("Baños", value=2)
    with col_sim3: garajes_in = st.number_input("Garajes", value=1); piso_in = st.number_input("Piso", value=3)
    with col_sim4: ciudad_in = st.selectbox("Ciudad", sorted(df['Ciudad'].unique())); tipo_in = st.selectbox("Inmueble", sorted(df['Tipo inmueble'].unique())); estado_in = st.selectbox("Acabados", sorted(df['Estado acabados'].unique()))
    submitted = st.form_submit_button("🚀 Calcular")

if submitted:
    try:
        modelo = joblib.load(Path(__file__).parent.parent / "modelos/modelo_inmobiliario_v2.pkl")
        X_input = pd.DataFrame([{'Area total': area_in, 'Estrato': estrato_in, 'Total habitaciones': hab_in, 'Total baños': banos_in, 'Total garajes': garajes_in, 'Vetustez': 10, 'Piso numero': piso_in, 'Ciudad': ciudad_in, 'Tipo inmueble': tipo_in, 'Estado acabados': estado_in}])
        prediccion = float(modelo.predict(X_input)[0])
        
        # SALIDA ESTÉTICA PREMIUM
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #0D2535, #153E5A); padding: 30px; border-radius: 15px; text-align: center; color: white;'>
                <h3 style='color: #FFCC33; margin: 0;'>VALOR ESTIMADO POR IA</h3>
                <h1 style='color: white; font-size: 3em; margin: 10px 0;'>${prediccion:,.0f} COP</h1>
                <p style='opacity: 0.8;'>Estimación basada en mercado actual y Random Forest v2</p>
            </div>
        """, unsafe_allow_html=True)
        st.balloons()
    except Exception as e: st.error(f"Error: {e}")