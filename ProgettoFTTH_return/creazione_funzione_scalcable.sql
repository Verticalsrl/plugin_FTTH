
/* CALCOLA CAVO */

CREATE OR REPLACE FUNCTION public.s_calc_cable(
    schemaname text,
    epsgsrid integer)
  RETURNS boolean AS
$BODY$
  DECLARE layerid integer;
  schemaname text := $1;
  epsg_srid integer := $2;
BEGIN


-- domanda: perche' il campo n_mt_occ e' un varchar quando vanno. Deve essere INTEGER
-- se si applicano funzioni di calcolo. Per tradurre in linguaggio db le regole che mi sono
-- arrivate via file .ods ho convertito il capo in intero, cast(n_mt_occ as integer)
-- in modo da far funzionare i range numerici >.. <.. ecc

-- per la prima parte, ho creato una tabella di decodifica public.nuova_codifica
-- con cui eseguo la prima update

-- dove nel file e' stato messo 0 (zero) ho considerato NULL nel caso di stringa

-- il tipo_scavo non e' 'NO DIG' ma 'NODIG'

DROP TABLE IF EXISTS public.nuova_codifica;

CREATE TABLE public.nuova_codifica (
    codice_inf varchar(50) NULL,
    tipo_scavo varchar(50) NULL,
    tipo_minit varchar(50) NULL,
    mod_mtubo varchar(50) NULL,
    posa varchar(50) NULL,
    posa_dett varchar(50) NULL,
    flag_posa varchar(5) NULL
) ;

INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'37-001-RAMO_BT_-_CAVO_INTERRAT',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'37-001-RAMO_BT_-_CAVO_INTERRAT_PTA',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'37-004-RAMO_BT_-_CAVO_AEREO',NULL,NULL,NULL,'aereo','graffettato','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'CIVICO-NODO',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'CIVICO-PTA',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'ED INTERRATA DA VERIFICARE',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'ED INTERRATA DA VERIFICARE PTA',NULL,'singolo',NULL,'interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'FIBRA',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'FO APS',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'GHOST',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'ILLUMINAZIONE PUBBLICA',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'MINITRINCEA','minitrincea','fender','10/14','interrato','in tubo','si');
--INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES ('RACCORDO',NULL,'singolo','10/12','interrato','in tubo','si');
--modificato RACCORDO da mail Gatti 31 ottobre 2017
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES ('RACCORDO',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'RAMO_BT_-_PALO_AEREO',NULL,NULL,NULL,'aereo','tesato','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'TRINCEA NORMALE','scavo tradizionale','fender','10/14','interrato','in tubo','si');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'TRINCEA NORMALE_PTA',NULL,'fender','10/14','interrato','in tubo','si');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'VENIS',NULL,'singolo','10/12','interrato','in tubo','no');
--INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES ('WIND',NULL,NULL,'10/12','interrato','in tubo','no');
--modificato WIND da mail Gatti 31 ottobre 2017
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'WIND',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
NULL,NULL,NULL,NULL,NULL,'in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'ILLUMINAZIONE PUBBLICA AEREA NUDA',NULL,NULL,NULL,'aereo','tesato','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'TRINCEA NORMALE_ATT','scavo tradizionale','fender','10/14','interrato','in tubo','si');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'NODIG','No-dig','fender','10/14','interrato','in tubo','si');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'RETELIT',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'FO COM',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'TIM',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'BT ENIA',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'LEPIDA',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'ACANTO',NULL,'singolo','10/12','interrato','in tubo','no');


EXECUTE 'SET search_path = ' || quote_ident(schemaname) || ', public, pg_catalog;';


UPDATE cavo
SET tipo_scavo = a.tipo_scavo,
tipo_minit = a.tipo_minit,
mod_mtubo = a.mod_mtubo,
tipo_posa = a.posa,
posa_dett = a.posa_dett,
flag_posa = a.flag_posa
FROM public.nuova_codifica a
WHERE a.codice_inf = cavo.codice_inf;

update cavo
set n_mt_occ = '0'
where n_mt_occ='';

update cavo
set n_mt_occ = '0'
where n_mt_occ IS NULL;


--nuove regole mail Gatti 14 novembre 2017:
UPDATE cavo SET 
    n_mt_occ_1 = CASE
    WHEN cavi_pr+cavi_bh = 14 THEN cavi_pr+cavi_bh +4
    WHEN cavi_pr+cavi_bh > 8 THEN cavi_pr+cavi_bh +3
    WHEN cavi_pr+cavi_bh > 4 THEN cavi_pr+cavi_bh +2
    WHEN cavi_pr+cavi_bh >0 THEN cavi_pr+cavi_bh +1
    ELSE 0
    END,
    n_mt_occ_2 = CASE
    WHEN cavi2=0 THEN 0
    ELSE cavi2 + 2
    END,
    n_mt_occ_cd = CASE
    WHEN cavi_cd = 14 THEN cavi_cd +4
    WHEN cavi_cd > 8 THEN cavi_cd +3
    WHEN cavi_cd > 4 THEN cavi_cd +2
    WHEN cavi_cd > 0 THEN cavi_cd +1
    ELSE 0
    END
WHERE flag_posa ~* '.*si.*';

