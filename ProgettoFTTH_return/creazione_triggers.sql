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
  UPDATE pfs SET n_pd=n_pd-1, n_ui=n_ui-old_ui WHERE id_pfs=OLD.id_pfs;
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
declare old_id text;
declare old_ui integer;
BEGIN
my_schema := TG_ARGV[0];
EXECUTE 'SET search_path = ' || quote_ident(my_schema) || ', pg_catalog;';
old_id := OLD.id_scala;
old_ui := coalesce(OLD.n_ui, 0);
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
  UPDATE pfs SET n_pd=n_pd-1, n_ui=n_ui-old_ui WHERE id_pfs=OLD.id_pfs;
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
--le creo a livello di DB nello script creazione_funzione_splitlines.sql


/* CREAZIONE TABELLE */
--le creo nello script creazione_batch_schemi_e_tabelle.sql

COMMIT;