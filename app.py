# app.py

# pip install -r requirements.txt para instalar dependencias

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io
import plotly.graph_objects as go
import locale
import datetime

st.set_page_config(page_title="Informe por Jefe", layout="wide")



locale.setlocale(locale.LC_TIME, "es_PY.UTF-8")
 # Para sistemas Linux/mac
# En Windows puede ser "Spanish_Paraguay" o "es_PY" si falla, probamos más abajo



url = "https://onedrive.live.com/personal/4ee4a6d408e38949/_layouts/15/Doc.download?sourcedoc=%7Bf2be71d5-e7ce-4cf1-97e2-fa1aec36b910%7D&action=default&redeem=aHR0cHM6Ly8xZHJ2Lm1zL3gvYy80ZWU0YTZkNDA4ZTM4OTQ5L0VkVnh2dkxPNV9GTWwtTDZHdXcydVJBQjM1Zzd3dHZuclV2a2FsTTZmNTltdVE_ZT12eTYzTEU&slrid=dbc69fa1-10b6-8000-f9aa-23b6d01dfcda&originalPath=aHR0cHM6Ly8xZHJ2Lm1zL3gvYy80ZWU0YTZkNDA4ZTM4OTQ5L0VkVnh2dkxPNV9GTWwtTDZHdXcydVJBQjM1Zzd3dHZuclV2a2FsTTZmNTltdVE_cnRpbWU9cURNT2doU1gzVWc&CID=76b65d10-0079-4365-a4b6-5681317e565e&_SRM=0:G:37"
# 🔐 Login básico (manual)
# =========================

usuarios_validos = {k.lower(): v for k, v in st.secrets["usuarios"].items()}




if "logueado" not in st.session_state:
    st.session_state.logueado = False

def login(usuario, clave):
    if usuario in usuarios_validos and usuarios_validos[usuario] == clave:
        st.session_state.logueado = True
        st.session_state.usuario = usuario
        return True
    return False

if not st.session_state.logueado:
    st.title("🔐 Acceso restringido")
    usuario = st.text_input("Usuario").lower()
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if login(usuario, password):
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

# Función para exportar DataFrame a Excel en memoria
def generar_excel(df, nombre_hoja="Resumen"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=True, sheet_name=nombre_hoja)
    output.seek(0)
    return output

# Función para formato paraguayo con símbolo ₲
def formatear_guaranies(valor):
    try:
        return f"₲ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor

# Función para formato sin símbolo (ej. margen)
def formatear_numero(valor):
    try:
        if pd.isna(valor):
            return ""
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return ""
    
def formatear_porcentaje(valor):
    try:
        return f"{valor:.2f}%".replace(".", ",")
    except:
        return valor



def formatear_numeroint(valor):
    try:
        return f"{valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor

# Título
st.title("📊 Informe Comercial por Jefe de Área")

# Cargar los datos
@st.cache_data
def cargar_datos():
    df = pd.read_excel(url, engine="openpyxl")
    return df

df = cargar_datos()

with st.sidebar:
    st.markdown(f"👤 Usuario: `{st.session_state.usuario}`")
    if st.button("🔓 Cerrar sesión"):
        st.session_state.logueado = False
        st.session_state.usuario = None
        st.rerun()


if "FECHA" not in df.columns:
    st.error("❌ El archivo no contiene la columna 'FECHA'.")
    st.stop()

# Filtro por rango de fechas
min_fecha = df["FECHA"].min()
max_fecha = df["FECHA"].max()

st.markdown("### 📅 Filtro de fechas para la vista general")
fecha_inicio, fecha_fin = st.date_input(
    "Seleccioná el rango de fechas para KPIs y tablas:",
    value=(min_fecha.date(), max_fecha.date()),
    min_value=min_fecha.date(),
    max_value=max_fecha.date()
)

df_rango = df[
    (df["FECHA"] >= pd.to_datetime(fecha_inicio)) &
    (df["FECHA"] <= pd.to_datetime(fecha_fin))
]

# Validar columna clave
usuario = st.session_state.usuario
if usuario == "admin":
    datos_filtrados = df_rango.copy()
else:
    datos_filtrados = df_rango[df_rango["JEFE_AREA"] == usuario]

st.markdown(f"👤 Usuario logueado: `{usuario}`")
st.markdown(f"🔎 Filas visibles: {len(datos_filtrados)}")
st.dataframe(datos_filtrados.head(), use_container_width=True)


# Mostrar tabla filtrada
st.subheader(f"📋 Datos del jefe: {usuario}")

# Crear una copia solo para la tabla y formatear la fecha como texto
tabla_para_mostrar = datos_filtrados.copy()
if "FECHA" in tabla_para_mostrar.columns:
    tabla_para_mostrar["FECHA"] = tabla_para_mostrar["FECHA"].dt.strftime("%d/%m/%Y")

# Mostrar tabla con fecha formateada
st.dataframe(tabla_para_mostrar, use_container_width=True)
 

# KPIs
st.subheader("📌 Indicadores Clave (KPIs)")

col_venta = "Valor de Vtas:"
col_utilidad = "Valor:"
col_margen = "%:"

cols_necesarias = [col_venta, col_utilidad, col_margen]
if not all(col in datos_filtrados.columns for col in cols_necesarias):
    st.warning("Faltan columnas para calcular KPIs. Revisá si existen 'Valor de Vtas:', 'Valor:', y '%:'.")
