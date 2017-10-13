
import pgRoutingLayer_utils as Utils
import os
import psycopg2
import re

QUERY_NAME = {
        'SCALA': 'QUERY_SCALA',
        'GIUNTO': 'QUERY_GIUNTO',
        'PD': 'QUERY_PD',
        'PFS': 'QUERY_PFS',
        'PFP': 'id_pfp'
    }

QUERY_SCALA_no_giunti_figli = """SELECT id_scala, array_agg(DISTINCT gid_giunto_padre) AS giunti_padre, array_agg(gid_scala) AS scale_figli, array_agg(DISTINCT gid_pd) AS pd_padre, array_agg(DISTINCT gid_pfs) AS pfs_padre, count(*) AS n_cont, max(n_ui) AS n_ui, 999 AS n_giunti_figli
    FROM
    (SELECT 
    a.gid AS gid_scala, a.id_scala, a.id_pop, a.id_pfp, a.id_pfs, a.id_pd AS pd_da_scala, a.id_giunto, a.n_ui,
    c.gid AS gid_pd, c.id_pd,
    d.gid AS gid_giunto_padre, d.id_giunto AS id_giunto_padre,
    e.gid AS gid_pfs, e.id_pfs
    FROM %(schema)s.scala a
    LEFT JOIN
    %(schema)s.giunti d ON a.id_giunto=d.id_giunto
    LEFT JOIN
    %(schema)s.pd c ON a.id_pd=c.id_pd    
    LEFT JOIN
    %(schema)s.pfs e ON a.id_pfs=e.id_pfs
    WHERE a.id_scala='%(id_oggetto)s'
    ) AS foo
    GROUP BY foo.id_scala;"""
    
QUERY_SCALA = """SELECT id_scala, 
array_agg(DISTINCT row(gid_giunto_figlio, gid_giunto_padre)) AS giunti,
array_agg(gid_scala) AS scale_figli, array_agg(DISTINCT gid_pd) AS pd_padre, array_agg(DISTINCT gid_pfs) AS pfs_padre, count(*) AS n_cont, max(n_ui) AS n_ui, count(gid_giunto_padre)+count(gid_giunto_figlio) AS n_giunti_padre, array_agg(foo.gid_cavoroute) AS gid_cavoroute
    FROM
    (SELECT 
    a.gid AS gid_scala, a.id_scala, a.id_pop, a.id_pfp, a.id_pfs, a.id_pd AS pd_da_scala, a.id_giunto, a.n_ui,
    c.gid AS gid_pd, c.id_pd,
    d.gid AS gid_giunto_figlio, d.id_giunto AS id_giunto_figlio,
    e.gid AS gid_pfs, e.id_pfs,
    padre.gid AS gid_giunto_padre, padre.id_giunto AS id_giunto_padre,
    f.gid AS gid_cavoroute
    FROM %(schema)s.scala a
    LEFT JOIN
    %(schema)s.giunti d ON a.id_giunto=d.id_giunto
LEFT JOIN
%(schema)s.giunti padre ON d.id_g_ref=padre.id_giunto
    LEFT JOIN
    %(schema)s.pd c ON a.id_pd=c.id_pd    
    LEFT JOIN
    %(schema)s.pfs e ON a.id_pfs=e.id_pfs
    LEFT JOIN
    %(schema)s.cavoroute f ON a.id_scala=f.from_p
    WHERE a.id_scala='%(id_oggetto)s'
    ) AS foo
    GROUP BY foo.id_scala;"""

QUERY_GIUNTO_no_padre_figlio = """SELECT id_giunto, array_agg(DISTINCT gid_giunti_figli) AS giunti_figli, array_agg(gid_scala) AS scale_figli, array_agg(DISTINCT gid_pd) AS pd_padre, array_agg(DISTINCT gid_pfs) AS pfs_padre, max(n_cont) AS n_cont, max(n_ui) AS n_ui, 999 AS n_giunti_figli, array_agg(DISTINCT foo.gid_cavoroute) AS gid_cavoroute
    FROM
    (SELECT 
    a.gid, a.id_giunto, a.id_pop, a.id_pfp, a.id_pfs, a.id_pd AS pd_da_giunto, a.id_g_ref, a.n_cont, a.n_ui,
    b.gid AS gid_scala, b.id_scala,
    c.gid AS gid_pd, c.id_pd,
    d.gid AS gid_giunti_figli, d.id_giunto AS id_giunto_figlio,
    e.gid AS gid_pfs, e.id_pfs,
    f.gid AS gid_cavoroute
    FROM %(schema)s.giunti a
    LEFT JOIN
    %(schema)s.scala b ON a.id_giunto=b.id_giunto
    LEFT JOIN
    %(schema)s.pd c ON a.id_pd=c.id_pd
    LEFT JOIN
    %(schema)s.giunti d ON a.id_g_ref=d.id_giunto
    LEFT JOIN
    %(schema)s.pfs e ON a.id_pfs=e.id_pfs
    LEFT JOIN
    %(schema)s.cavoroute f ON a.id_giunto IN (f.from_p, f.to_p)
    WHERE a.id_giunto='%(id_oggetto)s'
    ) AS foo
    GROUP BY foo.id_giunto;"""
    
