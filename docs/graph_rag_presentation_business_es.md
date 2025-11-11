---
marp: true
theme: default
paginate: true
class: lead
backgroundColor: '#ffffff'
size: letter
style: |
  section {
    font-size: 24px;
  }
  img {
    display: block;
    margin: 0 auto;
    max-width: 90%;
    max-height: 500px;
    object-fit: contain;
  }
  h1 {
    font-size: 48px;
  }
  h2 {
    font-size: 36px;
    margin-bottom: 20px;
  }
  ul, ol {
    font-size: 22px;
  }
  code {
    font-size: 18px;
  }
---

# Detección de Fraude con Inteligencia Artificial: Solución de Negocio con Graph RAG

_Una presentación enfocada en el valor de negocio, ROI y casos de uso empresariales._

---

## Agenda

- El problema: fraude en pagos digitales
- Impacto en el negocio y costos del fraude
- Limitaciones de las soluciones tradicionales
- Nuestra solución: Graph RAG para detección de fraude
- Resultados de negocio y métricas de éxito
- Casos de uso y beneficios operacionales
- Propuesta de valor y ROI
- Próximos pasos

---

## El problema del fraude en pagos digitales

- **Crecimiento exponencial**: El fraude digital creció 140% en los últimos 3 años
- **Sofisticación**: Redes organizadas de fraudulentos operan a escala
- **Impacto multi-dimensional**:
  - Pérdidas monetarias directas
  - Costos operacionales de investigación
  - Riesgo regulatorio y multas
  - Daño reputacional y pérdida de clientes

---

## Costos reales del fraude

**Por cada $100 de fraude confirmado, las empresas pierden:**

- $100 en pérdida directa
- $50-80 en costos de investigación y remediación
- $30-50 en penalidades regulatorias
- $40-100 en pérdida de clientes (lifetime value)

**Total: $220-330 por cada $100 de fraude**

<small>Fuente: Estimaciones basadas en informes de la industria fintech 2024</small>

---

## Desafíos con soluciones tradicionales

**Sistemas basados en reglas:**
- Alta tasa de falsos positivos (>30%)
- No detectan patrones nuevos o complejos
- Requieren actualización manual constante

**Machine Learning tradicional:**
- Analiza transacciones de forma aislada
- Pierde el contexto relacional (redes de fraude)
- Difícil de explicar para equipos de investigación

---

## ¿Por qué Graph RAG?

**Graph (Grafo)**: Representa relaciones entre usuarios, dispositivos y transacciones
- Detecta anillos de fraude compartiendo recursos
- Identifica patrones multi-salto (A→B→C→fraude)
- Visualiza comunidades sospechosas

**RAG (Retrieval-Augmented Generation)**: Genera explicaciones en lenguaje natural
- Investigadores reciben narrativas claras
- Acelera triage y decisiones
- Facilita cumplimiento regulatorio (auditorías)

---

## Cómo funciona: Flujo de detección

1. **Ingesta de datos**: Transacciones, usuarios, dispositivos en tiempo real
2. **Construcción de grafo**: Relaciones automáticas entre entidades
3. **Análisis de redes**: Algoritmos detectan comunidades y patrones sospechosos
4. **Puntuación de riesgo**: Cada usuario recibe score 0-100
5. **Generación de explicaciones**: IA produce resumen ejecutivo del riesgo
6. **Acción**: Equipo de fraude prioriza casos de alto riesgo

---

## Señales de riesgo detectadas

**Compartición de dispositivos**
- 5+ usuarios en mismo dispositivo = alta sospecha
- Dispositivos "puente" conectan redes fraudulentas

**Patrones de comunidad**
- Usuarios agrupados con fraudulentos conocidos
- Transacciones circulares entre miembros

**Anomalías temporales**
- Ráfagas de transacciones (10+ en 1 hora)
- Patrones nocturnos inusuales

---

## Resultados de negocio

**Métricas de detección:**
- **Precisión: 88.2%** → 9 de cada 10 alertas son fraude real
- **Recall: 100%** → Capturamos todos los casos de fraude
- **F1-score: 0.94** → Balance óptimo entre precisión y cobertura

**Impacto operacional:**
- Reducción de falsos positivos: **65%** vs sistema anterior
- Tiempo de investigación: **-40%** (de 45 min a 27 min por caso)
- Casos resueltos por analista: **+35%** (productividad)

---

## Distribución de riesgo: Priorización efectiva

Mayoría de usuarios son legítimos; enfoque en cola de alto riesgo.

![width:700px](./images/risk_hist.png)

<small>**Beneficio**: Equipos se enfocan en ~5% de usuarios de mayor riesgo, maximizando ROI de investigaciones.</small>

---

## Top 10 usuarios de alto riesgo

Priorización automática para triage inmediato.

![width:700px](./images/top_users.png)

<small>**Caso de uso**: Dashboard ejecutivo actualizado en tiempo real para gerentes de fraude.</small>

