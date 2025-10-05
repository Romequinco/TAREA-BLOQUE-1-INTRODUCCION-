# TAREA-BLOQUE-1-INTRODUCCION-
**Primera tarea del master MIAX**
El objetivo de este proyecto es crear un programa que actúe como un conjunto de herramientas para la obtención y el análisis de información bursátil. Si bien una parte importante de esto puede resolverlo una IA, la importancia radica en sedimentar en tu mente las estructuras y buenas prácticas a la hora de crear código. Decisiones que pueden parecer engorrosas a pequeña escala son las que luego permiten a los proyectos crecer más allá de los límites a los que un solo individuo puede llegar. Valora la importancia de la estructura, de las abstracciones y de la estandarización.

Crea un proyecto en GitHub para esta práctica.

Recuerda detallar en el fichero README aquello que consideres necesario.

Crea una carpeta /src donde se encuentre el núcleo de tu trabajo.

Añade aquello que consideres necesario para que el proyecto sea lo más “plug-n-play” posible.

Crea un programa extractor cuya función sea obtener datos desde varias fuentes de datos online (APIs).

Este programa puede contener múltiples opciones, pero es necesario que existan métodos para descargar información histórica de precios tanto de acciones como de índices.

Independientemente de la fuente de información, el formato de salida de esta información debe ser estandarizado. Es decir, con independencia de la fuente original, nuestro programa debe darnos en salida objetos iguales. Por ejemplo: independientemente de la api utilizada, el formato de precio histórico debe ser compatible con el formato de salida que resulte de utilizar otra API diferente.

Añade opción de conseguir otra tipología de datos a tu gusto.

Haz que el extractor pueda conseguir N series de datos al mismo tiempo dado un input que induzca a ello.

Hagamos que los datos sean coherentes. Cada serie de datos debe ser un objeto. Crea DataClasses para las series de precios. Existiendo estos objetos, ¿qué es una cartera?

Añade métodos a las dataclasses de series de precios que incorporen información estadística relevante. Haz que los métodos para la información más básica (media y desviación típica) se apliquen automáticamente.

Dado un valor o una cartera, elabora un pequeño programa que genere una simulación de Monte Carlo para su evolución.

Intenta que esta simulación sea maleable por el usuario por parámetros.

Haz que la simulación pueda ser tanto de la cartera en su conjunto como de los elementos que la componen.

Convierte el proceso de Monte Carlo en un método para la DataClass de la cartera. Incluye otro método que muestre por pantalla visualmente el resultado.

Incluye métodos para la “limpieza” y el preprocesado de los datos. ¿Debería el programa aceptarte cualquier tipo de input siempre que exista una serie temporal de precios?

Dada una cartera, crea un método .report (con los parámetros que consideres oportunos) que genere texto formateado en markdown y pueda mostrar por pantalla aquel análisis que consideres relevante, así como advertencias y cualquier otro aspecto.

Antiguamente, generar gráficos verdaderamente resultones era tedioso y no tenia gran aporte intelectual; la IA facilita enormemente todo esto. Intenta pensar en el tipo de visualizaciones más útiles para un usuario con su ayuda y guárdalas para que un método .plots_report() las muestre.

Estás construyendo un programa que empieza a tener dependencias, jerarquías, clases dentro de clases… es importante mantener la perspectiva general de lo que estás construyendo. Muchas veces, de hecho, igual debería ser tu primer paso. Intenta plasmar esta estructura utilizando algún recurso para mostrar diagramas. Esta es sencilla y útil https://github.com/stan-smith/FossFLOW 
