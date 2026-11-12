# Fuentes de Estadísticas Vitales del DANE

Los nacimientos se cuentan por territorio de ocurrencia. Los datos de 2020 a 2025 son definitivos. Se conserva el código de departamento con dos dígitos y la serie excluye los registros tardíos que el DANE publica por separado.

| Año | Archivo local para reconstruir el panel | Fuente |
| --- | --- | --- |
| 2020 | `nac2020.zip` | [Catálogo DANE](https://microdatos.dane.gov.co/index.php/catalog/732/get-microdata) |
| 2021 | `nacimientos2021.zip` | [Catálogo DANE](https://microdatos.dane.gov.co/index.php/catalog/775/get-microdata) |
| 2022 | `nac2022.zip` | [Catálogo DANE](https://microdatos.dane.gov.co/index.php/catalog/807/get-microdata) |
| 2023 | `BD-EEVV-Nacimientos-2023.zip` | [Catálogo DANE](https://microdatos.dane.gov.co/index.php/catalog/876/get-microdata) |
| 2024 | `2024.xlsx` | [Cuadros definitivos, actualización del 6 de febrero de 2026](https://www.dane.gov.co/files/operaciones/EEVV/2026/6-feb-2026/anex-EEVV-NacimientosCuadroAcumulado-2024.xlsx) |
| 2025 | `2025.xlsx` | [Cuadros definitivos del 24 de septiembre de 2026](https://www.dane.gov.co/files/operaciones/EEVV/2026/24-sep-2026/anex-EEVV-NacimientosCuadroAcumulado-2025.xlsx) |

Coloca los ZIP en `data/originales/microdatos` y los dos Excel en `data/originales/cuadros`, con los nombres de la tabla. Luego ejecuta:

```bash
python preparar_datos.py data/originales/microdatos data/originales/cuadros
```

El script lee únicamente el año y el código de ocurrencia de cada microdato. En los Excel conserva las filas de total departamental del Cuadro 2 y verifica que la suma coincida con el total nacional. El repositorio contiene conteos agregados.

Para el escenario de 2026, el [boletín técnico del 24 de septiembre de 2026](https://www.dane.gov.co/files/operaciones/EEVV/2026/24-sep-2026/bol-EEVV-Isem2026pr.pdf) compara los cortes nacionales de enero a julio de 2025 y 2026. El [anexo preliminar de 2026](https://www.dane.gov.co/files/operaciones/EEVV/2026/24-sep-2026/anex-EEVV-NacimientosCuadroAnoCorrido-2026pr.xlsx) confirma el total de 253.175 en su índice. Esos cortes se guardan en `nacimientos_enero_julio.csv` y se usan solo para el escenario nacional.