#query modificata per individuare sia g_padre che g_figlio, mutualmente esclusivi (da regole):
QUERY_GIUNTO = """SELECT id_giunto, 
array_agg(DISTINCT gid_giunti_figli) AS giunto_figlio,
array_agg(gid_scala) AS scale_figli, array_agg(DISTINCT gid_pd) AS pd_padre, array_agg(DISTINCT gid_pfs) AS pfs_padre, max(n_cont) AS n_cont, max(n_ui) AS n_ui, array_length(array_agg(DISTINCT gid_giunto_padre_figlio), 1) AS n_giunti_padre_figli, array_agg(DISTINCT foo.gid_cavoroute) AS gid_cavoroute, array_agg(DISTINCT gid_giunto_padre) AS giunto_padre
    FROM
    (SELECT 
    a.gid, a.id_giunto, a.id_pop, a.id_pfp, a.id_pfs, a.id_pd AS pd_da_giunto, a.id_g_ref, a.n_cont, a.n_ui,
    b.gid AS gid_scala, b.id_scala,
    c.gid AS gid_pd, c.id_pd,
    d.gid AS gid_giunto_padre, d.id_giunto AS id_giunto_padre,
    dd.gid AS gid_giunti_figli, dd.id_giunto AS id_giunto_figlio,
    CASE WHEN dd.gid IS NOT NULL THEN dd.gid
    WHEN d.gid IS NOT NULL THEN d.gid
    ELSE -999
    END AS gid_giunto_padre_figlio,
    e.gid AS gid_pfs, e.id_pfs,
    f.gid AS gid_cavoroute
    FROM %(schema)s.giunti a
    LEFT JOIN
    %(schema)s.scala b ON a.id_giunto=b.id_giunto
    LEFT JOIN
    %(schema)s.pd c ON a.id_pd=c.id_pd
    LEFT JOIN
    %(schema)s.giunti d ON a.id_g_ref=d.id_giunto
    LEFT JOIN
    %(schema)s.giunti dd ON a.id_giunto=dd.id_g_ref
    LEFT JOIN
    %(schema)s.pfs e ON a.id_pfs=e.id_pfs
    LEFT JOIN
    %(schema)s.cavoroute f ON a.id_giunto IN (f.from_p, f.to_p)
    WHERE a.id_giunto='%(id_oggetto)s'
    ) AS foo
    GROUP BY foo.id_giunto;"""
    
QUERY_PD = """SELECT id_pd, array_agg(DISTINCT gid_giunto) AS giunti_figli, array_agg(DISTINCT gid_scala) AS scale_figli, array_agg(DISTINCT gid_pd) AS pd_self, array_agg(DISTINCT gid_pfs) AS pfs_padre, max(n_cont) AS n_cont, max(n_ui) AS n_ui, max(n_giunti) AS n_giunti, array_agg(DISTINCT foo.gid_cavoroute) AS gid_cavoroute
    FROM
    (SELECT 
    a.gid AS gid_pd, a.id_pd, a.id_pop, a.id_pfp, a.id_pfs, a.n_cont, a.n_ui, n_giunti,
    b.gid AS gid_scala, b.id_scala,
    c.gid AS gid_giunto, c.id_giunto,
    d.gid AS gid_pfs, d.id_pfs,
    f.gid AS gid_cavoroute
    FROM %(schema)s.pd a
    LEFT JOIN
    %(schema)s.scala b ON a.id_pd=b.id_pd
    LEFT JOIN
    %(schema)s.giunti c ON a.id_pd=c.id_pd
    LEFT JOIN
    %(schema)s.pfs d ON a.id_pfs=d.id_pfs
    LEFT JOIN
    %(schema)s.cavoroute f ON a.id_pd IN (f.from_p, f.to_p)
    WHERE a.id_pd='%(id_oggetto)s'
    ) AS foo
    GROUP BY foo.id_pd;"""

