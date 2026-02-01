-- Agendamento de tarefas de manutenção
-- Vacuum diário (não-full) para tabela principal
CREATE OR REPLACE PROCEDURE perform_daily_vacuum()
LANGUAGE plpgsql
AS $$
BEGIN
    VACUUM (ANALYZE) registrations;
END;
$$;

-- Agendador para vacuum diário
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_proc 
        WHERE proname = 'perform_daily_vacuum'
    ) THEN
        PERFORM cron.schedule(
            'daily-vacuum',
            '0 3 * * *', -- Todos os dias às 3h
            'CALL perform_daily_vacuum()'
        );
    END IF;
END;
$$;

-- Atualização semanal de views materializadas
CREATE OR REPLACE PROCEDURE refresh_materialized_views()
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM refresh_materialized_views_concurrently();
END;
$$;

-- Agendador para atualização semanal
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_proc 
        WHERE proname = 'refresh_materialized_views'
    ) THEN
        PERFORM cron.schedule(
            'weekly-refresh-views',
            '0 4 * * 0', -- Domingo às 4h
            'CALL refresh_materialized_views()'
        );
    END IF;
END;
$$;

-- Backup lógico diário (via pg_dump)
-- Nota: Requer configuração externa do pgBackRest/Barman
-- COMMENT ON DATABASE current_database() IS 'Configurar pgBackRest para backups diários completos e incrementais';
