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



## 2026-11-15 · Validación de acciones.json (orden validar)

**Herramienta:** OpenCode 2 · modelo opencode/glm-5.3-flash-free

**Prompt del plan (agente plan):**
```
Carga la skill acciones-json y lee @acciones.json.
Quiero validar acciones.json ANTES de ejecutar nada:
- src/tareas/errores.py con TareasError, ConfigError y AccionNoValida;
- src/tareas/config.py con cargar(ruta) -> list[dict];
- la orden «tareas validar» en src/tareas/cli.py.
No toques nada todavía: dime qué ficheros crearías o cambiarías, qué clases y funciones tendrán y qué casos de error vas a detectar.
```

**Qué corregí del plan:**
- La ruta del fichero iba como argumento de validar; la cambié por la opción global --config, que vale para todas las órdenes.
- Una sola captura de TareasError en cli.py usando e.codigo_salida, sin códigos escritos a mano.
- Le di la lista de campos válidos (nombre, descripcion, tipo, origen, filtro, destino, plantilla, confirmar), porque si no habría rechazado campos legítimos.
- Nada de tests todavía: llegan en la semana 4.

**Funcionaba a la primera:** No.
- El agente encontró un UnicodeEncodeError en Windows al escribir el símbolo ✓ (la consola usaba cp1252). Se arregló forzando UTF-8 en la salida.
- Con mis casos feos encontré dos fallos más: con "acciones": [] decía «0 acciones válidas» y salía con 0; y el destino "/imagenes" se aceptaba, porque en Windows Path("/imagenes").is_absolute() es False, pero al unirlo acabaría en C:\imagenes, fuera de la carpeta. Se lo expliqué al agente con lo que veía y lo corrigió usando el «ancla» de la ruta (anchor).

**Diffs u órdenes que rechacé y por qué:** Rechacé dos veces que el agente creara ficheros de prueba fuera del proyecto (en la carpeta temporal de Windows). No se lo había pedido y los casos feos los pruebo yo con roto.json.

**Qué aprendí:** Que un mensaje de error útil dice qué acción y qué campo fallan. Y que Windows tiene sus propias trampas: una ruta que empieza por / no es absoluta para Python, pero sí se sale de la carpeta.

## 2026-11-17 · Motor y clases Accion

**Herramienta:** OpenCode 2 · modelo opencode/glm-5.3-flash-free

**Prompt del plan (agente plan):**
```
Carga la skill acciones-json y explícame cómo harías acciones.py y motor.py: clases, métodos y cómo garantizas que --simular no toca el disco.
Importante: en mi esquema el destino es relativo a la carpeta que se procesa (CARPETA / destino), no al directorio actual. Explica cómo lo resolverás en Mover.
```

**Qué corregí del plan:**
- Error grave: el plan hacía mkdir de la carpeta padre y luego shutil.move a una carpeta «imagenes» que no existía. Eso no mete el fichero dentro: lo renombra a «imagenes», y el siguiente fichero lo sobrescribe. Se habrían perdido ficheros. Le pedí crear primero la carpeta destino y mover a destino_libre(carpeta_destino / nombre).
- Le pedí seguir el diseño del profesor: clase Motor con ejecutar(nombre, carpeta, simular), registro de subclases con __init_subclass__ y que el motor no imprima ni pregunte.

**Qué corregí del código:**
1. Solo Borrar es destructiva (había marcado también Mover, Copiar y Renombrar).
2. Al simular, Mover y Copiar también calculan destino_libre, para que la simulación muestre el mismo destino que se usará, con « (1)» si hace falta.
3. {fecha} usaba la fecha de hoy (datetime.now()); la cambié por la fecha de modificación del fichero (st_mtime).
4. {ext} perdía el punto (salía 001jpg en vez de 001.jpg).
5. Faltaba expanduser() en la carpeta y en el origen, y Path() alrededor de origen por si llega como texto.

