# app.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(page_title="Analytics Educativo", page_icon="📊", layout="wide")

class AnalizadorEducativo:
    def __init__(self, df):
        self.df = df
        self.resultados = {}
        
    def limpiar_datos(self):
        """Limpia y prepara el dataset"""
        # Convertir columnas de fecha si existen
        columnas_fecha = ['fecha_registro', 'timestamp', 'fecha']
        for col in columnas_fecha:
            if col in self.df.columns:
                try:
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                except:
                    pass
        
        # Limpiar espacios en strings
        for col in self.df.select_dtypes(include=['object']).columns:
            self.df[col] = self.df[col].astype(str).str.strip()
            
        return self.df
    
    def usuarios_nuevos_semana(self):
        """Calcula usuarios nuevos por semana"""
        if 'fecha_registro' in self.df.columns:
            df_temp = self.df.copy()
            df_temp['semana_registro'] = df_temp['fecha_registro'].dt.isocalendar().week
            df_temp['año_registro'] = df_temp['fecha_registro'].dt.year
            usuarios_semana = df_temp.groupby(['año_registro', 'semana_registro']).size().reset_index(name='usuarios_nuevos')
            usuarios_semana['semana'] = usuarios_semana['año_registro'].astype(str) + '-S' + usuarios_semana['semana_registro'].astype(str)
            return usuarios_semana[['semana', 'usuarios_nuevos']]
        return pd.DataFrame()
    
    def tipo_usuario_mas_registrado(self):
        """Analiza distribución de tipos de usuario"""
        if 'tipo_usuario' in self.df.columns:
            distribucion = self.df['tipo_usuario'].value_counts()
            porcentajes = (self.df['tipo_usuario'].value_counts(normalize=True) * 100).round(2)
            resultado = pd.DataFrame({
                'tipo': distribucion.index,
                'cantidad': distribucion.values,
                'porcentaje': porcentajes.values
            })
            return resultado
        return pd.DataFrame()
    
    def hoja_vida_completa(self):
        """Analiza completitud de hojas de vida"""
        # Asumiendo columnas que deberían estar completas
        columnas_importantes = ['nombre', 'email', 'telefono', 'direccion']
        columnas_existentes = [col for col in columnas_importantes if col in self.df.columns]
        
        if columnas_existentes:
            df_temp = self.df.copy()
            df_temp['completado'] = df_temp[columnas_existentes].notna().all(axis=1)
            estado_hoja_vida = df_temp['completado'].value_counts().reset_index()
            estado_hoja_vida.columns = ['completado', 'cantidad']
            estado_hoja_vida['porcentaje'] = (estado_hoja_vida['cantidad'] / len(df_temp) * 100).round(2)
            return estado_hoja_vida
        return pd.DataFrame()
    
    def habilidades_mas_frecuentes(self):
        """Encuentra las habilidades más frecuentes"""
        if 'habilidades' in self.df.columns:
            # Separar habilidades por comas y crear lista plana
            habilidades = self.df['habilidades'].dropna().str.split(',').explode()
            habilidades = habilidades.str.strip().str.lower()
            top_habilidades = habilidades.value_counts().head(10).reset_index()
            top_habilidades.columns = ['habilidad', 'frecuencia']
            return top_habilidades
        return pd.DataFrame()
    
    def consultas_familiares(self):
        """Analiza consultas familiares a perfiles"""
        if all(col in self.df.columns for col in ['id_estudiante', 'tipo_usuario', 'timestamp']):
            df_familiares = self.df[self.df['tipo_usuario'] == 'familiar']
            consultas_por_estudiante = df_familiares.groupby('id_estudiante').size().reset_index(name='consultas')
            
            # Estudiantes sin interacción
            todos_estudiantes = self.df[self.df['tipo_usuario'] == 'estudiante']['id_estudiante'].unique()
            estudiantes_con_consulta = consultas_por_estudiante['id_estudiante'].unique()
            estudiantes_sin_interaccion = set(todos_estudiantes) - set(estudiantes_con_consulta)
            
            return {
                'consultas_por_estudiante': consultas_por_estudiante,
                'estudiantes_sin_interaccion': len(estudiantes_sin_interaccion),
                'total_estudiantes': len(todos_estudiantes)
            }
        return {}
    
    def horarios_acceso_familiares(self):
        """Analiza horarios de acceso de familiares"""
        if all(col in self.df.columns for col in ['timestamp', 'tipo_usuario']):
            df_familiares = self.df[self.df['tipo_usuario'] == 'familiar'].copy()
            df_familiares['hora'] = df_familiares['timestamp'].dt.hour
            df_familiares['franja_horaria'] = pd.cut(df_familiares['hora'], 
                                                   bins=[0, 6, 12, 18, 24], 
                                                   labels=['Madrugada', 'Mañana', 'Tarde', 'Noche'])
            horarios = df_familiares['franja_horaria'].value_counts().reset_index()
            horarios.columns = ['franja_horaria', 'accesos']
            return horarios
        return pd.DataFrame()
    
    def promedio_notas_grupo(self):
        """Calcula promedio general de notas por grupo"""
        if all(col in self.df.columns for col in ['grupo_id', 'nota']):
            promedio_grupos = self.df.groupby('grupo_id')['nota'].mean().round(2).reset_index()
            promedio_grupos.columns = ['grupo_id', 'promedio_nota']
            return promedio_grupos.sort_values('promedio_nota', ascending=False)
        return pd.DataFrame()
    
    def materias_mas_reprobaciones(self):
        """Identifica materias con más reprobaciones"""
        if all(col in self.df.columns for col in ['materia', 'nota']):
            df_temp = self.df.copy()
            df_temp['reprobado'] = df_temp['nota'] < 3.0
            reprobaciones_materia = df_temp.groupby('materia').agg({
                'reprobado': ['sum', 'count']
            }).round(2)
            reprobaciones_materia.columns = ['reprobados', 'total_estudiantes']
            reprobaciones_materia = reprobaciones_materia.reset_index()
            reprobaciones_materia['porcentaje_reprobacion'] = (reprobaciones_materia['reprobados'] / reprobaciones_materia['total_estudiantes'] * 100).round(2)
            return reprobaciones_materia.sort_values('porcentaje_reprobacion', ascending=False)
        return pd.DataFrame()
    
    def asistencia_promedio_estudiante(self):
        """Calcula asistencia promedio por estudiante"""
        if all(col in self.df.columns for col in ['id_estudiante', 'asistencia']):
            asistencia_estudiantes = self.df.groupby('id_estudiante').agg({
                'asistencia': 'mean'
            }).round(2).reset_index()
            asistencia_estudiantes.columns = ['id_estudiante', 'asistencia_promedio']
            return asistencia_estudiantes
        return pd.DataFrame()
    
    def estudiantes_ausencias_recurrentes(self):
        """Identifica estudiantes con ausencias recurrentes"""
        if all(col in self.df.columns for col in ['id_estudiante', 'estado_asistencia']):
            ausencias = self.df[self.df['estado_asistencia'] == 'ausente']
            conteo_ausencias = ausencias.groupby('id_estudiante').size().reset_index(name='ausencias')
            estudiantes_problema = conteo_ausencias[conteo_ausencias['ausencias'] > 3]
            return estudiantes_problema.sort_values('ausencias', ascending=False)
        return pd.DataFrame()
    
    def tipos_apoyo_solicitados(self):
        """Analiza tipos de apoyo más solicitados"""
        if 'tipo_apoyo' in self.df.columns:
            apoyos = self.df['tipo_apoyo'].value_counts().reset_index()
            apoyos.columns = ['tipo_apoyo', 'solicitudes']
            apoyos['porcentaje'] = (apoyos['solicitudes'] / apoyos['solicitudes'].sum() * 100).round(2)
            return apoyos.head(3)
        return pd.DataFrame()
    
    def frecuencia_solicitudes_mes(self):
        """Analiza frecuencia de solicitudes por mes"""
        if 'timestamp' in self.df.columns:
            df_temp = self.df.copy()
            df_temp['mes'] = df_temp['timestamp'].dt.to_period('M')
            solicitudes_mes = df_temp.groupby('mes').size().reset_index(name='solicitudes')
            solicitudes_mes['mes'] = solicitudes_mes['mes'].astype(str)
            return solicitudes_mes
        return pd.DataFrame()
    
    def resumen_estadistico_grupo(self):
        """Genera resumen estadístico por grupo"""
        if all(col in self.df.columns for col in ['grupo_id', 'nota', 'asistencia']):
            resumen = self.df.groupby('grupo_id')[['nota', 'asistencia']].describe()
            return resumen.round(2)
        return pd.DataFrame()
    
    def correlacion_nota_asistencia(self):
        """Calcula correlación entre nota y asistencia"""
        if all(col in self.df.columns for col in ['nota', 'asistencia']):
            correlacion = self.df[['nota', 'asistencia']].corr().iloc[0, 1]
            return round(correlacion, 4)
        return None
    
    def generar_informe_completo(self):
        """Ejecuta todos los análisis y genera informe completo"""
        st.header("📊 Informe Completo de Analytics Educativo")
        
        # Limpiar datos primero
        self.df = self.limpiar_datos()
        
        # Mostrar información básica del dataset
        st.subheader("📋 Información del Dataset")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Registros", len(self.df))
        with col2:
            st.metric("Columnas", len(self.df.columns))
        with col3:
            st.metric("Valores Nulos", self.df.isnull().sum().sum())
        
        # 1. Usuarios nuevos por semana
        st.subheader("👥 Usuarios Nuevos por Semana")
        usuarios_semana = self.usuarios_nuevos_semana()
        if not usuarios_semana.empty:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(usuarios_semana, use_container_width=True)
            with col2:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(usuarios_semana['semana'], usuarios_semana['usuarios_nuevos'])
                ax.set_title('Usuarios Nuevos por Semana')
                ax.set_xlabel('Semana')
                ax.set_ylabel('Usuarios Nuevos')
                plt.xticks(rotation=45)
                st.pyplot(fig)
        
        # 2. Tipo de usuario más registrado
        st.subheader("🎯 Distribución de Tipos de Usuario")
        tipo_usuario = self.tipo_usuario_mas_registrado()
        if not tipo_usuario.empty:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(tipo_usuario, use_container_width=True)
            with col2:
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.pie(tipo_usuario['cantidad'], labels=tipo_usuario['tipo'], autopct='%1.1f%%')
                ax.set_title('Distribución de Tipos de Usuario')
                st.pyplot(fig)
        
        # 3. Hoja de vida completa
        st.subheader("📄 Estado de Hojas de Vida")
        hoja_vida = self.hoja_vida_completa()
        if not hoja_vida.empty:
            st.dataframe(hoja_vida, use_container_width=True)
        
        # 4. Habilidades más frecuentes
        st.subheader("🛠️ Top 10 Habilidades Más Frecuentes")
        habilidades = self.habilidades_mas_frecuentes()
        if not habilidades.empty:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(habilidades, use_container_width=True)
            with col2:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.barh(habilidades['habilidad'], habilidades['frecuencia'])
                ax.set_title('Top 10 Habilidades Más Frecuentes')
                ax.set_xlabel('Frecuencia')
                st.pyplot(fig)
        
        # 5. Consultas familiares
        st.subheader("👨‍👩‍👧‍👦 Consultas Familiares a Perfiles")
        consultas = self.consultas_familiares()
        if consultas:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Estudiantes con consultas", len(consultas['consultas_por_estudiante']))
            with col2:
                st.metric("Estudiantes sin interacción", consultas['estudiantes_sin_interaccion'])
            with col3:
                st.metric("Total estudiantes", consultas['total_estudiantes'])
            
            if not consultas['consultas_por_estudiante'].empty:
                st.dataframe(consultas['consultas_por_estudiante'].head(10), use_container_width=True)
        
        # 6. Horarios de acceso familiares
        st.subheader("🕒 Horarios de Acceso de Familiares")
        horarios = self.horarios_acceso_familiares()
        if not horarios.empty:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(horarios, use_container_width=True)
            with col2:
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.bar(horarios['franja_horaria'], horarios['accesos'])
                ax.set_title('Accesos por Franja Horaria')
                ax.set_ylabel('Número de Accesos')
                st.pyplot(fig)
        
        # 7. Promedio de notas por grupo
        st.subheader("📈 Promedio de Notas por Grupo")
        promedio_notas = self.promedio_notas_grupo()
        if not promedio_notas.empty:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(promedio_notas, use_container_width=True)
            with col2:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(promedio_notas['grupo_id'].astype(str), promedio_notas['promedio_nota'])
                ax.set_title('Promedio de Notas por Grupo')
                ax.set_xlabel('Grupo')
                ax.set_ylabel('Promedio de Nota')
                plt.xticks(rotation=45)
                st.pyplot(fig)
        
        # 8. Materias con más reprobaciones
        st.subheader("📚 Materias con Más Reprobaciones")
        reprobaciones = self.materias_mas_reprobaciones()
        if not reprobaciones.empty:
            st.dataframe(reprobaciones.head(10), use_container_width=True)
        
        # 9. Asistencia promedio por estudiante
        st.subheader("✅ Asistencia Promedio por Estudiante")
        asistencia = self.asistencia_promedio_estudiante()
        if not asistencia.empty:
            st.dataframe(asistencia.head(15), use_container_width=True)
        
        # 10. Estudiantes con ausencias recurrentes
        st.subheader("⚠️ Estudiantes con Ausencias Recurrentes")
        ausencias = self.estudiantes_ausencias_recurrentes()
        if not ausencias.empty:
            st.dataframe(ausencias, use_container_width=True)
        else:
            st.info("No se encontraron estudiantes con más de 3 ausencias")
        
        # 11. Tipos de apoyo más solicitados
        st.subheader("🆕 Tipos de Apoyo Más Solicitados")
        apoyos = self.tipos_apoyo_solicitados()
        if not apoyos.empty:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(apoyos, use_container_width=True)
            with col2:
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.pie(apoyos['solicitudes'], labels=apoyos['tipo_apoyo'], autopct='%1.1f%%')
                ax.set_title('Top 3 Tipos de Apoyo Solicitados')
                st.pyplot(fig)
        
        # 12. Frecuencia de solicitudes por mes
        st.subheader("📅 Frecuencia de Solicitudes por Mes")
        solicitudes_mes = self.frecuencia_solicitudes_mes()
        if not solicitudes_mes.empty:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(solicitudes_mes, use_container_width=True)
            with col2:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(solicitudes_mes['mes'], solicitudes_mes['solicitudes'], marker='o')
                ax.set_title('Tendencia de Solicitudes por Mes')
                ax.set_xlabel('Mes')
                ax.set_ylabel('Solicitudes')
                plt.xticks(rotation=45)
                st.pyplot(fig)
        
        # 13. Resumen estadístico por grupo
        st.subheader("📊 Resumen Estadístico por Grupo")
        resumen_grupo = self.resumen_estadistico_grupo()
        if not resumen_grupo.empty:
            st.dataframe(resumen_grupo, use_container_width=True)
        
        # 14. Correlación entre nota y asistencia
        st.subheader("🔗 Correlación entre Nota y Asistencia")
        correlacion = self.correlacion_nota_asistencia()
        if correlacion is not None:
            st.metric("Coeficiente de Correlación", correlacion)
            
            # Heatmap de correlación
            fig, ax = plt.subplots(figsize=(6, 4))
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                corr_matrix = self.df[numeric_cols].corr()
                sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax)
                ax.set_title('Matriz de Correlación')
                st.pyplot(fig)

