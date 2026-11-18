# ADR-0001: Las acciones viven en acciones.json, no en el código

- Estado: aceptada
- Fecha: 2026-11-04
- Autor/a: Carolina Bermúdez

## Contexto

Mi herramienta «tareas» automatiza tareas repetitivas con ficheros
(ordenar Descargas, renombrar fotos, limpiar temporales...). Cada persona
que la use tendrá carpetas y manías distintas, y yo misma voy a querer
añadir acciones nuevas cada pocas semanas. En mi situación particular, pierdo tiempo buscando archivos porque los tengo desordenados y también tengo muchas copias en descargas porque no recuerdo si ya lo descargué, por ese motivo las tareas automatizadas son: apartar-copias, ordenar-imagenes, ordenar-comprimidos, ordenar-diagramas y limpiar-instaladores.

## Decisión

Las acciones se describen en un fichero JSON externo (acciones.json) con
un esquema documentado en el README. El código solo contiene el MOTOR que
lee, valida y ejecuta ese fichero. Añadir una acción = editar el JSON.

## Alternativas consideradas

1. Escribir cada acción como una función en Python.
   - A favor: la flexibilidad, una acción podrá hacer cualquier cosa, no sólo mover, copiar, renombrar y borrar.
   - En contra: cada cambio exige tocar el código y volver a instalar; quien
     no programa no puede añadir acciones.
2. Usar YAML o TOML en vez de JSON.
   - A favor: Se leen mejor y admiten comentarios para explicar cada acción.
   - En contra: En YAML hay que instalar una librería aparte para trabajar con Python, mientras que en TOML las listas de acciones son incómodas de escribir.
3. Preguntar las opciones en la terminal cada vez (sin fichero de configuración)
   Por ejemplo: tareas mover --extensiones .png .jpg --destino imagenes.
   - A favor: no hay ningún fichero que mantener ni que se pueda romper.
   - En contra: tendría que recordar y escribir todas las opciones cada vez; no podría guardar mis acciones favoritas con un nombre.
  
## Consecuencias

- Positivas: añadir una acción no toca el código; cuando añadí ordenar-diagramas y limpiar-instaladores, sólo edité   JSON. El JSON se valida antes de tocar ningún fichero, cuando puse una coma de más, mober o el nombre repetido, validar avisó y no hizo nada.
- Negativas: hay que mantener la validación al día cuando el esquema crezca; los errores de escritura en el JSON solo se ven al ejecutar validar; no se pueden poner comentarios, las barras invertidas van dobles.
- Qué haré si el esquema cambia: Subir "version" a 2, y que el programa siga aceptando los ficheros con versión 1 durante un tiempo, o que avise con un mensaje claro de cómo actualizarlos. Actualizar a la vez el README, la skill acciones-json y la validación de config.py.