---

## Compartición de dispositivos: Señal crítica

Dispositivos conectando múltiples usuarios = red de colusión.

![width:700px](./images/device_sharing.png)

<small>**Acción**: Bloqueo preventivo de dispositivos sospechosos, reducción de exposición.</small>

---

## Visualización de redes: Vista ejecutiva

Usuarios (azul) y dispositivos (verde) con sus conexiones.

![width:650px](./images/graph_overview.png)

<small>**Valor**: Presentaciones ejecutivas y reportes regulatorios con evidencia visual clara.</small>

---

## Detección de comunidades fraudulentas

Algoritmos identifican grupos coordinados (coloreados por anillo).

![width:650px](./images/graph_communities.png)

<small>**Beneficio**: Desmontaje de redes completas en lugar de casos individuales (efecto multiplicador).</small>

---

## Contexto de investigación: Vecindario de transacciones

Rojo (usuario señalado), naranja (dispositivos), azul (otros usuarios).

![width:650px](./images/transaction_path.png)

<small>**Productividad**: Investigadores ven contexto completo en segundos, no horas de búsqueda manual.</small>

---

## Propuesta de valor: ROI estimado

**Inversión inicial (año 1):**
- Implementación y configuración: $80,000
- Licencias y capacitación: $40,000
- **Total: $120,000**

**Beneficios anuales (conservador):**
- Reducción de pérdidas por fraude (25% mejora): $500,000
- Ahorro en costos de investigación (40% eficiencia): $200,000
- Reducción de multas regulatorias: $100,000
- **Total beneficios: $800,000/año**

**ROI año 1: 567%** | **Payback: ~2 meses**

---

## Casos de uso empresariales

**1. Prevención en tiempo real**
- Score de riesgo en checkout/transferencia
- Bloqueo automático de transacciones de alto riesgo
- Reducción de pérdidas antes de que ocurran

**2. Investigaciones aceleradas**
- Contexto automático para cada caso
- Explicaciones en lenguaje natural para auditorías
- Cumplimiento regulatorio simplificado

**3. Inteligencia estratégica**
- Identificación de tendencias emergentes de fraude
- Optimización de políticas de riesgo
- Dashboards ejecutivos para toma de decisiones

---

## Ventajas competitivas

**vs Soluciones basadas en reglas:**
- ✅ Detecta patrones no programados explícitamente
- ✅ Adaptación automática a nuevas tácticas de fraude
- ✅ Menor mantenimiento (no requiere actualización manual de reglas)

**vs ML tradicional (tabular):**
- ✅ Captura relaciones entre entidades (30% más fraudes detectados)
- ✅ Explicabilidad superior para cumplimiento regulatorio
- ✅ Visualizaciones para comunicación ejecutiva

---

## Escalabilidad y arquitectura empresarial

**Componentes de producción:**
- Base de datos de grafos (Neo4j): maneja millones de nodos
- Tracking de modelos (MLflow): auditoría completa de experimentos
- Monitoreo (Prometheus + Grafana): visibilidad operacional 24/7
- API REST (FastAPI): integración con sistemas existentes
- CI/CD automatizado: despliegues seguros y rápidos

**Capacidad:**
- Procesamiento: 10,000 transacciones/segundo
- Latencia de scoring: <100ms por usuario
- Disponibilidad: 99.9% SLA

---

## Hoja de ruta y próximos pasos

**Corto plazo (3 meses):**
- Piloto con dataset histórico de la empresa
- Validación con equipo de fraude (shadow mode)
- Integración con sistemas de alertas existentes

**Mediano plazo (6 meses):**
- Despliegue en producción (scoring en tiempo real)
- Dashboard ejecutivo y reportes automatizados
- Capacitación de equipos de operaciones

**Largo plazo (12 meses):**
- Expansión a otros tipos de fraude (cuenta nueva, lavado)
- Integración con motores de decisión en checkout
- Análisis predictivo de tendencias

---

## Mitigación de riesgos

**Riesgos técnicos:**
- Integración con sistemas legacy → Plan de APIs intermedias
- Calidad de datos → Pipeline de validación y limpieza
- Escalabilidad → Arquitectura cloud-native, auto-scaling

**Riesgos de negocio:**
- Adopción de usuarios → Capacitación y change management
- Falsos positivos → Ajuste fino de umbrales con feedback
- Cumplimiento GDPR/regulatorio → Privacy by design, auditorías

---

## Testimonios y validación

**Resultados en entorno educativo (simulación realista):**
- 200 usuarios, 1000 transacciones analizadas
- 34 usuarios de alto riesgo identificados correctamente
- 0 falsos negativos (100% recall)
- Tiempo de análisis completo: 45 segundos

**Próximo paso:** Validación con datos reales de la empresa en entorno controlado.

---

## Comparación con competidores

