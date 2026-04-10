import json
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from .services.loaders import (
    cargar_severidad_region,
    cargar_severidad_comuna,
    cargar_hospitales,
    cargar_traslados,
)

def home(request):
    df_region = cargar_severidad_region()
    regiones = df_region.to_dict(orient="records")

    ruta_geojson = settings.GEO_DIR / "chile_regiones.geojson"
    with open(ruta_geojson, "r", encoding="utf-8") as f:
        geojson_chile = json.load(f)

    context = {
        "regiones": regiones,
        "regiones_json": json.dumps(regiones, ensure_ascii=False),
        "geojson_chile_json": json.dumps(geojson_chile, ensure_ascii=False),
        "total_regiones": len(regiones),
    }
    return render(request, "dashboard/index.html", context)


def api_comunas(request, codregion):
    df_comunas = cargar_severidad_comuna()
    df_hospitales = cargar_hospitales()

    df_region = df_comunas[df_comunas["codregion"] == int(codregion)].copy()
    comunas = df_region.to_dict(orient="records")

    ruta_geo = settings.GEO_DIR / f"region_{int(codregion):02d}.geojson"

    try:
        with open(ruta_geo, "r", encoding="utf-8") as f:
            geojson = json.load(f)
    except FileNotFoundError:
        geojson = None

    df_hospitales = df_hospitales.dropna(subset=["LAT_GEO", "LON_GEO"]).copy()
    hospitales = df_hospitales.to_dict(orient="records")

    return JsonResponse({
        "comunas": comunas,
        "geojson": geojson,
        "hospitales": hospitales,
    })


def api_traslados(request):
    df = cargar_traslados()
    return JsonResponse({"traslados": df.to_dict(orient="records")})


def vista_traslados(request):
    df_traslados = cargar_traslados()
    df_regiones = cargar_severidad_region()

    region = request.GET.get("region", "").strip()

    if region:
        df_filtrado = df_traslados[
            df_traslados["region_origen"].astype(str).str.upper() == region.upper()
        ].copy()
    else:
        df_filtrado = df_traslados.copy()

    resumen = (
        df_filtrado
        .groupby(["hospital_origen", "region_origen"], as_index=False)
        .agg(
            total_traslados=("cantidad", "sum"),
            total_graves=("graves", "sum")
        )
    )

    if not resumen.empty:
        resumen["porcentaje_graves"] = (
            resumen["total_graves"] / resumen["total_traslados"] * 100
        ).round(2)
    else:
        resumen["porcentaje_graves"] = []

    idx = (
        df_filtrado
        .sort_values(["hospital_origen", "cantidad"], ascending=[True, False])
        .groupby("hospital_origen")["cantidad"]
        .idxmax()
    ) if not df_filtrado.empty else []

    principales_destinos = df_filtrado.loc[idx, [
        "hospital_origen",
        "hospital_destino",
        "cantidad"
    ]].rename(columns={
        "hospital_destino": "principal_destino",
        "cantidad": "traslados_a_principal_destino"
    }) if len(idx) > 0 else df_filtrado.head(0)

    if not resumen.empty and not principales_destinos.empty:
        resumen = resumen.merge(
            principales_destinos,
            on="hospital_origen",
            how="left"
        )

    resumen = resumen.sort_values("total_traslados", ascending=False).reset_index(drop=True)
    top10 = resumen.head(10)

    context = {
        "regiones": df_regiones["REGION"].dropna().tolist(),
        "region_seleccionada": region,
        "tabla": resumen.to_dict(orient="records"),
        "top10_labels": json.dumps(top10["hospital_origen"].tolist(), ensure_ascii=False),
        "top10_values": json.dumps(top10["total_traslados"].tolist(), ensure_ascii=False),
    }
    return render(request, "dashboard/traslados.html", context)


