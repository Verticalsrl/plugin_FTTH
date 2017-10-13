/*
Codice presumibilmente da lanciare via script python da plugin QGis

Parametri in ingresso tramite maschera da plugin:
- codice comune
- codice lotto
- numero fibre min/max
- UI in pd min/max
- UI in pfs min/max
- UI in pfp min/max

*/
--CREATE SCHEMA %lotto_109% AUTHORIZATION postgres;
--SET search_path = %lotto_109%, pg_catalog;

/*Inutile crearla se poi la si reimporta dallo shape. Ma la creo lo stesso per creare il progeto QGis all'inizializzazione di un nuovo schema da parte dell'utente*/
/*CREATE TABLE IF NOT EXISTS scala
(
  gid serial NOT NULL,
  id_scala character varying(160),
  regione character varying(30),
  provincia character varying(30),
  comune character varying(60),
  frazione character varying(20),
  id_pop character varying(254),
  id_pfp character varying(20),
  id_pfs character varying(20),
  id_pd character varying(20),
  id_giunto character varying(254),
  particella character varying(28),
  indirizzo character varying(70),
  cicivo character varying(10),
  scala_pala character varying(10),
  codice_via character varying(10),
  id_buildin character varying(150),
  coordinate character varying(40),
  coordina_1 character varying(40),
  pop character varying(10),
  n_ui smallint,
  stato_buil smallint,
  stato_scal smallint,
  data_rfc_i character varying(10),
  data_rfc_e character varying(10),
  data_rfa_i character varying(10),
  data_rfa_e character varying(10),
  data_ultim character varying(10),
  data_ult_1 character varying(10),
  data_ult_2 character varying(10),
  cod_belf character varying(4),
  lotto character varying(5),
  note_ character varying(254),
  geom public.geometry(Point,3004),
  CONSTRAINT scala_pkey PRIMARY KEY (gid)
);
CREATE INDEX scala_geom_idx ON scala USING gist (geom);
*/

--svuoto lo schema nel caso sia gia' pieno di queste tabelle, ma ho gia' avvertito l'utente ed ha accettato:
DROP TABLE IF EXISTS cavo;
DROP TABLE IF EXISTS sottotratta;
DROP TABLE IF EXISTS area_pfp;
DROP TABLE IF EXISTS area_pfs;
DROP TABLE IF EXISTS cavoroute;
DROP TABLE IF EXISTS giunti;
DROP TABLE IF EXISTS pd;
DROP TABLE IF EXISTS pfp;
DROP TABLE IF EXISTS pfs;
DROP TABLE IF EXISTS pop;
DROP TABLE IF EXISTS pozzetto;


/* VECCHIA DEFINIZIONE
CREATE TABLE IF NOT EXISTS cavo
(
  gid serial NOT NULL,
  id_cavo character varying(50),  
  id_sottotratta character varying(30),
  id_pop character varying(50),
  f_4 integer,
  f_12 integer,
  f_24 integer,
  f_48 integer,
  f_72 integer,
  f_96 smallint,
  f_144 smallint,  
  tot_cavi integer,
  tot_fibre integer,
  layer character varying(250),
  length_m double precision,
  tipo_cavo character varying(50),
  specifica_ character varying(50),
  costruttor character varying(50),
  modello_ca character varying(50),
  n_fo_per_c character varying(50),
  id_pop_end character varying(50),
  id_armadio character varying(50),
  id_muffola character varying(50),
  id_ce_endp character varying(50),
  id_armad_1 character varying(50),
  id_muffo_1 character varying(50),
  id_ce_en_1 character varying(50),
  id_ont_end character varying(50),
  matricola character varying(50),
  produttore character varying(50),
  seriale character varying(50),
  cod_belf character varying(4),
  lotto character varying(5),
  cod_geom integer,
  geom public.geometry(MultiLineString,3004),
  tipo_posa character varying(50),
  --source integer,
  --target integer,
  --length_m double precision,
  --n_ui integer DEFAULT 0,
  CONSTRAINT cavo_pkey PRIMARY KEY (gid)
);
*/
/*NUOVA DEFINIZIONE*/
CREATE TABLE IF NOT EXISTS cavo
(
  gid serial NOT NULL,
  geom public.geometry(MultiLineString,3004),
  objectid integer,
  id_stratt character varying(30),
  tipo_scavo character varying(50),
  tipo_pav character varying(25),
  n_tubi character varying(25),
  d_tubi character varying(25),
  libero character varying(25),
  n_mtubo character varying(50),
  n_mt_occ character varying(50),
  tipo_minit character varying(50),
  costr_mt character varying(50),
  mod_mtubo character varying(50),
  tipo_posa character varying(50),
  posa_dett character varying(50),
  flag_posa character varying(50),
  codice_inf character varying(50),
  id_cavo character varying(50),
  f_4 integer,
  f_12 integer,
  f_24 integer,
  f_48 integer,
  f_72 integer,
  f_96 integer,
  f_144 integer,
  f_192 integer,
  tipo_cavo character varying(50),
  specifica_ character varying(50),
  costrutt_1 character varying(50),
  modello_ca character varying(50),
  cod_belf character varying(4),
  lotto character varying(50),
  cod_geom integer,
  id_pop_end character varying(50),
  lunghezza1 character varying(50),
  lunghezz_1 character varying(50),
  matricola character varying(50),
  produttore character varying(50),
  seriale character varying(50),
  tot_fibre integer,
  tot_cavi integer,
  id_pfp character varying(50),
  codice_ins character varying(50),
  shape_leng double precision,
  length_m double precision,
  --source integer,
  --target integer,
  --n_ui integer DEFAULT 0,
  CONSTRAINT cavo_pkey PRIMARY KEY (gid)
);
CREATE INDEX cavo_geom_idx ON cavo USING gist (geom);

