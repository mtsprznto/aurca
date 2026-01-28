# AURCA (Autonomous Recursive Crypto-Agent)

> Visión: Un sistema agéntico capaz de realizar autocrítica y refinamiento de pesos matemáticos mediante un bucle de retroalimentación constante con la API de Binance.


## Informe Técnico: Arquitectura y Mejores Prácticas 2026

### Filosofía de Diseño: El Bucle de Recurrencia

Para que un agente sea su propio maestro, debe operar bajo una función de pérdida auto-evaluada. Matemáticamente, definimos su aprendizaje como la minimización del error de predicción $E$ en el tiempo $t$:

$$E_t = \sum_{i=1}^{n} w_i |P_{t+i} - \hat{P}_{t+i}| + \Omega(\theta)$$

Donde $\hat{P}$ es el precio predicho, $P$ el real, y $\Omega(\theta)$ representa una penalización por complejidad para evitar el overfitting (sobreajuste) a ruidos del mercado.

### Mejores Prácticas (Estándares 2026)

- **Seguridad Asimétrica:** Olvida las claves HMAC tradicionales. En 2026, el estándar de Binance es Ed25519. Es más rápido, más corto y mucho más seguro (basado en curvas elípticas).

- **Modularidad Políglota:** * C++: Manejo de WebSockets y serialización de datos (Latencia < 1ms).

    - **Python:** Orquestación de IA y lógica de Reinforcement Learning.

- **Observabilidad:** Implementar Structured Logging para que el agente pueda leer sus propios logs de errores y entender por qué una predicción falló.

- **Capa Gratuita (Rate Limiting):** El agente debe ser "consciente" de su propio consumo. Implementaremos un Token Bucket Algorithm para no exceder los 1,200 pesos de la API de Binance por minuto.

### Estructura de Carpetas Profesional

~~~
AURCA/
├── docs/                   # Informe técnico, diagramas y notas de API
├── src/
│   ├── aurca_core/         # Módulos de alto rendimiento (C++)
│   │   ├── include/        # Headers (.h)
│   │   ├── lib/            # Bindings (pybind11)
│   │   └── websocket.cpp   # Conexión binaria ultra-rápida
│   ├── aurca_agent/        # Lógica de Inteligencia Artificial
│   │   ├── brain/          # Arquitectura del Modelo (Transformers/RL)
│   │   ├── teacher/        # Módulo de auto-evaluación y crítica
│   │   └── memory/         # Interfaz con base de datos vectorial
│   └── aurca_data/         # Gestión de datos e ingestión
│       ├── database/       # Migraciones SQL y TimescaleDB
│       └── binance_api/    # Cliente modular de Binance
├── tests/                  # Pruebas unitarias y de integración
├── docker/                 # Archivos de despliegue (PostgreSQL, Redis)
├── .env.example            # Plantilla de secretos (NUNCA subir claves reales)
└── README.md               # Puerta de entrada al proyecto
~~~

### Guía de Inicio: Obtención de la API (Saneando dudas)

Para el agente, se necesita usar la interfaz WEB para la creación inicial de las llaves por estas razones:

1. Generación de Llaves RSA/Ed25519: La versión web permite subir tu llave pública de manera más limpia y segura.

2. Gestión de IP: Es obligatorio restringir el acceso a tu IP específica para habilitar permisos de lectura y trading. Esto se gestiona mejor desde el panel web.

**Pasos Clave (Actualizado 2026):**

- **Tipo de Llave:** Elige "Generada por el usuario" (Asimétrica).

- **Permisos:** Activa solo "Habilitar Lectura". No habilites trading ni retiros hasta que la fase de predicción tenga una precisión del 80% en Paper Trading.

- **Activación:** Como indica tu texto, asegúrate de tener una verificación de identidad (KYC) completa y un depósito mínimo para activar la cuenta de API.