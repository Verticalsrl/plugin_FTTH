'''
Numerazione degli elementi della rete compilando il campo naming_of
- approx dell'angolo a 2 decimali
- snap per il merge dela linea da MultiLinestring a Linestring --> ST_SnapToGrid a 0.25m
- lunghezza segmento cavoroute per calcolo degli angoli di 0.5m
- ignoro il cavoroute che poggia su un cavo di tipo "ghost"
'''

from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pgRoutingLayer_utils as Utils
import os
import psycopg2
import psycopg2.extras


#MAIL GATTI del Giovedi 4 Maggio 2017 15:31: NON VA CONSIDERATO L'ULTIMO TRATTO! E' indicato come GHOST nel campo "codice_inf" di cavo.
'''
SOLUZIONE GHOST: individuo il ghost che parte dal punto-sorgente, ne misuro la lunghezza e sposto tutto l'offset della funzione ST_Line_Interpolate_Point invece di solo 0,5mt lo sposto di 0,5mt+lunghezza del cavo ghost.
Al momento lavoro sull'individuare per ogni cavoroute il tratto di cavo con cui si sovrappone, e prendendo solo quello ghost:
SELECT * FROM areacavo1_mestre_bis.cavoroute a, areacavo1_mestre_bis.cavo b WHERE a.gid=5557 AND ST_Covers(a.geom, b.geom) AND codice_inf ~* 'ghost';

Ma come capire se questo tratto sta vicino al "punto sorgente", e dunque escluderlo? Creiamo una TAVOLA TEMP "temp_cavoghost_cavoroute" sul quale mi appoggio, e via...!

'''

QUERY_FIND_ANGLE_TO_PD = """
WITH pgr_netpoints AS (SELECT id_pgr FROM %(schema)s.pgrvertices_netpoints_array WHERE %(gid_elemento)s = ANY(%(campo_gid_pgr)s))
SELECT * FROM (
SELECT %(campo_id_elemento)s, from_p, to_p, pd_gid, length_m, net_type, n_ui,
  trunc(ST_Azimuth( ST_GeometryN(start_geom, 1), ST_GeometryN(end_geom, 1) )::numeric, 2) AS azimuth_to_pd,
  CASE --in questo modo gli angoli minori rispetto alla tratta principale diventano maggiori e dunque numerati per ultimi
    WHEN trunc(ST_Azimuth( ST_GeometryN(end_geom, 1), ST_GeometryN(start_geom, 1) )::numeric, 2) < %(angolo_principale)s THEN coalesce(trunc(ST_Azimuth( ST_GeometryN(end_geom, 1), ST_GeometryN(start_geom, 1) )::numeric, 2) + %(angle_offset)s, 0)
    ELSE coalesce(trunc(ST_Azimuth( ST_GeometryN(end_geom, 1), ST_GeometryN(start_geom, 1) )::numeric, 2), 0)
    --il coalesce in questi casi serve quando "length_m <= (coalesce(length_cavo,0) + 0.5)" --> vedi CASE successivo
    END AS azimuth_from_pd,
  start_geom::geometry(POINT, %(epsg_srid)i)
FROM
(SELECT
  pd.%(campo_id_elemento)s, 
  cavoroute.from_p,
  cavoroute.to_p,
  pd.gid AS pd_gid,
  cavoroute.length_m, 
  cavoroute.net_type, 
  pd.n_ui,
  ST_GeometryN(pd.geom, 1) AS end_geom,
  ST_Line_Locate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ST_GeometryN(pd.geom, 1)) AS start_pd,
  CASE
    WHEN length_m <= (coalesce(length_cavo,0) + 0.5) THEN ST_GeometryN(pd.geom, 1)
    --in questo caso il cavoroute che collegga i 2 pti o e' tutto ghost oppure non e' abbastanza lungo da permettere unn offset di 0.5m su cui piazzare il punto da cui calcolare gli angoli
    WHEN ST_Line_Locate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ST_GeometryN(pd.geom, 1))=0 THEN ST_Line_Interpolate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ((0.5+coalesce(length_cavo,0))/length_m)) --il PD sta all'inizio della linea cavoroute
    WHEN ST_Line_Locate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ST_GeometryN(pd.geom, 1))=1 THEN ST_Line_Interpolate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), 1-((0.5+coalesce(length_cavo,0))/length_m)) --il PD sta alla fine della linea cavoroute
    WHEN ST_Line_Locate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ST_GeometryN(pd.geom, 1))<(0.5/length_m) THEN ST_Line_Interpolate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ((0.5+coalesce(length_cavo,0))/length_m)) --il PD sta entro 0.5m dall'inizio della linea cavoroute
    WHEN ST_Line_Locate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ST_GeometryN(pd.geom, 1))>(1-(0.5/length_m)) THEN ST_Line_Interpolate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), 1-((0.5+coalesce(length_cavo,0))/length_m)) --il PD sta entro 0.5m dalla fine della linea cavoroute
  END --questo CASE non trova il punto se il PD sta ad oltre 0.5m di distanza dall'inizio o dalla fine della linea/cavoroute
   AS start_geom
FROM
  %(schema)s.%(tabella_punto)s AS pd, 
  %(schema)s.cavoroute
LEFT OUTER JOIN
  temp_cavoghost_cavoroute c ON ((c.to_p='%(id_elemento)s' OR c.from_p='%(id_elemento)s') AND (cavoroute.gid=c.gid)
  --adesso vedo che il cavo ghost sia effettivamente connesso al mio punto, altrimenti non mi interessa:
  AND (c.target_cavo=(SELECT id_pgr FROM pgr_netpoints) OR c.source_cavo=(SELECT id_pgr FROM pgr_netpoints))
)
WHERE 
  pd.%(campo_id_elemento)s='%(id_elemento)s' AND (pd.%(campo_id_elemento)s=cavoroute.to_p OR pd.%(campo_id_elemento)s=cavoroute.from_p) ) AS foo
) AS foo2
  %(where_clause)s
ORDER BY azimuth_from_pd ASC, length_m DESC;"""

