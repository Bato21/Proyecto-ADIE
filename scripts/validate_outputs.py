from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd

REQUIRED_FILES: dict[str, list[str]] = {
    "severidad_region.csv": [
        "codregion",
        "REGION",
        "total",
        "alta",
    ],
    "severidad_comuna.csv": [
        "codregion",
        "cod_comuna",
        "COMUNA_GEOJSON",
        "total",
        "alta",
    ],
    "hospitales.csv": [
        "COD_HOSPITAL",
        "NOMBRE_HOSPITAL",
        "total",
    ],
    "traslados.csv": [
        "cantidad",
    ],
    "motivo_traslado.csv": [
        "cod_hospital",
        "diagnostico",
    ],
}

ALTERNATIVE_REQUIRED_COLUMNS: dict[str, list[list[str]]] = {
    "traslados.csv": [
        ["cod_origen", "cod_destino"],
        ["cod_hospital_origen", "cod_hospital_destino"],
    ]
}


class ValidationError(Exception):
    """Raised when processed outputs do not satisfy required invariants."""


def _assert_columns(df: pd.DataFrame, expected: Iterable[str], file_name: str) -> None:
    missing = [column for column in expected if column not in df.columns]
    if missing:
        raise ValidationError(f"{file_name}: faltan columnas obligatorias: {', '.join(missing)}")


def _assert_positive_rows(df: pd.DataFrame, file_name: str) -> None:
    if df.empty:
        raise ValidationError(f"{file_name}: el archivo existe pero está vacío")


def _assert_alternative_columns(df: pd.DataFrame, file_name: str) -> None:
    alternatives = ALTERNATIVE_REQUIRED_COLUMNS.get(file_name, [])
    if not alternatives:
        return

    for option in alternatives:
        if all(column in df.columns for column in option):
            return

    pretty_options = [" + ".join(option) for option in alternatives]
    raise ValidationError(
        f"{file_name}: no cumple ninguna opción de columnas alternativas: {' | '.join(pretty_options)}"
    )


def _assert_metric_consistency(severidad_region: pd.DataFrame) -> None:
    total_cases = pd.to_numeric(severidad_region["total"], errors="coerce").sum()
    total_high = pd.to_numeric(severidad_region["alta"], errors="coerce").sum()

    if total_cases <= 0:
        raise ValidationError("severidad_region.csv: suma de total debe ser mayor a 0")
    if total_high < 0:
        raise ValidationError("severidad_region.csv: suma de alta no puede ser negativa")
    if total_high > total_cases:
        raise ValidationError("severidad_region.csv: suma de alta no puede superar suma de total")


def validate_processed_dir(processed_dir: Path) -> None:
    if not processed_dir.exists():
        raise ValidationError(f"No existe la carpeta de procesados: {processed_dir}")

    loaded: dict[str, pd.DataFrame] = {}

    for file_name, expected_columns in REQUIRED_FILES.items():
        file_path = processed_dir / file_name
        if not file_path.exists():
            raise ValidationError(f"Falta archivo obligatorio: {file_path}")

        df = pd.read_csv(file_path)
        _assert_positive_rows(df, file_name)
        _assert_columns(df, expected_columns, file_name)
        _assert_alternative_columns(df, file_name)
        loaded[file_name] = df

    _assert_metric_consistency(loaded["severidad_region.csv"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida integridad mínima de artefactos en data/processed."
    )
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Ruta a carpeta con CSV procesados (default: data/processed).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    processed_dir = Path(args.processed_dir).resolve()

    try:
        validate_processed_dir(processed_dir)
    except ValidationError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"OK: validación de artefactos completada en {processed_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
