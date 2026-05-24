# Prueba tecnica Yummy Wallet Service

Este documento explica qué construi, cómo funciona por dentro y por qué tome las decisiones que tome. Está escrito para que un cualquiera que lea esto pueda entender el sistema completo sin tener que leer ni una línea de código (o poner a la Ia a intenderlo).

---

## Qué construi

Un backend de billetera digital para Yummy. El producto le permite a un usuario:

- Registrarse y autenticarse (con JWT)
- Crear su wallet (Se tomo la decision de que 1 usuario solo puede tener 1 wallet)
- Depositar dinero a su wallet
- Retirar dinero de su wallet
- Transferir dinero a la wallet de otro usuario
- Consultar su saldo actual con las últimas 10 transacciones
- Ver el historial completo de transacciones

Lo más difícil de este sistema no fue ninguna de esos casos de uso por serapdo, sino lo fue garantizar que cuando dos cosas pasan al mismo tiempo (dos retiros simultáneos, una transferencia y un retiro cruzados), el dinero nunca se duplique ni desaparezca (como aveces pasa en la banca nacional).

---

## Cómo se ve el sistema

### Diagrama de arquitectura

```
 ────────────────────────────────────────────────────────────── 
│                         Cliente                              │
│     (móvil / web / Postman / Swagger / cualquier HTTP)       │
 ───────────────────────────-────────────────────────────────── 
                            │ HTTPS + JWT en Authorization header
 ────────────────────────────────────────────────────────────── 
│                    FastAPI + Uvicorn                         │
│                                                              │
│   /auth        /users         /wallets                       │
│   register     me (PUT)       /                (crear)       │
│   login        me (DELETE)    /{id}/deposit                  │
│                               /{id}/withdraw                 │
│                               /{id}/transfer                 │
│                               /me             (saldo home)   │
│                               /me/transactions (historial)   │
│                                                              │
│   Cada endpoint extrae el JWT, valida el usuario activo,     │
│   construye las dependencias e invoca el servicio.           │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│ │                   Capa de Servicios                    │   │
│ │                                                        │   │
│ │  WalletService                  UserService            │   │
│ │   ── create.execute()            ── create.execute()   │   │
│ │   ── deposit.execute()           ── login.execute()    │   │
│ │   ── withdraw.execute()          ── update.execute()   │   │
│ │   ── transfer.execute()          ── delete.execute()   │   │
│ │   ── get_summary.execute()                             │   │
│ │   ── get_transactions.execute()                        │   │
│ │                                                        │   │
│ │  Cada operación es un objeto independiente (command    │   │
│ │  pattern), el servicio solo los agrupa.                │   │
│  --------------------------------------------------------    │
│                         │                                    │
│  ─────────────────────---────────────────────────────────    │
│ │                  Capa de Repositorios                  │   │
│ │                                                        │   │
│ │  UserRepository   WalletRepository   TransactionRepo   │   │
│ │                                                        │   │
│ │  Toda la lógica SQL vive aquí, los servicios nunca     │   │
│ │  tocan SQLAlchemy directamente. (Intentando simular    │   │
│ │ una arquitectura por capas, solo teniendo que cambiar  │   │
│ │ esta capa si quisiera pasar de SQL a NoSql)            │   │
│  ───────────────────────┬────────────────────────────────    │
 ───────────────────────────────────────────────────────────── 
                          │ asyncpg (conexiones async a PostgreSQL)
 ────────────────────────────────────────────────────────────── 
│                      PostgreSQL 16                           │
│                                                              │
│   users          wallets          transactions               │
│   ──────         ───────          ────────────               │
│   id (UUID)      id (UUID)        id (UUID)                  │
│   email          user_id (FK)     wallet_id (FK)             │
│   hashed_pw      saldo          type                       │
│   is_active      is_active        amount                     │
│                                   saldo_after              │
│                                   reference_id               │
│                                   idempotency_key (UNIQUE)   │
│                                   created_at                 │
 ──────────────────────────────────────────────────────────────
```

### Lo mas complicado fue el flujo de una tranferencia, el mismo se ve asi: 

Por ejemplo, María quiere transferir $50 a Pedro.

