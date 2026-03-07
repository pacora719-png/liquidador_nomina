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

st.header("Datos de la empresa")

empresa = st.text_input("Nombre de la empresa")
nit = st.text_input("NIT o cédula del empleador")

logo = st.file_uploader("Logo de la empresa (opcional)", type=["png","jpg","jpeg"])

st.header("Periodo de pago")

fecha_inicio = st.date_input("Fecha inicio", date.today())
fecha_fin = st.date_input("Fecha fin", date.today())

observaciones = st.text_area("Observaciones")

st.header("Carga opcional de empleados desde Excel")

archivo_excel = st.file_uploader("Subir Excel", type=["xlsx"])

if archivo_excel:

    df = pd.read_excel(archivo_excel)

    st.dataframe(df)

    if st.button("Cargar empleados Excel"):

        for _,row in df.iterrows():

            empleado_data = {

                "Empleado":row["nombre"],
                "Cédula":row["cedula"],
                "Días trabajados":row["dias"],
                "Salario":row["salario"],
                "Auxilio Transporte":0,
                "Horas Extra Diurna":0,
                "Horas Extra Nocturna":0,
                "Horas Extra Dominical":0,
                "Horas Extra Nocturna Dominical":0,
                "Recargo Nocturno":0,
                "Recargo Dominical":0,
                "Bonificaciones":0,
                "IBC":row["salario"],
                "Devengado":row["salario"],
                "Salud":row["salario"]*0.04,
                "Pensión":row["salario"]*0.04,
                "Consumos":0,
                "Daños":0,
                "Ahorros":0,
                "Otros":0,
                "Deducciones":row["salario"]*0.08,
                "Neto":row["salario"]*0.92
            }

            st.session_state.empleados.append(empleado_data)

        st.success("Empleados cargados")

st.header("Agregar empleado manualmente")

with st.form("empleado"):

    nombre = st.text_input("Nombre empleado")
    cedula = st.text_input("Cédula")

    salario_mensual = st.number_input("Salario mensual",value=1750905)

    dias_trabajados = st.number_input("Días trabajados",0,30,30)

    pago_incapacidad = st.checkbox("Pago incapacidad")

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

        extra_diurna = valor_hora*1.25*extra_diurna_h
        extra_nocturna = valor_hora*1.75*extra_nocturna_h
        extra_dominical = valor_hora*2.15*extra_dominical_h
        extra_nocturna_dom = valor_hora*2.65*extra_nocturna_dom_h

        recargo_nocturno = valor_hora*0.35*recargo_nocturno_h
        recargo_dominical = valor_hora*0.90*recargo_dominical_h

        if pago_incapacidad:
            auxilio = 0
        else:
            auxilio = (249095/30)*dias_trabajados if salario_mensual<=3501810 else 0

        ibc = salario+extra_diurna+extra_nocturna+extra_dominical+extra_nocturna_dom+recargo_nocturno+recargo_dominical+bonificaciones

        salud = ibc*0.04
        pension = ibc*0.04

        devengado = ibc+auxilio

        deducciones = salud+pension+consumos+danos+ahorros+otros

        neto = devengado-deducciones

        empleado_data = {

            "Empleado":nombre,
            "Cédula":cedula,
            "Días trabajados":dias_trabajados,
            "Salario":salario,
            "Auxilio Transporte":auxilio,
            "Horas Extra Diurna":extra_diurna,
            "Horas Extra Nocturna":extra_nocturna,
            "Horas Extra Dominical":extra_dominical,
            "Horas Extra Nocturna Dominical":extra_nocturna_dom,
            "Recargo Nocturno":recargo_nocturno,
            "Recargo Dominical":recargo_dominical,
            "Bonificaciones":bonificaciones,
            "IBC":ibc,
            "Devengado":devengado,
            "Salud":salud,
            "Pensión":pension,
            "Consumos":consumos,
            "Daños":danos,
            "Ahorros":ahorros,
            "Otros":otros,
            "Deducciones":deducciones,
            "Neto":neto
        }

        st.session_state.empleados.append(empleado_data)

        st.success("Empleado agregado")

st.header("Lista empleados")

for emp in st.session_state.empleados:

    st.write(emp["Empleado"],"Neto:",pesos(emp["Neto"]))

def generar_pdf(emp):

    nombre_seguro=re.sub(r'[^a-zA-Z0-9]','_',emp["Empleado"])

    archivo=f"colilla_{nombre_seguro}.pdf"

    c=canvas.Canvas(archivo,pagesize=letter)

    y=750

    if logo is not None:

        image = Image.open(logo)

        image.save("logo_temp.png")

        c.drawImage("logo_temp.png",50,720,width=120,height=60)

    c.drawString(220,y,"COLILLA DE PAGO")

    y-=50

    c.drawString(50,y,f"Empresa: {empresa}")
    y-=20
    c.drawString(50,y,f"NIT: {nit}")

    y-=30

    c.drawString(50,y,f"Empleado: {emp['Empleado']}")
    y-=20
    c.drawString(50,y,f"Cédula: {emp['Cédula']}")
    y-=20
    c.drawString(50,y,f"Días trabajados: {emp['Días trabajados']}")
    y-=20
    c.drawString(50,y,f"Periodo: {fecha_inicio} a {fecha_fin}")

    y-=40

    c.drawString(50,y,"Total Devengado")
    c.drawRightString(550,y,pesos(emp["Devengado"]))

    y-=20

    c.drawString(50,y,"Total Deducciones")
    c.drawRightString(550,y,pesos(emp["Deducciones"]))

    y-=20

    c.drawString(50,y,"Neto a Pagar")
    c.drawRightString(550,y,pesos(emp["Neto"]))

    y-=60

    c.line(300,y,550,y)
    c.drawString(300,y-20,emp["Empleado"])
    c.drawString(300,y-35,"Firma empleado")

    c.save()

    return archivo

st.header("Generar PDF")

for i,emp in enumerate(st.session_state.empleados):

    if st.button(f"PDF {emp['Empleado']}",key=i):

        archivo=generar_pdf(emp)

        with open(archivo,"rb") as f:

            st.download_button("Descargar PDF",f,file_name=archivo)
