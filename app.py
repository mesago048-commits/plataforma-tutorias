import streamlit as st
from supabase import create_client
import datetime
import pandas as pd
from streamlit_calendar import calendar
import time

# ---------------------------
# 1. CONFIGURACIÓN Y CONEXIÓN
# ---------------------------
st.set_page_config(page_title="TUT0res 4.0 - Universidad 4.0", layout="wide")

# ---------------------------
# ESTILO VISUAL PROFESIONAL
# ---------------------------
st.markdown("""
<style>

.stApp{
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
color:white;
}

/* Sidebar */
section[data-testid="stSidebar"]{
background:#111827;
}

/* Títulos */
h1,h2,h3{
color:#00E5FF;
font-weight:700;
}

/* Botones */
.stButton>button{
background: linear-gradient(90deg,#00c6ff,#0072ff);
color:white;
border-radius:10px;
border:none;
padding:10px 20px;
font-weight:bold;
}

.stButton>button:hover{
background: linear-gradient(90deg,#0072ff,#00c6ff);
}

/* Inputs */
.stTextInput>div>div>input{
border-radius:10px;
}

.stSelectbox>div>div{
border-radius:10px;
}

/* Tarjetas */
.card{
background:rgba(255,255,255,0.05);
padding:25px;
border-radius:15px;
backdrop-filter: blur(10px);
box-shadow:0px 4px 20px rgba(0,0,0,0.3);
margin-bottom:20px;
}

/* tablas */
[data-testid="stDataFrame"]{
background:white;
border-radius:10px;
}

/* calendario */
.fc{
background:white;
border-radius:10px;
}

</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("⚠️ Error de conexión. Revisa los Secrets.")
        return None

supabase = init_connection()

dias_semana = {
"Monday":"Lunes",
"Tuesday":"Martes",
"Wednesday":"Miércoles",
"Thursday":"Jueves",
"Friday":"Viernes",
"Saturday":"Sábado",
"Sunday":"Domingo"
}

def generar_horas(inicio, fin):
    horas=[]
    try:
        fmt="%H:%M:%S"
        t_in=datetime.datetime.strptime(str(inicio),fmt) if isinstance(inicio,str) else datetime.datetime.combine(datetime.date.today(),inicio)
        t_out=datetime.datetime.strptime(str(fin),fmt) if isinstance(fin,str) else datetime.datetime.combine(datetime.date.today(),fin)
        while t_in<t_out:
            horas.append(t_in.strftime("%H:%M"))
            t_in+=datetime.timedelta(minutes=45)
    except:
        pass
    return horas

# ---------------------------
# 2. GESTIÓN DE SESIÓN
# ---------------------------
if "usuario" not in st.session_state: st.session_state["usuario"]=None
if "rol" not in st.session_state: st.session_state["rol"]=None
if "esperando_llave" not in st.session_state: st.session_state["esperando_llave"]=False
if "datos_temp" not in st.session_state: st.session_state["datos_temp"]=None

# ---------------------------
# 3. SIDEBAR
# ---------------------------
with st.sidebar:

    st.title("🎓 TUT0res 4.0")

    if st.session_state["usuario"]:

        st.success(f"Bienvenido {st.session_state['usuario']}")
        st.info(f"Perfil: {st.session_state['rol']}")

        if st.session_state["rol"]=="Estudiante":
            menu=st.radio("Panel Estudiante",["Inicio","Reservar Tutoría","Mis Reservas"])

        elif st.session_state["rol"]=="Docente":
            menu=st.radio("Panel Docente",["Inicio","Mi Agenda de Clases"])

        elif st.session_state["rol"]=="Administrador":
            menu=st.radio("Panel Admin",["Inicio","Control de Usuarios","Historial Global"])

        st.divider()

        if st.button("🚪 Cerrar sesión"):
            st.session_state.clear()
            st.rerun()

    else:
        menu=st.radio("Acceso Público",["Inicio","Crear Cuenta","Ingresar"])

# ---------------------------
# 4. MÓDULOS PÚBLICOS
# ---------------------------
if menu=="Inicio":

    st.markdown("""
    <div class="card">
    <h1>🚀 Bienvenidos a TUT0res 4.0</h1>
    <h3>Plataforma inteligente de tutorías universitarias</h3>
    <p>Agenda tutorías con docentes disponibles y gestiona tus horarios de forma rápida.</p>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3=st.columns(3)

    with c1:
        st.markdown("""
        <div class="card">
        <h3>📅 Reservas rápidas</h3>
        Agenda tutorías fácilmente con nuestros docentes.
        </div>
        """,unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="card">
        <h3>👨‍🏫 Profesores disponibles</h3>
        Consulta horarios disponibles en tiempo real.
        </div>
        """,unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="card">
        <h3>📊 Gestión inteligente</h3>
        Administra tutorías de forma moderna.
        </div>
        """,unsafe_allow_html=True)

# ---------------------------
# REGISTRO
# ---------------------------
elif menu=="Crear Cuenta":

    st.markdown('<div class="card">',unsafe_allow_html=True)

    st.subheader("📝 Formulario de Registro")

    c1,c2=st.columns(2)

    with c1:
        e_reg=st.text_input("Email",key="reg_email")
        p_reg=st.text_input("Contraseña",type="password",key="reg_pass")
        n_reg=st.text_input("Nombre completo")

    with c2:
        r_reg=st.selectbox("Rol:",["Estudiante","Docente","Administrador"])

        m,ds,hi,ho="","[]","08:00:00","12:00:00"

        if r_reg=="Docente":
            m=st.text_input("Materias (separadas por coma)")
            ds=st.multiselect("Días (Máximo 3)",list(dias_semana.values()),max_selections=3)
            hi=str(st.time_input("Hora Inicio"))
            ho=str(st.time_input("Hora Fin"))

    if st.button("Registrarme ahora"):
        try:
            u=supabase.auth.sign_up({"email":e_reg,"password":p_reg})

            if u.user:

                supabase.table("perfiles").insert({
                    "id":u.user.id,
                    "nombre":n_reg,
                    "rol":r_reg,
                    "materias":m,
                    "hora_inicio":hi,
                    "hora_fin":ho,
                    "dias_tutorias":",".join(ds)
                }).execute()

                st.success("✅ Cuenta creada con éxito")

        except:
            st.error("❌ Error en el registro")

    st.markdown('</div>',unsafe_allow_html=True)

# ---------------------------
# LOGIN
# ---------------------------
elif menu=="Ingresar":

    st.markdown('<div class="card">',unsafe_allow_html=True)

    st.subheader("🔑 Acceso Seguro al Sistema")

    LLAVE_DOCENTE="U40PROFE"
    LLAVE_ADMIN="U40ADMIN"

    placeholder=st.empty()

    if not st.session_state["esperando_llave"]:

        with st.form("login_form"):

            e_log=st.text_input("Email")
            p_log=st.text_input("Password",type="password")

            btn_login=st.form_submit_button("Validar Credenciales")

        if btn_login:

            success_trigger=False

            try:

                res=supabase.auth.sign_in_with_password({
                "email":e_log,
                "password":p_log
                })

                per=supabase.table("perfiles").select("*").eq("id",res.user.id).execute()

                if per.data:

                    u_data=per.data[0]

                    if u_data["rol"] in ["Docente","Administrador"]:

                        st.session_state["esperando_llave"]=True
                        st.session_state["datos_temp"]=u_data
                        success_trigger=True

                    else:

                        st.session_state["usuario"]=u_data["nombre"]
                        st.session_state["rol"]=u_data["rol"]

                        placeholder.success("✅ Acceso correcto")
                        success_trigger=True

            except:
                placeholder.error("❌ Correo o contraseña incorrectos")

            if success_trigger:
                time.sleep(0.5)
                st.rerun()

    else:

        st.warning(f"🛡️ Perfil de {st.session_state['datos_temp']['rol']} detectado")

        llave=st.text_input("Introduce la Llave Maestra",type="password")

        if st.button("Verificar Identidad Final"):

            llave_correcta=LLAVE_DOCENTE if st.session_state["datos_temp"]["rol"]=="Docente" else LLAVE_ADMIN

            if llave==llave_correcta:

                st.session_state["usuario"]=st.session_state["datos_temp"]["nombre"]
                st.session_state["rol"]=st.session_state["datos_temp"]["rol"]
                st.session_state["esperando_llave"]=False

                st.success("✅ Identidad confirmada")

                time.sleep(0.5)
                st.rerun()

            else:
                st.error("❌ Llave incorrecta")

    st.markdown('</div>',unsafe_allow_html=True)

# ---------------------------
# 5 PANEL ESTUDIANTE
# ---------------------------
elif menu=="Reservar Tutoría":

    st.title("📅 Agendar Nueva Tutoría")

    docs=supabase.table("perfiles").select("*").eq("rol","Docente").execute().data

    if docs:

        doc_nom=st.selectbox("Selecciona tu profesor:",[d["nombre"] for d in docs])

        d_sel=next(d for d in docs if d["nombre"]==doc_nom)

        d_dis=d_sel.get("dias_tutorias","").split(",")

        evs=[]
        hoy=datetime.date.today()

        for i in range(30):

            f=hoy+datetime.timedelta(days=i)

            if dias_semana[f.strftime("%A")] in d_dis:

                evs.append({
                "title":"Disponible",
                "start":str(f),
                "color":"#2ECC71"
                })

        calendar(events=evs,options={"initialView":"dayGridMonth"})

        st.divider()

        mats=d_sel["materias"].split(",") if d_sel["materias"] else ["General"]

        mat_sel=st.selectbox("Materia",mats)

        f_sel=st.date_input("Fecha",min_value=hoy)

        if dias_semana[f_sel.strftime("%A")] in d_dis:

            hrs=generar_horas(d_sel["hora_inicio"],d_sel["hora_fin"])

            res_db=supabase.table("reservas").select("hora").eq("docente",doc_nom).eq("fecha",str(f_sel)).execute().data

            ocup=[r["hora"][:5] for r in res_db] if res_db else []

            libres=[h for h in hrs if h not in ocup]

            if libres:

                h_sel=st.selectbox("Hora",libres)

                if st.button("Confirmar Cupo"):

                    supabase.table("reservas").insert({
                    "estudiante":st.session_state["usuario"],
                    "docente":doc_nom,
                    "materia":mat_sel,
                    "fecha":str(f_sel),
                    "hora":h_sel
                    }).execute()

                    st.success("🎉 ¡Tutoría reservada!")
                    st.balloons()

            else:
                st.warning("Sin cupos")

        else:
            st.error("Docente no disponible este día")

# ---------------------------
# MIS RESERVAS
# ---------------------------
elif menu=="Mis Reservas":

    st.title("📑 Mis Tutorías Programadas")

    res=supabase.table("reservas").select("*").eq("estudiante",st.session_state["usuario"]).execute().data

    if res:

        df=pd.DataFrame(res)

        st.dataframe(df[["id","docente","materia","fecha","hora"]],use_container_width=True)

        id_can=st.number_input("ID para cancelar",step=1)

        if st.button("❌ Cancelar"):

            supabase.table("reservas").delete().eq("id",id_can).execute()
            st.rerun()

    else:
        st.info("Sin reservas")

# ---------------------------
# PANEL DOCENTE
# ---------------------------
elif menu=="Mi Agenda de Clases":

    st.title("👨‍🏫 Mi Agenda de Tutorías")

    res=supabase.table("reservas").select("*").eq("docente",st.session_state["usuario"]).execute().data

    if res:

        df=pd.DataFrame(res)

        evs_doc=[{
        "title":f"{r['hora']} - {r['estudiante']} ({r['materia']})",
        "start":r["fecha"],
        "color":"#3498DB"
        } for _,r in df.iterrows()]

        calendar(events=evs_doc,options={"initialView":"dayGridMonth","height":500})

        st.table(df[["fecha","hora","estudiante","materia"]])

    else:
        st.info("No tienes alumnos agendados todavía")

# ---------------------------
# PANEL ADMIN
# ---------------------------
elif menu=="Control de Usuarios":

    st.title("🛠️ Consola Admin")

    usr=supabase.table("perfiles").select("*").execute().data

    if usr:

        df_u=pd.DataFrame(usr)

        st.dataframe(df_u)

        u_del=st.text_input("ID del usuario a eliminar")

        if st.button("🔥 Eliminar"):

            supabase.table("perfiles").delete().eq("id",u_del).execute()
            st.rerun()

elif menu=="Historial Global":

    st.title("📊 Seguimiento Global")

    all_res=supabase.table("reservas").select("*").execute().data

    if all_res:
        st.write(pd.DataFrame(all_res))