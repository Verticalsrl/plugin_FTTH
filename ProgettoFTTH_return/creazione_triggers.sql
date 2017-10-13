/* CREAZIONE FUNZIONI TRIGGER */
--In questo caso non ho bisogno di associare questi trigger alle tabelle, perche' tanto sono e resteranno vuote. Quando l'utente inizializzera' il suo schema di lavoro sara' la procedura in python del plgin ad associare queste funzioni alle tabelle relative

--al fondo, creo le funzioni per splittare cavo lungo i nodi che intersecano i nodi di altre linee: varie funzioni "split_lines_to_lines_*"

BEGIN;

CREATE OR REPLACE FUNCTION delete_giunto()
  RETURNS trigger AS
$BODY$
declare my_schema text;
declare old_id text;
declare old_ui integer;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
old_id := OLD.id_giunto;
old_ui := coalesce(OLD.n_ui, 0);
--Intercetto le SCALE connesse e ne annullo TUTTE le connessioni:
UPDATE scala SET id_giunto=NULL, id_pd=NULL, id_pfs=NULL, id_pfp=NULL WHERE id_giunto = old_id;
--Intercetto GIUNTI_FIGLI connessi e ne annullo TUTTE le connessioni:
UPDATE giunti SET id_g_ref=NULL, id_pd=NULL, id_pfs=NULL, id_pfp=NULL WHERE id_g_ref = old_id;
IF (OLD.id_g_ref IS NOT NULL) THEN --il giunto e' FIGLIO!!
  --Intercetto GIUNTI_FIGLI connessi e ne annullo TUTTE le connessioni:
  --UPDATE giunti SET id_g_ref=NULL, id_pd=NULL, id_pfs=NULL, id_pfp=NULL WHERE id_g_ref = old_id;
  --Aggiorno i PADRI scalando CONT e UI:
  UPDATE giunti SET n_cont=n_cont-1, n_ui=n_ui-old_ui WHERE id_giunto=OLD.id_g_ref;
  UPDATE pd SET n_ui=n_ui-old_ui WHERE id_pd=OLD.id_pd;
  UPDATE pfs SET n_ui=n_ui-old_ui WHERE id_pfs=OLD.id_pfs;
  UPDATE pfp SET n_ui=n_ui-old_ui WHERE id_pfp=OLD.id_pfp;
ELSIF (OLD.id_g_ref IS NULL) THEN
  --Poi aggiorno i PADRI scalando CONT e UI:
  UPDATE pd SET n_giunti=n_giunti-1, n_cont=n_cont-1, n_ui=n_ui-old_ui WHERE id_pd=OLD.id_pd;
  UPDATE pfs SET n_ui=n_ui-old_ui WHERE id_pfs=OLD.id_pfs;
  UPDATE pfp SET n_ui=n_ui-old_ui WHERE id_pfp=OLD.id_pfp;
END IF;
EXECUTE 'SET search_path = public, topology;';
RETURN NULL;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION delete_giunto() OWNER TO operatore;
  
CREATE OR REPLACE FUNCTION delete_pd()
  RETURNS trigger AS
$BODY$
declare my_schema text;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
--Intercetto le SCALE connesse e ne annullo TUTTE le connessioni:
UPDATE scala SET id_pd=NULL, id_pfs=NULL, id_pfp=NULL WHERE id_pd = OLD.id_pd;
--Intercetto i GIUNTI connessi e ne annullo TUTTE le connessioni:
UPDATE giunti SET id_pd=NULL, id_pfs=NULL, id_pfp=NULL WHERE id_pd = OLD.id_pd;
--Intercetto PD figli connessi:
UPDATE pd SET id_pd_ref=NULL, id_pfs=NULL, id_pfp=NULL WHERE id_pd_ref = OLD.id_pd;

--Aggiorno i PADRI scalando CONT e UI:
UPDATE pfs SET n_pd=n_pd-1, n_ui=n_ui-coalesce(OLD.n_ui, 0) WHERE id_pfs=OLD.id_pfs;
UPDATE pfp SET n_ui=n_ui-coalesce(OLD.n_ui, 0) WHERE id_pfp=OLD.id_pfp;
UPDATE pd SET n_cont=n_cont-1, n_ui=n_ui-coalesce(OLD.n_ui, 0) WHERE id_pd=OLD.id_pd_ref;
EXECUTE 'SET search_path = public, topology;';
RETURN NULL;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION delete_pd() OWNER TO operatore;

