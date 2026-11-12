"""Genera el panel agregado desde los archivos originales del DANE."""
import argparse
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
from openpyxl import load_workbook


ARCHIVOS = {
    2020: ("nac2020.zip", "nac2020.csv"),
    2021: ("nacimientos2021.zip", "nac2021.csv"),
    2022: ("nac2022.zip", "nac2022.csv"),
    2023: ("BD-EEVV-Nacimientos-2023.zip", "BD-EEVV-Nacimientos-2023.csv"),
}
TOTALES = {2020: 629402, 2021: 616914, 2022: 573625, 2023: 515549, 2024: 453901, 2025: 441537}


def contar_microdatos(anio, carpeta):
    nombre_zip, nombre_csv = ARCHIVOS[anio]
    with ZipFile(carpeta / nombre_zip) as archivo, archivo.open(nombre_csv) as fuente:
        registros = pd.read_csv(
            fuente, encoding="cp1252", usecols=["ANO", "COD_DPTO"],
            dtype={"COD_DPTO": str},
        )
    if not registros["ANO"].eq(anio).all() or registros["COD_DPTO"].isna().any():
        raise ValueError(f"Año o código de ocurrencia inválido en {nombre_zip}")
    return registros["COD_DPTO"].value_counts().to_dict()


def leer_cuadro(anio, carpeta):
    libro = load_workbook(carpeta / f"{anio}.xlsx", read_only=True, data_only=True)
    try:
        cuadro = libro["Cuadro2"]
        if "ocurrencia" not in cuadro["C4"].value or cuadro["E10"].value != TOTALES[anio]:
            raise ValueError(f"El Cuadro 2 de {anio} no coincide con la fuente esperada")
        filas = [
            (str(codigo).zfill(2), nombre.split(" ", 1)[1], total)
            for codigo, _, nombre, tipo, total in cuadro.iter_rows(min_row=11, max_col=5, values_only=True)
            if tipo == "Total Dpto"
        ]
    finally:
        libro.close()
    if len(filas) != 33 or len({codigo for codigo, _, _ in filas}) != 33:
        raise ValueError(f"Cobertura territorial inesperada en {anio}")
    return filas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("microdatos", type=Path)
    parser.add_argument("cuadros", type=Path)
    args = parser.parse_args()
    cuadros = {anio: leer_cuadro(anio, args.cuadros) for anio in (2024, 2025)}
    nombres = {codigo: nombre for codigo, nombre, _ in cuadros[2025]}
    historico = {anio: contar_microdatos(anio, args.microdatos) for anio in ARCHIVOS}
    historico.update({
        anio: {codigo: total for codigo, _, total in filas}
        for anio, filas in cuadros.items()
    })
    filas = []
    for anio, totales in historico.items():
        if totales.keys() != nombres.keys() or sum(totales.values()) != TOTALES[anio]:
            raise ValueError(f"Cobertura o total inesperado en {anio}")
        filas.extend((anio, codigo, nombres[codigo], total) for codigo, total in sorted(totales.items()))
    datos = pd.DataFrame(filas, columns=["anio", "codigo_dpto", "departamento", "nacimientos"])
    destino = Path(__file__).resolve().parent / "data" / "nacimientos_departamento.csv"
    datos.to_csv(destino, index=False, lineterminator="\n")


if __name__ == "__main__":
    main()