#In questo caso replico la query di prima ma cerco solo quando il punto e' effettivamente un punto finale che si connette a qualcosa piu' in alto cioe' un from_p:
QUERY_FIND_ANGLE_TO_PD_as_source = """
WITH pgr_netpoints AS (SELECT id_pgr FROM %(schema)s.pgrvertices_netpoints_array WHERE %(gid_elemento)s = ANY(%(campo_gid_pgr)s))
SELECT * FROM (
SELECT %(campo_id_elemento)s, from_p, to_p, pd_gid, length_m, net_type, n_ui,
  trunc(ST_Azimuth( ST_GeometryN(start_geom, 1), ST_GeometryN(end_geom, 1) )::numeric, 2) AS azimuth_to_pd,
  CASE --in questo modo gli angoli minori rispetto alla tratta principale diventano maggiori e dunque numerati per ultimi
    WHEN trunc(ST_Azimuth( ST_GeometryN(end_geom, 1), ST_GeometryN(start_geom, 1) )::numeric, 2) < %(angolo_principale)s THEN coalesce(trunc(ST_Azimuth( ST_GeometryN(end_geom, 1), ST_GeometryN(start_geom, 1) )::numeric, 2) + %(angle_offset)s, 0)
    ELSE coalesce(trunc(ST_Azimuth( ST_GeometryN(end_geom, 1), ST_GeometryN(start_geom, 1) )::numeric, 2), 0)
    --il coalesce in questi casi serve quando "length_m <= (coalesce(length_cavo,0) + 0.5)" --> vedi CASE successivo
    END AS azimuth_from_pd,
  start_geom::geometry(POINT, %(epsg_srid)i)
FROM
(SELECT
  pd.%(campo_id_elemento)s, 
  cavoroute.from_p,
  cavoroute.to_p,
  pd.gid AS pd_gid,
  cavoroute.length_m, 
  cavoroute.net_type, 
  pd.n_ui,
  ST_GeometryN(pd.geom, 1) AS end_geom,
  ST_Line_Locate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ST_GeometryN(pd.geom, 1)) AS start_pd,
  CASE
    WHEN length_m <= (coalesce(length_cavo,0) + 0.5) THEN ST_GeometryN(pd.geom, 1)
    --in questo caso il cavoroute che collega i 2 pti o e' tutto ghost oppure non e' abbastanza lungo da permettere unn offset di 0.5m su cui piazzare il punto da cui calcolare gli angoli
    WHEN ST_Line_Locate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ST_GeometryN(pd.geom, 1))=0 THEN ST_Line_Interpolate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ((0.5+coalesce(length_cavo,0))/length_m)) --il PD sta all'inizio della linea cavoroute
    WHEN ST_Line_Locate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ST_GeometryN(pd.geom, 1))=1 THEN ST_Line_Interpolate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), 1-((0.5+coalesce(length_cavo,0))/length_m)) --il PD sta alla fine della linea cavoroute
    WHEN ST_Line_Locate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ST_GeometryN(pd.geom, 1))<(0.5/length_m) THEN ST_Line_Interpolate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ((0.5+coalesce(length_cavo,0))/length_m)) --il PD sta entro 0.5m dall'inizio della linea cavoroute
    WHEN ST_Line_Locate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), ST_GeometryN(pd.geom, 1))>(1-(0.5/length_m)) THEN ST_Line_Interpolate_Point(ST_GeometryN(ST_LineMerge(ST_SnapToGrid(cavoroute.geom,0.25)), 1), 1-((0.5+coalesce(length_cavo,0))/length_m)) --il PD sta entro 0.5m dalla fine della linea cavoroute
  END --questo CASE non trova il punto se il PD sta ad oltre 0.5m di distanza dall'inizio o dalla fine della linea/cavoroute
   AS start_geom
FROM
  %(schema)s.%(tabella_punto)s AS pd, 
  %(schema)s.cavoroute
LEFT OUTER JOIN
  temp_cavoghost_cavoroute c ON ((c.to_p='%(id_elemento)s' OR c.from_p='%(id_elemento)s') AND (cavoroute.gid=c.gid)
  --adesso vedo che il cavo ghost sia effettivamente connesso al mio punto, altrimenti non mi interessa:
  AND (c.target_cavo=(SELECT id_pgr FROM pgr_netpoints) OR c.source_cavo=(SELECT id_pgr FROM pgr_netpoints))
)
WHERE 
  pd.%(campo_id_elemento)s='%(id_elemento)s' AND (pd.%(campo_id_elemento)s=cavoroute.from_p) ) AS foo
) AS foo2
  %(where_clause)s
ORDER BY azimuth_from_pd ASC, length_m DESC;"""

def add_count(query_add_count, test_conn, cursor_numerazione, tipo_punto):
    try:
        cursor_numerazione.execute(query_add_count)
        test_conn.commit()
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        test_conn.rollback()
    except:
        Utils.logMessage("Campo naming_of e/o fo_attive gia' presente su %s" % (tipo_punto))
        test_conn.rollback()