**Diffs u órdenes que rechacé y por qué:** Rechacé un tercer intento de crear carpetas de prueba fuera del proyecto, esta vez desde código Python, que no muestra el aviso de «carpeta externa». Lo detecté leyendo la orden antes de aprobarla.

**Qué aprendí:** Que hay que leer el plan antes de dejar escribir al agente: el error de shutil.move habría perdido ficheros reales. Y que el agente conoce las reglas de la skill pero no siempre las cumple.

## 2026-11-18 · Interfaz (acciones y ejecutar), /nueva-accion y revisor

**Herramienta:** OpenCode 2 · modelo opencode/glm-5.3-flash-free; a mitad de sesión OpenCode cambió a «Hy4 flash Free».

**Prompt del plan (agente plan):** el prompt de interfaz del profesor («Amplía SOLO @src/tareas/cli.py…»), añadiendo:
```
La opción global --config ya existe en cli.py: no la dupliques.
En la tabla de ejecutar, escapa los nombres con rich.markup.escape y, si destino es None (borrar), muestra «—».
Primero dime el plan; no toques nada todavía.
```

**Qué corregí del plan:**
- Usaba el atributo privado motor._acciones desde cli.py; le pedí un método público motor.obtener(nombre).
- Con abort=True, Typer escribía «Aborted!» en inglés; ahora dice «Cancelado: no se ha borrado nada.» y sale con 1.
- Faltaba la línea final «Para hacerlo de verdad, repite la orden sin --simular.»
- No ejecutar pytest, que todavía no está instalado.

**Pruebas que hice yo en ~/pruebas-tareas/Descargas:**
- Simulé las tres acciones y coincidieron con lo que esperaba: apartar-copias no coge «informe (borrador).pdf», ordenar-imagenes coge FOTO2.JPG y «cumpleaños 2.png».
- Ejecuté de verdad; la segunda vez dice que ningún fichero cumple el filtro.
- Con un foto.png repetido, la simulación propone «foto (1).png»: nunca se sobrescribe.

**Acciones 4 y 5 con /nueva-accion:**
- ordenar-diagramas: rechacé la versión simple (extensiones .pdf), que habría movido todos mis PDF. Elegí el patrón "(?i)\\.drawio", con el punto delante.
- limpiar-instaladores (tipo borrar, .exe y .msi con más de 30 días): probé contestando n (no borra nada y sale con 1) y contestando y (borra los dos viejos y no toca programa-nuevo.exe).

**Qué señaló el revisor y qué decidí:**
- Arreglado: una plantilla con «..» o «/» podía escribir fuera de la carpeta (ahora validar la rechaza); iterdir() sin proteger en el motor (el mismo fallo que encontré en listar con C:\System Volume Information); capturar también ValueError para que un fichero no corte el resto.
- Apuntado como mejora en el README: TOCTOU en destino_libre, .tar.gz, mayúsculas al renombrar en Windows, distinguir carpeta vacía de filtro sin coincidencias.
- Descartado: falta de HOME y locale de %B, porque son casos muy raros y mis acciones no los usan.

**Respuesta a la pregunta del revisor:** Renombrar no crea carpetas, al contrario que Mover, que hace mkdir del destino antes de mover. Con la plantilla {fecha:%Y}/{nombre}{ext} el nuevo nombre está dentro de una carpeta «2026» que no existe, el rename da un OSError y el fichero queda como «saltado». Para que funcionara habría que (1) crear la carpeta antes de renombrar y (2) comprobar que la ruta final no sale de la carpeta procesada. Yo preferí prohibir /, \ y «..» en la plantilla: es más sencillo y seguro, y renombrar solo cambia el nombre; para ordenar en carpetas ya está mover.

**Qué aprendí:** Que el revisor, al no haber escrito el código, ve fallos que el agente que lo escribió no ve. Y que /nueva-accion ahorra escribir, pero la decisión (qué filtro, qué ficheros) sigue siendo mía.