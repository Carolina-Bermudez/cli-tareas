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

Cada acción tiene:

| Campo            | Obligatorio                            | Qué es                                                                                                                                                      |
| ---------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `nombre`         | sí                                     | Lo que escribes en la terminal (`tareas ejecutar NOMBRE`). En minúsculas, con guiones y sin tildes. No puede repetirse.                                     |
| `descripcion`    | sí                                     | Una frase que explica qué hace. La muestra `tareas acciones`.                                                                                               |
| `tipo`           | sí                                     | `mover`, `copiar`, `renombrar`, `borrar`, `resumir` o `renombrar-ia`.                                                                                       |
| `filtro`         | no                                     | Qué ficheros coge: `extensiones` (lista, en minúsculas y con punto), `patron` (expresión regular sobre el nombre), `mas_antiguo_que_dias` o `mayor_que_mb`. |
| `destino`        | en mover y copiar; opcional en resumir | Nombre de una subcarpeta **dentro de la carpeta que se procesa**. No admite rutas absolutas, letra de unidad, `/` o `\` al principio, ni `..`.              |
| `plantilla`      | en renombrar                           | Nuevo nombre con huecos: `{fecha:%Y-%m-%d}`, `{n:03}`, `{ext}` y `{nombre}`. Sin `/`, `\` ni `..`.                                                          |
| `origen`         | no                                     | Carpeta que se usa si no indicas ninguna al ejecutar.                                                                                                       |
| `instrucciones`  | en las acciones con IA                 | Lo que le pides al modelo. Es configuración: se cambia sin tocar el Python.                                                                                 |
| `max_caracteres` | no                                     | Cuánto texto del documento se envía al modelo (500-50000, por defecto 12000).                                                                               |

**Por qué el destino es relativo.** Si el destino fuera una ruta fija, al probar en una carpeta de pruebas los ficheros acabarían en mis carpetas reales. Con un destino relativo, todo ocurre dentro de la carpeta que indico: puedo probar en `~/pruebas-tareas` con seguridad y, cuando funciona, usar la misma acción en `~/Downloads`.

Ejemplo, una de mis acciones:

    {
      "nombre": "ordenar-imagenes",
      "descripcion": "Mueve los .png y los .jpg a una carpeta imagenes",
      "tipo": "mover",
      "filtro": { "extensiones": [".jpg", ".jpeg", ".png"] },
      "destino": "imagenes"
    }

**Reglas de seguridad**

- `tareas validar` comprueba el fichero antes de ejecutar nada y dice qué acción y qué campo fallan.
- `--simular` enseña lo que haría sin tocar ningún fichero. En las acciones con IA, además, no llama al modelo: dice cuántos caracteres enviaría.
- Nunca se sobrescribe un fichero: si el destino ya existe, se añade ` (1)`, ` (2)`…
- `borrar` y `renombrar-ia` piden confirmación, salvo que uses `--si`.
- Orden recomendado con mi carpeta de descargas: primero `apartar-copias` y después las demás.

## Acciones con IA

Mis acciones `resumir-casos` y `nombrar-descargas` preguntan a un modelo de lenguaje del servidor del centro (API compatible con OpenAI). Necesitan tres variables:

    CENTRO_IA_URL=https://dirección-del-servidor/v1
    CENTRO_IA_KEY=tu-clave-personal
    CENTRO_IA_CA=~/ca-ies-simarro.crt

Copia `.env.example` como `.env` y rellénalo. **`.env` nunca se sube a git** (está en `.gitignore`). Comprueba la conexión con `tareas comprobar-ia`.

Sin clave o sin red, las acciones con IA salen con el código 4 y un mensaje claro, y todas las demás siguen funcionando.

## Mejoras pendientes

- Distinguir «la carpeta está vacía» de «ningún fichero cumple el filtro»: ahora los dos casos muestran el mismo aviso.
- Los ficheros .tar.gz no se reconocen como comprimidos, porque Python solo ve la extensión .gz.
- En Windows, renombrar cambiando solo mayúsculas (foto.jpg → FOTO.jpg) crea un duplicado «(1)».
- destino_libre comprueba si el destino existe y escribe después; si otro programa creara el mismo fichero en ese instante, podría sobrescribirse. En una herramienta de uso personal es muy poco probable.
- Un «\» dentro del destino (por ejemplo, "imagenes\2026") se interpreta distinto en Linux y en Windows.
- `rich` no está declarado en pyproject.toml: funciona porque lo instala Typer, pero el código lo importa directamente.
- Un PDF escaneado sin texto se envía vacío al modelo; sería mejor marcarlo como «saltado».- `rich` no está declarado en pyproject.toml: funciona porque lo instala Typer, pero el código lo importa directamente.
