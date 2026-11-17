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
    .stAlert { margin-top: 1rem; }
    </style>
""",
    unsafe_allow_html=True,
)

CANDIDATAS_TIEMPO = ["time", "_time", "timestamp", "fecha", "date", "datetime"]


# ============================================================
#  Preparación de datos
# ============================================================
def preparar_datos(df):
  """Detecta la columna de tiempo y las columnas numéricas del archivo."""
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

  numericas = df.select_dtypes(include="number").columns.tolist()
  return df, numericas, col_tiempo


def normalizar(df):
  """Escala cada columna a 0–1 para comparar variables con unidades distintas."""
  rango = (df.max() - df.min()).replace(0, 1)
  return (df - df.min()) / rango


# ============================================================
#  Encabezado del Sistema de Carnicería
# ============================================================
st.title("🥩 Sistema de Monitoreo y Control - Cuarto Frío de Carnicería")
st.markdown("""
    Plataforma IoT para la supervisión de temperatura, humedad relativa, 
    tiempos de conservación de la carne y gestión de ventilación automatizada.
""")

# ============================================================
#  Carga automática de archivos locales ('temp' y 'hum')
# ============================================================
df1 = None
posibles_temp = ["temp.csv", "temp", "temperatura.csv"]
posibles_hum = ["hum.csv", "hum", "humedad.csv"]

archivo_temp = next((f for f in posibles_temp if os.path.exists(f)), None)
archivo_hum = next((f for f in posibles_hum if os.path.exists(f)), None)

if archivo_temp and archivo_hum:
  try:
    df_t = pd.read_csv(archivo_temp)
    df_h = pd.read_csv(archivo_hum)

    df_t, vars_t, _ = preparar_datos(df_t)
    df_h, vars_h, _ = preparar_datos(df_h)

    if not df_t.empty and not df_h.empty:
      if isinstance(df_t.index, pd.DatetimeIndex) and isinstance(
          df_h.index, pd.DatetimeIndex
      ):
        df1 = pd.merge(
            df_t,
            df_h,
            left_index=True,
            right_index=True,
            how="outer",
            suffixes=("_temp", "_hum"),
        )
      else:
        df1 = pd.concat([df_t, df_h], axis=1)
    st.sidebar.success(
        f"📂 Datos cargados automáticamente desde: `{archivo_temp}` y"
        f" `{archivo_hum}`"
    )
  except Exception as e:
    st.sidebar.warning(f"Error al leer archivos locales: {e}")

# Respaldo con uploader manual si no se encuentran en la ruta
if df1 is None or df1.empty:
  st.sidebar.info(
      "No se detectaron los archivos `temp` y `hum` en la raíz del repositorio."
      " Puede cargarlos manualmente."
  )
  uploaded_file = st.sidebar.file_uploader(
      "Cargar archivo CSV consolidado", type=["csv"]
  )
  if uploaded_file is not None:
    df_original = pd.read_csv(uploaded_file)
    df1, _, _ = preparar_datos(df_original)
  else:
    st.warning("⚠️ Por favor, asegúrese de que los archivos `temp` y `hum` estén en el repositorio o cargue un archivo de respaldo.")
    st.stop()

df1, variables, col_tiempo = preparar_datos(df1)

if not variables:
  st.error("No se encontraron columnas numéricas válidas en los datos.")
  st.stop()

# ============================================================
#  Estructura de Pestañas
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Monitoreo en Vivo",
    "🥩 Conservación y Carnes",
    "📊 Estadísticas",
    "🔍 Filtros",
    "⚙️ Control y Ventilación",
])

# ----------------------------------------------------
#  TAB 1 · Monitoreo en Vivo
# ----------------------------------------------------
with tab1:
  st.subheader("Lecturas Actuales del Cuarto Frío")

  if not df1.empty:
    ultimo = df1.iloc[-1]
    
    # Identificar temperatura y humedad de forma segura
    col_t = next((c for c in variables if "temp" in c.lower()), variables[0])
    col_h = (
        next((c for c in variables if "hum" in c.lower()), variables[1])
        if len(variables) > 1
        else variables[0]
    )

    t_val = ultimo.get(col_t, 0)
    h_val = ultimo.get(col_h, 0)

    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Temperatura Actual",
        f"{t_val:.2f} °C",
        delta="Óptimo (<= -18°C)" if t_val <= -18 else "Alerta: Temperatura Alta",
    )
    m2.metric(
        "Humedad Relativa",
        f"{h_val:.1f} %",
        delta="Seguro (<= 70%)" if h_val <= 70 else "Peligro: Alta Humedad",
    )
    m3.metric(
        "Estado Sanitario",
        "Seguro" if t_val <= -18 and h_val <= 70 else "Revisar Alertas",
    )

    st.markdown("---")
    st.subheader("Tendencia Histórica Combinada")
    st.line_chart(df1[variables])

# ----------------------------------------------------
#  TAB 2 · Conservación y Carnes
# ----------------------------------------------------
with tab2:
  st.subheader("Análisis de Vida Útil y Descomposición de la Carne")
  st.write("""
        El control estricto de la temperatura y la humedad en el cuarto frío previene 
        la proliferación bacteriana y la descomposición prematura de los productos cárnicos.
    """)

  c1, c2 = st.columns(2)
  with c1:
    st.info("""
            **Umbrales de Temperatura:**
            * **Congelación (<= -18 °C):** Detiene la actividad microbiana. La carne se conserva de forma segura durante meses.
            * **Refrigeración (-2 °C a 2 °C):** Almacenamiento a corto plazo para carnes frescas (3 a 7 días según el corte).
            * **Zona de Peligro (> 4 °C):** Riesgo crítico de crecimiento de patógenos (*Salmonella, E. coli*), provocando descomposición rápida, malos olores y pérdida total del producto.
        """)
  with c2:
    st.success("""
            **Control de Humedad y Ventilación:**
            * Mantener la humedad por debajo del **70%** evita la condensación excesiva y la aparición de hongos superficiales.
            * El sistema activa la compuerta de ventilación automáticamente para renovar el aire cuando los niveles de humedad o temperatura se salen del rango óptimo.
        """)

# ----------------------------------------------------
#  TAB 3 · Estadísticas
# ----------------------------------------------------
with tab3:
  st.subheader("Resumen Estadístico")
  st.dataframe(df1[variables].describe().T.round(2))

  if len(variables) >= 2:
    st.write("#### Correlación entre Temperatura y Humedad")
    st.dataframe(df1[variables].corr().round(2))

# ----------------------------------------------------
#  TAB 4 · Filtros
# ----------------------------------------------------
with tab4:
  st.subheader("Filtrado de Registros por Variable")
  var_filtro = st.selectbox("Variable a filtrar", variables)
  min_v, max_v = float(df1[var_filtro].min()), float(df1[var_filtro].max())

  if min_v != max_v:
    rango = st.slider("Rango de valores", min_v, max_v, (min_v, max_v))
    filtrado = df1[df1[var_filtro].between(rango[0], rango[1])]
    st.dataframe(filtrado)
    st.download_button(
        "📥 Descargar datos filtrados (CSV)",
        filtrado.to_csv().encode("utf-8"),
        "datos_filtrados_carniceria.csv",
        "csv",
    )

# ----------------------------------------------------
#  TAB 5 · Control y Ventilación
# ----------------------------------------------------
with tab5:
  st.subheader("Estado de la Ventilación y Actuadores (Servomotor)")
  st.write("""
        Visualización del comportamiento del servo en función de las variables ambientales del cuarto frío.
    """)

  if not df1.empty:
    ultimo = df1.iloc[-1]
    t_val = ultimo.get(variables[0], -18)
    h_val = ultimo.get(variables[1] if len(variables) > 1 else variables[0], 50)

    if h_val > 70:
      estado_servo = "Abierto (180°) — Expulsando exceso de humedad"
    elif t_val <= -18:
      estado_servo = "Cerrado (0°) — Manteniendo frío óptimo"
    else:
      estado_servo = "Medio (90°) — Disipando temperatura alta"

    st.metric("Posición Actual de la Compuerta", estado_servo)

# ============================================================
#  Pie de página
# ============================================================
st.markdown("""
    ---
    **Sistema de Telemetría y Control de Cuarto Frío — Carnicería** | Universidad EAFIT
""")