CREATE OR REPLACE FUNCTION delete_pfp()
  RETURNS trigger AS
$BODY$
declare my_schema text;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
--Intercetto le SCALE connesse e ne annullo TUTTE le connessioni:
UPDATE scala SET id_pfp=NULL WHERE id_pfp = OLD.id_pfp;
--Intercetto i GIUNTI connessi e ne annullo TUTTE le connessioni:
UPDATE giunti SET id_pfp=NULL WHERE id_pfp = OLD.id_pfp;
--Intercetto i PD connessi e ne annullo TUTTE le connessioni:
UPDATE pd SET id_pfp=NULL WHERE id_pfp = OLD.id_pfp;
--Intercetto i PFS connessi e ne annullo TUTTE le connessioni:
UPDATE pfs SET id_pfp=NULL WHERE id_pfp = OLD.id_pfp;
EXECUTE 'SET search_path = public, topology;';
RETURN NULL;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION delete_pfp()
  OWNER TO operatore;

CREATE OR REPLACE FUNCTION delete_pfs()
  RETURNS trigger AS
$BODY$
declare my_schema text;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
--Intercetto le SCALE connesse e ne annullo TUTTE le connessioni:
UPDATE scala SET id_pfs=NULL, id_pfp=NULL WHERE id_pfs = OLD.id_pfs;
--Intercetto i GIUNTI connessi e ne annullo TUTTE le connessioni:
UPDATE giunti SET id_pfs=NULL, id_pfp=NULL WHERE id_pfs = OLD.id_pfs;
--Intercetto i PD connessi e ne annullo TUTTE le connessioni:
UPDATE pd SET id_pfs=NULL, id_pfp=NULL WHERE id_pfs = OLD.id_pfs;

--Aggiorno i PADRI scalando CONT e UI:
UPDATE pfp SET n_pfs=n_pfs-1, n_ui=n_ui-OLD.n_ui WHERE id_pfp=OLD.id_pfp;
EXECUTE 'SET search_path = public, topology;';
RETURN NULL;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION delete_pfs() OWNER TO operatore;

CREATE OR REPLACE FUNCTION delete_scala()
  RETURNS trigger AS
$BODY$
declare my_schema text;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
--Nel caso di ELIMINAZIONE di UNA SCALA aggiorno solo i PADRI:
if (OLD.id_giunto IS NOT NULL) THEN
  --La scala e' connessa ad un giunto:
  UPDATE giunti SET n_cont=n_cont-1, n_ui=n_ui-OLD.n_ui WHERE id_giunto=OLD.id_giunto;
  UPDATE pd SET n_ui=n_ui-OLD.n_ui WHERE id_pd=OLD.id_pd;
  UPDATE pfs SET n_ui=n_ui-OLD.n_ui WHERE id_pfs=OLD.id_pfs;
  UPDATE pfp SET n_ui=n_ui-OLD.n_ui WHERE id_pfp=OLD.id_pfp;
ELSIF (OLD.id_pd IS NOT NULL) THEN
  --La scala e' connessa ad un pd:
  UPDATE pd SET n_cont=n_cont-1, n_ui=n_ui-OLD.n_ui WHERE id_pd=OLD.id_pd;
  UPDATE pfs SET n_ui=n_ui-OLD.n_ui WHERE id_pfs=OLD.id_pfs;
  UPDATE pfp SET n_ui=n_ui-OLD.n_ui WHERE id_pfp=OLD.id_pfp;
ELSE
  UPDATE pfs SET n_ui=n_ui-OLD.n_ui WHERE id_pfs=OLD.id_pfs;
  UPDATE pfp SET n_ui=n_ui-OLD.n_ui WHERE id_pfp=OLD.id_pfp;
END IF;
EXECUTE 'SET search_path = public, topology;';
RETURN NULL;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION delete_scala() OWNER TO operatore;

CREATE OR REPLACE FUNCTION update_giunto()
  RETURNS trigger AS
