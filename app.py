# Importaciones necesarias
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
from io import BytesIO

# ------------------- CONFIGURACIÓN INICIAL -------------------
st.set_page_config(
    page_title="Dashboard Farmacéutico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------- FUNCIONES DE CARGA DE DATOS -------------------
@st.cache_data
def load_data():
    """
    Carga los datos desde el archivo CSV y realiza transformaciones iniciales.
    Retorna:
        DataFrame: Datos farmacéuticos procesados
    """
    try:
        # Asegúrate de que la ruta 'data/pharma_data_altibajos.csv' sea correcta
        df = pd.read_csv("pharma_data_altibajos.csv", parse_dates=["Fecha"])
        
        # Validación básica de datos
        if df.empty:
            st.error("El archivo de datos está vacío.")
            return None
            
        # Convertir regiones a formato consistente (primera letra mayúscula)
        # Asumiendo que 'Región' contiene los nombres de las ciudades
        if 'Región' in df.columns:
            df['Región'] = df['Región'].str.title().str.strip()
            
        return df
        
    except FileNotFoundError:
        st.error("No se encontró el archivo de datos. Verifica la ruta: 'data/pharma_data_altibajos.csv'")
        return None
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
        return None

# Cargar datos
df = load_data()

# Verificar si los datos se cargaron correctamente
if df is None:
    st.stop()

# ------------------- CONFIGURACIÓN DE ESTILOS -------------------
# Paleta de colores farmacéutica
pharma_palette = ['#0077b6', '#90e0ef', '#caf0f8', '#f1faff', '#00b4d8', '#ade8f4', '#48cae4', '#a2d2ff']

# Configuración CSS personalizada
st.markdown("""
    <style>
    .css-18e3th9 { padding-top: 1rem; }
    .metric { border-left: 4px solid #0077b6; padding-left: 1rem; }
    .stAlert { border-left: 4px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# ------------------- INTERFAZ PRINCIPAL -------------------
st.title("💊 Dashboard Farmacéutico - Rendimiento de Ventas")

# ------------------- SIDEBAR - FILTROS -------------------
st.sidebar.header("Filtros")

# 1. Filtro por rango de fechas
min_date, max_date = df["Fecha"].min().date(), df["Fecha"].max().date()
date_range = st.sidebar.date_input(
    "Rango de Fechas",
    (min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Aplicar filtro de fechas
if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df[(df["Fecha"].dt.date >= start_date) & (df["Fecha"].dt.date <= end_date)].copy()
else:
    st.sidebar.warning("Por favor, selecciona un rango de fechas válido.")
    df_filtered = df.copy()

# 2. Filtros dinámicos por columnas clave
filters = {
    "Región": sorted(df_filtered["Región"].unique()),
    "Producto": sorted(df_filtered["Producto"].unique()),
    "Canal": sorted(df_filtered["Canal"].unique()),
    "Categoría": sorted(df_filtered["Categoría"].unique()),
    "Laboratorio": sorted(df_filtered["Laboratorio"].unique()),
    "Vendedor": sorted(df_filtered["Vendedor"].unique())
}

# Crear filtros en el sidebar
selected_filters = {}
for key in filters:
    selected = st.sidebar.multiselect(
        f"Filtrar por {key}",
        options=filters[key],
        default=filters[key],
        key=f"filter_{key}"
    )
    selected_filters[key] = selected

# Aplicar todos los filtros seleccionados
for key, values in selected_filters.items():
    if values:  # Solo filtrar si se seleccionaron valores
        df_filtered = df_filtered[df_filtered[key].isin(values)]

# Validar si hay datos después de filtrar
if df_filtered.empty:
    st.warning("⚠️ No hay datos disponibles para los filtros seleccionados. Ajusta tus selecciones.")
    st.stop()

# ------------------- KPIs PRINCIPALES -------------------
st.markdown("### 📈 Indicadores Clave")
col1, col2, col3, col4, col5 = st.columns(5)

# Calcular métricas
ventas_totales = df_filtered['Ventas'].sum()
unidades_totales = df_filtered['Unidades'].sum()
inventario_prom = df_filtered['Inventario'].mean()
precio_unitario = ventas_totales / unidades_totales if unidades_totales > 0 else 0
ventas_prom_vendedor = df_filtered.groupby('Vendedor')['Ventas'].sum().mean()

# Mostrar métricas
col1.metric("Total Ventas ($)", f"${ventas_totales:,.0f}", delta_color="off")
col2.metric("Unidades Vendidas", f"{unidades_totales:,.0f}", delta_color="off")
col3.metric("Inventario Promedio", f"{inventario_prom:,.0f}", delta_color="off")
col4.metric("Precio Promedio/Unidad", f"${precio_unitario:,.2f}", delta_color="off")
col5.metric("Ventas Promedio/Vendedor", f"${ventas_prom_vendedor:,.0f}", delta_color="off")

# ------------------- TABS PRINCIPALES -------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Análisis General", "Tendencias", "Distribución", "Ventas por Ciudad", "Datos y Descarga"
])

# ---------- TAB 1: ANÁLISIS GENERAL ----------
with tab1:
    st.markdown("### 📊 Ventas por Producto y Categoría")
    colA, colB = st.columns(2)

    with colA:
        st.markdown("##### Top 10 Productos por Ventas")
        top_productos = df_filtered.groupby("Producto", as_index=False)["Ventas"].sum().nlargest(10, "Ventas")
        fig_prod = px.bar(
            top_productos,
            x="Ventas",
            y="Producto",
            orientation="h",
            color="Ventas",
            color_continuous_scale="Tealgrn",
            labels={"Ventas": "Ventas ($)", "Producto": ""},
            height=500
        )
        fig_prod.update_layout(margin=dict(l=0, r=0, b=0, t=30))
        st.plotly_chart(fig_prod, use_container_width=True)

    with colB:
        st.markdown("##### Ventas por Categoría")
        ventas_cat = df_filtered.groupby("Categoría", as_index=False)["Ventas"].sum()
        fig_cat = px.bar(
            ventas_cat,
            x="Ventas",
            y="Categoría",
            orientation="h",
            color="Categoría",
            color_discrete_sequence=pharma_palette,
            labels={"Ventas": "Ventas ($)", "Categoría": ""},
            height=500
        )
        fig_cat.update_layout(margin=dict(l=0, r=0, b=0, t=30), showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)

# ---------- TAB 2: TENDENCIAS ----------
with tab2:
    st.markdown("### 📈 Tendencias de Ventas e Inventario")
    
    # Selector de período
    periodo = st.selectbox(
        "Periodo de Agregación",
        ["Diario", "Semanal", "Mensual", "Trimestral", "Anual"],
        key="period_selector"
    )
    
    # Mapeo de códigos de resample
    period_code = {
        "Diario": "D",
        "Semanal": "W-MON",
        "Mensual": "M",
        "Trimestral": "Q",
        "Anual": "Y"
    }[periodo]
    
    # Agregar datos por período
    df_trend = df_filtered.set_index("Fecha").resample(period_code).agg({
        "Ventas": "sum",
        "Inventario": "mean",
        "Unidades": "sum"
    }).reset_index()
    
    # Gráfico de ventas
    fig_ventas = px.line(
        df_trend,
        x="Fecha",
        y="Ventas",
        markers=True,
        title=f"Ventas ({periodo})",
        color_discrete_sequence=["#0077b6"],
        labels={"Ventas": "Ventas ($)", "Fecha": ""}
    )
    fig_ventas.update_layout(hovermode="x unified")
    st.plotly_chart(fig_ventas, use_container_width=True)
    
    # Gráfico de inventario
    fig_inv = px.line(
        df_trend,
        x="Fecha",
        y="Inventario",
        markers=True,
        title=f"Inventario Promedio ({periodo})",
        color_discrete_sequence=["#90e0ef"],
        labels={"Inventario": "Unidades", "Fecha": ""}
    )
    fig_inv.update_layout(hovermode="x unified")
    st.plotly_chart(fig_inv, use_container_width=True)

# ---------- TAB 3: DISTRIBUCIÓN ----------
with tab3:
    st.markdown("### 📦 Distribución de Ventas")
    colC, colD = st.columns(2)

    with colC:
        st.markdown("##### Ventas por Canal de Distribución")
        df_canal = df_filtered.groupby("Canal", as_index=False)["Ventas"].sum()
        fig_canal = px.pie(
            df_canal,
            names="Canal",
            values="Ventas",
            title="",
            color_discrete_sequence=pharma_palette,
            hole=0.3
        )
        fig_canal.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate="%{label}: %{value:$,.0f} (%{percent})"
        )
        fig_canal.update_layout(showlegend=False)
        st.plotly_chart(fig_canal, use_container_width=True)

    with colD:
        st.markdown("##### Top 10 Vendedores")
        top_vendedores = df_filtered.groupby("Vendedor", as_index=False)["Ventas"].sum().nlargest(10, "Ventas")
        fig_vend = px.bar(
            top_vendedores,
            x="Ventas",
            y="Vendedor",
            orientation="h",
            color="Ventas",
            color_continuous_scale="Plasma",
            labels={"Ventas": "Ventas ($)", "Vendedor": ""},
            height=500
        )
        fig_vend.update_layout(margin=dict(l=0, r=0, b=0, t=30))
        st.plotly_chart(fig_vend, use_container_width=True)

# ---------- TAB 4: VENTAS POR CIUDAD ----------
with tab4:
    st.markdown("### 📊 Ventas por Ciudad")
    
    # Preparar datos de ventas por ciudad (Región)
    ventas_ciudad = df_filtered.groupby("Región", as_index=False).agg({
        "Ventas": "sum",
        "Unidades": "sum",
        "Producto": "nunique"
    }).rename(columns={"Producto": "Productos_Diferentes"})

    # Ordenar las ciudades por ventas de mayor a menor para el gráfico
    ventas_ciudad = ventas_ciudad.sort_values("Ventas", ascending=True)

    # Crear gráfico de barras de ventas por ciudad
    fig_city_sales = px.bar(
        ventas_ciudad,
        x="Ventas",
        y="Región",
        orientation="h",
        color="Ventas",
        color_continuous_scale="Sunsetdark", # Escala de colores diferente para variar
        labels={
            "Ventas": "Ventas ($)",
            "Región": "Ciudad",
            "Unidades": "Unidades Vendidas",
            "Productos_Diferentes": "Productos Diferentes"
        },
        hover_data=["Unidades", "Productos_Diferentes"],
        title="Total de Ventas por Ciudad",
        height=500
    )
    
    fig_city_sales.update_layout(margin=dict(l=0, r=0, b=0, t=30))
    st.plotly_chart(fig_city_sales, use_container_width=True)
    
    # Mostrar tabla de datos debajo del gráfico
    st.markdown("#### Datos por Ciudad")
    st.dataframe(
        ventas_ciudad.sort_values("Ventas", ascending=False), # Ordenar descendente para la tabla
        column_config={
            "Ventas": st.column_config.NumberColumn("Ventas ($)", format="$%,.0f"),
            "Unidades": st.column_config.NumberColumn("Unidades", format="%,.0f"),
            "Productos_Diferentes": st.column_config.NumberColumn("Productos Únicos")
        },
        use_container_width=True,
        hide_index=True
    )

# ---------- TAB 5: DATOS Y DESCARGA ----------
with tab5:
    st.markdown("### 📄 Datos Filtrados")
    
    # Mostrar estadísticas resumidas
    st.markdown(f"**Total de registros:** {len(df_filtered):,}")
    st.markdown(f"**Período:** {df_filtered['Fecha'].min().strftime('%d/%m/%Y')} - {df_filtered['Fecha'].max().strftime('%d/%m/%Y')}")
    
    # Mostrar dataframe con opciones de visualización
    st.dataframe(
        df_filtered.sort_values("Fecha", ascending=False),
        use_container_width=True,
        height=500,
        column_config={
            "Ventas": st.column_config.NumberColumn(format="$%,.0f"),
            "Unidades": st.column_config.NumberColumn(format="%,.0f"),
            "Inventario": st.column_config.NumberColumn(format="%,.0f")
        },
        hide_index=True
    )
    
    # Opciones de descarga
    st.markdown("### 📥 Exportar Datos")
    col_export1, col_export2 = st.columns(2)
    
    with col_export1:
        # Descargar como CSV
        csv = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📊 Descargar como CSV",
            data=csv,
            file_name=f"datos_farmaceuticos_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            help="Descargar los datos filtrados en formato CSV"
        )
    
    with col_export2:
        # Descargar como Excel - VERSIÓN CORREGIDA
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='DatosFarmaceuticos')
        excel_data = output.getvalue()
        
        st.download_button(
            "📑 Descargar como Excel",
            data=excel_data,
            file_name=f"datos_farmaceuticos_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Descargar los datos filtrados en formato Excel"
        )

# ------------------- FOOTER -------------------
st.markdown("---")
st.caption("""
    © 2025 Empresa Farmacéutica - Dashboard profesional por Juan Hernández | Streamlit & Plotly
    Última actualización: {}
    """.format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))