DO $migration$
DECLARE
  concepts_table CONSTANT REGCLASS := 'public.concepts'::regclass;
  name_attnum SMALLINT;
  owner_attnum SMALLINT;
  uniqueness RECORD;
  existing_index RECORD;
  collision RECORD;
BEGIN
  SELECT attnum INTO name_attnum
  FROM pg_attribute
  WHERE attrelid = concepts_table AND attname = 'name' AND NOT attisdropped;

  SELECT attnum INTO owner_attnum
  FROM pg_attribute
  WHERE attrelid = concepts_table AND attname = 'owner_id' AND NOT attisdropped;

  IF name_attnum IS NULL OR owner_attnum IS NULL THEN
    RAISE EXCEPTION 'Cannot apply concepts owner uniqueness: public.concepts.name or owner_id is missing';
  END IF;

  FOR uniqueness IN
    SELECT i.indexrelid, index_class.relname AS index_name,
           index_namespace.nspname AS index_schema, access_method.amname,
           opclass.opcdefault, i.indcollation[0] AS index_collation,
           name_attribute.attcollation AS column_collation, i.indnatts,
           constraint_row.conname, constraint_row.contype
    FROM pg_index i
    JOIN pg_class index_class ON index_class.oid = i.indexrelid
    JOIN pg_namespace index_namespace ON index_namespace.oid = index_class.relnamespace
    JOIN pg_am access_method ON access_method.oid = index_class.relam
    JOIN pg_opclass opclass ON opclass.oid = i.indclass[0]
    JOIN pg_attribute name_attribute
      ON name_attribute.attrelid = concepts_table
     AND name_attribute.attnum = name_attnum
    LEFT JOIN pg_constraint constraint_row ON constraint_row.conindid = i.indexrelid
    WHERE i.indrelid = concepts_table
      AND i.indisunique
      AND i.indnkeyatts = 1
      AND i.indkey[0] = name_attnum
      AND i.indexprs IS NULL
      AND i.indpred IS NULL
  LOOP
    IF uniqueness.contype = 'p' THEN
      RAISE EXCEPTION
        'Cannot replace global concepts.name uniqueness: index % is a primary key',
        uniqueness.index_schema || '.' || uniqueness.index_name;
    END IF;

    IF uniqueness.indnatts <> 1 THEN
      RAISE EXCEPTION
        'Cannot safely identify global concepts.name uniqueness: index % includes additional columns',
        uniqueness.index_schema || '.' || uniqueness.index_name;
    END IF;

    IF NOT uniqueness.opcdefault
       OR uniqueness.amname <> 'btree'
       OR uniqueness.index_collation IS DISTINCT FROM uniqueness.column_collation THEN
      RAISE EXCEPTION
        'Cannot safely identify global concepts.name uniqueness: index % has non-default uniqueness semantics',
        uniqueness.index_schema || '.' || uniqueness.index_name;
    END IF;

    IF uniqueness.conname IS NOT NULL AND uniqueness.contype <> 'u' THEN
      RAISE EXCEPTION
        'Cannot safely replace global concepts.name uniqueness: index % is backing constraint %',
        uniqueness.index_schema || '.' || uniqueness.index_name, uniqueness.conname;
    END IF;

    IF uniqueness.conname IS NOT NULL THEN
      EXECUTE format('ALTER TABLE public.concepts DROP CONSTRAINT %I', uniqueness.conname);
    ELSE
      EXECUTE format(
        'DROP INDEX %I.%I',
        uniqueness.index_schema,
        uniqueness.index_name
      );
    END IF;
  END LOOP;

  IF EXISTS (
    SELECT 1
    FROM pg_index i
    CROSS JOIN LATERAL generate_series(1, i.indnkeyatts) AS key_positions(position)
    WHERE i.indrelid = concepts_table
      AND i.indisunique
      AND (
        to_regclass('public.uq_concepts_owner_name') IS NULL
        OR i.indexrelid <> to_regclass('public.uq_concepts_owner_name')
      )
      AND pg_get_indexdef(i.indexrelid, key_positions.position, TRUE)
          ~* '(^|[^[:alnum:]_])"?name"?([^[:alnum:]_]|$)'
  ) THEN
    RAISE EXCEPTION
      'Cannot safely replace global concepts.name uniqueness: another unique index involving name has an unexpected definition';
  END IF;

  IF to_regclass('public.uq_concepts_owner_name') IS NOT NULL THEN
    SELECT index_class.relname AS index_name,
           i.indisunique AND NOT i.indisprimary
           AND i.indisvalid AND i.indisready
           AND i.indnkeyatts = 2 AND i.indnatts = 2
           AND i.indkey[0] = owner_attnum AND i.indkey[1] = 0
           AND i.indexprs IS NOT NULL AND i.indpred IS NOT NULL
           AND lower(regexp_replace(pg_get_expr(i.indexprs, i.indrelid), '[[:space:]()]', '', 'g')) = 'lowername'
           AND lower(regexp_replace(pg_get_expr(i.indpred, i.indrelid), '[[:space:]()]', '', 'g')) = 'owner_idisnotnull'
           AND access_method.amname = 'btree'
           AND owner_opclass.opcdefault AND name_opclass.opcdefault
           AND i.indcollation[0] = owner_attribute.attcollation
           AND i.indcollation[1] = name_attribute.attcollation AS is_expected
    INTO existing_index
    FROM pg_class index_class
    JOIN pg_namespace index_namespace ON index_namespace.oid = index_class.relnamespace
    LEFT JOIN pg_index i ON i.indexrelid = index_class.oid
    LEFT JOIN pg_am access_method ON access_method.oid = index_class.relam
    LEFT JOIN pg_opclass owner_opclass ON owner_opclass.oid = i.indclass[0]
    LEFT JOIN pg_opclass name_opclass ON name_opclass.oid = i.indclass[1]
    LEFT JOIN pg_attribute owner_attribute
      ON owner_attribute.attrelid = concepts_table AND owner_attribute.attnum = owner_attnum
    LEFT JOIN pg_attribute name_attribute
      ON name_attribute.attrelid = concepts_table AND name_attribute.attnum = name_attnum
    WHERE index_namespace.nspname = 'public'
      AND index_class.relname = 'uq_concepts_owner_name';

    IF NOT FOUND THEN
      RAISE EXCEPTION
        'Cannot create owner-scoped concept uniqueness: public.uq_concepts_owner_name exists with an unexpected definition';
    END IF;

    IF existing_index.is_expected IS DISTINCT FROM TRUE THEN
      RAISE EXCEPTION
        'Cannot create owner-scoped concept uniqueness: public.uq_concepts_owner_name exists with an unexpected definition';
    END IF;
  END IF;

  SELECT owner_id, lower(name) AS normalized_name,
         string_agg(id, ', ' ORDER BY id) AS concept_ids
  INTO collision
  FROM public.concepts
  WHERE owner_id IS NOT NULL
  GROUP BY owner_id, lower(name)
  HAVING count(*) > 1
  ORDER BY owner_id, lower(name)
  LIMIT 1;

  IF FOUND THEN
    RAISE EXCEPTION
      'Cannot create owner-scoped concept uniqueness: owner_id %, normalized name %, concept IDs % collide',
      collision.owner_id, collision.normalized_name, collision.concept_ids;
  END IF;
END
$migration$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_concepts_owner_name
  ON public.concepts(owner_id, lower(name))
  WHERE owner_id IS NOT NULL;
