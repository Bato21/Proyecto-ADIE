ARCHIVOS GENERADOS PARA DJANGO

1. severidad_region.csv
   - Métricas por región
   - Incluye:
     codregion, REGION, total, alta, porcentaje, poblacion,
     porcentaje_severidad, porcentaje_poblacion, tasa_100k

2. severidad_comuna.csv
   - Métricas por comuna
   - Incluye:
     codregion, cod_comuna, COMUNA_GEOJSON, REGION_GEOJSON, PROVINCIA_GEOJSON,
     total, alta, poblacion, porcentaje_severidad, porcentaje_poblacion, tasa_100k

3. hospitales.csv
   - Hospitales georreferenciados
   - Incluye datos hospitalarios y coordenadas

4. poblacion_comuna_censo2024.csv
   - Población agregada por región y comuna

5. comunas_geo_index.csv
   - Tabla puente comuna <-> cod_comuna <-> región

6. geojson/chile_regiones.geojson
   - GeoJSON país por regiones

7. geojson/region_XX.geojson
   - GeoJSON por región para click regional -> comunas

8. Flujos exportados:
   - traslados.csv

RUTA BASE:
C:\Users\sebas\Downloads\Inferencia\data\processed