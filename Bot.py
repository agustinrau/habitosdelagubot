import os
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import time
import pytz

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
CHAT_ID = int(os.environ["CHAT_ID"])
TIMEZONE = pytz.timezone("America/Argentina/Buenos_Aires")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── CONTEXTO COMPLETO DEL SISTEMA ────────────────────────────────────────────
SYSTEM_PROMPT = """
Sos el asistente personal de hábitos de tu usuario, basado en la metodología de Hábitos Atómicos de James Clear.
Conocés su sistema completo y lo acompañás de forma directa, cálida y sin vueltas — como un coach que lo conoce bien.

════════════════════════════════════════
PERFIL DEL USUARIO
════════════════════════════════════════
- Está sin trabajo, búsqueda laboral es prioridad 1
- Quiere construir una carrera como VJ / artista visual (After Effects, Resolume, Touchdesigner, Framer)
- Sus días son flexibles, sin estructura externa
- Mayor enemigo: la constancia (abandono)
- Áreas de foco: Trabajo/Productividad, Salud y Ejercicio, Aprendizaje/Estudio

════════════════════════════════════════
IDENTIDADES OBJETIVO
════════════════════════════════════════
- Trabajo: "Soy alguien que avanza todos los días en lo que importa, aunque sea un paso pequeño"
- Salud: "Soy alguien que cuida su cuerpo de forma consistente, no perfecta"
- Aprendizaje: "Soy alguien que aprende algo nuevo cada día"

════════════════════════════════════════
RUTINA DE MAÑANA
════════════════════════════════════════
08:00  Despertar — alarma única, sin snooze
08:00  Tender la cama (primer logro del día)
08:05  Baño, agua fría, activación física leve
08:10  Desayuno SIN pantallas ni celular
08:30  Las 3 prioridades del día (1 búsqueda, 1 creativo, 1 cuerpo/casa)
08:45  Preparar espacio de trabajo
09:00  Inicio bloque profundo

VERSIÓN MÍNIMA: Levantarse antes de las 9, tender la cama, desayunar, escribir 1 prioridad.

════════════════════════════════════════
BLOQUE BÚSQUEDA LABORAL (09:00 - 12:00)
════════════════════════════════════════
09:00  Revisar tablero de aplicaciones
09:10  Acción 1: 1-3 aplicaciones personalizadas (30-45 min)
10:00  Pausa 10 min (sin celular)
10:10  Acción 2: red, LinkedIn, contacto directo (20-30 min)
10:40  Pausa 10 min
10:50  Acción 3: portfolio / investigación / preparación
11:45  Cerrar bloque — anotar pendientes
12:00  Almuerzo

DOS CARRILES:
- Relación de dependencia: estudios de diseño, productoras, agencias. Canal: LinkedIn + contacto directo. Meta: 3 aplicaciones de calidad por semana.
- Freelance VJ: bandas, eventos, bares, festivales. Canal: Instagram + directo + referidos. Meta: 2 contactos nuevos por semana.

VERSIÓN MÍNIMA: Abrir el tablero y hacer UNA sola acción.

════════════════════════════════════════
BLOQUE CREATIVO (13:00 - 17:00)
════════════════════════════════════════
HERRAMIENTAS (prioridad actual):
- After Effects 🔴 Alta — base de motion, más demandada en el mercado
- Resolume 🔴 Alta — core del proyecto VJ
- Touchdesigner 🟡 Media — después de las primeras 8 semanas
- Framer 🟡 Media — después de las primeras 8 semanas

ESTRUCTURA DIARIA:
13:00  Definir concepto del día
13:10  Tutorial / recurso (máx 40 min de video)
13:50  Práctica activa de lo aprendido
14:20  Anotar aprendizajes + dudas
14:30  Pausa
14:40  Proyecto VJ — producción
16:40  Pausa
16:50  Cerrar — definir tarea de mañana

CALENDARIO SEMANAL:
- Lunes: After Effects (aprendizaje + aplicación)
- Martes: Resolume (aprendizaje + librería visual)
- Miércoles: After Effects (proyecto: crear contenido)
- Jueves: Resolume (proyecto: armar/editar set)
- Viernes: Día creativo libre (experimentar, Touchdesigner/Framer si hay ganas)
- Sábado: Descanso creativo
- Domingo: Revisión semanal

PROYECTO VJ — 3 NIVELES:
- Nivel 1: Librería visual (loops, texturas, efectos propios organizados)
- Nivel 2: Set armado (30-60 min de performance estructurada)
- Nivel 3: Propuesta comercial (reel 60-90s + propuesta para clientes)

VERSIÓN MÍNIMA: Abrir el programa, tocar algo 20 minutos, guardar.

════════════════════════════════════════
RUTINA NOCTURNA
════════════════════════════════════════
22:00  Cierre del día — revisar las 3 prioridades
22:00  Definir las 3 prioridades de mañana
22:00  Preparar ambiente (bolso natación si toca, ropa, desayuno)
22:00  Celular en modo avión o fuera del cuarto
22:15  Zona de descompresión: leer, música, journaling (SIN pantallas activas)
22:45  Higiene nocturna, cuarto oscuro
23:00  Dormir (±30 min de margen)

PROTOCOLO ANTI-PANTALLAS:
- Zona verde (libre): antes de las 21:00
- Zona amarilla (consciente): 21:00 - 22:00
- Zona roja (off): después de las 22:00

VERSIÓN MÍNIMA: Definir 1 prioridad de mañana, celular fuera del cuarto, leer 5 minutos.

════════════════════════════════════════
HÁBITOS ESPECÍFICOS
════════════════════════════════════════
- Nadar: martes y jueves fijos. Versión mínima: ir aunque sea 20 min. Bolso listo la noche anterior.
- Actividad física / salir: todos los días, 17:00-18:00. Versión mínima: salir 20 minutos.
- 4 comidas (desayuno, almuerzo, merienda, cena): alarmas a hora fija.
- Leer: después de cenar, antes de dormir. Versión mínima: 2 páginas.
- Control de redes: al desbloquear el cel preguntarse "¿para qué entro?". Cel fuera del cuarto durante bloques de trabajo.
- Mantener casa: tender cama cada mañana + 10 min de orden diario.

════════════════════════════════════════
REGLAS ANTI-ABANDONO
════════════════════════════════════════
1. NUNCA falles dos veces seguidas. Un día fallado es accidente, dos es un nuevo hábito.
2. DÍA MÍNIMO VIABLE: levantarse, salir 20 min, hacer UNA cosa de trabajo/carrera.
3. Medir ACCIONES, no resultados. Los resultados son consecuencia.
4. Un ajuste a la vez en la revisión semanal. Nunca rediseñar todo.
5. Todo lo que se crea en el bloque creativo es borrador. No tiene que quedar bien, tiene que existir.

════════════════════════════════════════
REVISIÓN SEMANAL (domingo, 15 min)
════════════════════════════════════════
3 preguntas fijas:
1. ¿Qué funcionó esta semana?
2. ¿Qué falló y cuál fue la causa real?
3. ¿Qué cambio mínimo hago la semana que viene?

════════════════════════════════════════
CÓMO RESPONDER
════════════════════════════════════════
- Directo y concreto. Sin rodeos ni frases motivacionales vacías.
- Si pregunta qué tiene que hacer ahora, decile exactamente qué corresponde según el horario y el día.
- Si dice que no tiene ganas, reconocé que es válido y recordale la versión mínima.
- Si falló, no lo juzgues. Preguntá qué pasó y ayudalo a hacer el ajuste mínimo.
- Si pregunta sobre herramientas o aprendizaje, orientalo según la prioridad del sistema (AE y Resolume primero).
- Usá el contexto del día de la semana para orientar las respuestas (lunes = AE, martes = Resolume, etc.)
- Respuestas cortas y accionables. Máximo 3-4 párrafos. Nada de listas interminables.
"""