else:
    total_venta = datos_filtrados[col_venta].sum()
    total_utilidad = datos_filtrados[col_utilidad].sum()
    margen_promedio = datos_filtrados[col_margen].replace([np.inf, -np.inf], np.nan).dropna().mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("💸 Total Ventas", formatear_guaranies(total_venta))
    col2.metric("📈 Total Utilidad", formatear_guaranies(total_utilidad))
    col3.metric("📊 Margen Promedio", f"{formatear_numero(margen_promedio)} %")


# Gráfico de evolución mensual
if "FECHA" in datos_filtrados.columns and col_venta in datos_filtrados.columns:
    df_mes = datos_filtrados.copy()
    df_mes["MES"] = df_mes["FECHA"].dt.to_period("M").astype(str)
    ventas_por_mes = df_mes.groupby("MES")[col_venta].sum().reset_index()

    fig = px.line(ventas_por_mes, x="MES", y=col_venta, title=f"Evolución de Ventas - {usuario}")
    fig.update_traces(mode="lines+markers")
    fig.update_layout(xaxis_title="Mes", yaxis_title="Ventas", hovermode="x unified")
    fig.update_layout(yaxis_tickprefix="₲ ", yaxis_tickformat=",")

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No se encontraron columnas 'FECHA' y 'Valor de Vtas:' para graficar la evolución mensual.")


