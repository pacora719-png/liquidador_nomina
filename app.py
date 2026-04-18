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

# Datos empresa
st.header("Datos de la empresa")
empresa = st.text_input("Nombre de la empresa")
nit = st.text_input("NIT o cédula del empleador")
logo = st.file_uploader("Logo de la empresa (opcional)", type=["png","jpg","jpeg"])

# Periodo
st.header("Periodo de pago")
fecha_inicio = st.date_input("Fecha inicio", date.today())
fecha_fin = st.date_input("Fecha fin", date.today())
observaciones = st.text_area("Observaciones")

# Agregar empleado
st.header("Agregar empleado manualmente")
with st.form("empleado"):
    nombre = st.text_input("Nombre empleado")
    cedula = st.text_input("Cédula")
    salario_mensual = st.number_input("Salario mensual",value=1750905)
    dias_trabajados = st.number_input("Días trabajados",0,30,30)

    no_pension = st.checkbox("No descontar pensión (persona pensionada)")

    situacion = st.radio(
        "Seleccione situación especial", 
        options=["Ninguna","Incapacidad","Vacaciones","Licencia","Teletrabajo","Empresa lo transporta"]
    )

    st.subheader("Horas extras")
    extra_diurna_h = st.number_input("Horas extra diurna",0)
    extra_nocturna_h = st.number_input("Horas extra nocturna",0)
    extra_dominical_h = st.number_input("Extra dominical/festivo",0)
    extra_nocturna_dom_h = st.number_input("Extra nocturna dominical",0)

    st.subheader("Recargos")
    recargo_nocturno_h = st.number_input("Recargo nocturno",0)
    recargo_dominical_h = st.number_input("Recargo dominical",0)

    bonificaciones = st.number_input("Bonificaciones",0)

    st.subheader("Deducciones")
    consumos = st.number_input("Consumos",0)
    danos = st.number_input("Daños",0)
    ahorros = st.number_input("Ahorros",0)
    otros = st.number_input("Otros",0)

    agregar = st.form_submit_button("Agregar empleado")

    if agregar:
        salario = (salario_mensual/30)*dias_trabajados
        valor_hora = salario_mensual/220

        # Horas extras
        extra_diurna = valor_hora*1.25*extra_diurna_h
        extra_nocturna = valor_hora*1.75*extra_nocturna_h
        extra_dominical = valor_hora*2.15*extra_dominical_h
        extra_nocturna_dom = valor_hora*2.65*extra_nocturna_dom_h

        # Recargos
        recargo_nocturno = valor_hora*0.35*recargo_nocturno_h
        recargo_dominical = valor_hora*0.90*recargo_dominical_h

        # Auxilio
        auxilio = 0
        if situacion == "Ninguna" and salario_mensual <= 3501810:
            auxilio = (249095/30) * dias_trabajados

        # IBC
        ibc = salario + extra_diurna + extra_nocturna + extra_dominical + extra_nocturna_dom + recargo_nocturno + recargo_dominical

        salud = ibc*0.04
        pension = 0 if no_pension else ibc*0.04

        devengado = ibc + auxilio + bonificaciones
        deducciones = salud + pension + consumos + danos + ahorros + otros
        neto = devengado - deducciones

        st.session_state.empleados.append({
            "Empleado": nombre,
            "Cédula": cedula,
            "Días trabajados": dias_trabajados,
            "Salario": salario,
            "Auxilio Transporte": auxilio,
            "Horas Extra Diurna": extra_diurna,
            "Horas Extra Nocturna": extra_nocturna,
            "Horas Extra Dominical": extra_dominical,
            "Horas Extra Nocturna Dominical": extra_nocturna_dom,
            "Recargo Nocturno": recargo_nocturno,
            "Recargo Dominical": recargo_dominical,
            "Horas Diurna H": extra_diurna_h,
            "Horas Nocturna H": extra_nocturna_h,
            "Horas Dominical H": extra_dominical_h,
            "Horas Nocturna Dom H": extra_nocturna_dom_h,
            "Recargo Nocturno H": recargo_nocturno_h,
            "Recargo Dominical H": recargo_dominical_h,
            "Bonificaciones": bonificaciones,
            "IBC": ibc,
            "Devengado": devengado,
            "Salud": salud,
            "Pensión": pension,
            "No Pension": no_pension,
            "Consumos": consumos,
            "Daños": danos,
            "Ahorros": ahorros,
            "Otros": otros,
            "Deducciones": deducciones,
            "Neto": neto,
            "Situacion Especial": situacion
        })
        st.success("Empleado agregado")

