# Observatorio Cine

Primera versión local del sitio académico de BI sobre Cinépolis y el mercado cinematográfico mexicano.

## Ejecutar

Desde esta carpeta:

```powershell
python -m http.server 8000
```

Abrir `http://localhost:8000`. No requiere instalar paquetes de frontend.

## Actualizar el directorio

```powershell
python scripts/build_data.py
```

El script lee `Archivos/data-2026-10-19.csv` y genera `data/complejos.json`. Selecciona registros cuyo nombre contiene «Cinépolis» (con o sin acento) y cuya adscripción es «Cinépolis de México, S.A. de C.V.». El filtro es conservador y está sujeto a revisión de calidad; el directorio no es una serie histórica ni un censo empresarial certificado.

Las cifras de 2025 de la sección Mercado proceden del PDF de CANACINE ubicado en `Archivos/`. Son cifras nacionales de toda la industria. El gráfico mensual del mismo reporte presenta una suma distinta del total anual; esa serie no se incluye hasta verificarla.

## Generar el piloto sintético

```powershell
python scripts/generate_synthetic.py
```

El script crea `data/piloto_sintetico.sqlite` y `data/resumen_sintetico.json` para los 477 complejos seleccionados. La sección «Operación modelada» usa el resumen JSON y distingue explícitamente sus métricas inventadas de las cifras observadas. El grano de las tablas, los supuestos y las limitaciones están en [MODELO_DATOS.md](MODELO_DATOS.md).

El módulo interactivo de simulación de escenarios está señalado como trabajo futuro.
