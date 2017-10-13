-- Table: variabili_progetto_return

--CREATE TABLE spatial_ref_sys AS SELECT * FROM public.spatial_ref_sys;
DROP TABLE IF EXISTS variabili_progetto_return;
CREATE TABLE variabili_progetto_return
(
  gid serial primary key,
  pta_ui_min integer NOT NULL DEFAULT 0,
  pta_ui_max integer NOT NULL DEFAULT 44,
  pta_cont_max integer NOT NULL DEFAULT 44,
  giunto_ui_min integer NOT NULL DEFAULT 0,
  giunto_ui_max integer NOT NULL DEFAULT 96,
  giunto_cont_max integer NOT NULL DEFAULT 8,
  pd_ui_min integer NOT NULL DEFAULT 16,
  pd_ui_max integer NOT NULL DEFAULT 96,
  pd_cont_max integer NOT NULL DEFAULT 8,
  pfs_ui_min integer NOT NULL DEFAULT 220,
  pfs_ui_max integer NOT NULL DEFAULT 254,
  pfs_pd_max integer NOT NULL DEFAULT 12,
  pfp_ui_min integer NOT NULL DEFAULT 850,
  pfp_ui_max integer NOT NULL DEFAULT 1024,
  pfp_pfs_max integer NOT NULL DEFAULT 4,
  
  scala_pta_f4 integer NOT NULL DEFAULT 0,
  scala_pta_f12 integer NOT NULL DEFAULT 3,
  scala_pta_f24 integer NOT NULL DEFAULT 0,
  scala_pta_f48 integer NOT NULL DEFAULT 0,
  scala_pta_f72 integer NOT NULL DEFAULT 0,
  scala_pta_f96 integer NOT NULL DEFAULT 0,
  scala_pta_f144 integer NOT NULL DEFAULT 0,
  scala_pta_f192 integer NOT NULL DEFAULT 0,
  
  scala_giunto_f4 integer NOT NULL DEFAULT 0,
  scala_giunto_f12 integer NOT NULL DEFAULT 0,
  scala_giunto_f24 integer NOT NULL DEFAULT 10,
  scala_giunto_f48 integer NOT NULL DEFAULT 34,
  scala_giunto_f72 integer NOT NULL DEFAULT 0,
  scala_giunto_f96 integer NOT NULL DEFAULT 42,
  scala_giunto_f144 integer NOT NULL DEFAULT 0,
  scala_giunto_f192 integer NOT NULL DEFAULT 0,
  
  scala_pd_f4 integer NOT NULL DEFAULT 0,
  scala_pd_f12 integer NOT NULL DEFAULT 0,
  scala_pd_f24 integer NOT NULL DEFAULT 10,
  scala_pd_f48 integer NOT NULL DEFAULT 34,
  scala_pd_f72 integer NOT NULL DEFAULT 0,
  scala_pd_f96 integer NOT NULL DEFAULT 42,
  scala_pd_f144 integer NOT NULL DEFAULT 0,
  scala_pd_f192 integer NOT NULL DEFAULT 0,
  
  scala_pfs_f4 integer NOT NULL DEFAULT 0, -- da definire
  scala_pfs_f12 integer NOT NULL DEFAULT 0, -- da definire
  scala_pfs_f24 integer NOT NULL DEFAULT 10, -- da definire
  scala_pfs_f48 integer NOT NULL DEFAULT 34, -- da definire
  scala_pfs_f72 integer NOT NULL DEFAULT 0, -- da definire
  scala_pfs_f96 integer NOT NULL DEFAULT 42, --da definire
  scala_pfs_f144 integer NOT NULL DEFAULT 0, -- da definire
  scala_pfs_f192 integer NOT NULL DEFAULT 0, -- da definire
  
  giunto_pd_f4 integer NOT NULL DEFAULT 0,
  giunto_pd_f12 integer NOT NULL DEFAULT 0,
  giunto_pd_f24 integer NOT NULL DEFAULT 10,
  giunto_pd_f48 integer NOT NULL DEFAULT 34,
  giunto_pd_f72 integer NOT NULL DEFAULT 0,
  giunto_pd_f96 integer NOT NULL DEFAULT 42,
  giunto_pd_f144 integer NOT NULL DEFAULT 0,
  giunto_pd_f192 integer NOT NULL DEFAULT 0,
  
  pta_pd_f4 integer NOT NULL DEFAULT 0,
  pta_pd_f12 integer NOT NULL DEFAULT 0,
  pta_pd_f24 integer NOT NULL DEFAULT 10,
  pta_pd_f48 integer NOT NULL DEFAULT 34,
  pta_pd_f72 integer NOT NULL DEFAULT 0,
  pta_pd_f96 integer NOT NULL DEFAULT 42,
  pta_pd_f144 integer NOT NULL DEFAULT 0,
  pta_pd_f192 integer NOT NULL DEFAULT 0,
  
  pd_pfs_f4 integer NOT NULL DEFAULT 0,
  pd_pfs_f12 integer NOT NULL DEFAULT 0,
  pd_pfs_f24 integer NOT NULL DEFAULT 16,
  pd_pfs_f48 integer NOT NULL DEFAULT 32,
  pd_pfs_f72 integer NOT NULL DEFAULT 0,
  pd_pfs_f96 integer NOT NULL DEFAULT 64,
  pd_pfs_f144 integer NOT NULL DEFAULT 96,
  pd_pfs_f192 integer NOT NULL DEFAULT 0,
  
  pfs_pfp_f96 integer NOT NULL DEFAULT 9999,
  
  routing_scale_vertici smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  routing_pta_vertici smallint NOT NULL DEFAULT 0,
  routing_giunti_vertici smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  routing_pd_vertici smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  routing_pfs_vertici smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  routing_pfp_vertici smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  routing_scale_fibre smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  routing_pta_fibre smallint NOT NULL DEFAULT 0,
  routing_giunti_fibre smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  routing_pd_fibre smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  routing_pfs_fibre smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  routing_pfp_fibre smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  routing_start smallint NOT NULL DEFAULT 0, -- 0-non eseguito o fallito; 1-eseguito
  
  id_pop integer,
  cod_belf character varying(4),
  lotto character varying(5),
  srid integer
);
ALTER TABLE variabili_progetto_return OWNER TO operatore;
GRANT ALL ON TABLE variabili_progetto_return TO operatore;
GRANT ALL ON TABLE variabili_progetto_return TO postgres;
COMMENT ON COLUMN variabili_progetto_return.pta_cont_max IS 'ATTENZIONE da definire';
COMMENT ON COLUMN variabili_progetto_return.routing_pta_vertici IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_pta_fibre IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_scale_vertici IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_giunti_vertici IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_pd_vertici IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_pfs_vertici IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_pfp_vertici IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_scale_fibre IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_giunti_fibre IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_pd_fibre IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_pfs_fibre IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_pfp_fibre IS '0-non eseguito o fallito; 1-eseguito';
COMMENT ON COLUMN variabili_progetto_return.routing_start IS '0-non eseguito o fallito; 1-eseguito';
--INSERT INTO variabili_progetto_return (gid) VALUES (1);