# Gráfico de ventas por LOCAL (sucursal)
if "LOCAL" in datos_filtrados.columns and col_venta in datos_filtrados.columns:
    ventas_por_local = datos_filtrados.groupby("LOCAL")[col_venta].sum().reset_index()
    ventas_por_local = ventas_por_local.sort_values(by=col_venta, ascending=False)

    fig_local = px.bar(
        ventas_por_local,
        x="LOCAL",
        y=col_venta,
        title="Ventas por Sucursal",
        labels={col_venta: "Ventas"},
        text=col_venta
    )
    fig_local.update_layout(
        xaxis_title="Sucursal",
        yaxis_title="Ventas (₲)",
        yaxis_tickprefix="₲ ",
        yaxis_tickformat=",",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    fig_local.update_traces(texttemplate='%{text:,.0f}', textposition='outside')

    st.plotly_chart(fig_local, use_container_width=True)
else:
    st.warning("No se encontraron columnas 'LOCAL' y 'Valor de Vtas:' para graficar ventas por sucursal.")


# Comparativo mensual: mes actual vs mes anterior vs mismo mes del año anterior
if "FECHA" in datos_filtrados.columns and col_venta in datos_filtrados.columns:
    df_cmp = datos_filtrados.copy()
    df_cmp["AÑO"] = df_cmp["FECHA"].dt.year
    df_cmp["MES"] = df_cmp["FECHA"].dt.month
    df_cmp["MES_AÑO"] = df_cmp["FECHA"].dt.to_period("M").astype(str)

    # Sumar ventas por mes-año
    ventas_mensuales = df_cmp.groupby(["AÑO", "MES", "MES_AÑO"])[col_venta].sum().reset_index()

    # Reordenar por fecha real
    ventas_mensuales["FECHA_ORDEN"] = pd.to_datetime(ventas_mensuales["MES_AÑO"])
    ventas_mensuales = ventas_mensuales.sort_values("FECHA_ORDEN")

    # Calcular desplazamientos
    ventas_mensuales["Mes anterior"] = ventas_mensuales[col_venta].shift(1)
    ventas_mensuales["Año anterior"] = ventas_mensuales[col_venta].shift(12)

    # Renombrar columna original para claridad
    ventas_mensuales.rename(columns={col_venta: "Mes actual"}, inplace=True)

    # Derretir para gráfico múltiple
    df_plot = ventas_mensuales[["MES_AÑO", "Mes actual", "Mes anterior", "Año anterior"]].melt(id_vars="MES_AÑO",
                                                                                               var_name="Tipo",
                                                                                               value_name="Ventas")

    # Crear gráfico
    fig_cmp = px.line(df_plot, x="MES_AÑO", y="Ventas", color="Tipo", markers=True,
                      title="📈 Comparativo Mensual de Ventas")
    fig_cmp.update_layout(
        xaxis_title="Mes",
        yaxis_title="Ventas (₲)",
        yaxis_tickprefix="₲ ",
        yaxis_tickformat=",",
        hovermode="x unified"
    )

    st.plotly_chart(fig_cmp, use_container_width=True)
else:
    st.warning("No se puede mostrar el comparativo mensual. Verificá que existan las columnas necesarias.")



st.subheader("📘 Tabla resumen de MARGEN por Sector, Subsector y Marca")

if all(col in datos_filtrados.columns for col in ["SECTOR", "SUBSECTOR", "MARCA", "LOCAL", "%:"]):
    tabla_margen = pd.pivot_table(
        datos_filtrados,
        index=["SECTOR", "SUBSECTOR", "MARCA"],
        columns="LOCAL",
        values="%:",
        aggfunc="mean"
    )

    # Formatear como texto estilo regional
    tabla_margen = tabla_margen.map(formatear_numero)

    st.dataframe(tabla_margen, use_container_width=True)
    # Botón de descarga
    excel_margen = generar_excel(tabla_margen, "Margen")
    st.download_button(
        label="⬇️ Descargar tabla de margen",
        data=excel_margen,
        file_name=f"tabla_margen_{usuario}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("Faltan columnas para generar la tabla de margen.")
    


st.subheader("📘 Tabla resumen de VENTAS por Sector, Subsector y Marca")

if all(col in datos_filtrados.columns for col in ["SECTOR", "SUBSECTOR", "MARCA", "LOCAL", "Valor de Vtas:"]):
    tabla_ventas = pd.pivot_table(
        datos_filtrados,
        index=["SECTOR", "SUBSECTOR", "MARCA"],
        columns="LOCAL",
        values="Valor de Vtas:",
        aggfunc="sum"
    )

    tabla_ventas = tabla_ventas.map(formatear_guaranies)

    st.dataframe(tabla_ventas, use_container_width=True)

    excel_ventas = generar_excel(tabla_ventas, "Ventas")
    st.download_button(
        label="⬇️ Descargar tabla de ventas",
        data=excel_ventas,
        file_name=f"tabla_ventas_{usuario}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


st.subheader("📘 Tabla resumen de UTILIDAD por Sector, Subsector y Marca")

if all(col in datos_filtrados.columns for col in ["SECTOR", "SUBSECTOR", "LOCAL", "Valor:"]):
    tabla_utilidad = pd.pivot_table(
        datos_filtrados,
        index=["SECTOR", "SUBSECTOR"],
        columns="LOCAL",
        values="Valor:",
        aggfunc="sum"
    )

    tabla_utilidad = tabla_utilidad.map(formatear_guaranies)

    st.dataframe(tabla_utilidad, use_container_width=True)

    excel_utilidad = generar_excel(tabla_utilidad, "Utilidad")
    st.download_button(
    label="⬇️ Descargar tabla de utilidad",
    data=excel_utilidad,
    file_name=f"tabla_utilidad_{usuario}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )






st.subheader("📊 Comparativo mensual: Ventas actuales vs mes anterior + variación (%)")

if "FECHA" in datos_filtrados.columns and col_venta in datos_filtrados.columns:
    df_cmp = datos_filtrados.copy()
    df_cmp["MES_AÑO"] = df_cmp["FECHA"].dt.to_period("M").astype(str)

    # Agrupar por mes
    ventas_mes = df_cmp.groupby("MES_AÑO")[col_venta].sum().reset_index()
    ventas_mes = ventas_mes.sort_values("MES_AÑO")

    # Desplazamiento
    ventas_mes["VENTA_ANTERIOR"] = ventas_mes[col_venta].shift(1)
    ventas_mes["VARIACION_%"] = ((ventas_mes[col_venta] - ventas_mes["VENTA_ANTERIOR"]) / ventas_mes["VENTA_ANTERIOR"]) * 100
    ventas_mes["VARIACION_%"] = ventas_mes["VARIACION_%"].fillna(0)

    # Crear figura combinada
    fig_combo = go.Figure()

    # Barra mes actual
    fig_combo.add_trace(go.Bar(
        x=ventas_mes["MES_AÑO"],
        y=ventas_mes[col_venta],
        name="Mes actual",
        marker_color="rgb(55, 83, 109)",
        yaxis="y"
    ))

    # Barra mes anterior
    fig_combo.add_trace(go.Bar(
        x=ventas_mes["MES_AÑO"],
        y=ventas_mes["VENTA_ANTERIOR"],
        name="Mes anterior",
        marker_color="rgb(112, 147, 179)",
        yaxis="y"
    ))

    # Línea de variación (%) con etiquetas
    fig_combo.add_trace(go.Scatter(
        x=ventas_mes["MES_AÑO"],
        y=ventas_mes["VARIACION_%"],
        name="Variación %",
        mode="lines+markers+text",
        marker=dict(color="red"),
        yaxis="y2",
        text=[f"{v:.1f}%" if not pd.isna(v) else "" for v in ventas_mes["VARIACION_%"]],
        textposition="top center",
        textfont=dict(color="white", size=13, family="Arial", weight="bold")
    ))


    # Layout dual eje
    fig_combo.update_layout(
        title="📊 Ventas y variación mensual",
        barmode="group",
        xaxis=dict(title="Mes"),
        yaxis=dict(
            title="Ventas (₲)",
            tickprefix="₲ ",
            tickformat=","
        ),
        yaxis2=dict(
            title="Variación (%)",
            overlaying="y",
            side="right",
            tickformat=".2f"
        ),
        legend=dict(x=0.01, y=0.99),
        hovermode="x unified"
    )

    st.plotly_chart(fig_combo, use_container_width=True)
else:
    st.warning("No se puede generar el gráfico combinado. Faltan columnas necesarias.")


##parte dos analisis de tiempo mas precisos

# Extraer opciones únicas de meses disponibles
df["MES_AÑO"] = df["FECHA"].dt.to_period("M") #esto es para que el mes y año se vean como un solo valor
  # mismo mes, pero del año anterior

#que el selector sea tipo abril-2024
# Convertir a string para el selectbox
# df["MES_AÑO"] = df["MES_AÑO"].dt.strftime("%B-%Y")

meses_periodos = sorted(df["FECHA"].dt.to_period("M").dropna().unique())
mes_labels = [p.to_timestamp().strftime("%B-%Y").upper() for p in meses_periodos]
label_to_period = dict(zip(mes_labels, meses_periodos))

# Selector de mes con nombres
mes_elegido_label = st.selectbox("🗓 Seleccioná un mes para comparar:", mes_labels)
mes_analizado = label_to_period[mes_elegido_label]
mes_anterior = mes_analizado - 1
mes_anterior_anio = mes_analizado - 12
# Convertir a datetime para filtrar
# Fecha actual y anterior
fecha_actual = mes_analizado.to_timestamp()
fecha_anterior = fecha_actual - pd.DateOffset(months=1)

# Datos del mes actual y anterior
if usuario == "admin":
    datos_mes_actual = df[df["FECHA"].dt.to_period("M") == mes_analizado].copy()
    datos_mes_anterior = df[df["FECHA"].dt.to_period("M") == (mes_analizado - 1)].copy()
    datos_mes_aa = df[df["FECHA"].dt.to_period("M") == (mes_analizado - 12)].copy()
else:
    datos_mes_actual = df[
        (df["JEFE_AREA"] == usuario) &
        (df["FECHA"].dt.to_period("M") == mes_analizado)
    ].copy()
    datos_mes_anterior = df[
        (df["JEFE_AREA"] == usuario) &
        (df["FECHA"].dt.to_period("M") == (mes_analizado - 1))
    ].copy()
    datos_mes_aa = df[
        (df["JEFE_AREA"] == usuario) &
        (df["FECHA"].dt.to_period("M") == (mes_analizado - 12))
    ].copy()


st.subheader(f"📋 Resumen de KPIs Anuales – {mes_analizado}")

col_venta = "Valor de Vtas:"
col_costo = "Costo de Vtas:"

# Total ventas
ventas_actual = datos_mes_actual[col_venta].sum()
ventas_anio_ant = datos_mes_aa[col_venta].sum()
delta_ventas = ((ventas_actual - ventas_anio_ant) / ventas_anio_ant) * 100 if ventas_anio_ant else 0

# Total utilidad
util_actual = (datos_mes_actual[col_venta] - datos_mes_actual[col_costo]).sum()
util_anio_ant = (datos_mes_aa[col_venta] - datos_mes_aa[col_costo]).sum()
delta_util = ((util_actual - util_anio_ant) / util_anio_ant) * 100 if util_anio_ant else 0

# Margen promedio
margen_actual = util_actual / ventas_actual if ventas_actual else 0
margen_anio_ant = util_anio_ant / ventas_anio_ant if ventas_anio_ant else 0
delta_margen = margen_actual - margen_anio_ant

# Mostrar métricas
col1, col2, col3 = st.columns(3)

col1.metric(
    label="💰 Ventas Totales",
    value=formatear_guaranies(ventas_actual),
    delta=formatear_porcentaje(delta_ventas)
)

col2.metric(
    label="📈 Utilidad Total",
    value=formatear_guaranies(util_actual),
    delta=formatear_porcentaje(delta_util)
)

col3.metric(
    label="📊 Margen Promedio",
    value=formatear_porcentaje(margen_actual),
    delta=formatear_porcentaje(delta_margen)
)








st.subheader("📊 Variación Mensual de Ventas por Local y Sector")

col_venta = "Valor de Vtas:"
grupo = ["LOCAL", "SECTOR"]

# Agrupar ventas por mes actual y anterior
actual_grouped = datos_mes_actual.groupby(grupo)[col_venta].sum().reset_index().rename(columns={col_venta: "ventas_mes_actual"})
anterior_grouped = datos_mes_anterior.groupby(grupo)[col_venta].sum().reset_index().rename(columns={col_venta: "ventas_mes_anterior"})

# Combinar
variacion = pd.merge(actual_grouped, anterior_grouped, on=grupo, how="outer").fillna(0)

# Calcular variaciones
variacion["variacion_%"] = ((variacion["ventas_mes_actual"] - variacion["ventas_mes_anterior"]) / 
                            variacion["ventas_mes_anterior"].replace(0, pd.NA)) * 100
variacion["diferencia"] = variacion["ventas_mes_actual"] - variacion["ventas_mes_anterior"]

#copiamos y mostramos la tabla mas lindo
tabla_para_mostrar = variacion.copy()

tabla_para_mostrar["ventas_mes_actual"] = tabla_para_mostrar["ventas_mes_actual"].map(formatear_guaranies)
tabla_para_mostrar["ventas_mes_anterior"] = tabla_para_mostrar["ventas_mes_anterior"].map(formatear_guaranies)
tabla_para_mostrar["variacion_%"] = tabla_para_mostrar["variacion_%"].map(formatear_porcentaje)
tabla_para_mostrar["diferencia"] = tabla_para_mostrar["diferencia"].map(formatear_guaranies)

st.dataframe(tabla_para_mostrar, use_container_width=True)
# Botón de descarga con datos originales
excel_variacion = generar_excel(variacion, nombre_hoja="Variación de Ventas")
st.download_button(
    label="⬇️ Descargar tabla de variación mensual",
    data=excel_variacion,
    file_name=f"variacion_mensual_{mes_analizado}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


st.subheader("📆 Comparativo Anual de Ventas por Local y Sector")

col_venta = "Valor de Vtas:"
grupo = ["LOCAL", "SECTOR"]

# Agrupación por mes actual
actual_grouped = datos_mes_actual.groupby(grupo)[col_venta].sum().reset_index()
actual_grouped = actual_grouped.rename(columns={col_venta: "ventas_actual"})

# Agrupación por mismo mes del año anterior
aa_grouped = datos_mes_aa.groupby(grupo)[col_venta].sum().reset_index()
aa_grouped = aa_grouped.rename(columns={col_venta: "ventas_anio_anterior"})

# Combinar
comparativo_aa = pd.merge(actual_grouped, aa_grouped, on=grupo, how="outer").fillna(0)

# Cálculos
comparativo_aa["variacion_%"] = (
    (comparativo_aa["ventas_actual"] - comparativo_aa["ventas_anio_anterior"]) /
    comparativo_aa["ventas_anio_anterior"].replace(0, pd.NA)
) * 100

comparativo_aa["diferencia"] = comparativo_aa["ventas_actual"] - comparativo_aa["ventas_anio_anterior"]

# Formato para mostrar
comparativo_mostrar = comparativo_aa.copy()
comparativo_mostrar["ventas_actual"] = comparativo_mostrar["ventas_actual"].map(formatear_guaranies)
comparativo_mostrar["ventas_anio_anterior"] = comparativo_mostrar["ventas_anio_anterior"].map(formatear_guaranies)
comparativo_mostrar["variacion_%"] = comparativo_mostrar["variacion_%"].round(2).map(formatear_porcentaje)
comparativo_mostrar["diferencia"] = comparativo_mostrar["diferencia"].map(formatear_guaranies)

st.dataframe(comparativo_mostrar.fillna(""), use_container_width=True)

# Descarga
excel_comparativo_aa = generar_excel(comparativo_aa, "Comparativo Anual Ventas")
st.download_button(
    label="⬇️ Descargar comparativo anual de ventas",
    data=excel_comparativo_aa,
    file_name=f"ventas_vs_año_pasado_{mes_analizado}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)



st.subheader("📊 Comparación Mensual de Ventas por Local")

# Agrupar
ventas_mes = datos_mes_actual.groupby("LOCAL")["Valor de Vtas:"].sum().reset_index().rename(columns={"Valor de Vtas:": "ventas_actual"})
ventas_ant = datos_mes_anterior.groupby("LOCAL")["Valor de Vtas:"].sum().reset_index().rename(columns={"Valor de Vtas:": "ventas_anterior"})
ventas_local_mes = pd.merge(ventas_mes, ventas_ant, on="LOCAL", how="outer").fillna(0)

# Generar etiquetas con formato ₲
ventas_local_mes["ventas_actual_txt"] = ventas_local_mes["ventas_actual"].apply(lambda x: f"₲ {int(x):,}".replace(",", "."))
ventas_local_mes["ventas_anterior_txt"] = ventas_local_mes["ventas_anterior"].apply(lambda x: f"₲ {int(x):,}".replace(",", "."))

# Nombre del mes anterior para el título
nombre_mes_ant = (mes_analizado - 1).strftime("%B-%Y").upper()

# Gráfico con etiquetas
fig_mes = go.Figure(data=[
    go.Bar(
        name="Mes actual",
        x=ventas_local_mes["LOCAL"],
        y=ventas_local_mes["ventas_actual"],
        text=ventas_local_mes["ventas_actual_txt"],
        textposition="outside",
        marker_color="rgb(55, 83, 109)",
        #negrita
        textfont=dict(size=10, color="white", family="Arial", weight="bold")
    ),
    go.Bar(
        name="Mes anterior",
        x=ventas_local_mes["LOCAL"],
        y=ventas_local_mes["ventas_anterior"],
        text=ventas_local_mes["ventas_anterior_txt"],
        textposition="outside",
        marker_color="rgb(204, 204, 204)"
    )
])

fig_mes.update_layout(
    barmode="group",
    title=f"📊 Ventas por Local – {mes_analizado} vs {nombre_mes_ant}",
    xaxis_title="Local",
    yaxis_title="Ventas (₲)",
    yaxis_tickprefix="₲ ",
    yaxis_tickformat=",",
    hovermode="x unified",
    uniformtext_minsize=8,
    uniformtext_mode="hide"
)

st.plotly_chart(fig_mes, use_container_width=True)





st.subheader("📍 Dispersión: Margen vs Utilidad por Subsector")

# Opciones de agrupación
opciones_agrupador = {
    "Subsector": "SUBSECTOR",
    "Sector": "SECTOR",
    "Marca": "MARCA",
    "Local": "LOCAL"
}

# Selector de dimensión
dimension_seleccionada = st.selectbox("Agrupar por:", list(opciones_agrupador.keys()))
agrupador = opciones_agrupador[dimension_seleccionada]

# Limpieza solo si la columna existe y tiene valores válidos
if agrupador not in datos_mes_actual.columns:
    st.warning(f"La columna {agrupador} no está disponible en los datos.")
    st.stop()

# Eliminar nulos
datos_filtrados = datos_mes_actual[datos_mes_actual[agrupador].notna()].copy()

# Convertir a string por seguridad (Plotly a veces falla con ints o mixtos)
datos_filtrados[agrupador] = datos_filtrados[agrupador].astype(str)

col_venta = "Valor de Vtas:"
col_costo = "Costo de Vtas:"

# Agrupación
df_disp = datos_filtrados.groupby(agrupador).agg({
    col_venta: "sum",
    col_costo: "sum"
}).reset_index()

df_disp["UTILIDAD"] = df_disp[col_venta] - df_disp[col_costo]
df_disp["MARGEN_%"] = (df_disp["UTILIDAD"] / df_disp[col_venta].replace(0, pd.NA)) * 100

# Filtro opcional: eliminar casos sin ventas
df_disp = df_disp[df_disp[col_venta] > 0]
# Limitar a las 50 marcas con más ventas
df_disp = df_disp.sort_values(col_venta, ascending=False).head(50)


# Crear gráfico
fig_disp = px.scatter(
    df_disp,
    x="UTILIDAD",
    y="MARGEN_%",
    size=col_venta,
    text=agrupador,
    color=col_venta,
    labels={"UTILIDAD": "Utilidad (₲)", "MARGEN_%": "Margen (%)"},
    title=f"📍 Margen vs Utilidad por {dimension_seleccionada} – {mes_analizado}",
    hover_name=agrupador,
    size_max=40
)

fig_disp.update_traces(textposition='top center')
fig_disp.update_layout(
    xaxis_tickprefix="₲ ",
    xaxis_tickformat=",",
    yaxis_tickformat=".2f",
    hovermode="closest"
)

st.plotly_chart(fig_disp, use_container_width=True)






st.subheader("📊 Comparación Anual de Ventas por Local")

# Agrupación por LOCAL
ventas_local = comparativo_aa.groupby("LOCAL")[["ventas_actual", "ventas_anio_anterior"]].sum().reset_index()

# Etiquetas con formato ₲
ventas_local["ventas_actual_txt"] = ventas_local["ventas_actual"].apply(lambda x: f"₲ {int(x):,}".replace(",", "."))
ventas_local["ventas_anio_anterior_txt"] = ventas_local["ventas_anio_anterior"].apply(lambda x: f"₲ {int(x):,}".replace(",", "."))

# Crear gráfico con etiquetas
fig = go.Figure(data=[
    go.Bar(
        name="Mes actual",
        x=ventas_local["LOCAL"],
        y=ventas_local["ventas_actual"],
        text=ventas_local["ventas_actual_txt"],
        textposition="outside",
        marker_color="rgb(55, 83, 109)",
        #negrita
        textfont=dict(size=10, color="white", family="Arial", weight="bold")
    ),
    go.Bar(
        name="Mismo mes año anterior",
        x=ventas_local["LOCAL"],
        y=ventas_local["ventas_anio_anterior"],
        text=ventas_local["ventas_anio_anterior_txt"],
        textposition="outside",
        marker_color="rgb(204, 204, 204)"
    )
])

fig.update_layout(
    barmode="group",
    title=f"📊 Ventas por Local – {mes_analizado} vs año anterior",
    xaxis_title="Local",
    yaxis_title="Ventas (₲)",
    yaxis_tickprefix="₲ ",
    yaxis_tickformat=",",
    hovermode="x unified",
    uniformtext_minsize=8,
    uniformtext_mode="hide"
)

st.plotly_chart(fig, use_container_width=True)








st.subheader("📈 Variación Mensual de Margen por Local y Sector")

col_venta = "Valor de Vtas:"
col_costo = "Costo de Vtas:"
grupo = ["LOCAL", "SECTOR"]

# Margen mes actual
m_actual = datos_mes_actual.copy()
m_actual = m_actual.groupby(grupo).agg({col_venta: "sum", col_costo: "sum"}).reset_index()
m_actual["margen_actual"] = (m_actual[col_venta] - m_actual[col_costo]) / m_actual[col_venta]
m_actual.drop(columns=[col_venta, col_costo], inplace=True)

# Margen mes anterior
m_anterior = datos_mes_anterior.copy()
m_anterior = m_anterior.groupby(grupo).agg({col_venta: "sum", col_costo: "sum"}).reset_index()
m_anterior["margen_anterior"] = (m_anterior[col_venta] - m_anterior[col_costo]) / m_anterior[col_venta]
m_anterior.drop(columns=[col_venta, col_costo], inplace=True)

# Merge y cálculo
tabla_margen = pd.merge(m_actual, m_anterior, on=grupo, how="outer").fillna(0)
tabla_margen["diferencia_margen"] = tabla_margen["margen_actual"] - tabla_margen["margen_anterior"]

# Formato
tabla_mostrar = tabla_margen.copy()
tabla_mostrar["margen_actual"] = tabla_mostrar["margen_actual"].map(formatear_porcentaje)
tabla_mostrar["margen_anterior"] = tabla_mostrar["margen_anterior"].map(formatear_porcentaje)
tabla_mostrar["diferencia_margen"] = tabla_mostrar["diferencia_margen"].map(formatear_porcentaje)

st.dataframe(tabla_mostrar, use_container_width=True)

# Botón de descarga
excel_margen = generar_excel(tabla_margen, "Variación de Margen")
st.download_button(
    label="⬇️ Descargar tabla de margen",
    data=excel_margen,
    file_name=f"variacion_margen_{mes_analizado}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)



st.subheader("📆 Comparativo Anual de Margen por Local y Sector")

col_venta = "Valor de Vtas:"
col_costo = "Costo de Vtas:"
grupo = ["LOCAL", "SECTOR"]

# Calcular margen actual
m_actual = datos_mes_actual.groupby(grupo).agg({col_venta: "sum", col_costo: "sum"}).reset_index()
m_actual["margen_actual"] = (m_actual[col_venta] - m_actual[col_costo]) / m_actual[col_venta]
m_actual = m_actual[grupo + ["margen_actual"]]

# Calcular margen mismo mes del año anterior
m_aa = datos_mes_aa.groupby(grupo).agg({col_venta: "sum", col_costo: "sum"}).reset_index()
m_aa["margen_anio_anterior"] = (m_aa[col_venta] - m_aa[col_costo]) / m_aa[col_venta]
m_aa = m_aa[grupo + ["margen_anio_anterior"]]

# Combinar
tabla_margen_aa = pd.merge(m_actual, m_aa, on=grupo, how="outer").fillna(0)

# Variación de margen
tabla_margen_aa["variacion_margen"] = tabla_margen_aa["margen_actual"] - tabla_margen_aa["margen_anio_anterior"]

# Formato
tabla_mostrar_aa = tabla_margen_aa.copy()
tabla_mostrar_aa["margen_actual"] = tabla_mostrar_aa["margen_actual"].map(formatear_porcentaje)
tabla_mostrar_aa["margen_anio_anterior"] = tabla_mostrar_aa["margen_anio_anterior"].map(formatear_porcentaje)
tabla_mostrar_aa["variacion_margen"] = tabla_mostrar_aa["variacion_margen"].map(formatear_porcentaje)

st.dataframe(tabla_mostrar_aa.fillna(""), use_container_width=True)

# Descarga 44
excel_margen_aa = generar_excel(tabla_margen_aa, "Comparativo Anual Margen")
st.download_button(
    label="⬇️ Descargar comparativo anual de margen",
    data=excel_margen_aa,
    file_name=f"margen_vs_año_pasado_{mes_analizado}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)





st.subheader("💵 Variación Mensual de Utilidad por Local y Sector")

col_venta = "Valor de Vtas:"
col_costo = "Costo de Vtas:"
grupo = ["LOCAL", "SECTOR"]

# Utilidad mes actual
u_actual = datos_mes_actual.copy()
u_actual = u_actual.groupby(grupo).agg({col_venta: "sum", col_costo: "sum"}).reset_index()
u_actual["utilidad_actual"] = u_actual[col_venta] - u_actual[col_costo]
u_actual = u_actual[grupo + ["utilidad_actual"]]

# Utilidad mes anterior
u_anterior = datos_mes_anterior.copy()
u_anterior = u_anterior.groupby(grupo).agg({col_venta: "sum", col_costo: "sum"}).reset_index()
u_anterior["utilidad_anterior"] = u_anterior[col_venta] - u_anterior[col_costo]
u_anterior = u_anterior[grupo + ["utilidad_anterior"]]

# Unir y calcular
tabla_utilidad = pd.merge(u_actual, u_anterior, on=grupo, how="outer").fillna(0)
tabla_utilidad["variacion_%"] = ((tabla_utilidad["utilidad_actual"] - tabla_utilidad["utilidad_anterior"]) / 
                                 tabla_utilidad["utilidad_anterior"].replace(0, pd.NA)) * 100
tabla_utilidad["diferencia"] = tabla_utilidad["utilidad_actual"] - tabla_utilidad["utilidad_anterior"]

# Formato para mostrar
tabla_u_mostrar = tabla_utilidad.copy()
tabla_u_mostrar["utilidad_actual"] = tabla_u_mostrar["utilidad_actual"].map(formatear_guaranies)
tabla_u_mostrar["utilidad_anterior"] = tabla_u_mostrar["utilidad_anterior"].map(formatear_guaranies)
tabla_u_mostrar["variacion_%"] = tabla_u_mostrar["variacion_%"].round(2).map(formatear_porcentaje)
tabla_u_mostrar["diferencia"] = tabla_u_mostrar["diferencia"].map(formatear_guaranies)

st.dataframe(tabla_u_mostrar, use_container_width=True)

# Botón para descargar
excel_utilidad = generar_excel(tabla_utilidad, "Variación de Utilidad")
st.download_button(
    label="⬇️ Descargar tabla de utilidad",
    data=excel_utilidad,
    file_name=f"variacion_utilidad_{mes_analizado}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


st.subheader("📆 Comparativo Anual de Utilidad por Local y Sector")

col_venta = "Valor de Vtas:"
col_costo = "Costo de Vtas:"
grupo = ["LOCAL", "SECTOR"]

# Utilidad actual
u_actual = datos_mes_actual.groupby(grupo).agg({col_venta: "sum", col_costo: "sum"}).reset_index()
u_actual["utilidad_actual"] = u_actual[col_venta] - u_actual[col_costo]
u_actual = u_actual[grupo + ["utilidad_actual"]]

# Utilidad mismo mes año anterior
u_aa = datos_mes_aa.groupby(grupo).agg({col_venta: "sum", col_costo: "sum"}).reset_index()
u_aa["utilidad_anio_anterior"] = u_aa[col_venta] - u_aa[col_costo]
u_aa = u_aa[grupo + ["utilidad_anio_anterior"]]

# Combinar
tabla_utilidad_aa = pd.merge(u_actual, u_aa, on=grupo, how="outer").fillna(0)

# Variación y diferencia
tabla_utilidad_aa["variacion_%"] = (
    (tabla_utilidad_aa["utilidad_actual"] - tabla_utilidad_aa["utilidad_anio_anterior"]) /
    tabla_utilidad_aa["utilidad_anio_anterior"].replace(0, pd.NA)
) * 100
tabla_utilidad_aa["diferencia"] = tabla_utilidad_aa["utilidad_actual"] - tabla_utilidad_aa["utilidad_anio_anterior"]

# Formato para mostrar
tabla_mostrar_aa = tabla_utilidad_aa.copy()
tabla_mostrar_aa["utilidad_actual"] = tabla_mostrar_aa["utilidad_actual"].map(formatear_guaranies)
tabla_mostrar_aa["utilidad_anio_anterior"] = tabla_mostrar_aa["utilidad_anio_anterior"].map(formatear_guaranies)
tabla_mostrar_aa["variacion_%"] = tabla_mostrar_aa["variacion_%"].round(2).map(formatear_porcentaje)
tabla_mostrar_aa["diferencia"] = tabla_mostrar_aa["diferencia"].map(formatear_guaranies)

st.dataframe(tabla_mostrar_aa.fillna(""), use_container_width=True)

# Descarga
excel_utilidad_aa = generar_excel(tabla_utilidad_aa, "Comparativo Anual Utilidad")
st.download_button(
    label="⬇️ Descargar comparativo anual de utilidad",
    data=excel_utilidad_aa,
    file_name=f"utilidad_vs_año_pasado_{mes_analizado}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)







st.subheader("❌ Productos en Quiebre Total")

# Filtrar productos vendidos sin stock
quiebre = datos_mes_actual.copy()
quiebre = quiebre[
    (quiebre["Valor de Stock:"] <= 0) &
    (quiebre["Valor de Vtas:"] > 0)
]

# Columnas clave a mostrar
columnas_mostrar = ["LOCAL", "SECTOR", "SUBSECTOR", "MARCA", "DESCRIPCION", 
                    "Valor de Vtas:", "Valor de Stock:", "Fec.Ult Compra:"]

# st.write("📋 Columnas en df:", df.columns.tolist())
# st.write("📋 Columnas en quiebre:", quiebre.columns.tolist())

# Verificar columnas disponibles
columnas_presentes = [col for col in columnas_mostrar if col in quiebre.columns]
quiebre_mostrar = quiebre[columnas_presentes].copy()
if "Fec.Ult Compra:" in quiebre_mostrar.columns:
    quiebre_mostrar = quiebre_mostrar.sort_values("Fec.Ult Compra:", ascending=True)




# Formateo si están las columnas
if "Valor de Vtas:" in quiebre_mostrar:
    quiebre_mostrar["Valor de Vtas:"] = quiebre_mostrar["Valor de Vtas:"].map(formatear_guaranies)
if "Valor de Stock:" in quiebre_mostrar:
    quiebre_mostrar["Valor de Stock:"] = quiebre_mostrar["Valor de Stock:"].map(formatear_guaranies)

# Formatear la fecha de última compra si existe
if "Fec.Ult Compra:" in quiebre_mostrar.columns:
    # Convertir a datetime
    quiebre_mostrar["Fec.Ult Compra:"] = pd.to_datetime(quiebre_mostrar["Fec.Ult Compra:"], errors="coerce")

    # Calcular días desde la última compra
    hoy = pd.to_datetime(datetime.date.today())
    quiebre_mostrar["Días sin compra"] = (hoy - quiebre_mostrar["Fec.Ult Compra:"]).dt.days

    # Formatear la fecha para mostrar
    quiebre_mostrar["Fec.Ult Compra:"] = quiebre_mostrar["Fec.Ult Compra:"].dt.strftime("%d/%m/%Y")

st.dataframe(quiebre_mostrar, use_container_width=True)

# Descargar Excel
excel_quiebre = generar_excel(quiebre[columnas_presentes], "Quiebre Total")
st.download_button(
    label="⬇️ Descargar tabla de quiebre total",
    data=excel_quiebre,
    file_name=f"quiebre_total_{mes_analizado}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)



st.subheader("⚠️ Productos en Sobre Stock")
# Copia del mes actual
sobre_stock = datos_mes_actual.copy()

# Calcular MESES DE STOCK
sobre_stock["MESES DE STOCK"] = sobre_stock["Valor de Stock:"] / sobre_stock["Valor de Vtas:"].replace(0, pd.NA)

# Aplicar condición de sobre stock
sobre_stock = sobre_stock[
    (sobre_stock["MESES DE STOCK"] >= 6) |
    ((sobre_stock["Valor de Vtas:"] == 0) & (sobre_stock["Valor de Stock:"] > 0))
]

# Columnas a mostrar
columnas_sobre = [
    "LOCAL", "SECTOR", "SUBSECTOR", "MARCA", "Fec.Ult Compra:",
    "Valor de Vtas:", "Valor de Stock:", "MESES DE STOCK"
]

# Verificar columnas disponibles
columnas_presentes = [col for col in columnas_sobre if col in sobre_stock.columns]
sobre_mostrar = sobre_stock[columnas_presentes].copy()

# Formato de fechas y moneda
if "Fec.Ult Compra:" in sobre_mostrar.columns:
    sobre_mostrar["Fec.Ult Compra:"] = pd.to_datetime(sobre_mostrar["Fec.Ult Compra:"], errors="coerce")
    sobre_mostrar["Días sin compra"] = (pd.to_datetime(datetime.date.today()) - sobre_mostrar["Fec.Ult Compra:"]).dt.days
    sobre_mostrar["Fec.Ult Compra:"] = sobre_mostrar["Fec.Ult Compra:"].dt.strftime("%d/%m/%Y")

if "Valor de Vtas:" in sobre_mostrar:
    sobre_mostrar["Valor de Vtas:"] = sobre_mostrar["Valor de Vtas:"].map(formatear_guaranies)
if "Valor de Stock:" in sobre_mostrar:
    sobre_mostrar["Valor de Stock:"] = sobre_mostrar["Valor de Stock:"].map(formatear_guaranies)
if "MESES DE STOCK" in sobre_mostrar.columns:
    sobre_mostrar["MESES DE STOCK"] = sobre_mostrar["MESES DE STOCK"].map(formatear_numero)
if "Días sin compra" in sobre_mostrar.columns:
    sobre_mostrar["Días sin compra"] = sobre_mostrar["Días sin compra"].map(formatear_numeroint)
    #no mostrar vacios como nan, poner ""

# Mostrar tabla
st.dataframe(sobre_mostrar.fillna(""), use_container_width=True)

# Descargar Excel
excel_sobre = generar_excel(sobre_stock[columnas_presentes], "Sobre Stock")
st.download_button(
    label="⬇️ Descargar tabla de sobre stock",
    data=excel_sobre,
    file_name=f"sobre_stock_{mes_analizado}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)