def numerazione_ftth(dest_dir, self, theSchema):
    test_conn = None    
    test_conn = psycopg2.connect(dest_dir)
    cursor_numerazione = test_conn.cursor()
    dict_cur = test_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    #Innanzitutto controllo e avviso l'utente nel caso in cui il routing non sia eseguito:
    query_check_routing = "SELECT routing_scale_vertici + routing_pta_vertici + routing_giunti_vertici + routing_pd_vertici + routing_pfs_vertici + routing_pfp_vertici + routing_scale_fibre + routing_pta_fibre + routing_giunti_fibre + routing_pd_fibre + routing_pfs_fibre + routing_start FROM %s.variabili_progetto_return" % (theSchema)
    cursor_numerazione.execute(query_check_routing)
    results_check_routing = cursor_numerazione.fetchone()
    msg = QMessageBox()
    if (results_check_routing[0]<12):
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Attenzione routing non completato! Se si continua la procedura potrebbe non fornire dei risultati accurati. Continuare lo stesso?")
        msg.setWindowTitle("Routing non completo: continuare?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
            Utils.logMessage("Numerazione oggetti non effettuata per scelta dell'utente")
            return 0
    
    msg = QMessageBox()
    msg.setWindowTitle("Numerazione punti rete")
    msg.setText("Il processo di numerazione potrebbe durare alcuni minuti. Non chiudere il programma. Ricordarsi inoltre di aver eseguito prima il calcolo del cavoroute e label per avere dei risultati attendibili.")
    msg.setIcon(QMessageBox.Information)
    msg.setStandardButtons(QMessageBox.Ok)
    retval = msg.exec_()
    
    #per primo, aggiungo il campo naming_of ai vari layer se non esiste:
    query_add_count = """ALTER TABLE %s.scala ADD COLUMN naming_of integer;""" % (theSchema)
    add_count(query_add_count, test_conn, cursor_numerazione, 'scala')
    query_add_count = """ALTER TABLE %s.scala ADD COLUMN fo_attive varchar (32);""" % (theSchema)
    add_count(query_add_count, test_conn, cursor_numerazione, 'scala')
    query_add_count = """ALTER TABLE %s.giunti ADD COLUMN naming_of integer;""" % (theSchema)
    add_count(query_add_count, test_conn, cursor_numerazione, 'giunti')
    query_add_count = """ALTER TABLE %s.giunti ADD COLUMN fo_attive varchar (32);""" % (theSchema)
    add_count(query_add_count, test_conn, cursor_numerazione, 'giunti')
    query_add_count = """ALTER TABLE %s.pd ADD COLUMN naming_of integer;""" % (theSchema)
    add_count(query_add_count, test_conn, cursor_numerazione, 'pd')
    query_add_count = """ALTER TABLE %s.pd ADD COLUMN fo_attive varchar (32);""" % (theSchema)
    add_count(query_add_count, test_conn, cursor_numerazione, 'pd')
    
    msg = QMessageBox()
    msg.setWindowTitle("Numerazione punti rete")
    
    try:
    
        ########RESET NAMING########
        query_reset_raw = """UPDATE %(schema)s.scala SET naming_of=NULL, fo_attive=NULL;UPDATE %(schema)s.giunti SET naming_of=NULL, fo_attive=NULL;UPDATE %(schema)s.pd SET naming_of=NULL, fo_attive=NULL;"""
        query_reset = query_reset_raw % {'schema': theSchema}
        cursor_numerazione.execute(query_reset)
        test_conn.commit()
    
        ########TEMP TABLE########
        '''
        query_temp_raw = """CREATE TEMP TABLE temp_cavoghost_cavoroute AS
            SELECT a.gid, a.id_cavo AS id_cavoroute, a.from_p, a.to_p, a.net_type, a.length_m AS length_cavoroute, a.source, a.target, b.source AS source_cavo, b.target AS target_cavo, b.gid AS gid_cavo, b.id_stratt, b.codice_inf, b.id_cavo, b.length_m AS length_cavo
            FROM %(schema)s.cavoroute a, %(schema)s.cavo b WHERE ST_Covers(a.geom, b.geom) AND codice_inf ~* 'ghost';"""
        '''
        #Da mail di Gatti del 18 Mag 2017: escludo anche i cavi "raccordo":
        #Da mail di Gatti del 30 Mag 2017: tolgo b.id_cavo, campo non piu' esistente su cavo. Non dovrebbe creare particolari complicazioni...spero
        query_temp_raw = """CREATE TEMP TABLE temp_cavoghost_cavoroute AS
            SELECT a.gid, a.id_cavo AS id_cavoroute, a.from_p, a.to_p, a.net_type, a.length_m AS length_cavoroute, a.source, a.target, b.source AS source_cavo, b.target AS target_cavo, b.gid AS gid_cavo, b.id_stratt, b.codice_inf, b.length_m AS length_cavo
            FROM %(schema)s.cavoroute a, %(schema)s.cavo b WHERE ST_Covers(a.geom, b.geom) AND (codice_inf ~* 'ghost' OR codice_inf ~* 'raccordo');"""
        query_temp = query_temp_raw % {'schema': theSchema}
        cursor_numerazione.execute(query_temp)
        
        
        ########PTA######## --OK!
        query_giunti = """SELECT id_giunto, max(gid) FROM %s.giunti WHERE tipo_giunt='PTA' GROUP BY id_giunto ORDER BY id_giunto;""" % (theSchema)
        cursor_numerazione.execute(query_giunti)
        results_giunti = cursor_numerazione.fetchall() #tira fuori un dictionary
        for result in results_giunti:
            id_punto = result[0]
            gid_punto = result[1]
            #Utils.logMessage( 'id=%s - gid=%s' % (str(id_punto), str(gid_punto)) )
            if id_punto==None:
                continue
            
            #PTA-PD
            where_clause = 'WHERE net_type=\'%s\'' % (self.NET_TYPE['PTA_PD'])
            query_iniziale = QUERY_FIND_ANGLE_TO_PD_as_source % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pta', 'angle_offset': 0, 'angolo_principale': 0, 'epsg_srid': self.epsg_srid}
            dict_cur.execute(query_iniziale)
            result_iniziale = dict_cur.fetchone()
            #Utils.logMessage(str(query_iniziale))
            if result_iniziale!=None: #ok la situazione e' questa PTA-PD continuo cosi'
                angolo_principale = result_iniziale['azimuth_from_pd']
                #Utils.logMessage(str(angolo_principale))
                if angolo_principale==None:
                    Utils.logMessage("Angolo Nullo: cosa vorra' dire?")
                    #continue
                #Ordino i dati secondo l'angolo e lunghezza:
                where_clause = 'WHERE net_type!=\'%s\' AND azimuth_from_pd>=%f' % (self.NET_TYPE['PTA_PD'], angolo_principale)
                query_seconda = QUERY_FIND_ANGLE_TO_PD % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pta', 'angle_offset': 'radians(360)', 'angolo_principale': angolo_principale, 'epsg_srid': self.epsg_srid}
                #Utils.logMessage(str(query_seconda))
                dict_cur.execute(query_seconda)
                #adesso ho quei punti che hanno un angolo maggiore o uguale alla rotta madre, ordinati dal piu lungo al piu corto:
                results_count = dict_cur.fetchall() #tira fuori un dictionary
                count = 1 #contatore per numerare i punti
                for punto in results_count:
                    net_type = punto['net_type']
                    from_p = punto['from_p']
                    if net_type==self.NET_TYPE['SCALA_PTA']:
                        query_count = "UPDATE %s.scala SET naming_of=%i WHERE id_scala='%s'" % (theSchema, count, from_p)
                    elif net_type==self.NET_TYPE['PTA_PTA']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    #query inutile dopo che passero ai vari livelli PTA-*, per ora mi serve per debug:
                    elif net_type==self.NET_TYPE['GIUNTO_GIUNTO']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    cursor_numerazione.execute(query_count)
                    count += 1
                    test_conn.commit()
                    
            #PTA-PFS
            where_clause = 'WHERE net_type=\'%s\'' % (self.NET_TYPE['PTA_PFS'])
            query_iniziale = QUERY_FIND_ANGLE_TO_PD_as_source % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pta', 'angle_offset': 0, 'angolo_principale': 0, 'epsg_srid': self.epsg_srid}
            dict_cur.execute(query_iniziale)
            result_iniziale = dict_cur.fetchone()
            #Utils.logMessage(str(query_iniziale))
            if result_iniziale!=None: #ok la situazione e' questa PTA-PFS continuo cosi'
                angolo_principale = result_iniziale['azimuth_from_pd']
                #Utils.logMessage(str(angolo_principale))
                if angolo_principale==None:
                    Utils.logMessage("Angolo Nullo: cosa vorra' dire?")
                    #continue
                #Ordino i dati secondo l'angolo e lunghezza:
                where_clause = 'WHERE net_type!=\'%s\' AND azimuth_from_pd>=%f' % (self.NET_TYPE['PTA_PFS'], angolo_principale)
                query_seconda = QUERY_FIND_ANGLE_TO_PD % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pta', 'angle_offset': 'radians(360)', 'angolo_principale': angolo_principale, 'epsg_srid': self.epsg_srid}
                #Utils.logMessage(str(query_seconda))
                dict_cur.execute(query_seconda)
                #adesso ho quei punti che hanno un angolo maggiore o uguale alla rotta madre, ordinati dal piu lungo al piu corto:
                results_count = dict_cur.fetchall() #tira fuori un dictionary
                count = 1 #contatore per numerare i punti
                for punto in results_count:
                    net_type = punto['net_type']
                    from_p = punto['from_p']
                    if net_type==self.NET_TYPE['SCALA_PTA']:
                        query_count = "UPDATE %s.scala SET naming_of=%i WHERE id_scala='%s';" % (theSchema, count, from_p)
                    elif net_type==self.NET_TYPE['PTA_PTA']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s';" % (theSchema, count, from_p)
                    #query inutile dopo che passero ai vari livelli PTA-*, per ora mi serve per debug:
                    elif net_type==self.NET_TYPE['GIUNTO_GIUNTO']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    cursor_numerazione.execute(query_count)
                    count += 1
                    test_conn.commit()
                
            #PTA-PTA
            #Utils.logMessage( 'id=%s - gid=%s' % (str(id_punto), str(gid_punto)) )
            where_clause = 'WHERE net_type=\'%s\'' % (self.NET_TYPE['PTA_PTA'])
            query_iniziale = QUERY_FIND_ANGLE_TO_PD_as_source % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pta', 'angle_offset': 0, 'angolo_principale': 0, 'epsg_srid': self.epsg_srid}
            dict_cur.execute(query_iniziale)
            result_iniziale = dict_cur.fetchone()
            if result_iniziale!=None: #ok la situazione e' questa PTA-PTA continuo cosi'
                angolo_principale = result_iniziale['azimuth_from_pd']
                #Utils.logMessage(str(angolo_principale))
                if angolo_principale==None:
                    Utils.logMessage("Angolo Nullo: cosa vorra' dire?")
                    #continue
                #Ordino i dati secondo l'angolo e lunghezza:
                where_clause = 'WHERE net_type!=\'%s\' AND azimuth_from_pd>=%f' % (self.NET_TYPE['PTA_PTA'], angolo_principale)
                query_seconda = QUERY_FIND_ANGLE_TO_PD % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pta', 'angle_offset': 'radians(360)', 'angolo_principale': angolo_principale, 'epsg_srid': self.epsg_srid}
                #Utils.logMessage(str(query_seconda))
                dict_cur.execute(query_seconda)
                #adesso ho quei punti che hanno un angolo maggiore o uguale alla rotta madre, ordinati dal piu lungo al piu corto:
                results_count = dict_cur.fetchall() #tira fuori un dictionary
                count = 1 #contatore per numerare i punti
                for punto in results_count:
                    net_type = punto['net_type']
                    from_p = punto['from_p']
                    if net_type==self.NET_TYPE['SCALA_PTA']:
                        query_count = "UPDATE %s.scala SET naming_of=%i WHERE id_scala='%s'" % (theSchema, count, from_p)
                    #un secondo livello pta-pta non sarebbe possibile ma non si sa mai...
                    elif net_type==self.NET_TYPE['PTA_PTA']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    cursor_numerazione.execute(query_count)
                    count += 1
                    test_conn.commit()
                
            #PTA-GIUNTO
            where_clause = 'WHERE net_type=\'%s\'' % (self.NET_TYPE['PTA_GIUNTO'])
            query_iniziale = QUERY_FIND_ANGLE_TO_PD_as_source % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pta', 'angle_offset': 0, 'angolo_principale': 0, 'epsg_srid': self.epsg_srid}
            dict_cur.execute(query_iniziale)
            result_iniziale = dict_cur.fetchone()
            #Utils.logMessage(str(query_iniziale))
            if result_iniziale!=None: #ok la situazione e' questa PTA-GIUNTO continuo cosi'
                angolo_principale = result_iniziale['azimuth_from_pd']
                #Utils.logMessage(str(angolo_principale))
                if angolo_principale==None:
                    Utils.logMessage("Angolo Nullo: cosa vorra' dire?")
                    #continue
                #Ordino i dati secondo l'angolo e lunghezza:
                where_clause = 'WHERE net_type!=\'%s\' AND azimuth_from_pd>=%f' % (self.NET_TYPE['PTA_GIUNTO'], angolo_principale)
                query_seconda = QUERY_FIND_ANGLE_TO_PD % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pta', 'angle_offset': 'radians(360)', 'angolo_principale': angolo_principale, 'epsg_srid': self.epsg_srid}
                #Utils.logMessage(str(query_seconda))
                dict_cur.execute(query_seconda)
                #adesso ho quei punti che hanno un angolo maggiore o uguale alla rotta madre, ordinati dal piu lungo al piu corto:
                results_count = dict_cur.fetchall() #tira fuori un dictionary
                count = 1 #contatore per numerare i punti
                for punto in results_count:
                    net_type = punto['net_type']
                    from_p = punto['from_p']
                    if net_type==self.NET_TYPE['SCALA_PTA']:
                        query_count = "UPDATE %s.scala SET naming_of=%i WHERE id_scala='%s'" % (theSchema, count, from_p)
                    elif net_type==self.NET_TYPE['PTA_GIUNTO']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    cursor_numerazione.execute(query_count)
                    count += 1
                    test_conn.commit()
                
            #Continuando a ciclare dentro i PTA popolo il campo FO_ATTIVE recuperando gli elementi connessi a questo punto della rete:
            query_fo_attive = """UPDATE %s.scala SET fo_attive=foo.fo_attive FROM
        (SELECT id_scala AS id_pto, gid AS gid_pto, n_ui, naming_of,
        (SUM(n_ui) OVER (ORDER BY naming_of ASC) - n_ui + 1 || '-' ||
        SUM(n_ui) OVER (ORDER BY naming_of ASC)) AS fo_attive
        FROM %s.scala WHERE id_giunto='%s' AND id_sc_ref IS NULL ORDER BY naming_of ASC) AS foo WHERE foo.id_pto=scala.id_scala;""" % (theSchema, theSchema, id_punto)
            cursor_numerazione.execute(query_fo_attive)
            test_conn.commit()
            
            #Continuando a ciclare dentro i PTA popolo il campo FO_ATTIVE recuperando gli elementi connessi a questo punto della rete ad altri PTA:
            query_fo_attive = """UPDATE %s.giunti SET fo_attive=foo.fo_attive FROM
        (SELECT id_giunto AS id_pto, gid AS gid_pto, n_ui, naming_of,
        (SUM(n_ui) OVER (ORDER BY naming_of ASC) - n_ui + 1 || '-' ||
        SUM(n_ui) OVER (ORDER BY naming_of ASC)) AS fo_attive
        FROM %s.giunti WHERE id_g_ref='%s' ORDER BY naming_of ASC) AS foo WHERE foo.id_pto=giunti.id_giunto;""" % (theSchema, theSchema, id_punto)
            cursor_numerazione.execute(query_fo_attive)
            test_conn.commit()

        Utils.logMessage('Fine analisi per numerazione PTA')
        
        ########GIUNTO######## --OK!
        query_giunti = """SELECT id_giunto, max(gid) FROM %s.giunti WHERE tipo_giunt!='PTA' GROUP BY id_giunto ORDER BY id_giunto;""" % (theSchema)
        cursor_numerazione.execute(query_giunti)
        results_giunti = cursor_numerazione.fetchall() #tira fuori un dictionary
        for result in results_giunti:
            id_punto = result[0]
            gid_punto = result[1]
            if id_punto==None:
                continue
            
            #GIUNTO-GIUNTO
            where_clause = 'WHERE net_type=\'%s\'' % (self.NET_TYPE['GIUNTO_GIUNTO'])
            query_iniziale = QUERY_FIND_ANGLE_TO_PD_as_source % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_giunto', 'angle_offset': 0, 'angolo_principale': 0, 'epsg_srid': self.epsg_srid}
            dict_cur.execute(query_iniziale)
            result_iniziale = dict_cur.fetchone()
            if result_iniziale!=None: #ok la situazione e' questa GIUNTO-GIUNTO continuo cosi'
                angolo_principale = result_iniziale['azimuth_from_pd']
                #Utils.logMessage(str(angolo_principale))
                if angolo_principale==None:
                    Utils.logMessage("Angolo Nullo: cosa vorra' dire?")
                    #continue
                #Ordino i dati secondo l'angolo e lunghezza:
                where_clause = 'WHERE net_type!=\'%s\' AND azimuth_from_pd>=%f' % (self.NET_TYPE['GIUNTO_GIUNTO'], angolo_principale)
                query_seconda = QUERY_FIND_ANGLE_TO_PD % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_giunto', 'angle_offset': 'radians(360)', 'angolo_principale': angolo_principale, 'epsg_srid': self.epsg_srid}
                dict_cur.execute(query_seconda)
                #adesso ho quei punti che hanno un angolo maggiore o uguale alla rotta madre, ordinati dal piu lungo al piu corto:
                results_count = dict_cur.fetchall() #tira fuori un dictionary
                count = 1 #contatore per numerare i punti
                for punto in results_count:
                    net_type = punto['net_type']
                    from_p = punto['from_p']
                    if net_type==self.NET_TYPE['SCALA_GIUNTO']:
                        query_count = "UPDATE %s.scala SET naming_of=%i WHERE id_scala='%s'" % (theSchema, count, from_p)
                    elif net_type==self.NET_TYPE['PTA_GIUNTO']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    #giunto-giunto non dovrebbe essere possibile in un collegamento gia' giunto-giunto ma non si sa mai:
                    elif net_type==self.NET_TYPE['GIUNTO_GIUNTO']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    cursor_numerazione.execute(query_count)
                    count += 1
                    test_conn.commit()
            
            #GIUNTO-PD
            where_clause = 'WHERE net_type=\'%s\'' % (self.NET_TYPE['GIUNTO_PD'])
            query_iniziale = QUERY_FIND_ANGLE_TO_PD_as_source % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_giunto', 'angle_offset': 0, 'angolo_principale': 0, 'epsg_srid': self.epsg_srid}
            dict_cur.execute(query_iniziale)
            result_iniziale = dict_cur.fetchone()
            if result_iniziale!=None: #ok la situazione e' questa GIUNTO-PD continuo cosi'
                angolo_principale = result_iniziale['azimuth_from_pd']
                #Utils.logMessage(str(angolo_principale))
                if angolo_principale==None:
                    Utils.logMessage("Angolo Nullo: cosa vorra' dire?")
                    #continue
                #Ordino i dati secondo l'angolo e lunghezza:
                where_clause = 'WHERE net_type!=\'%s\' AND azimuth_from_pd>=%f' % (self.NET_TYPE['GIUNTO_PD'], angolo_principale)
                query_seconda = QUERY_FIND_ANGLE_TO_PD % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'giunti', 'campo_id_elemento': 'id_giunto', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_giunto', 'angle_offset': 'radians(360)', 'angolo_principale': angolo_principale, 'epsg_srid': self.epsg_srid}
                dict_cur.execute(query_seconda)
                #adesso ho quei punti che hanno un angolo maggiore o uguale alla rotta madre, ordinati dal piu lungo al piu corto:
                results_count = dict_cur.fetchall() #tira fuori un dictionary
                count = 1 #contatore per numerare i punti
                for punto in results_count:
                    net_type = punto['net_type']
                    from_p = punto['from_p']
                    if net_type==self.NET_TYPE['SCALA_GIUNTO']:
                        query_count = "UPDATE %s.scala SET naming_of=%i WHERE id_scala='%s'" % (theSchema, count, from_p)
                    elif net_type==self.NET_TYPE['PTA_GIUNTO']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    elif net_type==self.NET_TYPE['GIUNTO_GIUNTO']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    cursor_numerazione.execute(query_count)
                    count += 1
                    test_conn.commit()
                    
            #Continuando a ciclare dentro i GIUNTI popolo il campo FO_ATTIVE recuperando gli elementi connessi a questo punto della rete:
            query_fo_attive = """UPDATE %s.scala SET fo_attive=foo.fo_attive FROM
        (SELECT id_scala AS id_pto, gid AS gid_pto, n_ui, naming_of,
        (SUM(n_ui) OVER (ORDER BY naming_of ASC) - n_ui + 1 || '-' ||
        SUM(n_ui) OVER (ORDER BY naming_of ASC)) AS fo_attive
        FROM %s.scala WHERE id_giunto='%s' AND id_sc_ref IS NULL ORDER BY naming_of ASC) AS foo WHERE foo.id_pto=scala.id_scala;""" % (theSchema, theSchema, id_punto)
            cursor_numerazione.execute(query_fo_attive)
            test_conn.commit()
            
            #Continuando a ciclare dentro i GIUNTI popolo il campo FO_ATTIVE recuperando gli elementi connessi a questo punto della rete ad altri GIUNTI:
            query_fo_attive = """UPDATE %s.giunti SET fo_attive=foo.fo_attive FROM
        (SELECT id_giunto AS id_pto, gid AS gid_pto, n_ui, naming_of,
        (SUM(n_ui) OVER (ORDER BY naming_of ASC) - n_ui + 1 || '-' ||
        SUM(n_ui) OVER (ORDER BY naming_of ASC)) AS fo_attive
        FROM %s.giunti WHERE id_g_ref='%s' ORDER BY naming_of ASC) AS foo WHERE foo.id_pto=giunti.id_giunto;""" % (theSchema, theSchema, id_punto)
            cursor_numerazione.execute(query_fo_attive)
            test_conn.commit()

        Utils.logMessage('Fine analisi per numerazione GIUNTI')

        ########PD######## --OK!
        query_pd = """SELECT id_pd, max(gid) FROM %s.pd GROUP BY id_pd ORDER BY id_pd;""" % (theSchema)
        cursor_numerazione.execute(query_pd)
        results_pd = cursor_numerazione.fetchall() #tira fuori un dictionary
        for result in results_pd:
            id_punto = result[0]
            gid_punto = result[1]
            if id_punto==None:
                continue
            
            where_clause = 'WHERE net_type=\'%s\'' % (self.NET_TYPE['PD_PFS'])
            query_iniziale = QUERY_FIND_ANGLE_TO_PD_as_source % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'pd', 'campo_id_elemento': 'id_pd', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pd', 'angle_offset': 0, 'angolo_principale': 0, 'epsg_srid': self.epsg_srid}
            dict_cur.execute(query_iniziale)
            #come prendere l'angolo pd-pfs? come ordinare gli altri punti secondo questo angolo e secondo la lunghezza del cavo???
            result_iniziale = dict_cur.fetchone()
            if result_iniziale!=None: #ok la situazione e' questa PD_PFS continuo cosi'
                angolo_principale = result_iniziale['azimuth_from_pd']
                #Utils.logMessage(str(angolo_principale))
                if angolo_principale==None:
                    Utils.logMessage("Angolo Nullo: cosa vorra' dire?")
                #Ordino i dati secondo l'angolo e lunghezza:
                where_clause = 'WHERE net_type!=\'%s\' AND azimuth_from_pd>=%f' % (self.NET_TYPE['PD_PFS'], angolo_principale)
                query_seconda = QUERY_FIND_ANGLE_TO_PD % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'pd', 'campo_id_elemento': 'id_pd', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pd', 'angle_offset': 'radians(360)', 'angolo_principale': angolo_principale, 'epsg_srid': self.epsg_srid}
                dict_cur.execute(query_seconda)
                #adesso ho quei punti che hanno un angolo maggiore o uguale al PD-PFS, ordinati dal piu lungo al piu corto:
                results_count = dict_cur.fetchall() #tira fuori un dictionary
                count = 1 #contatore per numerare i punti
                for punto in results_count:
                    net_type = punto['net_type']
                    from_p = punto['from_p']
                    if net_type==self.NET_TYPE['SCALA_PD']:
                        query_count = "UPDATE %s.scala SET naming_of=%i WHERE id_scala='%s'" % (theSchema, count, from_p)
                    elif net_type==self.NET_TYPE['PTA_PD']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    elif net_type==self.NET_TYPE['GIUNTO_PD']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s'" % (theSchema, count, from_p)
                    cursor_numerazione.execute(query_count)
                    count += 1
                    test_conn.commit()
                
            #Continuando a ciclare dentro i PD popolo il campo FO_ATTIVE recuperando gli elementi connessi a questo punto della rete:
            query_fo_attive_raw = """UPDATE %(schema)s.scala SET fo_attive=foo.fo_attive FROM
        (SELECT * FROM (
        SELECT *, 
        (SUM(n_ui) OVER (ORDER BY naming_of ASC) - n_ui + 1 || '-' ||
        SUM(n_ui) OVER (ORDER BY naming_of ASC)) AS fo_attive
        FROM (
        SELECT 'SCALA'::text AS tipo_pto, id_scala AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer
        FROM %(schema)s.scala WHERE id_pd='%(id_elemento)s' AND id_giunto IS NULL AND id_sc_ref IS NULL
        UNION
        select 'GIUNTO'::text AS tipo_pto, id_giunto AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer from %(schema)s.giunti WHERE id_pd='%(id_elemento)s' AND id_g_ref IS NULL
        ORDER BY naming_of ASC) AS foo3
        ) AS foo2
        WHERE foo2.tipo_pto='SCALA') AS foo 
            WHERE foo.id_pto=scala.id_scala;"""
            query_fo_attive = query_fo_attive_raw % {'schema': theSchema, 'id_elemento': id_punto}
            #Utils.logMessage(query_fo_attive)
            cursor_numerazione.execute(query_fo_attive)
            
            query_fo_attive_raw = """UPDATE %(schema)s.giunti SET fo_attive=foo.fo_attive FROM
        (SELECT * FROM (
        SELECT *, 
        (SUM(n_ui) OVER (ORDER BY naming_of ASC) - n_ui + 1 || '-' ||
        SUM(n_ui) OVER (ORDER BY naming_of ASC)) AS fo_attive
        FROM (
        SELECT 'SCALA'::text AS tipo_pto, id_scala AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer
        FROM %(schema)s.scala WHERE id_pd='%(id_elemento)s' AND id_giunto IS NULL AND id_sc_ref IS NULL
        UNION
        select 'GIUNTO'::text AS tipo_pto, id_giunto AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer from %(schema)s.giunti WHERE id_pd='%(id_elemento)s' AND id_g_ref IS NULL
        ORDER BY naming_of ASC) AS foo3
        ) AS foo2
        WHERE foo2.tipo_pto='GIUNTO') AS foo 
            WHERE foo.id_pto=giunti.id_giunto;"""
            query_fo_attive = query_fo_attive_raw % {'schema': theSchema, 'id_elemento': id_punto}
            cursor_numerazione.execute(query_fo_attive)
            test_conn.commit()
            
            #Continuando a ciclare dentro i PD popolo il campo FO_ATTIVE recuperando gli elementi connessi a questo punto della rete ad altri PD:
            query_fo_attive = """UPDATE %s.pd SET fo_attive=foo.fo_attive FROM
        (SELECT id_pd AS id_pto, gid AS gid_pto, n_ui, naming_of,
        (SUM(n_ui) OVER (ORDER BY naming_of ASC) - n_ui + 1 || '-' ||
        SUM(n_ui) OVER (ORDER BY naming_of ASC)) AS fo_attive
        FROM %s.pd WHERE id_pd_ref='%s' ORDER BY naming_of ASC) AS foo WHERE foo.id_pto=pd.id_pd;""" % (theSchema, theSchema, id_punto)
            cursor_numerazione.execute(query_fo_attive)
            test_conn.commit()
        
        Utils.logMessage('Fine analisi per numerazione PD')
        
        ########PFS######## --OK!
        query_pfs = """SELECT id_pfs, max(gid) FROM %s.pfs GROUP BY id_pfs ORDER BY id_pfs;""" % (theSchema)
        cursor_numerazione.execute(query_pfs)
        results_pfs = cursor_numerazione.fetchall() #tira fuori un dictionary
        for result in results_pfs:
            id_punto = result[0]
            gid_punto = result[1]
            if id_punto==None:
                continue
            
            where_clause = 'WHERE net_type=\'%s\'' % (self.NET_TYPE['PFS_PFP'])
            query_iniziale = QUERY_FIND_ANGLE_TO_PD_as_source % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'pfs', 'campo_id_elemento': 'id_pfs', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pfs', 'angle_offset': 0, 'angolo_principale': 0, 'epsg_srid': self.epsg_srid}
            dict_cur.execute(query_iniziale)
            #come prendere l'angolo pd-pfs? come ordinare gli altri punti secondo questo angolo e secondo la lunghezza del cavo???
            result_iniziale = dict_cur.fetchone()
            if result_iniziale!=None: #ok la situazione e' questa PFS_PFP continuo cosi'
                angolo_principale = result_iniziale['azimuth_from_pd']
                #Utils.logMessage(str(angolo_principale))
                if angolo_principale==None:
                    Utils.logMessage("Angolo Nullo: cosa vorra' dire?")
                #Ordino i dati secondo l'angolo e lunghezza:
                where_clause = 'WHERE net_type!=\'%s\' AND azimuth_from_pd>=%f' % (self.NET_TYPE['PFS_PFP'], angolo_principale)
                query_seconda = QUERY_FIND_ANGLE_TO_PD % {'schema': theSchema, 'id_elemento': id_punto, 'tabella_punto': 'pfs', 'campo_id_elemento': 'id_pfs', 'where_clause': where_clause, 'gid_elemento': gid_punto, 'campo_gid_pgr': 'gid_pfs', 'angle_offset': 'radians(360)', 'angolo_principale': angolo_principale, 'epsg_srid': self.epsg_srid}
                dict_cur.execute(query_seconda)
                #adesso ho quei punti che hanno un angolo maggiore o uguale al PD-PFS, ordinati dal piu lungo al piu corto:
                results_count = dict_cur.fetchall() #tira fuori un dictionary
                count = 1 #contatore per numerare i punti
                for punto in results_count:
                    net_type = punto['net_type']
                    from_p = punto['from_p']
                    if net_type==self.NET_TYPE['SCALA_PFS']:
                        query_count = "UPDATE %s.scala SET naming_of=%i WHERE id_scala='%s';" % (theSchema, count, from_p)
                    elif net_type==self.NET_TYPE['PTA_PFS']:
                        query_count = "UPDATE %s.giunti SET naming_of=%i WHERE id_giunto='%s';" % (theSchema, count, from_p)
                    elif net_type==self.NET_TYPE['PD_PFS']:
                        query_count = "UPDATE %s.pd SET naming_of=%i WHERE id_pd='%s';" % (theSchema, count, from_p)
                    cursor_numerazione.execute(query_count)
                    count += 1
                    test_conn.commit()
                    
            #Continuando a ciclare dentro i PFS popolo il campo FO_ATTIVE recuperando gli elementi connessi a questo punto della rete:
            query_fo_attive_raw = """UPDATE %(schema)s.scala SET fo_attive=foo.fo_attive FROM
        (SELECT * FROM (
        SELECT *, 
        (SUM(n_ui) OVER (ORDER BY naming_of ASC) - n_ui + 1 || '-' ||
        SUM(n_ui) OVER (ORDER BY naming_of ASC)) AS fo_attive
        FROM (
        SELECT 'SCALA'::text AS tipo_pto, id_scala AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer
        FROM %(schema)s.scala WHERE id_pfs='%(id_elemento)s' AND id_pd IS NULL AND id_giunto IS NULL AND id_sc_ref IS NULL
        UNION
        select 'PTA'::text AS tipo_pto, id_giunto AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer from %(schema)s.giunti WHERE id_pfs='%(id_elemento)s' AND id_pd IS NULL AND id_g_ref IS NULL
        UNION
        select 'PD'::text AS tipo_pto, id_pd AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer from %(schema)s.pd WHERE id_pfs='%(id_elemento)s' AND id_pd_ref IS NULL
        ORDER BY naming_of ASC) AS foo3
        ) AS foo2
        WHERE foo2.tipo_pto='SCALA') AS foo 
            WHERE foo.id_pto=scala.id_scala;"""
            query_fo_attive = query_fo_attive_raw % {'schema': theSchema, 'id_elemento': id_punto}
            #Utils.logMessage(query_fo_attive)
            cursor_numerazione.execute(query_fo_attive)
            
            query_fo_attive_raw = """UPDATE %(schema)s.giunti SET fo_attive=foo.fo_attive FROM
        (SELECT * FROM (
        SELECT *, 
        (SUM(n_ui) OVER (ORDER BY naming_of ASC) - n_ui + 1 || '-' ||
        SUM(n_ui) OVER (ORDER BY naming_of ASC)) AS fo_attive
        FROM (
        SELECT 'SCALA'::text AS tipo_pto, id_scala AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer
        FROM %(schema)s.scala WHERE id_pfs='%(id_elemento)s' AND id_pd IS NULL AND id_giunto IS NULL AND id_sc_ref IS NULL
        UNION
        select 'PTA'::text AS tipo_pto, id_giunto AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer from %(schema)s.giunti WHERE id_pfs='%(id_elemento)s' AND id_pd IS NULL AND id_g_ref IS NULL
        UNION
        select 'PD'::text AS tipo_pto, id_pd AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer from %(schema)s.pd WHERE id_pfs='%(id_elemento)s' AND id_pd_ref IS NULL
        ORDER BY naming_of ASC) AS foo3
        ) AS foo2
        WHERE foo2.tipo_pto='PTA') AS foo 
            WHERE foo.id_pto=giunti.id_giunto;"""
            query_fo_attive = query_fo_attive_raw % {'schema': theSchema, 'id_elemento': id_punto}
            cursor_numerazione.execute(query_fo_attive)
            test_conn.commit()
            
            query_fo_attive_raw = """UPDATE %(schema)s.pd SET fo_attive=foo.fo_attive FROM
        (SELECT * FROM (
        SELECT *, 
        (SUM(n_ui) OVER (ORDER BY naming_of ASC) - n_ui + 1 || '-' ||
        SUM(n_ui) OVER (ORDER BY naming_of ASC)) AS fo_attive
        FROM (
        SELECT 'SCALA'::text AS tipo_pto, id_scala AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer
        FROM %(schema)s.scala WHERE id_pfs='%(id_elemento)s' AND id_pd IS NULL AND id_giunto IS NULL AND id_sc_ref IS NULL
        UNION
        select 'PTA'::text AS tipo_pto, id_giunto AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer from %(schema)s.giunti WHERE id_pfs='%(id_elemento)s' AND id_pd IS NULL AND id_g_ref IS NULL
        UNION
        select 'PD'::text AS tipo_pto, id_pd AS id_pto, gid::integer AS gid_pto, n_ui::integer, naming_of::integer from %(schema)s.pd WHERE id_pfs='%(id_elemento)s' AND id_pd_ref IS NULL
        ORDER BY naming_of ASC) AS foo3
        ) AS foo2
        WHERE foo2.tipo_pto='PD') AS foo 
            WHERE foo.id_pto=pd.id_pd;"""
            query_fo_attive = query_fo_attive_raw % {'schema': theSchema, 'id_elemento': id_punto}
            cursor_numerazione.execute(query_fo_attive)
            test_conn.commit()
        
        Utils.logMessage('Fine analisi per numerazione PFS')
    
    except psycopg2.Error, e:
        msg.setText(e.pgerror)
        Utils.logMessage(str(e.pgerror))
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        return 0
    except SystemError, e:
        msg.setText("Errore di sistema")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        return 0
    else:
        msg.setText("Processo concluso con successo")
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        return 1
    finally:
        if test_conn:
            cursor_numerazione.close()
            dict_cur.close()
            test_conn.close()
