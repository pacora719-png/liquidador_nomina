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

# Inicializar lista de empleados
if "empleados" not in st.session_state:
    st.session_state.empleados = []

# Datos de la empresa
st.header("Datos de la empresa")
empresa = st.text_input("Nombre de la empresa")
nit = st.text_input("NIT o cédula del empleador")
logo = st.file_uploader("Logo de la empresa (opcional)", type=["png","jpg","jpeg"])

# Periodo y observaciones
st.header("Periodo de pago")
fecha_inicio = st.date_input("Fecha inicio", date.today())
fecha_fin = st.date_input("Fecha fin", date.today())
observaciones = st.text_area("Observaciones")

# Carga opcional desde Excel
st.header("Carga opcional de empleados desde Excel")
archivo_excel = st.file_uploader("Subir Excel", type=["xlsx"])

if archivo_excel:
    df = pd.read_excel(archivo_excel)
    st.dataframe(df)
    if st.button("Cargar empleados Excel"):
        for _,row in df.iterrows():
            st.session_state.empleados.append({
                "Empleado": row["nombre"],
                "Cédula": row["cedula"],
                "Días trabajados": row["dias"],
                "Salario": row["salario"],
                "Auxilio Transporte": 0,
                "Horas Extra Diurna": 0,
                "Horas Extra Nocturna": 0,
                "Horas Extra Dominical": 0,
                "Horas Extra Nocturna Dominical": 0,
                "Recargo Nocturno": 0,
                "Recargo Dominical": 0,
                "Bonificaciones": 0,
                "IBC": row["salario"],
                "Devengado": row["salario"],
                "Salud": row["salario"]*0.04,
                "Pensión": row["salario"]*0.04,
                "Consumos": 0,
                "Daños": 0,
                "Ahorros": 0,
                "Otros": 0,
                "Deducciones": row["salario"]*0.08,
                "Neto": row["salario"]*0.92,
                "Situacion Especial": None
            })
        st.success("Empleados cargados desde Excel")

# Agregar empleado manualmente
st.header("Agregar empleado manualmente")
with st.form("empleado"):
    nombre = st.text_input("Nombre empleado")
    cedula = st.text_input("Cédula")
    salario_mensual = st.number_input("Salario mensual",value=1750905)
    dias_trabajados = st.number_input("Días trabajados",0,30,30)

    # Selección única de situación especial
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

        recargo_nocturno = valor_hora*0.35*recargo_nocturno_h
        recargo_dominical = valor_hora*0.90*recargo_dominical_h

        # Auxilio transporte solo si salario base <= 2 SMMLV y no hay situación especial
        auxilio = 0
        if situacion == "Ninguna" and salario_mensual <= 3501810:
            auxilio = (249095/30) * dias_trabajados

        # IBC sin bonificaciones ni auxilio
        ibc = salario + extra_diurna + extra_nocturna + extra_dominical + extra_nocturna_dom + recargo_nocturno + recargo_dominical

        salud = ibc*0.04
        pension = ibc*0.04

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
            "Bonificaciones": bonificaciones,
            "IBC": ibc,
            "Devengado": devengado,
            "Salud": salud,
            "Pensión": pension,
            "Consumos": consumos,
            "Daños": danos,
            "Ahorros": ahorros,
            "Otros": otros,
            "Deducciones": deducciones,
            "Neto": neto,
            "Situacion Especial": situacion
        })
        st.success("Empleado agregado")

# Mostrar empleados
st.header("Lista de empleados")
for emp in st.session_state.empleados:
    st.write(emp["Empleado"], "Neto a pagar:", pesos(emp["Neto"]))