$BODY$
declare codpop integer;
declare my_schema text;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
SELECT id_pop INTO codpop FROM variabili_progetto_return WHERE cod_belf = NEW.cod_belf AND lotto = NEW.lotto;
NEW.id_g_num := ('9'::text||lpad(NEW.gid::text, 5, '0'))::integer;
NEW.id_giunto := NEW.cod_belf || NEW.lotto || ('9'::text||lpad(NEW.gid::text, 5, '0'));
--NEW.id_pop := codpop; --lo setto da DEFAULT
EXECUTE 'SET search_path = public, topology;';
NEW.coord_e := ST_X(NEW.geom)::double precision;
NEW.coord_n := ST_Y(NEW.geom)::double precision;
RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION update_giunto() OWNER TO operatore;
  
CREATE OR REPLACE FUNCTION update_pd()
  RETURNS trigger AS
$BODY$
declare codpop integer;
declare my_schema text;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
SELECT id_pop INTO codpop FROM variabili_progetto_return WHERE cod_belf = NEW.cod_belf AND lotto = NEW.lotto;
NEW.id_pd_num := ('6'::text||lpad(NEW.gid::text, 5, '0'))::integer;
NEW.id_pd := NEW.cod_belf || NEW.lotto || ('6'::text||lpad(NEW.gid::text, 5, '0'));
--NEW.id_pop := codpop; --lo setto da DEFAULT
EXECUTE 'SET search_path = public, topology;';
NEW.coord_e := ST_X(NEW.geom)::double precision;
NEW.coord_n := ST_Y(NEW.geom)::double precision;
RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION update_pd() OWNER TO operatore;
  
CREATE OR REPLACE FUNCTION update_pfp()
  RETURNS trigger AS
$BODY$
declare codpop integer;
declare my_schema text;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
SELECT id_pop INTO codpop FROM variabili_progetto_return WHERE cod_belf = NEW.cod_belf AND lotto = NEW.lotto;
NEW.id_pfp_num := ('2'::text||lpad(NEW.gid::text, 5, '0'))::integer;
NEW.id_pfp := NEW.cod_belf || NEW.lotto || ('2'::text||lpad(NEW.gid::text, 5, '0'));
--NEW.id_pop := codpop; --lo setto da DEFAULT
EXECUTE 'SET search_path = public, topology;';
NEW.coord_e := ST_X(NEW.geom)::double precision;
NEW.coord_n := ST_Y(NEW.geom)::double precision;
RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION update_pfp() OWNER TO operatore;
  
CREATE OR REPLACE FUNCTION update_pfs()
  RETURNS trigger AS
$BODY$
declare codpop integer;
declare my_schema text;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
SELECT id_pop INTO codpop FROM variabili_progetto_return WHERE cod_belf = NEW.cod_belf AND lotto = NEW.lotto;
NEW.id_pfs_num := ('5'::text||lpad(NEW.gid::text, 5, '0'))::integer;
NEW.id_pfs := NEW.cod_belf || NEW.lotto || ('5'::text||lpad(NEW.gid::text, 5, '0'));
--NEW.id_pop := codpop; --lo setto da DEFAULT
EXECUTE 'SET search_path = public, topology;';
NEW.coord_e := ST_X(NEW.geom)::double precision;
NEW.coord_n := ST_Y(NEW.geom)::double precision;
RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION update_pfs() OWNER TO operatore;

CREATE OR REPLACE FUNCTION update_pop()
  RETURNS trigger AS
$BODY$
declare codpop integer;
declare my_schema text;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
SELECT id_pop INTO codpop FROM variabili_progetto_return WHERE cod_belf = NEW.cod_belf AND lotto = NEW.lotto;
NEW.id_pop_num := ('1'::text||lpad(NEW.gid::text, 5, '0'))::integer;
--NEW.id_pop := codpop; --lo setto da DEFAULT
EXECUTE 'SET search_path = public, topology;';
NEW.coord_e := ST_X(NEW.geom)::double precision;
NEW.coord_n := ST_Y(NEW.geom)::double precision;
RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION update_pop() OWNER TO operatore;

CREATE OR REPLACE FUNCTION update_pozzetto()
  RETURNS trigger AS
