# Notebooks de análisis

Esta carpeta agrupa los notebooks usados para exploración, limpieza, visualización y validación estadística.

## Uso recomendado
- Mantener aquí los notebooks de trabajo y sus versiones finales.
- Separar exploración, preparación y análisis final cuando el proyecto crezca.

## Notebook actual
- `00_pipeline_maestra_grd_2024.ipynb`: notebook maestro del flujo completo, desde carga y limpieza hasta mapas, georreferenciación y exportación de archivos para el dashboard.

## División sugerida
Los notebooks de trabajo ya quedaron separados así:
- `01_carga_limpieza_base_grd_2024.ipynb`
- `02_analisis_regional_severidad_grd_2024.ipynb`
- `03_analisis_comunal_hospitalario_grd_2024.ipynb`
- `04_exportacion_traslados_django_grd_2024.ipynb`

## Apoyo compartido
- `scripts/grd_common.py`: funciones comunes para cargar, limpiar y reutilizar insumos entre notebooks.
