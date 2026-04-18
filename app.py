import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import date
import re

st.title("LIQUIDADOR DE NÓMINA")
st.markdown("### by Juan Pablo Villegas")

def pesos(valor):
    return "${:,.0f}".format(valor).replace(",", ".")

if "empleados" not in st.session_state:
    st.session_state.empleados = []

# Empresa
st.header("Datos de la empresa")
empresa = st.text_input("Nombre de la empresa")
nit = st.text_input("NIT o cédula del empleador")
logo = st.file_uploader("Logo de la empresa (opcional)", type=["png","jpg","jpeg"])

# Periodo
st.header("Periodo de pago")
fecha_inicio = st.date_input("Fecha inicio", date.today())
fecha_fin = st.date_input("Fecha fin", date.today())

# Formulario
st.header("Agregar empleado")
with st.form("empleado"):
    nombre = st.text_input("Nombre")
    cedula = st.text_input("Cédula")
    salario_mensual = st.number_input("Salario mensual", value=1750905)
    dias_trabajados = st.number_input("Días trabajados",0,30,30)

    no_pension = st.checkbox("No descontar pensión")

    st.subheader("Horas extras")
    h_ed = st.number_input("Extra diurna",0)
    h_en = st.number_input("Extra nocturna",0)
    h_ef = st.number_input("Extra dominical",0)
    h_end = st.number_input("Extra nocturna dominical",0)

    st.subheader("Recargos")
    h_rn = st.number_input("Recargo nocturno",0)
    h_rd = st.number_input("Recargo dominical",0)

    bonificaciones = st.number_input("Bonificaciones",0)

    st.subheader("Deducciones")
    consumos = st.number_input("Consumos",0)
    danos = st.number_input("Daños",0)
    ahorros = st.number_input("Ahorros",0)
    otros = st.number_input("Otros",0)

    agregar = st.form_submit_button("Agregar")

    if agregar:
        valor_hora = salario_mensual / 220
        salario = (salario_mensual/30)*dias_trabajados

        # Extras
        ed = valor_hora*1.25*h_ed
        en = valor_hora*1.75*h_en
        ef = valor_hora*2.15*h_ef
        end = valor_hora*2.65*h_end

        # Recargos
        rn = valor_hora*0.35*h_rn
        rd = valor_hora*0.90*h_rd

        ibc = salario + ed + en + ef + end + rn + rd

        salud = ibc*0.04
        pension = 0 if no_pension else ibc*0.04

        auxilio = 0
        if salario_mensual <= 3501810:
            auxilio = (249095/30)*dias_trabajados

        devengado = ibc + auxilio + bonificaciones
        deducciones = salud + pension + consumos + danos + ahorros + otros
        neto = devengado - deducciones

        st.session_state.empleados.append({
            "Empleado": nombre,
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
            "Neto": neto
        })

        st.success("Empleado agregado")

# Lista
st.header("Empleados")
for emp in st.session_state.empleados:
    st.write(emp["Empleado"], pesos(emp["Neto"]))

# PDF
def generar_pdf(emp):
    archivo = f"colilla_{emp['Empleado']}.pdf"
    c = canvas.Canvas(archivo, pagesize=letter)

    y = 800

    # LOGO
    if logo:
        try:
            with open("logo_temp.png", "wb") as f:
                f.write(logo.getbuffer())
            c.drawImage("logo_temp.png", 50, 740, width=120, height=60)
            y = 700  # baja contenido para no chocar
        except:
            pass

    # Título
    c.setFont("Helvetica-Bold",14)
    c.drawString(200,y,"COLILLA DE PAGO")
    y -= 30

    c.setFont("Helvetica",10)
    c.drawString(50,y,f"Empresa: {empresa}")
    y -= 15
    c.drawString(50,y,f"Empleado: {emp['Empleado']}")
    y -= 25

    # DEVENGADO
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"DEVENGADO")
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

    # HORAS EXTRAS
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"HORAS EXTRAS")
    y -= 15

    c.setFont("Helvetica",10)
    c.drawString(50,y,f"Extra Diurna ({emp['h_ed']}h)")
    c.drawRightString(550,y,pesos(emp["ed"]))
    y -= 15

    c.drawString(50,y,f"Extra Nocturna ({emp['h_en']}h)")
    c.drawRightString(550,y,pesos(emp["en"]))
    y -= 15

    c.drawString(50,y,f"Extra Dominical ({emp['h_ef']}h)")
    c.drawRightString(550,y,pesos(emp["ef"]))
    y -= 15

    c.drawString(50,y,f"Extra Nocturna Dominical ({emp['h_end']}h)")
    c.drawRightString(550,y,pesos(emp["end"]))
    y -= 20

    # RECARGOS
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"RECARGOS")
    y -= 15

    c.setFont("Helvetica",10)
    c.drawString(50,y,f"Nocturno ({emp['h_rn']}h)")
    c.drawRightString(550,y,pesos(emp["rn"]))
    y -= 15

    c.drawString(50,y,f"Dominical ({emp['h_rd']}h)")
    c.drawRightString(550,y,pesos(emp["rd"]))
    y -= 20

    # DEDUCCIONES
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"DEDUCCIONES")
    y -= 15

    c.setFont("Helvetica",10)
    for campo in ["Salud","Pension","Consumos","Daños","Ahorros","Otros"]:
        c.drawString(50,y,campo)
        c.drawRightString(550,y,pesos(emp[campo]))
        y -= 15

    y -= 10
    c.setFont("Helvetica-Bold",11)
    c.drawString(50,y,"NETO A PAGAR")
    c.drawRightString(550,y,pesos(emp["Neto"]))

    c.save()
    return archivo

# Botón
st.header("Generar PDF")
for i, emp in enumerate(st.session_state.empleados):
    if st.button(f"PDF - {emp['Empleado']}", key=i):
        archivo = generar_pdf(emp)
        with open(archivo, "rb") as f:
            st.download_button("Descargar", f, archivo)
