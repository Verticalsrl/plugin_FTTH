--Setta il SEARCH_PATH sullo schema di lavoro!
--Creo ai nodi dei punti:
CREATE TEMP TABLE cavoroute_node_labels AS (
WITH ix AS
( SELECT DISTINCT public.ST_Intersection(public.ST_SnapToGrid(a.geom, 0.01), public.ST_SnapToGrid(b.geom, 0.01)) geom 
  FROM cavoroute a JOIN cavoroute b ON public.ST_Intersects(a.geom,b.geom) ),
ix_simple_lines AS 
( SELECT
    (public.ST_Dump(public.ST_LineMerge(public.ST_CollectionExtract(geom, 2)))).geom geom
  FROM
    ix ),
ix_points AS
( SELECT
    (public.ST_Dump(public.ST_CollectionExtract(geom, 1))).geom geom
  FROM
    ix )
SELECT row_number() OVER() id, geom
FROM (
  SELECT public.ST_StartPoint(geom) geom FROM ix_simple_lines
  UNION
  SELECT public.ST_EndPoint(geom) FROM ix_simple_lines
  UNION
  SELECT geom FROM ix_points
) points_union);
CREATE INDEX ON cavoroute_node_labels (id);
CREATE INDEX ON cavoroute_node_labels USING gist (geom);

--Splitto cavoroute sui nodi precedenti:
CREATE TABLE cavoroute_labels AS (
SELECT max(id) AS id, public.ST_UNION(geom) AS geom, gid_cavoroute, sum(count) AS count FROM (
SELECT row_number() OVER() id, geom, array_to_string(array_agg(DISTINCT gid_cavoroute), ',') AS gid_cavoroute, count(*) FROM (
SELECT (public.ST_Dump(public.ST_Split(public.ST_Snap(a.geom, b.geom, 0.01), b.geom))).geom, array_to_string(array_agg(DISTINCT a.gid), ',') AS gid_cavoroute
FROM cavoroute a
JOIN cavoroute_node_labels b 
ON public.ST_DWithin(b.geom, a.geom, 0.01)
WHERE a.net_type != 'Contatori-PTA'
GROUP BY public.ST_Dump(public.ST_Split(public.ST_Snap(a.geom, b.geom, 0.01), b.geom))
) AS foo GROUP BY geom
) AS foo2 GROUP BY gid_cavoroute);

--Creo le etichette sulla tabella:
ALTER TABLE cavoroute_labels ADD COLUMN cavo_label character varying(1250);
UPDATE cavoroute_labels SET cavo_label = label FROM
(SELECT a.id,
--array_to_string(array_agg('1mc ' || b.fibre_coun || ' # ' || b.length_m::integer || 'm'), ', ') AS label
array_to_string(array_agg(array_to_string(temp_cavo_label, ', ')), ', ') AS label
FROM cavoroute_labels a
LEFT JOIN
cavoroute b ON b.gid::text = ANY(string_to_array(a.gid_cavoroute, ','))
GROUP BY id) AS foo WHERE cavoroute_labels.id = foo.id;
