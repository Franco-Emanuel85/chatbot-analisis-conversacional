-- ============================================
-- CONSULTAS PARA ANÁLISIS DE A/B TESTING
-- ============================================

-- 1. Ver asignaciones por intent
SELECT 
    intent_tag,
    variant,
    COUNT(DISTINCT session_id) as usuarios_asignados
FROM ab_assignments
GROUP BY intent_tag, variant
ORDER BY intent_tag, variant;

-- 2. Ver conversiones por intent y variante
SELECT 
    intent_tag,
    variant,
    COUNT(DISTINCT session_id) as conversiones
FROM ab_events
WHERE event_type = 'conversion'
GROUP BY intent_tag, variant;

-- 3. Tasa de conversión por variante (reporte principal)
SELECT 
    a.intent_tag,
    a.variant,
    COUNT(DISTINCT a.session_id) as usuarios,
    COUNT(DISTINCT e.session_id) as conversiones,
    ROUND(100.0 * COUNT(DISTINCT e.session_id) / COUNT(DISTINCT a.session_id), 2) as conversion_rate
FROM ab_assignments a
LEFT JOIN ab_events e 
    ON a.session_id = e.session_id 
    AND a.intent_tag = e.intent_tag 
    AND e.event_type = 'conversion'
GROUP BY a.intent_tag, a.variant
ORDER BY a.intent_tag, conversion_rate DESC;

-- 4. Mejor variante por intent
SELECT 
    intent_tag,
    variant,
    conversion_rate
FROM (
    SELECT 
        a.intent_tag,
        a.variant,
        ROUND(100.0 * COUNT(DISTINCT e.session_id) / COUNT(DISTINCT a.session_id), 2) as conversion_rate,
        ROW_NUMBER() OVER (PARTITION BY a.intent_tag ORDER BY COUNT(DISTINCT e.session_id) DESC) as rank
    FROM ab_assignments a
    LEFT JOIN ab_events e 
        ON a.session_id = e.session_id 
        AND a.intent_tag = e.intent_tag 
        AND e.event_type = 'conversion'
    GROUP BY a.intent_tag, a.variant
) WHERE rank = 1;
