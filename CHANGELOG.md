# Changelog

Todos los cambios que notará quien USA la herramienta. Formato: Keep a Changelog · versiones: SemVer.

## [1.0.0] - 2026-11-20

### Añadido
- Órdenes `tareas listar`, `tareas acciones`, `tareas validar` y `tareas ejecutar`, con tabla de resultados.
- Siete acciones en `acciones.json`: `apartar-copias`, `ordenar-imagenes`, `ordenar-comprimidos`, `ordenar-diagramas`, `limpiar-instaladores`, `resumir-casos` y `nombrar-descargas`.
- `--simular`: enseña lo que haría sin tocar ningún fichero; en las acciones con IA dice cuántos caracteres enviaría, sin gastar.
- Confirmación antes de borrar o renombrar con IA (`--si` para no preguntar).
- Acciones con IA: `resumir` y `renombrar-ia`, con los modelos del centro.
- `tareas comprobar-ia`: dice si hay IA disponible (sale con 4 si no la hay).
- `.env.example` con las variables que hacen falta.
- La opción `--config` para usar otro fichero de acciones.

### Arreglado
- Un destino como `/imagenes`, `~/PDF` o con `..` ya no se acepta: los ficheros nunca salen de la carpeta que procesas.
- Un fichero que ya existe nunca se sobrescribe: se añade ` (1)`, ` (2)`…
- Si el modelo propone un nombre peligroso o vacío, el fichero no se renombra.
- Una carpeta sin permisos da un mensaje claro en lugar de un error técnico.
- En Windows, los símbolos y las tildes se muestran bien en la terminal.