**Paso 1**
Lo primero que hace el sistema es revisar si ya hizo esta operación. El cliente envía una "llave de idempotencia" aka un código único que él mismo generó antes de hacer el request. 

El sistema busca esa llave en el historial de transacciones, si ya existe, devuelve la misma respuesta de antes y no hace nada más. 

Esto protege el caso donde la app de María ya hizo la transferencia, la red falló antes de responderle y la app lo intenta de nuevo por tanto el dinero no se descuenta dos veces.

**Paso 2**
Antes de leer los saldos, el sistema va y bloquea las wallets de María y Pedro en la BD para que nadie más las pueda tocar mientras está procesando. 

El truco está en el orden: siempre congela primero la wallet cuyo ID sea el más pequeño alfabéticamente, sin importar quién envía y quién recibe. Particularmente porque si dos transferencias cruzadas llegan al mismo tiempo (María a Pedro y Pedroa María), ambas intentan congelar las mismas wallets en el mismo orden entonces una espera a que la otra termine, en lugar de
bloquearse mutuamente para siempre.

**Paso 3**
Con las wallets ya congeladas y con los saldos reales en mano, el sistema verifica: la wallet de origen es realmente de María y esta activa?, tiene al menos $50?, la wallet de Pedro está activa? Si algo falla aquí, se retorna el error correspondiente y los saldos no cambian.

**Paso 4**
Se calculan los nuevos saldos: María queda con $50 menos, Pedro con $50 más.

**Paso 5**
Se hace el commit de la transaccion o le rollback de la misma. No existe el escenario donde a una cuenta
le bajaron $50 pero a la otra no le subieron. Si en este paso falla cualquier cosa (se cayó la base de datos, se fue la luz), el sistema revierte automáticamente y los saldos quedan exactamente como estaban antes.

---

## Decisiones de diseño

### 1. REST en lugar de gRPC o eventos asíncronos

**Que elegi:** API REST clásica con JSON sobre HTTPS.

**Por qué:** REST es el contrato más universal, no requiere generación de stubs, y cualquier desarrollador puede probarla con curl o Postman o el Swagger en segundos. Para un sistema financiero donde cada operación necesita una respuesta inmediata de éxito o error, REST es la opción natural.

**Alternativa descartada — eventos asíncronos:** Los eventos son ideales para sistemas que toleran consistencia eventual, como notificaciones o reportes. Pero en una sistema bancario, el usuario necesita saber ahora mismo si el dinero llegó. 
Un modelo de eventos obligaría al cliente a polling o websockets para saber el resultado, y añadiría complejidad de infraestructura (broker, consumidores, manejo de retries) sin beneficio real para este caso de uso.

---

### 2. La idempotency key la genera el cliente, no el servidor

**Que elegi:** El cliente genera un UUID en su v4 antes de hacer el request y lo envía en el body. El servidor lo guarda en `transactions.idempotency_key` que tiene un constraint UNIQUE.

**Por qué:** El problema que resuelve la idempotencia es el siguiente: el cliente envía una solicitud de retiro, la red falla antes de recibir la respuesta, y el cliente no sabe si la operación se ejecutó o no. Si vuelve a enviar la misma key, el servidor reconoce que ya procesó esa operación y devuelve el mismo resultado sin tocar el slado.

Si el servidor generara la key, el cliente necesitaría primero hacer una peticion para obtenerla, y luego otro para ejecutar la operación. Eso es el doble de llamadas, el doble de puntos de falla y el doble de consumo. Con la key del lado del cliente, el flujo es un solo request que se puede reintentar indefinidamente sin riesgo de duplicar dinero.

**Alternativa descartada — servidor genera la key en un endpoint previo:** Añade latencia y complejidad sin ninguna ventaja real. Si el cliente pierde la key (crash antes de guardarla), queda en el mismo problema de incertidumbre.

**Alternativa descartada — no tener idempotencia:** Dejaría al sistema vulnerable a cobros dobles por problemas de red como a pasado en algunos bancos de la banca nacional (banesco).

---

### 3. SELECT FOR UPDATE en lugar de bloqueo optimista

**Que elegi:** Antes de leer el saldo para modificarlo, ejecutamos `SELECT ... FOR UPDATE`. En PostgreSQL esto bloquea la fila hasta que el request actual haga commit, serializando a cualquier otro request que quiera modificar la misma wallet al mismo tiempo.