$BODY$
declare codpop integer;
declare my_schema text;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
SELECT id_pop INTO codpop FROM variabili_progetto_return WHERE cod_belf = NEW.cod_belf AND lotto = NEW.lotto;
NEW.cod_geom := ('3'::text||lpad(NEW.gid::text, 5, '0'))::integer;
NEW.id_pozzetto := NEW.cod_belf || NEW.lotto || ('3'::text||lpad(NEW.gid::text, 5, '0'));
--NEW.id_pop := codpop; --lo setto da DEFAULT
EXECUTE 'SET search_path = public, topology;';
NEW.pos_poz_n := ST_X(NEW.geom)::double precision;
NEW.pos_poz_e := ST_Y(NEW.geom)::double precision;
RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION update_pozzetto() OWNER TO operatore;
  
CREATE OR REPLACE FUNCTION update_cavo()
  RETURNS trigger AS
$BODY$
BEGIN
NEW.cod_geom := ('8'::text||lpad(NEW.gid::text, 5, '0'))::integer;
NEW.id_cavo := NEW.cod_belf || NEW.lotto || ('8'::text||lpad(NEW.gid::text, 5, '0'));
RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION update_cavo() OWNER TO operatore;


/* FUNZIONI SPLIT_LINES_TO_LINES */
/* prova creazione funzioni split_lines_to_lines a livello di DB sotto public una volta per tutte e non a livello di singolo schema in modo tale da facilitarne l'aggiornamento:
CREATE OR REPLACE FUNCTION split_lines_to_lines_pulizia(
    schemaname text,
    epsgsrid integer)
  RETURNS boolean AS
$BODY$
  DECLARE layerid integer;
  schema_topo text := $1||'_topo';
  schemaname text := $1;
  epsg_srid integer := $2;
BEGIN

BEGIN
EXECUTE format('SELECT topology.DropTopoGeometryColumn(''%s'', ''cavo'', ''topo_geom'')', schemaname);
EXCEPTION WHEN others THEN
--non mi interessa se da errore qui, comunque proseguo, probabilmente la topologia non e' mai stata inizializzata.
      RAISE NOTICE 'Error code: %', SQLSTATE;
      RAISE NOTICE 'Error message: %', SQLERRM;
END;

EXECUTE format('DELETE FROM topology.layer WHERE schema_name||''.''||table_name = ''%s.cavo''', schemaname);
EXECUTE format('DELETE FROM topology.topology WHERE name=''%s''', schema_topo);
EXECUTE format('DROP SCHEMA IF EXISTS %s CASCADE', schema_topo);
EXECUTE format('DROP TABLE IF EXISTS %s.cavo_corretto CASCADE', schemaname);
EXECUTE format('DROP TABLE IF EXISTS %s.cavo_vertex CASCADE', schemaname);
EXECUTE format('DROP TABLE IF EXISTS %s.cavo_finale CASCADE', schemaname);
EXECUTE format('DROP TABLE IF EXISTS %s.cavo_sporco CASCADE', schemaname);
RAISE NOTICE 'fine pulizia DB dai residui';

RETURN true;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
COMMENT ON FUNCTION split_lines_to_lines_pulizia(text, integer) IS 'pulizia residui di split_lines_to_lines precedenti';


CREATE OR REPLACE FUNCTION split_lines_to_lines_topo(
    schemaname text,
    epsgsrid integer)
  RETURNS boolean AS
$BODY$
  DECLARE layerid integer;
  schema_topo text := $1||'_topo';
  schemaname text := $1;
  epsg_srid integer := $2;
BEGIN

--PRIMO STEP: creare i vertici della linea e la topologia, assegnando gli opportuni GRANT all'utente operatore:
EXECUTE format('SELECT topology.CreateTopology(''%s'', %s) AS topo_id', schema_topo, epsg_srid) INTO layerid; --AS topo_id dovrei recuperare cosi' l'ID
RAISE NOTICE 'Recupero ID layer aggiunto alla topology';
--EXECUTE format('SELECT layer_id FROM topology.layer WHERE schema_name=''%s'' AND table_name= ''cavo''', schemaname) INTO layerid;
--layerid := (SELECT layer_id FROM topology.layer WHERE schema_name||'.'||table_name = schemaname||'.cavo');
RAISE NOTICE 'ID del layer = %' ,  layerid;

EXECUTE format('SELECT topology.AddTopoGeometryColumn(''%s'', ''%s'', ''cavo'', ''topo_geom'', ''LINESTRING'')', schema_topo, schemaname);

RETURN true;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
COMMENT ON FUNCTION split_lines_to_lines_topo(text, integer) IS 'creazione topogeometrie per split_lines_to_lines';


CREATE OR REPLACE FUNCTION split_lines_to_lines_conclusivo(
    schemaname text,
    epsgsrid integer)
  RETURNS boolean AS
$BODY$
  DECLARE layerid integer;
  DECLARE time_epoch integer;
  DECLARE chiave_pk text;
  DECLARE gid_old_esiste integer;
  schema_topo text := $1||'_topo';
  schemaname text := $1;
  epsg_srid integer := $2;
BEGIN

EXECUTE format('SELECT layer_id FROM topology.layer WHERE schema_name=''%s'' AND table_name= ''cavo''', schemaname) INTO layerid;
--layerid := (SELECT layer_id FROM topology.layer WHERE schema_name||'.'||table_name = schemaname||'.cavo');
RAISE NOTICE 'ID del layer = %' ,  layerid;

EXECUTE 'SET search_path = ' || quote_ident(schemaname) || ', ' || quote_ident(schema_topo) || ', public;';

EXECUTE format('UPDATE cavo SET topo_geom = topology.toTopoGeom(geom, ''%s'', %s)', schema_topo, layerid); --essendo all'interno di una funzione, il record non e' stato ancora creato
--SENZA TOLLERANZA! Con la tolleranza potrebbe trovare alcuni errori, meglio NIENTE

--Prima verifico esista colonna_gid_old altrimenti vuol dire che cavo e' nuovo:
EXECUTE format('SELECT count(*) FROM information_schema.columns WHERE table_name=''cavo'' and column_name=''gid_old'' and table_schema=''%s''', schemaname) INTO gid_old_esiste;
IF gid_old_esiste>0 THEN
	--creo tabella solo con vertici nuove linee eventualmente create:
	EXECUTE 'CREATE TABLE cavo_vertex AS SELECT (ST_DumpPoints(geom)).path as path, gid, (ST_DumpPoints(geom)).geom FROM cavo WHERE gid_old IS NULL';
ELSE
	--In una tabella copio tutti i vertici del layer cavo:
	EXECUTE 'CREATE TABLE cavo_vertex AS SELECT (ST_DumpPoints(geom)).path as path, gid, (ST_DumpPoints(geom)).geom FROM cavo';
END IF;

--creo il primo set corretto di segmenti escludendo quelli che poi andro ad unire:
EXECUTE 'CREATE TABLE cavo_finale AS
SELECT r.gid, e.geom
FROM edge e,
     relation rel,
     cavo r
WHERE e.edge_id = rel.element_id
  AND rel.topogeo_id = (r.topo_geom).id
  AND e.edge_id NOT IN (
    --lista degli edge_id da NON dividere:
    SELECT edge_id FROM edge e
    WHERE start_node IN (
    (SELECT node_id FROM node
    EXCEPT
    SELECT a.node_id FROM node a, cavo_vertex b WHERE a.geom=b.geom))
    OR end_node IN (
    (SELECT node_id FROM node
    EXCEPT
    SELECT a.node_id FROM node a, cavo_vertex b WHERE a.geom=b.geom))
  )
UNION
--questo invece e il set di edges uniti perche fan parte di quelle linee che si intersecano ma che non condividono alcun vertice tra loro:
SELECT gid, the_geom FROM (
SELECT ST_Union(e.geom) AS the_geom, topogeo_id  FROM (
SELECT
array_agg(edge_id) AS edge_id, topogeo_id
FROM
(
--lista degli edge_id da NON dividere:
SELECT * FROM edge e
WHERE start_node IN (
(SELECT node_id FROM node
EXCEPT
SELECT a.node_id FROM node a, cavo_vertex b WHERE a.geom=b.geom))
OR end_node IN (
(SELECT node_id FROM node
EXCEPT
SELECT a.node_id FROM node a, cavo_vertex b WHERE a.geom=b.geom))
) AS foo,
     relation rel,
     cavo r
WHERE foo.edge_id = rel.element_id AND rel.topogeo_id = (r.topo_geom).id
GROUP BY topogeo_id
) AS edge_coppie
LEFT JOIN
edge e ON e.edge_id = ANY(edge_coppie.edge_id)
GROUP BY topogeo_id
) AS union_edges,
cavo r
WHERE union_edges.topogeo_id = (r.topo_geom).id';

--ricreo una nuova tabella come cavo:
EXECUTE 'CREATE TABLE cavo_corretto ( LIKE cavo INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)';
EXECUTE format('ALTER TABLE cavo_corretto ALTER COLUMN geom type geometry(Linestring, %s)', epsg_srid);

EXECUTE format('SELECT constraint_name FROM information_schema.table_constraints WHERE table_name = ''cavo_corretto'' AND table_schema=''%s'' AND constraint_type=''PRIMARY KEY''', schemaname) INTO chiave_pk ;
IF chiave_pk IS NOT NULL THEN
	EXECUTE format('ALTER TABLE IF EXISTS cavo_corretto DROP CONSTRAINT IF EXISTS %s', chiave_pk);
END IF;
EXECUTE 'ALTER TABLE IF EXISTS cavo_corretto ALTER COLUMN gid DROP NOT NULL'; --tolgo questa CONSTRAINTS  altrimenti il campo gid rischia di essere integer e non seriale, come serve invece averlo per le query successive --ricreando il GID seriale forse non mi serve piu questo accrogimento!

BEGIN
	EXECUTE 'ALTER TABLE IF EXISTS cavo_corretto ADD COLUMN gid_old integer';
EXCEPTION
	WHEN duplicate_column THEN RAISE NOTICE 'column <gid_old> already exists in <cavo_corretto>.';
END;

--inserisco i nuovi elementi:
--EXECUTE 'INSERT INTO cavo_corretto(gid_old, geom) SELECT gid, ST_Multi(geom) FROM cavo_finale'; --perche' ST_Multi??
EXECUTE 'INSERT INTO cavo_corretto(gid_old, geom) SELECT gid, (ST_Dump(ST_LineMerge(geom))).geom FROM cavo_finale'; --se da problemi con Linestring ritorna a MultiLinestring


EXECUTE 'UPDATE cavo_corretto SET codice_inf = b.codice_inf
FROM cavo b WHERE b.gid=cavo_corretto.gid_old';
EXECUTE 'UPDATE cavo_corretto SET length_m = ST_Length(geom)';

EXECUTE format('CREATE TRIGGER update_ids_cavo_corretto
  BEFORE INSERT
  ON cavo_corretto
  FOR EACH ROW
  EXECUTE PROCEDURE %s.update_cavo(''%s'')', schemaname, schemaname);

--E infine rinomino la tabella di cavo ormai sporca:
SELECT EXTRACT(EPOCH FROM now())::integer INTO time_epoch;
EXECUTE format('ALTER TABLE cavo RENAME TO cavo_%s', time_epoch);
--Elimino gli indici sulla vecchia tabella cosi' non vanno in conflitto quando inizializzero' il nuovo cavo per il routing:
EXECUTE format('DROP INDEX IF EXISTS %s.cavo_source_idx', schemaname);
EXECUTE format('DROP INDEX IF EXISTS %s.cavo_geom_idx', schemaname);
EXECUTE format('DROP INDEX IF EXISTS %s.cavo_target_idx', schemaname);
EXECUTE format('ALTER TABLE IF EXISTS %s.cavo_sporco DROP CONSTRAINT IF EXISTS cavo_pkey', schemaname);

EXECUTE 'ALTER TABLE IF EXISTS cavo_corretto DROP COLUMN IF EXISTS gid';
EXECUTE 'ALTER TABLE IF EXISTS cavo_corretto ADD COLUMN gid serial';
EXECUTE 'ALTER TABLE cavo_corretto ADD PRIMARY KEY (gid)';
EXECUTE 'ALTER TABLE cavo_corretto RENAME TO cavo';

EXECUTE 'SET search_path = public, topology;';

RETURN true;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION split_lines_to_lines_conclusivo(text, integer)
  OWNER TO operatore;
COMMENT ON FUNCTION split_lines_to_lines_conclusivo(text, integer) IS 'pulizia di cavo spezzando le linee alla intersezione nodo-nodo con altre linee';
*/


/* CREAZIONE TABELLE */
--le creo nello script creazione_batch_schemi_e_tabelle.sql

COMMIT;