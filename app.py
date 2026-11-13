import base64
import time

import anthropic
import streamlit as st
from PIL import Image

MODEL_NAME = "claude-sonnet-5-5"
MAX_TOKENS = 2048
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

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
st.caption("Análisis técnico de price action y niveles clave con Claude Vision.")

# ---------------------------------------------------------------------------
# Barra lateral: credenciales y guía
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Tu clave se usa solo en esta sesión y no se guarda en el servidor.",
    )
    st.caption("Consigue una clave en [Anthropic Console](https://console.anthropic.com/settings/keys).")
    st.caption(f"Modelo en uso: `{MODEL_NAME}`")

    st.divider()
    st.markdown(
        """
        **¿Cómo usar TradeMentor IA?**
        1. Pega tu API Key de Anthropic.
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
image_bytes = None
image_media_type = None

if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()
    image_media_type = uploaded_file.type if uploaded_file.type in ("image/png", "image/jpeg") else "image/jpeg"
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


def build_user_text(context: str) -> str:
    context = (context or "").strip()
    if not context:
        return "Analiza el gráfico adjunto y entrega el reporte técnico."
    return f"Analiza el gráfico adjunto. Contexto adicional del usuario: {context}"


def is_transient_error(exc: Exception) -> bool:
    """Detecta saturación o errores temporales de la API de Anthropic."""
    if getattr(exc, "status_code", None) in (429, 500, 502, 503, 529):
        return True
    message = str(exc).upper()
    return "503" in message or "529" in message or "OVERLOADED" in message


def analyze_chart(client, image_bytes: bytes, media_type: str, user_text: str):
    """Envía la imagen a Claude y reintenta si la API está saturada."""
    content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.b64encode(image_bytes).decode("utf-8"),
            },
        },
        {"type": "text", "text": user_text},
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                system=PROMPT_BASE,
                messages=[{"role": "user", "content": content}],
            )
        except Exception as exc:
            if attempt == MAX_RETRIES or not is_transient_error(exc):
                raise
            st.info(
                f"Claude está con alta demanda temporalmente. "
                f"Reintentando en {RETRY_DELAY_SECONDS}s ({attempt}/{MAX_RETRIES})…"
            )
            time.sleep(RETRY_DELAY_SECONDS)


# ---------------------------------------------------------------------------
# Análisis con Claude
# ---------------------------------------------------------------------------
if analyze:
    if not api_key:
        st.error("Ingresa tu API Key de Anthropic en la barra lateral para continuar.")
    elif image is None:
        st.warning("Sube primero una imagen de tu gráfico.")
    else:
        try:
            with st.spinner("Analizando estructura de mercado, liquidez y price action con Claude..."):
                client = anthropic.Anthropic(api_key=api_key)
                response = analyze_chart(
                    client, image_bytes, image_media_type, build_user_text(user_prompt)
                )

            report = "".join(
                block.text for block in response.content if getattr(block, "type", None) == "text"
            ).strip()

            if not report:
                st.error("El modelo no devolvió contenido. Intenta de nuevo con otra imagen.")
            else:
                st.success("Análisis completado.")
                with st.container(border=True):
                    st.markdown("### 📊 Reporte de TradeMentor IA")
                    st.markdown(report)
        except anthropic.AuthenticationError:
            st.error("La API Key de Anthropic no es válida. Verifícala en la barra lateral.")
        except anthropic.RateLimitError:
            st.error("Se alcanzó el límite de peticiones de tu API Key. Espera un momento y reintenta.")
        except anthropic.NotFoundError:
            st.error(
                f"El modelo `{MODEL_NAME}` no está disponible para esta API Key. "
                "Verifica el acceso en Anthropic Console."
            )
        except Exception as exc:
            if is_transient_error(exc):
                st.error(
                    "Claude no respondió tras varios intentos por alta demanda. "
                    "Es temporal: espera un momento y vuelve a intentarlo."
                )
            else:
                st.error(f"No se pudo completar el análisis: {exc}")
elif image is None:
    st.info("👆 Carga una imagen de tu gráfico para comenzar el análisis técnico.")
