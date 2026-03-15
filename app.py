import streamlit as st
from supabase import create_client
import datetime
import pandas as pd
from streamlit_calendar import calendar

# ---------------------------
# CONFIGURACIÓN Y CONEXIÓN
# ---------------------------
st.set_page_config(page_title="TUT0res 4.0", layout="wide")

@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("Error en credenciales.")
        return None

supabase = init_connection()
dias_semana = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles", "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}

def generar_horas(inicio, fin):
    horas = []
    try:
        fmt = "%H:%M:%S"
        t_in = datetime.datetime.strptime(str(inicio), fmt) if isinstance(inicio, str) else datetime.datetime.combine(datetime.date.today(), inicio)
        t_out = datetime.datetime.strptime(str(fin), fmt) if isinstance(fin, str) else datetime.datetime.combine(datetime.date.today(), fin)
        while t_in < t_out:
            horas.append(t_in.strftime("%H:%M"))
            t_in += datetime.timedelta(minutes=45)
    except: pass
    return horas

# ---------------------------
# SESIÓN Y MENÚ
# ---------------------------
if "usuario" not in st.session_state: st.session_state["usuario"] = None
if "rol" not in st.session_state: st.session_state["rol"] = None

st.sidebar.title("📌 TUT0res 4.0")

if st.session_state["usuario"]:
    st.sidebar.success(f"Conectado: {st.session_state['usuario']}")
    st.sidebar.info(f"Rol: {st.session_state['rol']}")
    ops = ["Inicio"]
    if st.session_state["rol"] == "Estudiante": ops += ["Reservar", "Ver Reservas"]
    elif st.session_state["rol"] == "Docente": ops += ["Ver Mis Tutorías"]
    elif st.session_state["rol"] == "Administrador": ops += ["Gestionar Usuarios", "Gestionar Reservas"]
    
    menu = st.sidebar.radio("Navegación", ops)
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()
else:
    menu = st.sidebar.radio("Acceso", ["Inicio", "Registro", "Login"])

# ---------------------------
# LÓGICA DE MÓDULOS
# ---------------------------
if menu == "Inicio":
    st.title("🚀 TUT0res - Universidad 4.0")
    st.write("Bienvenido al gestor de tutorías.")

elif menu == "Registro":
    st.subheader("📝 Registro")
    e, p, n = st.text_input("Email"), st.text_input("Password", type="password"), st.text_input("Nombre")
    r = st.selectbox("Rol", ["Estudiante", "Docente", "Administrador"])
    m, ds, hi, ho = "", [], "08:00:00", "12:00:00"
    if r == "Docente":
        m = st.text_input("Materias")
        ds = st.multiselect("Días", list(dias_semana.values()))
        hi, ho = str(st.time_input("Inicio")), str(st.time_input("Fin"))
    if st.button("Registrar"):
        try:
            u = supabase.auth.sign_up({"email": e, "password": p})
            if u.user:
                supabase.table("perfiles").insert({"id": u.user.id, "nombre": n, "rol": r, "materias": m, "hora_inicio": hi, "hora_fin": ho, "dias_tutorias": ",".join(ds)}).execute()
                st.success("Registrado.")
        except: st.error("Error.")

elif menu == "Login":
    st.subheader("🔑 Login")
    e, p = st.text_input("Email"), st.text_input("Password", type="password")
    if st.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": e, "password": p})
            per = supabase.table("perfiles").select("*").eq("id", res.user.id).execute()
            if per.data:
                st.session_state["usuario"], st.session_state["rol"] = per.data[0]["nombre"], per.data[0]["rol"]
                st.rerun()
        except: st.error("Error de login.")

