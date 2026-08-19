# -*- coding: utf-8 -*-
import datetime
import calendar
import os.path
import io
import pandas as pd
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Mem-Aid Pro | Agenda & Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTADO GLOBAL Y CATEGORÍAS POR DEFECTO ---
CATEGORIAS_BASE = {
    "Trabajo / Guardias": {"id": "6", "icono": "💼", "badge": "🟠", "color_hex": "#F4511E"},
    "Urgente / Médico": {"id": "11", "icono": "🩺", "badge": "🔴", "color_hex": "#D50000"},
    "Hogar / Bricolaje": {"id": "10", "icono": "🏠", "badge": "🟢", "color_hex": "#0B8043"},
    "Vehículos / Taller": {"id": "9", "icono": "🚗", "badge": "🔵", "color_hex": "#3F51B5"},
    "Personal / Familia": {"id": "3", "icono": "👨‍👩‍👦", "badge": "🟣", "color_hex": "#8E24AA"},
    "Recordatorio": {"id": "5", "icono": "⭐", "badge": "🟡", "color_hex": "#E4C441"},
    "Proyectos / Cursos": {"id": "7", "icono": "📚", "badge": "🩵", "color_hex": "#039BE5"},
    "General": {"id": "8", "icono": "📌", "badge": "⚪", "color_hex": "#616161"}
}

if "categorias_custom" not in st.session_state:
    st.session_state["categorias_custom"] = CATEGORIAS_BASE.copy()

if "evento_en_edicion" not in st.session_state:
    st.session_state["evento_en_edicion"] = None

# --- MAPEO DE COLORES GOOGLE ---
COLOR_ID_MAP = {v["id"]: {"nombre": k, "icono": v["icono"], "badge": v["badge"]} for k, v in st.session_state["categorias_custom"].items()}
COLOR_ID_MAP.update({
    "1": {"nombre": "Personal / Lavanda", "icono": "💜", "badge": "🟣"},
    "2": {"nombre": "Salud / Salvia", "icono": "🌿", "badge": "🟢"},
    "4": {"nombre": "Social / Flamenco", "icono": "🌸", "badge": "🌸"}
})