UPDATE cavo SET 
    n_mt_occ = n_mt_occ_1::int + n_mt_occ_2::int + n_mt_occ_cd::int,
    n_mtubo = ceil((n_mt_occ_1::int + n_mt_occ_2::int + n_mt_occ_cd::int)::double precision / 7) || 'x7'
WHERE flag_posa ~* '.*si.*';

UPDATE cavo SET
    n_mt_occ = CASE
    WHEN tot_cavi=0 THEN 0
    ELSE tot_cavi+2
    END,
    n_mtubo = NULL,
    n_mt_occ_1 = NULL,
    n_mt_occ_2 = NULL,
    n_mt_occ_cd = NULL
WHERE flag_posa ~* '.*no.*';
--fine nuove regole mai Gatti 14 novembre 2017


UPDATE cavo
SET n_mtubo = NULL
WHERE tipo_posa = 'aereo' AND flag_posa = 'no';

UPDATE cavo
SET n_mtubo = NULL
WHERE tipo_posa IS NULL AND flag_posa IS NULL;


/*da mail di gatti del 31 ottobre 2017. cambiano le regole!
UPDATE cavo 
SET n_mt_occ = tot_cavi
WHERE tipo_posa = 'interrato' AND codice_ins IN ('PR','BH','PR+BH') AND tot_cavi = 0;

UPDATE cavo 
SET n_mt_occ = tot_cavi + 1
WHERE tipo_posa = 'interrato' AND codice_ins IN ('PR','BH','PR+BH') AND tot_cavi = 1;

UPDATE cavo 
SET n_mt_occ = tot_cavi + 3
WHERE tipo_posa = 'interrato' AND codice_ins IN ('PR','BH','PR+BH') AND tot_cavi > 1;


UPDATE cavo 
SET n_mt_occ = tot_cavi
WHERE tipo_posa = 'interrato' AND codice_ins IS NULL AND tot_cavi = 0;

UPDATE cavo 
SET n_mt_occ = tot_cavi + 2
WHERE tipo_posa = 'interrato' AND codice_ins IS NULL AND tot_cavi > 0;

UPDATE cavo
SET n_mt_occ = tot_cavi
WHERE tipo_posa = 'aereo' AND flag_posa = 'no' AND tot_cavi >= 0;

UPDATE cavo
SET n_mt_occ = 0
WHERE tipo_posa IS NULL AND flag_posa IS NULL AND tot_cavi >= 0;

UPDATE cavo
SET n_mtubo = '1x7'
WHERE codice_inf IN ('MINITRINCEA', 'TRINCEA NORMALE', 'NODIG') AND CAST(n_mt_occ as integer) between 1 and 7;

UPDATE cavo
SET n_mtubo = '2x7'
WHERE codice_inf IN ('MINITRINCEA', 'TRINCEA NORMALE', 'NODIG') AND CAST(n_mt_occ as integer) between 8 and 14;

UPDATE cavo
SET n_mtubo = '3x7'
WHERE codice_inf IN ('MINITRINCEA', 'TRINCEA NORMALE', 'NODIG') AND CAST(n_mt_occ as integer) between 15 and 21;

UPDATE cavo
SET n_mtubo = '4x7'
WHERE codice_inf IN ('MINITRINCEA', 'TRINCEA NORMALE', 'NODIG') AND CAST(n_mt_occ as integer) between 22 and 28;

UPDATE cavo
SET n_mtubo = '5x7'
WHERE codice_inf IN ('MINITRINCEA', 'TRINCEA NORMALE', 'NODIG') AND CAST(n_mt_occ as integer) between 29 and 35;

UPDATE cavo
SET n_mtubo = '6x7'
WHERE codice_inf IN ('MINITRINCEA', 'TRINCEA NORMALE', 'NODIG') AND CAST(n_mt_occ as integer) between 36 and 42;

UPDATE cavo
SET n_mtubo = '7x7'
WHERE codice_inf IN ('MINITRINCEA', 'TRINCEA NORMALE', 'NODIG') AND CAST(n_mt_occ as integer) between 43 and 49;

UPDATE cavo
SET n_mtubo = '8x7'
WHERE codice_inf IN ('MINITRINCEA', 'TRINCEA NORMALE', 'NODIG') AND CAST(n_mt_occ as integer) between 50 and 56;

UPDATE cavo
SET n_mtubo = '9x7'
WHERE codice_inf IN ('MINITRINCEA', 'TRINCEA NORMALE', 'NODIG') AND CAST(n_mt_occ as integer) between 57 and 63;

UPDATE cavo
SET n_mtubo = '10x7'
WHERE codice_inf IN ('MINITRINCEA', 'TRINCEA NORMALE', 'NODIG') AND CAST(n_mt_occ as integer) between 64 and 70;
*/

/* da mail di gatti del 31 ottobre 2017: nuove regole:*/
--le calcolo su db_cavoroute.py


UPDATE cavo
SET n_tubi = 3
WHERE codice_inf = 'TRINCEA NORMALE_ATT';

UPDATE cavo
SET d_tubi = 50
WHERE codice_inf = 'TRINCEA NORMALE_ATT';

RAISE NOTICE 'calcolo sui campi di cavo ultimato';

RETURN true;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION public.s_calc_cable(text, integer) OWNER TO operatore;
COMMENT ON FUNCTION public.s_calc_cable(text, integer) IS 'calcola cavo';