**Por qué:** Si dos retiros llegan al mismo tiempo a la misma wallet con $100 y ambos piden retirar $80, sin ningún lock ambos leerían $100, validarían que hay fondos, y ambos escribirían $20 como nuevo saldo. 
El resultado sería que el usuario retiró $160 de $100. Con FOR UPDATE, el segundo request queda bloqueado hasta que el primero commitee, lee $20 y falla con "fondos insuficientes".

**Alternativa descartada — bloqueo por versionamiento:** Este bloqueo añade un campo `version` a la tabla. 

Cada UPDATE incluye `WHERE version = version_leída`, si alguien modificó la fila entre la lectura y el write, el UPDATE no encuentra la fila (afecta 0 rows) y el servicio reintenta. 
Es una buena solución cuando los conflictos son raros. En una billetera que deberia contar con muchos requests concurrentes, los reintentos se multiplican y la experiencia del usuario se pierde. 

---

### 4. Prevención de deadlock en transferencias por ordenamiento de UUID

**Que elegi:** Antes de hacer los dos `SELECT FOR UPDATE`, se ordena los wallet IDs de menor a mayor y siempre se bloquean en ese orden.

**Por qué:** Como se explico en el flujo de la transferencia, si la transferencia A - B y B - A llegan al mismo tiempo, cada hilo bloquea la wallet y espera a la otra de manera indefinida creando un deadlock clasico. PostgreSQL eventualmente
detecta esto y mata una de las transacciones con error, pero es una situación que no deberíamos forzar. Con el ordenamiento, ambos threads intentan bloquear la misma wallet primero (la de menor UUID). Uno lo logra y continúa, la otra espera.

**Alternativa descartada — dejar que PostgreSQL maneje el deadlock y reintentar:** Es lo que implementaria en un proyecto más simple. Funciona, pero obliga a lógica de retry en la capa de servicio y expone errores de DB al cliente si los reintentos se agotan.

---

### 5. Un solo COMMIT al final de las operaciones de escritura

**Que elegi:** Las operaciones de saldo (update_saldo) usan `flush()`, lo que significa que escriben el SQL en la transacción activa sin cerrarla, y el commit ocurre una sola vez al final luego de haber registrado/actualizado todo segun corresponda.

**Por qué:** Se quiere que el cambio de saldo y el registro de la transacción sean atómicos. Si hiciéramos commit del saldo y luego la inserción de la transacción fallara, el dinero habría movido pero no habría registro. 

Con flush + commit único, si algo falla en el medio, el rollback deshace todo. 

**Alternativa descartada — dos commits separados:** Rompería la atomicidad. Entre el primer y el segundo commit hay una ventana donde el sistema está en estado inconsistente.

---

### 6. Tabla transactions de tipo historial

**Que elegi:** La tabla `transactions` nunca recibe UPDATE ni DELETE, haciendola una tabla historial. Cada operación crea un registro nuevo. El campo `saldo_after` guarda el saldo del wallet en ese momento exacto.

**Por qué:** Si en algún momento hay una situacion en donde se pueda cuestionar ("¿por qué tengo $50 si debería tener $200?"), el historial completo de transacciones tiene que poder responder esa o cualquier otra pregunta. 

Si se permitieran actualizar o eliminar los registros no se podría validar el recorrido del dinero del cliente

El campo `saldo_after` es especialmente importante — no solo dice cuánto se movió, sino cuánto quedó después. Con eso se puede reconstruir el saldo en cualquier punto del tiempo sin recalcular toda la historia.

**Alternativa descartada — tabla mutable con campo `updated_at`:** Eficiente en almacenamiento, pero destruye la trazabilidad, solo me dice cuando cambio mas no el que cambio.

---

### 7. GET /wallets/me devuelve saldo + últimas 10 transacciones juntos

**Que elegi:** Este seria un endpoint de home screen en donde devuelve en una sola respuesta el saldo actual y las ultimas 10 transacciones.

**Por qué:** Estuvo inspirado en cómo funcionaba Zinli previo al cambio... ya que me di cuenta cuando estaba haciendo la prueba que Zinli cambio su pantalla de inicio y todo su UX y ahora no se ven las transacciones mas recientes. 

