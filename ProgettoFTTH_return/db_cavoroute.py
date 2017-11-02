from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pgRoutingLayer_utils as Utils
import os
import psycopg2

QUERY_FROM_TO_NAME = {
    'SCALA_SCALA': 'QUERY_SC_SC',
    'SCALA_PTA': 'QUERY_SC_PTA',
    'SCALA_GIUNTO': 'QUERY_SC_GI',
    'SCALA_PD': 'QUERY_SC_PD',
    'SCALA_PFS': 'QUERY_SC_PFS',
    'PTA_PD': 'QUERY_PTA_PD',
    'PTA_PTA': 'QUERY_PTA_PTA',
    'PTA_PFS': 'QUERY_PTA_PFS',
    'PTA_GIUNTO': 'QUERY_PTA_GI',
    'GIUNTO_GIUNTO': 'QUERY_GI_GI',
    'GIUNTO_PD': 'QUERY_GI_PD',
    'PD_PD': 'QUERY_PD_PD',
    'PD_PFS': 'QUERY_PD_PFS',
    'PFS_PFP': 'QUERY_PFS_PFP'
}

def new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, tipo_punto):
    #dovrei riuscire a leggere tutto cio' che mi serve direttamnte dal DB
    #prima recupero a seconda del tipo_punto la fibra massima per fare un ciclo corretto fino all'esaurimento delle fibre
    if (self.FIBRE_CAVO[tipo_punto]['F_192']) > 0:
        max_fibra = self.FIBRE_CAVO[tipo_punto]['F_192']
        max_campo = 'f_192'
    elif (self.FIBRE_CAVO[tipo_punto]['F_144']) > 0:
        max_fibra = self.FIBRE_CAVO[tipo_punto]['F_144']
        max_campo = 'f_144'
    elif (self.FIBRE_CAVO[tipo_punto]['F_96']) > 0:
        max_fibra = self.FIBRE_CAVO[tipo_punto]['F_96']
        max_campo = 'f_96'
    elif (self.FIBRE_CAVO[tipo_punto]['F_72']) > 0:
        max_fibra = self.FIBRE_CAVO[tipo_punto]['F_72']
        max_campo = 'f_72'
    elif (self.FIBRE_CAVO[tipo_punto]['F_48']) > 0:
        max_fibra = self.FIBRE_CAVO[tipo_punto]['F_48']
        max_campo = 'f_48'
    elif (self.FIBRE_CAVO[tipo_punto]['F_24']) > 0:
        max_fibra = self.FIBRE_CAVO[tipo_punto]['F_24']
        max_campo = 'f_24'
    elif (self.FIBRE_CAVO[tipo_punto]['F_12']) > 0:
        max_fibra = self.FIBRE_CAVO[tipo_punto]['F_12']
        max_campo = 'f_12'
    elif (self.FIBRE_CAVO[tipo_punto]['F_4']) > 0:
        max_fibra = self.FIBRE_CAVO[tipo_punto]['F_4']
        max_campo = 'f_4'
    else:
        max_fibra = 9999
        max_campo = 'f_192'
        
    QUERY_UPDATE_FIBRE = ""
    #Da mail di Gatti del 15 Mar 2017: escludo connessioni Contatore-PTA se tipo_posa=AEREA:
    if (tipo_punto=='SCALA_PTA'):
        where_clause = "gid = %i AND (tipo_posa !~* '.*aere.*' OR tipo_posa IS NULL)" % (id_cavo)
    else:
        where_clause = "gid = %i" % (id_cavo)
        #Da mail di Gatti del 19 aprile 2017: escludo per TUTTE le connessioni se tipo_posa~aereo...Ma a quanto pare si e' sbagliato
        #where_clause = "gid = %i AND tipo_posa !~* '.*aere.*'" % (id_cavo)
    if (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_4']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_4=f_4+1 WHERE %s;" % (theSchema, where_clause)
        n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_4']
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_12']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_12=f_12+1 WHERE %s;" % (theSchema, where_clause)
        n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_12']
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_24']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_24=f_24+1 WHERE %s;" % (theSchema, where_clause)
        n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_24']
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_48']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_48=f_48+1 WHERE %s;" % (theSchema, where_clause)
        n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_48']
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_72']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_72=f_72+1 WHERE %s;" % (theSchema, where_clause)
        n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_72']
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_96']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_96=f_96+1 WHERE %s;" % (theSchema, where_clause)
        n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_96']
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_144']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_144=f_144+1 WHERE %s;" % (theSchema, where_clause)
        n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_144']
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_192']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_192=f_192+1 WHERE %s;" % (theSchema, where_clause)
        n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_192']
    elif (n_ui>max_fibra):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET %s=%s+1 WHERE %s;" % (theSchema, max_campo, max_campo, where_clause)
        n_ui = n_ui - max_fibra
    #Utils.logMessage("QUERY_UPDATE_FIBRE: " + QUERY_UPDATE_FIBRE)
    cur_update_fibre.execute(QUERY_UPDATE_FIBRE)
    test_conn.commit()
    #n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_96']
    return n_ui

def update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, tipo_punto):
    """ da mail di Gatti del 19 settembre
    contatore-Giunto contatore-PD contatore-PFS
    da 1 a 2 UI: cavo a 4 fibre ottiche;
    da 3 a 10 UI: cavo a 12 fibre ottiche;
    da 11 a 20 UI: cavo a 24 fibre ottiche;
    da 21 a 40 UI: cavo a 48 fibre ottiche."""
    
    #Prendendo i dati da DB si potrebbe riscrivere cosi passando il TIPO di punto:
    QUERY_UPDATE_FIBRE = ""
    if (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_4']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_4=f_4+1 WHERE gid = %i" % (theSchema, id_cavo)
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_12']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_12=f_12+1 WHERE gid = %i" % (theSchema, id_cavo)
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_24']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_24=f_24+1 WHERE gid = %i" % (theSchema, id_cavo)
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_48']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_48=f_48+1 WHERE gid = %i" % (theSchema, id_cavo)
    elif (n_ui>self.FIBRE_CAVO[tipo_punto]['F_48']):
        QUERY_UPDATE_FIBRE = "UPDATE %s.cavo SET f_48=f_48+1 WHERE gid = %i" % (theSchema, id_cavo)
    cur_update_fibre.execute(QUERY_UPDATE_FIBRE)
    test_conn.commit()
    n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_48']
    return n_ui


def update_fibre_pd_pfs(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, tipo_punto):
    """ da mail di Gatti del 19 settembre
    rete di drop-Giunto-PD PD-PFS
    da 1 a 12 UI: cavo a 24 fibre ottiche;
    da 13 a 36 UI: cavo a 48 fibre ottiche;
    da 37 a 60 UI: cavo a 72 fibre ottiche;
    da 61 a 72 UI: cavo a 96 fibre ottiche;
    da 73 a 120 UI: cavo a 144 fibre ottiche."""
    
    #Prendendo i dati da DB si potrebbe riscrivere cosi passando il TIPO di punto:
    QUERY_UPDATE_FIBRE_PD_PFS = ""
    if (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_24']):
        QUERY_UPDATE_FIBRE_PD_PFS = "UPDATE %s.cavo SET f_24=f_24+1 WHERE gid = %i" % (theSchema, id_cavo)
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_48']):
        QUERY_UPDATE_FIBRE_PD_PFS = "UPDATE %s.cavo SET f_48=f_48+1 WHERE gid = %i" % (theSchema, id_cavo)
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_72']):
        QUERY_UPDATE_FIBRE_PD_PFS = "UPDATE %s.cavo SET f_72=f_72+1 WHERE gid = %i" % (theSchema, id_cavo)
    elif (n_ui<=self.FIBRE_CAVO[tipo_punto]['F_96']):
        QUERY_UPDATE_FIBRE_PD_PFS = "UPDATE %s.cavo SET f_96=f_96+1 WHERE gid = %i" % (theSchema, id_cavo)
    elif (n_ui>self.FIBRE_CAVO[tipo_punto]['F_96']):
        QUERY_UPDATE_FIBRE_PD_PFS = "UPDATE %s.cavo SET f_144=f_144+1 WHERE gid = %i" % (theSchema, id_cavo)
        #n_ui = n_ui - 72
    cur_update_fibre.execute(QUERY_UPDATE_FIBRE_PD_PFS)
    test_conn.commit()
    n_ui = n_ui - self.FIBRE_CAVO[tipo_punto]['F_96']
    return n_ui

    
def update_fibre_pfs_pfp(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, tipo_punto):
    """dal PFS al PFP : sempre 1 cavo da 96 fibre ottiche"""    
    QUERY_UPDATE_FIBRE_PFS_PFP = "UPDATE %s.cavo SET f_96=f_96+1 WHERE gid = %i" % (theSchema, id_cavo)
    cur_update_fibre.execute(QUERY_UPDATE_FIBRE_PFS_PFP)
    test_conn.commit()
    return n_ui    

QUERY_SC_SC = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.scala a
LEFT JOIN
%(schema)s.scala b ON (a.id_sc_ref = b.id_scala)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_scala))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_scala))
WHERE a.id_scala IS NOT NULL AND a.id_sc_ref IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL;"""

QUERY_SC_PTA = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.scala a
LEFT JOIN
%(schema)s.giunti b ON (b.id_giunto = a.id_giunto)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_scala))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pta))
WHERE a.id_giunto IS NOT NULL AND a.id_sc_ref IS NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(tipo_giunt)='PTA';"""

