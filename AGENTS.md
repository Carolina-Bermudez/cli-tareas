# tareas · CLI de tareas con ficheros (proyecto de 1º DAM)
## Stack y órdenes
- Python 3.12 + Typer + Rich, gestionado con uv (src layout, paquete src/tareas).
- Ejecutar: `uv run tareas --help` · Validar config: `uv run tareas validar` · Pruebas (semana 4): `uv run pytest`.
## Normas
- Mensajes y comentarios en español; código claro antes que listo.
- pathlib siempre, encoding="utf-8", nada de os.system ni shell=True: tiene que funcionar en Linux, Windows y macOS.
- Nunca ejecutes acciones sobre carpetas reales: solo en ~/pruebas-tareas y con --simular.
- No toques .env ni escribas claves en ningún fichero. No hagas git push ni commits: los hace el alumno.
- Antes de cambiar un fichero, explica en 2-3 líneas qué vas a hacer.

## Reglas duras (del spec, no negociables)
- Nunca borrar ficheros sin preguntar.
- Nunca tocar ficheros fuera de la carpeta que el usuario indique.
- Códigos de salida: 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida.
- Windows primero (cuidado con rutas y codificación al abrir ficheros), pero el código debe funcionar también en Linux y macOS.

## Convenciones
- Mantener sincronizados `__version__` en `src/tareas/__init__.py` y `version` en `pyproject.toml`.
- `opencode.json` ya fuerza los permisos: las ediciones y la mayoría de comandos shell piden confirmación; `git push`, `git reset`, `rm` y `sudo` están denegados por política. Los comandos permitidos sin preguntar son: `ls`, `pwd`, `cat`, `git status/diff/log`, `uv run tareas --help`, `uv run tareas validar *`, `uv run pytest *`.
