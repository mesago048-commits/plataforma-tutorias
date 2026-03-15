import streamlit as st
from supabase import create_client
import datetime
import pandas as pd
from streamlit_calendar import calendar

# ---------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------
st.set_page_config(page_title="Tutores - Universidad 4.0", layout="wide")

# ---------------------------
# CONEXIÓN SUPABASE (OPTIMIZADA)
# ---------------------------
@st.cache_resource
def init_connection():
    # En Streamlit Cloud, usa st.secrets. 
    # En local, asegúrate de tener el archivo .streamlit/secrets.toml
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Error de configuración de credenciales. Revisa los Secrets.")
        return None

supabase = init_connection()

# ---------------------------
# FUNCIONES DE APOYO
# ---------------------------
dias_semana = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
}

def generar_horas(inicio, fin):
    horas = []
    try:
        # Manejo de strings o objetos time
        fmt = "%H:%M:%S"
        t_inicio = datetime.datetime.strptime(str(inicio), fmt) if isinstance(inicio, str) else datetime.datetime.combine(datetime.date.today(), inicio)
        t_fin = datetime.datetime.strptime(str(fin), fmt) if isinstance(fin, str) else datetime.datetime.combine(datetime.date.today(), fin)
        
        while t_inicio < t_fin:
            horas.append(t_inicio.strftime("%H:%M"))
            t_inicio += datetime.timedelta(minutes=45)
    except:
        pass
    return horas

def obtener_docentes():
    try:
        res = supabase.table("perfiles").select("*").eq("rol", "Docente").execute()
        return res.data
    except:
        return []

# ---------------------------
# GESTIÓN DE SESIÓN
# ---------------------------
if "usuario" not in st.session_state:
    st.session_state["usuario"] = None
if "rol" not in st.session_state:
    st.session_state["rol"] = None

# ---------------------------
# SIDEBAR / NAVEGACIÓN
# ---------------------------
st.sidebar.title("📌 TUT0res 4.0")

if st.session_state["usuario"]:
    st.sidebar.success(f"Conectado: {st.session_state['usuario']}")
    st.sidebar.info(f"Rol: {st.session_state['rol']}")
    
    opciones = ["Inicio"]
    if st.session_state["rol"] == "Estudiante":
        opciones += ["Reservar", "Ver Reservas"]
    elif st.session_state["rol"] == "Docente":
        opciones += ["Ver Mis Tutorías"]
    elif st.session_state["rol"] == "Administrador":
        opciones += ["Gestionar Usuarios", "Gestionar Reservas"]
    
    menu = st.sidebar.radio("Navegación", opciones)
    
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()
else:
    menu = st.sidebar.radio("Acceso", ["Inicio", "Registro", "Login"])

# ---------------------------
# LÓGICA DE MÓDULOS
# ---------------------------

if menu == "Inicio":
    st.title("🚀 TUT0res - Salvemos la Universidad 4.0")
    st.markdown("Bienvenido al sistema de gestión de tutorías académicas.")

elif menu == "Registro":
    st.subheader("Crear nueva cuenta")
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        nombre = st.text_input("Nombre completo")
    with col2:
        rol = st.selectbox("Rol", ["Estudiante", "Docente", "Administrador"])
        
        if rol == "Docente":
            materias = st.text_input("Materias (separadas por coma)")
            dias = st.multiselect("Días disponibles", list(dias_semana.values()))
            h_inicio = st.time_input("Hora Inicio", datetime.time(8, 0))
            h_fin = st.time_input("Hora Fin", datetime.time(12, 0))

    if st.button("Finalizar Registro"):
        try:
            auth_res = supabase.auth.sign_up({"email": email, "password": password})
            if auth_res.user:
                perfil_data = {
                    "id": auth_res.user.id,
                    "nombre": nombre,
                    "rol": rol,
                    "materias": materias if rol == "Docente" else "",
                    "hora_inicio": str(h_inicio) if rol == "Docente" else None,
                    "hora_fin": str(h_fin) if rol == "Docente" else None,
                    "dias_tutorias": ",".join(dias) if rol == "Docente" else ""
                }
                supabase.table("perfiles").insert(perfil_data).execute()
                st.success("✅ Registro exitoso. Ya puedes iniciar sesión.")
        except Exception as e:
            st.error(f"Error en el registro: {e}")

elif menu == "Login":
    st.subheader("Iniciar Sesión")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            perfil = supabase.table("perfiles").select("*").eq("id", res.user.id).execute()
            if perfil.data:
                st.session_state["usuario"] = perfil.data[0]["nombre"]
                st.session_state["rol"] = perfil.data[0]["rol"]
                st.success("Acceso concedido")
                st.rerun()
        except:
            st.error("Credenciales inválidas")

elif menu == "Reservar":
    st.subheader("📅 Agendar Tutoría")
    docentes = obtener_docentes()
    if docentes:
        nombres = [d["nombre"] for d in docentes]
        doc_sel_nombre = st.selectbox("Selecciona al docente", nombres)
        doc_data = next(d for d in docentes if d["nombre"] == doc_sel_nombre)
        
        materias = doc_data["materias"].split(",") if doc_data["materias"] else ["General"]
        materia_sel = st.selectbox("Materia", materias)
        
        fecha_sel = st.date_input("Fecha", min_value=datetime.date.today())
        dia_nombre = dias_semana[fecha_sel.strftime("%A")]
        
        disponibles = doc_data["dias_tutorias"].split(",") if doc_data["dias_tutorias"] else []
        
        if dia_nombre in disponibles:
            horas = generar_horas(doc_data["hora_inicio"], doc_data["hora_fin"])
            # Filtrar ocupadas
            res_busq = supabase.table("reservas").select("hora").eq("docente", doc_sel_nombre).eq("fecha", str(fecha_sel)).execute()
            ocupadas = [r["hora"][:5] for r in res_busq.data]
            libres = [h for h in horas if h not in ocupadas]
            
            if libres:
                hora_sel = st.selectbox("Horas disponibles", libres)
                if st.button("Confirmar Reserva"):
                    supabase.table("reservas").insert({
                        "estudiante": st.session_state["usuario"],
                        "docente": doc_sel_nombre,
                        "materia": materia_sel,
                        "fecha": str(fecha_sel),
                        "hora": hora_sel
                    }).execute()
                    st.success("¡Reserva guardada!")
            else:
                st.warning("No hay horas libres para este día.")
        else:
            st.error(f"El docente no atiende los días {dia_nombre}")

elif menu in ["Ver Reservas", "Ver Mis Tutorías", "Gestionar Reservas"]:
    st.subheader("📑 Listado de Tutorías")
    try:
        res = supabase.table("reservas").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            if st.session_state["rol"] == "Estudiante":
                df = df[df["estudiante"] == st.session_state["usuario"]]
            elif st.session_state["rol"] == "Docente":
                df = df[df["docente"] == st.session_state["usuario"]]
            
            st.dataframe(df, use_container_width=True)
            
            # Calendario visual
            cal_events = []
            for _, row in df.iterrows():
                cal_events.append({
                    "title": f"{row['materia']} - {row['estudiante']}",
                    "start": f"{row['fecha']}T{row['hora']}",
                    "end": f"{row['fecha']}T{row['hora']}",
                })
            calendar(events=cal_events)
        else:
            st.info("No hay datos para mostrar.")
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
