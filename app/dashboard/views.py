import json
import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from .services.loaders import (
    cargar_severidad_region,
    cargar_severidad_comuna,
    cargar_hospitales,
    cargar_traslados,
    cargar_motivo_traslado,
)


def safe_pct(numerador, denominador):
    try:
        numerador = float(numerador)
        denominador = float(denominador)
        if denominador == 0:
            return 0
        return round((numerador / denominador) * 100, 2)
    except Exception:
        return 0


def clasificar_perfil(pct_graves, pct_traslados, umbral_graves, umbral_traslados):
    if pct_graves >= umbral_graves and pct_traslados >= umbral_traslados:
        return "Alta gravedad / alto traslado"
    if pct_graves >= umbral_graves and pct_traslados < umbral_traslados:
        return "Alta gravedad / bajo traslado"
    if pct_graves < umbral_graves and pct_traslados >= umbral_traslados:
        return "Baja gravedad / alto traslado"
    return "Menor intensidad relativa"


def texto_interpretacion_hospital(nombre_hospital, pct_graves, pct_traslados, prom_graves_pais, prom_traslados_pais):
    gravedad_arriba = pct_graves >= prom_graves_pais
    traslado_arriba = pct_traslados >= prom_traslados_pais

    if gravedad_arriba and traslado_arriba:
        return (
            f"{nombre_hospital} presenta una proporción de casos graves y una tasa de traslados "
            f"por sobre el promedio nacional. Dentro de la muestra, esto sugiere un establecimiento "
            f"con alta complejidad clínica y alta circulación de casos trasladados."
        )
    if gravedad_arriba and not traslado_arriba:
        return (
            f"{nombre_hospital} presenta una proporción de casos graves superior al promedio nacional, "
            f"pero una tasa de traslados inferior al promedio. Dentro de la muestra, esto sugiere una "
            f"mayor concentración de complejidad con menor intensidad relativa de traslado."
        )
    if not gravedad_arriba and traslado_arriba:
        return (
            f"{nombre_hospital} presenta una proporción de casos graves inferior al promedio nacional, "
            f"pero una tasa de traslados superior al promedio. Dentro de la muestra, esto sugiere un "
            f"comportamiento con mayor movimiento relativo de casos trasladados."
        )
    return (
        f"{nombre_hospital} presenta una proporción de casos graves y una tasa de traslados por debajo "
        f"del promedio nacional. Dentro de la muestra, esto lo ubica en un perfil de menor intensidad relativa."
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
    df_region = cargar_severidad_region().copy()
    df_comuna = cargar_severidad_comuna().copy()
    df_hospitales = cargar_hospitales().copy()
    df_motivo = cargar_motivo_traslado().copy()

    fila = df_region[df_region["codregion"] == int(codregion)].copy()
    if fila.empty:
        return render(request, "dashboard/analisis_region.html", {"encontrado": False})

    r = fila.iloc[0].to_dict()
    nombre_region = str(r["REGION"]).strip().upper()

    df_region["alta"] = pd.to_numeric(df_region["alta"], errors="coerce").fillna(0)
    df_region["total"] = pd.to_numeric(df_region["total"], errors="coerce").fillna(0)

    total_graves_pais = int(df_region["alta"].sum())
    total_pacientes_pais = int(df_region["total"].sum())
    total_traslados_pais = int(len(df_motivo))

    promedio_graves_pais = safe_pct(total_graves_pais, total_pacientes_pais)
    promedio_traslados_pais = safe_pct(total_traslados_pais, total_pacientes_pais)

    comunas_region = df_comuna[df_comuna["codregion"] == int(codregion)].copy()
    top_comunas = comunas_region.sort_values("alta", ascending=False).head(10)

    df_hospitales["REGION_GEO_UP"] = df_hospitales["REGION_GEO"].fillna("").astype(str).str.upper()
    df_hospitales["COD_HOSPITAL"] = pd.to_numeric(df_hospitales["COD_HOSPITAL"], errors="coerce")
    df_hospitales["total"] = pd.to_numeric(df_hospitales["total"], errors="coerce").fillna(0)
    df_hospitales["alta"] = pd.to_numeric(df_hospitales["alta"], errors="coerce").fillna(0)
    df_hospitales["porcentaje_traslado"] = pd.to_numeric(df_hospitales["porcentaje_traslado"], errors="coerce").fillna(0)

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
        df_hospitales["REGION_GEO_UP"].apply(lambda x: any(clave in x for clave in claves))
    ].copy()

    top_hospitales = hospitales_region.sort_values("alta", ascending=False).head(10)

    df_motivo["cod_hospital"] = pd.to_numeric(df_motivo["cod_hospital"], errors="coerce")
    df_motivo["severidad"] = pd.to_numeric(df_motivo["severidad"], errors="coerce")
    df_motivo["diagnostico"] = df_motivo["diagnostico"].fillna("Sin registro").astype(str)

    codigos_region = hospitales_region["COD_HOSPITAL"].dropna().astype(int).tolist()
    motivo_region = df_motivo[df_motivo["cod_hospital"].isin(codigos_region)].copy()

    total_traslados = int(len(motivo_region))
    severidad_0 = int((motivo_region["severidad"] == 0).sum())
    severidad_1 = int((motivo_region["severidad"] == 1).sum())
    severidad_2 = int((motivo_region["severidad"] == 2).sum())
    severidad_3 = int((motivo_region["severidad"] == 3).sum())

    porcentaje_sev_0 = safe_pct(severidad_0, total_traslados)
    porcentaje_sev_1 = safe_pct(severidad_1, total_traslados)
    porcentaje_sev_2 = safe_pct(severidad_2, total_traslados)
    porcentaje_sev_3 = safe_pct(severidad_3, total_traslados)

    top_diagnosticos = (
        motivo_region.groupby("diagnostico", as_index=False)
        .size()
        .rename(columns={"size": "cantidad"})
        .sort_values("cantidad", ascending=False)
        .head(10)
    ) if not motivo_region.empty else pd.DataFrame(columns=["diagnostico", "cantidad"])

    traslados_por_hospital = (
        motivo_region.groupby(["cod_hospital", "hospital"], as_index=False)
        .size()
        .rename(columns={"size": "total_traslados_registrados"})
    ) if not motivo_region.empty else pd.DataFrame(columns=["cod_hospital", "hospital", "total_traslados_registrados"])

    hospitales_region_resumen = hospitales_region[
        ["COD_HOSPITAL", "NOMBRE_HOSPITAL", "COMUNA_GEO", "REGION_GEO", "total", "alta", "porcentaje_traslado"]
    ].copy()

    hospitales_region_resumen = hospitales_region_resumen.merge(
        traslados_por_hospital,
        left_on="COD_HOSPITAL",
        right_on="cod_hospital",
        how="left"
    )

    hospitales_region_resumen["total_traslados_registrados"] = (
        pd.to_numeric(hospitales_region_resumen["total_traslados_registrados"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    hospitales_region_resumen["porcentaje_graves_hospital"] = hospitales_region_resumen.apply(
        lambda x: safe_pct(x["alta"], x["total"]), axis=1
    )
    hospitales_region_resumen["porcentaje_traslados_hospital"] = hospitales_region_resumen["porcentaje_traslado"]

    hospitales_validos = hospitales_region_resumen[hospitales_region_resumen["total"] > 0].copy()

    umbral_graves_region = round(hospitales_validos["porcentaje_graves_hospital"].median(), 2) if not hospitales_validos.empty else 0
    umbral_traslados_region = round(hospitales_validos["porcentaje_traslados_hospital"].median(), 2) if not hospitales_validos.empty else 0

    hospitales_region_resumen["perfil"] = hospitales_region_resumen.apply(
        lambda x: clasificar_perfil(
            x["porcentaje_graves_hospital"],
            x["porcentaje_traslados_hospital"],
            umbral_graves_region,
            umbral_traslados_region
        ),
        axis=1
    )

    base_ranking = hospitales_region_resumen[hospitales_region_resumen["total"] >= 20].copy()
    if base_ranking.empty:
        base_ranking = hospitales_region_resumen.copy()

    top_hospitales_normalizados = base_ranking.sort_values(
        ["porcentaje_traslados_hospital", "total_traslados_registrados"],
        ascending=False
    ).head(10)

    perfiles_region = (
        hospitales_region_resumen["perfil"]
        .value_counts()
        .reset_index()
    )
    perfiles_region.columns = ["perfil", "cantidad"]

    porcentaje_graves_region = safe_pct(r.get("alta", 0), r.get("total", 0))
    porcentaje_traslados_region = safe_pct(total_traslados, r.get("total", 0))

    diferencia_graves_vs_pais = round(porcentaje_graves_region - promedio_graves_pais, 2)
    diferencia_traslados_vs_pais = round(porcentaje_traslados_region - promedio_traslados_pais, 2)

    context = {
        "encontrado": True,
        "region": r,
        "top_comunas": top_comunas.to_dict(orient="records"),
        "top_hospitales": top_hospitales.to_dict(orient="records"),
        "hospitales_region_resumen": hospitales_region_resumen.sort_values(
            ["porcentaje_traslados_hospital", "alta"], ascending=False
        ).to_dict(orient="records"),
        "top_hospitales_normalizados": top_hospitales_normalizados.to_dict(orient="records"),
        "total_hospitales_region": int(len(hospitales_validos)),
        "total_traslados": total_traslados,
        "severidad_0": severidad_0,
        "severidad_1": severidad_1,
        "severidad_2": severidad_2,
        "severidad_3": severidad_3,
        "porcentaje_sev_0": porcentaje_sev_0,
        "porcentaje_sev_1": porcentaje_sev_1,
        "porcentaje_sev_2": porcentaje_sev_2,
        "porcentaje_sev_3": porcentaje_sev_3,
        "top_diagnosticos": top_diagnosticos.to_dict(orient="records"),
        "porcentaje_graves_region": porcentaje_graves_region,
        "porcentaje_traslados_region": porcentaje_traslados_region,
        "promedio_graves_pais": promedio_graves_pais,
        "promedio_traslados_pais": promedio_traslados_pais,
        "diferencia_graves_vs_pais": diferencia_graves_vs_pais,
        "diferencia_traslados_vs_pais": diferencia_traslados_vs_pais,
        "graf_region_labels": json.dumps(top_hospitales_normalizados["NOMBRE_HOSPITAL"].tolist(), ensure_ascii=False) if not top_hospitales_normalizados.empty else "[]",
        "graf_region_values": json.dumps(top_hospitales_normalizados["porcentaje_traslados_hospital"].tolist(), ensure_ascii=False) if not top_hospitales_normalizados.empty else "[]",
        "graf_perfiles_labels": json.dumps(perfiles_region["perfil"].tolist(), ensure_ascii=False) if not perfiles_region.empty else "[]",
        "graf_perfiles_values": json.dumps(perfiles_region["cantidad"].tolist(), ensure_ascii=False) if not perfiles_region.empty else "[]",
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
    df_hospitales = cargar_hospitales().copy()
    df_motivo = cargar_motivo_traslado().copy()
    df_region = cargar_severidad_region().copy()

    df_hospitales["COD_HOSPITAL"] = pd.to_numeric(df_hospitales["COD_HOSPITAL"], errors="coerce")
    df_hospitales["total"] = pd.to_numeric(df_hospitales["total"], errors="coerce").fillna(0)
    df_hospitales["alta"] = pd.to_numeric(df_hospitales["alta"], errors="coerce").fillna(0)
    df_hospitales["porcentaje_traslado"] = pd.to_numeric(df_hospitales["porcentaje_traslado"], errors="coerce").fillna(0)

    fila = df_hospitales[df_hospitales["COD_HOSPITAL"] == int(cod_hospital)].copy()
    if fila.empty:
        return render(request, "dashboard/analisis_hospital.html", {"encontrado": False})

    h = fila.iloc[0].to_dict()

    df_motivo["cod_hospital"] = pd.to_numeric(df_motivo["cod_hospital"], errors="coerce")
    df_motivo["severidad"] = pd.to_numeric(df_motivo["severidad"], errors="coerce")
    df_motivo["diagnostico"] = df_motivo["diagnostico"].fillna("Sin registro").astype(str)
    df_motivo["procedimiento"] = df_motivo["procedimiento"].fillna("Sin registro").astype(str)

    motivo_hospital = df_motivo[df_motivo["cod_hospital"] == int(cod_hospital)].copy()

    total_traslados = int(len(motivo_hospital))
    severidad_0 = int((motivo_hospital["severidad"] == 0).sum())
    severidad_1 = int((motivo_hospital["severidad"] == 1).sum())
    severidad_2 = int((motivo_hospital["severidad"] == 2).sum())
    severidad_3 = int((motivo_hospital["severidad"] == 3).sum())

    porcentaje_sev_0 = safe_pct(severidad_0, total_traslados)
    porcentaje_sev_1 = safe_pct(severidad_1, total_traslados)
    porcentaje_sev_2 = safe_pct(severidad_2, total_traslados)
    porcentaje_sev_3 = safe_pct(severidad_3, total_traslados)

    top_diagnosticos = (
        motivo_hospital.groupby("diagnostico", as_index=False)
        .size()
        .rename(columns={"size": "cantidad"})
        .sort_values("cantidad", ascending=False)
        .head(10)
    ) if not motivo_hospital.empty else pd.DataFrame(columns=["diagnostico", "cantidad"])

    top_procedimientos = (
        motivo_hospital.groupby("procedimiento", as_index=False)
        .size()
        .rename(columns={"size": "cantidad"})
        .sort_values("cantidad", ascending=False)
        .head(10)
    ) if not motivo_hospital.empty else pd.DataFrame(columns=["procedimiento", "cantidad"])

    df_region["alta"] = pd.to_numeric(df_region["alta"], errors="coerce").fillna(0)
    df_region["total"] = pd.to_numeric(df_region["total"], errors="coerce").fillna(0)

    total_graves_pais = int(df_region["alta"].sum())
    total_pacientes_pais = int(df_region["total"].sum())
    total_traslados_pais = int(len(df_motivo))

    prom_graves = safe_pct(total_graves_pais, total_pacientes_pais)
    prom_traslados = safe_pct(total_traslados_pais, total_pacientes_pais)

    total = h.get("total", 0)
    graves = h.get("alta", 0)

    pct_graves = safe_pct(graves, total)
    pct_traslados = h.get("porcentaje_traslado", 0)

    interpretacion = texto_interpretacion_hospital(
        h.get("NOMBRE_HOSPITAL", ""),
        pct_graves,
        pct_traslados,
        prom_graves,
        prom_traslados
    )

    context = {
        "encontrado": True,
        "hospital": h,
        "total_traslados": total_traslados,
        "severidad_0": severidad_0,
        "severidad_1": severidad_1,
        "severidad_2": severidad_2,
        "severidad_3": severidad_3,
        "porcentaje_sev_0": porcentaje_sev_0,
        "porcentaje_sev_1": porcentaje_sev_1,
        "porcentaje_sev_2": porcentaje_sev_2,
        "porcentaje_sev_3": porcentaje_sev_3,
        "top_diagnosticos": top_diagnosticos.to_dict(orient="records"),
        "top_procedimientos": top_procedimientos.to_dict(orient="records"),
        "pct_graves": pct_graves,
        "pct_traslados": pct_traslados,
        "prom_graves": prom_graves,
        "prom_traslados": prom_traslados,
        "interpretacion": interpretacion,
    }
    return render(request, "dashboard/analisis_hospital.html", context)


def analisis_pais(request):
    df_region = cargar_severidad_region().copy()
    df_comuna = cargar_severidad_comuna().copy()
    df_hospitales = cargar_hospitales().copy()
    df_motivo = cargar_motivo_traslado().copy()

    df_region["alta"] = pd.to_numeric(df_region["alta"], errors="coerce").fillna(0)
    df_region["total"] = pd.to_numeric(df_region["total"], errors="coerce").fillna(0)

    df_hospitales["COD_HOSPITAL"] = pd.to_numeric(df_hospitales["COD_HOSPITAL"], errors="coerce")
    df_hospitales["total"] = pd.to_numeric(df_hospitales["total"], errors="coerce").fillna(0)
    df_hospitales["alta"] = pd.to_numeric(df_hospitales["alta"], errors="coerce").fillna(0)
    df_hospitales["porcentaje_traslado"] = pd.to_numeric(df_hospitales["porcentaje_traslado"], errors="coerce").fillna(0)

    df_motivo = df_motivo[df_motivo['año'] == 2024]
    df_motivo["cod_hospital"] = pd.to_numeric(df_motivo["cod_hospital"], errors="coerce")
    df_motivo["severidad"] = pd.to_numeric(df_motivo["severidad"], errors="coerce")
    df_motivo["diagnostico"] = df_motivo["diagnostico"].fillna("Sin registro").astype(str)

    total_poblacion = int(df_region["poblacion"].sum()) if "poblacion" in df_region.columns else 0
    total_graves = int(df_region["alta"].sum())
    total_pacientes = int(df_region["total"].sum())
    total_traslados = int(len(df_motivo))

    promedio_graves = safe_pct(total_graves, total_pacientes)
    promedio_traslados = safe_pct(total_traslados, total_pacientes)

    top_regiones = df_region.sort_values("alta", ascending=False).head(10).copy()
    top_comunas = df_comuna.sort_values("alta", ascending=False).head(10).copy()
    top_hospitales_graves = df_hospitales.sort_values("alta", ascending=False).head(10).copy()

    traslados_por_hospital = (
        df_motivo.groupby(["cod_hospital", "hospital"], as_index=False)
        .size()
        .rename(columns={"size": "traslados"})
    ) if not df_motivo.empty else pd.DataFrame(columns=["cod_hospital", "hospital", "traslados"])

    hospitales = df_hospitales.copy()

    hospitales["pct_graves"] = hospitales.apply(lambda x: safe_pct(x["alta"], x["total"]), axis=1)
    hospitales["pct_traslados"] = hospitales["porcentaje_traslado"]
    hospitales["pct_traslados"] = hospitales["porcentaje_traslado"]

    umbral_graves = hospitales["pct_graves"].median() if not hospitales.empty else 0
    umbral_traslados = hospitales["pct_traslados"].median() if not hospitales.empty else 0

    hospitales["perfil"] = hospitales.apply(
        lambda x: clasificar_perfil(x["pct_graves"], x["pct_traslados"], umbral_graves, umbral_traslados),
        axis=1
    )

    perfiles = hospitales["perfil"].value_counts().reset_index()
    perfiles.columns = ["perfil", "cantidad"]

    top_hospitales_normalizados = hospitales[hospitales["total"] >= 20].copy()
    if top_hospitales_normalizados.empty:
        top_hospitales_normalizados = hospitales.copy()

    top_hospitales_normalizados = top_hospitales_normalizados.sort_values(
        ["pct_traslados", "total"], ascending=False
    ).head(10)

    top_diagnosticos = (
        df_motivo.groupby("diagnostico", as_index=False)
        .size()
        .rename(columns={"size": "cantidad"})
        .sort_values("cantidad", ascending=False)
        .head(10)
        .copy()
    ) if not df_motivo.empty else pd.DataFrame(columns=["diagnostico", "cantidad"])

    severidad_0 = int((df_motivo["severidad"] == 0).sum())
    severidad_1 = int((df_motivo["severidad"] == 1).sum())
    severidad_2 = int((df_motivo["severidad"] == 2).sum())
    severidad_3 = int((df_motivo["severidad"] == 3).sum())

    porcentaje_sev_0 = safe_pct(severidad_0, total_traslados)
    porcentaje_sev_1 = safe_pct(severidad_1, total_traslados)
    porcentaje_sev_2 = safe_pct(severidad_2, total_traslados)
    porcentaje_sev_3 = safe_pct(severidad_3, total_traslados)

    context = {
        "total_poblacion": total_poblacion,
        "total_graves": total_graves,
        "total_pacientes": total_pacientes,
        "total_traslados": total_traslados,
        "promedio_graves": promedio_graves,
        "promedio_traslados": promedio_traslados,
        "severidad_0": severidad_0,
        "severidad_1": severidad_1,
        "severidad_2": severidad_2,
        "severidad_3": severidad_3,
        "porcentaje_sev_0": porcentaje_sev_0,
        "porcentaje_sev_1": porcentaje_sev_1,
        "porcentaje_sev_2": porcentaje_sev_2,
        "porcentaje_sev_3": porcentaje_sev_3,
        "top_regiones": top_regiones.to_dict(orient="records"),
        "top_comunas": top_comunas.to_dict(orient="records"),
        "top_hospitales_graves": top_hospitales_graves.to_dict(orient="records"),
        "top_hospitales_normalizados": top_hospitales_normalizados.to_dict(orient="records"),
        "top_diagnosticos": top_diagnosticos.to_dict(orient="records"),
        "perfiles": perfiles.to_dict(orient="records"),
        "graf_regiones_labels": json.dumps(top_regiones["REGION"].tolist(), ensure_ascii=False),
        "graf_regiones_values": json.dumps(top_regiones["alta"].tolist(), ensure_ascii=False),
        "graf_comunas_labels": json.dumps(top_comunas["COMUNA_GEOJSON"].tolist(), ensure_ascii=False),
        "graf_comunas_values": json.dumps(top_comunas["alta"].tolist(), ensure_ascii=False),
        "graf_hosp_labels": json.dumps(top_hospitales_normalizados["NOMBRE_HOSPITAL"].tolist(), ensure_ascii=False) if not top_hospitales_normalizados.empty else "[]",
        "graf_hosp_values": json.dumps(top_hospitales_normalizados["pct_traslados"].tolist(), ensure_ascii=False) if not top_hospitales_normalizados.empty else "[]",
        "graf_perfiles_labels": json.dumps(perfiles["perfil"].tolist(), ensure_ascii=False) if not perfiles.empty else "[]",
        "graf_perfiles_values": json.dumps(perfiles["cantidad"].tolist(), ensure_ascii=False) if not perfiles.empty else "[]",
    }

    return render(request, "dashboard/analisis_pais.html", context)
