

/* FUNZIONE RINOMINA/AGGIUNGI ALCUNE COLONNE ALLE TABELLE tranne SCALA */


CREATE OR REPLACE FUNCTION public.s_alter_table_fn(
    schemaname text,
    epsgsrid integer)
  RETURNS boolean AS
$BODY$
  DECLARE layerid integer;
  schemaname text := $1;
  epsg_srid integer := $2;
BEGIN


BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN cod_belf character varying(5);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN lotto character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN cod_geom integer;', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN id_pop_end character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;


BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo RENAME COLUMN posa TO tipo_posa;', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN tipo_posa character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN tipo_minit character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN codice_inf character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN tipo_pav character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN n_mtubo character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN n_tubi character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN d_tubi character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN libero character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN n_mt_occ character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN mod_mtubo character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN flag_posa character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN posa_dett character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN tipo_scavo character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;


BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo ADD COLUMN length_m double precision;', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;


--Nuove colonne WALKOUT:
BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo
ADD COLUMN wo varchar(6),
ADD COLUMN tubi int2,
ADD COLUMN tubo1diam int2,
ADD COLUMN tubo1liber int2,
ADD COLUMN tubo2diam int2,
ADD COLUMN tubo2liber int2,
ADD COLUMN tubo3diam int2,
ADD COLUMN tubo3liber int2,
ADD COLUMN tubo4diam int2,
ADD COLUMN tubo4liber int2,
ADD COLUMN tubo5diam int2,
ADD COLUMN tubo5liber int2,
ADD COLUMN tubo6diam int2,
ADD COLUMN tubo6liber int2,
ADD COLUMN tubo7diam int2,
ADD COLUMN tubo7liber int2,
ADD COLUMN tubo8diam int2,
ADD COLUMN tubo8liber int2,
ADD COLUMN tubo9diam int2,
ADD COLUMN tubo9liber int2,
ADD COLUMN tubo10diam int2,
ADD COLUMN tubo10liber int2,
ADD COLUMN tubo11diam int2,
ADD COLUMN tubo11liber int2,
ADD COLUMN tubo12diam int2,
ADD COLUMN tubo12liber int2;', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo
ADD COLUMN n_mt_occ_CD character varying(50),
ADD COLUMN n_mt_occ_1 character varying(50),
ADD COLUMN n_mt_occ_2 character varying(50);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.giunti
ADD COLUMN wo varchar(6),
ADD COLUMN tipo varchar(25),
ADD COLUMN proprieta varchar(25),
ADD COLUMN note text;', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.pd
ADD COLUMN wo varchar(6),
ADD COLUMN tipo varchar(25),
ADD COLUMN proprieta varchar(25),
ADD COLUMN note text;', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.pozzetto
ADD COLUMN wo varchar(6),
ADD COLUMN stato varchar(50),
ADD COLUMN chiuso varchar(30),
ADD COLUMN marchio varchar(30),
ADD COLUMN lato_1 varchar(10),
ADD COLUMN lato_2 varchar(10),
ADD COLUMN lato_3 varchar(10),
ADD COLUMN lato_4 varchar(10),
ADD COLUMN foto_l1 varchar(250),
ADD COLUMN progetto varchar(25),
ADD COLUMN proprieta varchar(25),
ADD COLUMN cassetta_ed varchar(2),
ADD COLUMN foto_l2 varchar(250),
ADD COLUMN foto_l3 varchar(250),
ADD COLUMN foto_l4 varchar(250);', schemaname);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;


RAISE NOTICE 'rinomina e aggiunta campi alle tabelle FTTH ultimato';

RETURN true;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION public.s_alter_table_fn(text, integer)
  OWNER TO operatore;
COMMENT ON FUNCTION public.s_alter_table_fn(text, integer) IS 'rinomina e aggiunta campi alle tabelle FTTH tranne SCALA';
