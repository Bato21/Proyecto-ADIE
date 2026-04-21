from __future__ import annotations

import csv
import glob
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

RAW_COLUMNS = [
    "CIP_ENCRIPTADO",
    "COD_HOSPITAL",
    "COMUNA",
    "PROVINCIA",
    "TIPO_PROCEDENCIA",
    "FECHA_INGRESO",
    "FECHAALTA",
    "TIPOALTA",
    "DIAGNOSTICO1",
    "PROCEDIMIENTO1",
    "USOSPABELLON",
    "IR_29301_PESO",
    "IR_29301_SEVERIDAD",
    "IR_29301_MORTALIDAD",
    "HOSPPROCEDENCIA",
]

PROVINCIA_REGION = {
    "ARICA": "ARICA Y PARINACOTA",
    "PARINACOTA": "ARICA Y PARINACOTA",
    "IQUIQUE": "TARAPACA",
    "TAMARUGAL": "TARAPACA",
    "ANTOFAGASTA": "ANTOFAGASTA",
    "EL LOA": "ANTOFAGASTA",
    "TOCOPILLA": "ANTOFAGASTA",
    "CHAÑARAL": "ATACAMA",
    "COPIAPO": "ATACAMA",
    "HUASCO": "ATACAMA",
    "ELQUI": "COQUIMBO",
    "LIMARI": "COQUIMBO",
    "CHOAPA": "COQUIMBO",
    "VALPARAISO": "VALPARAISO",
    "SAN ANTONIO": "VALPARAISO",
    "QUILLOTA": "VALPARAISO",
    "PETORCA": "VALPARAISO",
    "LOS ANDES": "VALPARAISO",
    "SAN FELIPE": "VALPARAISO",
    "ISLA DE PASCUA": "VALPARAISO",
    "SANTIAGO": "METROPOLITANA",
    "CORDILLERA": "METROPOLITANA",
    "MAIPO": "METROPOLITANA",
    "MELIPILLA": "METROPOLITANA",
    "TALAGANTE": "METROPOLITANA",
    "CACHAPOAL": "O’HIGGINS",
    "COLCHAGUA": "O’HIGGINS",
    "CARDENAL CARO": "O’HIGGINS",
    "CURICO": "MAULE",
    "TALCA": "MAULE",
    "LINARES": "MAULE",
    "CAUQUENES": "MAULE",
    "DIGUILLIN": "ÑUBLE",
    "PUNILLA": "ÑUBLE",
    "ITATA": "ÑUBLE",
    "CONCEPCION": "BIOBIO",
    "BIO-BIO": "BIOBIO",
    "ARAUCO": "BIOBIO",
    "MALLECO": "LA ARAUCANIA",
    "CAUTIN": "LA ARAUCANIA",
    "VALDIVIA": "LOS RIOS",
    "RANCO": "LOS RIOS",
    "OSORNO": "LOS LAGOS",
    "LLANQUIHUE": "LOS LAGOS",
    "CHILOE": "LOS LAGOS",
    "PALENA": "LOS LAGOS",
    "AYSEN": "AYSEN",
    "COYHAIQUE": "AYSEN",
    "CAPITAN PRAT": "AYSEN",
    "GENERAL CARRERA": "AYSEN",
    "MAGALLANES": "MAGALLANES",
    "ULTIMA ESPERANZA": "MAGALLANES",
    "TIERRA DEL FUEGO": "MAGALLANES",
    "ANTARTICA": "MAGALLANES",
}

REGION_CODES = {
    "ARICA Y PARINACOTA": 15,
    "TARAPACA": 1,
    "ANTOFAGASTA": 2,
    "ATACAMA": 3,
    "COQUIMBO": 4,
    "VALPARAISO": 5,
    "METROPOLITANA": 13,
    "O’HIGGINS": 6,
    "O'HIGGINS": 6,
    "MAULE": 7,
    "ÑUBLE": 16,
    "BIOBIO": 8,
    "LA ARAUCANIA": 9,
    "LOS RIOS": 14,
    "LOS LAGOS": 10,
    "AYSEN": 11,
    "MAGALLANES": 12,
}


def find_project_root(start: Path | str | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "app").exists() and (candidate / "data").exists():
            return candidate
    return current


