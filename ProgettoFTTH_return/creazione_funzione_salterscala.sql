

/* FUNZIONE RINOMINA/AGGIUNGI ALCUNE COLONNE ALLA TABELLA SCALA */


CREATE OR REPLACE FUNCTION public.s_alter_scala_fn(
    schemaname text,
    epsgsrid integer,
	tablename varchar default 'scala')
  RETURNS boolean AS
$BODY$
  DECLARE layerid integer;
  schemaname text := $1;
  epsg_srid integer := $2;
  table_name varchar := $3;
BEGIN


BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN gid serial;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN ebw_region TO regione;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN ebw_provin TO provincia;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN ebw_comune TO comune;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN ebw_frazio TO frazione;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN ebw_indiri TO indirizzo;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN ebw_partic TO particella;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN address_nu TO civico;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN type TO tipo;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN ebw_codice TO id_buildin;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;


BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN ebw_totale TO n_ui;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

/* da valutare
BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN ebw_numero TO ??;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;
*/

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN id_scala character varying(50);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN id_pop character varying(50);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;
BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN id_pfp character varying(20);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;
BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN id_pfs character varying(20);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;
BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN id_pd character varying(20);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN id_giunto character varying(50);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN particella character varying(24);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN codice_via character varying(24);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN nord character varying(40);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN est character varying(40);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN cod_cft character varying(5);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN enabled integer;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN tipo character varying(24);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN naming_of character varying(250);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

/*
 
BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN fo_attive character varying(50);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN n_ui_origi character int8;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

*/

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN id_sc_ref character varying(160);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s RENAME COLUMN totale_ui TO n_ui;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN n_ui integer;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN n_ui_originali integer;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('UPDATE %s.%s SET n_ui_originali = n_ui WHERE n_ui_originali IS NULL;', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN provincia character varying(250);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN comune character varying(250);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN frazione character varying(250);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;


BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN indirizzo character varying(250);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN id_buildin character varying(250);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN regione character varying(250);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN civico character varying(250);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;
  
BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN ebw_propri character varying(24);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN ebw_stato_ character varying(250);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

BEGIN
EXECUTE format('ALTER TABLE IF EXISTS %s.%s ADD COLUMN ebw_note character varying(250);', schemaname, table_name);
EXCEPTION WHEN others THEN
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;


RAISE NOTICE 'rinomina e aggiunta campi alla tabella scala FTTH ultimato';

RETURN true;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION public.s_alter_scala_fn(text, integer, varchar)
  OWNER TO operatore;
COMMENT ON FUNCTION public.s_alter_scala_fn(text, integer, varchar) IS 'rinomina e aggiunta campi alla tabella SCALA FTTH';