QUERY_SC_GI = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.scala a
LEFT JOIN
%(schema)s.giunti b ON (b.id_giunto = a.id_giunto)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_scala))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_giunto))
WHERE a.id_giunto IS NOT NULL AND a.id_sc_ref IS NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(tipo_giunt)!='PTA';"""

QUERY_SC_PD = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.scala a
LEFT JOIN
%(schema)s.pd b ON (b.id_pd = a.id_pd)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_scala))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pd))
WHERE a.id_giunto IS NULL AND a.id_sc_ref IS NULL AND a.id_pd IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL;"""
    
QUERY_SC_PFS = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.scala a
LEFT JOIN
%(schema)s.pfs b ON (b.id_pfs = a.id_pfs)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_scala))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pfs))
WHERE a.id_giunto IS NULL AND a.id_sc_ref IS NULL AND a.id_pd IS NULL AND a.id_pfs IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL;"""

#DA TESTARE!!!
QUERY_GI_GI = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.giunti a
LEFT JOIN
%(schema)s.giunti b ON (a.id_g_ref = b.id_giunto)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_giunto))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_giunto))
WHERE a.id_giunto IS NOT NULL AND a.id_g_ref IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(a.tipo_giunt)!='PTA' AND upper(b.tipo_giunt)!='PTA';"""

#Da Mail di Gatti del 22 maggio 2017 e successive: abilitare tutte le connessioni Giunto-Giunto anche se sono dei PTA. Funziona ma bisogna suddividerle tra le varie tipologie..
'''
QUERY_GI_GI = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.giunti a
LEFT JOIN
%(schema)s.giunti b ON (b.id_g_ref = a.id_giunto)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_giunto))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_giunto))
WHERE a.id_giunto IS NOT NULL AND b.id_g_ref IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(a.tipo_giunt)!='PTA' AND upper(b.tipo_giunt)!='PTA'
UNION
SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.giunti a
LEFT JOIN
%(schema)s.giunti b ON (b.id_g_ref = a.id_giunto)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_giunto))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pta))
WHERE a.id_giunto IS NOT NULL AND b.id_g_ref IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(a.tipo_giunt)!='PTA' AND upper(b.tipo_giunt)='PTA'
UNION
SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.giunti a
LEFT JOIN
%(schema)s.giunti b ON (b.id_g_ref = a.id_giunto)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_pta))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pta))
WHERE a.id_giunto IS NOT NULL AND b.id_g_ref IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(a.tipo_giunt)='PTA' AND upper(b.tipo_giunt)='PTA';"""
'''

#Suddivido:
QUERY_PTA_PTA = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.giunti a
LEFT JOIN
%(schema)s.giunti b ON (a.id_g_ref = b.id_giunto)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_pta))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pta))
WHERE a.id_giunto IS NOT NULL AND a.id_g_ref IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(a.tipo_giunt)='PTA' AND upper(b.tipo_giunt)='PTA';"""

QUERY_PTA_GI = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.giunti a
LEFT JOIN
%(schema)s.giunti b ON (a.id_g_ref = b.id_giunto)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_giunto))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pta))
WHERE a.id_giunto IS NOT NULL AND a.id_g_ref IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(a.tipo_giunt)!='PTA' AND upper(b.tipo_giunt)='PTA';"""

QUERY_PTA_PD = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.giunti a
LEFT JOIN
%(schema)s.pd b ON (b.id_pd = a.id_pd)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_pta))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pd))
WHERE a.id_pd IS NOT NULL AND a.id_g_ref IS NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(a.tipo_giunt)='PTA';"""

QUERY_PTA_PFS = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.giunti a
LEFT JOIN
%(schema)s.pfs b ON (b.id_pfs = a.id_pfs)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_pta))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pfs))
WHERE a.id_pfs IS NOT NULL AND a.id_pd IS NULL AND a.id_g_ref IS NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(a.tipo_giunt)='PTA';"""

QUERY_GI_PD = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.giunti a
LEFT JOIN
%(schema)s.pd b ON (b.id_pd = a.id_pd)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_giunto))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pd))
WHERE a.id_pd IS NOT NULL AND a.id_g_ref IS NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL AND upper(a.tipo_giunt)!='PTA';"""

QUERY_PD_PD = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.pd a
LEFT JOIN
%(schema)s.pd b ON (a.id_pd_ref = b.id_pd)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_pd))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pd))
WHERE a.id_pd IS NOT NULL AND a.id_pd_ref IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL;"""

