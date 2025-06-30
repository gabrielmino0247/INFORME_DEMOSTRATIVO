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

    # --- NUEVA TABLA: Categorías generales que han bajado respecto al año anterior ---
    st.subheader("Categorías generales que han bajado en ventas respecto al año anterior")
    # Filtrar las que bajaron
    categorias_bajaron = tabla_ventas_anual[tabla_ventas_anual["ventas_actual"] < tabla_ventas_anual["ventas_anio_anterior"]].copy()
    # Unir con ventas mes anterior
    ventas_mes_ant = tabla_ventas_mensual[["LOCAL", "SECTOR", "SUBSECTOR", "MARCA", "ventas_mes_anterior"]].copy()
    categorias_bajaron = categorias_bajaron.merge(ventas_mes_ant, on=["LOCAL", "SECTOR", "SUBSECTOR", "MARCA"], how="left")
    # Unir con margen actual y margen año anterior
    margen_actual = tabla_margen_anual[["LOCAL", "SECTOR", "SUBSECTOR", "MARCA", "margen_actual", "margen_anio_anterior"]].copy()
    categorias_bajaron = categorias_bajaron.merge(margen_actual, on=["LOCAL", "SECTOR", "SUBSECTOR", "MARCA"], how="left")
    # Unir con margen mes anterior
    margen_mes_ant = tabla_margen_mensual[["LOCAL", "SECTOR", "SUBSECTOR", "MARCA", "margen_anterior"]].copy()
    categorias_bajaron = categorias_bajaron.merge(margen_mes_ant, on=["LOCAL", "SECTOR", "SUBSECTOR", "MARCA"], how="left")
    # Seleccionar y renombrar columnas para mostrar
    cols = [
        "LOCAL", "SECTOR", "SUBSECTOR", "MARCA",
        "ventas_actual", "ventas_mes_anterior", "ventas_anio_anterior",
        "margen_actual", "margen_mes_anterior", "margen_anio_anterior"
    ]
    categorias_bajaron = categorias_bajaron.rename(columns={"margen_anterior": "margen_mes_anterior"})
    categorias_bajaron = categorias_bajaron[cols]
    # Formatear
    categorias_bajaron["ventas_actual"] = categorias_bajaron["ventas_actual"].map(formatear_guaranies)
    categorias_bajaron["ventas_mes_anterior"] = categorias_bajaron["ventas_mes_anterior"].map(formatear_guaranies)
    categorias_bajaron["ventas_anio_anterior"] = categorias_bajaron["ventas_anio_anterior"].map(formatear_guaranies)
    categorias_bajaron["margen_actual"] = categorias_bajaron["margen_actual"].map(formatear_porcentaje)
    categorias_bajaron["margen_mes_anterior"] = categorias_bajaron["margen_mes_anterior"].map(formatear_porcentaje)
    categorias_bajaron["margen_anio_anterior"] = categorias_bajaron["margen_anio_anterior"].map(formatear_porcentaje)
    st.dataframe(categorias_bajaron, use_container_width=True)
    st.download_button(
        label="⬇️ Descargar categorías que bajaron",
        data=generar_excel(categorias_bajaron, "Categorias Bajaron"),
        file_name="categorias_bajaron_ventas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