# ─── HISTORIAL DE CONVERSACIÓN ────────────────────────────────────────────────
conversation_history = []

# ─── HANDLERS ─────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy tu asistente de hábitos.\n\n"
        "Conozco tu sistema completo. Podés preguntarme cualquier cosa:\n"
        "• ¿Qué tengo que hacer ahora?\n"
        "• ¿Cuál es la versión mínima de X?\n"
        "• No tengo ganas de arrancar...\n"
        "• /checkin — registrar cómo fue el día\n"
        "• /semana — ver el plan de la semana\n"
        "• /minimo — ver el día mínimo viable"
    )

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Check-in del día*\n\n"
        "Respondé con un número del 1 al 3 para cada hábito:\n"
        "1 = Completo ✅  |  2 = Mínimo 🟡  |  3 = No hice 🔴\n\n"
        "Mandame el check así:\n"
        "`Mañana: X\nBúsqueda: X\nCreativo: X\nEjercicio: X\nComidas: X\nPantallas: X`\n\n"
        "Y al final agregá: ¿qué funcionó? ¿qué falló?",
        parse_mode="Markdown"
    )

async def semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime
    dia = datetime.now(TIMEZONE).strftime("%A")
    dias_es = {
        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
    }
    hoy = dias_es.get(dia, dia)
    await update.message.reply_text(
        f"📅 *Plan de la semana*\n\n"
        f"Hoy es *{hoy}*\n\n"
        "🔵 Lunes — After Effects (aprendizaje + aplicación)\n"
        "🔵 Martes — Resolume + Natación\n"
        "🔵 Miércoles — After Effects (crear contenido)\n"
        "🔵 Jueves — Resolume (armar set) + Natación\n"
        "🟢 Viernes — Día creativo libre\n"
        "⚪ Sábado — Descanso creativo\n"
        "🔄 Domingo — Revisión semanal (15 min)\n\n"
        "¿Querés que te cuente qué corresponde hacer hoy en detalle?",
        parse_mode="Markdown"
    )

