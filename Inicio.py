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
#  Carga de archivos locales (temp.csv y hum.csv)
# ============================================================
df1 = None
archivo_temp = "temp.csv" if os.path.exists("temp.csv") else ("temp" if os.path.exists("temp") else None)
archivo_hum = "hum.csv" if os.path.exists("hum.csv") else ("hum" if os.path.exists("hum") else None)

try:
  df_list = []
  if archivo_temp and os.path.exists(archivo_temp):
    df_t = pd.read_csv(archivo_temp)
    df_t = preparar_datos(df_t)
    df_list.append(df_t)

  if archivo_hum and os.path.exists(archivo_hum):
    df_h = pd.read_csv(archivo_hum)
    df_h = preparar_datos(df_h)
    df_list.append(df_h)

  if df_list:
    # Unir ambos DataFrames de manera segura para evitar valores NaN
    df1 = pd.concat(df_list, axis=1)
    # Limpiar duplicados de columnas si los hubiera
    df1 = df1.loc[:, ~df1.columns.duplicated()]
    st.sidebar.success("📂 Archivos `temp.csv` y `hum.csv` cargados correctamente.")

except Exception as e:
  st.sidebar.error(f"Error al procesar los archivos locales: {e}")

# Respaldo si no encuentra los archivos separados
if df1 is None or df1.empty:
  uploaded_file = st.sidebar.file_uploader("Cargar CSV consolidado", type=["csv"])
  if uploaded_file is not None:
    df1 = pd.read_csv(uploaded_file)
    df1 = preparar_datos(df1)
  else:
    st.warning("⚠️ No se encontraron `temp.csv` o `hum.csv` en la raíz del repositorio. Por favor, súbelos a GitHub.")
    st.stop()

variables = df1.select_dtypes(include="number").columns.tolist()

if not variables:
  st.error("No se encontraron columnas numéricas válidas en los datos.")
  st.stop()

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
#  TAB 1 · Panel Principal (Basado en tu imagen)
# ----------------------------------------------------
with tab1:
  st.subheader("Estado Actual del Sistema")

  if not df1.empty:
    ultimo = df1.iloc[-1]
    
    # Detección inteligente de variables para evitar NaN
    col_t = next((c for c in variables if "temp" in c.lower() or "t" in c.lower()), variables[0])
    col_h = next((c for c in variables if "hum" in c.lower() or "h" in c.lower()), variables[1] if len(variables) > 1 else variables[0])

    t_val = ultimo.get(col_t, 0)
    h_val = ultimo.get(col_h, 0)

    # Determinar el estado del cuarto frío basado en umbrales lógicos
    if h_val > 70:
      estado_texto = "Peligro alta humedad"
      estado_color = "🔴"
    elif t_val <= -18:
      estado_texto = "Condiciones óptimas"
      estado_color = "🟢"
    else:
      estado_texto = "Temperatura alta"
      estado_color = "🟡"

    # Tarjetas principales idénticas a la estructura solicitada
    c1, c2 = st.columns(2)
    with c1:
      st.metric(label="🌡️ Temperatura", value=f"{t_val:.1f} °C")
    with c2:
      st.metric(label="💧 Humedad", value=f"{h_val:.1f} %")

    st.markdown("---")
    
    # Tarjeta de Estado Grande
    st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: #f0f2f6; border-left: 6px solid #ffa100;">
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
  st.line_chart(df1[variables])

# ----------------------------------------------------
#  TAB 4 · Control y Ventilación
# ----------------------------------------------------
with tab4:
  st.subheader("Gestión del Servomotor (Ventilación)")
  st.write("El sistema ajusta la compuerta de ventilación según los valores del entorno para disipar calor o expulsar humedad.")
  
  if not df1.empty:
    ultimo = df1.iloc[-1]
    t_val = ultimo.get(variables[0], -18)
    h_val = ultimo.get(variables[1] if len(variables) > 1 else variables[0], 50)

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
