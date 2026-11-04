# tareas

Mi herramienta de línea de órdenes para automatizar tareas repetitivas con ficheros.

## Spec (versión 0 · 04/11/2026)
1. **Problema:** cada semana pierdo tiempo en buscar y borrar archivos duplicados, más de 1000 ficheros de descargas, 566 PDF algunos se repiten hasta 6 veces.
2. **Para quién:** para mí.
3. **Cómo se usa:** `tareas ORDEN [CARPETA] [opciones]` desde cualquier terminal.
4. **Órdenes de la semana 1:** `tareas --help`, `tareas version`, `tareas listar [CARPETA]`.
5. **Órdenes previstas:** `tareas acciones`, `tareas validar`, `tareas ejecutar NOMBRE --simular`.
6. **Mis 3 acciones (borrador):** `apartar-copias` (mueve los archivos duplicados a una carpeta), `ordenar-imagenes` (ordenar según la extensión .png o .jpg ), `ordenar-comprimidos` (según su extensión .zip, .rar , .iso).
7. **Nunca hará:** borrar sin preguntar ni tocar ficheros fuera de la carpeta que le indique.
8. **Plataformas:** Windows primero; también Linux y macOS.
9. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida.
10. **Instalación:** `uv tool install --editable .` (lo completo en la semana 4).