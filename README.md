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

---

**Autores:** Benjamín Pinto, Sebastían Ruiz, Baptiste Vial  
**Curso:** Análisis de datos e inferencia estadística - Sección 2  
**Institución:** Universidad del Desarrollo (UDD), Facultad de Ingeniería
