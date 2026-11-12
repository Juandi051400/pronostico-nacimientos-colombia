"""Evalúa pronósticos anuales y estima los nacimientos de 2026."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error


ROOT = Path(__file__).resolve().parent
ENTRADAS = ["anio", "nacimientos_previos"]
ANIOS_PRUEBA = (2023, 2024, 2025)
MODELOS = {
    "ingenuo": None,
    "regresion_lineal": LinearRegression,
    "bosque_aleatorio": lambda: RandomForestRegressor(n_estimators=100, random_state=42),
}


def cargar_panel():
    datos = pd.read_csv(ROOT / "data/nacimientos_departamento.csv", dtype={"codigo_dpto": str})
    cobertura = datos.groupby("anio")["codigo_dpto"].agg(set)
    if (
        list(cobertura.index) != list(range(2020, 2026))
        or len(cobertura.iloc[0]) != 33
        or any(codigos != cobertura.iloc[0] for codigos in cobertura)
        or datos.duplicated(["anio", "codigo_dpto"]).any()
        or not datos["nacimientos"].gt(0).all()
    ):
        raise ValueError("Se requieren 33 territorios por año y conteos positivos para 2020–2025")
    return datos.sort_values(["codigo_dpto", "anio"])


def estimar(datos, anio, modelo):
    panel = datos.assign(nacimientos_previos=datos.groupby("codigo_dpto")["nacimientos"].shift())
    entrenamiento = panel.loc[(panel["anio"] < anio) & panel["nacimientos_previos"].notna()]
    objetivo = datos.loc[datos["anio"].eq(anio - 1), ["codigo_dpto", "departamento", "nacimientos"]]
    objetivo = objetivo.rename(columns={"nacimientos": "nacimientos_previos"}).assign(anio=anio)
    previos = objetivo["nacimientos_previos"]
    factor = 1.0
    if modelo is not None:
        y = entrenamiento["nacimientos"] / entrenamiento["nacimientos_previos"]
        factor = modelo().fit(entrenamiento[ENTRADAS], y).predict(objetivo[ENTRADAS])
    return objetivo.assign(estimacion=np.rint(np.maximum(previos * factor, 0)).astype(int))


def evaluar(datos):
    metricas = []
    for anio in ANIOS_PRUEBA:
        observado = datos.loc[datos["anio"].eq(anio), ["codigo_dpto", "nacimientos"]]
        for nombre, modelo in MODELOS.items():
            prueba = estimar(datos, anio, modelo).merge(observado, on="codigo_dpto", validate="one_to_one")
            real, estimado = prueba["nacimientos"], prueba["estimacion"]
            error = estimado.sum() - real.sum()
            metricas.append({
                "anio": anio, "modelo": nombre, "observado_nacional": real.sum(),
                "estimado_nacional": estimado.sum(), "error_nacional": error,
                "error_nacional_pct": 100 * error / real.sum(),
                "mae_territorial": mean_absolute_error(real, estimado),
                "rmse_territorial": root_mean_squared_error(real, estimado),
                "r2_territorial": r2_score(real, estimado),
            })
    return pd.DataFrame(metricas)


def graficar(serie, estimado, ruta):
    anio = int(serie.index[-1])
    fig, ax = plt.subplots(figsize=(9.6, 4.6), layout="constrained")
    ax.plot(serie.index, serie.values, "o-", color="#075985", lw=2.4, label="DANE · datos definitivos")
    ax.plot([anio, anio + 1], [serie.iloc[-1], estimado], "o--", color="#a44a12",
            lw=2.4, label=f"Pronóstico {anio + 1}")
    ax.annotate(f"{estimado:,}".replace(",", "."), (anio + 1, estimado),
                xytext=(0, 12), textcoords="offset points", ha="center",
                color="#a44a12", fontweight="bold")
    ax.set(title="Nacidos vivos en Colombia", ylabel="Nacimientos", xticks=range(2020, anio + 2))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", ".")))
    ax.margins(x=0.08, y=0.18)
    ax.grid(axis="y", color="#dbe4ea")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.savefig(ruta, dpi=150, facecolor="white")
    plt.close(fig)


def main():
    datos = cargar_panel()
    destino = ROOT / "resultados"
    destino.mkdir(exist_ok=True)
    metricas = evaluar(datos)
    seleccion = metricas.groupby("modelo")["mae_territorial"].mean().idxmin()
    pronostico = estimar(datos, 2026, MODELOS[seleccion])
    pronostico = pronostico.sort_values("estimacion", ascending=False)
    totales = datos.groupby("anio")["nacimientos"].sum()
    parcial = pd.read_csv(ROOT / "data/nacimientos_enero_julio.csv").set_index("anio")["nacimientos"]
    estimacion_corte = round(totales[2025] * parcial[2026] / parcial[2025])
    escenarios = [
        {"metodo": nombre, "estimacion_nacional": estimar(datos, 2026, modelo)["estimacion"].sum()}
        for nombre, modelo in MODELOS.items()
    ]
    escenarios.append({"metodo": "ajuste_con_corte_preliminar", "estimacion_nacional": estimacion_corte})

    metricas.to_csv(destino / "validacion_temporal.csv", index=False, float_format="%.6f", lineterminator="\n")
    pronostico.to_csv(destino / "pronostico_2026.csv", index=False, lineterminator="\n")
    pd.DataFrame(escenarios).to_csv(destino / "escenarios_2026.csv", index=False, lineterminator="\n")
    graficar(totales, pronostico["estimacion"].sum(), destino / "serie_nacional.png")
    print(metricas.to_string(index=False))
    print("\nMAE territorial medio:\n" + metricas.groupby("modelo")["mae_territorial"].mean().to_string())
    print("\nPronósticos nacionales 2026:")
    for fila in escenarios:
        print(f"  {fila['metodo']}: {fila['estimacion_nacional']:,}")
    print(f"Seleccionado: {seleccion} | Escenario con corte preliminar: {estimacion_corte:,}")
    print(pronostico.head().to_string(index=False))


if __name__ == "__main__":
    main()