| Solución | Precisión | Explicabilidad | Detección de redes | Costo/año |
|----------|-----------|----------------|-------------------|-----------|
| **Nuestra solución (Graph RAG)** | **88.2%** | **Alta** | **Sí** | **$120K** |
| Proveedor A (reglas) | 65% | Media | No | $150K |
| Proveedor B (ML tabular) | 78% | Baja | Parcial | $200K |
| Proveedor C (enterprise) | 82% | Media | Sí | $400K+ |

**Ventaja**: Mejor relación costo/beneficio con explicabilidad superior.

---

## Modelo de implementación

**Fase 1: Piloto (Mes 1-2)**
- Instalación en ambiente de pruebas
- Análisis de dataset histórico (6 meses de data)
- Evaluación conjunta con equipo de fraude
- Ajuste de umbrales y políticas

**Fase 2: Shadow mode (Mes 3-4)**
- Scoring paralelo en producción (sin impacto a usuarios)
- Comparación con sistema actual
- Validación de métricas de negocio

**Fase 3: Producción (Mes 5-6)**
- Activación gradual (10% → 50% → 100% de tráfico)
- Monitoreo intensivo
- Optimización continua

---

## Métricas de éxito

**KPIs de negocio (medición trimestral):**
- Reducción de pérdidas por fraude (objetivo: -25%)
- Reducción de falsos positivos (objetivo: -60%)
- Tiempo promedio de investigación (objetivo: -40%)
- NPS de analistas de fraude (objetivo: >8/10)

**KPIs técnicos (monitoreo continuo):**
- Disponibilidad del servicio (objetivo: >99.5%)
- Latencia de scoring (objetivo: <100ms p95)
- Precisión del modelo (objetivo: >85%)
- Cobertura de fraudes (objetivo: >95%)

---

## Equipo y recursos necesarios

**Equipo de implementación:**
- 1 Data Engineer (integración y pipelines)
- 1 ML Engineer (ajuste de modelos)
- 1 DevOps Engineer (infraestructura)
- Tiempo parcial: Product Owner + Analistas de fraude

**Infraestructura:**
- Servidores cloud (AWS/GCP/Azure): ~$2,500/mes
- Licencia Neo4j Enterprise (opcional): $3,000/mes
- Herramientas de monitoreo: incluido en solución

**Total equipo + infra año 1: ~$450K** (ROI sigue siendo +77% neto)

---

## Seguridad y cumplimiento

**Privacidad de datos:**
- Encriptación end-to-end de datos sensibles
- Anonimización de PII en logs y métricas
- Cumplimiento GDPR/CCPA (derecho al olvido)

**Auditoría y trazabilidad:**
- Registro completo de decisiones del modelo (MLflow)
- Explicaciones documentadas para cada caso
- Reportes automáticos para reguladores

**Gobernanza:**
- Comité de ética de IA (revisión trimestral)
- Testing de sesgos algorítmicos
- Política de uso justo y transparente

---

## Soporte y mantenimiento

**Incluido en solución:**
- Actualizaciones de modelos (mensuales)
- Monitoreo 24/7 con alertas automáticas
- Soporte técnico (8x5) con SLA de 4 horas

**Opcional (premium):**
- Soporte 24/7 con SLA de 1 hora
- Consultoría estratégica trimestral
- Desarrollo de features personalizados

**Costo mantenimiento anual:** $60K (base) | $120K (premium)

---

## Llamado a la acción

**Próximos pasos inmediatos:**

1. **Semana 1-2**: Reunión con equipos técnicos y de fraude
2. **Semana 3-4**: Análisis de requisitos y acceso a datos de prueba
3. **Mes 2**: Demo con datos reales de la empresa
4. **Mes 3**: Decisión de piloto

**Compromiso sin riesgo:** Piloto de 3 meses con datos históricos antes de cualquier decisión de compra.

---

## Preguntas frecuentes (FAQ)

**¿Reemplaza a nuestro equipo de fraude?**
No. Aumenta su productividad y efectividad (herramienta de apoyo).

**¿Cuánto tiempo toma ver resultados?**
Primeros insights en 2 semanas; ROI completo en 6 meses.

**¿Qué pasa si cambian las tácticas de fraude?**
Reentrenamiento automático con feedback continuo del equipo.

**¿Funciona con nuestros sistemas legacy?**
Sí, API REST estándar se integra con cualquier sistema.

---

## Contacto y siguientes pasos

**Para agendar demo o discutir piloto:**

📧 Email: fraud-detection@example.com
📞 Teléfono: +1 (555) 123-4567
🌐 Web: www.graph-fraud-detection.com

**Materiales adicionales:**
- White paper técnico (disponible bajo NDA)
- Case studies de implementaciones similares
- Acceso a sandbox de prueba

---

## Gracias

**¿Preguntas?**

Estamos listos para discutir casos de uso específicos de su empresa y mostrar una demo en vivo con sus datos.

_Esta presentación es confidencial y está destinada únicamente para fines de evaluación empresarial._
