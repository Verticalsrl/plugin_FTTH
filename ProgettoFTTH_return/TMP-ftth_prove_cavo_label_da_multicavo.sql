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


  
  
--Source: http://blog.mathieu-leplatre.info/use-postgis-topologies-to-clean-up-road-networks.html