CREATE TABLE IF NOT EXISTS sottotratta
(
  gid serial NOT NULL,
  id_sottotr character varying(30),
  id_sotto_1 character varying(30),
  shape_leng numeric,
  id_pozzett character varying(50),
  id_armadio character varying(50),
  id_facciat character varying(50),
  id_sostegn character varying(50),
  id_ce_endp character varying(50),
  id_pozze_1 character varying(50),
  id_armad_1 character varying(50),
  id_facci_1 character varying(50),
  id_soste_1 character varying(50),
  id_ce_en_1 character varying(50),
  id_ont_end character varying(50),
  lunghezza_ character varying(50),
  tipo_scavo character varying(50),
  num_minitu character varying(50),
  num_mini_1 character varying(50),
  tipo_minit character varying(50),
  costruttor character varying(50),
  modello_mi character varying(50),
  tipo_posa character varying(50),
  tipo_posa_ character varying(50),
  infrastrut character varying(50),
  codice_ins character varying(50),
  layer character varying(250),
  geom public.geometry(MultiLineString,3004),
  CONSTRAINT sottotratta_pkey PRIMARY KEY (gid)
);
CREATE INDEX sottotratta_geom_idx ON sottotratta USING gist (geom);


CREATE TABLE IF NOT EXISTS area_pfp
(
  gid serial NOT NULL,
  regione character varying(30),
  provincia character varying(30),
  comune character varying(60),
  id_areapfp character varying(20),
  id_areapop character varying(20),
  n_pfp integer,
  n_pfs integer,
  n_pd integer,
  n_giunti integer,
  n_ui integer,
  shape_leng numeric,
  shape_area numeric,
  geom public.geometry(MultiPolygon,3004),
  CONSTRAINT area_pfp_pkey PRIMARY KEY (gid)
);
CREATE INDEX area_pfp_geom_idx ON area_pfp USING gist (geom);

CREATE TABLE IF NOT EXISTS area_pfs
(
  gid serial NOT NULL,
  regione character varying(30),
  provincia character varying(30),
  comune character varying(60),
  id_areapfs character varying(20),
  id_areapop character varying(20),
  id_areapfp character varying(50),
  shape_leng numeric,
  shape_area numeric,
  n_pfs integer,
  n_pd integer,
  n_giunti integer,
  n_ui integer,
  note_ character varying(254),
  geom public.geometry(MultiPolygon,3004),
  CONSTRAINT area_pfs_pkey PRIMARY KEY (gid)
);
CREATE INDEX area_pfs_geom_idx ON area_pfs USING gist (geom);


CREATE TABLE IF NOT EXISTS pozzetto
(
  gid serial NOT NULL,
  geom public.geometry(Point,3004),
  id_pozzetto character varying(13),
  pos_poz_n double precision,
  pos_poz_e double precision,
  cod_belf character varying(4),
  cod_geom integer,
  id_pop character varying(50),
  id_pfp character varying(50),
  id_pfs character varying(50),
  id_pd character varying(50),
  cod_tipo character varying(50),
  matricola character varying(50),
  produttore character varying(50),
  seriale character varying(50),
  insert_type character varying(16) DEFAULT 'manual'::character varying,
  lotto character varying(5),
  CONSTRAINT pozzetto_pkey PRIMARY KEY (gid),
  UNIQUE (id_pozzetto)
);
CREATE INDEX pozzetto_geom_idx ON pozzetto USING gist (geom);


CREATE TABLE IF NOT EXISTS cavoroute
(
  gid serial NOT NULL,
  id_cavo character varying(64),
  fibre_coun integer,
  n_ui integer,
  from_p character varying(64),
  to_p character varying(64),
  net_type character varying(255),
  num_scorte smallint,
  length_m double precision,
  source integer,
  target integer,
  geom public.geometry(MultiLineString,3004),
  n_gnz_un smallint,
  n_gnz_tot integer,
  n_gnz_min8 smallint,
  n_gnz_mag8 smallint,
  n_gnz_min12 smallint,
  n_gnz_mag12 smallint,
  teste_cavo smallint,
  scorta smallint,
  CONSTRAINT cavoroute_pkey PRIMARY KEY (gid)
);
CREATE INDEX cavoroute_geom_idx ON cavoroute USING gist (geom);