elif menu == "Reservar" and st.session_state["rol"] == "Estudiante":
    st.subheader("📅 Reservar")
    docs = supabase.table("perfiles").select("*").eq("rol", "Docente").execute().data
    if docs:
        doc_nom = st.selectbox("Docente", [d["nombre"] for d in docs])
        d_sel = next(d for d in docs if d["nombre"] == doc_nom)
        d_dis = d_sel.get("dias_tutorias", "").split(",")
        evs = []
        hoy = datetime.date.today()
        for i in range(30):
            f = hoy + datetime.timedelta(days=i)
            if dias_semana[f.strftime("%A")] in d_dis:
                evs.append({"title": "Disponible", "start": str(f), "color": "#2ECC71"})
        calendar(events=evs, options={"initialView": "dayGridMonth"})
        
        mats = d_sel["materias"].split(",") if d_sel["materias"] else ["General"]
        mat_sel, f_sel = st.selectbox("Materia", mats), st.date_input("Fecha", min_value=hoy)
        if dias_semana[f_sel.strftime("%A")] in d_dis:
            hrs = generar_horas(d_sel["hora_inicio"], d_sel["hora_fin"])
            ocup = [r["hora"][:5] for r in supabase.table("reservas").select("hora").eq("docente", doc_nom).eq("fecha", str(f_sel)).execute().data]
            libres = [h for h in hrs if h not in ocup]
            if libres:
                h_sel = st.selectbox("Hora", libres)
                if st.button("Confirmar"):
                    supabase.table("reservas").insert({"estudiante": st.session_state["usuario"], "docente": doc_nom, "materia": mat_sel, "fecha": str(f_sel), "hora": h_sel}).execute()
                    st.success("¡Listo!")
                    st.balloons()
            else: st.warning("Sin cupos.")
        else: st.error("Día no disponible.")

# --- MÓDULO MEJORADO PARA DOCENTES Y ESTUDIANTES ---
elif menu in ["Ver Reservas", "Ver Mis Tutorías", "Gestionar Reservas"]:
    st.subheader("📅 Calendario de Agenda")
    res = supabase.table("reservas").select("*").execute().data
    if res:
        df = pd.DataFrame(res)
        if st.session_state["rol"] == "Estudiante": 
            df = df[df["estudiante"] == st.session_state["usuario"]]
        elif st.session_state["rol"] == "Docente": 
            df = df[df["docente"] == st.session_state["usuario"]]
        
        # Crear eventos para el calendario
        evs_agenda = []
        for _, r in df.iterrows():
            lbl = f"{r['hora']} - {r['materia']} ({r['estudiante'] if st.session_state['rol'] == 'Docente' else r['docente']})"
            evs_agenda.append({"title": lbl, "start": r["fecha"], "color": "#3498DB"})
        
        calendar(events=evs_agenda, options={"initialView": "dayGridMonth", "height": 500})
        
        st.divider()
        st.subheader("🔍 Detalle y Cancelación")
        
        # Filtro para que el docente elija qué tutoría cancelar de forma más fácil
        res_list = [f"#{r['id']} | {r['fecha']} | {r['hora']} | {r['estudiante'] if st.session_state['rol'] == 'Docente' else r['docente']}" for _, r in df.iterrows()]
        sel_cancel = st.selectbox("Selecciona una tutoría para gestionar", ["---"] + res_list)
        
        if sel_cancel != "---":
            id_cancel = sel_cancel.split("|")[0].replace("#", "").strip()
            if st.button("❌ Cancelar esta tutoría"):
                supabase.table("reservas").delete().eq("id", id_cancel).execute()
                st.success(f"Tutoría {id_cancel} eliminada.")
                st.rerun()
        
        with st.expander("Ver tabla completa"):
            st.write(df)
    else:
        st.info("No hay tutorías en la agenda.")

elif menu == "Gestionar Usuarios":
    st.subheader("👥 Usuarios")
    usr = supabase.table("perfiles").select("*").execute().data
    if usr:
        df_u = pd.DataFrame(usr)
        st.dataframe(df_u)
        for _, u in df_u.iterrows():
            if st.button(f"Eliminar {u['nombre']}", key=f"d_{u['id']}"):
                supabase.table("perfiles").delete().eq("id", u["id"]).execute()
                st.rerun()