Cuando el usuario abria la app, quiere ver su saldo y sus últimas transacciones al mismo tiempo. Si esos fueran dos endpoints separados, la app tendría que hacer dos llamadas en paralelo (o secuenciales), lo que duplica la latencia
percibida y añade estados de loading parcial que hay que manejar en el cliente.

El historial completo y paginado vive en `/wallets/me/transactions?page=1&page_size=20` para cuando el usuario explícitamente quiere ver más.

---

### 8. Bd de relacional

**Que elegi:** Utilizar una BD relacional (PostgreSQL) sobre una NoSQL (mongo) a pesar de que pudieran haber millones de registros

**Por qué:**  Al ser un backend para un sistema bancario PostgreSQL me garantiza las transacciones ACID. Si la luz se va justo en el medio, PostgreSQL revierte automáticamente al estado anterior. 

MongoDB históricamente no tenía esa garantía a nivel de múltiples documentos (la añadió en 2018 con multi-document transactions, pero es una funcionalidad que es mas bien una simulacion).

---

## Qué cosas podrian romperse en producción? 

### 1. El escenario de key duplicada en paralelo perfecto

**Qué pasa:** Si el mismo cliente envía exactamente la misma idempotency_key dos veces
al mismo tiempo (hablamos de micro mini milisegundos), ambos requests pueden pasar el check de "ya existe esta key?" antes de que alguno haya escrito. Ambos adquieren el FOR UPDATE secuencialmente. El primero commitea. El segundo intenta commitear y la constraint UNIQUE de idempotency_key rechaza la inserción, el repositorio hace rollback y el cliente recibe un 500 o 400.

Una app bien implementada no haría esto si ya tiene una respuesta en espera no debería reenviar. 

**Qué haría al respecto:** Agregaria un distributed lock en Redis antes de entrar a la lógica de negocio. La key de Redis sería la idempotency_key misma, con TTL de 30 segundos. Si el lock ya está tomado, esperar brevemente y reintentar, o devolveria otro estatus.


---


### 5. No hay rate limiting

**Qué pasa:** Un atacante puede intentar retirar saldo con miles de requests por segundo. Aunque el FOR UPDATE serializa las escrituras, el servidor y la DB igualmente procesan cada request, lo que puede saturar el connection pool de PostgreSQL o llevar la CPU del servidor a 100%.

**Qué haría al respecto:** Añadir rate limiting por usuario, no solo por IP, en el API Gateway o con un middleware de FastAPI. Para endpoints de escritura (depósito, retiro, transferencia) un límite de 10 requests/minuto por usuario es razonable ppor ahora.

---

### 6. Una sola instancia de la app

**Qué pasa:** El sistema está diseñado para correr en un solo proceso. 

El FOR UPDATE en PostgreSQL protege la consistencia aunque haya múltiples instancias de FastAPI apuntando a la misma DB (porque el lock vive en la DB, no en la app). Pero el connection pool (`asyncpg`) no está configurado explícitamente — usa los defaults de SQLAlchemy, que pueden ser insuficientes bajo carga real.

**Qué haría al respecto:** Configurar `pool_size`, `max_overflow` y `pool_timeout` en el engine según la carga esperada. En un ambiente de producción real, añadir PgBouncer como connection pooler entre la app y PostgreSQL para manejar muchas instancias concurrentes sin saturar las conexiones de la DB.

---

### 7. Los tests corren contra SQLite, producción usa PostgreSQL

**Qué pasa:** SQLite no soporta `SELECT FOR UPDATE`. 

La implementación lo maneja capturando `CompileError` y cayendo a una lectura normal, lo que significa que los tests no pueden verificar el comportamiento de concurrencia real. Los tests prueban la lógica de negocio correctamente, pero hay una brecha entre lo que se testea y lo que corre en producción.

**Qué haría al respecto:** Para un proyecto más maduro, añadiría un segundo conjunto de tests de integración que corran contra un PostgreSQL real (en Docker, en CI). Los tests de SQLite quedarían para desarrollo rápido local; los tests de Postgres serían la garantía de que el comportamiento de concurrencia funciona como se diseñó.
