import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import date
from PIL import Image
import re

st.title("LIQUIDADOR DE NÓMINA")
st.markdown("### by Juan Pablo Villegas")

def pesos(valor):
    return "${:,.0f}".format(valor).replace(",", ".")

if "empleados" not in st.session_state:
    st.session_state.empleados = []

# EMPRESA
st.header("Datos de la empresa")
empresa = st.text_input("Nombre de la empresa")
nit = st.text_input("NIT")
representante = st.text_input("Representante legal")
logo = st.file_uploader("Logo", type=["png","jpg","jpeg"])

# PERIODO
st.header("Periodo")
fecha_inicio = st.date_input("Inicio", date.today())
fecha_fin = st.date_input("Fin", date.today())

# EMPLEADO
st.header("Empleado")
with st.form("form"):
    nombre = st.text_input("Nombre")
    cedula = st.text_input("Cédula")
    salario_mensual = st.number_input("Salario", value=1750905)
    dias = st.number_input("Días trabajados",0,30,30)

    col1, col2 = st.columns(2)
    with col1:
        no_pension = st.checkbox("No descontar pensión")
    with col2:
        no_salud = st.checkbox("No descontar salud")

    st.subheader("Situaciones especiales")
    incapacidad = st.checkbox("Incapacidad")
    maternidad = st.checkbox("Licencia maternidad")
    sin_auxilio = st.checkbox("No incluye auxilio transporte")

    st.subheader("Horas extras")
    h_ed = st.number_input("Extra diurna",0.0,step=0.1)
    h_en = st.number_input("Extra nocturna",0.0,step=0.1)
    h_ef = st.number_input("Extra dominical",0.0,step=0.1)
    h_end = st.number_input("Extra nocturna dominical",0.0,step=0.1)

    st.subheader("Recargos")
    h_rn = st.number_input("Recargo nocturno",0.0,step=0.1)
    h_rd = st.number_input("Recargo dominical",0.0,step=0.1)

    bonificaciones = st.number_input("Bonificaciones",0)

    st.subheader("Deducciones")
    consumos = st.number_input("Consumos",0)
    danos = st.number_input("Daños",0)
    ahorros = st.number_input("Ahorros",0)
    otros = st.number_input("Otros",0)

    btn = st.form_submit_button("Agregar")

    if btn:
        valor_hora = salario_mensual / 220
        salario = (salario_mensual/30)*dias

        ed = valor_hora*1.25*h_ed
        en = valor_hora*1.75*h_en
        ef = valor_hora*2.15*h_ef
        end = valor_hora*2.65*h_end

        rn = valor_hora*0.35*h_rn
        rd = valor_hora*0.90*h_rd

        ibc = salario + ed + en + ef + end + rn + rd

        salud = 0 if no_salud else ibc*0.04
        pension = 0 if no_pension else ibc*0.04

        auxilio = 0
        if salario_mensual <= 3501810 and not (incapacidad or maternidad or sin_auxilio):
            auxilio = (249095/30)*dias

        devengado = ibc + auxilio + bonificaciones
        deducciones = salud + pension + consumos + danos + ahorros + otros
        neto = devengado - deducciones

        st.session_state.empleados.append({
            "Empleado": nombre,
            "Cedula": cedula,
            "Salario": salario,
            "Auxilio": auxilio,
            "Bonificaciones": bonificaciones,

            "h_ed": h_ed, "ed": ed,
            "h_en": h_en, "en": en,
            "h_ef": h_ef, "ef": ef,
            "h_end": h_end, "end": end,

            "h_rn": h_rn, "rn": rn,
            "h_rd": h_rd, "rd": rd,

            "Salud": salud,
            "Pension": pension,

            "Consumos": consumos,
            "Daños": danos,
            "Ahorros": ahorros,
            "Otros": otros,

            "Devengado": devengado,
            "Deducciones": deducciones,
            "Neto": neto,

            "Incapacidad": incapacidad,
            "Maternidad": maternidad,
            "SinAuxilio": sin_auxilio
        })

        st.success("Empleado agregado")

