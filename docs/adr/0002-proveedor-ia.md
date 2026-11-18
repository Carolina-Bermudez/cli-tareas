# ADR-0002: La IA va detrás de una interfaz (ProveedorIA)

- Estado: aceptada
- Fecha: 2026-11-18
- Autora: Carolina Bermúdez

## Contexto

Mis acciones resumir-casos y nombrar-descargas necesitan un modelo de lenguaje. El curso usa el servidor del centro (API de OpenAI, CENTRO_IA_URL), pero yo trabajo desde casa y todavía no tengo ni la dirección ni la clave: tengo que poder avanzar sin servidor y probar en la semana 4 sin depender de la red. El año que viene el servidor podría ser otro.

## Decisión

Toda llamada a un modelo pasa por la clase abstracta ProveedorIA, con un único método completar(sistema, usuario). ProveedorCentro la implementa con httpx. Las acciones no saben qué servidor hay detrás, y el proveedor solo se crea cuando hay que llamar al modelo de verdad: ni validar ni --simular lo necesitan.

## Alternativas consideradas

1. Llamar a httpx directamente desde cada acción.
   - A favor: menos código y menos clases.
   - En contra: la dirección, la clave y los errores de red se repetirían en cada acción, y no podría probarlas sin red.
2. Usar la librería oficial de OpenAI (uv add openai).
   - A favor: ya trae los reintentos y los tipos de error.
   - En contra: es una dependencia grande para una sola llamada, y me ataría a un proveedor concreto.
3. Ejecutar un modelo en local (por ejemplo, con Ollama).
   - A favor: funcionaría sin red y sin clave.
   - En contra: necesita un ordenador potente y descargar el modelo; además, con la interfaz podría añadirse después como otra subclase.

## Consecuencias

- Positivas: cambiar de servidor es escribir otra subclase; las pruebas de la semana 4 usarán un proveedor falso, sin red; todos los errores de red están en un solo sitio y salen como IANoDisponible (código 4), así que sin IA el resto de acciones sigue funcionando.
- Negativas: una clase más que entender; la respuesta del modelo puede cambiar cada vez (con la misma entrada, nombres distintos), por eso --simular no puede enseñar el nombre y las acciones que cambian ficheros piden confirmación.
- La clave: vive en el .env de mi ordenador o en las variables de la terminal, nunca en el repositorio. .env está en el .gitignore desde el primer commit y el agente tiene prohibido leerlo (read *.env: deny). En el programa se guarda en un atributo privado y nunca se imprime: comprobar-ia solo dice «clave: definida».