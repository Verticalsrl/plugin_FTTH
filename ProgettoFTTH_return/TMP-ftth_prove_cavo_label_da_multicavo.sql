/* Prove per FTTH da cavo con tante linee sovrapposte, crearne UNA, poi spezzarla ai vertici ed assegnare ad ogni segmento le proprietà, concatenate, delle linee originarie, per simulare cavoroute_label */

SELECT topology.CreateTopology('sheath_with_loc_topo', 3003);
SELECT topology.AddTopoGeometryColumn('sheath_with_loc_topo', 'pc_ac05w', 'sheath_with_loc', 'topo_geom', 'LINESTRING');

GRANT ALL ON SCHEMA sheath_with_loc_topo TO operatore;
GRANT ALL ON SCHEMA sheath_with_loc_topo TO postgres;
GRANT USAGE ON SCHEMA sheath_with_loc_topo TO public;

--recupero il layer id creato con topology:
SELECT layer_id FROM topology.layer WHERE schema_name='pc_ac05w' AND table_name= 'sheath_with_loc';

UPDATE pc_ac05w.sheath_with_loc SET topo_geom = topology.toTopoGeom(geom, 'sheath_with_loc_topo', 1);
--SENZA TOLLERANZA! Con la tolleranza potrebbe trovare alcuni errori, meglio NIENTE


--carico su QGis le tabelle:
--sheath_with_loc_topo.edge_data
--sheath_with_loc_topo.node


--split the lines at intersections and assign original attributes, just join sheath_with_loc_topo.edge_data on the sheath_with_loc table:
--Per verificare sia corretta creo una vista da caricare su QGis:
CREATE OR REPLACE VIEW pc_ac05w.v_sheath AS
SELECT r.*, e.geom::geometry(LineString,3003) AS the_geom, row_number() OVER (ORDER BY e.edge_id) AS fid
FROM sheath_with_loc_topo.edge e,
     sheath_with_loc_topo.relation rel,
     pc_ac05w.sheath_with_loc r
WHERE e.edge_id = rel.element_id
  AND rel.topogeo_id = (r.topo_geom).id;
GRANT ALL ON TABLE pc_ac05w.v_sheath TO operatore;
--NO!! Mi crea comunque linee sovrapposte

--Ma cosa contiene esattamente la vista edge?? E' la stessa roba di edge_data....
--Provo ad analizzare un caso specifica, la spezzata che va dal nodo 132 al 53, fa riferimento alla lineaa 20 originale:
SELECT (r.topo_geom).id FROM pc_ac05w.sheath_with_loc r WHERE gid=20; --=25
SELECT * FROM sheath_with_loc_topo.relation rel WHERE topogeo_id=25;
/*
25;1;45;2
25;1;129;2
*/
--45 e 129 sono gli EDGE_ID degli EDGE di cui in realtà si compone il cavo gid=20
--In teoria dunque per ogni EDGE io dovrei ricercarne l'EDGE_ID dentro la tabella relation, da cui poi recupero il campo topogeo_id attraverso il quale poi risalgo al cavo originale.
--Proviamo ancora con questo caso, però partendo dall'EDGE:
SELECT topogeo_id FROM sheath_with_loc_topo.relation rel WHERE element_id = 45;
/*
25
63
*/
SELECT gid, spec_id, fiber_coun FROM pc_ac05w.sheath_with_loc r WHERE (r.topo_geom).id IN (25, 63);
/*
gid=
20
60
*/
--YES!!!
--poi potrei unire le linee che hanno stessi attributi ad esempio creo un array_agg di gid, in questo caso ad esempio [20, 60], e tutti i singoli segmenti che hanno uguale questo campo li unisco in modo tale da non avere troppe spezzate...Si potrebbe funzionare!!


/***** QUERY 1 *****/
SELECT element_id, array_agg(topogeo_id) FROM sheath_with_loc_topo.relation GROUP BY element_id ORDER BY element_id;
--cicli poi dentro il risultato e per ogni element_id recuperi la lista di topogeo_id associata.