CREATE TABLE IF NOT EXISTS giunti
(
  gid serial NOT NULL,
  id_giunto character varying(50),
  coord_n double precision,
  coord_e double precision,
  id_pop character varying(50),
  id_pfp character varying(50),
  id_pfs character varying(50),
  id_pd character varying(50),
  n_cont integer,
  n_ui integer,
  cartolina character varying(50),
  id_armadio character varying(50),
  id_muffola character varying(50),
  id_fo_1 character varying(50),
  id_fo_2 character varying(50),
  owner character varying(50),
  cod_belf character varying(4),
  lotto character varying(5),
  id_g_num integer,
  id_g_ref character varying(50),
  tipo_giunt character varying(10),
  tipo_posa character varying(10),
  cod_cft character varying(5),
  geom public.geometry(Point,3004),
  CONSTRAINT giunti_pkey PRIMARY KEY (gid),
  UNIQUE (cod_belf, lotto, id_g_num),
  UNIQUE (id_giunto)
);
CREATE INDEX giunti_geom_idx ON giunti USING gist (geom);


CREATE TABLE IF NOT EXISTS pd
(
  gid serial NOT NULL,
  id_pd character varying(13),
  coord_n double precision,
  coord_e double precision,
  id_pop character varying(20),
  id_pfp character varying(20),
  id_pfs character varying(20),
  n_giunti integer,
  n_cont integer,
  n_ui integer,
  id_muffola character varying(50),
  id_armadio character varying(50),
  id_pozzett character varying(50),
  cod_belf character varying(4),
  lotto character varying(5),
  id_pd_num integer,
  id_pd_ref character varying(50),
  tipo_posa character varying(10),
  cod_cft character varying(5),
  geom public.geometry(Point,3004),
  CONSTRAINT pd_pkey PRIMARY KEY (gid),
  UNIQUE (cod_belf, lotto, id_pd_num),
  UNIQUE (id_pd)
);
CREATE INDEX pd_geom_idx ON pd USING gist (geom);


CREATE TABLE IF NOT EXISTS pfs
(
  gid serial NOT NULL,
  id_pfs character varying(13),
  coord_n double precision,
  coord_e double precision,
  id_pop character varying(20),
  id_pfp character varying(20),
  n_pd integer,
  n_ui integer,
  id_muffola character varying(50),
  id_armadio character varying(50),
  codice_cab character varying(50),
  flag_inter character varying(50),
  cod_belf character varying(4),
  lotto character varying(5),
  id_pfs_num integer,
  tipo_posa character varying(10),
  cod_cft character varying(5),
  geom public.geometry(Point,3004),
  CONSTRAINT pfs_pkey PRIMARY KEY (gid),
  UNIQUE (cod_belf, lotto, id_pfs_num),
  UNIQUE (id_pfs)
);
CREATE INDEX pfs_geom_idx ON pfs USING gist (geom);


CREATE TABLE IF NOT EXISTS pfp
(
  gid serial NOT NULL,
  id_pfp character varying(13),
  coord_n double precision,
  coord_e double precision,
  id_pop character varying(20),
  n_pfs integer,
  n_ui integer,
  id_muffola character varying(50),
  id_armadio character varying(50),
  id_pozzett character varying(50),
  cod_belf character varying(4),
  lotto character varying(5),
  id_pfp_num integer,
  tipo_posa character varying(10),
  cod_cft character varying(5),
  geom public.geometry(Point,3004),
  CONSTRAINT pfp_pkey PRIMARY KEY (gid),
  UNIQUE (id_pfp)
);
CREATE INDEX pfp_geom_idx ON pfp USING gist (geom);


CREATE TABLE IF NOT EXISTS pop
(
  gid serial NOT NULL,
  id_pop character varying(10),
  coord_n double precision,
  coord_e double precision,
  area_pop character varying(50),
  cabina_pri character varying(50),
  nome character varying(50),
  n_ce integer,
  cod_belf character varying(4),
  lotto character varying(5),
  id_pop_num integer,
  tipo_posa character varying(10),
  cod_cft character varying(5),
  geom public.geometry(Point,3004),
  CONSTRAINT pop_pkey PRIMARY KEY (gid)
);
CREATE INDEX pop_geom_idx ON pop USING gist (geom);


--GRANT TO USER operatore
--GRANT ALL ON TABLE cavo TO operatore;
--GRANT ALL ON TABLE giunti TO operatore;
--GRANT ALL ON TABLE pd TO operatore;
--GRANT ALL ON TABLE pfp TO operatore;
--GRANT ALL ON TABLE pfs TO operatore;
--GRANT ALL ON TABLE pop TO operatore;
--GRANT ALL ON TABLE scala TO operatore;
--GRANT ALL ON TABLE sottotratta TO operatore;