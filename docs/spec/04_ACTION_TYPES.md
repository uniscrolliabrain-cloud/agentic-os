# 04 — Tipos de acción (ACTION)

Las acciones son la dimensión verbal del metamodelo. No se ejecutan "sueltas":
cada acción se realiza mediante una **microacción** concreta (`08_MICROACTION_CATALOG.md`).

## Semántica de cada acción

| Action | Qué significa | Ejemplo |
|---|---|---|
| Discover | Encontrar algo que no se sabía que existía | descubrir competidores |
| Search | Buscar dentro de un universo conocido | buscar en la web |
| Retrieve | Traer una entidad por referencia | recuperar un documento por id |
| Read | Leer contenido sin modificarlo | leer un email |
| Write | Escribir/almacenar contenido | escribir un fichero |
| Create | Instanciar una entidad nueva | crear un contacto |
| Transform | Cambiar formato/estructura sin cambiar esencia | CSV → JSON |
| Analyze | Extraer insights | analizar métricas |
| Classify | Etiquetar/ordenar en categorías | clasificar leads |
| Validate | Comprobar que cumple un contrato | validar output |
| Communicate | Enviar un mensaje a alguien | enviar email |
| Publish | Hacer público/deploy | publicar un post |
| Execute | Ejecutar un procedimiento | ejecutar un workflow |
| Update | Cambiar campos de una entidad existente | actualizar el CRM |
| Delete | Eliminar una entidad | borrar un registro |
| Monitor | Observar a lo largo del tiempo | monitorizar una web |

## Reglas

1. Toda microacción se etiqueta con **una y solo una** acción del catálogo.
2. Combinaciones lógicas se expresan como pipelines, nunca como "acciones híbridas".
3. Las acciones `Delete` y `Publish` requieren **aprobación humana** por defecto
   (ver `14_HUMAN_APPROVAL.md`) salvo política explícita del tenant.
4. `Execute` solo puede encadenarse a un pipeline definido (nunca a "código libre").

## Invariante

Cada microacción define acción + entidad sobre la que opera. El par
`(Action, Entity)` debe ser válido en la ontología; pares no contemplados
p.ej. `(Delete, Person)` quedan **denegados por defecto** salvo capability explícita.