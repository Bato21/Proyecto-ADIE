# Análisis de las Desigualdades en el Acceso y Derivación de Pacientes de Alta Complejidad en la Red Pública de Salud de Chile (2024)

## Descripción del Proyecto
El sistema público de salud chileno presenta una distribución heterogénea de recursos y especialistas, lo que genera una constante derivación interhospitalaria de pacientes graves. Este proyecto busca llenar el vacío existente en la literatura mediante un análisis sistémico post-pandemia. Para ello, se utiliza el universo completo de egresos GRD para modelar matemáticamente la relación entre el volumen de emisión de traslados de un hospital y sus índices de mortalidad en casos de alta severidad.

## Pregunta de Investigación
¿Cuál es la relación estadística y espacial entre los altos índices de mortalidad hospitalaria y los patrones de derivación de pacientes de alta severidad (IR ≥ 3) en la red pública de salud de Chile durante el año 2024, y qué características clínicas o de gestión explican el comportamiento de los establecimientos con mayor emisión de traslados?

## Metodología
El proyecto emplea un diseño metodológico cuantitativo, observacional y retrospectivo. El estudio se divide en tres fases principales:

* **Análisis Descriptivo y Espacial**: Caracterización de las frecuencias y mapeo geoespacial mediante coropletas a nivel regional y provincial para observar la concentración de pacientes de alta severidad.
* **Análisis Bivariado**: Evaluación inicial de las correlaciones entre el volumen de traslados emitidos por cada centro y sus tasas de mortalidad.
* **Análisis Inferencial y Predictivo**: Modelamiento estadístico para establecer la significancia de las relaciones y predecir riesgos asociados a la derivación.

## Modelos Estadísticos Aplicados
* **Correlación de Pearson y/o Spearman**: Para medir la fuerza y dirección de la relación entre la emisión de traslados y la mortalidad.
* **Pruebas de Hipótesis (ANOVA / Kruskal-Wallis)**: Para identificar diferencias significativas en severidad y mortalidad entre las regiones de Chile.
* **Regresión Logística Multivariada**: Modelo donde la variable de respuesta es la mortalidad, utilizando predictores para calcular el riesgo de traslado.

## Variables Clave
* **IR_29301_SEVERIDAD**: Nivel de severidad GRD para ajustar el riesgo clínico del paciente.
* **IR_29301_MORTALIDAD**: Índice de mortalidad que actúa como variable dependiente para evaluar el desenlace clínico.
* **HOSPPROCEDENCIA y ESTABLECIMIENTO**: Variables categóricas utilizadas para construir la matriz de traslados entre hospitales emisores y receptores.
* **CODREGION**: Código regional esencial para evaluar la inequidad territorial mediante análisis espacial.
* **PESO_GRD**: Variable que funciona como proxy del esfuerzo terapéutico y los costos asociados al consumo de recursos.

## Tecnologías y Herramientas
Para llevar a cabo la limpieza de datos, la homologación de formatos y la estructuración de la información, el proyecto se apoya en lenguajes como Python y librerías especializadas en el análisis de datos como Pandas.

## Fuente de Datos
Los datos utilizados en esta investigación corresponden a las bases de datos maestras de Grupos Relacionados por el Diagnóstico (GRD) del sistema público chileno para el año 2024. Estos registros son gestionados institucionalmente por el Ministerio de Salud (MINSAL) a través del Departamento de Estadísticas e Información de Salud (DEIS).

**https://public.tableau.com/views/PropuestaTableroGRD/PropuestaTableroGRD?%3AshowVizHome=no#1**

## Estructura del proyecto

La organización actual separa el trabajo en cuatro zonas principales:

* `app/`: backend Django, con `manage.py`, configuración del proyecto y la app `dashboard`.
* `data/`: insumos crudos y salidas procesadas para análisis y visualización.
* `docs/`: guía operativa y notas de arranque del proyecto.
* `notebooks/`: exploración y análisis en Jupyter.
* `scripts/`: espacio reservado para automatizar limpieza, carga o generación de datos derivados.

### Flujo sugerido
1. Revisar `docs/INICIO.txt` para la ejecución rápida.
2. Usar `notebooks/00_pipeline_maestra_grd_2024.ipynb` como referencia consolidada si quieres revisar todo el flujo en un solo lugar.
3. Trabajar por etapas en `notebooks/01_carga_limpieza_base_grd_2024.ipynb`, `notebooks/02_analisis_regional_severidad_grd_2024.ipynb`, `notebooks/03_analisis_comunal_hospitalario_grd_2024.ipynb` y `notebooks/04_exportacion_traslados_django_grd_2024.ipynb`.
4. Dejar los procesos reutilizables en `scripts/grd_common.py`.
5. Consumir los datos finales desde `data/processed/` dentro del dashboard Django.

### Validación de reestructuración
Para validar que la nueva estructura mantiene funcionalidad (notebooks, artefactos y Django), ejecutar desde la raíz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/validar_reestructuracion.ps1
```

Opciones útiles:
- Omitir notebooks: `-SkipNotebooks`
- Omitir validación de CSV: `-SkipArtifacts`
- Omitir tests Django: `-SkipDjango`
- Ajustar timeout por notebook (segundos): `-NotebookTimeout 3600`

---

**Autores:** Benjamín Pinto, Sebastían Ruiz, Baptiste Vial  
**Curso:** Análisis de datos e inferencia estadística - Sección 2  
**Institución:** Universidad del Desarrollo (UDD), Facultad de Ingeniería
