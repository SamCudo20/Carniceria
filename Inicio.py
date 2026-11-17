import os
import pandas as pd
import streamlit as st

# ============================================================
#  Configuración de la página
# ============================================================
st.set_page_config(
    page_title="Control de Cuarto Frío - Carnicería", page_icon="🥩", layout="wide"
)

st.markdown(
    """
    <style>
    .main { padding: 2rem; }
    </style>
""",
    unsafe_allow_html=True,
)

CANDIDATAS_TIEMPO = ["time", "_time", "timestamp", "fecha", "date", "datetime"]


def preparar_datos(df):
  """Detecta la columna de tiempo y limpia las columnas numéricas."""
  df = df.copy()
  col_tiempo = next(
      (
          c
          for c in df.columns
          if str(c).strip().lower() in CANDIDATAS_TIEMPO
      ),
      None,
  )
  if col_tiempo is not None:
    df[col_tiempo] = pd.to_datetime(df[col_tiempo], errors="coerce")
    df = df.dropna(subset=[col_tiempo]).set_index(col_tiempo).sort_index()
    df.index.name = "Time"

  for c in df.columns:
    if not pd.api.types.is_numeric_dtype(df[c]):
      convertida = pd.to_numeric(
          df[c].astype(str).str.replace(",", ".", regex=False), errors="coerce"
      )
      if convertida.notna().mean() >= 0.9:
        df[c] = convertida

  return df


# ============================================================
#  Encabezado Principal
# ============================================================
st.title("🥩 Monitoreo del Cuarto Frío - Carnicería")
st.markdown("""
    Control de temperatura, humedad relativa y estado operativo para la conservación óptima de la carne.
""")

# ============================================================
#  Carga robusta de temp.csv y hum.csv
# ============================================================
df_t, df_h = pd.DataFrame(), pd.DataFrame()
t_val, h_val = 0.0, 0.0

try:
  if os.path.exists("temp.csv"):
    df_t = pd.read_csv("temp.csv")
    df_t = preparar_datos(df_t)
    nums_t = df_t.select_dtypes(include="number").columns
    if len(nums_t) > 0 and not df_t.empty:
      t_val = float(df_t[nums_t[0]].iloc[-1])
  
  if os.path.exists("hum.csv"):
    df_h = pd.read_csv("hum.csv")
    df_h = preparar_datos(df_h)
    nums_h = df_h.select_dtypes(include="number").columns
    if len(nums_h) > 0 and not df_h.empty:
      h_val = float(df_h[nums_h[0]].iloc[-1])

  if not df_t.empty or not df_h.empty:
    st.sidebar.success("📂 Archivos `temp.csv` y `hum.csv` cargados correctamente.")
except Exception as e:
  st.sidebar.error(f"Error al procesar los archivos: {e}")

# Combinar para gráficas si ambos existen
df1 = pd.DataFrame()
if not df_t.empty and not df_h.empty:
  df1 = pd.concat([df_t, df_h], axis=1)
  df1 = df1.loc[:, ~df1.columns.duplicated()]
elif not df_t.empty:
  df1 = df_t
elif not df_h.empty:
  df1 = df_h

variables = df1.select_dtypes(include="number").columns.tolist() if not df1.empty else []

# ============================================================
#  Pestañas de la Aplicación
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Panel Principal",
    "🥩 Conservación de Carnes",
    "📈 Gráficas Históricas",
    "⚙️ Control y Ventilación",
])

# ----------------------------------------------------
#  TAB 1 · Panel Principal (Métricas exactas)
# ----------------------------------------------------
with tab1:
  st.subheader("Estado Actual del Sistema")

  # Determinar el estado del cuarto frío basado en los valores leídos
  if h_val > 70:
    estado_texto = "Peligro alta humedad"
    estado_color = "🔴"
    borde_color = "#ff4b4b"
  elif t_val <= -18:
    estado_texto = "Condiciones óptimas"
    estado_color = "🟢"
    borde_color = "#09ab3b"
  else:
    estado_texto = "Temperatura alta"
    estado_color = "🟡"
    borde_color = "#ffa100"

  # Tarjetas principales de Temperatura y Humedad
  c1, c2 = st.columns(2)
  with c1:
    st.metric(label="🌡️ Temperatura", value=f"{t_val:.1f} °C")
  with c2:
    st.metric(label="💧 Humedad", value=f"{h_val:.1f} %")

  st.markdown("---")
  
  # Tarjeta de Estado Grande
  st.markdown(f"""
      <div style="padding: 20px; border-radius: 10px; background-color: #f0f2f6; border-left: 6px solid {borde_color};">
          <h3 style="margin:0; color: #31333F;">⚠️ Estado del Sistema</h3>
          <p style="font-size: 24px; font-weight: bold; margin: 5px 0 0 0; color: #1f1f1f;">
              {estado_color} {estado_texto}
          </p>
      </div>
  """, unsafe_allow_html=True)

# ----------------------------------------------------
#  TAB 2 · Conservación de Carnes
# ----------------------------------------------------
with tab2:
  st.subheader("Tiempos de Descomposición y Conservación")
  st.write("""
    Un control adecuado de la temperatura previene la proliferación bacteriana en la carnicería:
  """)
  st.info("""
    * **Menor o igual a -18 °C (Congelación):** Detiene la actividad microbiana. La carne se conserva de forma segura durante meses sin perder propiedades organolépticas.
    * **Entre -2 °C y 2 °C (Refrigeración fresca):** Extiende la vida útil de cortes frescos de res o cerdo de 3 a 7 días.
    * **Mayor a 4 °C (Zona de Peligro):** Aumenta drásticamente el riesgo de descomposición, malos olores y crecimiento de bacterias patógenas.
  """)

# ----------------------------------------------------
#  TAB 3 · Gráficas Históricas
# ----------------------------------------------------
with tab3:
  st.subheader("Tendencia de Temperatura y Humedad")
  if not df1.empty and len(variables) > 0:
    st.line_chart(df1[variables])
  else:
    st.warning("No hay suficientes datos históricos para graficar.")

# ----------------------------------------------------
#  TAB 4 · Control y Ventilación
# ----------------------------------------------------
with tab4:
  st.subheader("Gestión del Servomotor (Ventilación)")
  st.write("El sistema ajusta la compuerta de ventilación según los valores del entorno para disipar calor o expulsar humedad.")
  
  if h_val > 70:
    servo_pos = "Abierto (180°) - Expulsando humedad"
  elif t_val <= -18:
    servo_pos = "Cerrado (0°) - Manteniendo frío"
  else:
    servo_pos = "Medio (90°) - Disipando temperatura alta"

  st.metric("Posición de la Compuerta", servo_pos)

# ============================================================
#  Pie de página
# ============================================================
st.markdown("""
    ---
    **Sistema IoT de Monitoreo para Cuarto Frío** | Universidad EAFIT
""")
