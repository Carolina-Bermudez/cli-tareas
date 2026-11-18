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

## Instalación

Necesitas [uv](https://docs.astral.sh/uv/) y Git.

    git clone https://github.com/Carolina-Bermudez/cli-tareas.git
    cd cli-tareas
    uv tool install --editable .
    tareas --help

## Formato de acciones.json

Las acciones no están escritas en el código: se describen en el fichero `acciones.json`. El programa lo lee, lo valida y ejecuta lo que pone. Para añadir una acción nueva basta con editar este fichero, sin tocar el Python.

El fichero tiene un número de versión del formato y una lista de acciones:

    {
      "version": 1,
      "acciones": [ ... ]
    }



Cada acción tiene:

| Campo         | Obligatorio       | Qué es                                                                                        |
| ------------- | ----------------- | --------------------------------------------------------------------------------------------- |
| `nombre`      | sí                | ________                                                                                      |
| `descripcion` | sí                | ________                                                                                      |
| `tipo`        | sí                | `mover`, `copiar`, `renombrar` o `borrar`                                                     |
| `filtro`      | no                | ________ [qué ficheros coge: `extensiones`, `patron`, `mas_antiguo_que_dias`, `mayor_que_mb`] |
| `destino`     | en mover y copiar | ________ [explica TU regla: relativo a la carpeta que se procesa]                             |
| `plantilla`   | en renombrar      | huecos `{fecha:%Y-%m-%d}`, `{n:03}`, `{ext}`, `{nombre}`                                      |
| `origen`      | no                | carpeta por defecto si no indicas una al ejecutar                                             |

Ejemplo:
**Por qué el destino es relativo.** Si el destino fuera una ruta fija (por ejemplo, `~/Documentos/Imagenes`), al probar en una carpeta de pruebas los ficheros acabarían en mis carpetas reales. Con un destino relativo, todo ocurre dentro de la carpeta que indico: puedo probar en `~/pruebas-tareas` con total seguridad y, cuando funciona, usar la misma acción en `~/Downloads`.

Ejemplo, una de mis acciones:

    {
      "nombre": "ordenar-imagenes",
      "descripcion": "Mueve los .png y los .jpg a una carpeta imagenes",
      "tipo": "mover",
      "filtro": { "extensiones": [".jpg", ".jpeg", ".png"] },
      "destino": "imagenes"
    }

Con la orden `tareas ejecutar ordenar-imagenes ~/Downloads`, las imágenes van a `~/Downloads/imagenes`.

**Reglas de seguridad**

- `tareas validar` comprueba el fichero antes de ejecutar nada, y dice qué acción y qué campo fallan.
- `--simular` enseña lo que haría sin tocar ningún fichero. Úsalo siempre primero.
- Nunca se sobrescribe un fichero: si el destino ya existe, se añade ` (1)`, ` (2)`…
- Las acciones de tipo `borrar` piden confirmación, salvo que uses `--si`.
- Orden recomendado con mi carpeta de descargas: primero `apartar-copias` y después las demás, para que una imagen repetida no acabe en la carpeta de imágenes.
**Por qué el destino es relativo.** Si el destino fuera una ruta fija (por ejemplo, `~/Documentos/Imagenes`), al probar en una carpeta de pruebas los ficheros acabarían en mis carpetas reales. Con un destino relativo, todo ocurre dentro de la carpeta que indico: puedo probar en `~/pruebas-tareas` con total seguridad y, cuando funciona, usar la misma acción en `~/Downloads`.

Ejemplo, una de mis acciones:

    {
      "nombre": "ordenar-imagenes",
      "descripcion": "Mueve los .png y los .jpg a una carpeta imagenes",
      "tipo": "mover",
      "filtro": { "extensiones": [".jpg", ".jpeg", ".png"] },
      "destino": "imagenes"
    }

Con la orden `tareas ejecutar ordenar-imagenes ~/Downloads`, las imágenes van a `~/Downloads/imagenes`.

**Reglas de seguridad**

- `tareas validar` comprueba el fichero antes de ejecutar nada, y dice qué acción y qué campo fallan.
- `--simular` enseña lo que haría sin tocar ningún fichero. Usar siempre primero.
- Nunca se sobrescribe un fichero: si el destino ya existe, se añade ` (1)`, ` (2)`…
- Las acciones de tipo `borrar` piden confirmación, salvo que uses `--si`.
- Orden recomendado con mi carpeta de descargas: primero `apartar-copias` y después las demás, para que una imagen repetida no acabe en la carpeta de imágenes.