/***** QUERY 2 *****/
--questa lista di topogeo_id la usi per selezionare dallo shp originario:
SELECT gid, spec_id, fiber_coun FROM pc_ac05w.sheath_with_loc r WHERE (r.topo_geom).id IN (25, 63);


/***** UNICA QUERY *****/
CREATE TABLE pc_ac05w.cavonuovo_labels AS
WITH elem_topo AS (SELECT element_id, array_agg(topogeo_id) AS topoid_arr FROM sheath_with_loc_topo.relation GROUP BY element_id ORDER BY element_id)
SELECT c.edge_id, foo.*, c.geom FROM sheath_with_loc_topo.edge_data c
LEFT JOIN (
SELECT 
array_to_string(
array_agg('1mc ' || fiber_coun || ' # ' || round(ST_Length(geom)) || 'm')
, ', ') AS cavo_label,
max(element_id) AS elem_id, array_agg(gid) AS gids_cavoroute, array_agg(spec_id) AS spec_id_arr, array_agg(fiber_coun) AS fiber_coun_arr, topoid_arr, count(*)
FROM pc_ac05w.sheath_with_loc r,
elem_topo b
WHERE (r.topo_geom).id = ANY (topoid_arr)
GROUP BY topoid_arr ORDER BY max(element_id)
) AS foo ON foo.elem_id=c.edge_id;
--i record NULL potrebbero individuare degli errori nella geometria dei cavi --> COMUNICA QUESTO ERRORE ALL'UTENTE!!!
SELECT edge_id, topogeo_id, count(*) OVER () FROM pc_ac05w.cavonuovo_labels, sheath_with_loc_topo.relation rel WHERE elem_id IS NULL AND element_id = edge_id ORDER BY topogeo_id;
--if >0 --> SEGNALA ERRORE! I "topogeo_id" elencati potrebbero appartenere a delle geometrie scorrette

--per valutare se l'unione delle geometrie possa essere utile o meno, conto gli elementi:
SELECT
(SELECT count(*) FROM pc_ac05w.cavonuovo_labels a WHERE a.gids_cavoroute IS NOT NULL),
(SELECT count(*) FROM (SELECT gids_cavoroute FROM pc_ac05w.cavonuovo_labels WHERE gids_cavoroute IS NOT NULL GROUP BY gids_cavoroute
) AS foo):
--se i 2 count sono uguali, o differiscono di poco, allora non ha senso unire i segmenti


/* Query di unione geometrie forse inutile...
--A questo punto, posso provare a creare delle geometrie univoche laddove il campo gids_cavi sia il medesimo OVVERO laddove il segmento di cavo è attraversato dagli stessi cavi, sebbene sia stato spezzato all'intersezione con un nodo:
CREATE TABLE pc_ac05w.cavonuovo_uniti_label AS
SELECT row_number() OVER (ORDER BY gids_cavoroute) AS gid, gids_cavoroute, array_agg(edge_id) AS edge_ids_arr, ST_Collect(geom) AS the_geom, ST_Multi(ST_Union(geom)) as singlegeom FROM pc_ac05w.cavonuovo_labels GROUP BY gids_cavoroute;
--in questo caso l'edge_ids_arr ci dice quali segmenti edge non sono associati a dei cavi laddove gids_cavoroute IS NULL...ma prelevo questa informazione con delle query precedenti più raffinate.
--QUEST'ULTIMA QUERY E'INUTILE! Difatti quando spezzo il cavo in base ai nodi, non mi serve più riunirlo: ogni segmento è di fatto portatore di uno specifico numero di fibre. Potrebbero esserci tuttavia dei casi in cui ciò non succede...Al massimo fare una query per valutare ciò.
*/


--Source: http://blog.mathieu-leplatre.info/use-postgis-topologies-to-clean-up-road-networks.html
