import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import date
import pandas as pd
import re
from PIL import Image
import os

st.title("LIQUIDADOR DE NÓMINA - MULTI EMPLEADOS")

# Formato pesos colombianos
def pesos(valor):
    return "${:,.0f}".format(valor).replace(",", ".")

# Lista de empleados
if "empleados" not in st.session_state:
    st.session_state.empleados = []

# Datos de empresa
st.subheader("Datos de la empresa")
empresa = st.text_input("Nombre de la empresa")
nit = st.text_input("NIT o Cédula del empleador")
rep_legal = st.text_input("Representante legal / Persona a cargo (opcional)")
rep_cedula = st.text_input("Cédula del representante legal (opcional)")

# Logo
logo = st.file_uploader("Logo de la empresa (opcional)", type=["png", "jpg", "jpeg"])

# Periodo y observaciones
st.subheader("Periodo de pago")
fecha_inicio = st.date_input("Fecha inicio periodo", date.today())
fecha_fin = st.date_input("Fecha fin periodo", date.today())
observaciones = st.text_area("Observaciones / notas")

# Formulario para nuevo empleado
st.subheader("Agregar empleado")
with st.form("nuevo_empleado"):
    nombre = st.text_input("Nombre del empleado")
    cedula = st.text_input("Cédula del empleado")
    salario_mensual = st.number_input("Salario mensual", value=1750905)
    dias_trabajados = st.number_input("Días trabajados (base 30)", min_value=0, max_value=30, value=30)

    # Horas extras
    st.markdown("**Horas extras**")
    extra_diurna_horas = st.number_input("Horas extra diurnas", value=0)
    extra_nocturna_horas = st.number_input("Horas extra nocturnas", value=0)
    extra_dominical_horas = st.number_input("Horas extra dominical/festivo", value=0)
    extra_nocturna_dominical_horas = st.number_input("Horas extra nocturna dominical/festivo", value=0)

    # Recargos
    st.markdown("**Recargos**")
    recargo_nocturno_horas = st.number_input("Horas con recargo nocturno", value=0)
    recargo_dominical_horas = st.number_input("Horas dominicales o festivas", value=0)

    # Otros devengados
    st.markdown("**Otros devengados**")
    bonificaciones = st.number_input("Bonificaciones", value=0)

    # Deducciones
    st.markdown("**Deducciones**")
    consumos = st.number_input("Consumos", value=0)
    danos = st.number_input("Daños", value=0)
    ahorros = st.number_input("Ahorros", value=0)

    submitted = st.form_submit_button("Agregar empleado")
    if submitted:
        # Cálculos
        salario = (salario_mensual / 30) * dias_trabajados
        valor_hora = salario_mensual / 220

        extra_diurna = valor_hora * 1.25 * extra_diurna_horas
        extra_nocturna = valor_hora * 1.75 * extra_nocturna_horas
        extra_dominical = valor_hora * 2.15 * extra_dominical_horas
        extra_nocturna_dominical = valor_hora * 2.65 * extra_nocturna_dominical_horas

        recargo_nocturno = valor_hora * 0.35 * recargo_nocturno_horas
        recargo_dominical = valor_hora * 0.90 * recargo_dominical_horas

        auxilio_transporte = (249095 / 30) * dias_trabajados if salario_mensual <= 3501810 else 0

        devengado = (
            salario + extra_diurna + extra_nocturna + extra_dominical +
            extra_nocturna_dominical + recargo_nocturno + recargo_dominical +
            bonificaciones + auxilio_transporte
        )

        salud = salario * 0.04
        pension = salario * 0.04

        deducciones = salud + pension + consumos + danos + ahorros
        neto = devengado - deducciones

        empleado_data = {
            "Empleado": nombre,
            "Cédula": cedula,
            "Días trabajados": dias_trabajados,
            "Salario": salario,
            "Auxilio Transporte": auxilio_transporte,
            "Horas Extra Diurna": extra_diurna,
            "Horas Extra Nocturna": extra_nocturna,
            "Horas Extra Dominical": extra_dominical,
            "Horas Extra Nocturna Dominical": extra_nocturna_dominical,
            "Recargo Nocturno": recargo_nocturno,
            "Recargo Dominical": recargo_dominical,
            "Bonificaciones": bonificaciones,
            "Devengado": devengado,
            "Salud": salud,
            "Pensión": pension,
            "Consumos": consumos,
            "Daños": danos,
            "Ahorros": ahorros,
            "Deducciones": deducciones,
            "Neto": neto,
            "Resumen Horas": {
                "Extra Diurna": extra_diurna_horas,
                "Extra Nocturna": extra_nocturna_horas,
                "Extra Dominical/Festivo": extra_dominical_horas,
                "Extra Nocturna Dominical/Festivo": extra_nocturna_dominical_horas,
                "Recargo Nocturno": recargo_nocturno_horas,
                "Recargo Dominical/Festivo": recargo_dominical_horas
            }
        }

        st.session_state.empleados.append(empleado_data)
        st.success(f"Empleado {nombre} agregado")

# Mostrar empleados agregados
st.subheader("Empleados agregados")
for idx, emp in enumerate(st.session_state.empleados):
    st.write(f"{idx+1}. {emp['Empleado']} - Neto a pagar: {pesos(emp['Neto'])}")

