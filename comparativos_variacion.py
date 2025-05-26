import pandas as pd
import streamlit as st

def mostrar_comparativos_variacion(  
    tabla_ventas_mensual,
    tabla_margen_mensual,
    tabla_utilidad_mensual,
    tabla_ventas_anual,
    tabla_margen_anual,
    tabla_utilidad_anual,
    formatear_guaranies,
    formatear_porcentaje,
    generar_excel
):
    
    df = st.session_state.get("df")
    if df is None:
        st.error("Los datos no están disponibles. Volvé a la página principal.")
        return
    st.header("📊 Comparativo por Tipo de Variación")

    def seccion_variacion(nombre, tabla, campo_variacion, tipo):
        if tabla.empty:
            st.info(f"No hay datos para {nombre} ({tipo})")
            return

        tabla_mostrar = tabla.copy()
        tabla_mostrar = tabla.copy()

        if "variacion_%" in tabla_mostrar:
            tabla_mostrar["variacion_%"] = tabla_mostrar["variacion_%"].map(formatear_porcentaje)

        if "utilidad_actual" in tabla_mostrar:
            tabla_mostrar["utilidad_actual"] = tabla_mostrar["utilidad_actual"].map(formatear_guaranies)

        if "utilidad_anterior" in tabla_mostrar:
            tabla_mostrar["utilidad_anterior"] = tabla_mostrar["utilidad_anterior"].map(formatear_guaranies)

        if "margen_actual" in tabla_mostrar:
            tabla_mostrar["margen_actual"] = tabla_mostrar["margen_actual"].map(formatear_porcentaje)

        if "margen_anterior" in tabla_mostrar:
            tabla_mostrar["margen_anterior"] = tabla_mostrar["margen_anterior"].map(formatear_porcentaje)

        if "ventas_mes_actual" in tabla_mostrar:
            tabla_mostrar["ventas_mes_actual"] = tabla_mostrar["ventas_mes_actual"].map(formatear_guaranies)

        if "ventas_mes_anterior" in tabla_mostrar:
            tabla_mostrar["ventas_mes_anterior"] = tabla_mostrar["ventas_mes_anterior"].map(formatear_guaranies)
        if "ventas_anio_actual" in tabla_mostrar:
            tabla_mostrar["ventas_anio_actual"] = tabla_mostrar["ventas_anio_actual"].map(formatear_guaranies)
        if "ventas_anio_anterior" in tabla_mostrar:
            tabla_mostrar["ventas_anio_anterior"] = tabla_mostrar["ventas_anio_anterior"].map(formatear_guaranies)
        if "diferencia" in tabla_mostrar:
            tabla_mostrar["diferencia"] = tabla_mostrar["diferencia"].map(formatear_guaranies)
        if "ventas_actual" in tabla_mostrar:
            tabla_mostrar["ventas_actual"] = tabla_mostrar["ventas_actual"].map(formatear_guaranies)
        if "margen_anio_anterior" in tabla_mostrar:
            tabla_mostrar["margen_anio_anterior"] = tabla_mostrar["margen_anio_anterior"].map(formatear_porcentaje)
        if "utilidad_anio_anterior" in tabla_mostrar:
            tabla_mostrar["utilidad_anio_anterior"] = tabla_mostrar["utilidad_anio_anterior"].map(formatear_guaranies)

        st.subheader(f"{tipo} de {nombre}")
        st.dataframe(tabla_mostrar, use_container_width=True)

        st.download_button(
            label=f"⬇️ Descargar {tipo.lower()} de {nombre}",
            data=generar_excel(tabla),
            file_name=f"{tipo.lower()}_{nombre.lower().replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with st.expander("📆 Comparativo Mensual", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            seccion_variacion("Ventas (mensual)", tabla_ventas_mensual[tabla_ventas_mensual["variacion_%"] > 0], "variacion_%", "Aumento")
            seccion_variacion("Margen (mensual)", tabla_margen_mensual[tabla_margen_mensual["variacion_%"] > 0], "variacion_%", "Aumento")
            seccion_variacion("Utilidad (mensual)", tabla_utilidad_mensual[tabla_utilidad_mensual["variacion_%"] > 0], "variacion_%", "Aumento")
        with col2:
            seccion_variacion("Ventas (mensual)", tabla_ventas_mensual[tabla_ventas_mensual["variacion_%"] < 0], "variacion_%", "Disminución")
            seccion_variacion("Margen (mensual)", tabla_margen_mensual[tabla_margen_mensual["variacion_%"] < 0], "variacion_%", "Disminución")
            seccion_variacion("Utilidad (mensual)", tabla_utilidad_mensual[tabla_utilidad_mensual["variacion_%"] < 0], "variacion_%", "Disminución")

    with st.expander("📅 Comparativo Anual", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            seccion_variacion("Ventas (anual)", tabla_ventas_anual[tabla_ventas_anual["variacion_%"] > 0], "variacion_%", "Aumento")
            seccion_variacion("Margen (anual)", tabla_margen_anual[tabla_margen_anual["variacion_%"] > 0], "variacion_%", "Aumento")
            seccion_variacion("Utilidad (anual)", tabla_utilidad_anual[tabla_utilidad_anual["variacion_%"] > 0], "variacion_%", "Aumento")
        with col2:
            seccion_variacion("Ventas (anual)", tabla_ventas_anual[tabla_ventas_anual["variacion_%"] < 0], "variacion_%", "Disminución")
            seccion_variacion("Margen (anual)", tabla_margen_anual[tabla_margen_anual["variacion_%"] < 0], "variacion_%", "Disminución")
            seccion_variacion("Utilidad (anual)", tabla_utilidad_anual[tabla_utilidad_anual["variacion_%"] < 0], "variacion_%", "Disminución")