# Lista
st.header("Lista de empleados")
for emp in st.session_state.empleados:
    st.write(emp["Empleado"], "Neto a pagar:", pesos(emp["Neto"]))

# PDF
def generar_pdf(emp):
    nombre_seguro = re.sub(r'[^a-zA-Z0-9]','_',emp["Empleado"])
    archivo = f"colilla_{nombre_seguro}.pdf"
    c = canvas.Canvas(archivo,pagesize=letter)
    y = 750

    if logo:
        image = Image.open(logo)
        image.save("logo_temp.png")
        c.drawImage("logo_temp.png",50,720,width=120,height=60)

    c.setFont("Helvetica-Bold",14)
    c.drawString(220,y,"COLILLA DE PAGO")
    y -= 40

    c.setFont("Helvetica",10)
    c.drawString(50,y,f"Empresa: {empresa}")
    y -= 15
    c.drawString(50,y,f"Empleado: {emp['Empleado']}")
    y -= 15
    c.drawString(50,y,f"Cédula: {emp['Cédula']}")
    y -= 20

    if emp["No Pension"]:
        c.setFont("Helvetica-Bold",10)
        c.setFillColorRGB(0,0.5,0)
        c.drawString(50,y,"No aplica descuento de pensión")
        c.setFillColorRGB(0,0,0)
        y -= 20

    # DEVENGADOS
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"DEVENGADOS")
    y -= 20
    c.setFont("Helvetica",10)

    c.drawString(50,y,"Salario")
    c.drawRightString(550,y,pesos(emp["Salario"]))
    y -= 15

    c.drawString(50,y,"Auxilio Transporte")
    c.drawRightString(550,y,pesos(emp["Auxilio Transporte"]))
    y -= 15

    c.drawString(50,y,"Bonificaciones")
    c.drawRightString(550,y,pesos(emp["Bonificaciones"]))
    y -= 20

    # HORAS EXTRAS
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"HORAS EXTRAS")
    y -= 20
    c.setFont("Helvetica",10)

    c.drawString(50,y,f"Horas Extra Diurna ({emp['Horas Diurna H']} h)")
    c.drawRightString(550,y,pesos(emp["Horas Extra Diurna"]))
    y -= 15

    c.drawString(50,y,f"Horas Extra Nocturna ({emp['Horas Nocturna H']} h)")
    c.drawRightString(550,y,pesos(emp["Horas Extra Nocturna"]))
    y -= 15

    c.drawString(50,y,f"Horas Extra Dominical ({emp['Horas Dominical H']} h)")
    c.drawRightString(550,y,pesos(emp["Horas Extra Dominical"]))
    y -= 15

    c.drawString(50,y,f"Extra Nocturna Dominical ({emp['Horas Nocturna Dom H']} h)")
    c.drawRightString(550,y,pesos(emp["Horas Extra Nocturna Dominical"]))
    y -= 20

    # RECARGOS
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"RECARGOS")
    y -= 20
    c.setFont("Helvetica",10)

    c.drawString(50,y,f"Recargo Nocturno ({emp['Recargo Nocturno H']} h)")
    c.drawRightString(550,y,pesos(emp["Recargo Nocturno"]))
    y -= 15

    c.drawString(50,y,f"Recargo Dominical ({emp['Recargo Dominical H']} h)")
    c.drawRightString(550,y,pesos(emp["Recargo Dominical"]))
    y -= 20

    # DEDUCCIONES
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"DEDUCCIONES")
    y -= 20
    c.setFont("Helvetica",10)

    c.drawString(50,y,"Salud")
    c.drawRightString(550,y,pesos(emp["Salud"]))
    y -= 15

    c.drawString(50,y,"Pensión")
    c.drawRightString(550,y,pesos(emp["Pensión"]))
    y -= 20

    # NETO
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"NETO A PAGAR")
    c.drawRightString(550,y,pesos(emp["Neto"]))

    c.save()
    return archivo

# Botón PDF
st.header("Generar PDF de colilla de pago")
for i, emp in enumerate(st.session_state.empleados):
    if st.button(f"Generar PDF - {emp['Empleado']}", key=i):
        archivo = generar_pdf(emp)
        with open(archivo, "rb") as f:
            st.download_button("Descargar PDF", f, archivo)
