
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

UPDATE cavo
    SET n_mt_occ = CASE
    WHEN n_mt_occ='' THEN '0'
    WHEN n_mt_occ IS NULL THEN '0'
    END;

--nuove regole mail Gatti 14 novembre 2017:
UPDATE cavo SET cavi2 = CASE
    WHEN (tipo_posa ~* '.*interr.*') THEN f_12 + f_24 + f_48 + f_72 + f_96 + f_144
    ELSE f_24 + f_48 + f_72 + f_96 + f_144
END;

UPDATE cavo SET 
    tot_cavi1 = cavi_pr + cavi_bh,
    tot_cavi2 = cavi2,
    tot_cavicd = cavi_cd;

UPDATE cavo SET
    tot_cavi = tot_cavi1 + tot_cavi2 + tot_cavicd;

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
COMMENT ON FUNCTION public.s_calc_cable(text, integer) IS 'calcola scorte e tot_cavi su cavo';