# PDF
def generar_pdf(emp):
    archivo = f"{emp['Empleado']}.pdf"
    c = canvas.Canvas(archivo, pagesize=letter)

    y = 780

    # LOGO BIEN POSICIONADO
    if logo:
        with open("logo.png","wb") as f:
            f.write(logo.getbuffer())
        c.drawImage("logo.png", 50, 720, width=100, height=50)

    # TITULO
    c.setFont("Helvetica-Bold",14)
    c.drawString(200,750,"COLILLA DE PAGO")

    y = 700
    c.setFont("Helvetica",10)
    c.drawString(50,y,f"Empresa: {empresa}")
    y -= 15
    c.drawString(50,y,f"NIT: {nit}")
    y -= 15
    c.drawString(50,y,f"Empleado: {emp['Empleado']}")
    y -= 15
    c.drawString(50,y,f"Cédula: {emp['Cedula']}")
    y -= 20

    # DEVENGADOS
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"DEVENGADOS")
    y -= 15
    c.setFont("Helvetica",10)

    c.drawString(50,y,"Salario")
    c.drawRightString(550,y,pesos(emp["Salario"]))
    y -= 15

    c.drawString(50,y,"Auxilio")
    c.drawRightString(550,y,pesos(emp["Auxilio"]))
    y -= 15

    c.drawString(50,y,"Bonificaciones")
    c.drawRightString(550,y,pesos(emp["Bonificaciones"]))
    y -= 20

    # HORAS
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"HORAS EXTRAS Y RECARGOS")
    y -= 15
    c.setFont("Helvetica",10)

    c.drawString(50,y,f"Extra diurna ({emp['h_ed']}h)")
    c.drawRightString(550,y,pesos(emp["ed"]))
    y -= 15

    c.drawString(50,y,f"Extra nocturna ({emp['h_en']}h)")
    c.drawRightString(550,y,pesos(emp["en"]))
    y -= 15

    c.drawString(50,y,f"Dominical ({emp['h_ef']}h)")
    c.drawRightString(550,y,pesos(emp["ef"]))
    y -= 15

    c.drawString(50,y,f"Nocturna dominical ({emp['h_end']}h)")
    c.drawRightString(550,y,pesos(emp["end"]))
    y -= 15

    c.drawString(50,y,f"Recargo nocturno ({emp['h_rn']}h)")
    c.drawRightString(550,y,pesos(emp["rn"]))
    y -= 15

    c.drawString(50,y,f"Recargo dominical ({emp['h_rd']}h)")
    c.drawRightString(550,y,pesos(emp["rd"]))
    y -= 20

    # DEDUCCIONES
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"DEDUCCIONES")
    y -= 15
    c.setFont("Helvetica",10)

    c.drawString(50,y,"Salud")
    c.drawRightString(550,y,pesos(emp["Salud"]))
    y -= 15

    c.drawString(50,y,"Pensión")
    c.drawRightString(550,y,pesos(emp["Pension"]))
    y -= 15

    c.drawString(50,y,"Consumos")
    c.drawRightString(550,y,pesos(emp["Consumos"]))
    y -= 15

    c.drawString(50,y,"Daños")
    c.drawRightString(550,y,pesos(emp["Daños"]))
    y -= 15

    c.drawString(50,y,"Ahorros")
    c.drawRightString(550,y,pesos(emp["Ahorros"]))
    y -= 15

    c.drawString(50,y,"Otros")
    c.drawRightString(550,y,pesos(emp["Otros"]))
    y -= 20

    # TOTALES
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"TOTAL DEVENGADO")
    c.drawRightString(550,y,pesos(emp["Devengado"]))
    y -= 15

    c.drawString(50,y,"TOTAL DEDUCCIONES")
    c.drawRightString(550,y,pesos(emp["Deducciones"]))
    y -= 15

    c.drawString(50,y,"NETO A PAGAR")
    c.drawRightString(550,y,pesos(emp["Neto"]))
    y -= 40

    # FIRMAS
    c.line(50,y,250,y)
    c.drawString(50,y-15,emp["Empleado"])

    c.line(300,y,550,y)
    c.drawString(300,y-15,representante)

    c.save()
    return archivo

# BOTONES PDF
st.header("Generar PDF")
for i, emp in enumerate(st.session_state.empleados):
    if st.button(f"PDF - {emp['Empleado']}", key=i):
        archivo = generar_pdf(emp)
        with open(archivo,"rb") as f:
            st.download_button("Descargar",f,archivo)
