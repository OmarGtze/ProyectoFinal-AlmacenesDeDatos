# Modelo piloto de datos operativos

**Estado:** modelo implementado para los 477 complejos seleccionados. Todos los hechos operativos son **sintéticos**. Los nombres, municipios, estados y conteos de pantallas provienen del CSV público del Sistema de Información Cultural. Ninguna cifra de ventas u ocupación se atribuye como observación real de Cinépolis.

## Alcance

- Periodo simulado: 1 de enero a 31 de diciembre de 2025.
- Alcance: los 477 complejos cuyo nombre contiene «Cinépolis» (con o sin acento) y cuya adscripción es «Cinépolis de México, S.A. de C.V.» en el directorio descargado.
- El directorio se descargó en 2026; su presencia en ese archivo no demuestra que cada complejo operara durante todo 2025. El año 2025 del modelo es un escenario inventado.
- En cada complejo se modelan entre **una y tres salas**, sin pretender representar el inventario completo ni la capacidad real. Se generan tres funciones diarias por sala. Para los 14 complejos con cero pantallas registradas se supone una sala de ejemplo; ese cero se trata como dato no utilizable para estimar capacidad, no como evidencia de cierre.
- Grano de `hecho_funcion_sintetica`: una función en una sala, complejo, fecha y horario. Contiene capacidad supuesta, boletos e ingreso simulado.
- Grano de `hecho_dulceria_diaria_sintetica`: una categoría de producto, complejo y fecha. **No** se vinculan compras a una función o cliente porque no hay evidencia de esa relación.

## Tablas

| Tabla | Origen | Papel |
| --- | --- | --- |
| `dim_complejo` | Directorio SIC | Identidad y ubicación reales; pantallas declaradas en el directorio. |
| `dim_fecha` | Calendario generado | Año, mes, día de semana y fin de semana. |
| `dim_sala_modelada` | Supuestos | Entre una y tres salas de ejemplo por complejo; capacidad y formato supuestos. |
| `dim_pelicula_ficticia` | Supuestos | Títulos inventados para la distribución de funciones. |
| `hecho_funcion_sintetica` | Generador | Asistencia, capacidad, precio e ingreso por función. |
| `hecho_dulceria_diaria_sintetica` | Generador | Unidades e ingresos por categoría y día. |

## Reglas de generación

El script `scripts/generate_synthetic.py` usa semilla fija `20261020` para obtener siempre el mismo resultado. La ocupación se calcula con una base de 33 % multiplicada por factores supuestos de mes, fin de semana, horario y popularidad de una película ficticia, más variación aleatoria. Se limita entre 4 % y 97 %. Los precios por boleto son 75 MXN en sala tradicional y 115 MXN en formato especial, con 8 MXN adicionales en fines de semana.

Las unidades de dulcería se aproximan con tasas supuestas por asistente: 38 % palomitas, 47 % bebidas y 20 % otros alimentos. Estas tasas pueden sumar más de 100 % porque una persona puede comprar varias categorías. Los precios supuestos por unidad son 95, 65 y 72 MXN, respectivamente. Ninguno de estos parámetros está calibrado con registros internos de Cinépolis.

## Fuentes y límites

- `Archivos/data-2026-10-19.csv`: directorio SIC. Solo se usa para seleccionar complejos y conservar sus datos geográficos e infraestructura publicada.
- `Archivos/RESULTADOS-DE-LA-INDUSTRIA-CINEMATOGRAFICA.SERIE-2016-2025.pptx-1.pdf`: CANACINE. Sirve como contexto nacional; sus totales no se imputan a los complejos de la muestra.
- La serie mensual de CANACINE queda fuera de la calibración por la discrepancia entre el total anual y la suma de los meses detectada en el PDF.

## Ejecución

```powershell
python scripts/generate_synthetic.py
```

Produce `data/piloto_sintetico.sqlite` y `data/resumen_sintetico.json`. La base SQLite permite demostrar el modelo dimensional y consultar indicadores. El resumen JSON prepara una futura vista del sitio, etiquetada como simulada.
