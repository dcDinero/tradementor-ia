import streamlit as st
from PIL import Image
from google import genai

# Configuración de la página
st.set_page_config(
    page_title="TradeMentor IA",
    page_icon="📈",
    layout="centered"
)

st.title("📈 TradeMentor IA")
st.markdown("Tu mentor de trading inteligente impulsado por **Gemini Vision**. Sube la captura de pantalla de tu gráfico para recibir un análisis técnico detallado.")

# Configuración de la API Key en la barra lateral
st.sidebar.header("⚙️ Configuración")
api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password")

st.sidebar.markdown("""
---
**¿Cómo usar TradeMentor IA?**
1. Ingresa tu clave de API de Google Gemini.
2. Sube una imagen de tu gráfico (TradingView, MetaTrader, etc.).
3. Escribe cualquier contexto adicional (temporalidad, activo).
4. Haz clic en **Analizar Gráfico**.
""")

# Área principal de la aplicación
uploaded_file = st.file_uploader("Sube la captura de tu gráfico (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

user_prompt = st.text_input(
    "Contexto adicional o pregunta (Opcional):",
    placeholder="Ej: ¿Ves alguna ruptura de rango o zona de liquidez clara en 1 hora para EURUSD?"
)

if uploaded_file is not None:
    # Mostrar la imagen cargada
    image = Image.open(uploaded_file)
    st.image(image, caption="Gráfico cargado para análisis", use_container_width=True)

    if st.button("🚀 Analizar Gráfico", type="primary"):
        if not api_key:
            st.error("Por favor, ingresa tu API Key de Gemini en la barra lateral antes de continuar.")
        else:
            try:
                with st.spinner("Analizando acción del precio, mechas y estructuras de mercado..."):
                    # Inicializar el cliente de Gemini
                    client = genai.Client(api_key=api_key)
                    
                    # Prompt especializado para trading
                    prompt_base = (
                        "Eres un trader profesional experto en análisis técnico, price action, "
                        "interpretación de mechas, zonas de liquidez y ruptura de rangos. "
                        "Analiza detalladamente esta captura de pantalla de un gráfico de trading e identifica: "
                        "1. Tendencia actual y estructura de mercado. "
                        "2. Niveles clave de soporte y resistencia / zonas de liquidez. "
                        "3. Patrones de velas o rechazos (mechas). "
                        "4. Posibles escenarios operativos (riesgo/beneficio sugerido). "
                        "Sé directo, profesional y claro en tus conclusiones."
                    )
                    
                    if user_prompt:
                        full_prompt = f"{prompt_base}\n\nContexto adicional del usuario: {user_prompt}"
                    else:
                        full_prompt = prompt_base

                    # Llamada a Gemini Flash (modelo multimodal optimizado para visión)
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=[image, full_prompt]
                    )

                    # Mostrar resultados
                    st.success("¡Análisis completado con éxito!")
                    st.markdown("### 📊 Reporte de TradeMentor IA")
                    st.write(response.text)

            except Exception as e:
                st.error(f"Ocurrió un error al procesar el análisis con la API: {e}")
else:
    st.info("👆 Por favor, carga una imagen para comenzar el análisis técnico.")
