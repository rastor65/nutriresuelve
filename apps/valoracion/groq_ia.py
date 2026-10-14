import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def generar_plan_alimentario(paciente, clasificacion, alimentos):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error IA: configura GROQ_API_KEY en el archivo .env para generar el plan alimentario."

    client = Groq(api_key=api_key)
    nombres_alimentos = ", ".join([a.nombre for a in alimentos]) if alimentos else "alimentos básicos del PAE"

    prompt = f"""
    Eres un asistente nutricional especializado en nutrición infantil en zonas vulnerables de Colombia.
    
    Genera un plan alimentario personalizado para el siguiente paciente:
    
    - Nombre: {paciente.nombre_completo}
    - Edad: {paciente.edad} años
    - IMC: {paciente.imc}
    - Estado nutricional: {clasificacion}
    - Nivel socioeconómico: {paciente.get_nivel_socioeconomico_display()}
    - Nivel de actividad física: {paciente.get_nivel_actividad_display()}
    - Alergias: {", ".join([a.descripcion for a in paciente.alergias.all()]) or "ninguna"}
    - Alimentos PAE disponibles: {nombres_alimentos}
    
    El plan debe:
    1. Usar solo los alimentos PAE disponibles
    2. Incluir recomendaciones para desayuno, almuerzo y cena
    3. Considerar las alergias del paciente
    4. Ser comprensible para padres o cuidadores
    5. Incluir una meta nutricional para el próximo mes
    
    Responde en español, de forma clara y empática. Máximo 300 palabras.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error IA: {type(e).__name__}: {str(e)}"
