-- Phase 14: optimize owner RLS helper evaluation without changing authorization semantics.
-- Wrap the per-request JWT claim lookup in a scalar subquery so PostgreSQL
-- evaluates the stable request value once per statement instead of once per row.
DO $$
DECLARE
    policy_row record;
    using_expr text;
    check_expr text;
BEGIN
    FOR policy_row IN
        SELECT
            n.nspname AS schema_name,
            c.relname AS table_name,
            p.polname AS policy_name,
            pg_get_expr(p.polqual, p.polrelid) AS using_expr,
            pg_get_expr(p.polwithcheck, p.polrelid) AS check_expr
        FROM pg_policy p
        JOIN pg_class c ON c.oid = p.polrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND (
              pg_get_expr(p.polqual, p.polrelid) LIKE '%current_setting(''request.jwt.claim.sub''%'
              OR pg_get_expr(p.polwithcheck, p.polrelid) LIKE '%current_setting(''request.jwt.claim.sub''%'
          )
    LOOP
        using_expr := replace(
            policy_row.using_expr,
            'current_setting(''request.jwt.claim.sub'', true)',
            '(select current_setting(''request.jwt.claim.sub'', true))'
        );
        check_expr := CASE
            WHEN policy_row.check_expr IS NULL THEN NULL
            ELSE replace(
                policy_row.check_expr,
                'current_setting(''request.jwt.claim.sub'', true)',
                '(select current_setting(''request.jwt.claim.sub'', true))'
            )
        END;

        IF policy_row.check_expr IS NULL THEN
            EXECUTE format(
                'ALTER POLICY %I ON %I.%I USING (%s)',
                policy_row.policy_name,
                policy_row.schema_name,
                policy_row.table_name,
                using_expr
            );
        ELSE
            EXECUTE format(
                'ALTER POLICY %I ON %I.%I USING (%s) WITH CHECK (%s)',
                policy_row.policy_name,
                policy_row.schema_name,
                policy_row.table_name,
                using_expr,
                check_expr
            );
        END IF;
    END LOOP;
END
$$;
