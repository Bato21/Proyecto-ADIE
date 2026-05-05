import pandas as pd
from django.conf import settings

def cargar_severidad_region():
    ruta = settings.DATA_DIR / "severidad_region.csv"
    return pd.read_csv(ruta)

def cargar_severidad_comuna():
    ruta = settings.DATA_DIR / "severidad_comuna.csv"
    return pd.read_csv(ruta)

def cargar_hospitales():
    ruta = settings.DATA_DIR / "hospitales.csv"
    return pd.read_csv(ruta)

def cargar_traslados():
    ruta = settings.DATA_DIR / "traslados.csv"
    return pd.read_csv(ruta)

def cargar_motivo_traslado():
    ruta = settings.DATA_DIR / "motivo_traslado.csv"
    return pd.read_csv(ruta)

def cargar_CIE9():
    ruta = settings.DATA_DIR / "CIE-9.xlsx"
    return pd.read_excel(ruta)

def cargar_CIE10():
    ruta = settings.DATA_DIR / "CIE-10.xlsx"
    return pd.read_excel(ruta)