def get_calendar_service():
    """Autentica y devuelve el cliente de la API de Google Calendar."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

# --- BARRA LATERAL: PERSONALIZACIÓN & AJUSTES ---
with st.sidebar:
    st.markdown("### ⚙️ Panel de Control")
    modo_tema = st.radio("Tema visual:", ["🌙 Modo Oscuro", "☀️ Modo Claro"], index=0)
    zona_horaria = st.selectbox("Zona Horaria:", ["Europe/Madrid", "UTC", "America/New_York", "America/Mexico_City", "America/Argentina/Buenos_Aires"], index=0)
    
    st.divider()
    st.markdown("### 🏷️ Personalización de Categorías")
    with st.expander("Añadir nueva categoría"):
        nueva_cat_nom = st.text_input("Nombre de categoría:", placeholder="Ej: Gimnasio / Deporte")
        c_ic, c_col = st.columns(2)
        with c_ic:
            nuevo_ic = st.selectbox("Icono:", ["🏋️", "✈️", "💰", "🎓", "🛒", "💻", "🎨", "🐾"])
        with c_col:
            color_g_id = st.selectbox("Color Google:", ["1", "2", "3", "4", "5", "6", "7", "9", "10", "11"], index=5)
        
        if st.button("➕ Crear Categoría", use_container_width=True):
            if nueva_cat_nom.strip():
                st.session_state["categorias_custom"][nueva_cat_nom] = {
                    "id": color_g_id,
                    "icono": nuevo_ic,
                    "badge": "🔹",
                    "color_hex": "#2563eb"
                }
                st.success(f"Categoría '{nueva_cat_nom}' añadida.")
                st.rerun()

    st.divider()
    st.caption("Mem-Aid Pro v2.5 | Conexión directa Google API")

# --- ESTILOS VISUALES ---
if modo_tema == "🌙 Modo Oscuro":
    css_tema = """
        <style>
        .stApp { background-color: #0e1117; color: #e6edf3; }
        .main-header {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 20px; border-radius: 12px; text-align: center;
            border: 1px solid #334155; margin-bottom: 20px;
        }
        .main-header h2 { color: #38bdf8 !important; margin: 0; }
        .main-header p { color: #94a3b8 !important; margin: 5px 0 0 0; }
        .cal-box { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 8px; min-height: 90px; }
        .cal-box-header { font-weight: bold; color: #38bdf8; margin-bottom: 4px; }
        .cal-event-tag { font-size: 11px; background-color: #334155; border-radius: 4px; padding: 2px 5px; margin-bottom: 2px; }
        </style>
    """
else:
    css_tema = """
        <style>
        .stApp { background-color: #f8fafc; color: #0f172a; }
        .main-header {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            padding: 20px; border-radius: 12px; text-align: center;
            box-shadow: 0 4px 12px rgba(2,132,199,0.15); margin-bottom: 20px;
        }
        .main-header h2 { color: #ffffff !important; margin: 0; }
        .main-header p { color: #e0f2fe !important; margin: 5px 0 0 0; }
        .cal-box { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; min-height: 90px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .cal-box-header { font-weight: bold; color: #0284c7; margin-bottom: 4px; }
        .cal-event-tag { font-size: 11px; background-color: #f1f5f9; border-radius: 4px; padding: 2px 5px; margin-bottom: 2px; }
        </style>
    """
st.markdown(css_tema, unsafe_allow_html=True)

# Encabezado Principal
st.markdown("""
    <div class="main-header">
        <h2>📅 Mem-Aid Pro Agenda</h2>
        <p>Gestión avanzada por años, cuadrícula interactiva y analítica de citas</p>
    </div>
""", unsafe_allow_html=True)

try:
    service = get_calendar_service()
except Exception as e:
    st.error(f"Error conectando con Google Calendar: {e}")
    st.stop()

# --- PESTAÑAS PRINCIPALES ---
tab_anual, tab_lista, tab_crear, tab_metricas = st.tabs([
    "🗓️ Cuadrícula Anual / Mensual",
    "📋 Vista de Lista & Edición",
    "➕ Programar Cita",
    "📊 Analítica & Exportación"
])

# =========================================================
# PESTAÑA 1: VISUALIZACIÓN POR AÑOS Y MESES (CUADRÍCULA)
# =========================================================
with tab_anual:
    hoy_actual = datetime.date.today()
    c_y, c_m, c_nav = st.columns([1.5, 2, 3])
    
    with c_y:
        anio_sel = st.selectbox("Año:", list(range(hoy_actual.year - 5, hoy_actual.year + 11)), index=5)
    with c_m:
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_sel_idx = st.selectbox("Mes:", range(1, 13), format_func=lambda x: meses_nombres[x-1], index=hoy_actual.month - 1)

    # Calcular rango de fechas para el mes seleccionado
    primer_dia_mes = datetime.datetime(anio_sel, mes_sel_idx, 1, 0, 0, 0)
    ultimo_dia_num = calendar.monthrange(anio_sel, mes_sel_idx)[1]
    fin_dia_mes = datetime.datetime(anio_sel, mes_sel_idx, ultimo_dia_num, 23, 59, 59)

    eventos_mes_res = service.events().list(
        calendarId='primary',
        timeMin=primer_dia_mes.isoformat() + 'Z',
        timeMax=fin_dia_mes.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    eventos_mes = eventos_mes_res.get('items', [])

    # Agrupar eventos por día del mes
    eventos_por_dia = {d: [] for d in range(1, ultimo_dia_num + 1)}
    for ev in eventos_mes:
        inicio_raw = ev['start'].get('dateTime', ev['start'].get('date'))
        try:
            d_obj = datetime.datetime.fromisoformat(inicio_raw.replace('Z', '+00:00'))
            if d_obj.month == mes_sel_idx and d_obj.year == anio_sel:
                eventos_por_dia[d_obj.day].append(ev)
        except Exception:
            pass

    st.markdown(f"### 📅 {meses_nombres[mes_sel_idx-1]} {anio_sel}")
    
    # Encabezados de días de la semana
    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    cols_dias = st.columns(7)
    for i, col in enumerate(cols_dias):
        col.markdown(f"<div style='text-align: center; font-weight: bold;'>{dias_semana[i]}</div>", unsafe_allow_html=True)

    # Matriz del mes
    cal_matriz = calendar.monthcalendar(anio_sel, mes_sel_idx)
    for semana in cal_matriz:
        cols_sem = st.columns(7)
        for d_idx, dia_num in enumerate(semana):
            with cols_sem[d_idx]:
                if dia_num == 0:
                    st.write("")
                else:
                    evs_del_dia = eventos_por_dia.get(dia_num, [])
                    es_hoy = (dia_num == hoy_actual.day and mes_sel_idx == hoy_actual.month and anio_sel == hoy_actual.year)
                    badge_hoy = "⭐ " if es_hoy else ""
                    
                    with st.container(border=True):
                        st.markdown(f"**{badge_hoy}{dia_num}**")
                        if not evs_del_dia:
                            st.caption("-")
                        else:
                            for ev in evs_del_dia[:3]:
                                col_id = ev.get('colorId', '8')
                                icono = COLOR_ID_MAP.get(col_id, {}).get("icono", "📌")
                                tit_corto = ev.get('summary', 'Sin título')[:12]
                                st.caption(f"{icono} {tit_corto}")
                            if len(evs_del_dia) > 3:
                                st.caption(f"+{len(evs_del_dia)-3} más")

# =========================================================
# PESTAÑA 2: VISTA DE LISTA, BÚSQUEDA Y EDICIÓN
# =========================================================
with tab_lista:
    c_b1, c_b2, c_b3 = st.columns([2, 2, 1])
    with c_b1:
        txt_buscar = st.text_input("Buscar cita:", placeholder="🔍 Filtrar texto...", label_visibility="collapsed")
    with c_b2:
        cat_filtro = st.selectbox("Filtrar por categoría:", ["Todas las categorías"] + list(st.session_state["categorias_custom"].keys()), label_visibility="collapsed")
    with c_b3:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.session_state["evento_en_edicion"] = None
            st.rerun()

    hoy_inicio = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    eventos_lista_res = service.events().list(
        calendarId='primary',
        timeMin=hoy_inicio.isoformat() + 'Z',
        maxResults=60,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    eventos_todos = eventos_lista_res.get('items', [])

    if cat_filtro != "Todas las categorías":
        c_id = st.session_state["categorias_custom"][cat_filtro]["id"]
        eventos_todos = [ev for ev in eventos_todos if ev.get('colorId', '8') == c_id]

    if txt_buscar.strip():
        q = txt_buscar.lower()
        eventos_todos = [ev for ev in eventos_todos if q in ev.get('summary', '').lower() or q in ev.get('description', '').lower() or q in ev.get('location', '').lower()]

    if not eventos_todos:
        st.info("No se encontraron citas con los filtros aplicados.")
    else:
        for ev in eventos_todos:
            ev_id = ev['id']
            titulo = ev.get('summary', 'Sin título')
            ubicacion = ev.get('location', '')
            descripcion = ev.get('description', '')
            col_id = ev.get('colorId', '8')
            meta_cat = COLOR_ID_MAP.get(col_id, {"nombre": "General", "icono": "📌", "badge": "⚪"})
            
            inicio_raw = ev['start'].get('dateTime', ev['start'].get('date'))
            fin_raw = ev['end'].get('dateTime', ev['end'].get('date'))
            
            try:
                dt_i = datetime.datetime.fromisoformat(inicio_raw.replace('Z', '+00:00'))
                dt_f = datetime.datetime.fromisoformat(fin_raw.replace('Z', '+00:00'))
                fecha_fmt = dt_i.strftime("%d/%m/%Y")
                hora_fmt = dt_i.strftime("%H:%M h")
                dur_est = max(10, int((dt_f - dt_i).total_seconds() // 60))
                d_obj_edit = dt_i.date()
                h_obj_edit = dt_i.time()
            except Exception:
                fecha_fmt = inicio_raw
                hora_fmt = "Todo el día"
                dur_est = 60
                d_obj_edit = datetime.date.today()
                h_obj_edit = datetime.time(9, 0)

            with st.container(border=True):
                c_top1, c_top2 = st.columns([3, 1])
                with c_top1:
                    st.markdown(f"#### {meta_cat['badge']} {titulo}")
                    st.caption(f"Categoría: **{meta_cat['icono']} {meta_cat['nombre']}**")
                with c_top2:
                    st.markdown(f"📅 **{fecha_fmt}** | ⏰ `{hora_fmt}`")

                if ubicacion:
                    st.write(f"📍 **Lugar:** {ubicacion}")
                if descripcion:
                    st.write(f"📝 **Notas:** {descripcion}")

                # Alarmas
                reminders = ev.get('reminders', {})
                if 'overrides' in reminders and reminders['overrides']:
                    txt_al = [f"{o['minutes']} min" for o in reminders['overrides']]
                    st.caption(f"🔔 **Alarmas activas:** {', '.join(txt_al)} antes")

                st.divider()
                col_m1, col_m2, _ = st.columns([1.5, 1.5, 4])
                with col_m1:
                    if st.button("✏️ Modificar", key=f"edit_{ev_id}", use_container_width=True):
                        st.session_state["evento_en_edicion"] = None if st.session_state["evento_en_edicion"] == ev_id else ev_id
                        st.rerun()
                with col_m2:
                    if st.button("🗑️ Eliminar", key=f"del_{ev_id}", use_container_width=True):
                        service.events().delete(calendarId='primary', eventId=ev_id).execute()
                        st.toast("Cita eliminada.")
                        st.session_state["evento_en_edicion"] = None
                        st.rerun()

                # Panel de Edición en vivo
                if st.session_state["evento_en_edicion"] == ev_id:
                    with st.expander("🛠️ Editor de Cita", expanded=True):
                        with st.form(f"f_edit_{ev_id}"):
                            e_tit = st.text_input("Título:", value=titulo)
                            cats_keys = list(st.session_state["categorias_custom"].keys())
                            idx_def = 0
                            for idx_k, k_name in enumerate(cats_keys):
                                if st.session_state["categorias_custom"][k_name]["id"] == col_id:
                                    idx_def = idx_k
                                    break

                            e_cat = st.selectbox("Categoría:", cats_keys, index=idx_def)
                            cf1, cf2, cf3 = st.columns(3)
                            with cf1: e_fec = st.date_input("Fecha:", value=d_obj_edit)
                            with cf2: e_hor = st.time_input("Hora:", value=h_obj_edit)
                            with cf3: e_dur = st.number_input("Duración (min):", min_value=10, value=dur_est, step=10)

                            e_ub = st.text_input("Ubicación:", value=ubicacion)
                            e_des = st.text_area("Notas:", value=descripcion)

                            st.markdown("##### 🔔 Alarmas:")
                            ca1, ca2, ca3 = st.columns(3)
                            with ca1:
                                al_10 = st.checkbox("10m antes", value=True, key=f"a10_{ev_id}")
                                al_30 = st.checkbox("30m antes", value=False, key=f"a30_{ev_id}")
                            with ca2:
                                al_1h = st.checkbox("1h antes", value=True, key=f"a1h_{ev_id}")
                                al_2h = st.checkbox("2h antes", value=False, key=f"a2h_{ev_id}")
                            with ca3:
                                al_1d = st.checkbox("1d antes", value=False, key=f"a1d_{ev_id}")
                                al_2d = st.checkbox("2d antes", value=False, key=f"a2d_{ev_id}")

                            cs1, cs2 = st.columns(2)
                            with cs1: s_btn = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)
                            with cs2: c_btn = st.form_submit_button("❌ Cancelar", use_container_width=True)

                            if s_btn:
                                dt_start_n = datetime.datetime.combine(e_fec, e_hor)
                                dt_end_n = dt_start_n + datetime.timedelta(minutes=e_dur)
                                
                                al_list = []
                                if al_10: al_list.append({'method': 'popup', 'minutes': 10})
                                if al_30: al_list.append({'method': 'popup', 'minutes': 30})
                                if al_1h: al_list.append({'method': 'popup', 'minutes': 60})
                                if al_2h: al_list.append({'method': 'popup', 'minutes': 120})
                                if al_1d: al_list.append({'method': 'popup', 'minutes': 1440})
                                if al_2d: al_list.append({'method': 'popup', 'minutes': 2880})

                                mod_body = {
                                    'summary': e_tit,
                                    'location': e_ub,
                                    'description': e_des,
                                    'start': {'dateTime': dt_start_n.isoformat(), 'timeZone': zona_horaria},
                                    'end': {'dateTime': dt_end_n.isoformat(), 'timeZone': zona_horaria},
                                    'colorId': st.session_state["categorias_custom"][e_cat]["id"],
                                    'reminders': {'useDefault': False if al_list else True, 'overrides': al_list}
                                }
                                service.events().update(calendarId='primary', eventId=ev_id, body=mod_body).execute()
                                st.toast("✅ Modificado con éxito.")
                                st.session_state["evento_en_edicion"] = None
                                st.rerun()

                            if c_btn:
                                st.session_state["evento_en_edicion"] = None
                                st.rerun()

# =========================================================
# PESTAÑA 3: PROGRAMACIÓN DE NUEVAS CITAS
# =========================================================
with tab_crear:
    st.subheader("➕ Registrar Nueva Cita y Alertas")
    with st.form("form_alta_pro", border=True):
        n_tit = st.text_input("Título de la cita *", placeholder="Ej: Revisión médica, Guardias...")
        
        c_k1, c_k2 = st.columns([2, 1])
        with c_k1:
            n_cat = st.selectbox("Categoría / Color:", list(st.session_state["categorias_custom"].keys()))
        with c_k2:
            n_dur = st.number_input("Duración (minutos)", min_value=10, value=60, step=10)

        c_dt1, c_dt2 = st.columns(2)
        with c_dt1:
            n_fec = st.date_input("Fecha:", datetime.date.today())
        with c_dt2:
            n_hor = st.time_input("Hora de inicio:", datetime.time(10, 0))

        n_ub = st.text_input("Lugar / Ubicación:")
        n_des = st.text_area("Observaciones:")

        st.markdown("#### 🔔 Configuración de Notificaciones Móviles")
        ck1, ck2 = st.columns(2)
        with ck1:
            n_10m = st.checkbox("10 min antes", value=True)
            n_30m = st.checkbox("30 min antes", value=False)
            n_1h = st.checkbox("1 hora antes", value=True)
        with ck2:
            n_2h = st.checkbox("2 horas antes", value=False)
            n_1d = st.checkbox("1 día antes (24h)", value=False)
            n_2d = st.checkbox("2 días antes (48h)", value=False)

        crear_btn = st.form_submit_button("💾 Guardar en Google Calendar", type="primary", use_container_width=True)

        if crear_btn:
            if not n_tit.strip():
                st.error("El título es obligatorio.")
            else:
                dt_in = datetime.datetime.combine(n_fec, n_hor)
                dt_out = dt_in + datetime.timedelta(minutes=n_dur)
                
                n_rem = []
                if n_10m: n_rem.append({'method': 'popup', 'minutes': 10})
                if n_30m: n_rem.append({'method': 'popup', 'minutes': 30})
                if n_1h: n_rem.append({'method': 'popup', 'minutes': 60})
                if n_2h: n_rem.append({'method': 'popup', 'minutes': 120})
                if n_1d: n_rem.append({'method': 'popup', 'minutes': 1440})
                if n_2d: n_rem.append({'method': 'popup', 'minutes': 2880})

                new_event_body = {
                    'summary': n_tit,
                    'location': n_ub,
                    'description': n_des,
                    'start': {'dateTime': dt_in.isoformat(), 'timeZone': zona_horaria},
                    'end': {'dateTime': dt_out.isoformat(), 'timeZone': zona_horaria},
                    'colorId': st.session_state["categorias_custom"][n_cat]["id"],
                    'reminders': {'useDefault': False if n_rem else True, 'overrides': n_rem}
                }
                service.events().insert(calendarId='primary', body=new_event_body).execute()
                st.success("✅ Cita programada y sincronizada.")
                st.rerun()

# =========================================================
# PESTAÑA 4: ANALÍTICA Y EXPORTACIÓN
# =========================================================
with tab_metricas:
    st.subheader("📊 Analítica & Respaldo")
    
    # Construir DataFrame con todos los eventos para analítica
    data_evs = []
    for ev in eventos_todos:
        cid = ev.get('colorId', '8')
        nombre_c = COLOR_ID_MAP.get(cid, {}).get("nombre", "General")
        ini = ev['start'].get('dateTime', ev['start'].get('date'))
        data_evs.append({
            "Título": ev.get('summary', 'Sin título'),
            "Categoría": nombre_c,
            "Inicio": ini,
            "Ubicación": ev.get('location', ''),
            "Descripción": ev.get('description', '')
        })

    if data_evs:
        df = pd.DataFrame(data_evs)
        
        # Tarjetas de Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Citas Próximas", len(df))
        m2.metric("Categoría Principal", df["Categoría"].mode()[0] if not df.empty else "-")
        m3.metric("Ubicaciones Únicas", df["Ubicación"].nunique())

        st.divider()
        st.markdown("#### 📈 Distribución por Categorías")
        conteo_cats = df["Categoría"].value_counts()
        st.bar_chart(conteo_cats)

        st.divider()
        st.markdown("#### 📥 Exportar Agenda")
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        st.download_button(
            label="💾 Descargar Agenda en CSV / Excel",
            data=csv_buffer.getvalue(),
            file_name=f"MemAid_Agenda_{datetime.date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No hay suficientes datos para generar analíticas.")