import streamlit as st

st.title("TUTores - Salvemos la Universidad 4.0")

menu = st.sidebar.selectbox("Menú", ["Inicio", "Registro", "Reservar"])

if menu == "Inicio":
    st.write("Bienvenido al sistema de tutorías")

elif menu == "Registro":
    nombre = st.text_input("Nombre")
    rol = st.selectbox("Rol", ["Estudiante", "Docente"])
    if st.button("Registrar"):
        st.success(f"{nombre} registrado como {rol}")

elif menu == "Reservar":
    tutor = st.text_input("Nombre del docente")
    fecha = st.date_input("Selecciona fecha")
    if st.button("Reservar"):
        st.success("Tutoría reservada correctamente")