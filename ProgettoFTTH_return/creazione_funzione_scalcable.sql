
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


EXECUTE 'SET search_path = ' || quote_ident(schemaname) || ', public, pg_catalog;';

/* la porto dentro il routing di db_cavoroute:
UPDATE cavo
SET tipo_scavo = a.tipo_scavo,
tipo_minit = a.tipo_minit,
mod_mtubo = a.mod_mtubo,
tipo_posa = a.posa,
posa_dett = a.posa_dett,
flag_posa = a.flag_posa
FROM public.nuova_codifica a
WHERE a.codice_inf = cavo.codice_inf;
*/

UPDATE cavo SET
    n_mt_occ = '0',
    n_mt_occ_1 = '0',
    n_mt_occ_2 = '0',
    n_mt_occ_cd = '0',
    n_mtubo = '0';
    
UPDATE cavo
    SET cavi_pr = 0 WHERE cavi_pr IS NULL;
    
UPDATE cavo
    SET cavi_bh = 0 WHERE cavi_bh IS NULL;
    
UPDATE cavo
    SET cavi_cd = 0 WHERE cavi_cd IS NULL;

UPDATE cavo
    SET cavi2 = 0;

--nuove regole mail Gatti 14 novembre 2017:
UPDATE cavo SET cavi2 = CASE
    WHEN (tipo_posa ~* '.*interr.*') THEN f_12 + f_24 + f_48 + f_72 + f_96 + f_144
    ELSE f_24 + f_48 + f_72 + f_96 + f_144
END;

UPDATE cavo SET 
    tot_cavi1 = COALESCE(cavi_pr, 0) + COALESCE(cavi_bh, 0),
    tot_cavi2 = COALESCE(cavi2, 0),
    tot_cavicd = COALESCE(cavi_cd, 0);

UPDATE cavo SET
    tot_cavi = COALESCE(tot_cavi1, 0) + COALESCE(tot_cavi2, 0) + COALESCE(tot_cavicd, 0);

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
    WHEN cavi_cd=0 THEN 0
    ELSE cavi_cd + 3
    END
WHERE flag_posa ~* '.*si.*' AND tipo_posa ~* '.*interr.*';

UPDATE cavo SET 
    n_mt_occ = COALESCE(n_mt_occ_1::int + n_mt_occ_2::int + n_mt_occ_cd::int, '0')::text,
    --n_mtubo = ceil(( COALESCE(n_mt_occ_1::int + n_mt_occ_2::int + n_mt_occ_cd::int, '0') )::double precision / 7) || 'x7'
	n_mtubo = (
	ceil(( COALESCE(n_mt_occ_1::int, '0') )::double precision / 7) +
	ceil(( COALESCE(n_mt_occ_2::int, '0') )::double precision / 7) +
	ceil(( COALESCE(n_mt_occ_cd::int, '0') )::double precision / 7)
	)::integer || 'x7'
WHERE flag_posa ~* '.*si.*' AND tipo_posa ~* '.*interr.*';

UPDATE cavo SET
    n_mt_occ = CASE
    WHEN tot_cavi=0 THEN '0'
    ELSE (tot_cavi+2)::text
    END,
    n_mtubo = '0',
    n_mt_occ_1 = '0',
    n_mt_occ_2 = '0',
    n_mt_occ_cd = '0'
WHERE flag_posa ~* '.*no.*' AND tipo_posa ~* '.*interr.*';

UPDATE cavo SET
    n_mt_occ = CASE
    WHEN tot_cavi=0 THEN '0'
    ELSE tot_cavi::text
    END
WHERE tipo_posa ~* '.*aereo.*';
--fine nuove regole mai Gatti 14 novembre 2017


UPDATE cavo
SET n_mtubo = NULL
WHERE tipo_posa = 'aereo' AND flag_posa = 'no';

UPDATE cavo
SET n_mtubo = NULL
WHERE tipo_posa IS NULL AND flag_posa IS NULL;

UPDATE cavo SET
	n_tubi = 1,
	n_mtubo = '0',
	n_mt_occ = CASE
	WHEN tot_cavi=0 THEN '0'
    ELSE (tot_cavi+1)::text
    END
WHERE upper(codice_inf) = 'ADDUZIONE_SCAVO';

UPDATE cavo SET
	n_tubi = 3,
	d_tubi = 50
WHERE upper(codice_inf) = 'TRINCEA NORMALE_ATT';


RAISE NOTICE 'calcolo sui campi di cavo ultimato';

RETURN true;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION public.s_calc_cable(text, integer) OWNER TO operatore;
COMMENT ON FUNCTION public.s_calc_cable(text, integer) IS 'calcola scorte e tot_cavi su cavo';

