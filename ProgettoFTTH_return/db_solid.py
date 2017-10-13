
import pgRoutingLayer_utils as Utils
import os
from qgis.core import *
import psycopg2
import psycopg2.extras
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import db_cavoroute as db_cavoroute

def consolida_aree(self, connInfo, theSchema, dialog):
    Utils.logMessage(connInfo)
    test_conn = None
    gids_pfs_vuoti = list()
    gids_pfs_multi = list()
    gids_pfs_uimax = list()
    codice_errore = 0 #cioe' parto da una situazione SENZA errori
    aree_PFS = dict()
    aree_PFP = dict()
    gids_pfp_vuoti = list()
    gids_pfp_multi = list()
    gids_pfp_pdmax = list()
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_solid = test_conn.cursor()
        
        query_pfs = """SELECT pfs.*, COALESCE(c.n_giunti, 0) AS n_giunti FROM (
            SELECT a.gid AS gid_area, array_agg(b.gid) AS gid_punto, array_agg(b.id_pfs) AS ids_pfs, array_agg(b.id_pfp) AS ids_pfp, array_agg(b.id_pop) AS ids_pop, array_length(array_agg(b.gid), 1) AS n_pfs, array_agg(b.n_pd) AS n_pd, array_agg(b.n_ui) AS n_ui
            FROM %s.area_pfs a, %s.pfs b
            WHERE ST_Intersects(a.geom, b.geom)
            GROUP BY gid_area) AS pfs
            LEFT JOIN
        (SELECT id_pfs, count(*) AS n_giunti FROM %s.giunti GROUP BY id_pfs) c ON (c.id_pfs = ANY(pfs.ids_pfs) );""" % (theSchema, theSchema, theSchema)
        cur_solid.execute(query_pfs)
        for results_solid in cur_solid:
            gid_pfs_single = results_solid[0]
            n_pfs = results_solid[5]
            if (n_pfs>1):
                #critico: area che contiene piu di 1 punto PFS
                codice_errore = codice_errore + 1
                gids_pfs_multi.append(gid_pfs_single)
            elif (n_pfs==0):
                #critico: area che non contiene alcun punto PFS
                codice_errore = codice_errore + 100
                gids_pfs_vuoti.append(gid_pfs_single)
            else:
                #Compilo il dictionary delle aree che se tutto va bene riuso dopo, considerando tutto UNICO cosi come dovrebbe essere, cioe prendo il primo dato della lista:
                aree_PFS[gid_pfs_single] = dict()
                aree_PFS[gid_pfs_single]['gid'] = gid_pfs_single
                aree_PFS[gid_pfs_single]['id_areapfs'] = results_solid[2][0]
                aree_PFS[gid_pfs_single]['id_areapop'] = results_solid[4][0]
                aree_PFS[gid_pfs_single]['id_areapfp'] = results_solid[3][0]
                aree_PFS[gid_pfs_single]['n_pfs'] = results_solid[5]
                aree_PFS[gid_pfs_single]['n_pd'] = results_solid[6][0]
                aree_PFS[gid_pfs_single]['n_giunti'] = results_solid[8]
                aree_PFS[gid_pfs_single]['n_ui'] = results_solid[7][0]
                if (aree_PFS[gid_pfs_single]['n_ui'] > self.FROM_TO_RULES['PFS']['MAX_UI']):
                    gids_pfs_uimax.append(gid_pfs_single)
        
        if (codice_errore < 100 and codice_errore > 0): #area con tanti punti
            dialog.txtFeedback.setText("Aree PFS con piu' di 1 punto PFS (lista dei gid):\n" + str(gids_pfs_multi))
            return codice_errore
        elif (codice_errore >= 100): #area senza punti
            dialog.txtFeedback.setText("Aree PFS senza punti PFS (lista dei gid):\n" + str(gids_pfs_vuoti))
            return codice_errore
        else:
            #Nessun errore posso continuare e aggiornare l'area ciclando dentro il dictionary:
            #for gid_a_pfs in aree_PFS:
            for key,val in aree_PFS.items():
                query_update_pfs = "UPDATE %s.area_pfs SET id_areapfs='%s', id_areapop='%s', id_areapfp='%s', n_pfs=%i, n_pd=%i, n_giunti=%i, n_ui=%i WHERE gid=%i;" % (theSchema, val['id_areapfs'], val['id_areapop'], val['id_areapfp'], val['n_pfs'], val['n_pd'], val['n_giunti'], val['n_ui'], val['gid'])
                cur_solid.execute(query_update_pfs)
                #Utils.logMessage( val['id_areapop'] )
            test_conn.commit()
            dialog.txtFeedback.setText("Aree PFS aggiornate con successo")
            
        ############## PFP #################
        #Fatto questo passo a calcolare le aree PFP:
        query_pfp = """SELECT pfp.*, COALESCE(e.n_pfs, 0) AS n_pfs, COALESCE(d.n_pd, 0) AS n_pd, COALESCE(c.n_giunti, 0) AS n_giunti
            FROM (
            SELECT a.gid AS gid_area, array_agg(b.gid) AS gid_punto, array_agg(b.id_pfp) AS ids_pfp, array_agg(b.id_pop) AS ids_pop, array_length(array_agg(b.gid), 1) AS n_pfp, array_agg(b.n_ui) AS n_ui
            FROM %s.area_pfp a, %s.pfp b
            WHERE ST_Intersects(a.geom, b.geom)
            GROUP BY gid_area) AS pfp
            LEFT JOIN
            (SELECT id_pfp, count(*) AS n_pfs FROM %s.pfs GROUP BY id_pfp) e ON (e.id_pfp = ANY(pfp.ids_pfp) )
            LEFT JOIN
            (SELECT id_pfp, count(*) AS n_pd FROM %s.pd GROUP BY id_pfp) d ON (d.id_pfp = ANY(pfp.ids_pfp) )
            LEFT JOIN
        (SELECT id_pfp, count(*) AS n_giunti FROM %s.giunti GROUP BY id_pfp) c ON (c.id_pfp =     ANY(pfp.ids_pfp) );""" % (theSchema, theSchema, theSchema, theSchema, theSchema)
        cur_solid.execute(query_pfp)
        for results_solid in cur_solid:
            gid_pfp_single = results_solid[0]
            n_pfp = results_solid[4]
            if (n_pfp>1):
                #critico: area che contiene piu di 1 punto PFP
                codice_errore = codice_errore + 1000
                gids_pfp_multi.append(gid_pfp_single)
            elif (n_pfp==0):
                #critico: area che non contiene alcun punto PFP
                codice_errore = codice_errore + 10000
                gids_pfp_vuoti.append(gid_pfp_single)
            else:
                #Compilo il dictionary delle aree che se tutto va bene riuso dopo, considerando tutto UNICO cosi come dovrebbe essere, cioe prendo il primo dato della lista:
                aree_PFP[gid_pfp_single] = dict()
                aree_PFP[gid_pfp_single]['gid'] = gid_pfp_single
                aree_PFP[gid_pfp_single]['id_areapop'] = results_solid[3][0]
                aree_PFP[gid_pfp_single]['id_areapfp'] = results_solid[2][0]
                aree_PFP[gid_pfp_single]['n_pfp'] = results_solid[4]
                aree_PFP[gid_pfp_single]['n_pfs'] = results_solid[6]
                aree_PFP[gid_pfp_single]['n_pd'] = results_solid[7]
                aree_PFP[gid_pfp_single]['n_giunti'] = results_solid[8]
                aree_PFP[gid_pfp_single]['n_ui'] = results_solid[5][0]
                if (aree_PFP[gid_pfp_single]['n_pfs'] > self.FROM_TO_RULES['PFP']['MAX_CONT']):
                    gids_pfp_pdmax.append(gid_pfp_single)
                    
        if (codice_errore >= 1000 and codice_errore < 10000): #area con tanti punti
            dialog.txtFeedback.setText("Aree PFP con piu' di 1 punto PFP (lista dei gid):\n" + str(gids_pfp_multi))
            return codice_errore
        elif (codice_errore >= 10000): #area senza punti
            dialog.txtFeedback.setText("Aree PFP senza punti PFP (lista dei gid):\n" + str(gids_pfp_vuoti))
            return codice_errore
        else:
            #Nessun errore posso continuare e aggiornare l'area ciclando dentro il dictionary:
            #for gid_a_pfs in aree_PFP:
            for key,val in aree_PFP.items():
                query_update_pfp = "UPDATE %s.area_pfp SET id_areapop='%s', id_areapfp='%s', n_pfp=%i, n_pfs=%i, n_pd=%i, n_giunti=%i, n_ui=%i WHERE gid=%i;" % (theSchema, val['id_areapop'], val['id_areapfp'], val['n_pfp'], val['n_pfs'], val['n_pd'], val['n_giunti'], val['n_ui'], val['gid'])
                cur_solid.execute(query_update_pfp)
                #Utils.logMessage( val['id_areapop'] )
            test_conn.commit()
            dialog.txtFeedback.setText("Aree PFP aggiornate con successo")
            
        ############## FINALIZZO ##############
        #In ogni caso mando un messaggio di AVVISO nel caso le UI superino quelle consentite:
        if (len(gids_pfs_uimax)>0):
            dialog.txtFeedback.setText("Aree PFS aggiornate con successo, ma qualcuna supera le UI massime consentite (lista dei gid):\n" + str(gids_pfs_uimax))
            return -1
        elif (len(gids_pfp_pdmax)>0):
            dialog.txtFeedback.setText("Aree PFP aggiornate con successo, ma qualcuna supera il numero massimo di PD consentiti (lista dei gid):\n" + str(gids_pfp_pdmax))
            return -2
        else: #tutto dovrebbe essere andato bene per cui:
            dialog.txtFeedback.setText("Aree PFS e PFP aggiornate con successo")
            return 0
        
        return 0
        
        #test_conn.commit()
        cur_solid.close()
        
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        return 0
    else:
        Utils.logMessage('Consolidate le aree PFS e PFP con successo!')
        return 1
    finally:
        #if cur_solid:
        #    cur_solid.close()
        if test_conn is not None:
            test_conn.close()            

def popola_pozzetti(self, connInfo, theSchema, dialog):
    #popolo il layer pozzetti prendendo le geometrie da pd, pfs e pfp. Svuoto e riempio ogni volta:
    test_conn = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_pozzetti = test_conn.cursor()
        
        #Recupero variabili di progetto per il codice comune e id_pop:
        query = "SELECT cod_com, id_pop, srid FROM %s.variabili_progetto_return;" % (theSchema)
        cur_pozzetti.execute(query)
        results = cur_pozzetti.fetchone()
        cod_com = results[0]
        id_pop = results[1]
        srid = results[2]
        #Svuoto lasciando pero quelli inseriti manualmente dall'operatore:
        #query_pozzetti = "TRUNCATE %s.pozzetto;" % (theSchema)
        query_pozzetti = "DELETE FROM %s.pozzetto WHERE insert_type != 'manual';" % (theSchema)
        cur_pozzetti.execute(query_pozzetti)
        #Popolo prima dai PD:
        query_pozzetti_pd = "INSERT INTO %s.pozzetto (geom, id_pozzetto, id_pd, cod_belf, id_pop, pos_poz_n, pos_poz_e, cod_geom, cod_tipo, id_pfs, id_pfp, insert_type) SELECT geom, id_pd, id_pd, cod_com, id_pop, coord_n, coord_e, id_pd_num, '125x80', id_pfs, id_pfp, 'PD' FROM %s.pd;" % (theSchema, theSchema)
        cur_pozzetti.execute(query_pozzetti_pd)
        #Popolo dai PFS:
        query_pozzetti_pfs = "INSERT INTO %s.pozzetto (geom, id_pozzetto, cod_belf, id_pop, pos_poz_n, pos_poz_e, cod_geom, cod_tipo, id_pfs, id_pfp, insert_type) SELECT geom, id_pfs, cod_com, id_pop, coord_n, coord_e, id_pfs_num, '125x80', id_pfs, id_pfp, 'PFS' FROM %s.pfs;" % (theSchema, theSchema)
        cur_pozzetti.execute(query_pozzetti_pfs)
        #Popolo dai PFP:
        query_pozzetti_pfp = "INSERT INTO %s.pozzetto (geom, id_pozzetto, cod_belf, id_pop, pos_poz_n, pos_poz_e, cod_geom, cod_tipo, id_pfp, insert_type) SELECT geom, id_pfp, cod_com, id_pop, coord_n, coord_e, id_pfp_num, '125x80', id_pfp, 'PFP' FROM %s.pfp;" % (theSchema, theSchema)
        cur_pozzetti.execute(query_pozzetti_pfp)

        test_conn.commit()
        cur_pozzetti.close()
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        #dialog.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        #dialog.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        #self.dlg_solid.start_routing_btn.setEnabled(False); #inizializzazione avvenuta con successo
        #self.dlg_solid.chk_start.setChecked(True);
        Utils.logMessage("Creazione pozzetti effettuata con successo")
        return 1
    finally:
        #if cur_pozzetti:
        #    cur_pozzetti.close()
        if test_conn is not None:
            test_conn.close()

