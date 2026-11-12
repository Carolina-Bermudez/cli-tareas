# Prompts clave del proyecto

## 2026-11-12 · Primera orden: listar

**Herramienta:** OpenCode 2 · modelo opencode/glm-5.3-flash-free

**Prompt del plan (agente plan):** 
``` 
Lee @README.md y @pyproject.toml. Quiero src/tareas/cli.py (app de Typer llamada app) y src/tareas/__main__.py con dos órdenes: version y listar [CARPETA].
No escribas código todavía: dime qué ficheros crearías, qué funciones tendría cada uno y cómo tratarías la carpeta inexistente, la vacía, los nombres con corchetes y los ficheros que no se pueden leer.

Criterio de aceptación:
- uv run tareas sin argumentos muestra la ayuda, en español y sin autocompletado.
- version imprime «tareas 0.1.0» leyendo __version__ del paquete.
- listar (por defecto la carpeta actual, acepta ~) pinta una tabla Rich: Nombre, Tipo (extensión o «carpeta»), Tamaño legible, Modificado (AAAA-MM-DD HH:MM). Carpetas primero, luego alfabético sin distinguir mayúsculas.
- Carpeta inexistente o que no es carpeta: mensaje en stderr, sin traza, código 1. Carpeta vacía: aviso en vez de tabla vacía.
- pathlib, sin os.system ni subprocess, sin dependencias nuevas. uv run python -m tareas también funciona.
```
  
**Qué corregí del plan:** 
- Escapar con Rich,
- saltar los ficheros ilegibles,
- la carpeta vacía por la salida normal,
- prog_name,
 Sobre todo, que el agente creía que los corchetes solo daban problemas con glob, cuando el problema estaba en Rich.

**Diffs que rechacé o deshice (/undo) y por qué:** No rechacé ningún diff, pero no acepté "Always Allow" para uv * porque si lo permito siempre el agente puede ejecutar cosas sin preguntarme antes.

**Funcionaba a la primera:** No: al listar una carpeta sin permisos salía una traza (PermissionError). Le expliqué el fallo con la orden y lo que esperaba.

**Qué aprendí:** A trabajar con el agente en modo plan y build, primero me explicaba el plan (plan)  así podía corregirlo antes de que escribiera código (build).