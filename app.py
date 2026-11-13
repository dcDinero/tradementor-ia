import streamlit as st
from PIL import Image
from google import genai

# ---------------------------------------------------------------------------
# Configuración de la página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TradeMentor IA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 TradeMentor IA")
st.caption("Análisis técnico de price action y niveles clave con Gemini Vision.")

# ---------------------------------------------------------------------------
# Barra lateral: credenciales y guía
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Tu clave se usa solo en esta sesión y no se guarda en el servidor.",
    )
    st.caption("Consigue una clave gratuita en [Google AI Studio](https://aistudio.google.com/apikey).")

    st.divider()
    st.markdown(
        """
        **¿Cómo usar TradeMentor IA?**
        1. Pega tu API Key de Google Gemini.
        2. Sube la captura de tu gráfico (TradingView, MetaTrader, etc.).
        3. Añade contexto: activo, temporalidad o la duda que tengas.
        4. Pulsa **Analizar Gráfico**.
        """
    )
    st.divider()
    st.caption("⚠️ Contenido educativo. No constituye asesoramiento financiero.")

# ---------------------------------------------------------------------------
# Área principal: carga del gráfico y contexto
# ---------------------------------------------------------------------------
col_upload, col_context = st.columns([3, 2], gap="large")

with col_upload:
    uploaded_file = st.file_uploader(
        "Sube la captura de tu gráfico",
        type=["png", "jpg", "jpeg"],
        help="Formatos admitidos: PNG, JPG y JPEG.",
    )

with col_context:
    user_prompt = st.text_area(
        "Contexto adicional (opcional)",
        placeholder="Ej: EURUSD en 1H, busco confirmación de ruptura del rango asiático.",
        height=140,
    )

image = None
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    with col_upload:
        st.image(image, caption="Gráfico cargado para análisis", use_container_width=True)

analyze = st.button(
    "🚀 Analizar Gráfico",
    type="primary",
    use_container_width=True,
    disabled=image is None,
)

# ---------------------------------------------------------------------------
# Prompt especializado
# ---------------------------------------------------------------------------
PROMPT_BASE = """Eres un analista técnico profesional especializado en price action, estructura de mercado,
zonas de liquidez institucional y gestión de riesgo. Analiza la captura de un gráfico de trading
y entrega un reporte técnico claro, objetivo y accionable.

Usa exactamente esta estructura en Markdown:

## 1. Contexto del gráfico
Activo, temporalidad y rango visible (si se pueden inferir del gráfico).

## 2. Tendencia y estructura de mercado
Tendencia dominante (alcista, bajista o lateral), secuencia de máximos/mínimos,
última estructura relevante (BOS/CHOCH si aplica).

## 3. Niveles clave
Tabla Markdown con columnas: Nivel | Tipo (soporte/resistencia/liquidez) | Precio aproximado | Por qué importa.

## 4. Price action y patrones
Velas relevantes, rechazos, mechas, consolidaciones, patrones de continuación o agotamiento.

## 5. Escenarios operativos
Dos escenarios (alcista y bajista) con: zona de entrada, invalidación (stop), objetivo
y relación riesgo/beneficio estimada. Si el gráfico no permite definirlos con claridad, dilo.

## 6. Conclusión del mentor
Sesgo operativo, nivel a vigilar y advertencia de riesgo.

Reglas:
- Sé directo y profesional; evita relleno y promesas de rentabilidad.
- Basa cada afirmación en lo visible en la imagen; si algo no se distingue, indícalo.
- Usa precios aproximados cuando los ejes no sean legibles.
- Responde en español.
"""


def build_prompt(context: str) -> str:
    context = (context or "").strip()
    if not context:
        return PROMPT_BASE
    return f"{PROMPT_BASE}\nContexto adicional del usuario: {context}"


# ---------------------------------------------------------------------------
# Análisis con Gemini
# ---------------------------------------------------------------------------
if analyze:
    if not api_key:
        st.error("Ingresa tu API Key de Gemini en la barra lateral para continuar.")
    elif image is None:
        st.warning("Sube primero una imagen de tu gráfico.")
    else:
        try:
            with st.spinner("Analizando estructura de mercado, liquidez y price action..."):
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[image, build_prompt(user_prompt)],
                )
            report = (response.text or "").strip()

            if not report:
                st.error("El modelo no devolvió contenido. Intenta de nuevo con otra imagen.")
            else:
                st.success("Análisis completado.")
                with st.container(border=True):
                    st.markdown("### 📊 Reporte de TradeMentor IA")
                    st.markdown(report)
        except Exception as exc:
            message = str(exc)
            if "API_KEY" in message.upper() or "PERMISSION" in message.upper() or "401" in message:
                st.error("La API Key no es válida o no tiene permisos para Gemini. Verifícala en la barra lateral.")
            elif "quota" in message.lower() or "429" in message:
                st.error("Se agotó la cuota de la API Key. Revisa tu plan en Google AI Studio.")
            else:
                st.error(f"No se pudo completar el análisis: {message}")
elif image is None:
    st.info("👆 Carga una imagen de tu gráfico para comenzar el análisis técnico.")