def main():
    st.title("🎓 Analytics Educativo")
    st.markdown("Carga un archivo CSV con datos educativos para generar un análisis completo")
    
    # --- CÓDIGO SIMPLE PARA DESCARGAR CSV ---
    with open("datos_educativos.csv", "r") as file:
        csv_data = file.read()
    
    st.download_button(
        "📥 Descargar csv de ejemplo",
        csv_data,
        "datos_educativos_ejemplo.csv",
        "text/csv"
    )
    
    
    # Subir archivo
    uploaded_file = st.file_uploader("Sube tu archivo CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # Leer el archivo CSV
            df = pd.read_csv(uploaded_file)
            st.success(f"Archivo cargado exitosamente: {len(df)} registros, {len(df.columns)} columnas")
            
            # Mostrar vista previa
            with st.expander("Vista previa de los datos"):
                st.dataframe(df.head())
                st.write("**Información del dataset:**")
                st.write(f"- Columnas: {list(df.columns)}")
                st.write(f"- Tipos de datos: {df.dtypes.to_dict()}")
            
            # Generar análisis
            if st.button("🚀 Generar Análisis Completo", type="primary"):
                with st.spinner("Analizando datos..."):
                    analizador = AnalizadorEducativo(df)
                    analizador.generar_informe_completo()
                    
                    # Guardar resultados
                    if not os.path.exists('resultados'):
                        os.makedirs('resultados')
                    
                    # Crear resumen ejecutivo
                    st.subheader("📋 Resumen Ejecutivo")
                    
                    # Métricas clave
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if 'tipo_usuario' in df.columns:
                            total_estudiantes = len(df[df['tipo_usuario'] == 'estudiante'])
                            st.metric("Total Estudiantes", total_estudiantes)
                    
                    with col2:
                        if 'nota' in df.columns:
                            promedio_general = df['nota'].mean()
                            st.metric("Promedio General", f"{promedio_general:.2f}")
                    
                    with col3:
                        if 'asistencia' in df.columns:
                            asistencia_promedio = df['asistencia'].mean()
                            st.metric("Asistencia Promedio", f"{asistencia_promedio:.1f}%")
                    
                    with col4:
                        correlacion = analizador.correlacion_nota_asistencia()
                        if correlacion:
                            st.metric("Correlación Nota-Asistencia", f"{correlacion:.2f}")
        
        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
    
    else:
        st.info("""
        ### 📝 Formato esperado del CSV:
        
        El archivo CSV debería contener columnas como:
        - `id_estudiante`, `nombre`, `email`, `tipo_usuario` (estudiante/docente/familiar)
        - `fecha_registro`, `timestamp`, `grupo_id`, `materia`
        - `nota` (numérica), `asistencia` (porcentaje), `estado_asistencia` (presente/ausente)
        - `habilidades` (separadas por comas), `tipo_apoyo`
        
        ### 🎯 Ejemplo de estructura:
        ```
        id_estudiante,nombre,tipo_usuario,nota,asistencia,materia,habilidades,timestamp
        1,Juan Pérez,estudiante,4.2,95,Matemáticas,"python,matemáticas,análisis",2024-01-15
        2,María López,estudiante,3.8,88,Ciencias,"ciencias,investigación",2024-01-16
        ```
        ### 🔗 Análisis que realiza:
        1. Cuenta cuántos usuarios nuevos se registran cada semana y lo muestra claramente en una tabla.
        2. Identifica qué tipo de usuario se registra más y mostrar porcentajes por categoría.
        3. Analiza cuántos estudiantes completan su hoja de vida y calcula proporciones de completitud.
        4. Encuentra las habilidades más comunes en perfiles y muestra las diez más mencionadas.
        5. Cuenta cuántos familiares revisan el perfil del estudiante y detecta sin interacción.
        6. Analiza a qué horas del día los familiares ingresan con más frecuencia.
        7. Calcula el promedio general de notas por grupo y ordenar de mayor a menor.
        8. Detecta materias con más reprobados y muestra porcentaje de estudiantes con nota baja.
        9. Calcula el promedio de asistencia por estudiante y muestra su porcentaje total.
        10. Identifica estudiantes con más de tres ausencias y muestra lista correspondiente.
        11. Contar qué tipos de apoyo se piden más y muestra los tres principales.
        12. Analiza cuántas solicitudes se hacen cada mes para ver su frecuencia.
        13. Genera un resumen estadístico de notas y asistencia agrupado por cada grupo.
        14. Analiza la relación entre notas y asistencia usando correlación y visualización gráfica."""
)

if __name__ == "__main__":
    main()