# Función generar PDF
def generar_pdf(emp):
    nombre_seguro = re.sub(r'[^a-zA-Z0-9]','_',emp["Empleado"])
    archivo = f"colilla_{nombre_seguro}.pdf"
    c = canvas.Canvas(archivo,pagesize=letter)
    y = 750

    # Logo
    if logo is not None:
        image = Image.open(logo)
        image.save("logo_temp.png")
        c.drawImage("logo_temp.png",50,720,width=120,height=60)

    c.setFont("Helvetica-Bold",14)
    c.drawString(220,y,"COLILLA DE PAGO")
    y -= 40

    c.setFont("Helvetica",10)
    c.drawString(50,y,f"Empresa: {empresa}")
    y -= 15
    c.drawString(50,y,f"NIT: {nit}")
    y -= 15
    c.drawString(50,y,f"Empleado: {emp['Empleado']}")
    y -= 15
    c.drawString(50,y,f"Cédula: {emp['Cédula']}")
    y -= 15
    c.drawString(50,y,f"Días trabajados: {emp['Días trabajados']}")
    y -= 15
    c.drawString(50,y,f"Periodo: {fecha_inicio} a {fecha_fin}")
    y -= 15

    # Nota de situación especial
    if emp["Situacion Especial"] != "Ninguna":
        c.setFont("Helvetica-Bold",10)
        c.setFillColorRGB(0,0.5,0)  # letra verde
        c.drawString(50,y,f"Situación especial: {emp['Situacion Especial']}")
        c.setFillColorRGB(0,0,0)
        y -= 20

    # Devengados
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
    y -= 25

    # Resumen horas
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"RESUMEN HORAS Y RECARGOS")
    y -= 20
    c.setFont("Helvetica",10)
    c.drawString(50,y,"Horas Extra Diurna")
    c.drawRightString(550,y,pesos(emp["Horas Extra Diurna"]))
    y -= 15
    c.drawString(50,y,"Horas Extra Nocturna")
    c.drawRightString(550,y,pesos(emp["Horas Extra Nocturna"]))
    y -= 15
    c.drawString(50,y,"Horas Extra Dominical")
    c.drawRightString(550,y,pesos(emp["Horas Extra Dominical"]))
    y -= 15
    c.drawString(50,y,"Extra Nocturna Dominical")
    c.drawRightString(550,y,pesos(emp["Horas Extra Nocturna Dominical"]))
    y -= 15
    c.drawString(50,y,"Recargo Nocturno")
    c.drawRightString(550,y,pesos(emp["Recargo Nocturno"]))
    y -= 15
    c.drawString(50,y,"Recargo Dominical")
    c.drawRightString(550,y,pesos(emp["Recargo Dominical"]))
    y -= 30

    # Deducciones
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"DEDUCCIONES")
    y -= 20
    c.setFont("Helvetica",10)
    c.drawString(50,y,"Salud")
    c.drawRightString(550,y,pesos(emp["Salud"]))
    y -= 15
    c.drawString(50,y,"Pensión")
    c.drawRightString(550,y,pesos(emp["Pensión"]))
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
    y -= 30

    # Totales
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"TOTAL DEVENGADO")
    c.drawRightString(550,y,pesos(emp["Devengado"]))
    y -= 20
    c.drawString(50,y,"TOTAL DEDUCCIONES")
    c.drawRightString(550,y,pesos(emp["Deducciones"]))
    y -= 20
    c.drawString(50,y,"NETO A PAGAR")
    c.drawRightString(550,y,pesos(emp["Neto"]))
    y -= 60

    # Firma
    c.line(300,y,550,y)
    c.drawString(300,y-15,emp["Empleado"])
    c.drawString(300,y-30,"Firma empleado")

    c.save()
    return archivo

# Botón PDF
st.header("Generar PDF de colilla de pago")
for i, emp in enumerate(st.session_state.empleados):
    if st.button(f"Generar PDF - {emp['Empleado']}", key=i):
        archivo = generar_pdf(emp)
        with open(archivo, "rb") as f:
            st.download_button(
                label="Descargar PDF",
                data=f,
                file_name=archivo,
                mime="application/pdf"
            )
