#Creamos el archivo de la APP del dashboard de GAC
#####################################################
#Importamos librerias
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
#####################################################
#Configuración general de la página (debe ir antes de cualquier otro elemento)
st.set_page_config(page_title="GAC | Dashboard Comercial", page_icon="🚗", layout="wide")

#Formato visual inspirado en el sitio de GAC:
#fondo negro, texto blanco, acento rojo y tipografía sans-serif en negritas y mayúsculas
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800&display=swap');
h1, h2, h3, p, label {font-family: 'Montserrat', sans-serif;}
h1, h2, h3 {text-transform: uppercase; font-weight: 800; letter-spacing: 1px;}
[data-testid="stSidebar"] {background-color: #000000; border-right: 3px solid #E60000;}
[data-testid="stMetric"] {background-color: #141414; border-left: 4px solid #E60000;
                          padding: 10px 15px; border-radius: 4px;}
[data-testid="stMetricValue"] {color: #E60000; font-weight: 800;}
</style>
""", unsafe_allow_html=True)

#Colores de la marca
ROJO = "#E60000"
PALETA = ["#E60000", "#FFFFFF", "#8C8C8C", "#B30000", "#4D4D4D", "#D9D9D9"]
MESES = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
         7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
ETAPAS = ["Leads generados", "Leads efectivos", "Cita programada", "Cita efectiva",
          "Prueba de manejo", "Solicitud de crédito generada",
          "Solicitud de crédito aprobada", "Formalizado", "Ventas"]
######################################################
#Definimos la instancia
@st.cache_data
######################################################
#Creamos la función de carga de datos (bases limpias exportadas desde el notebook)
def load_data():
    marketing = pd.read_csv("gac_marketing.csv")
    citas = pd.read_csv("gac_citas_digital.csv")
    leads = pd.read_csv("gac_leads_canal.csv")
    funnel = pd.read_csv("gac_funnel.csv")
    bitacora = pd.read_csv("gac_bitacora.csv")
    tops = pd.read_csv("gac_tops_mkt.csv")
    tdh = pd.read_csv("gac_tops_tdh.csv")
    canales = pd.read_csv("gac_principales_canales.csv")
    sdc = pd.read_csv("gac_sdc.csv")
    resumen = pd.read_csv("gac_resumen.csv")
    return marketing, citas, leads, funnel, bitacora, tops, tdh, canales, sdc, resumen
###############################################################################
#Cargo los datos obtenidos de la función "load_data"
marketing, citas, leads, funnel, bitacora, tops, tdh, canales, sdc, resumen = load_data()
###############################################################################
#FUNCIONES DE APOYO
#Clasifica una variable numérica en intervalos con la regla de Sturges
#(si se indica k, se usa ese número de intervalos)
def clasificar(serie, k=None, sufijo=""):
    serie = serie.dropna()
    if k is None:
        k = round(1 + 3.322 * np.log10(serie.count()))
    limites = np.linspace(serie.min(), serie.max(), k + 1)
    etiquetas = [f"{limites[j]:.0f}-{limites[j+1]:.0f}{sufijo}" for j in range(k)]
    return pd.cut(serie, bins=limites, labels=etiquetas, include_lowest=True)

#Obtiene la tabla de frecuencias de una variable categórica respetando el orden de los intervalos
def frecuencias(categoria):
    tabla = categoria.value_counts().sort_index().reset_index()
    tabla.columns = ['categorias', 'frecuencia']
    tabla['categorias'] = tabla['categorias'].astype(str)
    return tabla

#Aplica el mismo estilo GAC a todas las gráficas
def estilo(figura, alto=350, escala=False):
    figura.update_layout(template="plotly_dark", height=alto,
                         paper_bgcolor="#000000", plot_bgcolor="#000000",
                         font=dict(family="Montserrat, sans-serif", color="#FFFFFF"),
                         margin=dict(l=10, r=10, t=50, b=10),
                         coloraxis_showscale=escala)
    figura.update_xaxes(automargin=True)
    figura.update_yaxes(automargin=True)
    return figura
###############################################################################
#EXTRACCIÓN DE CARACTERÍSTICAS (las mismas que se trabajaron en el notebook)
#Base 1: Marketing
marketing = marketing.dropna(subset=['Leads total'])

#Base 2: Citas Digital
citas['Fecha_dt'] = pd.to_datetime(citas['Fecha'].astype(str).str[:7], format="%Y-%m", errors="coerce")
citas['Periodo'] = citas['Fecha_dt'].dt.strftime("%Y-%m")
citas['Año'] = citas['Fecha_dt'].dt.year
citas['Mes_num'] = citas['Fecha_dt'].dt.month
citas['PDM_categoria'] = citas['PDM'].astype(str).str.upper().map({
    "TRUE": "Realizó la prueba", "FALSE": "No realizó la prueba"})
citas['Potencial_num'] = pd.to_numeric(citas['Potencial de compra'], errors="coerce")
citas['Rango_Potencial'] = clasificar(citas['Potencial_num'], k=10, sufijo="%")

#Base 4: Funnel (eliminamos registros repetidos, como en el notebook)
funnel = funnel.drop_duplicates(subset=["Mes", "Canal", "Item", "Real"])

#Base 5: Bitácora de piso (leads por asesor y su nivel de volumen)
bitacora['Asesor'] = bitacora['Asesor'].str.strip().str.title()
leads_asesor = bitacora['Asesor'].value_counts().reset_index()
leads_asesor.columns = ['Asesor', 'Leads']
leads_asesor = leads_asesor[leads_asesor['Asesor'] != "Sin Dato"]
leads_asesor['Volumen_Leads'] = clasificar(leads_asesor['Leads'])

#Base 6 y 7: TOPS MKT y TOPS TDH
tops['Categoria_Afluencia'] = clasificar(tops['Afluencia_RealPisos'])
tdh['Categoria_Plantilla'] = clasificar(tdh['Plantilla'])

#Base 8, 9 y 10: Principales canales, SDC y Resumen
canales['Categoria_Leads'] = clasificar(canales['Leads'])
sdc['Categoria_Generadas'] = clasificar(sdc['Generadas'])
resumen['Categoria_Leads'] = clasificar(resumen['Leads'])
###############################################################################
# Encabezado reutilizable con logo en la misma carpeta que app.py.
from pathlib import Path

def encabezado_con_logo(titulo, pregunta=None):
    col_titulo, col_logo = st.columns([8, 1])
    with col_titulo:
        st.title(titulo)
        if pregunta:
            st.caption(pregunta)
    with col_logo:
        ruta_logo = Path(__file__).resolve().parent / "gac_logo.jpeg"
        if ruta_logo.is_file():
            st.image(str(ruta_logo), width=90)
        else:
            st.markdown("**GAC**")

# Navegación: una actividad por página
pagina = st.sidebar.radio(
    "Actividad",
    ["Actividad 1 · Análisis univariado", "Actividad 2 · Regresión lineal"],
    key="pagina_actividad"
)

if pagina == "Actividad 1 · Análisis univariado":
    #CREACIÓN DEL DASHBOARD
    #Generamos los encabezados para la barra lateral (sidebar)
    st.sidebar.title("GAC")
    st.sidebar.caption("DASHBOARD COMERCIAL · 2024 - 2026")
    #Widget 1: Selectbox
    #Menu desplegable de opciones de las páginas
    View = st.sidebar.selectbox(label="Tipo de Análisis", options=["Captación de clientes",
                                                                   "Conversión",
                                                                   "Equipo comercial",
                                                                   "Operación y crédito"])
    st.sidebar.divider()
    ###############################################################################
    # CONTENIDO DE LA VISTA 1
    if View == "Captación de clientes":
        #Widgets propios de la vista
        Tipo_Canal = st.sidebar.radio("Gráfica de leads por canal", ["Barras", "Dona"])
        Canal_Sel = st.sidebar.selectbox("Canal (Principales Canales)",
                                         ["Todos"] + sorted(canales['Canal'].unique()))

        #Generamos los encabezados para el dashboard
        encabezado_con_logo('Captación de clientes', '¿Cuándo y por qué canal llegan los prospectos a GAC?')

        #Indicadores clave (KPIs)
        Leads_Canal = leads.groupby('Canal')['Leads'].sum().sort_values(ascending=False).reset_index()
        Mes_Pico = marketing.loc[marketing['Leads total'].idxmax()]
        K1, K2, K3, K4 = st.columns(4)
        K1.metric("Leads totales", f"{Leads_Canal['Leads'].sum():,.0f}")
        K2.metric("Canal líder", Leads_Canal['Canal'].iloc[0])
        K3.metric("Mes con más leads", Mes_Pico['Mes'])
        K4.metric("Promedio mensual", f"{marketing['Leads total'].mean():,.0f}")

        # Fila 1
    # GRAPH 1: Leads totales por mes (Base 1: Marketing)

        figure1 = px.line(
            data_frame=marketing,
            x='Mes',
            y='Leads total',
            text='Leads total',
            markers=True,
            title='Leads totales por mes'
        )

        figure1.update_traces(
            line=dict(color=ROJO, width=3),
            marker=dict(size=8),
            textposition="top center"
        )

        figure1.update_xaxes(tickangle=45)

        figure1.update_yaxes(
        range=[0, marketing['Leads total'].max() * 1.15])

        st.plotly_chart(estilo(figure1))


        # Fila 2
        Contenedor_A, Contenedor_B = st.columns(2)

        with Contenedor_A:
            # GRAPH 2: Total de leads por canal
            if Tipo_Canal == "Barras":
                figure2 = px.bar(
                    data_frame=Leads_Canal,
                    x='Canal',
                    y='Leads',
                    text='Leads',
                    title='Total de leads por canal',
                    color='Leads',
                    color_continuous_scale='Reds'
                )
            else:
                figure2 = px.pie(
                    data_frame=Leads_Canal,
                    names='Canal',
                    values='Leads',
                    hole=0.4,
                    title='Total de leads por canal',
                    color_discrete_sequence=PALETA
                )

            st.plotly_chart(estilo(figure2))


        with Contenedor_B:
            # GRAPH 3: Distribución de leads por intervalos
            Datos_Canal = canales if Canal_Sel == "Todos" else canales[canales['Canal'] == Canal_Sel]

            Tabla_frecuencias = frecuencias(Datos_Canal['Categoria_Leads'])

            figure3 = px.bar(
                data_frame=Tabla_frecuencias,
                x='frecuencia',
                y='categorias',
                orientation='h',
                text='frecuencia',
                color='frecuencia',
                color_continuous_scale='Reds',
                title=f'Meses por intervalo de leads · Canal: {Canal_Sel}'
            )

            st.plotly_chart(estilo(figure3))


        # Fila 3
        figure5 = px.box(
            data_frame=leads,
            x='Canal',
            y='Leads',
            color='Canal',
            points='all',
            title='Variación mensual de leads por canal',
            color_discrete_sequence=PALETA
        )

        st.plotly_chart(estilo(figure5, alto=400))
    ###############################################################################
    # CONTENIDO DE LA VISTA 2
    elif View == "Conversión":
        #Widget propio de la vista
        Canal_Funnel = st.sidebar.selectbox("Canal del funnel",
                                            ["Todos"] + sorted(funnel['Canal'].dropna().unique()))
        Datos_Funnel = funnel if Canal_Funnel == "Todos" else funnel[funnel['Canal'] == Canal_Funnel]

        #Tabla del embudo: suma de "Real" por etapa y porcentajes de conversión
        Tabla_Funnel = Datos_Funnel.groupby('Item')['Real'].sum().reindex(ETAPAS).dropna().reset_index()
        Tabla_Funnel.columns = ['Etapa', 'Total']
        Tabla_Funnel['% vs Leads generados'] = (Tabla_Funnel['Total'] / Tabla_Funnel['Total'].iloc[0] * 100).round(1)
        Tabla_Funnel['% vs etapa anterior'] = (Tabla_Funnel['Total'] / Tabla_Funnel['Total'].shift(1) * 100).round(1)

        encabezado_con_logo('Conversión', '¿En qué etapa se pierden los clientes y qué tan cerca están de comprar?')

        #Indicadores clave (KPIs)
        Totales = Datos_Funnel.groupby('Item')['Real'].sum()
        Leads_Gen = Totales.get("Leads generados", 0)
        Ventas = Totales.get("Ventas", 0)
        Conversion = Ventas / Leads_Gen * 100 if Leads_Gen > 0 else 0
        Pct_PDM = (citas['PDM_categoria'] == "Realizó la prueba").mean() * 100
        K1, K2, K3, K4 = st.columns(4)
        K1.metric("Leads generados", f"{Leads_Gen:,.0f}")
        K2.metric("Ventas", f"{Ventas:,.0f}")
        K3.metric("Conversión lead → venta", f"{Conversion:.1f}%")
        K4.metric("Citas con prueba de manejo", f"{Pct_PDM:.1f}%")

        # Fila 1
        Contenedor_A, Contenedor_B = st.columns(2)
        with Contenedor_A:
            #GRAPH 1: Embudo de conversión (Base 4: Funnel)
            figure1 = px.funnel(data_frame=Tabla_Funnel, x='Total', y='Etapa',
                                title=f'Embudo de ventas · Canal: {Canal_Funnel}',
                                color_discrete_sequence=[ROJO])
            st.plotly_chart(estilo(figure1, alto=420))

        with Contenedor_B:
            #GRAPH 2: Pruebas de manejo (Base 2: Citas Digital)
            Tabla_frecuencias = citas['PDM_categoria'].value_counts().reset_index()
            Tabla_frecuencias.columns = ['categorias', 'frecuencia']
            figure2 = px.pie(data_frame=Tabla_frecuencias, names='categorias', values='frecuencia',
                             hole=0.4, title='Distribución de pruebas de manejo',
                             color_discrete_sequence=PALETA)
            st.plotly_chart(estilo(figure2, alto=420))

        # Fila 2
        Contenedor_C, Contenedor_D = st.columns(2)
        with Contenedor_C:
            #GRAPH 3: Estatus de lead (Base 2: Citas Digital)
            Tabla_frecuencias = citas['Estatus de Lead'].value_counts().reset_index()
            Tabla_frecuencias.columns = ['categorias', 'frecuencia']
            figure3 = px.bar(data_frame=Tabla_frecuencias, x='categorias', y='frecuencia',
                             text='frecuencia', title='Distribución del estatus de lead',
                             color='frecuencia', color_continuous_scale='Reds')
            st.plotly_chart(estilo(figure3))

        with Contenedor_D:
            #GRAPH 4: Potencial de compra por rangos (Base 2: Citas Digital)
            Tabla_frecuencias = frecuencias(citas['Rango_Potencial'])
            figure4 = px.bar(data_frame=Tabla_frecuencias, x='categorias', y='frecuencia',
                             text='frecuencia', title='Potencial de compra por rangos',
                             color='frecuencia', color_continuous_scale='Reds')
            figure4.update_xaxes(tickangle=45)
            st.plotly_chart(estilo(figure4))

        # Fila 3 (widget adicional: TABLA)
        st.subheader("Conversión por etapa del funnel")
        st.dataframe(Tabla_Funnel, hide_index=True)
    ###############################################################################
    # CONTENIDO DE LA VISTA 3
    elif View == "Equipo comercial":
        #Widget propio de la vista (widget adicional: SLIDER)
        Top_N = st.sidebar.slider("Número de asesores a mostrar", min_value=3, max_value=15, value=8)

        encabezado_con_logo('Equipo comercial', '¿Cómo se distribuye la carga de trabajo entre los asesores?')

        #Tablas de asesores (se excluyen los registros sin asesor identificado)
        Citas_Asesor = citas['Asesor Asignado'].value_counts().reset_index()
        Citas_Asesor.columns = ['Asesor', 'Citas']
        Citas_Asesor = Citas_Asesor[Citas_Asesor['Asesor'] != "Sin registro"]

        #Indicadores clave (KPIs)
        K1, K2, K3, K4 = st.columns(4)
        K1.metric("Asesores con citas digitales", Citas_Asesor['Asesor'].nunique())
        K2.metric("Más citas digitales", Citas_Asesor['Asesor'].iloc[0])
        K3.metric("Más leads en piso", leads_asesor['Asesor'].iloc[0])
        K4.metric("Plantilla promedio", f"{tdh['Plantilla'].mean():.0f}")

        # Fila 1
        Contenedor_A, Contenedor_B = st.columns(2)
        with Contenedor_A:
            #GRAPH 1: Asesores con más citas digitales (Base 2: Citas Digital)
            figure1 = px.bar(data_frame=Citas_Asesor.head(Top_N), x='Citas', y='Asesor',
                             orientation='h', text='Citas', color='Citas',
                             color_continuous_scale='Reds',
                             title=f'Top {Top_N} asesores · Citas digitales')
            figure1.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(estilo(figure1))

        with Contenedor_B:
            #GRAPH 2: Leads atendidos por asesor (Base 5: Bitácora de piso)
            figure2 = px.bar(data_frame=leads_asesor.head(Top_N), x='Leads', y='Asesor',
                             orientation='h', text='Leads', color='Leads',
                             color_continuous_scale='Reds',
                             title=f'Top {Top_N} asesores · Leads atendidos en piso')
            figure2.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(estilo(figure2))

        # Fila 2
        Contenedor_C, Contenedor_D = st.columns(2)
        with Contenedor_C:
            #GRAPH 3: Asesores por volumen de leads (Base 5: Bitácora de piso)
            Tabla_frecuencias = frecuencias(leads_asesor['Volumen_Leads'])
            figure3 = px.bar(data_frame=Tabla_frecuencias, x='categorias', y='frecuencia',
                             text='frecuencia', color='frecuencia', color_continuous_scale='Reds',
                             title='Asesores agrupados por volumen de leads')
            figure3.update_layout(xaxis_title='Leads atendidos', yaxis_title='Número de asesores')
            st.plotly_chart(estilo(figure3))

        with Contenedor_D:
            #GRAPH 4: Meses por tamaño de plantilla (Base 7: TOPS TDH)
            Tabla_frecuencias = frecuencias(tdh['Categoria_Plantilla'])
            figure4 = px.bar(data_frame=Tabla_frecuencias, x='categorias', y='frecuencia',
                             text='frecuencia', color='frecuencia', color_continuous_scale='Reds',
                             title='Meses agrupados por tamaño de plantilla')
            figure4.update_layout(xaxis_title='Personas en plantilla', yaxis_title='Número de meses')
            st.plotly_chart(estilo(figure4))
    ###############################################################################
    # CONTENIDO DE LA VISTA 4
    elif View == "Operación y crédito":
        #Widget propio de la vista (widget adicional: MULTISELECT)
        Años = sorted(citas['Año'].dropna().astype(int).unique())
        Años_Sel = st.sidebar.multiselect("Año de las citas digitales", Años, default=Años)
        if len(Años_Sel) == 0:
            st.warning("Selecciona al menos un año en la barra lateral.")
            st.stop()
        Datos_Citas = citas[citas['Año'].isin(Años_Sel)]

        encabezado_con_logo('Operación y crédito', '¿En qué meses hay más actividad y cómo se comporta el crédito?')

        #Indicadores clave (KPIs)
        Citas_Mes = Datos_Citas['Periodo'].value_counts().sort_index().reset_index()
        Citas_Mes.columns = ['Periodo', 'Citas']
        Tasa_Aprobacion = sdc['Aprobadas'].sum() / sdc['Generadas'].sum() * 100
        K1, K2, K3, K4 = st.columns(4)
        K1.metric("Citas digitales", f"{len(Datos_Citas):,}")
        K2.metric("Mes con más citas", Citas_Mes.loc[Citas_Mes['Citas'].idxmax(), 'Periodo'])
        K3.metric("Solicitudes de crédito", f"{sdc['Generadas'].sum():,.0f}")
        K4.metric("Tasa de aprobación", f"{Tasa_Aprobacion:.1f}%")

        # Fila 1
        Contenedor_A, Contenedor_B = st.columns(2)
        with Contenedor_A:
            #GRAPH 1: Registros de citas digitales por mes (Base 2: Citas Digital)
            figure1 = px.line(
                data_frame=Citas_Mes,
                x='Periodo',
                y='Citas',
                markers=True,
                text='Citas',
                title='Citas digitales por mes')
            figure1.update_traces(
                line=dict(color=ROJO, width=3),
                marker=dict(size=8),
                textposition="top center")
            figure1.update_xaxes(tickangle=45)
            st.plotly_chart(estilo(figure1))


        with Contenedor_B:
            #GRAPH 2 (widget adicional: HEATMAP): citas por mes y año
            Tabla_Calor = Datos_Citas.pivot_table(index='Año', columns='Mes_num', values='Periodo',
                                                  aggfunc='count', fill_value=0)
            Tabla_Calor = Tabla_Calor.rename(columns=MESES)
            Tabla_Calor.index = Tabla_Calor.index.astype(int).astype(str)
            figure2 = px.imshow(Tabla_Calor, text_auto=True, aspect='auto',
                                color_continuous_scale='Reds', title='Mapa de calor de citas',
                                labels=dict(x='Mes', y='Año', color='Citas'))
            st.plotly_chart(estilo(figure2, escala=True))

        # Fila 2
        Contenedor_C, Contenedor_D = st.columns(2)
        with Contenedor_C:
            #GRAPH 3: Meses por nivel de afluencia a piso (Base 6: TOPS MKT)
            Tabla_frecuencias = frecuencias(tops['Categoria_Afluencia'])
            figure3 = px.bar(data_frame=Tabla_frecuencias, x='categorias', y='frecuencia',
                             text='frecuencia', color='frecuencia', color_continuous_scale='Reds',
                             title='Meses agrupados por nivel de asistencia a piso')
            figure3.update_layout(xaxis_title='Visitas a piso', yaxis_title='Número de meses')
            st.plotly_chart(estilo(figure3))

        with Contenedor_D:
            #GRAPH 4: Distribución de solicitudes de crédito generadas (Base 9: SDC)
            Tabla_frecuencias = frecuencias(sdc['Categoria_Generadas'])
            figure4 = px.bar(data_frame=Tabla_frecuencias, x='categorias', y='frecuencia',
                             text='frecuencia', color='frecuencia', color_continuous_scale='Reds',
                             title='Distribución de solicitudes de crédito generadas')
            figure4.update_layout(xaxis_title='Solicitudes por mes', yaxis_title='Número de meses')
            st.plotly_chart(estilo(figure4))

        # Fila 3 (widget adicional: TABLA con botón de descarga)
        st.subheader("Detalle mensual de solicitudes de crédito")
        Tabla_SDC = sdc.drop(columns=['Categoria_Generadas'])
        st.dataframe(Tabla_SDC, hide_index=True)
        st.download_button("⬇ Descargar tabla (CSV)", data=Tabla_SDC.to_csv(index=False).encode("utf-8"),
                           file_name="solicitudes_credito_gac.csv", mime="text/csv")
    ###############################################################################
    st.sidebar.divider()
    st.stop()

# ACTIVIDAD 2: REGRESIÓN LINEAL
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import plotly.graph_objects as go

encabezado_con_logo("Actividad 2 · Regresión lineal")
base_reg = st.sidebar.selectbox("Base", ["Resumen", "Principales Canales"], key="reg_base")
nombres = {
    "PDM": "Pruebas de manejo",
    "Efectivos": "Leads efectivos",
    "Leads": "Leads generados",
    "SDC": "Solicitudes de crédito",
    "Autorizadas": "Solicitudes autorizadas",
    "Ventas Real": "Ventas reales",
    "Ventas": "Ventas"
}

meses_reg = dict(zip(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio",
     "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    range(1, 13)
))

def numero_reg(serie):
    return pd.to_numeric(
        serie.astype("string").str.replace(",", "", regex=False).str.strip()
        .replace({"": pd.NA, "-": pd.NA}), errors="coerce"
    ).astype("float64")

if base_reg == "Resumen":
    d = resumen.copy()
    y_col = "Ventas Real"

    variables_disponibles = [
        "PDM",
        "Efectivos",
        "Leads",
        "SDC",
        "Autorizadas"
    ]

    validacion = ["Ventas Real"] + variables_disponibles
    requeridas = ["Año", "Mes"] + validacion
else:
    d = canales.copy()
    y_col = "Ventas"
    validacion = ["Ventas", "Leads"]
    requeridas = ["Mes", "Canal"] + validacion

d.columns = d.columns.astype(str).str.strip()
faltantes = [c for c in requeridas if c not in d.columns]
if faltantes:
    st.error(f"Faltan columnas: {', '.join(faltantes)}. Ejecuta la exportación de CSV y reinicia la app.")
    st.stop()

if base_reg == "Resumen":
    d["Periodo"] = pd.to_datetime(pd.DataFrame({
        "year": pd.to_numeric(d["Año"], errors="coerce"),
        "month": d["Mes"].astype("string").str.strip().str.lower().map(meses_reg),
        "day": 1
    }), errors="coerce")
    tipo = st.sidebar.radio("Modelo", ["Regresión simple", "Regresión múltiple"], key="reg_tipo")
    if tipo == "Regresión simple":
        xs = [
            st.sidebar.selectbox(
                "Variable explicativa",
                variables_disponibles,
                format_func=lambda c: nombres[c],
                key="reg_simple_x"
            )
        ]

    else:
        xs = st.sidebar.multiselect(
            "Variables explicativas",
            variables_disponibles,
            default=["PDM", "Efectivos"],
            format_func=lambda c: nombres[c],
            key="reg_multiple_x"
        )

        if len(xs) < 2:
            st.info(
                "Selecciona al menos dos variables "
                "para la regresión múltiple."
            )
            st.stop()

    pregunta = "¿Cómo se relacionan " + ", ".join(nombres[c].lower() for c in xs) + " con las ventas reales mensuales?"
else:
    d["Canal"] = d["Canal"].astype("string").str.strip()
    elegido = st.sidebar.selectbox("Canal", sorted(d["Canal"].dropna().unique()), key="reg_canal")
    d = d.loc[d["Canal"] == elegido].copy()
    partes = d["Mes"].astype("string").str.strip().str.lower().str.extract(
        r"^([a-záéíóú]+)\s*,\s*(\d{2}|\d{4})$"
    )
    anio = pd.to_numeric(partes[1], errors="coerce")
    anio = anio.where(anio >= 100, anio + 2000)
    d["Periodo"] = pd.to_datetime(pd.DataFrame({
        "year": anio, "month": partes[0].map(meses_reg), "day": 1
    }), errors="coerce")
    tipo = "Regresión simple"
    xs = ["Leads"]
    pregunta = f"¿Cómo se relacionan los leads generados con las ventas mensuales del canal {elegido}?"

st.write("**" + pregunta + "**")

# NOTAS PARA EL EQUIPO (no aparecen en la página):
# Corte elegido: febrero de 2024 a junio de 2026.
# Resumen: 23 meses de entrenamiento y 6 de evaluación.
# Julio de 2026 está en la fuente; se excluye por el corte elegido,
# sin afirmar que sus cifras sean incompletas.
# Para comparar variables en Resumen usamos los mismos registros completos.
# No se imputan ventas faltantes ni se eliminan extremos válidos.
# Las asociaciones son contemporáneas, no causales ni pronósticos futuros.
# Los selectores permiten una exploración; confirmar con otro periodo independiente.

for c in validacion:
    d[c] = numero_reg(d[c])
    invalido = d[c].lt(0) | d[c].mod(1).ne(0)
    d.loc[invalido, c] = np.nan

if d["Periodo"].isna().any():
    st.warning("Hay fechas que no pudieron interpretarse; esos registros se excluyen.")

d = d.loc[d["Periodo"].notna() & d["Periodo"].le(pd.Timestamp("2026-06-01"))].copy()
excluidos = int(d[validacion].isna().any(axis=1).sum())
d = d.dropna(subset=validacion).sort_values("Periodo")
if d["Periodo"].duplicated().any():
    st.error("Hay meses duplicados en esta selección. Revisa la base antes de modelar.")
    st.stop()
train = d.loc[d["Periodo"] < pd.Timestamp("2026-01-01")].copy()
test = d.loc[d["Periodo"] >= pd.Timestamp("2026-01-01")].copy()
if len(train) < 8 or len(test) < 3:
    st.warning("No hay suficientes meses completos: se necesitan 8 de entrenamiento y 3 de evaluación.")
    st.stop()

xt = train[xs].to_numpy(dtype=np.float64)
xe = test[xs].to_numpy(dtype=np.float64)
yt = train[y_col].to_numpy(dtype=np.float64)
ye = test[y_col].to_numpy(dtype=np.float64)
matriz = np.column_stack([np.ones(len(xt), dtype=np.float64), xt]).astype(np.float64)
if np.linalg.matrix_rank(matriz) < len(xs) + 1:
    st.warning("Las explicativas son constantes o dependen exactamente entre sí. Cambia la selección.")
    st.stop()
modelo = LinearRegression().fit(xt, yt)

# Predicciones con datos de entrenamiento y evaluación
pt = modelo.predict(xt)
pe = modelo.predict(xe)

# Métricas de evaluación
mae = mean_absolute_error(ye, pe)
rmse = np.sqrt(mean_squared_error(ye, pe))

# R² del modelo con datos históricos
r2_train = r2_score(yt, pt) if np.ptp(yt) > 0 else np.nan

# R² del modelo con datos de evaluación
r2 = r2_score(ye, pe) if np.ptp(ye) > 0 else np.nan

col_mae, col_rmse, col_r2_train, col_r2_eval = st.columns(4)

col_mae.metric(
    "Error promedio · MAE",
    f"{mae:.2f} ventas",
    help="Error absoluto promedio en los meses de evaluación. Menor es mejor."
)

col_rmse.metric(
    "RMSE",
    f"{rmse:.2f} ventas",
    help="Penaliza más los errores grandes. Menor es mejor."
)

col_r2_train.metric(
    "R² · Entrenamiento",
    f"{r2_train:.3f}" if np.isfinite(r2_train) else "No definido",
    help="Mide el ajuste del modelo con los datos históricos utilizados para entrenarlo."
)

col_r2_eval.metric(
    "R² · Evaluación",
    f"{r2:.3f}" if np.isfinite(r2) else "No definido",
    help="Mide el desempeño del modelo con datos no utilizados durante el entrenamiento. Puede ser negativo."
)



st.subheader(tipo)

st.markdown(
    "**Grises:** datos reales de febrero de 2024 a diciembre de 2025, "
    "usados para crear el modelo.  \n"
    "**Rojos:** datos reales de enero a junio de 2026, "
    "usados para comprobar sus estimaciones."
)
if len(xs) == 1:
    st.markdown(
        "**Cruces verdes:** ventas calculadas para esos mismos meses de prueba."
    )
else:
    st.markdown(
        "**Cada punto compara las ventas reales de un mes con las calculadas.** "
        "Cuanto más cerca de la diagonal, menor es el error."
    )
if base_reg == "Principales Canales" and elegido == "Digital":
    st.caption(
        f"Digital: se utilizan solo los meses con datos completos. "
        f"Se excluyeron {excluidos} registros incompletos dentro del corte."
    )

fig = go.Figure()
if len(xs) == 1:
    x = xs[0]
    for frame, valores, etiqueta, color in [
        (train, yt, "Ventas reales · meses usados para crear el modelo", "#AAAAAA"),
        (test, ye, "Ventas reales · meses de prueba", ROJO)
    ]:
        fig.add_trace(go.Scatter(
            x=frame[x], y=valores, mode="markers", name=etiqueta,
            marker=dict(color=color, size=10),
            text=frame["Periodo"].dt.strftime("%Y-%m"),
            hovertemplate="Mes: %{text}<br>" + nombres[x] + ": %{x}<br>Ventas reales: %{y}<extra></extra>"
        ))
    grid = np.linspace(d[x].min(), d[x].max(), 100).reshape(-1, 1)
    fig.add_trace(go.Scatter(x=grid.ravel(), y=modelo.predict(grid),
                            mode="lines", name="Tendencia del modelo", line=dict(color="#FFFFFF")))
    fig.add_trace(go.Scatter(
        x=test[x], y=pe, mode="markers", name="Ventas calculadas · meses de prueba",
        marker=dict(color="#33CC99", symbol="x", size=12),
        text=test["Periodo"].dt.strftime("%Y-%m"),
        hovertemplate="Mes: %{text}<br>" + nombres[x] + ": %{x}<br>Ventas calculadas: %{y:.2f}<extra></extra>"
    ))
    fig.update_layout(xaxis_title=nombres[x], yaxis_title="Ventas mensuales")
else:
    for frame, observados, predichos, etiqueta, color in [
        (train, yt, pt, "Meses usados para crear el modelo", "#AAAAAA"),
        (test, ye, pe, "Meses de prueba", ROJO)
    ]:
        fig.add_trace(go.Scatter(
            x=observados, y=predichos, mode="markers", name=etiqueta,
            marker=dict(color=color, size=10), text=frame["Periodo"].dt.strftime("%Y-%m"),
            hovertemplate="Mes: %{text}<br>Ventas reales: %{x}<br>Ventas calculadas: %{y:.2f}<extra></extra>"
        ))
    lim = [min(yt.min(), ye.min(), pt.min(), pe.min()),
           max(yt.max(), ye.max(), pt.max(), pe.max())]
    fig.add_trace(go.Scatter(x=lim, y=lim, mode="lines", name="Estimación perfecta",
                            line=dict(color="#FFFFFF", dash="dash")))
    fig.update_layout(xaxis_title="Ventas reales", yaxis_title="Ventas calculadas")
st.plotly_chart(estilo(fig, alto=480), use_container_width=True)


# Comparación de los mismos seis meses: cifras reales y calculadas.
st.subheader("Ventas reales y calculadas por mes")
mensual = go.Figure()
mensual.add_trace(go.Scatter(
    x=test["Periodo"], y=ye, mode="lines+markers",
    name="Ventas reales", line=dict(color=ROJO),
    hovertemplate="Mes: %{x|%Y-%m}<br>Ventas reales: %{y}<extra></extra>"
))
mensual.add_trace(go.Scatter(
    x=test["Periodo"], y=pe, mode="lines+markers",
    name="Ventas calculadas", line=dict(color="#33CC99", dash="dash"),
    hovertemplate="Mes: %{x|%Y-%m}<br>Ventas calculadas: %{y:.2f}<extra></extra>"
))
mensual.update_layout(xaxis_title="Mes de prueba", yaxis_title="Ventas",
                      hovermode="x unified")
mensual.update_xaxes(dtick="M1", tickformat="%Y-%m")
st.plotly_chart(estilo(mensual, alto=360), use_container_width=True)

# Proyección por escenario: usa el mismo modelo entrenado, sin alterar sus KPI.
if len(xs) > 1:
    st.subheader("Proyección de ventas")
    st.write("Ingresa los valores que esperas para un mes y calcula las ventas de ese escenario.")
    columnas_escenario = st.columns(len(xs))
    entradas = []
    fuera_rango = []
    for i, variable in enumerate(xs):
        minimo = int(train[variable].min())
        maximo = int(train[variable].max())
        with columnas_escenario[i]:
            valor = st.number_input(
                nombres[variable] + " esperados",
                min_value=0,
                value=int(round(train[variable].median())),
                step=1,
                key="proyeccion_" + variable
            )
            st.caption(f"Rango usado para crear el modelo: {minimo}–{maximo}")
        entradas.append(valor)
        if valor < minimo or valor > maximo:
            fuera_rango.append(nombres[variable])
    escenario = np.asarray([entradas], dtype=np.float64)
    proyeccion = float(modelo.predict(escenario)[0])
    st.metric("Ventas proyectadas para el escenario", f"{proyeccion:.2f}")
    st.caption(
        "Es una estimación condicionada a los valores ingresados, no una garantía. "
        "Los indicadores de arriba evalúan meses históricos y no miden el error de este escenario."
    )
    if fuera_rango:
        st.warning("Fuera del rango histórico: " + ", ".join(fuera_rango) +
                   ". Esta proyección extrapola y puede ser menos confiable.")
    if proyeccion < 0:
        st.warning("El modelo proyecta ventas negativas; este resultado no es válido como cantidad de ventas.")
    if np.isfinite(r2) and r2 < 0:
        st.caption("El R² de evaluación es negativo: interpreta esta proyección como exploratoria.")
    formula = f"Ventas proyectadas = {modelo.intercept_:.4f}"
    for variable, coeficiente in zip(xs, modelo.coef_):
        formula += f" {coeficiente:+.4f} × {nombres[variable]}"
    with st.expander("Fórmula de la proyección"):
        st.write(formula)
    export_escenario = pd.DataFrame([{**dict(zip(xs, entradas)), "Ventas proyectadas": proyeccion}])
    st.download_button(
        "Descargar escenario", export_escenario.to_csv(index=False).encode("utf-8-sig"),
        "proyeccion_ventas_gac.csv", "text/csv", key="descargar_escenario"
    )


resultados = []
def resultado(nombre, pred):
    resultados.append({
        "Modelo": nombre,
        "MAE · ventas": mean_absolute_error(ye, pred),
        "RMSE · ventas": np.sqrt(mean_squared_error(ye, pred)),
        "R² evaluación": r2_score(ye, pred) if np.ptp(ye) > 0 else np.nan
    })
resultado("Modelo seleccionado", pe)
resultado("Referencia: promedio histórico", np.full(len(ye), yt.mean(), dtype=np.float64))
if len(xs) > 1:
    for x in xs:
        simple = LinearRegression().fit(train[[x]].to_numpy(dtype=np.float64), yt)
        resultado("Simple: " + nombres[x], simple.predict(test[[x]].to_numpy(dtype=np.float64)))
    mejor = min(r["MAE · ventas"] for r in resultados if r["Modelo"].startswith("Simple:"))
    mensaje = ("La combinación reduce el error frente a los modelos simples comparados."
               if mae < mejor else
               "La combinación no reduce el error frente al mejor modelo simple comparado.")
else:
    mensaje = f"El error promedio en evaluación es de {mae:.2f} ventas por mes."

st.write(mensaje)
st.subheader("Comparación de modelos")
st.dataframe(pd.DataFrame(resultados).round(3), hide_index=True, use_container_width=True)

with st.expander("Correlaciones y coeficientes"):
    corr = train[[y_col] + xs].corr().rename(index=nombres, columns=nombres)
    heat = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1,
                     color_continuous_scale="RdBu_r", title="Correlación de Pearson")
    st.plotly_chart(estilo(heat, alto=400, escala=True), use_container_width=True)
    st.dataframe(pd.DataFrame({"Variable": [nombres[x] for x in xs],
                              "Coeficiente": modelo.coef_}).round(4), hide_index=True)
    st.write(f"Intercepto: {modelo.intercept_:.4f}")
    st.caption("Los coeficientes describen asociaciones manteniendo las otras variables constantes; no demuestran causalidad.")

with st.expander("Detalle mensual y descarga"):
    detalle = test[["Periodo"] + xs + [y_col]].copy()
    detalle["Periodo"] = detalle["Periodo"].dt.strftime("%Y-%m")
    detalle["Ventas calculadas"] = pe
    detalle["Error absoluto"] = np.abs(ye - pe)
    detalle = detalle.rename(columns=nombres)
    st.dataframe(detalle.round(2), hide_index=True, use_container_width=True)
    st.download_button("Descargar estimaciones", detalle.to_csv(index=False).encode("utf-8-sig"),
                       "estimaciones_regresion_gac.csv", "text/csv", key="reg_download")

with st.expander("Cómo leer los resultados"):
    st.write(
        "MAE: error absoluto promedio. RMSE: da más peso a errores grandes. "
        "R²: compara el modelo con la media observada del periodo de evaluación; "
        "puede ser negativo y no representa un porcentaje de precisión."
    )
    st.write(
        "En la simple, las cruces verdes son las estimaciones y los puntos son los datos observados. "
        "En la múltiple, acercarse a la diagonal significa menor error; arriba sobreestima y abajo subestima."
    )
    st.write(
        "Las explicativas corresponden al mismo mes que las ventas. "
        "Para pronosticar un mes futuro también tendríamos que conocer o estimar esas explicativas."
    )
    st.write(f"Entrenamiento: {len(train)} meses. Evaluación: {len(test)} meses. Registros incompletos excluidos: {excluidos}.")
    st.write("Corte elegido: junio de 2026. Las comparaciones son exploratorias y requieren confirmación independiente.")

if (pe < 0).any():
    st.warning("Hay estimaciones negativas: la regresión lineal no restringe las predicciones a conteos positivos.")