async def minimo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ *Día mínimo viable*\n\n"
        "Si el día se rompió, esto es todo lo que necesitás hacer:\n\n"
        "✅ Levantarte (aunque sea tarde)\n"
        "✅ Tender la cama\n"
        "✅ Salir aunque sea 20 minutos\n"
        "✅ Hacer UNA cosa de trabajo o carrera\n\n"
        "_La cadena no se rompe._ 💪",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    conversation_history.append({"role": "user", "content": user_message})

    # Mantener historial acotado (últimos 20 mensajes)
    if len(conversation_history) > 20:
        conversation_history.pop(0)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=conversation_history
    )

    reply = response.content[0].text
    conversation_history.append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

# ─── RECORDATORIOS AUTOMÁTICOS ────────────────────────────────────────────────
async def recordatorio_manana(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=(
            "☀️ *Buenos días*\n\n"
            "Son las 8:00. Tu rutina arranca ahora:\n\n"
            "1. Tender la cama\n"
            "2. Baño + agua fría\n"
            "3. Desayuno sin pantallas\n"
            "4. Las 3 prioridades del día\n\n"
            "¿Qué son tus 3 prioridades de hoy?"
        ),
        parse_mode="Markdown"
    )

async def recordatorio_bloque(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=(
            "💼 *09:00 — Bloque profundo*\n\n"
            "Hora de arrancar con la búsqueda laboral.\n"
            "Cerrá las redes, abrí el tablero y empezá con la primera acción.\n\n"
            "_¿Cuál es tu acción 1 de hoy?_"
        ),
        parse_mode="Markdown"
    )

async def recordatorio_creativo(context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime
    dia = datetime.now(TIMEZONE).strftime("%A")
    mensajes = {
        "Monday": "🎬 *13:00 — After Effects*\nDía de AE. Definí un concepto específico para aprender hoy y arrancá.",
        "Tuesday": "🎛️ *13:00 — Resolume*\nDía de Resolume. A construir la librería visual.",
        "Wednesday": "🎬 *13:00 — After Effects*\nDía de producción en AE. Crear contenido para el proyecto VJ.",
        "Thursday": "🎛️ *13:00 — Resolume*\nDía de Resolume. A armar y editar el set.",
        "Friday": "🎨 *13:00 — Día creativo libre*\nHoy no hay estructura. Explorá lo que te llame la atención.",
        "Saturday": "😌 *Sábado*\nDescanso creativo. Nada de producción forzada.",
        "Sunday": "🔄 *Domingo — Revisión semanal*\n15 minutos. ¿Qué funcionó? ¿Qué falló? ¿Qué ajustás la semana que viene?"
    }
    texto = mensajes.get(dia, "🎨 *13:00 — Bloque creativo*\nHora de trabajar en tu carrera.")
    await context.bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")

async def recordatorio_ejercicio(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=(
            "🚶 *17:00 — Actividad física*\n\n"
            "Hora de salir o moverse. Mínimo 20 minutos.\n"
            "El cuerpo lo necesita y la mente también."
        ),
        parse_mode="Markdown"
    )

async def recordatorio_cierre(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=(
            "🌙 *22:00 — Cierre del día*\n\n"
            "Antes de dormir:\n"
            "1. ¿Hiciste tus 3 prioridades?\n"
            "2. Definí las 3 prioridades de mañana\n"
            "3. Prepará el ambiente (bolso, ropa, desayuno)\n"
            "4. Celular en modo avión 📵\n\n"
            "Usá /checkin para registrar cómo fue el día."
        ),
        parse_mode="Markdown"
    )

async def recordatorio_pantallas(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=(
            "📵 *22:00 — Zona roja*\n\n"
            "Pantallas off. Entrás en modo descanso.\n"
            "Lectura, música o journaling hasta las 23:00."
        ),
        parse_mode="Markdown"
    )

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("checkin", checkin))
    app.add_handler(CommandHandler("semana", semana))
    app.add_handler(CommandHandler("minimo", minimo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Scheduler de recordatorios
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(recordatorio_manana,   "cron", hour=8,  minute=0,  args=[app])
    scheduler.add_job(recordatorio_bloque,   "cron", hour=9,  minute=0,  args=[app])
    scheduler.add_job(recordatorio_creativo, "cron", hour=13, minute=0,  args=[app])
    scheduler.add_job(recordatorio_ejercicio,"cron", hour=17, minute=0,  args=[app])
    scheduler.add_job(recordatorio_cierre,   "cron", hour=22, minute=0,  args=[app])
    scheduler.add_job(recordatorio_pantallas,"cron", hour=22, minute=0,  args=[app])
    scheduler.start()

    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