def normalize_text(text: object) -> str:
    if pd.isna(text):
        return ""
    normalized = str(text).upper().strip()
    normalized = "".join(
        character
        for character in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(character)
    )
    normalized = re.sub(r"[^A-Z0-9 ]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def find_grd_files(root: Path | None = None) -> list[Path]:
    root = Path(root or find_project_root())
    patterns = [
        root / "*.txt",
        root / "data" / "archivosDuros" / "*.txt",
        root / "data" / "raw" / "*.txt",
        root / "data" / "raw" / "**" / "*.txt",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(Path(path) for path in glob.glob(str(pattern), recursive=True))
    unique_files = sorted({path.resolve() for path in files if path.is_file()})
    if not unique_files:
        raise FileNotFoundError(
            "No se encontraron archivos GRD .txt en las rutas esperadas."
        )
    return unique_files


def read_grd_file(path: Path) -> pd.DataFrame:
    for encoding in ("utf-16", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(
                path,
                sep="|",
                decimal=",",
                encoding=encoding,
                quoting=csv.QUOTE_NONE,
                usecols=RAW_COLUMNS,
                index_col=False,
                on_bad_lines="warn",
                low_memory=False,
            )
        except UnicodeError:
            continue
    raise ValueError(f"No se pudo leer el archivo {path}")


def load_grd_base(root: Path | None = None) -> pd.DataFrame:
    files = find_grd_files(root)
    frames = []
    for file_path in files:
        frames.append(read_grd_file(file_path))
    return pd.concat(frames, ignore_index=True)


def clean_2024(df: pd.DataFrame) -> pd.DataFrame:
    df_2024 = df[df["FECHA_INGRESO"].astype(str).str.startswith("2024-")].copy()
    df_2024["FECHA_INGRESO"] = pd.to_datetime(
        df_2024["FECHA_INGRESO"], format="%Y-%m-%d", errors="coerce"
    )
    df_2024["FECHAALTA"] = pd.to_datetime(
        df_2024["FECHAALTA"], format="%Y-%m-%d", errors="coerce"
    )
    df_2024["IR_29301_SEVERIDAD"] = pd.to_numeric(
        df_2024["IR_29301_SEVERIDAD"], errors="coerce"
    )
    df_2024["IR_29301_MORTALIDAD"] = pd.to_numeric(
        df_2024["IR_29301_MORTALIDAD"], errors="coerce"
    )
    df_2024["IR_29301_PESO"] = (
        df_2024["IR_29301_PESO"].astype(str).str.replace(",", ".", regex=False).str.strip()
    )
    df_2024["IR_29301_PESO"] = pd.to_numeric(df_2024["IR_29301_PESO"], errors="coerce")
    df_2024["PROVINCIA"] = df_2024["PROVINCIA"].astype(str).str.upper().str.strip()
    df_2024["REGION"] = df_2024["PROVINCIA"].map(PROVINCIA_REGION)
    df_2024["PROVINCIA"] = df_2024["PROVINCIA"].replace(
        {"DIGUILL�N": "DIGUILLIN", "DIGUILLÍN": "DIGUILLIN"}
    )
    df_2024["codregion"] = df_2024["REGION"].map(REGION_CODES)
    df_2024 = df_2024.drop_duplicates().copy()
    df_2024["ALTA_SEVERIDAD"] = df_2024["IR_29301_SEVERIDAD"] >= 3
    return df_2024


def load_hospital_catalog(root: Path | None = None) -> pd.DataFrame:
    root = Path(root or find_project_root())
    raw_xlsx = root / "data" / "archivosDuros" / "Tablas maestras bases GRD  (1).xlsx"
    processed_csv = root / "data" / "processed" / "hospitales.csv"
    if raw_xlsx.exists():
        df = pd.read_excel(raw_xlsx)
        df = df.rename(columns={"HOSPITALES": "COD_HOSPITAL", "Unnamed: 1": "NOMBRE_HOSPITAL"})
        df["COD_HOSPITAL"] = pd.to_numeric(df["COD_HOSPITAL"], errors="coerce")
        return df
    if processed_csv.exists():
        df = pd.read_csv(processed_csv)
        if "NOMBRE_HOSPITAL" not in df.columns and "hospital" in df.columns:
            df = df.rename(columns={"hospital": "NOMBRE_HOSPITAL"})
        return df
    raise FileNotFoundError("No se encontró la tabla maestra de hospitales ni hospitales.csv.")


def load_population_comuna(root: Path | None = None) -> pd.DataFrame:
    root = Path(root or find_project_root())
    path = root / "data" / "processed" / "poblacion_comuna_censo2024.csv"
    if not path.exists():
        raise FileNotFoundError("No se encontró poblacion_comuna_censo2024.csv en data/processed.")
    return pd.read_csv(path)


def load_geojson_regions(root: Path | None = None) -> tuple[dict, dict]:
    root = Path(root or find_project_root())
    geo_dir = root / "data" / "processed" / "geojson"
    chile_path = geo_dir / "chile_regiones.geojson"
    if not chile_path.exists():
        raise FileNotFoundError("No se encontró chile_regiones.geojson en data/processed/geojson.")
    with open(chile_path, "r", encoding="utf-8") as handle:
        chile = json.load(handle)
    regiones: dict[int, dict] = {}
    for path in sorted(geo_dir.glob("region_*.geojson")):
        try:
            code = int(path.stem.split("_")[1])
        except (IndexError, ValueError):
            continue
        with open(path, "r", encoding="utf-8") as handle:
            regiones[code] = json.load(handle)
    return chile, regiones


def build_region_summary(df_2024: pd.DataFrame, population_comuna: pd.DataFrame | None = None) -> pd.DataFrame:
    resumen_region = df_2024.groupby("REGION").agg(
        total=("CIP_ENCRIPTADO", "count"),
        alta=("ALTA_SEVERIDAD", "sum"),
    ).reset_index()
    resumen_region["porcentaje"] = resumen_region["alta"] / resumen_region["total"] * 100
    resumen_region["codregion"] = resumen_region["REGION"].map(REGION_CODES)
    if population_comuna is not None:
        poblacion_region = (
            population_comuna.groupby("region")["poblacion"].sum().reset_index().rename(columns={"region": "codregion"})
        )
        resumen_region = resumen_region.merge(poblacion_region, on="codregion", how="left")
        resumen_region["porcentaje_severidad"] = resumen_region["porcentaje"]
        resumen_region["porcentaje_poblacion"] = (resumen_region["alta"] / resumen_region["poblacion"]) * 100
        resumen_region["tasa_100k"] = (resumen_region["alta"] / resumen_region["poblacion"]) * 100000
    return resumen_region
