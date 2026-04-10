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
    traslados = df.to_dict(orient="records")
    return JsonResponse({"traslados": traslados})


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

    resumen["porcentaje_graves"] = (
        resumen["total_graves"] / resumen["total_traslados"] * 100
    ).round(2)

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

    resumen = resumen.sort_values(
        "total_traslados",
        ascending=False
    ).reset_index(drop=True)

    top10 = resumen.head(10)

    context = {
        "regiones": df_regiones["REGION"].dropna().tolist(),
        "region_seleccionada": region,
        "tabla": resumen.to_dict(orient="records"),
        "top10_labels": json.dumps(top10["hospital_origen"].tolist(), ensure_ascii=False),
        "top10_values": json.dumps(top10["total_traslados"].tolist(), ensure_ascii=False),
    }

    return render(request, "dashboard/traslados.html", context)