QUERY_PD_PFS = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.pd a
LEFT JOIN
%(schema)s.pfs b ON (b.id_pfs = a.id_pfs)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_pd))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pfs))
WHERE a.id_pfs IS NOT NULL AND a.id_pd_ref IS NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL;"""

QUERY_PFS_PFP = """SELECT c.id_pgr AS source, d.id_pgr AS target, a.n_ui FROM %(schema)s.pfs a
LEFT JOIN
%(schema)s.pfp b ON (b.id_pfp = a.id_pfp)
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array c ON (a.gid = ANY (c.gid_pfs))
LEFT JOIN
%(schema)s.pgrvertices_netpoints_array d ON (b.gid = ANY (d.gid_pfp))
WHERE a.id_pfp IS NOT NULL AND c.id_pgr IS NOT NULL AND d.id_pgr IS NOT NULL;"""

def recupero_ui_cavo(dest_dir, self, theSchema, epsg_srid):
    Utils.logMessage(dest_dir)
    test_conn = None
    
    test_conn = psycopg2.connect(dest_dir)
    cur_clean  = test_conn.cursor()
    cur_sc_pta = test_conn.cursor()
    cur_sc_gi = test_conn.cursor()
    cur_sc_pd = test_conn.cursor()
    cur_sc_pfs = test_conn.cursor()
    cur_pta_pd = test_conn.cursor()
    cur_gi_gi = test_conn.cursor()
    cur_gi_pd = test_conn.cursor()
    cur_pd_pfs = test_conn.cursor()
    cur_pfs_pfp = test_conn.cursor()
    cur_associa_sc_pta = test_conn.cursor()
    cur_associa_sc_gi = test_conn.cursor()
    cur_associa_sc_pd = test_conn.cursor()
    cur_associa_sc_pfs = test_conn.cursor()
    cur_associa_pta_pd = test_conn.cursor()
    cur_associa_gi_gi = test_conn.cursor()
    cur_associa_gi_pd = test_conn.cursor()
    cur_associa_pd_pfs = test_conn.cursor()
    cur_associa_pfs_pfp = test_conn.cursor()
    cur_update = test_conn.cursor()
    cur_update_fibre = test_conn.cursor()
        
    #Secondo me potresti lanciare queste funzioni a STEP dall'utente, cosi' se ci sono errori di qualsiasi tipo puo' metter mano, e non imballa il sistema.
    #creo delle variabili in cui stocco le coppie source-target che non restituiscono valori validi nel routing, plausibilmente perche' il layer cavo e' mal costruito:
    dict_null_id = dict()
    dict_null_id_not_empty = 0

    #controllo se vi e' qualche elemento con n_ui=0 o NULL e blocco la procedura:
    msg = QMessageBox()
    query_nui = "SELECT count(*) FROM %s.scala WHERE n_ui IS NULL;" % (theSchema)
    cur_sc_pta.execute(query_nui)
    results_nui = cur_sc_pta.fetchone()
    if (results_nui[0]>0):
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Uno o piu' elementi SCALA risulta avere n_ui NULL. Alcuni risultati potrebbero essere inaspettati. Non e' possibile procedere. Riprovare a lanciare il routing correggendo gli elementi SCALA con n-ui NULL, sapendo che questa modifica non verra' riportata agli elementi a valle a cui la SCALA e' eventualmente associata.")
        msg.setWindowTitle("Errore: n_ui su SCALA con valore NULL")
        msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        return 4
    
    query_nui = "SELECT count(*) FROM %s.scala WHERE n_ui<=0;" % (theSchema)
    cur_sc_pta.execute(query_nui)
    results_nui = cur_sc_pta.fetchone()
    if (results_nui[0]>0):
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Uno o piu' elementi SCALA risulta avere n_ui<=0. Alcuni risultati potrebbero essere inaspettati. Si desidera proseguire comunque?")
        #msg.setInformativeText(messaggio_warning)
        #msg.setDetailedText("The details are as follows:")
        #msg.buttonClicked.connect(msgbtn)
        msg.setWindowTitle("Problema sulle n_ui: continuare?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
            Utils.logMessage("Calcolo delle fibre non effettuato per scelta dell'utente")
            return 3
                
    msg.setIcon(QMessageBox.Information)
    msg.setText("Il programma impieghera' un po' di tempo ad eseguire il routing: non chiudere il programma, e avere pazienza...")
    msg.setWindowTitle("Elaborazione in corso...")
    msg.setStandardButtons(QMessageBox.Ok)
    retval = msg.exec_()
    
    #Per prima cosa correggo le geometrie del cavo:
    query_clean = "UPDATE %s.cavo set geom=ST_MakeValid(geom); DELETE FROM %s.cavo WHERE length_m IS NULL;" % (theSchema, theSchema)
    cur_clean.execute(query_clean)
    test_conn.commit()
    
    try:
        #SCALA-SCALA:
        id_associazione = 'SCALA_SCALA'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing SCALA-SCALA - test')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_sc_pta.execute(query_scala)
        #results_scala = cur_sc_pta.fetchone()
        for results_scala in cur_sc_pta:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            if results_scala[2] is not None: #poiche' se le n_ui sono ZERO le pone a None e non va bene
                n_ui = results_scala[2]
            else:
                n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                    SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            #Utils.logMessage(query_cavoroute)
            #se vi e' un errore nella geometria del cavo questa query inserisce un record in cavoroute anche se i campi source-target-singlegeom sono vuoti...
            #Utils.logMessage("query cavoroute: " + query_cavoroute)
            cur_associa_sc_pta.execute(query_cavoroute)
            test_conn.commit()
            #associo e calcolo le fibre - recupero ID dei cavi che compongono cavoroute:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
              SELECT gid AS id,
              source,
              target,
              length_m AS cost
              FROM %s.cavo',
              %i, %i, false, false);""" % (theSchema, id_source, id_target)
            #ATTENZIONE! Se questa query NON RESTITUISCE niente, vuol dire molto probabilmente che vi e' un problema nella geometria del layer CAVO! Ad esempio la linea del cavo non e' stata spezzata in prossimita di un vertice. Devo restituire questo errore, e se riesco l'id del cavo o almeno l'id dei punti che NON SONO RIUSCITO A COLLEGARE
            cur_associa_sc_pta.execute(query_associa)
            results_associacavo_dict = cur_associa_sc_pta.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                #Utils.logMessage("query update_ui: " + query_update_ui)
                cur_update.execute(query_update_ui)
                #A questo punto incrementare le UI non ti serve poi a molto, se non forse alla fine. DEVI SUBITO CALCOLARE LE FIBRE!! Sui cavi appena trovati
                
                #Da mail di GATTI del 27 gennaio: "I CAVI CHE DALLE SCALE FINO A 3 UI NON VANNO POSATI, VEDO IO POI DI ESCLUDERLI" o meglio "devi solo escludere il calcolo dei cavi dal contatore al PTA". Spero si riferisca a questo...
                #Da mail di Gatti del 07 Mar 2017: devo reinserire questo calcolo! Ponendo pero' sempre 12 fibre. Modificando la variabile FIBRE_CAVO e cosi' la tabella variabili_progetto dovrebbe venire in automatico questa associazione con le f_12.
                #Da mail di Gatti del 15 Mar 2017: escludo connessioni Contatore-PTA se tipo_posa=AEREA --> vedi modifica alla funzione new_update_fibre
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #Utils.logMessage('Rimaste ' + str(n_ui_rimaste) + ' UI scala-SCALA')
                #Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)
                
                test_conn.commit()
        #cur_sc_pta.close()
        #cur_associa_sc_pta.close()
        #Utils.logMessage("Source and target orphanes ID: " + str(source_null_id) + " - " + str(target_null_id) + "SCALA-SCALA")
        Utils.logMessage('Fine routing SCALA-SCALA')
        
        #SCALA-PTA:
        id_associazione = 'SCALA_PTA'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing SCALA-PTA - test')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_sc_pta.execute(query_scala)
        #results_scala = cur_sc_pta.fetchone()
        for results_scala in cur_sc_pta:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            if results_scala[2] is not None: #poiche' se le n_ui sono ZERO le pone a None e non va bene
                n_ui = results_scala[2]
            else:
                n_ui = results_scala[2] or None
            Utils.logMessage('id_source=' + str(id_source) + ' id_target='+str(id_target) + ' n_ui='+str(n_ui))
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString,%i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                    SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            Utils.logMessage(query_cavoroute)
            #se vi e' un errore nella geometria del cavo questa query inserisce un record in cavoroute anche se i campi source-target-singlegeom sono vuoti...
            #Utils.logMessage("query cavoroute: " + query_cavoroute)
            cur_associa_sc_pta.execute(query_cavoroute)
            test_conn.commit()
            #associo e calcolo le fibre - recupero ID dei cavi che compongono cavoroute:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
              SELECT gid AS id,
              source,
              target,
              length_m AS cost
              FROM %s.cavo',
              %i, %i, false, false);""" % (theSchema, id_source, id_target)
            #ATTENZIONE! Se questa query NON RESTITUISCE niente, vuol dire molto probabilmente che vi e' un problema nella geometria del layer CAVO! Ad esempio la linea del cavo non e' stata spezzata in prossimita di un vertice. Devo restituire questo errore, e se riesco l'id del cavo o almeno l'id dei punti che NON SONO RIUSCITO A COLLEGARE
            cur_associa_sc_pta.execute(query_associa)
            results_associacavo_dict = cur_associa_sc_pta.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                #Utils.logMessage("query update_ui: " + query_update_ui)
                cur_update.execute(query_update_ui)
                #A questo punto incrementare le UI non ti serve poi a molto, se non forse alla fine. DEVI SUBITO CALCOLARE LE FIBRE!! Sui cavi appena trovati
                
                #Da mail di GATTI del 27 gennaio: "I CAVI CHE DALLE SCALE FINO A 3 UI NON VANNO POSATI, VEDO IO POI DI ESCLUDERLI" o meglio "devi solo escludere il calcolo dei cavi dal contatore al PTA". Spero si riferisca a questo...
                #Da mail di Gatti del 07 Mar 2017: devo reinserire questo calcolo! Ponendo pero' sempre 12 fibre. Modificando la variabile FIBRE_CAVO e cosi' la tabella variabili_progetto dovrebbe venire in automatico questa associazione con le f_12.
                #Da mail di Gatti del 15 Mar 2017: escludo connessioni Contatore-PTA se tipo_posa=AEREA --> vedi modifica alla funzione new_update_fibre
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #Utils.logMessage('Rimaste ' + str(n_ui_rimaste) + ' UI scala-PTA')
                #Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)
                
                test_conn.commit()
        cur_sc_pta.close()
        cur_associa_sc_pta.close()
        #Utils.logMessage("Source and target orphanes ID: " + str(source_null_id) + " - " + str(target_null_id) + "SCALA-PTA")
        Utils.logMessage('Fine routing SCALA-PTA')
        
        #SCALA-GIUNTO:
        id_associazione = 'SCALA_GIUNTO'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing SCALA-GIUNTO')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_sc_gi.execute(query_scala)
        #results_scala = cur_sc_gi.fetchone()
        for results_scala in cur_sc_gi:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            if results_scala[2] is not None: #poiche' se le n_ui sono ZERO le pone None e non va bene
                n_ui = results_scala[2]
            else:
                n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                    SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f ) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            #Utils.logMessage("query cavoroute: " + query_cavoroute)
            cur_associa_sc_gi.execute(query_cavoroute)
            test_conn.commit()
            #associo e calcolo le fibre:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
              SELECT gid AS id,
              source,
              target,
              length_m AS cost
              FROM %s.cavo',
              %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_sc_gi.execute(query_associa)
            results_associacavo_dict = cur_associa_sc_gi.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                #Utils.logMessage("query update_ui: " + query_update_ui)
                cur_update.execute(query_update_ui)
                #A questo punto incrementare le UI non ti serve poi a molto, se non forse alla fine. DEVI SUBITO CALCOLARE LE FIBRE!! Sui cavi appena trovati
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)
                test_conn.commit()
        cur_sc_gi.close()
        cur_associa_sc_gi.close()
        Utils.logMessage('Fine routing SCALA-GIUNTO')
        
        #SCALA-PD:
        id_associazione = 'SCALA_PD'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing SCALA-PD')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_sc_pd.execute(query_scala)
        #results_scala = cur_sc_pd.fetchone()
        for results_scala in cur_sc_pd:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            if results_scala[2] is not None: #poiche' se le n_ui sono ZERO le pone None e non va bene
                n_ui = results_scala[2]
            else:
                n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                    SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_sc_pd.execute(query_cavoroute)
            test_conn.commit()
            #associo e calcolo le fibre:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
              SELECT gid AS id,
              source,
              target,
              length_m AS cost
              FROM %s.cavo',
              %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_sc_pd.execute(query_associa)
            results_associacavo_dict = cur_associa_sc_pd.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                #Utils.logMessage(query_update_ui)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)
                test_conn.commit()
        cur_sc_pd.close()
        cur_associa_sc_pd.close()
        Utils.logMessage('Fine routing SCALA-PD')
        
        #SCALA-PFS:
        id_associazione = 'SCALA_PFS'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing SCALA-PFS')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_sc_pfs.execute(query_scala)
        #results_scala = cur_sc_pfs.fetchone()
        for results_scala in cur_sc_pfs:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            if results_scala[2] is not None: #poiche' se le n_ui sono ZERO le pone None e non va bene
                n_ui = results_scala[2]
            else:
                n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_sc_pfs.execute(query_cavoroute)
            test_conn.commit()
            #associo e calcolo le fibre:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
              SELECT gid AS id,
              source,
              target,
              length_m AS cost
              FROM %s.cavo',
              %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_sc_pfs.execute(query_associa)
            results_associacavo_dict = cur_associa_sc_pfs.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                #Utils.logMessage(query_update_ui)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)
                test_conn.commit()
        
        #Aggiorno il campo sulla tabella variabili_progetto per probabili usi futuri:
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_scale_fibre=1;" % (theSchema)
        cur_sc_pfs.execute(query_ok)
        test_conn.commit()
        
        cur_sc_pfs.close()
        cur_associa_sc_pfs.close()
        Utils.logMessage('Fine routing SCALA-PFS')
    except psycopg2.Error, e:
        Utils.logMessage(e.pgcode + e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if (len(dict_null_id['SCALA_PTA'])>0) | (len(dict_null_id['SCALA_GIUNTO'])>0) | (len(dict_null_id['SCALA_PD'])>0) | (len(dict_null_id['SCALA_PFS'])>0): #occhio perche' cosi' come scritta dentro vi e' sempre qualcosa!!
            result_text = "STEPS SCALA-PTA, SCALA-GIUNTO, SCALA-PD, SCALA-PFS: Calcolo delle fibre nei cavi effettuato ma CON QUALCHE ERRORE: alcune CAVI non sono stati trovati nell'associare le SCALE. Vedere il log..."
        else:
            result_text = 'STEPS SCALA-PTA, SCALA-GIUNTO, SCALA-PD, SCALA-PFS: Calcolo delle fibre nei cavi realizzato con successo!'
        Utils.logMessage(result_text)
        self.dlg_solid.txtFeedback.setText(result_text)
        #return 1
    #finally:
    #    if test_conn:
    #        test_conn.close()
    
    try:
        #PTA-PFS:
        id_associazione = 'PTA_PFS'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing PTA-PFS')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_pta_pd.execute(query_scala)
        #results_scala = cur_pta_pd.fetchone()
        for results_scala in cur_pta_pd:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_pta_pd.execute(query_cavoroute)
            test_conn.commit()
            #associo le fibre:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
              SELECT gid AS id,
              source,
              target,
              length_m AS cost
              FROM %s.cavo',
              %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_pta_pd.execute(query_associa)
            results_associacavo_dict = cur_associa_pta_pd.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #DA MAIL DI GATTI DEL 4 NOVEMBRE 2016: su questa rete, detta anche "rete di drop", NON ciclo piu' ma assegno tutte le fibre al primo giro!
                test_conn.commit()

        #cur_associa_pta_pd.close()
        Utils.logMessage('Fine routing PTA-PFS')
        
        
        #PTA-PD:
        id_associazione = 'PTA_PD'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing PTA-PD')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_pta_pd.execute(query_scala)
        #results_scala = cur_pta_pd.fetchone()
        for results_scala in cur_pta_pd:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_pta_pd.execute(query_cavoroute)
            test_conn.commit()
            #associo le fibre:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
              SELECT gid AS id,
              source,
              target,
              length_m AS cost
              FROM %s.cavo',
              %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_pta_pd.execute(query_associa)
            results_associacavo_dict = cur_associa_pta_pd.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #DA MAIL DI GATTI DEL 4 NOVEMBRE 2016: su questa rete, detta anche "rete di drop", NON ciclo piu' ma assegno tutte le fibre al primo giro!
                '''#Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = update_fibre_pd_pfs(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, 'PTA_PD')'''
                test_conn.commit()

        #cur_associa_pta_pd.close()
        Utils.logMessage('Fine routing PTA-PD')
        
        #PTA-PTA:
        id_associazione = 'PTA_PTA'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing PTA-PTA')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_pta_pd.execute(query_scala)
        #results_scala = cur_pta_pd.fetchone()
        for results_scala in cur_pta_pd:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_pta_pd.execute(query_cavoroute)
            test_conn.commit()
            #associo le fibre:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
              SELECT gid AS id,
              source,
              target,
              length_m AS cost
              FROM %s.cavo',
              %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_pta_pd.execute(query_associa)
            results_associacavo_dict = cur_associa_pta_pd.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #DA MAIL DI GATTI DEL 4 NOVEMBRE 2016: su questa rete, detta anche "rete di drop", NON ciclo piu' ma assegno tutte le fibre al primo giro!
                '''#Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = update_fibre_pd_pfs(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)'''
                test_conn.commit()
        Utils.logMessage('Fine routing PTA-PTA')
        
        #PTA-GIUNTO:
        id_associazione = 'PTA_GIUNTO'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing PTA-GIUNTO')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_pta_pd.execute(query_scala)
        #results_scala = cur_pta_pd.fetchone()
        for results_scala in cur_pta_pd:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_pta_pd.execute(query_cavoroute)
            test_conn.commit()
            #associo le fibre:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
              SELECT gid AS id,
              source,
              target,
              length_m AS cost
              FROM %s.cavo',
              %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_pta_pd.execute(query_associa)
            results_associacavo_dict = cur_associa_pta_pd.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #DA MAIL DI GATTI DEL 4 NOVEMBRE 2016: su questa rete, detta anche "rete di drop", NON ciclo piu' ma assegno tutte le fibre al primo giro!
                '''#Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = update_fibre_pd_pfs(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)'''
                test_conn.commit()
        cur_associa_pta_pd.close()
        Utils.logMessage('Fine routing PTA-GIUNTO')
        
        #Aggiorno il campo sulla tabella variabili_progetto per probabili usi futuri:
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_pta_fibre=1;" % (theSchema)
        cur_pta_pd.execute(query_ok)
        test_conn.commit()
        cur_pta_pd.close()
        
    except psycopg2.Error, e:
        Utils.logMessage(e.pgcode + e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if len(dict_null_id[id_associazione])>0: #occhio perche' cosi' come scritta dentro vi e' sempre qualcosa!!
            result_text = "STEPS PTA-PD, PTA-PTA e PTA-GIUNTO: Calcolo delle fibre nei cavi effettuato ma CON QUALCHE ERRORE: alcune CAVI non sono stati trovati nell'associare i GIUNTI. Vedere il log..."
        else:
            result_text = 'STEPS PTA-PD, PTA-PTA e PTA-GIUNTO: Calcolo delle fibre nei cavi realizzato con successo!'
        Utils.logMessage(result_text)
        self.dlg_solid.txtFeedback.setText(result_text)

    
    try:
        #GIUNTO-GIUNTO:
        id_associazione = 'GIUNTO_GIUNTO'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing GIUNTO-GIUNTO')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_gi_gi.execute(query_scala)
        #results_scala = cur_gi_gi.fetchone()
        for results_scala in cur_gi_gi:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_gi_gi.execute(query_cavoroute)
            test_conn.commit()
            #associo le fibre:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
              SELECT gid AS id,
              source,
              target,
              length_m AS cost
              FROM %s.cavo',
              %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_gi_gi.execute(query_associa)
            results_associacavo_dict = cur_associa_gi_gi.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #DA MAIL DI GATTI DEL 4 NOVEMBRE 2016: su questa rete, detta anche "rete di drop", NON ciclo piu' ma assegno tutte le fibre al primo giro!
                '''#Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = update_fibre_pd_pfs(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)'''
                test_conn.commit()
        cur_gi_gi.close()
        cur_associa_gi_gi.close()
        Utils.logMessage('Fine routing GIUNTO-GIUNTO')
        
        #GIUNTO-PD:
        id_associazione = 'GIUNTO_PD'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing GIUNTO-PD')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_gi_pd.execute(query_scala)
        #results_scala = cur_gi_pd.fetchone()
        for results_scala in cur_gi_pd:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_gi_pd.execute(query_cavoroute)
            test_conn.commit()
            #associo le fibre:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
            SELECT gid AS id,
            source,
            target,
            length_m AS cost
            FROM %s.cavo',
            %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_gi_pd.execute(query_associa)
            results_associacavo_dict = cur_associa_gi_pd.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #DA MAIL DI GATTI DEL 4 NOVEMBRE 2016: su questa rete, detta anche "rete di drop", NON ciclo piu' ma assegno tutte le fibre al primo giro!
                '''#Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = update_fibre_pd_pfs(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)'''
                test_conn.commit()
        
        cur_associa_gi_pd.close()
        Utils.logMessage('Fine routing GIUNTO-PD')
        
        #Aggiorno il campo sulla tabella variabili_progetto per probabili usi futuri:
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_giunti_fibre=1;" % (theSchema)
        cur_gi_pd.execute(query_ok)
        test_conn.commit()
        cur_gi_pd.close()
        
    except psycopg2.Error, e:
        Utils.logMessage(e.pgcode + e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if (len(dict_null_id['GIUNTO_GIUNTO'])>0) | (len(dict_null_id['GIUNTO_PD'])>0): #occhio perche' cosi' come scritta dentro vi e' sempre qualcosa!!
            result_text = "STEPS GIUNTO-GIUNTO, GIUNTO-PD: Calcolo delle fibre nei cavi effettuato ma CON QUALCHE ERRORE: alcune CAVI non sono stati trovati nell'associare i GIUNTI. Vedere il log..."
        else:
            result_text = 'STEPS GIUNTO-GIUNTO, GIUNTO-PD: Calcolo delle fibre nei cavi realizzato con successo!'
        Utils.logMessage(result_text)
        self.dlg_solid.txtFeedback.setText(result_text)
        #return 1
    #finally:
    #    if test_conn:
    #        test_conn.close()
    

    try:
        #PD-PD:
        id_associazione = 'PD_PD'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing PD-PD')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_pd_pfs.execute(query_scala)
        for results_scala in cur_pd_pfs:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_pd_pfs.execute(query_cavoroute)
            test_conn.commit()
            #associo:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
            SELECT gid AS id,
            source,
            target,
            length_m AS cost
            FROM %s.cavo',
            %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_pd_pfs.execute(query_associa)
            results_associacavo_dict = cur_associa_pd_pfs.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #DA MAIL DI GATTI DEL 4 NOVEMBRE 2016: su questa rete, detta anche "rete di drop", NON ciclo piu' ma assegno tutte le fibre al primo giro!
                '''#Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = update_fibre_pd_pfs(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)'''
                test_conn.commit()
                
        #Aggiorno il campo sulla tabella variabili_progetto per probabili usi futuri:
        #query_ok = "UPDATE %s.variabili_progetto_return SET routing_pd_fibre=1;" % (theSchema.replace('lotto_', ''))
        #cur_pd_pfs.execute(query_ok)
        #test_conn.commit()
        
        #PD-PFS:
        id_associazione = 'PD_PFS'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing PD-PFS')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_pd_pfs.execute(query_scala)
        for results_scala in cur_pd_pfs:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_pd_pfs.execute(query_cavoroute)
            test_conn.commit()
            #associo:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
            SELECT gid AS id,
            source,
            target,
            length_m AS cost
            FROM %s.cavo',
            %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_pd_pfs.execute(query_associa)
            results_associacavo_dict = cur_associa_pd_pfs.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = new_update_fibre(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                #DA MAIL DI GATTI DEL 4 NOVEMBRE 2016: su questa rete, detta anche "rete di drop", NON ciclo piu' ma assegno tutte le fibre al primo giro!
                '''#Provo a rendere questa formula potenzialmente accettante un numero infinito di UI:
                while n_ui_rimaste>0:
                    n_ui_rimaste = update_fibre_pd_pfs(self, test_conn, cur_update_fibre, n_ui_rimaste, id_cavo, theSchema, id_associazione)'''
                test_conn.commit()
                
        #Aggiorno il campo sulla tabella variabili_progetto per probabili usi futuri:
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_pd_fibre=1;" % (theSchema.replace('lotto_', ''))
        cur_pd_pfs.execute(query_ok)
        test_conn.commit()
        
        cur_pd_pfs.close()
        cur_associa_pd_pfs.close()
        Utils.logMessage('Fine routing PD-PFS')
    except psycopg2.Error, e:
        Utils.logMessage(e.pgcode + e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if len(dict_null_id[id_associazione])>0: #occhio perche' cosi' come scritta dentro vi e' sempre qualcosa!!
            result_text = "STEPS PD-PFS: Calcolo delle fibre nei cavi effettuato ma CON QUALCHE ERRORE: alcune CAVI non sono stati trovati nell'associare i PD. Vedere il log..."
        else:
            result_text = 'STEPS PD-PFS: Calcolo delle fibre nei cavi realizzato con successo!'
        Utils.logMessage(result_text)
        self.dlg_solid.txtFeedback.setText(result_text)
        #return 1
    #finally:
    #    if test_conn:
    #        test_conn.close()
    

    try:
        #PFS-PFP:
        id_associazione = 'PFS_PFP'
        dict_null_id[id_associazione] = []
        Utils.logMessage('Inizio routing PFS-PFP')
        query_scala = eval(QUERY_FROM_TO_NAME[id_associazione]) % {'schema': theSchema}
        cur_pfs_pfp.execute(query_scala)
        for results_scala in cur_pfs_pfp:
            id_source = results_scala[0] or None
            id_target = results_scala[1] or None #[2, 4, 5, 428, 1224]
            n_ui = results_scala[2] or None
            #Mentre ciclo in queste connessioni creo "cavoroute":
            query_cavoroute = """INSERT INTO %s.cavoroute (net_type, source, target, geom, tipo_posa)
                SELECT '%s', max(t3.source) AS source, max(t3.target) AS target, ST_CollectionExtract(ST_Multi(ST_Collect(t3.geom)),2)::geometry(MultiLineString, %i) as singlegeom
                , array_agg(DISTINCT grp||'@'||tipo_posa||'@'||atm) AS tipo_posa
                FROM (
                SELECT t2.*, round( (sum(length_m) OVER (PARTITION BY t2.grp))::numeric, 2) AS atm
                FROM (
                SELECT
                f.*, sum(group_flag) OVER (ORDER BY f.seq) AS grp
                FROM (
                SELECT b.geom::geometry(MultiLineString, %i)
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq) AS source 
                ,first_value(id1) OVER (PARTITION BY 1 ORDER BY seq DESC) AS target
                ,seq, tipo_posa, case when lag(tipo_posa) OVER (ORDER BY seq) = tipo_posa THEN null ELSE 1 end group_flag, length_m
                FROM pgr_dijkstra('
                    SELECT gid AS id, source, target, length_m AS cost FROM %s.cavo',
                    %i, %i, false, false) AS a
                LEFT JOIN %s.cavo as b
                ON (id2 = gid) ORDER BY seq
            ) As f) AS t2) AS t3;""" % (theSchema, self.NET_TYPE[id_associazione], epsg_srid, epsg_srid, theSchema, id_source, id_target, theSchema)
            cur_associa_pfs_pfp.execute(query_cavoroute)
            test_conn.commit()
            #associo:
            query_associa = """SELECT id2 FROM pgr_dijkstra('
            SELECT gid AS id,
            source,
            target,
            length_m AS cost
            FROM %s.cavo',
            %i, %i, false, false);""" % (theSchema, id_source, id_target)
            cur_associa_pfs_pfp.execute(query_associa)
            results_associacavo_dict = cur_associa_pfs_pfp.fetchall()
            if not results_associacavo_dict: #result list is empty
                dict_null_id[id_associazione].append([id_source, id_target])
                dict_null_id_not_empty += 1
            for results_associacavo in results_associacavo_dict:            
                id_cavo = results_associacavo[0] or None
                #aggiorno UI cavo:
                query_update_ui = "UPDATE %s.cavo SET n_ui=n_ui+%i WHERE gid=%i;" % (theSchema, n_ui, id_cavo)
                cur_update.execute(query_update_ui)
                #Calcolo subito le fibre:
                n_ui_rimaste = update_fibre_pfs_pfp(self, test_conn, cur_update_fibre, n_ui, id_cavo, theSchema, id_associazione)
                '''if (n_ui_rimaste>0):
                    #Da PFS a PFP a quanto pare sempre e solo 1 cavo da 96 fibre, dunque finisce qui il giro:
                    Utils.logMessage('Rimaste ' + str(n_ui_rimaste) + ' UI pfs-pfp')'''
                test_conn.commit()
                
        #Aggiorno il campo sulla tabella variabili_progetto per probabili usi futuri:
        query_ok = "UPDATE %s.variabili_progetto_return SET routing_pfs_fibre=1;" % (theSchema.replace('lotto_', ''))
        cur_pfs_pfp.execute(query_ok)
        test_conn.commit()
        
        cur_pfs_pfp.close()
        cur_associa_pfs_pfp.close()
        Utils.logMessage('Fine routing PFS-PFP')
    except psycopg2.Error, e:
        Utils.logMessage(e.pgcode + e.pgerror)
        self.dlg_solid.txtFeedback.setText(e.pgerror)
        return 0;
    except SystemError, e:
        Utils.logMessage('Errore di sistema!')
        self.dlg_solid.txtFeedback.setText('Errore di sistema!')
        return 0
    else:
        if len(dict_null_id[id_associazione])>0: #occhio perche' cosi' come scritta dentro vi e' sempre qualcosa!!
            result_text = "STEPS PFS-PFP: Calcolo delle fibre nei cavi effettuato ma CON QUALCHE ERRORE: alcune CAVI non sono stati trovati nell'associare i PFS. Vedere il log..."
        else:
            result_text = 'STEPS PFS-PFP: Calcolo delle fibre nei cavi realizzato con successo!'
        Utils.logMessage(result_text)
        self.dlg_solid.txtFeedback.setText(result_text)
        #return 1
    #finally:
    #    if test_conn:
    #        test_conn.close()

    
    '''vecchia procedura sostituita ad mail del 31 ottobre 2017
    #NOTA MAIL GATTI del 20-21-23 Febbraio 2017: devo aggiungere delle f_192 in base al contenuto del campo codice_ins:
    #query_codice_ins = "UPDATE %s.cavo SET f_192 = CASE WHEN upper(codice_ins)='PR' THEN f_192+1 WHEN upper(codice_ins)='PR+BH' THEN f_192+2 ELSE f_192 END;" % (theSchema)
    #NOTA MAIL GATTI del 19 Aprile 2017: aggiungo ancora UN f_192 se solo BH:
    query_codice_ins = "UPDATE %s.cavo SET f_192 = CASE WHEN upper(codice_ins)='PR' THEN f_192+1 WHEN upper(codice_ins)='PR+BH' THEN f_192+2 WHEN upper(codice_ins)='BH' THEN f_192+1 ELSE f_192 END;" % (theSchema)
    cur_update.execute(query_codice_ins)
    
    #Restano ancora da calcolare i cavi e le fibre:
    query_update_cavi = "UPDATE %s.cavo SET tot_cavi=f_4+f_12+f_24+f_48+f_72+f_96+f_144+f_192;" % (theSchema)
    cur_update.execute(query_update_cavi)   
    '''
    #NUOVA RISCHIESTA MAIL GATTI del 24 Ottobre 2017: ricalcolo f_192 e altri campi in base ad altri criteri - DA SVILUPPARE E APPROFONDIRE!!
    #Da mail di Gatti del 31 Ottobre 2017: tot_cavi1, tot_cavi2, tot_cavicd: messi a mano dal progettista
    #Da mail di Gatti del 31 Ottobre 2017: "cavi_pr", "cavi_bh", "cavi_cd": messi a mano dal progettista
    query_tot_cavi = "UPDATE %s.cavo SET tot_cavi = tot_cavi1 + tot_cavi2 + tot_cavicd;" % (theSchema)
    cur_update.execute(query_tot_cavi)
    test_conn.commit()
    
    query_codice_ins = "UPDATE %s.cavo SET f_192 = cavi_pr + cavi_bh + cavi_cd;" % (theSchema)
    cur_update.execute(query_codice_ins)
    test_conn.commit()
    
    query_cavi2 = """UPDATE %s.cavo SET cavi2 = CASE
        WHEN (cavi_pr + cavi_bh + cavi_cd)=0 THEN tot_cavi
        WHEN (cavi_pr + cavi_bh + cavi_cd)>0 THEN f_4 + f_12  + f_24  + f_48  + f_72  + f_96  + f_144
    END;""" % (theSchema)
    cur_update.execute(query_cavi2)
    test_conn.commit()
    
    '''
    #vecchie query della mail del 24 ottobre 2017 ridefinite dalla mail del 31 ottobre 2017:
    query_flag_no = "UPDATE %s.cavo SET n_mt_occ = (tot_cavi1 + tot_cavi2 + tot_cavicd + 2)::text || 'x7', n_mt_occ_1=0, n_mt_occ_2=0, n_mt_occ_cd=0 WHERE UPPER(flag_posa) LIKE '%NO%';" % (theSchema)
    cur_update.execute(query_flag_no)
    test_conn.commit()
    
    query_flag_si = """UPDATE %s.cavo SET 
        n_mt_occ_1 = CASE
        WHEN tot_cavi1+tot_cavicd < 6 THEN '1x7'
        WHEN tot_cavi1+tot_cavicd < 13 THEN '2x7'
        ELSE '3x7'
        END,
        n_mt_occ_2 = CASE
        WHEN tot_cavi2+2 < 6 THEN '1x7'
        WHEN tot_cavi2+2 < 13 THEN '2x7'
        ELSE '3x7'
        END
    WHERE UPPER(flag_posa) LIKE '%SI%';""" % (theSchema)
    cur_update.execute(query_flag_si)
    test_conn.commit()
    
    #in questo caso per compilare n_mt_occ prendo la prima cifra dei campi n_mt_occ_1 e n_mt_occ_2:
    query_flag_si2 = """UPDATE %s.cavo SET 
        n_mt_occ = (substr(n_mt_occ_1, 1, 1)::integer + substr(n_mt_occ_2, 1, 1)::integer) || 'x7'
    WHERE UPPER(flag_posa) LIKE '%SI%';""" % (theSchema)
    cur_update.execute(query_flag_si2)    
    test_conn.commit()
    '''
    
    #Restano ancora da calcolare i cavi e le fibre:
    query_update_fibre = "UPDATE %s.cavo SET tot_fibre=(f_4*4)+(f_12*12)+(f_24*24)+(f_48*48)+(f_72*72)+(f_96*96)+(f_144*144)+(f_192*192);" % (theSchema)
    cur_update.execute(query_update_fibre)
    
    test_conn.commit()
    
    #MAIL GATTI/MOCCO del 19 Giugno 2017: ricalcolare alcuni campi del layer cavo in base ad alcune regole definite in un file .ods allegato alla mail.
    query_update_cavo = """
        UPDATE %s.cavo SET tipo_scavo=
        CASE
        WHEN upper(codice_inf)='MINITRINCEA' THEN 'minitrincea'
        WHEN upper(codice_inf)='TRINCEA NORMALE' THEN 'scavo tradizionale'
        END
        , tipo_minit=
        CASE
        WHEN upper(codice_inf)='NO DIG' THEN 'bandle'
        WHEN upper(codice_inf)='RACCORDO' THEN 'singolo'
        END;
    """ % (theSchema)
    cur_update.execute(query_update_cavo)
    test_conn.commit()
    
    #cur_update.close()
    #if test_conn:
    #    test_conn.close()
    
    if dict_null_id_not_empty > 0:
        Utils.logMessage("Coppie non abbinate al cavo per via probabilmente di una scorretta geometria del cavo:")
        #Utils.logMessage("SCALA_PTA IDs: " + str(dict_null_id['SCALA_PTA']))
        if len(dict_null_id['SCALA_SCALA'])>0:
            Utils.logMessage("SCALA_SCALA IDs: ")
            for SCALA_SCALA in dict_null_id['SCALA_SCALA']:
                query_SCALA_SCALA = """SELECT * FROM
                (SELECT array_to_string(gid_scala, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_scala, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(SCALA_SCALA[0]), theSchema, int(SCALA_SCALA[1]))
                cur_update.execute(query_SCALA_SCALA)
                for result_SCALA_SCALA in cur_update:
                    Utils.logMessage(result_SCALA_SCALA[0] + ' - ' + result_SCALA_SCALA[1])
        else:
            Utils.logMessage("SCALA_SCALA IDs: OK!")
        
        if len(dict_null_id['SCALA_PTA'])>0:
            Utils.logMessage("SCALA_PTA IDs: ")
            for SCALA_PTA in dict_null_id['SCALA_PTA']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_scala, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_pta, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(SCALA_PTA[0]), theSchema, int(SCALA_PTA[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("SCALA_PTA IDs: OK!")
        
        if len(dict_null_id['SCALA_GIUNTO'])>0:
            Utils.logMessage("SCALA_GIUNTO IDs: ")
            for SCALA_GIUNTO in dict_null_id['SCALA_GIUNTO']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_scala, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_giunto, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(SCALA_GIUNTO[0]), theSchema, int(SCALA_GIUNTO[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("SCALA_GIUNTO IDs: OK!")
        
        if len(dict_null_id['SCALA_PD'])>0:
            Utils.logMessage("SCALA_PD IDs: ")
            for SCALA_PD in dict_null_id['SCALA_PD']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_scala, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_pd, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(SCALA_PD[0]), theSchema, int(SCALA_PD[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("SCALA_PD IDs: OK!")
            
        if len(dict_null_id['SCALA_PFS'])>0:
            Utils.logMessage("SCALA_PFS IDs: ")
            for SCALA_PFS in dict_null_id['SCALA_PFS']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_scala, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_pfs, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(SCALA_PFS[0]), theSchema, int(SCALA_PFS[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("SCALA_PFS IDs: OK!")
            
        if len(dict_null_id['PTA_PFS'])>0:
            Utils.logMessage("PTA_PFS IDs: ")
            for PTA_PFS in dict_null_id['PTA_PFS']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_pta, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_pd, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(PTA_PFS[0]), theSchema, int(PTA_PFS[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("PTA_PFS IDs: OK!")
        
        if len(dict_null_id['PTA_PD'])>0:
            Utils.logMessage("PTA_PD IDs: ")
            for PTA_PD in dict_null_id['PTA_PD']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_pta, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_pd, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(PTA_PD[0]), theSchema, int(PTA_PD[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("PTA_PD IDs: OK!")
            
        if len(dict_null_id['PTA_PTA'])>0:
            Utils.logMessage("PTA_PTA IDs: ")
            for PTA_PTA in dict_null_id['PTA_PTA']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_pta, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_pta, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(PTA_PTA[0]), theSchema, int(PTA_PTA[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("PTA_PTA IDs: OK!")
            
        if len(dict_null_id['PTA_GIUNTO'])>0:
            Utils.logMessage("PTA_GIUNTO IDs: ")
            for PTA_GIUNTO in dict_null_id['PTA_GIUNTO']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_pta, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_giunto, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(PTA_GIUNTO[0]), theSchema, int(PTA_GIUNTO[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("PTA_GIUNTO IDs: OK!")
        
        if len(dict_null_id['GIUNTO_GIUNTO'])>0:
            Utils.logMessage("GIUNTO_GIUNTO IDs: ")
            for GIUNTO_GIUNTO in dict_null_id['GIUNTO_GIUNTO']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_giunto, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_giunto, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(GIUNTO_GIUNTO[0]), theSchema, int(GIUNTO_GIUNTO[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("GIUNTO_GIUNTO IDs: OK!")

        if len(dict_null_id['GIUNTO_PD'])>0:
            Utils.logMessage("GIUNTO_PD IDs: ")
            for GIUNTO_PD in dict_null_id['GIUNTO_PD']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_giunto, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_pd, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(GIUNTO_PD[0]), theSchema, int(GIUNTO_PD[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("GIUNTO_PD IDs: OK!")
        
        if len(dict_null_id['PD_PD'])>0:
            Utils.logMessage("PD_PD IDs: ")
            for PD_PD in dict_null_id['PD_PD']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_pd, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_pd, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(PD_PD[0]), theSchema, int(PD_PD[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("PD_PD IDs: OK!")
        
        if len(dict_null_id['PD_PFS'])>0:
            Utils.logMessage("PD_PFS IDs: ")
            for PD_PFS in dict_null_id['PD_PFS']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_pd, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_pfs, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(PD_PFS[0]), theSchema, int(PD_PFS[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("PD_PFS IDs: OK!")
        
        if len(dict_null_id['PFS_PFP'])>0:
            Utils.logMessage("PFS_PFP IDs: ")
            for PFS_PFP in dict_null_id['PFS_PFP']:
                query_SCALA_PTA = """SELECT * FROM
                (SELECT array_to_string(gid_pfs, ',') AS id_source FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS source,
                (SELECT array_to_string(gid_pfp, ',') AS id_target FROM %s.pgrvertices_netpoints_array WHERE id_pgr=%i) AS target;""" % (theSchema, int(PFS_PFP[0]), theSchema, int(PFS_PFP[1]))
                cur_update.execute(query_SCALA_PTA)
                for result_SCALA_PTA in cur_update:
                    Utils.logMessage(result_SCALA_PTA[0] + ' - ' + result_SCALA_PTA[1])
        else:
            Utils.logMessage("PFS_PFP IDs: OK!")
            
        return 2
    else:
        return 1
    
    cur_update.close()
    if test_conn:
        test_conn.close()    