def calcola_fibre(self, connInfo, theSchema, epsg_srid):
    Utils.logMessage(connInfo)
    self.dlg_solid.txtFeedback.setText("Elaborazione in corso NON chiudere il programma...")
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        return_code = db_cavoroute.recupero_ui_cavo(dest_dir, self, theSchema, epsg_srid)
    except SystemError, e:
        Utils.logMessage(e)
        return 0
        #QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Routing non eseguito!')
        #self.dlg.txtFeedback.setText('Errore di sistema! Routing non eseguito!')
    else:
        #Aggiorno la maschera e i pulsanti da abilitare/disabilitare:
        inizializza_gui(self, connInfo, theSchema)
        return return_code
        #QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing avvenuto con successo!')

def calcola_route(self, connInfo, theSchema):
    Utils.logMessage(connInfo)
    self.dlg_solid.txtFeedback.setText("Elaborazione in corso NON chiudere il programma...")
    test_conn = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        #Parto subito con l'update della tabella cavoroute:
        cur = None        
        test_conn = psycopg2.connect(dest_dir)
        cur = test_conn.cursor()
        
        #Ripulisco la tavola cosi' la posso aggiornare senza problemi tutte le volte che voglio senza dover resettare tutto ogni volta. Al PRIMO GIRO assegno a cavoroute le N_UI REALI prendendole direttamente dai pti_rete:
        #Da Mail di Gatti del 22 maggio 2017 e successive: abilitare tutte le connessioni Giunto-Giunto anche se sono dei PTA. Ho dunque aggiunto 2 QUERY che considerano PTA-PTA e PTA-GI sempre prendendo un NET_TYPE=GI_GI
        query_update_raw = """UPDATE %(schema)s.cavoroute SET id_cavo=Null, fibre_coun=Null, n_ui=Null, from_p=Null, to_p=Null, length_m=Null, temp_cavo_label=Null;
        UPDATE %(schema)s.cavoroute SET id_cavo=lpad(gid::text, 13, '0');
        UPDATE %(schema)s.cavoroute SET length_m=ST_Length(geom);
        UPDATE %(schema)s.cavoroute SET length_m=0 WHERE geom IS NULL;
        --SCALA_SCALA
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.id_scala_f, to_p=foo.id_scala FROM
            (SELECT a.gid, c.n_ui, c.id_scala AS id_scala_f, d.id_scala FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.scala c ON (c.gid = ANY (b.gid_scala))
            LEFT JOIN %(schema)s.scala d ON (d.gid = ANY (e.gid_scala))
            WHERE a.net_type='%(SCALA_SCALA)s') AS foo WHERE cavoroute.gid=foo.gid;
        --SCALA_PTA
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.id_scala, to_p=foo.id_giunto FROM
            (SELECT a.gid, c.n_ui, c.id_scala, d.id_giunto FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.scala c ON (c.gid = ANY (b.gid_scala))
            LEFT JOIN %(schema)s.giunti d ON (d.gid = ANY (e.gid_pta))
            WHERE a.net_type='%(SCALA_PTA)s') AS foo WHERE cavoroute.gid=foo.gid;
        --SCALA_GIUNTO
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.id_scala, to_p=foo.id_giunto FROM
            (SELECT a.gid, c.n_ui, c.id_scala, d.id_giunto FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.scala c ON (c.gid = ANY (b.gid_scala))
            LEFT JOIN %(schema)s.giunti d ON (d.gid = ANY (e.gid_giunto))
            WHERE a.net_type='%(SCALA_GIUNTO)s') AS foo WHERE cavoroute.gid=foo.gid;
        --SCALA_PD
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.id_scala, to_p=foo.id_pd FROM
            (SELECT a.gid, c.n_ui, c.id_scala, d.id_pd FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.scala c ON (c.gid = ANY (b.gid_scala))
            LEFT JOIN %(schema)s.pd d ON (d.gid = ANY (e.gid_pd))
            WHERE a.net_type='%(SCALA_PD)s') AS foo WHERE cavoroute.gid=foo.gid;
        --SCALA_PFS
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.id_scala, to_p=foo.id_pfs FROM
            (SELECT a.gid, c.n_ui, c.id_scala, d.id_pfs FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.scala c ON (c.gid = ANY (b.gid_scala))
            LEFT JOIN %(schema)s.pfs d ON (d.gid = ANY (e.gid_pfs))
            WHERE a.net_type='%(SCALA_PFS)s') AS foo WHERE cavoroute.gid=foo.gid;
        --PTA_PD
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.id_giunto, to_p=foo.id_pd FROM
            (SELECT a.gid, c.n_ui, c.id_giunto, d.id_pd FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.giunti c ON (c.gid = ANY (b.gid_pta))
            LEFT JOIN %(schema)s.pd d ON (d.gid = ANY (e.gid_pd))
            WHERE a.net_type='%(PTA_PD)s') AS foo WHERE cavoroute.gid=foo.gid;
        --PTA_PTA
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.giunto_f, to_p=foo.id_giunto FROM
            (SELECT a.gid, c.n_ui, c.id_giunto AS giunto_f, d.id_giunto FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.giunti c ON (c.gid = ANY (b.gid_pta))
            LEFT JOIN %(schema)s.giunti d ON (d.gid = ANY (e.gid_pta))
            WHERE a.net_type='%(PTA_PTA)s' AND upper(c.tipo_giunt)='PTA' AND upper(d.tipo_giunt)='PTA') AS foo WHERE cavoroute.gid=foo.gid;
        --PTA_GIUNTO
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.giunto_f, to_p=foo.id_giunto FROM
            (SELECT a.gid, c.n_ui, c.id_giunto AS giunto_f, d.id_giunto FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.giunti c ON (c.gid = ANY (b.gid_pta))
            LEFT JOIN %(schema)s.giunti d ON (d.gid = ANY (e.gid_giunto))
            WHERE a.net_type='%(PTA_GIUNTO)s' AND upper(c.tipo_giunt)='PTA' AND upper(d.tipo_giunt)!='PTA') AS foo WHERE cavoroute.gid=foo.gid;
        --GIUNTO_GIUNTO
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.giunto_f, to_p=foo.id_giunto FROM
            (SELECT a.gid, c.n_ui, c.id_giunto AS giunto_f, d.id_giunto FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.giunti c ON (c.gid = ANY (b.gid_giunto))
            LEFT JOIN %(schema)s.giunti d ON (d.gid = ANY (e.gid_giunto))
            WHERE a.net_type='%(GIUNTO_GIUNTO)s' AND upper(c.tipo_giunt)!='PTA' AND upper(d.tipo_giunt)!='PTA') AS foo WHERE cavoroute.gid=foo.gid;
        --GIUNTO_PD
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.id_giunto, to_p=foo.id_pd FROM
            (SELECT a.gid, c.n_ui, c.id_giunto, d.id_pd FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.giunti c ON (c.gid = ANY (b.gid_giunto))
            LEFT JOIN %(schema)s.pd d ON (d.gid = ANY (e.gid_pd))
            WHERE a.net_type='%(GIUNTO_PD)s') AS foo WHERE cavoroute.gid=foo.gid;
        --PD_PD
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.id_pd_f, to_p=foo.id_pd FROM
            (SELECT a.gid, c.n_ui, c.id_pd AS id_pd_f, d.id_pd FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.pd c ON (c.gid = ANY (b.gid_pd))
            LEFT JOIN %(schema)s.pd d ON (d.gid = ANY (e.gid_pd))
            WHERE a.net_type='%(PD_PD)s') AS foo WHERE cavoroute.gid=foo.gid;
        --PD_PFS
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.id_pd, to_p=foo.id_pfs FROM
            (SELECT a.gid, c.n_ui, c.id_pd, d.id_pfs FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.pd c ON (c.gid = ANY (b.gid_pd))
            LEFT JOIN %(schema)s.pfs d ON (d.gid = ANY (e.gid_pfs))
            WHERE a.net_type='%(PD_PFS)s') AS foo WHERE cavoroute.gid=foo.gid;
        --PFS_PFP
        UPDATE %(schema)s.cavoroute SET n_ui=foo.n_ui, from_p=foo.id_pfs, to_p=foo.id_pfp FROM
            (SELECT a.gid, c.n_ui, c.id_pfs, d.id_pfp FROM %(schema)s.cavoroute a
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array b ON (b.id_pgr=a.source)
            LEFT JOIN %(schema)s.pgrvertices_netpoints_array e ON (e.id_pgr=a.target)
            LEFT JOIN %(schema)s.pfs c ON (c.gid = ANY (b.gid_pfs))
            LEFT JOIN %(schema)s.pfp d ON (d.gid = ANY (e.gid_pfp))
        WHERE a.net_type='%(PFS_PFP)s') AS foo WHERE cavoroute.gid=foo.gid;"""
        
        query_update = query_update_raw % {'schema': theSchema, 'SCALA_PTA': self.NET_TYPE['SCALA_PTA'], 'SCALA_GIUNTO': self.NET_TYPE['SCALA_GIUNTO'], 'SCALA_PD': self.NET_TYPE['SCALA_PD'], 'SCALA_PFS': self.NET_TYPE['SCALA_PFS'], 'PTA_PTA': self.NET_TYPE['PTA_PTA'], 'PTA_GIUNTO': self.NET_TYPE['PTA_GIUNTO'], 'GIUNTO_GIUNTO': self.NET_TYPE['GIUNTO_GIUNTO'], 'GIUNTO_PD': self.NET_TYPE['GIUNTO_PD'], 'PTA_PD': self.NET_TYPE['PTA_PD'], 'PD_PFS': self.NET_TYPE['PD_PFS'], 'PFS_PFP': self.NET_TYPE['PFS_PFP'], 'SCALA_SCALA': self.NET_TYPE['SCALA_SCALA'], 'PD_PD' : self.NET_TYPE['PD_PD']}
        cur.execute(query_update)
        #test_conn.commit()
        
        '''
        #Poi aggiorno le fibre: sfrutto la stessa query modificando i parametri:
        query_fibre_drop_raw = """UPDATE %(schema)s.cavoroute SET fibre_coun = 
            CASE
            WHEN n_ui-%(n_ui_limit)i<=%(f4)i THEN COALESCE(fibre_coun,0)+4
            WHEN n_ui-%(n_ui_limit)i<=%(f12)i THEN COALESCE(fibre_coun,0)+12
            WHEN n_ui-%(n_ui_limit)i<=%(f24)i THEN COALESCE(fibre_coun,0)+24
            WHEN n_ui-%(n_ui_limit)i<=%(f48)i THEN COALESCE(fibre_coun,0)+48
            WHEN n_ui-%(n_ui_limit)i>%(f48)i THEN COALESCE(fibre_coun,0)+48
            END
            WHERE net_type ~* 'Contatori*' AND n_ui>%(n_ui_limit)i;"""
        query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': 0, 'f4': self.FIBRE_CAVO['PD']['F_4'], 'f12': self.FIBRE_CAVO['PD']['F_12'], 'f24': self.FIBRE_CAVO['PD']['F_24'], 'f48': self.FIBRE_CAVO['PD']['F_48']}
        cur.execute(query_fibre_drop)
        #Secondo giro:
        query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': self.FIBRE_CAVO['PD']['F_48'], 'f4': self.FIBRE_CAVO['PD']['F_4'], 'f12': self.FIBRE_CAVO['PD']['F_12'], 'f24': self.FIBRE_CAVO['PD']['F_24'], 'f48': self.FIBRE_CAVO['PD']['F_48']}
        cur.execute(query_fibre_drop)
        #Terzo giro:
        query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': self.FIBRE_CAVO['PD']['F_48']*2, 'f4': self.FIBRE_CAVO['PD']['F_4'], 'f12': self.FIBRE_CAVO['PD']['F_12'], 'f24': self.FIBRE_CAVO['PD']['F_24'], 'f48': self.FIBRE_CAVO['PD']['F_48']}
        cur.execute(query_fibre_drop)
        '''
        
        #AGGIORNO LE FIBRE:
        #il campo temp_cavo_label e' un'etichetta provvisoria per il cavoroute: verra poi utilizzato da cavoroute_label per tenere conto delle fibre-metri
        for key, value in sorted(self.FIBRE_CAVO.items()):
          query_fibre_drop_raw = """UPDATE %(schema)s.cavoroute SET fibre_coun = 
            CASE
            WHEN n_ui-%(n_ui_limit)i<=%(f4)i AND n_ui-%(n_ui_limit)i>0 THEN COALESCE(fibre_coun,0)+4
            WHEN n_ui-%(n_ui_limit)i<=%(f12)i AND n_ui-%(n_ui_limit)i>0 THEN COALESCE(fibre_coun,0)+12
            WHEN n_ui-%(n_ui_limit)i<=%(f24)i AND n_ui-%(n_ui_limit)i>0 THEN COALESCE(fibre_coun,0)+24
            WHEN n_ui-%(n_ui_limit)i<=%(f48)i AND n_ui-%(n_ui_limit)i>0 THEN COALESCE(fibre_coun,0)+48
            WHEN n_ui-%(n_ui_limit)i<=%(f72)i AND n_ui-%(n_ui_limit)i>0 THEN COALESCE(fibre_coun,0)+72
            WHEN n_ui-%(n_ui_limit)i<=%(f96)i AND n_ui-%(n_ui_limit)i>0 THEN COALESCE(fibre_coun,0)+96
            WHEN n_ui-%(n_ui_limit)i<=%(f144)i AND n_ui-%(n_ui_limit)i>0 THEN COALESCE(fibre_coun,0)+144
            WHEN n_ui-%(n_ui_limit)i<=%(f192)i AND n_ui-%(n_ui_limit)i>0 THEN COALESCE(fibre_coun,0)+196
            WHEN n_ui-%(n_ui_limit)i>%(max_fibra)i THEN COALESCE(fibre_coun,0)+%(max_fibra_coun)i
            END
            , temp_cavo_label =
            CASE
            WHEN n_ui-%(n_ui_limit)i<=%(f4)i AND n_ui-%(n_ui_limit)i>0 THEN array_append(temp_cavo_label, ('1mc 4 # ' || length_m::integer || 'm')::character varying)
            WHEN n_ui-%(n_ui_limit)i<=%(f12)i AND n_ui-%(n_ui_limit)i>0 THEN array_append(temp_cavo_label, ('1mc 12 # ' || length_m::integer || 'm')::character varying)
            WHEN n_ui-%(n_ui_limit)i<=%(f24)i AND n_ui-%(n_ui_limit)i>0 THEN array_append(temp_cavo_label, ('1mc 24 # ' || length_m::integer || 'm')::character varying)
            WHEN n_ui-%(n_ui_limit)i<=%(f48)i AND n_ui-%(n_ui_limit)i>0 THEN array_append(temp_cavo_label, ('1mc 48 # ' || length_m::integer || 'm')::character varying)
            WHEN n_ui-%(n_ui_limit)i<=%(f72)i AND n_ui-%(n_ui_limit)i>0 THEN array_append(temp_cavo_label, ('1mc 72 # ' || length_m::integer || 'm')::character varying)
            WHEN n_ui-%(n_ui_limit)i<=%(f96)i AND n_ui-%(n_ui_limit)i>0 THEN array_append(temp_cavo_label, ('1mc 96 # ' || length_m::integer || 'm')::character varying)
            WHEN n_ui-%(n_ui_limit)i<=%(f144)i AND n_ui-%(n_ui_limit)i>0 THEN array_append(temp_cavo_label, ('1mc 144 # ' || length_m::integer || 'm')::character varying)
            WHEN n_ui-%(n_ui_limit)i<=%(f192)i AND n_ui-%(n_ui_limit)i>0 THEN array_append(temp_cavo_label, ('1mc 196 # ' || length_m::integer || 'm')::character varying)
            WHEN n_ui-%(n_ui_limit)i>%(max_fibra)i THEN array_append(temp_cavo_label, ('1mc %(max_fibra_coun)i # ' || length_m::integer || 'm')::character varying)
            END
          WHERE net_type ~* '%(tipo_net_type)s' AND n_ui>%(n_ui_limit)i;"""
          
          if ('F_192' in value) and (value['F_192'] > 0):
             max_fibra = value['F_192']
             max_campo = 'f_192'
          elif ('F_144' in value) and (value['F_144'] > 0):
              max_fibra = value['F_144']
              max_campo = 'f_144'
          elif ('F_96' in value) and (value['F_96'] > 0):
              max_fibra = value['F_96']
              max_campo = 'f_96'
          elif ('F_72' in value) and (value['F_72'] > 0):
              max_fibra = value['F_72']
              max_campo = 'f_72'
          elif ('F_48' in value) and (value['F_48'] > 0):
              max_fibra = value['F_48']
              max_campo = 'f_48'
          elif ('F_24' in value) and (value['F_24'] > 0):
              max_fibra = value['F_24']
              max_campo = 'f_24'
          elif ('F_12' in value) and (value['F_12'] > 0):
              max_fibra = value['F_12']
              max_campo = 'f_12'
          elif ('F_4' in value) and (value['F_4'] > 0):
              max_fibra = value['F_4']
              max_campo = 'f_4'
          else:
              max_fibra = 9999
              max_campo = 'f_192'
        
          max_fibra_coun = int(max_campo[2:])
          
          if key.find("SCALA") > -1: #faccio fare piu' giri. Per essere precisi dovrei fare un while fino ad esaurimento delle n_ui, ma in questo caso non le so, sono sul DB...
            query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': 0, 'f4': value['F_4'], 'f12': value['F_12'], 'f24': value['F_24'], 'f48': value['F_48'], 'f72': value['F_72'], 'f96': value['F_96'], 'f144': value['F_144'], 'f192': value['F_192'], 'tipo_net_type': self.NET_TYPE[key], 'max_fibra': max_fibra, 'max_fibra_coun': max_fibra_coun}
            #Utils.logMessage(query_fibre_drop)
            cur.execute(query_fibre_drop)
            #Secondo giro:
            query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': max_fibra, 'f4': value['F_4'], 'f12': value['F_12'], 'f24': value['F_24'], 'f48': value['F_48'], 'f72': value['F_72'], 'f96': value['F_96'], 'f144': value['F_144'], 'f192': value['F_192'], 'tipo_net_type': self.NET_TYPE[key], 'max_fibra': max_fibra, 'max_fibra_coun': max_fibra_coun}
            #Utils.logMessage(query_fibre_drop)
            cur.execute(query_fibre_drop)
            #Terzo giro:
            query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': max_fibra*2, 'f4': value['F_4'], 'f12': value['F_12'], 'f24': value['F_24'], 'f48': value['F_48'], 'f72': value['F_72'], 'f96': value['F_96'], 'f144': value['F_144'], 'f192': value['F_192'], 'tipo_net_type': self.NET_TYPE[key], 'max_fibra': max_fibra, 'max_fibra_coun': max_fibra_coun}
            cur.execute(query_fibre_drop)
          elif key.find("PFS_PFP") > -1: #Fibre per la rete da PFS a PFP - numero costante:
            query_fibre_pfspfp_raw = """UPDATE %(schema)s.cavoroute SET fibre_coun = 96
            ,temp_cavo_label = array_append(temp_cavo_label, ('1mc 96 # ' || length_m::integer || 'm')::character varying)
            WHERE net_type = '%(tipo_net_type)s' AND n_ui>0;"""
            query_fibre_pfspfp = query_fibre_pfspfp_raw % {'schema': theSchema, 'tipo_net_type': self.NET_TYPE[key]}
            cur.execute(query_fibre_pfspfp)
          else: #assegno tutte le fibre al primo giro!
            query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': 0, 'f4': value['F_4'], 'f12': value['F_12'], 'f24': value['F_24'], 'f48': value['F_48'], 'f72': value['F_72'], 'f96': value['F_96'], 'f144': value['F_144'], 'f192': value['F_192'], 'tipo_net_type': self.NET_TYPE[key], 'max_fibra': max_fibra, 'max_fibra_coun': max_fibra_coun}
            cur.execute(query_fibre_drop)
        
        '''
        #Fibre per la rete da giunto in poi:
        query_fibre_drop_raw = """UPDATE %(schema)s.cavoroute SET fibre_coun = 
            CASE
            WHEN n_ui-%(n_ui_limit)i<=%(f24)i THEN COALESCE(fibre_coun,0)+24
            WHEN n_ui-%(n_ui_limit)i<=%(f48)i THEN COALESCE(fibre_coun,0)+48
            WHEN n_ui-%(n_ui_limit)i<=%(f72)i THEN COALESCE(fibre_coun,0)+72
            WHEN n_ui-%(n_ui_limit)i<=%(f96)i THEN COALESCE(fibre_coun,0)+96
            WHEN n_ui-%(n_ui_limit)i<=%(f144)i THEN COALESCE(fibre_coun,0)+144
            WHEN n_ui-%(n_ui_limit)i>%(f144)i THEN COALESCE(fibre_coun,0)+144
            END
            WHERE net_type !~* 'Contatori*' AND n_ui>%(n_ui_limit)i;"""
        query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': 0, 'f24': self.FIBRE_CAVO['PFS']['F_24'], 'f48': self.FIBRE_CAVO['PFS']['F_48'], 'f72': self.FIBRE_CAVO['PFS']['F_72'], 'f96': self.FIBRE_CAVO['PFS']['F_96'], 'f144': self.FIBRE_CAVO['PFS']['F_144']}
        cur.execute(query_fibre_drop)
        #DA MAIL DI GATTI DEL 4 NOVEMBRE 2016: su questa rete, detta anche "rete di drop", NON ciclo piu' ma assegno tutte le fibre al primo giro!
        '''
        '''
        #Secondo giro:
        query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': self.FIBRE_CAVO['PFS']['F_144'], 'f24': self.FIBRE_CAVO['PFS']['F_24'], 'f48': self.FIBRE_CAVO['PFS']['F_48'], 'f72': self.FIBRE_CAVO['PFS']['F_72'], 'f96': self.FIBRE_CAVO['PFS']['F_96'], 'f144': self.FIBRE_CAVO['PFS']['F_144']}
        cur.execute(query_fibre_drop)
        #Terzo giro:
        query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': self.FIBRE_CAVO['PFS']['F_144']*2, 'f24': self.FIBRE_CAVO['PFS']['F_24'], 'f48': self.FIBRE_CAVO['PFS']['F_48'], 'f72': self.FIBRE_CAVO['PFS']['F_72'], 'f96': self.FIBRE_CAVO['PFS']['F_96'], 'f144': self.FIBRE_CAVO['PFS']['F_144']}
        cur.execute(query_fibre_drop)
        #Quarto giro:
        query_fibre_drop = query_fibre_drop_raw % {'schema': theSchema, 'n_ui_limit': self.FIBRE_CAVO['PFS']['F_144']*3, 'f24': self.FIBRE_CAVO['PFS']['F_24'], 'f48': self.FIBRE_CAVO['PFS']['F_48'], 'f72': self.FIBRE_CAVO['PFS']['F_72'], 'f96': self.FIBRE_CAVO['PFS']['F_96'], 'f144': self.FIBRE_CAVO['PFS']['F_144']}
        cur.execute(query_fibre_drop)
        '''
        
        '''
        #Fibre per la rete da PFS a PFP - numero costante:
        query_fibre_pfspfp_raw = """UPDATE %(schema)s.cavoroute SET fibre_coun = 96 WHERE net_type = '%(tipo_net_type)s' AND n_ui>0;"""
        query_fibre_pfspfp = query_fibre_pfspfp_raw % {'schema': theSchema, 'tipo_net_type': self.NET_TYPE['PFS_PFP']}
        cur.execute(query_fibre_pfspfp)
        '''
        
        #Aggiorno il campo num_scorte in base alle specifiche datemi:
        query_update_scorte = "UPDATE %s.cavoroute SET num_scorte = 1 WHERE net_type ~* 'Contatori*'; UPDATE %s.cavoroute SET num_scorte = 2 WHERE net_type !~* 'Contatori*';" % (theSchema, theSchema)
        #cur.execute(query_update_scorte)
        #ma dove lo creo questo campo????
        
        #Aggiorno gli altri milioni di campi che mi sono stati aggiunti solo alla fine...
        '''
        query_update_allafine_raw = """UPDATE %(schema)s.cavoroute SET n_gnz_un = CASE WHEN net_type IN ('Contatori-PTA', 'Contatori-giunto', 'Contatori-PD') THEN 0 ELSE 1 END;
            UPDATE %(schema)s.cavoroute SET n_gnz_tot = n_gnz_un * n_ui;
            UPDATE %(schema)s.cavoroute SET n_gnz_min8 = CASE WHEN n_gnz_tot!=0 THEN 1 ELSE 0 END;
            UPDATE %(schema)s.cavoroute SET n_gnz_mag8 = CASE WHEN (n_gnz_tot<=8 OR n_gnz_min8=0) THEN 0 ELSE 8 END;
            UPDATE %(schema)s.cavoroute SET n_gnz_min12 = CASE WHEN n_gnz_tot!=0 THEN 1 ELSE 0 END;
            UPDATE %(schema)s.cavoroute SET n_gnz_mag12 = CASE WHEN (n_gnz_tot<128 OR n_gnz_min12=0) THEN 0 ELSE 8 END;
            UPDATE %(schema)s.cavoroute SET teste_cavo = CASE WHEN net_type IN ('Contatori-giunto', 'Contatori-PD') THEN 0 ELSE 2 END;
        UPDATE %(schema)s.cavoroute SET scorta = CASE WHEN length_m=0 THEN 15 WHEN length_m<=10 THEN 3 WHEN length_m<=20 THEN 5 WHEN length_m<=50 THEN 10 WHEN length_m<=100 THEN 15 ELSE 20 END;"""
        '''
        #Secondo le ultime indicazioni - MAIL di GATTI del 31 Gen 2017 h12.03:
        query_update_allafine_raw = """UPDATE %(schema)s.cavoroute SET n_gnz_un = CASE WHEN net_type IN ('Contatori-PTA', 'Contatori-giunto', 'Contatori-PD') THEN 0 ELSE 1 END;
            UPDATE %(schema)s.cavoroute SET n_gnz_tot = n_gnz_un * n_ui;
            UPDATE %(schema)s.cavoroute SET n_gnz_min8 = CASE WHEN n_gnz_tot!=0 THEN 1 ELSE 0 END;
            UPDATE %(schema)s.cavoroute SET n_gnz_mag8 = CASE WHEN (n_gnz_tot<=8 OR n_gnz_min8=0) THEN 0 ELSE 8 END;
            UPDATE %(schema)s.cavoroute SET n_gnz_min12 = CASE WHEN n_gnz_tot!=0 THEN 1 ELSE 0 END;
            UPDATE %(schema)s.cavoroute SET n_gnz_mag12 = CASE WHEN (n_gnz_tot<128 OR n_gnz_min12=0) THEN 0 ELSE 8 END;
            UPDATE %(schema)s.cavoroute SET teste_cavo = CASE WHEN net_type IN ('Contatori-giunto', 'Contatori-PD') THEN 0 ELSE 2 END;
        UPDATE %(schema)s.cavoroute SET scorta = CASE WHEN upper(net_type) ~* 'CONTATOR*' THEN 1 ELSE 2 END;
        UPDATE %(schema)s.cavoroute SET lung_ott =  length_m + ( (scorta*15) + ((length_m/250) * 30));"""
        query_update_allafine = query_update_allafine_raw % {'schema': theSchema}
        cur.execute(query_update_allafine)
        
        #Secondo le ultimissime indicazioni ricalcolo le N_UI - MAIL di GATTI del 03 Feb 2017 h10.14:
        '''query_update_ui_raw = """UPDATE %(schema)s.cavoroute SET n_ui =
        CASE
        WHEN upper(net_type) ~* 'CONTATOR*' THEN n_ui+2
        WHEN upper(net_type) ~* 'PTA*' THEN n_ui+2
        WHEN upper(net_type) ~* 'GIUNTI*' THEN n_ui*1.5
        WHEN upper(net_type) ~* 'PD*' THEN n_ui*1.5
        END;"""
        query_update_ui = query_update_ui_raw % {'schema': theSchema}
        cur.execute(query_update_ui)'''
        #ULTIME NEWS: mail di Gatti del 19 aprile 2017: ricalcolo n_ui:
        query_update_ui_raw = """UPDATE %(schema)s.cavoroute SET n_ui_reali = n_ui;
        UPDATE %(schema)s.cavoroute SET n_ui =
        CASE
        WHEN upper(net_type) ~* 'CONTATOR*' THEN n_ui_reali+2
        WHEN upper(net_type) ~* 'PTA*' THEN n_ui_reali+2
        WHEN upper(net_type) ~* 'PD*' THEN n_ui_reali*1.5
        WHEN upper(net_type) ~* 'PFS*' THEN n_ui_reali*1.5
        END;
        UPDATE %(schema)s.cavoroute SET n_ui = cavoroute.n_ui_reali+(b.n_cont*2) FROM %(schema)s.giunti b
        WHERE cavoroute.from_p = b.id_giunto AND upper(cavoroute.net_type) ~* 'GIUNTI*';"""
        query_update_ui = query_update_ui_raw % {'schema': theSchema}
        cur.execute(query_update_ui)
        
        #Indicazioni di Gatti da mail del 07 Mar 2017: calcolo del campo terminaz
        query_update_terminaz_raw = """UPDATE %(schema)s.cavoroute SET terminaz =
        CASE
        WHEN n_ui<=6 THEN 8
        WHEN n_ui>=7 AND n_ui<=12 THEN 16
        WHEN n_ui>=13 AND n_ui<=20 THEN 24
        WHEN n_ui>=21 AND n_ui<=36 THEN 36
        WHEN n_ui>=37 AND n_ui<=44 THEN 48
        WHEN n_ui>=45 AND n_ui<=96 THEN 96
        ELSE NULL
        END;"""
        query_update_terminaz = query_update_terminaz_raw % {'schema': theSchema}
        cur.execute(query_update_terminaz)
        
        #Indicazioni FLASH: creazione di un layer cavoroute per etichettare le rotte. Lancio uno script sql esterno - SCRIPT ANCORA IN TEST!!
        try:
            #before check if table already exist:
            query_exist = """SELECT EXISTS (
                SELECT 1
                FROM   information_schema.tables 
                WHERE  table_schema = '%s'
                AND    table_name = 'cavoroute_labels'
                );
            """ % (theSchema)
            cur.execute(query_exist)
            if cur.fetchone()[0]==True:
                #la tabella esiste gia'. La elimino per ricrearla
                query_drop = "DROP TABLE %s.cavoroute_labels" % (theSchema)
                cur.execute(query_drop)
                test_conn.commit()
            query = "SET search_path = %s, public, pg_catalog;" % (theSchema)
            cur.execute(query)
            sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_cavoroute_per_label.sql'
            cur.execute(open(sql_file, "r").read())
            test_conn.commit()
        except psycopg2.Error, e:
            Utils.logMessage(e.pgerror)
            test_conn.rollback()
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Errore nel creare le labels per cavoroute. Si proseguira comunque con il resto della procedura')
            Utils.logMessage('Errore nel creare le labels per cavoroute. Si proseguira comunque con il resto della procedura')
        except SystemError, e:
            test_conn.rollback()
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Errore nel creare le labels per cavoroute. Si proseguira comunque con il resto della procedura')
            Utils.logMessage('Errore nel creare le labels per cavoroute. Si proseguira comunque con il resto della procedura')
        else:
            #Carico il layer sulla mappa:
            uri = "%s key=id table=\"%s\".\"cavoroute_labels\" (geom) sql=" % (dest_dir, theSchema)
            layer = QgsVectorLayer(uri, "cavoroute_labels", "postgres")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            layer.loadNamedStyle(os.getenv("HOME")+'/.qgis2/python/plugins/ProgettoFTTH_return/qml_base/cavoroute_labels.qml')
        
        #Tolgo i valori NULL dall'array tipo_posa di cavoroute:
        query_drop_null = "UPDATE %s.cavoroute SET tipo_posa = array_remove(tipo_posa, NULL);" % (theSchema)
        try:
            cur.execute(query_drop_null)
            test_conn.commit()
        except psycopg2.Error, e:
            Utils.logMessage(e.pgerror)
            test_conn.rollback()
            message = 'Errore nel rimuovere i valori NULL dal campo tipo_posa di cavoroute. Si proseguira comunque con il resto della procedura.'
            QMessageBox.warning(self.dock, self.dock.windowTitle(), message)
            Utils.logMessage(message)
        except SystemError, e:
            test_conn.rollback()
            message = 'Errore nel rimuovere i valori NULL dal campo tipo_posa di cavoroute. Si proseguira comunque con il resto della procedura.'
            QMessageBox.warning(self.dock, self.dock.windowTitle(), message)
            Utils.logMessage(message)
        
        #Aggiorno id del cavoroute -- ATTENZIONE!! Devo prelevare il COD_POP impostato a livello di progetto!!
        #query_update_id = "UPDATE %s.cavoroute SET id_cavo = '%s' || '%s' || ('08'::text||lpad(gid::text, 6, '0'));" % (theSchema, self.COD_POP, theSchema.replace('lotto_', ''))
        #cur.execute(query_update_id)
        
        #Infine CANCELLO i CAMPI da CAVO considerati INUTILI e che eventualmente ripristinero' ad una nuova sessione di routing:
        try:
            query_drop_column = """ALTER TABLE %s.cavo DROP COLUMN source;
            ALTER TABLE %s.cavo DROP COLUMN target;
            ALTER TABLE %s.cavo DROP COLUMN n_ui;""" % (theSchema, theSchema, theSchema)
            #cur.execute(query_drop_column)
        except:
            Utils.logMessage("Cavoroute probabilmente gia' calcolato. E' stato comunque ricalcolato con successo")
        
        cur.close()
        
    except psycopg2.Error, e:
        test_conn.rollback()
        test_conn.close()
        Utils.logMessage(e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        test_conn.rollback()
        test_conn.close()
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        test_conn.commit()
        #if test_conn is not None:
        #    test_conn.close()
        Utils.logMessage('Calcolo cavoroute realizzato con successo!')
        self.dlg_solid.txtFeedback.setText('Calcolo cavoroute realizzato con successo!')
        return 1
    finally:
        if test_conn is not None:
            test_conn.close()

def check_grouping(self, connInfo, theSchema):
    test_conn = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_check = test_conn.cursor()
        
        query_count = """SELECT 
            (SELECT count(b.gid) FROM %s.scala b, %s.area_pfp c WHERE id_pfs IS NULL AND ST_Intersects(b.geom, c.geom))
            +
            (SELECT count(b.gid) FROM %s.giunti b, %s.area_pfp c WHERE id_pfs IS NULL AND ST_Intersects(b.geom, c.geom))
            +
            (SELECT count(b.gid) FROM %s.pd b, %s.area_pfp c WHERE id_pfs IS NULL AND ST_Intersects(b.geom, c.geom))
            +
            (SELECT count(b.gid) FROM %s.pfs b, %s.area_pfp c WHERE id_pfp IS NULL AND ST_Intersects(b.geom, c.geom));""" % (theSchema, theSchema, theSchema, theSchema, theSchema, theSchema, theSchema, theSchema)
        cur_check.execute(query_count)
        results_check = cur_check.fetchone()
        count_check = results_check[0]
        if (count_check>0):
            #Qualche punto non e' associato: restituisco elenco dei GID non associati:        
            query_check = """SELECT 'Contatori' AS tipo_punto, array_agg(b.gid) AS non_associati FROM %s.scala b, %s.area_pfp c WHERE id_pfs IS NULL AND ST_Intersects(b.geom, c.geom)
                UNION
                SELECT 'Giunti', array_agg(b.gid) FROM %s.giunti b, %s.area_pfp c WHERE id_pfs IS NULL AND ST_Intersects(b.geom, c.geom)
                UNION
                SELECT 'PD', array_agg(b.gid) FROM %s.pd b, %s.area_pfp c WHERE id_pfs IS NULL AND ST_Intersects(b.geom, c.geom)
                UNION
                SELECT 'PFS', array_agg(b.gid) FROM %s.pfs b, %s.area_pfp c WHERE id_pfp IS NULL AND ST_Intersects(b.geom, c.geom)
                ORDER BY tipo_punto;""" % (theSchema, theSchema, theSchema, theSchema, theSchema, theSchema, theSchema, theSchema)
            cur_check.execute(query_check)
            results_check = cur_check.fetchall()
            cur_check.close()
            Utils.logMessage('Controllo grouping effettuato: alcune anomalie riscontrate. Di seguito elencati i GID degli oggetti non associati a PFS o nel caso dei PFS a PFP')
            Utils.logMessage(str(results_check))
            self.dlg_solid.txtFeedback.setText('Controllo grouping effettuato: alcune anomalie riscontrate. Vedere i log di QGis!')
            return 0
        else:
            #tutto ok:
            Utils.logMessage('Controllo grouping effettuato: nessuna anomalia')
            self.dlg_solid.txtFeedback.setText('Controllo grouping effettuato: nessuna anomalia')
            return 1
        
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        return 0
    finally:
        #if cur_check:
        #   cur_check.close()
        if test_conn is not None:
            test_conn.close()
        
def reset_all(self, connInfo, theSchema):
    test_conn = None
    cur_reset = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_reset = test_conn.cursor()
        #Resetto TUTTO:
        query_reset = "UPDATE %s.cavo SET f_4=0, f_12=0, f_24=0, f_48=0, f_72=0, f_96=0, f_144=0, f_192=0, tot_cavi=0, tot_fibre=0; UPDATE %s.variabili_progetto_return SET routing_scale_vertici=0, routing_pta_vertici=0, routing_giunti_vertici=0, routing_pd_vertici=0, routing_pfs_vertici=0, routing_pfp_vertici=0, routing_scale_fibre=0, routing_pta_fibre=0, routing_giunti_fibre=0, routing_pd_fibre=0, routing_pfs_fibre=0, routing_pfp_fibre=0, routing_start=0;" % (theSchema, theSchema)
        cur_reset.execute(query_reset)
        test_conn.commit()
        #Infine CANCELLO i CAMPI da CAVO considerati INUTILI e che eventualmente ripristinero' ad una nuova sessione di routing. Ma se son gia' stati cancellati non deve andare in errore!
        query_drop_column = """ALTER TABLE %s.cavo DROP COLUMN source;
        ALTER TABLE %s.cavo DROP COLUMN target;
        ALTER TABLE %s.cavo DROP COLUMN n_ui;""" % (theSchema, theSchema, theSchema)
        try:
            cur_reset.execute(query_drop_column)
        except:
            Utils.logMessage("Campi source-target-n_ui gia' non presenti su cavo")
        else:
            test_conn.commit()
        finally:
            cur_reset.close()
        #Aggiorno la maschera e i pulsanti da abilitare/disabilitare:
        inizializza_gui(self, connInfo, theSchema)
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        return 0
    else:
        Utils.logMessage('Resettato tutto il routing con successo!')
        self.dlg_solid.txtFeedback.setText('Resettato tutto il routing con successo!')
        return 1
    finally:
        #if cur_reset is not None:
        #    cur_reset.close()
        if test_conn is not None:
            test_conn.close()

def inizializza_gui(self, connInfo, theSchema):
    #Inizializzo la maschera "Consolida il progetto" scegliendo quali pulsanti attivare e quali no
    test_conn = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        #cur_gui = test_conn.cursor()
        dict_cur = test_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        #Controllo inizializzazione CAVO:
        query = "SELECT routing_scale_vertici, routing_pta_vertici, routing_giunti_vertici, routing_pd_vertici, routing_pfs_vertici, routing_pfp_vertici, routing_scale_fibre, routing_pta_fibre, routing_giunti_fibre, routing_pd_fibre, routing_pfs_fibre, routing_pfp_fibre, routing_start FROM %s.variabili_progetto_return;" % (theSchema)
        dict_cur.execute(query)
        results = dict_cur.fetchone()
        routing_start = results['routing_start']
        if (routing_start>0):
            self.dlg_solid.start_routing_btn.setEnabled(False); #inizializzazione gia' avvenuta
            self.dlg_solid.chk_start.setChecked(True);
        else:
            self.dlg_solid.start_routing_btn.setEnabled(True);
            self.dlg_solid.chk_start.setChecked(False);
        #Controllo routing su SCALA:
        routing_scale_vertici = results['routing_scale_vertici']
        if (routing_start==0):
            self.dlg_solid.associa_scale.setEnabled(False); #inizializzazione nn possibile
            self.dlg_solid.chk_scale.setChecked(False);
        elif (routing_scale_vertici>0):
            self.dlg_solid.associa_scale.setEnabled(False); #inizializzazione gia' avvenuta
            self.dlg_solid.chk_scale.setChecked(True);
        else:
            self.dlg_solid.associa_scale.setEnabled(True);
            self.dlg_solid.chk_scale.setChecked(False);
        #Controllo routing su PTA:
        routing_pta_vertici = results['routing_pta_vertici']
        if (routing_start==0 or routing_scale_vertici==0):
            self.dlg_solid.associa_pta.setEnabled(False); #inizializzazione nn possibile
            self.dlg_solid.chk_pta.setChecked(False);
        elif (routing_pta_vertici>0):
            self.dlg_solid.associa_pta.setEnabled(False); #inizializzazione gia' avvenuta
            self.dlg_solid.chk_pta.setChecked(True);
        else:
            self.dlg_solid.associa_pta.setEnabled(True);
            self.dlg_solid.chk_pta.setChecked(False);
        #Controllo routing su GIUNTO:
        routing_giunti_vertici = results['routing_giunti_vertici']
        if (routing_start==0 or routing_scale_vertici==0 or routing_pta_vertici==0):
            self.dlg_solid.associa_giunti.setEnabled(False); #inizializzazione nn possibile
            self.dlg_solid.chk_giunti.setChecked(False);
        elif (routing_giunti_vertici>0):
            self.dlg_solid.associa_giunti.setEnabled(False); #inizializzazione gia' avvenuta
            self.dlg_solid.chk_giunti.setChecked(True);
        else:
            self.dlg_solid.associa_giunti.setEnabled(True);
            self.dlg_solid.chk_giunti.setChecked(False);
        #Controllo routing su PD:
        routing_pd_vertici = results['routing_pd_vertici']
        if (routing_start==0 or routing_scale_vertici==0 or routing_pta_vertici==0 or routing_giunti_vertici==0):
            self.dlg_solid.associa_pd.setEnabled(False); #inizializzazione nn possibile
            self.dlg_solid.chk_pd.setChecked(False);
        elif (routing_pd_vertici>0):
            self.dlg_solid.associa_pd.setEnabled(False); #inizializzazione gia' avvenuta
            self.dlg_solid.chk_pd.setChecked(True);
        else:
            self.dlg_solid.associa_pd.setEnabled(True);
            self.dlg_solid.chk_pd.setChecked(False);
        #Controllo routing su PFS:
        routing_pfs_vertici = results['routing_pfs_vertici']
        if (routing_start==0 or routing_scale_vertici==0 or routing_pta_vertici==0 or routing_giunti_vertici==0 or routing_pd_vertici==0):
            self.dlg_solid.associa_pfs.setEnabled(False); #inizializzazione nn possibile
            self.dlg_solid.chk_pfs.setChecked(False);
        elif (routing_pfs_vertici>0):
            self.dlg_solid.associa_pfs.setEnabled(False); #inizializzazione gia' avvenuta
            self.dlg_solid.chk_pfs.setChecked(True);
        else:
            self.dlg_solid.associa_pfs.setEnabled(True);
            self.dlg_solid.chk_pfs.setChecked(False);
        #Controllo routing su PFP:
        routing_pfp_vertici = results['routing_pfp_vertici']
        if (routing_start==0 or routing_scale_vertici==0 or routing_pta_vertici==0 or routing_giunti_vertici==0 or routing_pd_vertici==0 or routing_pfs_vertici==0):
            self.dlg_solid.associa_pfp.setEnabled(False); #inizializzazione nn possibile
            self.dlg_solid.chk_pfp.setChecked(False);
        elif (routing_pfp_vertici>0):
            self.dlg_solid.associa_pfp.setEnabled(False); #inizializzazione gia' avvenuta
            self.dlg_solid.chk_pfp.setChecked(True);
        else:
            self.dlg_solid.associa_pfp.setEnabled(True);
            self.dlg_solid.chk_pfp.setChecked(False);
        
        routing_scale_fibre = results['routing_scale_fibre']
        routing_pta_fibre = results['routing_pta_fibre']
        routing_giunti_fibre = results['routing_giunti_fibre']
        routing_pd_fibre = results['routing_pd_fibre']
        routing_pfs_fibre = results['routing_pfs_fibre']
        routing_pfp_fibre = results['routing_pfp_fibre'] #di fatto al momento e' sempre ZERO perche' non calcolo realmente delle fibre a partire dai PFP...
        #Se tutto e' stato inizializzato con successo allora sblocco il pulsante del calcolo finale, altrimenti lo lascio disabilitato:
        routing_vertici = routing_start + routing_scale_vertici + routing_pta_vertici + routing_giunti_vertici + routing_pd_vertici + routing_pfs_vertici + routing_pfp_vertici
        routing_fibre = routing_scale_fibre + routing_pta_fibre + routing_giunti_fibre + routing_pd_fibre + routing_pfs_fibre
        if (routing_vertici==7 and routing_fibre==0): #posso procedere
            self.dlg_solid.calcola_fibre_btn.setEnabled(True);
            self.dlg_solid.chk_fibre.setChecked(False);
        elif (routing_vertici==7 and routing_fibre==5): #inizializzazione gia' avvenuta
            self.dlg_solid.calcola_fibre_btn.setEnabled(False);
            self.dlg_solid.chk_fibre.setChecked(True);
        else: #manca ancora qualcosa da inizializzare
            self.dlg_solid.calcola_fibre_btn.setEnabled(False);
            self.dlg_solid.chk_fibre.setChecked(False);
        
        dict_cur.close()
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        return 0
    else:
        return 1
        Utils.logMessage('Connessioni analizzate con successo!')
    finally:
        if test_conn is not None:
            test_conn.close()

def popola_cavo(self, connInfo, theSchema):
    #popolo il layer cavo prendendo le geometrie da sottotratta. Svuoto e riempio ogni volta, elimino le colonne di troppo e di conseguenza resetto prima tutto:
    test_conn = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_cavo = test_conn.cursor()
        query_cavo = "TRUNCATE %s.cavo; INSERT INTO %s.cavo (geom, id_sottotratta) SELECT geom, id_sottotr FROM %s.sottotratta;" % (theSchema, theSchema, theSchema)
        cur_cavo.execute(query_cavo)
        test_conn.commit()
        cur_cavo.close()
        #Aggiorno la maschera e i pulsanti da abilitare/disabilitare - superfluo in quanto prima lancio la funzione reset_all
        #inizializza_gui(self, connInfo, theSchema)
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        #self.dlg_solid.start_routing_btn.setEnabled(False); #inizializzazione avvenuta con successo
        #self.dlg_solid.chk_start.setChecked(True);
        Utils.logMessage("Creazione cavo effettuata con successo")
        return 1
    finally:
        #if cur_cavo:
        #    cur_cavo.close()
        if test_conn is not None:
            test_conn.close()

def inizializza_routing(self, connInfo, theSchema):
    test_conn = None
    count = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_start = test_conn.cursor()
        
        #Aggiungo questi campi che poi verranno eliminati sotto calcola_route:
        query_pgr = """ALTER TABLE %s.cavo ADD COLUMN source integer;
            ALTER TABLE %s.cavo ADD COLUMN target integer;
            ALTER TABLE %s.cavo ADD COLUMN n_ui integer DEFAULT 0;
            DROP INDEX IF EXISTS %s.cavo_geom_gidx;
            SELECT public.pgr_createTopology('%s.cavo', 0.1, 'geom', 'gid');""" % (theSchema, theSchema, theSchema, theSchema, theSchema)
        cur_start.execute(query_pgr)
        test_conn.commit()
        
        query_routing_raw = """CREATE TABLE IF NOT EXISTS %(schema)s.pgrvertices_netpoints_array (
id_pgr bigint, gid_scala integer[], gid_pta integer[], gid_giunto integer[], gid_pd integer[], gid_pfs integer[], gid_pfp integer[]
        );
        TRUNCATE TABLE %(schema)s.pgrvertices_netpoints_array;
        INSERT INTO %(schema)s.pgrvertices_netpoints_array(id_pgr) SELECT id FROM %(schema)s.cavo_vertices_pgr;
        UPDATE %(schema)s.variabili_progetto_return SET routing_start = 1;
        UPDATE %(schema)s.cavo SET length_m = ST_Length(geom);
        CREATE TABLE IF NOT EXISTS %(schema)s.cavoroute (
  gid serial NOT NULL PRIMARY KEY, id_cavo character varying(64), fibre_coun integer, n_ui integer, n_ui_reali integer, from_p character varying(64), to_p character varying(64), net_type character varying(255), length_m double precision, source integer, target integer, geom geometry(MultiLineString,3004), tipo_posa character varying(450)[], n_gnz_un smallint, n_gnz_tot integer, n_gnz_min8 smallint, n_gnz_mag8 smallint, n_gnz_min12 smallint, n_gnz_mag12 smallint, teste_cavo smallint, scorta smallint, terminaz integer, temp_cavo_label character varying(250)[], lung_ott double precision);
        TRUNCATE TABLE %(schema)s.cavoroute;
        """
        query_routing = query_routing_raw % {'schema': theSchema, 'lotto': theSchema.replace('lotto_', '')}
        cur_start.execute(query_routing)
        test_conn.commit()
        
        #PRIMO CONTROLLO: che il layer lineare non abbia source=target:
        query_primo_check = "SELECT count(*), array_agg(gid) FROM %s.cavo WHERE source=target;" % (theSchema)
        cur_start.execute(query_primo_check)
        results_primo_check = cur_start.fetchone()
        count = results_primo_check[0]
        if (count>0):
            #QMessageBox.warning(self.dock, self.dock.windowTitle(), "Attenzione, sono stati ritrovati dei cavi il cui vertice d'origine coincide con la destinazione!\nQuesto puo' essere dovuto ad una errata vettorializzazione della linea.\nIn ogni caso il layer e' stato inizializzato con successo!\nVedere il log di QGis per i dettagli.")
            Utils.logMessage("GID dei cavi con vertici di origine e destinazione coincidenti: " + str(results_primo_check[1]))
        else:
            Utils.logMessage("Primo controllo andato a buon fine!")
        
        cur_start.close()
        #Aggiorno la maschera e i pulsanti da abilitare/disabilitare:
        inizializza_gui(self, connInfo, theSchema)
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        test_conn.rollback()
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        test_conn.rollback()
        return 0
    else:
        self.dlg_solid.start_routing_btn.setEnabled(False); #inizializzazione avvenuta con successo
        self.dlg_solid.chk_start.setChecked(True);
        if (count>0):
            Utils.logMessage("Inizializzazione routing effettuata con successo ma con qualche eccezione")
            return 2
        else:
            Utils.logMessage("Inizializzazione routing effettuata con successo")
            return 1
    finally:
        #if cur_start is not None:
        #    cur_start.close()
        if test_conn is not None:
            test_conn.close()

def messaggio_verifica_routing(self, cursor, chiave, results, diff_count, theSchema, test_conn):
    gids = []
    for gid in results:
        gids.append(gid[0])
    Utils.logMessage("GIDs "+ chiave + " NON associati:" + str(gids))
    msg = QMessageBox()
    msg.setText("Attenzione " + str(diff_count) +" "+ chiave + " non e' stata associata!\n GID non associati: vedi log di QGis")
    msg.setInformativeText("Alcuni elementi non sono stati associati ai vertici del layer cavo. Se questi elementi non fanno parte del progetto, si puo' continuare senza problemi, altrimenti e' bene interrompere le operazioni e ricontrollare il progetto. Continuare?")
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Alcuni elementi non associati: continuare?")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    retval = msg.exec_()
    if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
        self.dlg_solid.txtFeedback.setText("Attenzione " + str(diff_count) +" "+ chiave + " non e' stata associata!\n GID non associati: vedi log di QGis. Si e' scelto di fermarsi.")
        return 0                
    self.dlg_solid.txtFeedback.setText("Attenzione " + str(diff_count) +" "+ chiave + " non e' stata associata!\n GID non associati: vedi log di QGis. Si e' scelto comunque di continuare.")
    #E dunque continuo e associo:
    query_ok = None
    if (chiave=='SCALA'):
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_scale_vertici=1;" % (theSchema)
    elif (chiave=='PTA'):
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_pta_vertici=1;" % (theSchema)
    elif (chiave=='GIUNTO'):
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_giunti_vertici=1;" % (theSchema)
    elif (chiave=='PD'):
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_pd_vertici=1;" % (theSchema)
    elif (chiave=='PFS'):
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_pfs_vertici=1;" % (theSchema)
    elif (chiave=='PFP'):
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_pfp_vertici=1;" % (theSchema)        
    cursor.execute(query_ok)
    test_conn.commit()
    return 1

def scale_routing(self, connInfo, theSchema): #aggiornato per gestire array
    test_conn = None
    gids = None
    punti_abbandonati = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_scala = test_conn.cursor()
        #Verifica:
        #query_verifica = "SELECT ( SELECT count(*) FROM %s.cavo_vertices_pgr a, %s.scala b WHERE ST_Equals(a.the_geom, b.geom)) - (SELECT COUNT(*) FROM %s.scala) AS diff_count;" % (theSchema, theSchema, theSchema)
        #Aggiungo filtro su area PFP:
        query_verifica = "SELECT ( SELECT count(*) FROM %s.cavo_vertices_pgr a, %s.scala b, %s.area_pfp c WHERE ST_Equals(a.the_geom, b.geom) AND ST_Intersects(b.geom, c.geom) ) - (SELECT COUNT(*) FROM %s.scala b, %s.area_pfp c WHERE ST_Intersects(b.geom, c.geom)) AS diff_count;" % (theSchema, theSchema, theSchema, theSchema, theSchema)
        cur_scala.execute(query_verifica)
        results_verifica = cur_scala.fetchone()
        diff_count = cur_scala.rowcount
        if (diff_count!=0):
            #Se diverso da ZERO --> aumento la tolleranza in metri, e filtro su area PFP:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_scala = scala_node FROM
            (SELECT pg_node, array_agg(gid) AS scala_node FROM (
            SELECT max(a.id) AS pg_node, b.gid FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.scala b, %(schema)s.area_pfp c WHERE ST_DWithin(a.the_geom, b.geom, 0.5) AND ST_Intersects(b.geom, c.geom) GROUP BY b.gid) AS foo GROUP BY pg_node) AS foo
            WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node AND pgrvertices_netpoints_array.gid_scala IS NULL;"""
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
            #Ultima verifica:
            query_verifica = "SELECT b.gid FROM %s.scala b, %s.area_pfp c WHERE ST_Intersects(b.geom, c.geom) EXCEPT SELECT b.gid FROM %s.cavo_vertices_pgr a, %s.scala b, %s.area_pfp c WHERE ST_DWithin(a.the_geom, b.geom, 0.5) AND ST_Intersects(b.geom, c.geom);" % (theSchema, theSchema, theSchema, theSchema, theSchema)
            cur_scala.execute(query_verifica)
            results_verifica = cur_scala.fetchall()
            diff_count = cur_scala.rowcount
            #Se anche aumentando la tolleranza dei punti restano fuori, chiedo all'utente se vuole abbandonare o proseguire:
            if (diff_count!=0):
                risposta = messaggio_verifica_routing(self, cur_scala, 'SCALA', results_verifica, diff_count, theSchema, test_conn)
                gids = results_verifica[0]
                if (risposta==0):
                    return 0
                #Per poter ritornare indietro con un messaggio diverso:
                punti_abbandonati = diff_count
            else:
                query_ok = "UPDATE %s.variabili_progetto_return SET routing_scale_vertici=1;" % (theSchema)
                cur_scala.execute(query_ok)
                test_conn.commit()
                self.dlg_solid.txtFeedback.setText("Associazione delle SCALE ai CAVI andata a buon fine aumentando la tolleranza di ricerca!")
        else:
            #Se al primo giro posso associare tutti le SCALE:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_scala = scala_node FROM
                (SELECT a.id AS pg_node, array_agg(b.gid) AS scala_node FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.scala b, %(schema)s.area_pfp c WHERE ST_Equals(a.the_geom, b.geom) AND ST_Intersects(b.geom, c.geom) GROUP BY pg_node) AS foo
                WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node;"""
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
        
            query_ok = "UPDATE %s.variabili_progetto_return SET routing_scale_vertici=1;" % (theSchema)
            cur_scala.execute(query_ok)
            test_conn.commit()
            self.dlg_solid.txtFeedback.setText('Associazione delle SCALE ai CAVI andata a buon fine al primo giro!')
        
        cur_scala.close()
        #Aggiorno la maschera e i pulsanti da abilitare/disabilitare:
        inizializza_gui(self, connInfo, theSchema)
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if (punti_abbandonati):
            Utils.logMessage('Inizializzazione routing su scale effettuata ma con qualche reticenza')
            return 3
        elif (gids):
            Utils.logMessage('Inizializzazione routing su scale NON effettuata, controllare!')
            return 2
        else:
            self.dlg_solid.associa_scale.setEnabled(False); #inizializzazione avvenuta con successo
            self.dlg_solid.chk_scale.setChecked(True);
            Utils.logMessage('Inizializzazione routing su scale effettuata con successo!')
            return 1
    finally:
        #if cur_scala:
        #    cur_scala.close()
        if test_conn is not None:
            test_conn.close()
    
def pta_routing(self, connInfo, theSchema): #aggiornato per gestire array
    test_conn = None
    gids = None
    punti_abbandonati = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_scala = test_conn.cursor()
        #Verifica:
        query_verifica = "SELECT ( SELECT count(*) FROM %s.cavo_vertices_pgr a, %s.giunti b, %s.area_pfp c WHERE ST_Equals(a.the_geom, b.geom) AND upper(tipo_giunt)='PTA' AND ST_Intersects(b.geom, c.geom)) - (SELECT COUNT(*) FROM %s.giunti b, %s.area_pfp c WHERE upper(tipo_giunt)='PTA' AND ST_Intersects(b.geom, c.geom)) AS diff_count;" % (theSchema, theSchema, theSchema, theSchema, theSchema)
        cur_scala.execute(query_verifica)
        results_verifica = cur_scala.fetchone()
        diff_count = cur_scala.rowcount
        if (diff_count!=0):
            #Se diverso da ZERO --> aumento la tolleranza in metri:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_pta = pta_node FROM
            (SELECT pg_node, array_agg(gid) AS pta_node FROM (
            SELECT max(a.id) AS pg_node, b.gid FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.giunti b, %(schema)s.area_pfp c WHERE ST_DWithin(a.the_geom, b.geom, 0.5) AND upper(tipo_giunt)='PTA' AND ST_Intersects(b.geom, c.geom) GROUP BY b.gid) AS foo GROUP BY pg_node) AS foo
            WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node AND pgrvertices_netpoints_array.gid_pta IS NULL;"""            
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
            #Ultima verifica:
            query_verifica = "SELECT b.gid FROM %s.giunti b, %s.area_pfp c WHERE upper(tipo_giunt)='PTA' AND ST_Intersects(b.geom, c.geom) EXCEPT SELECT b.gid FROM %s.cavo_vertices_pgr a, %s.giunti b, %s.area_pfp c WHERE ST_DWithin(a.the_geom, b.geom, 0.5) AND upper(tipo_giunt)='PTA' AND ST_Intersects(b.geom, c.geom);" % (theSchema, theSchema, theSchema, theSchema, theSchema)
            cur_scala.execute(query_verifica)
            results_verifica = cur_scala.fetchall()
            diff_count = cur_scala.rowcount
            #Se anche aumentando la tolleranza dei punti restano fuori, chiedo all'utente se vuole abbandonare o proseguire:
            if (diff_count!=0):
                risposta = messaggio_verifica_routing(self, cur_scala, 'PTA', results_verifica, diff_count, theSchema, test_conn)
                gids = results_verifica[0]
                if (risposta==0):
                    return 0
                #Per poter ritornare indietro con un messaggio diverso:
                punti_abbandonati = diff_count
            else:
                query_ok = "UPDATE %s.variabili_progetto_return SET routing_pta_vertici=1;" % (theSchema)
                cur_scala.execute(query_ok)
                test_conn.commit()
                self.dlg_solid.txtFeedback.setText("Associazione dei PTA ai CAVI andata a buon fine aumentando la tolleranza di ricerca!")
        else:
            #Se al primo giro posso associare tutti i PTA:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_pta = pta_node FROM
                (SELECT a.id AS pg_node, array_agg(b.gid) AS pta_node FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.giunti b, %(schema)s.area_pfp c WHERE ST_Equals(a.the_geom, b.geom) AND upper(tipo_giunt)='PTA' AND ST_Intersects(b.geom, c.geom) GROUP BY pg_node) AS foo
                WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node;"""
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
        
            query_ok = "UPDATE %s.variabili_progetto_return SET routing_pta_vertici=1;" % (theSchema)
            cur_scala.execute(query_ok)
            test_conn.commit()
            self.dlg_solid.txtFeedback.setText('Associazione dei PTA ai CAVI andata a buon fine al primo giro!')
        
        cur_scala.close()
        #Aggiorno la maschera e i pulsanti da abilitare/disabilitare:
        inizializza_gui(self, connInfo, theSchema)
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if (punti_abbandonati):
            Utils.logMessage('Inizializzazione routing su pta effettuata ma con qualche reticenza')
            return 3
        elif (gids):
            Utils.logMessage('Inizializzazione routing su pta NON effettuata, controllare!')
            return 2
        else:
            self.dlg_solid.associa_pta.setEnabled(False); #inizializzazione avvenuta con successo
            self.dlg_solid.chk_pta.setChecked(True);
            Utils.logMessage('Inizializzazione routing su pta effettuata con successo!')
            return 1
    finally:
        #if cur_scala:
        #    cur_scala.close()
        if test_conn is not None:
            test_conn.close()
            
def giunti_routing(self, connInfo, theSchema): #aggiornato per gestire array
    test_conn = None
    gids = None
    punti_abbandonati = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_scala = test_conn.cursor()
        #Verifica:
        query_verifica = "SELECT ( SELECT count(*) FROM %s.cavo_vertices_pgr a, %s.giunti b, %s.area_pfp c WHERE ST_Equals(a.the_geom, b.geom) AND upper(tipo_giunt)!='PTA' AND ST_Intersects(b.geom, c.geom)) - (SELECT COUNT(*) FROM %s.giunti b, %s.area_pfp c WHERE upper(tipo_giunt)!='PTA' AND ST_Intersects(b.geom, c.geom)) AS diff_count;" % (theSchema, theSchema, theSchema, theSchema, theSchema)
        cur_scala.execute(query_verifica)
        results_verifica = cur_scala.fetchone()
        diff_count = cur_scala.rowcount
        if (diff_count!=0):
            #Se diverso da ZERO --> aumento la tolleranza in metri:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_giunto = giunto_node FROM
            (SELECT pg_node, array_agg(gid) AS giunto_node FROM (
            SELECT max(a.id) AS pg_node, b.gid FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.giunti b, %(schema)s.area_pfp c WHERE ST_DWithin(a.the_geom, b.geom, 0.5) AND upper(tipo_giunt)!='PTA' AND ST_Intersects(b.geom, c.geom) GROUP BY b.gid) AS foo GROUP BY pg_node) AS foo
            WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node AND pgrvertices_netpoints_array.gid_giunto IS NULL;"""            
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
            #Ultima verifica:
            query_verifica = "SELECT b.gid FROM %s.giunti b, %s.area_pfp c WHERE upper(tipo_giunt)!='PTA' AND ST_Intersects(b.geom, c.geom) EXCEPT SELECT b.gid FROM %s.cavo_vertices_pgr a, %s.giunti b, %s.area_pfp c WHERE ST_DWithin(a.the_geom, b.geom, 0.5) AND upper(tipo_giunt)!='PTA' AND ST_Intersects(b.geom, c.geom);" % (theSchema, theSchema, theSchema, theSchema, theSchema)
            cur_scala.execute(query_verifica)
            results_verifica = cur_scala.fetchall()
            diff_count = cur_scala.rowcount
            #Se anche aumentando la tolleranza dei punti restano fuori, chiedo all'utente se vuole abbandonare o proseguire:
            if (diff_count!=0):
                risposta = messaggio_verifica_routing(self, cur_scala, 'GIUNTO', results_verifica, diff_count, theSchema, test_conn)
                gids = results_verifica[0]
                if (risposta==0):
                    return 0
                #Per poter ritornare indietro con un messaggio diverso:
                punti_abbandonati = diff_count
            else:
                query_ok = "UPDATE %s.variabili_progetto_return SET routing_giunti_vertici=1;" % (theSchema)
                cur_scala.execute(query_ok)
                test_conn.commit()
                self.dlg_solid.txtFeedback.setText("Associazione dei GIUNTI ai CAVI andata a buon fine aumentando la tolleranza di ricerca!")
        else:
            #Se al primo giro posso associare tutti i GIUNTI:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_giunto = giunto_node FROM
                (SELECT a.id AS pg_node, array_agg(b.gid) AS giunto_node FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.giunti b, %(schema)s.area_pfp c WHERE ST_Equals(a.the_geom, b.geom) AND upper(tipo_giunt)!='PTA' AND ST_Intersects(b.geom, c.geom) GROUP BY pg_node) AS foo
                WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node;"""
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
        
            query_ok = "UPDATE %s.variabili_progetto_return SET routing_giunti_vertici=1;" % (theSchema)
            cur_scala.execute(query_ok)
            test_conn.commit()
            self.dlg_solid.txtFeedback.setText('Associazione dei GIUNTI ai CAVI andata a buon fine al primo giro!')
        
        cur_scala.close()
        #Aggiorno la maschera e i pulsanti da abilitare/disabilitare:
        inizializza_gui(self, connInfo, theSchema)
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if (punti_abbandonati):
            Utils.logMessage('Inizializzazione routing su giunti effettuata ma con qualche reticenza')
            return 3
        elif (gids):
            Utils.logMessage('Inizializzazione routing su giunti NON effettuata, controllare!')
            return 2
        else:
            self.dlg_solid.associa_giunti.setEnabled(False); #inizializzazione avvenuta con successo
            self.dlg_solid.chk_giunti.setChecked(True);
            Utils.logMessage('Inizializzazione routing su giunti effettuata con successo!')
            return 1
    finally:
        #if cur_scala:
        #    cur_scala.close()
        if test_conn is not None:
            test_conn.close()
    
def pd_routing(self, connInfo, theSchema): #aggiornato per gestire array
    test_conn = None
    gids = None
    punti_abbandonati = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_scala = test_conn.cursor()
        #Verifica:
        query_verifica = "SELECT ( SELECT count(*) FROM %s.cavo_vertices_pgr a, %s.pd b, %s.area_pfp c WHERE ST_Equals(a.the_geom, b.geom) AND ST_Intersects(b.geom, c.geom)) - (SELECT COUNT(*) FROM %s.pd b, %s.area_pfp c WHERE ST_Intersects(b.geom, c.geom)) AS diff_count;" % (theSchema, theSchema, theSchema, theSchema, theSchema)
        cur_scala.execute(query_verifica)
        results_verifica = cur_scala.fetchone()
        #diff_count = results_verifica[0]
        diff_count = cur_scala.rowcount
        if (diff_count!=0):
            #Se diverso da ZERO --> Seconda passata aumentando la tolleranza in metri:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_pd = pd_node FROM
            (SELECT pg_node, array_agg(gid) AS pd_node FROM (
            SELECT max(a.id) AS pg_node, b.gid FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.pd b, %(schema)s.area_pfp c WHERE ST_DWithin(a.the_geom, b.geom, 0.5) AND ST_Intersects(b.geom, c.geom) GROUP BY b.gid) AS foo GROUP BY pg_node) AS foo
            WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node AND pgrvertices_netpoints_array.gid_pd IS NULL;"""       
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
            #Ultima verifica:
            query_verifica = "SELECT b.gid FROM %s.pd b, %s.area_pfp c WHERE ST_Intersects(b.geom, c.geom) EXCEPT SELECT b.gid FROM %s.cavo_vertices_pgr a, %s.pd b, %s.area_pfp c WHERE ST_DWithin(a.the_geom, b.geom, 0.5) AND ST_Intersects(b.geom, c.geom);" % (theSchema, theSchema, theSchema, theSchema, theSchema)
            cur_scala.execute(query_verifica)
            results_verifica = cur_scala.fetchall()
            #diff_count = results_verifica[0]
            diff_count = cur_scala.rowcount
            #Se anche aumentando la tolleranza dei punti restano fuori, chiedo all'utente se vuole abbandonare o proseguire:
            if (diff_count!=0):
                risposta = messaggio_verifica_routing(self, cur_scala, 'PD', results_verifica, diff_count, theSchema, test_conn)
                gids = results_verifica[0]
                if (risposta==0):
                    return 0
                #Per poter ritornare indietro con un messaggio diverso:
                punti_abbandonati = diff_count
            else:
                query_ok = "UPDATE %s.variabili_progetto_return SET routing_pd_vertici=1;" % (theSchema)
                cur_scala.execute(query_ok)
                test_conn.commit()
                self.dlg_solid.txtFeedback.setText("Associazione dei PD ai CAVI andata a buon fine aumentando la tolleranza di ricerca!")
        else:
            #Se al primo giro posso associare tutti i PD:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_pd = pd_node FROM
                (SELECT a.id AS pg_node, array_agg(b.gid) AS pd_node FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.pd b, %(schema)s.area_pfp c WHERE ST_Equals(a.the_geom, b.geom) AND ST_Intersects(b.geom, c.geom) GROUP BY pg_node) AS foo
                WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node;"""
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
        
            query_ok = "UPDATE %s.variabili_progetto_return SET routing_pd_vertici=1;" % (theSchema)
            cur_scala.execute(query_ok)
            test_conn.commit()
            self.dlg_solid.txtFeedback.setText('Associazione dei PD ai CAVI andata a buon fine al primo giro!')
        
        cur_scala.close()
        #Aggiorno la maschera e i pulsanti da abilitare/disabilitare:
        inizializza_gui(self, connInfo, theSchema)
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if (punti_abbandonati):
            Utils.logMessage('Inizializzazione routing su pd effettuata ma con qualche reticenza')
            return 3
        elif (gids):
            Utils.logMessage('Inizializzazione routing su pd NON effettuata, controllare!')
            return 2
        else:
            self.dlg_solid.associa_pd.setEnabled(False); #inizializzazione avvenuta con successo
            self.dlg_solid.chk_pd.setChecked(True);
            Utils.logMessage('Inizializzazione routing su pd effettuata con successo!')
            return 1
    finally:
        #if cur_scala:
        #    cur_scala.close()
        if test_conn is not None:
            test_conn.close()

def pfs_routing(self, connInfo, theSchema): #aggiornato per gestire array
    test_conn = None
    gids = None
    punti_abbandonati = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_scala = test_conn.cursor()
        #Verifica:
        query_verifica = "SELECT ( SELECT count(*) FROM %s.cavo_vertices_pgr a, %s.pfs b, %s.area_pfp c WHERE ST_Equals(a.the_geom, b.geom) AND ST_Intersects(b.geom, c.geom)) - (SELECT COUNT(*) FROM %s.pfs b, %s.area_pfp c WHERE ST_Intersects(b.geom, c.geom)) AS diff_count;" % (theSchema, theSchema, theSchema, theSchema, theSchema)
        cur_scala.execute(query_verifica)
        results_verifica = cur_scala.fetchone()
        diff_count = cur_scala.rowcount
        if (diff_count!=0):
            #Se diverso da ZERO --> Seconda passata aumentando la tolleranza in metri:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_pfs = pfs_node FROM
            (SELECT pg_node, array_agg(gid) AS pfs_node FROM (
            SELECT max(a.id) AS pg_node, b.gid FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.pfs b, %(schema)s.area_pfp c WHERE ST_DWithin(a.the_geom, b.geom, 0.5) AND ST_Intersects(b.geom, c.geom) GROUP BY b.gid) AS foo GROUP BY pg_node) AS foo
            WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node AND pgrvertices_netpoints_array.gid_pfs IS NULL;"""       
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
            #Ultima verifica:
            query_verifica = "SELECT b.gid FROM %s.pfs b, %s.area_pfp c WHERE ST_Intersects(b.geom, c.geom) EXCEPT SELECT b.gid FROM %s.cavo_vertices_pgr a, %s.pfs b, %s.area_pfp c  WHERE ST_DWithin(a.the_geom, b.geom, 0.5) AND ST_Intersects(b.geom, c.geom);" % (theSchema, theSchema, theSchema, theSchema, theSchema)
            cur_scala.execute(query_verifica)
            results_verifica = cur_scala.fetchall()
            diff_count = cur_scala.rowcount
            #Se anche aumentando la tolleranza dei punti restano fuori, chiedo all'utente se vuole abbandonare o proseguire:
            if (diff_count!=0):
                risposta = messaggio_verifica_routing(self, cur_scala, 'PFS', results_verifica, diff_count, theSchema, test_conn)
                gids = results_verifica[0]
                if (risposta==0):
                    return 0
                #Per poter ritornare indietro con un messaggio diverso:
                punti_abbandonati = diff_count
            else:
                query_ok = "UPDATE %s.variabili_progetto_return SET routing_pfs_vertici=1;" % (theSchema)
                cur_scala.execute(query_ok)
                test_conn.commit()
                self.dlg_solid.txtFeedback.setText("Associazione dei PFS ai CAVI andata a buon fine aumentando la tolleranza di ricerca!")
        else:
            #Se al primo giro posso associare tutti i PFS:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_pfs = pfs_node FROM
                (SELECT a.id AS pg_node, array_agg(b.gid) AS pfs_node FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.pfs b, %(schema)s.area_pfp c WHERE ST_Equals(a.the_geom, b.geom) AND ST_Intersects(b.geom, c.geom) GROUP BY pg_node) AS foo
                WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node;"""
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
        
            query_ok = "UPDATE %s.variabili_progetto_return SET routing_pfs_vertici=1;" % (theSchema)
            cur_scala.execute(query_ok)
            test_conn.commit()
            self.dlg_solid.txtFeedback.setText('Associazione dei PFS ai CAVI andata a buon fine al primo giro!')
        
        cur_scala.close()
        #Aggiorno la maschera e i pulsanti da abilitare/disabilitare:
        inizializza_gui(self, connInfo, theSchema)
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if (punti_abbandonati):
            Utils.logMessage('Inizializzazione routing su pfs effettuata ma con qualche reticenza')
            return 3
        elif (gids):
            Utils.logMessage('Inizializzazione routing su pfs NON effettuata, controllare!')
            return 2
        else:
            self.dlg_solid.associa_pfs.setEnabled(False); #inizializzazione avvenuta con successo
            self.dlg_solid.chk_pfs.setChecked(True);
            Utils.logMessage('Inizializzazione routing su pfs effettuata con successo!')
            return 1
    finally:
        #if cur_scala:
        #    cur_scala.close()
        if test_conn is not None:
            test_conn.close()

def pfp_routing(self, connInfo, theSchema): #aggiornato per gestire array
    test_conn = None
    gids = None
    punti_abbandonati = None
    try:
        dest_dir = self.estrai_param_connessione(connInfo)
        test_conn = psycopg2.connect(dest_dir)
        cur_scala = test_conn.cursor()
        #Verifica:
        query_verifica = "SELECT ( SELECT count(*) FROM %s.cavo_vertices_pgr a, %s.pfp b WHERE ST_Equals(a.the_geom, b.geom)) - (SELECT COUNT(*) FROM %s.pfp) AS diff_count;" % (theSchema, theSchema, theSchema)
        cur_scala.execute(query_verifica)
        results_verifica = cur_scala.fetchone()
        diff_count = cur_scala.rowcount
        if (diff_count!=0):
            #Se diverso da ZERO --> Seconda passata aumentando la tolleranza in metri:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_pfp = pfp_node FROM
            (SELECT pg_node, array_agg(gid) AS pfp_node FROM (
            SELECT max(a.id) AS pg_node, b.gid FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.pfp b WHERE ST_DWithin(a.the_geom, b.geom, 0.5) GROUP BY b.gid) AS foo GROUP BY pg_node) AS foo
            WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node AND pgrvertices_netpoints_array.gid_pfp IS NULL;"""      
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
            #Ultima verifica:
            query_verifica = "SELECT gid FROM %s.pfp EXCEPT SELECT gid FROM %s.cavo_vertices_pgr a, %s.pfp b WHERE ST_DWithin(a.the_geom, b.geom, 0.5)" % (theSchema, theSchema, theSchema)
            cur_scala.execute(query_verifica)
            results_verifica = cur_scala.fetchall()
            diff_count = cur_scala.rowcount
            #Se anche aumentando la tolleranza dei punti restano fuori, chiedo all'utente se vuole abbandonare o proseguire:
            if (diff_count!=0):
                risposta = messaggio_verifica_routing(self, cur_scala, 'PFP', results_verifica, diff_count, theSchema, test_conn)
                gids = results_verifica[0]
                if (risposta==0):
                    return 0
                #Per poter ritornare indietro con un messaggio diverso:
                punti_abbandonati = diff_count
            else:
                query_ok = "UPDATE %s.variabili_progetto_return SET routing_pfp_vertici=1;" % (theSchema)
                cur_scala.execute(query_ok)
                test_conn.commit()
                self.dlg_solid.txtFeedback.setText("Associazione dei PFP ai CAVI andata a buon fine aumentando la tolleranza di ricerca!")
        else:
            #Se al primo giro posso associare tutti i PFP:
            query_scala_raw = """UPDATE %(schema)s.pgrvertices_netpoints_array SET gid_pfp = pfp_node FROM
                (SELECT a.id AS pg_node, array_agg(b.gid) AS pfp_node FROM %(schema)s.cavo_vertices_pgr a, %(schema)s.pfp b WHERE ST_Equals(a.the_geom, b.geom) GROUP BY pg_node) AS foo
                WHERE pgrvertices_netpoints_array.id_pgr = foo.pg_node;"""
            query_scala = query_scala_raw % {'schema': theSchema}
            cur_scala.execute(query_scala)
            test_conn.commit()
        
            query_ok = "UPDATE %s.variabili_progetto_return SET routing_pfp_vertici=1;" % (theSchema)
            cur_scala.execute(query_ok)
            test_conn.commit()
            self.dlg_solid.txtFeedback.setText('Associazione dei PFP ai CAVI andata a buon fine al primo giro!')
        
        cur_scala.close()
        #Aggiorno la maschera e i pulsanti da abilitare/disabilitare:
        inizializza_gui(self, connInfo, theSchema)
    except psycopg2.Error, e:
        Utils.logMessage(e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if (punti_abbandonati):
            Utils.logMessage('Inizializzazione routing su pfp effettuata ma con qualche reticenza')
            return 3
        elif (gids):
            Utils.logMessage('Inizializzazione routing su pfp NON effettuata, controllare!')
            return 2
        else:
            self.dlg_solid.associa_pfp.setEnabled(False); #inizializzazione avvenuta con successo
            self.dlg_solid.chk_pfp.setChecked(True);
            Utils.logMessage('Inizializzazione routing su pfp effettuata con successo!')
            return 1
    finally:
        #if cur_scala:
        #    cur_scala.close()
        if test_conn is not None:
            test_conn.close()