# Función PDF corregida
def generar_pdf(empleado_data):
    nombre_seguro = re.sub(r'[^a-zA-Z0-9_]', '', empleado_data['Empleado'].replace(' ', '_'))
    archivo = f"colilla_{nombre_seguro}.pdf"
    c = canvas.Canvas(archivo, pagesize=letter)
    y = 750

    # LOGO CORREGIDO
    if logo is not None:
        image = Image.open(logo)
        image.save("temp_logo.png")
        c.drawImage("temp_logo.png", 50, 730, width=100, height=50)

    # TITULO
    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, 750, "COLILLA DE PAGO")
    y -= 40
    c.setFont("Helvetica", 10)

    # Datos empresa y empleado
    c.drawString(50, y, f"Empresa: {empresa}")
    y -= 20
    c.drawString(50, y, f"NIT: {nit}")
    y -= 30
    c.drawString(50, y, f"Empleado: {empleado_data['Empleado']}")
    y -= 20
    c.drawString(50, y, f"Cédula: {empleado_data['Cédula']}")
    y -= 20
    c.drawString(50, y, f"Días trabajados: {empleado_data['Días trabajados']}")
    y -= 30
    c.drawString(50, y, f"Periodo: {fecha_inicio} a {fecha_fin}")
    y -= 20
    c.drawString(50, y, f"Observaciones: {observaciones}")
    y -= 30

    # Resumen horas
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "RESUMEN HORAS EXTRAS / RECARGOS")
    y -= 20
    c.setFont("Helvetica", 10)
    for k, v in empleado_data["Resumen Horas"].items():
        c.drawString(50, y, f"{k}: {v} horas")
        y -= 15
    y -= 10

    # Devengados
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "DEVENGADOS")
    c.drawRightString(550, y, "VALOR")
    y -= 20
    c.setFont("Helvetica", 10)
    devengados_lista = [
        ("Salario", empleado_data["Salario"]),
        ("Auxilio transporte", empleado_data["Auxilio Transporte"]),
        ("Horas Extra Diurna", empleado_data["Horas Extra Diurna"]),
        ("Horas Extra Nocturna", empleado_data["Horas Extra Nocturna"]),
        ("Horas Extra Dominical", empleado_data["Horas Extra Dominical"]),
        ("Horas Extra Nocturna Dominical", empleado_data["Horas Extra Nocturna Dominical"]),
        ("Recargo Nocturno", empleado_data["Recargo Nocturno"]),
        ("Recargo Dominical", empleado_data["Recargo Dominical"]),
        ("Bonificaciones", empleado_data["Bonificaciones"])
    ]
    for concepto, valor in devengados_lista:
        c.drawString(50, y, concepto)
        c.drawRightString(550, y, pesos(valor))
        y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "TOTAL DEVENGADO")
    c.drawRightString(550, y, pesos(empleado_data["Devengado"]))
    y -= 40

    # Deducciones
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "DEDUCCIONES")
    c.drawRightString(550, y, "VALOR")
    y -= 20
    c.setFont("Helvetica", 10)
    deducciones_lista = [
        ("Salud", empleado_data["Salud"]),
        ("Pensión", empleado_data["Pensión"]),
        ("Consumos", empleado_data["Consumos"]),
        ("Daños", empleado_data["Daños"]),
        ("Ahorros", empleado_data["Ahorros"])
    ]
    for concepto, valor in deducciones_lista:
        c.drawString(50, y, concepto)
        c.drawRightString(550, y, pesos(valor))
        y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "TOTAL DEDUCCIONES")
    c.drawRightString(550, y, pesos(empleado_data["Deducciones"]))
    y -= 40

    # Neto
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "NETO A PAGAR")
    c.drawRightString(550, y, pesos(empleado_data["Neto"]))
    y -= 80

    # Líneas de firma
    if rep_legal and rep_cedula:
        c.line(50, y, 250, y)
        c.drawString(50, y-15, f"{rep_legal} - {rep_cedula}")
        c.drawString(50, y-30, "Representante legal / Persona a cargo")
    c.line(300, y, 550, y)
    c.drawString(300, y-15, f"{empleado_data['Empleado']} - {empleado_data['Cédula']}")
    c.drawString(300, y-30, "Empleado / Aprobación")

    c.save()

    # Borrar logo temporal
    if logo is not None:
        os.remove("temp_logo.png")

    return archivo

# Botones PDF individual con key único
st.subheader("Generar colilla PDF individual")
for idx, emp in enumerate(st.session_state.empleados):
    boton_id = f"pdf_{emp['Empleado'].replace(' ','_')}_{idx}"
    if st.button(f"Generar PDF - {emp['Empleado']}", key=boton_id):
        archivo = generar_pdf(emp)
        with open(archivo, "rb") as file:
            st.download_button(
                label=f"Descargar PDF - {emp['Empleado']}",
                data=file,
                file_name=archivo,
                mime="application/pdf"
            )

# Botón Excel completo
st.subheader("Exportar nómina completa a Excel")
if st.button("Generar Excel de todos los empleados"):
    df = pd.DataFrame(st.session_state.empleados)
    archivo_excel = "nomina_completa.xlsx"
    df.to_excel(archivo_excel, index=False)
    with open(archivo_excel, "rb") as file:
        st.download_button(
            label="Descargar Excel completo",
            data=file,
            file_name=archivo_excel,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
