# Lista de pendientes antes de producción real

## 1. Cifrado de credenciales de conectores

- [ ] Definir `CREDENTIAL_ENCRYPTION_KEY` en el entorno de producción.
- [ ] Verificar que las credenciales cifradas sobreviven a un reinicio del proceso.
- [ ] Eliminar la excepción que permite operar sin clave en entornos que no sean producción.
- [ ] Rotar la clave mediante el procedimiento operativo definido y comprobar que no quedan credenciales cifradas con la clave anterior.

## 2. Secretos y registros

- [ ] Revisar logs, métricas, trazas y respuestas de error para confirmar que no contienen secretos.
- [ ] Mantener redactados en representaciones de configuración los campos que incluyan clave, secreto, token, contraseña o DSN.
- [ ] Comprobar que los secretos no se persisten en conversaciones, eventos ni artefactos.

## 3. Autenticación y tenants

- [ ] Configurar claves API y de administrador mediante secretos del entorno o del proveedor de despliegue.
- [ ] Verificar aislamiento de lectura y escritura entre tenants.
- [ ] Revisar permisos de cada capability y dejar `DEV_ALLOW_ALL=false`.
- [ ] Definir rotación, revocación y expiración de credenciales.

## 4. Persistencia y recuperación

- [ ] Elegir y validar el backend de EventLog para producción.
- [ ] Ejecutar backups y una restauración de prueba.
- [ ] Verificar migraciones, permisos de almacenamiento y retención de eventos.
- [ ] Comprobar que las credenciales cifradas permanecen legibles después de restaurar los datos.

## 5. Observabilidad y operación

- [ ] Configurar logs estructurados, métricas y trazas sin datos sensibles.
- [ ] Definir alertas para fallos de persistencia, proveedor LLM, cola y políticas.
- [ ] Documentar el procedimiento de despliegue, rollback y respuesta a incidentes.
- [ ] Ejecutar una prueba de carga y una prueba de recuperación ante fallos.