def analisis_region(request, codregion):
    df_region = cargar_severidad_region()
    df_comuna = cargar_severidad_comuna()
    df_hospitales = cargar_hospitales()
    df_traslados = cargar_traslados()

    fila = df_region[df_region["codregion"] == int(codregion)].copy()
    if fila.empty:
        return render(request, "dashboard/analisis_region.html", {"encontrado": False})

    r = fila.iloc[0].to_dict()
    nombre_region = str(r["REGION"]).strip().upper()


    comunas_region = df_comuna[df_comuna["codregion"] == int(codregion)].copy()
    top_comunas = comunas_region.sort_values("alta", ascending=False).head(10)


    df_hospitales["REGION_GEO_UP"] = df_hospitales["REGION_GEO"].astype(str).str.upper()

    mapa_region = {
        "ARICA Y PARINACOTA": ["ARICA", "PARINACOTA"],
        "TARAPACA": ["TARAPACA"],
        "ANTOFAGASTA": ["ANTOFAGASTA"],
        "ATACAMA": ["ATACAMA"],
        "COQUIMBO": ["COQUIMBO"],
        "VALPARAISO": ["VALPARAISO"],
        "OHIGGINS": ["OHIGGINS", "LIBERTADOR", "BERNARDO"],
        "O HIGGINS": ["OHIGGINS", "LIBERTADOR", "BERNARDO"],
        "MAULE": ["MAULE"],
        "NUBLE": ["NUBLE"],
        "BIOBIO": ["BIOBIO"],
        "ARAUCANIA": ["ARAUCANIA"],
        "LOS RIOS": ["LOS RIOS"],
        "LOS LAGOS": ["LOS LAGOS"],
        "AYSEN": ["AYSEN", "AISEN"],
        "MAGALLANES": ["MAGALLANES"],
        "METROPOLITANA": ["METROPOLITANA", "SANTIAGO"],
    }

    claves = mapa_region.get(nombre_region, [nombre_region])

    hospitales_region = df_hospitales[
        df_hospitales["REGION_GEO_UP"].apply(
            lambda x: any(clave in x for clave in claves)
        )
    ].copy()

    top_hospitales = hospitales_region.sort_values("alta", ascending=False).head(10)


    nombres_hospitales_region = (
        hospitales_region["NOMBRE_HOSPITAL"]
        .astype(str)
        .str.strip()
        .str.upper()
        .unique()
        .tolist()
    )

    df_traslados["hospital_origen_up"] = (
        df_traslados["hospital_origen"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    tras_region = df_traslados[
        df_traslados["hospital_origen_up"].isin(nombres_hospitales_region)
    ].copy()

    total_traslados = int(tras_region["cantidad"].sum()) if not tras_region.empty else 0

    top_origenes = (
        tras_region.groupby("hospital_origen", as_index=False)["cantidad"]
        .sum()
        .sort_values("cantidad", ascending=False)
        .head(10)
    ) if not tras_region.empty else tras_region.head(0)

    context = {
        "encontrado": True,
        "region": r,
        "top_comunas": top_comunas.to_dict(orient="records"),
        "top_hospitales": top_hospitales.to_dict(orient="records"),
        "total_traslados": total_traslados,
        "top_origenes_labels": json.dumps(top_origenes["hospital_origen"].tolist(), ensure_ascii=False) if not top_origenes.empty else "[]",
        "top_origenes_values": json.dumps(top_origenes["cantidad"].tolist(), ensure_ascii=False) if not top_origenes.empty else "[]",
    }
    return render(request, "dashboard/analisis_region.html", context)


def analisis_comuna(request, cod_comuna):
    df_comuna = cargar_severidad_comuna()
    df_hospitales = cargar_hospitales()

    fila = df_comuna[df_comuna["cod_comuna"] == int(cod_comuna)].copy()
    if fila.empty:
        return render(request, "dashboard/analisis_comuna.html", {"encontrado": False})

    c = fila.iloc[0].to_dict()

    hospitales_comuna = df_hospitales[
        df_hospitales["COMUNA_GEO"].astype(str).str.upper() == str(c["COMUNA_GEOJSON"]).upper()
    ].copy()

    context = {
        "encontrado": True,
        "comuna": c,
        "hospitales": hospitales_comuna.sort_values("alta", ascending=False).to_dict(orient="records"),
    }
    return render(request, "dashboard/analisis_comuna.html", context)


def analisis_hospital(request, cod_hospital):
    df_hospitales = cargar_hospitales()
    df_traslados = cargar_traslados()

    fila = df_hospitales[df_hospitales["COD_HOSPITAL"] == int(cod_hospital)].copy()
    if fila.empty:
        return render(request, "dashboard/analisis_hospital.html", {"encontrado": False})

    h = fila.iloc[0].to_dict()

    salientes = df_traslados[df_traslados["cod_hospital_origen"] == int(cod_hospital)].copy()
    entrantes = df_traslados[df_traslados["cod_hospital_destino"] == int(cod_hospital)].copy()

    total_salientes = int(salientes["cantidad"].sum()) if not salientes.empty else 0
    total_entrantes = int(entrantes["cantidad"].sum()) if not entrantes.empty else 0

    top_destinos = (
        salientes.groupby("hospital_destino", as_index=False)["cantidad"]
        .sum()
        .sort_values("cantidad", ascending=False)
        .head(10)
    ) if not salientes.empty else salientes.head(0)

    top_origenes = (
        entrantes.groupby("hospital_origen", as_index=False)["cantidad"]
        .sum()
        .sort_values("cantidad", ascending=False)
        .head(10)
    ) if not entrantes.empty else entrantes.head(0)

    context = {
        "encontrado": True,
        "hospital": h,
        "total_salientes": total_salientes,
        "total_entrantes": total_entrantes,
        "salientes": salientes.sort_values("cantidad", ascending=False).head(20).to_dict(orient="records"),
        "entrantes": entrantes.sort_values("cantidad", ascending=False).head(20).to_dict(orient="records"),
        "top_destinos_labels": json.dumps(top_destinos["hospital_destino"].tolist(), ensure_ascii=False) if not top_destinos.empty else "[]",
        "top_destinos_values": json.dumps(top_destinos["cantidad"].tolist(), ensure_ascii=False) if not top_destinos.empty else "[]",
        "top_origenes_labels": json.dumps(top_origenes["hospital_origen"].tolist(), ensure_ascii=False) if not top_origenes.empty else "[]",
        "top_origenes_values": json.dumps(top_origenes["cantidad"].tolist(), ensure_ascii=False) if not top_origenes.empty else "[]",
    }
    return render(request, "dashboard/analisis_hospital.html", context)

def analisis_pais(request):
    df_region = cargar_severidad_region()
    df_comuna = cargar_severidad_comuna()
    df_hospitales = cargar_hospitales()
    df_traslados = cargar_traslados()

    total_poblacion = int(df_region["poblacion"].sum()) if "poblacion" in df_region.columns else 0
    total_graves = int(df_region["alta"].sum()) if "alta" in df_region.columns else 0
    total_pacientes = int(df_region["total"].sum()) if "total" in df_region.columns else 0
    total_traslados = int(df_traslados["cantidad"].sum()) if "cantidad" in df_traslados.columns else 0

    top_regiones = (
        df_region.sort_values("alta", ascending=False)
        .head(10)
        .copy()
    )

    top_comunas = (
        df_comuna.sort_values("alta", ascending=False)
        .head(10)
        .copy()
    )

    top_hospitales_graves = (
        df_hospitales.sort_values("alta", ascending=False)
        .head(10)
        .copy()
    )

    top_hospitales_trasladan = (
        df_traslados.groupby("hospital_origen", as_index=False)["cantidad"]
        .sum()
        .sort_values("cantidad", ascending=False)
        .head(10)
        .copy()
    )

    top_destinos = (
        df_traslados.groupby("hospital_destino", as_index=False)["cantidad"]
        .sum()
        .sort_values("cantidad", ascending=False)
        .head(10)
        .copy()
    )

    context = {
        "total_poblacion": total_poblacion,
        "total_graves": total_graves,
        "total_pacientes": total_pacientes,
        "total_traslados": total_traslados,

        "top_regiones": top_regiones.to_dict(orient="records"),
        "top_comunas": top_comunas.to_dict(orient="records"),
        "top_hospitales_graves": top_hospitales_graves.to_dict(orient="records"),
        "top_hospitales_trasladan": top_hospitales_trasladan.to_dict(orient="records"),
        "top_destinos": top_destinos.to_dict(orient="records"),

        "graf_regiones_labels": json.dumps(top_regiones["REGION"].tolist(), ensure_ascii=False),
        "graf_regiones_values": json.dumps(top_regiones["alta"].tolist(), ensure_ascii=False),

        "graf_comunas_labels": json.dumps(top_comunas["COMUNA_GEOJSON"].tolist(), ensure_ascii=False),
        "graf_comunas_values": json.dumps(top_comunas["alta"].tolist(), ensure_ascii=False),

        "graf_hosp_tras_labels": json.dumps(top_hospitales_trasladan["hospital_origen"].tolist(), ensure_ascii=False),
        "graf_hosp_tras_values": json.dumps(top_hospitales_trasladan["cantidad"].tolist(), ensure_ascii=False),
    }

    return render(request, "dashboard/analisis_pais.html", context)