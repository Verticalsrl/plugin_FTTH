
/* TABELLA CODIFICA CAMPO CODICE_INF per CAVO */

CREATE OR REPLACE FUNCTION public.s_codifica_cable(
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
'CANALETTA',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'MINITRINCEA','minitrincea','fender','10/14','interrato','in tubo','si');
--INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES ('RACCORDO',NULL,'singolo','10/12','interrato','in tubo','si');
--modificato RACCORDO da mail Gatti 31 ottobre 2017
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'RACCORDO',NULL,NULL,NULL,NULL,NULL,NULL);
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
'ADDUZIONE_SCAVO','scavo tradizionale','singolo','10/14','interrato','in tubo','si');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'ADDUZIONE_TRINCEA','scavo tradizionale','singolo','10/14','interrato','in tubo','si');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'ADDUZIONE_MINITRINCEA','scavo tradizionale','singolo','10/14','interrato','in tubo','si');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'NODIG','No-dig','bandle','10/14','interrato','in tubo','si');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'NO_DIG','No-dig','bandle','10/14','interrato','in tubo','si');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'NO DIG','No-dig','bandle','10/14','interrato','in tubo','si');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'RETELIT',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'FO COM',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'FO_COM',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'TIM',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'BT ENIA',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'LEPIDA',NULL,'singolo','10/12','interrato','in tubo','no');
INSERT INTO public.nuova_codifica (codice_inf,tipo_scavo,tipo_minit,mod_mtubo,posa,posa_dett,flag_posa) VALUES (
'ACANTO',NULL,'singolo','10/12','interrato','in tubo','no');


RAISE NOTICE 'creazione tabella codifica campo codice_inf per cavo ultimato';

RETURN true;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION public.s_codifica_cable(text, integer) OWNER TO operatore;
COMMENT ON FUNCTION public.s_codifica_cable(text, integer) IS 'crea tabella di decodifica campo codice_inf per cavo';

