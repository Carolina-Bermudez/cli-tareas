---
name: acciones-json
description: Reglas del fichero acciones.json de la CLI tareas (campos, tipos, filtros, plantillas y validación). Úsala siempre que crees o cambies acciones o el código que las lee (config.py, acciones.py, motor.py).
---
# Esquema de acciones.json
- Raíz: {"version": 1, "acciones": [...]}. Cada acción: nombre (único, minúsculas-con-guiones), descripcion, tipo.
- Tipos: mover y copiar (requieren destino), renombrar (requiere plantilla), borrar (siempre pide confirmación salvo --si).
- filtro opcional: extensiones (lista, en minúsculas), patron (regex válida), mas_antiguo_que_dias, mayor_que_mb.
- plantilla: huecos {fecha:%Y-%m-%d}, {n:03}, {ext}, {nombre}.
- destino es relativo: se crea dentro de la carpeta que se procesa (p. ej. "imagenes" → CARPETA/imagenes). Nunca relativo al directorio actual.
## Reglas al programar
- Valida el JSON en config.py ANTES de ejecutar; errores con AccionNoValida(accion, campo, motivo).
- pathlib y shutil; encoding="utf-8"; nunca shell=True; nunca sobrescribir (destino_libre).
- Toda acción admite --simular y devuelve list[Resultado].
- Si añades un campo o un tipo nuevo, documéntalo en el README y en esta skill.

## Acciones con IA (semana 3)
- Tipos con IA: resumir y renombrar-ia.
- Campos: instrucciones (texto, obligatorio), max_caracteres (500-50000, por defecto 12000), categorias (lista, opcional).
- resumir admite destino opcional, relativo a la carpeta del fichero; renombrar-ia NO admite destino.
- La IA va SIEMPRE por ProveedorIA (src/tareas/ia.py): las acciones no importan httpx.
- --simular nunca llama al modelo: solo cuenta los caracteres que enviaría.
- La respuesta del modelo nunca se usa tal cual: a_nombre_seguro() la limpia; si queda vacía, «saltado».
- Sin clave o sin red: IANoDisponible (sale con 4) y las acciones sin IA siguen funcionando.