QUERY_PFS = """SELECT id_pfs, array_agg(DISTINCT gid_giunto) AS giunti_figli, array_agg(DISTINCT gid_scala) AS scale_figli, array_agg(DISTINCT gid_pd) AS pd_figli, array_agg(DISTINCT gid_pfs) AS pfs_self, max(n_pd) AS n_pd, max(n_ui) AS n_ui, 999 AS niente, array_agg(DISTINCT foo.gid_cavoroute) AS gid_cavoroute
    FROM
    (SELECT 
    a.gid AS gid_pfs, a.id_pfs, a.id_pop, a.id_pfp, a.n_pd, a.n_ui,
    b.gid AS gid_scala, b.id_scala,
    c.gid AS gid_giunto, c.id_giunto,
    d.gid AS gid_pd, d.id_pd,
    f.gid AS gid_cavoroute
    FROM %(schema)s.pfs a
    LEFT JOIN
    %(schema)s.scala b ON a.id_pfs=b.id_pfs
    LEFT JOIN
    %(schema)s.giunti c ON a.id_pfs=c.id_pfs
    LEFT JOIN
    %(schema)s.pd d ON a.id_pfs=d.id_pfs
    LEFT JOIN
    %(schema)s.cavoroute f ON a.id_pfs IN (f.from_p, f.to_p)
    WHERE a.id_pfs='%(id_oggetto)s'
    ) AS foo
    GROUP BY foo.id_pfs;"""

def recupero_relazioni_punti(connInfo, id_compare, chiave_compare, self):
    kvp = connInfo.split(" ")
    for kv in kvp:
        if kv.startswith("password"):
            thePassword = kv.split("=")[1][1:-1]
        elif kv.startswith("host"):
            theHost = kv.split("=")[1]
        elif kv.startswith("port"):
            thePort = kv.split("=")[1]
        elif kv.startswith("dbname"):
            theDbName = kv.split("=")[1][1:-1]
        elif kv.startswith("user"):
            theUser = kv.split("=")[1][1:-1]
        elif kv.startswith("table"):
            theTable_raw = kv.split("=")[1]
            theSchema = theTable_raw.split(".")[0][1:-1]
            theTable = theTable_raw.split(".")[1][1:-1]
    Utils.logMessage("ID del punto da controllare = " + str(id_compare))
    test_conn = None
    cur = None
    dest_dir = "dbname=%s host=%s port=%s user=%s password=%s" % (theDbName, theHost, thePort, theUser, thePassword)
    Utils.logMessage(dest_dir)
    try:
        test_conn = psycopg2.connect(dest_dir)
        cur = test_conn.cursor()
        
        query_compare = eval(QUERY_NAME[chiave_compare]) % {'schema': theSchema, 'id_oggetto': id_compare}
        cur.execute(query_compare)
        results = cur.fetchone()
        if (chiave_compare=='SCALA'):
            #id_giunti_figli = results[1].split(',') or None
            #Estraggo solo i numeri dalla stringa:
            id_giunti_figli = [int(s) for s in re.findall(r'\b\d+\b', results[1])]
            id_giunto_padre = [None]
        elif (chiave_compare=='GIUNTO'):
            id_giunti_figli = results[1] or None
            #Estraggo il campo giunto_padre per discernere cosi tra padri e figlio:
            id_giunto_padre = results[9] or None
        else:
            id_giunti_figli = results[1] or None
            id_giunto_padre = [None]
        id_scale_figli = results[2] or None #[2, 4, 5, 428, 1224]
        id_pd_padre = results[3] or None
        id_pfs_padre = results[4] or None
        n_cont = results[5] or None
        n_ui = results[6] or None
        n_giunti = results[7] or None
        gid_cavoroute = results[8] or None
        #Utils.logMessage(str(id_giunto_padre))
        return id_giunti_figli, id_scale_figli, id_pd_padre, id_pfs_padre, n_cont, n_ui, n_giunti, gid_cavoroute, id_giunto_padre
        
        cur.close()
    except NameError as err:
        self.dlg_compare.txtFeedback.setText(err.args[0])
        return 0;
    except psycopg2.Error, e:
        Utils.logMessage(e.pgcode + e.pgerror)
        self.dlg_compare.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_compare.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        self.dlg_compare.txtFeedback.setText('Connessioni analizzate con successo!')
    finally:
        if test_conn:
            test_conn.close()
