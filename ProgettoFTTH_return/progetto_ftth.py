# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProgettoFTTH
                                 A QGIS plugin
 Gestione reti elettriche ENEL
                              -------------------
        begin                : 2016-09-01
        git sha              : $Format:%H$
        copyright            : (C) 2016 by A.R.Gaeta/Vertical Srl
        email                : ar_gaeta@yahoo.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

'''
NOTE:
- all'interno della funzione recupero_ui_cavo di db_cavoroute ho introdotto la variabile dict_null_id che contiene gli id dalla tabella pgrvertices_netpoints_array che non sono stati correttamente collegati col Routing molto presumibilmente perche' la geometria del layer cavo e' scorretta. Le coppie non associate al cavo vengono riportate nel file di log
- ci sono delle moltiplicazioni di UI fatte in db_solid per popolare le n_ui di cavoroute, che non rappresentano dunque quelle reali ma le UI effettive...Da mail di Gatti del 03/02/2017

NUOVA VERSIONE - CASCATA:
- ho assunto che le regole "FROM_TO_RULES" per connettere in cascata le SCALE siano come quelle dei PTA
- nel caso di SCALA-SCALA non ho considerato alcun vincolo sui contatori tant'e' che sulla tabella non c'e' il campo n_cont... Nel caso, aggiungere la colonna in tabella ed aggiungere l'opzione relativa nella funzione "import_action"
- nella funzione "associa_cascata_scala" e "associa_cascata_pd" nonche' in quella dei "associa_padri_giunti" io mi fermo solo al PRIMO LIVELLO di connessione, dovrei invece ciclare fino a beccare TUTTI i figli...!
- ho imposto:   FIBRE_CAVO['SCALA_SCALA'] = FIBRE_CAVO['SCALA_PTA']
    FIBRE_CAVO['PD_PD'] = FIBRE_CAVO['GIUNTO_PD']
    FIBRE_CAVO['PTA_PFS'] = FIBRE_CAVO['PTA_PD']
- occorrerebbe forse a questo punto pensare ad un modo per come scollegare un punto SENZA eliminarlo...
- le SCALE non essendo possibile eliminarle non e' possibile SCOLLEGARLE!



OTTIMIZZAZIONI/DUBBI:
- "Aggiorno id del cavoroute -- ATTENZIONE!! Devo prelevare il COD_POP impostato a livello di progetto!!" Al fondo della funzione calcola_route in db_solid: come lo faccio? Al momento ho commentato le righe per non avere errore. Lo devo fare? Se si, potrei prelevare l'ID_POP da uno degli shp importati, quindi in questo script nella funzione di importazione definire la variabile self.COD_POP.
- devi ancora implementare la parte "Consolida progetto" del vecchio plugin!! Ma fallo anche alla fine, precedenza al routing.
- ATTENZIONE! Il campo num_scorte di cavoroute, quando lo creo? Perche' non esiste piu'?? Vedere verso rigo 400 db_solid.py...
- ATTENZIONE! Le variabili del progetto nella maschera del plugin al momento LE SCRIVI sulla maschera: devi riuscire a recuperarle dal DB!
- la procedura per creare le cavoroute_labels in db_solid.py e' ancora molto da verificare...
'''


#from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
#from PyQt4.QtGui import QAction, QIcon, QFileDialog
from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from progetto_ftth_dockwidget import ProgettoFTTHDockWidget
from progetto_ftth_config_dockwidget import ProgettoFTTHConfigDockWidget
from progetto_ftth_compare_dockwidget import ProgettoFTTHCompareDockWidget
from progetto_ftth_solid_dockwidget import ProgettoFTTHSolidDockWidget
from progetto_ftth_export_dockwidget import ProgettoFTTHExportDockWidget
from progetto_ftth_help_dockwidget import ProgettoFTTHHelpDockWidget
from progetto_ftth_append_dockwidget import ProgettoFTTHAppendDockWidget
#import os.path

#Importo i miei script dedicati e altre cose utili per il catasto:
#from optparse import OptionParser
from os.path import basename as path_basename
from os.path import expanduser
#import os, sys #forse importare sys, che mi serviva solo per recuperare info sul sistema, rallenta il plugin. Difatti la 3.5b che non caricava sys risulta essere meno onerosa
import os
from osgeo import ogr

#importo alcune librerie per gestione dei layer caricati
from qgis.core import *
#from qgis.core import QgsVectorLayer, QgsMapLayerRegistry
#from qgis.utils import iface, QGis #forse importare QGis, che mi serviva solo per recuperare info sul sistema, rallenta il plugin. Difatti la 3.5b che non caricava QGis risulta essere meno onerosa
from qgis.utils import iface
from qgis.gui import *

#importo altre librerie prese dal plugin pgrouting
import pgRoutingLayer_utils as Utils
#import db_utils as db_utils #ricopiavo delle funzione da pgRoutingLayer ma penso di farne a meno
#import dbConnection #ricopiavo delle funzione da pgRoutingLayer ma penso di farne a meno
import psycopg2
import psycopg2.extras
#Per aprire link web
#import webbrowser

import db_compare as db_compare
import db_solid as db_solid
import computo_metrico as computo_metrico
import numerazione_puntirete as numerazione_puntirete
#importo DockWidget
from Core_dockwidget import CoreDockWidget


class ProgettoFTTH:
    """QGIS Plugin Implementation."""
    
    #Ridefinisco la funzione selectByIds in base alla versione
    #TENTATIVO FALLITO!! Meglio usare la versione 2.18.11 new LTR
    #Qgis_sw_version = QGis.QGIS_VERSION
    #Qgis_sw_version_arr = Qgis_sw_version.split('.')
    '''global func_to_version
    func_to_version = 0
    msg = QMessageBox()
    if (int(Qgis_sw_version_arr[0]) < 2):
        msg.setText("Plugin non compatibile con questa versione di QGis!")
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Plugin non compatibile!")
        msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
    elif (int(Qgis_sw_version_arr[1]) <= 14):
        #msg.setText("Plugin per la versione " + str(Qgis_sw_version_arr[0]) + "." + str(Qgis_sw_version_arr[1]))
        QgsVectorLayer.setSelectedFeatures = QgsVectorLayer.setSelectedFeatures
        func_to_version = 1
    elif (int(Qgis_sw_version_arr[1]) >= 18):
        func_to_version = 2'''
    
    #Modificare SOLO la SECONDA voce e non la PRIMA che rappresenta l'indice di questo dictionary. La seconda voce e' il nome come da Legenda in QGis:
    LAYER_NAME = {
        'SCALA': 'Scala',
        'PTA': 'Giunti',
        'GIUNTO': 'Giunti',
        'PD': 'PD',
        'PFS': 'PFS',
        'PFP': 'PFP',
        'GIUNTO_F_dev': 'Giunti',
        'CAVO': 'Cavo',
        'CAVOROUTE': 'Cavoroute',
        'SOTTOT': 'Sottotratta',
        'Area_PFS': 'Area_PFS',
        'Area_PFP': 'Area_PFP',
        'Pozzetto': 'Pozzetto',
        'PD_F': 'PD',
        'SCALA_F': 'Scala',
        'SCALA_append': 'scala_append'
    }
    ID_NAME = {
        'SCALA': 'id_scala',
        'PTA': 'id_giunto',
        'GIUNTO': 'id_giunto',
        'PD': 'id_pd',
        'PFS': 'id_pfs',
        'PFP': 'id_pfp',
        'GIUNTO_F_dev': 'id_g_ref',
        'PD_F': 'id_pd_ref',
        'SCALA_F': 'id_sc_ref'
    }
    FROM_POINT = [
        '--seleziona--',
        LAYER_NAME['SCALA'],
        LAYER_NAME['GIUNTO'],
        LAYER_NAME['PD'],
        LAYER_NAME['PFS']
    ]
    #regole di deafult
    FROM_TO_RULES = {
        'PTA': {'MIN_UI': 0, 'MAX_UI': 44, 'MAX_CONT': 44},
        'GIUNTO': {'MIN_UI': 0, 'MAX_UI': 96, 'MAX_CONT': 8},
        'GIUNTO_F_dev': {'MIN_UI': 0, 'MAX_UI': 96, 'MAX_CONT': 8},
        'PD': {'MIN_UI': 16, 'MAX_UI': 96, 'MAX_CONT': 8},
        'PFS': {'MIN_UI': 220, 'MAX_UI': 254, 'MAX_CONT': 12},
        'PFP': {'MIN_UI': 850, 'MAX_UI': 1024, 'MAX_CONT': 4}
    }
    #Per non riscrivere il dictionary, e dunque il DB, eseguo questa uguaglianza:
    #Dopo telefonata con Gatti il mattino del 13 ottobre 2017 assegno nel caso di collegamenti in cascata tra SCALE le stesse regole del PD. Ma visto che il PD ha MIN_UI<>0 per non rischiare dei pasticci lo opngo uguale al GIUNTO
    FROM_TO_RULES['SCALA'] = FROM_TO_RULES['GIUNTO']
    '''FIBRE_CAVO = {
        'PD': {'F_4': 2, 'F_12': 10, 'F_24': 20, 'F_48': 40, 'F_72': 0, 'F_96': 0, 'F_144': 0},
        'PFS': {'F_4': 0, 'F_12': 0, 'F_24': 12, 'F_48': 36, 'F_72': 60, 'F_96': 72, 'F_144': 120}
    }'''
    FIBRE_CAVO = {
        'SCALA_PTA': {'F_4': 0, 'F_12': 3, 'F_24': 0, 'F_48': 0, 'F_72': 0, 'F_96': 0, 'F_144': 0, 'F_192': 0},
        'SCALA_GIUNTO': {'F_4': 0, 'F_12': 0, 'F_24': 10, 'F_48': 34, 'F_72': 0, 'F_96': 42, 'F_144': 0, 'F_192': 0},
        'SCALA_PD': {'F_4': 0, 'F_12': 0, 'F_24': 10, 'F_48': 34, 'F_72': 0, 'F_96': 42, 'F_144': 0, 'F_192': 0},
        'SCALA_PFS': {'F_4': 0, 'F_12': 0, 'F_24': 10, 'F_48': 34, 'F_72': 0, 'F_96': 42, 'F_144': 0, 'F_192': 0},
        'GIUNTO_PD': {'F_4': 0, 'F_12': 0, 'F_24': 10, 'F_48': 34, 'F_72': 0, 'F_96': 42, 'F_144': 0, 'F_192': 0},
        'PTA_PD': {'F_4': 0, 'F_12': 0, 'F_24': 10, 'F_48': 34, 'F_72': 0, 'F_96': 42, 'F_144': 0, 'F_192': 0},
        'PD_PFS': {'F_4': 0, 'F_12': 0, 'F_24': 16, 'F_48': 32, 'F_72': 0, 'F_96': 64, 'F_144': 96, 'F_192': 0},
        #'PFS_PFP': {'F_4': 0, 'F_12': 0, 'F_24': 0, 'F_48': 0, 'F_72': 0, 'F_96': 9999, 'F_144': 0, 'F_192': 0}
        'PFS_PFP': {'F_96': 9999}
    }
    #Per non riscrivere il dictionary, e dunque il DB, eseguo questa uguaglianza:
    FIBRE_CAVO['GIUNTO_GIUNTO'] = FIBRE_CAVO['GIUNTO_PD']
    FIBRE_CAVO['PTA_GIUNTO'] = FIBRE_CAVO['GIUNTO_PD']
    FIBRE_CAVO['PTA_PTA'] = FIBRE_CAVO['GIUNTO_PD']
    FIBRE_CAVO['PTA_PFS'] = FIBRE_CAVO['PTA_PD']
    FIBRE_CAVO['SCALA_SCALA'] = FIBRE_CAVO['SCALA_PTA']
    FIBRE_CAVO['PD_PD'] = FIBRE_CAVO['GIUNTO_PD']
    #le chiavi di net_type devono essere LE STESSE di fibre_cavo. Indicano il valore da scrivere nel layer cavoroute
    NET_TYPE = {
        'SCALA_SCALA': "Contatori-contatore",
        'SCALA_PTA': "Contatori-PTA",
        'SCALA_GIUNTO': "Contatori-giunto",
        'SCALA_PD': "Contatori-PD",
        'SCALA_PFS': "Contatori-PFS",
        'GIUNTO_GIUNTO': "Giunti-giunto",
        'GIUNTO_PD': "Giunti-PD",
        'PTA_PTA': "PTA-PTA",
        'PTA_GIUNTO': "PTA-giunto",
        'PTA_PD': "PTA-PD",
        'PTA_PFS': "PTA-PFS",
        'PD_PD': "PD-PD",
        'PD_PFS': "PD-PFS",
        'PFS_PFP': "PFS-PFP"
    }
    
    COD_POP = 0
    epsg_srid = 0

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
    
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ProgettoFTTH_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg_config = ProgettoFTTHConfigDockWidget()
        self.dlg_compare = ProgettoFTTHCompareDockWidget()
        self.dlg_solid = ProgettoFTTHSolidDockWidget()
        self.dlg_export = ProgettoFTTHExportDockWidget()
        self.dlg_append = ProgettoFTTHAppendDockWidget()
        self.dlg_help = ProgettoFTTHHelpDockWidget()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&ProgettoFTTH')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'ProgettoFTTH')
        self.toolbar.setObjectName(u'ProgettoFTTH')
        #TEST: aggiungo DockWidget
        self.pluginIsActive = False
        self.dockwidget = None
        
        #Implemento alcune azioni sui miei pulsanti
        #Scelgo che punto voglio associare e faccio partire in qualche modo il controllo sulla selezione sulla mappa:
        '''self.dlg = ProgettoFTTHDockWidget()
        self.dlg.scala_giunto_btn.clicked.connect(self.associa_scala_giunto)
        self.dlg.scala_pd_btn.clicked.connect(self.associa_scala_pd)
        self.dlg.scala_pfs_btn.clicked.connect(self.associa_scala_pfs)
        self.dlg.giunto_giunto_btn.clicked.connect(self.associa_giunto_giunto)
        self.dlg.giunto_pd_btn.clicked.connect(self.associa_giunto_pd)
        self.dlg.pd_pfs_btn.clicked.connect(self.associa_pd_pfs)
        self.dlg.pfs_pfp_btn.clicked.connect(self.associa_pfs_pfp)
        self.dlg.solid_btn_aree.clicked.connect(self.lancia_consolida_aree_dlg)'''
        
        self.dlg_compare.comboBoxFromPoint.clear()
        self.dlg_compare.fileBrowse_btn.clicked.connect(self.controlla_connessioni)
        
        #SELEZIONA CARTELLA
        self.dlg_config.dirBrowse_txt.clear()
        self.dlg_config.dirBrowse_btn.clicked.connect(self.select_output_dir)
        #Seleziono layer SCALA per inizializza un nuovo progetto da zero:
        self.dlg_config.shpBrowse_btn.clicked.connect(self.select_shp_scala)
        #self.dlg_config.cavoBrowse_btn.clicked.connect(self.select_shp_cavo)
        #Ad ogni nuova riapertura del pannello di configurazione del progetto disabilito alcuni pannelli:
        self.dlg_config.import_DB.setEnabled(False);
        self.dlg_config.variabili_DB.setEnabled(False);
        #Verifico se i dati sono o meno gia' importati sul DB escludendo la doppia scelta:
        self.dlg_config.no_import.clicked.connect(self.toggle_no_import)
        self.dlg_config.si_import.clicked.connect(self.toggle_si_import)
        self.dlg_config.si_inizializza.clicked.connect(self.toggle_si_inizializza)
        #Azioni sul tasto import per spostare gli shp su DB:
        self.dlg_config.import_shp.clicked.connect(self.import_shp2db)
        #Azioni sul taasto import_scala per inizializzare un nuovo progetto:
        self.dlg_config.import_scala.clicked.connect(self.inizializza_DB)
        
        self.dlg_export.dirBrowse_btn.clicked.connect(self.select_output_dir_export)
        self.dlg_export.exportBtn.clicked.connect(self.exportDB)
        
        self.dlg_append.shpBrowse_btn.clicked.connect(self.select_shp_scala_append)
        self.dlg_append.importBtn.clicked.connect(self.append_scala)
        self.dlg_append.importBtn_DbManager.clicked.connect(self.append_scala_DbManager)
        
        #AZIONO PULSANTE PERSONALIZZATO:
        self.dlg_config.aggiorna_variabiliBtn.clicked.connect(self.inizializzaDB)
        self.dlg_config.importBtn.clicked.connect(self.load_layers_from_db)
        
        #AZIONO pulsante per TESTARE CONNESSIONE AL DB:
        self.dlg_config.testBtn.clicked.connect(self.test_connection)
        
        #AZIONO i vari pulsanti della maschera dlg_solid:
        self.dlg_solid.calcola_fibre_btn.clicked.connect(self.lancia_calcola_fibre)
        self.dlg_solid.calcola_route_btn.clicked.connect(self.lancia_calcola_route)
        
        self.dlg_solid.start_routing_btn.clicked.connect(self.lancia_inizializza_routing)
        self.dlg_solid.associa_scale.clicked.connect(self.lancia_scale_routing)
        self.dlg_solid.associa_pta.clicked.connect(self.lancia_pta_routing)
        self.dlg_solid.associa_giunti.clicked.connect(self.lancia_giunti_routing)
        self.dlg_solid.associa_pd.clicked.connect(self.lancia_pd_routing)
        self.dlg_solid.associa_pfs.clicked.connect(self.lancia_pfs_routing)
        self.dlg_solid.associa_pfp.clicked.connect(self.lancia_pfp_routing)
        
        #Nella versione 4.4 riporto la funzione consolida_aree sotto il routing:
        self.dlg_solid.solid_btn_aree.clicked.connect(self.lancia_consolida_aree)
        #Nella versione 4.3 sostituisco questo pulsante con quello che verifica che tutti i nodi della rete siano associati:
        #self.dlg_solid.solid_btn_aree.clicked.connect(self.check_grouping_from_user)
        
        self.dlg_solid.reset_fibre_btn.clicked.connect(self.lancia_reset_all)
        self.dlg_solid.popola_cavo_btn.clicked.connect(self.lancia_popola_cavo)
        
        #Apro un link esterno per l'help - come si fa ad interagire con i pulsanti di default di QT? Mistero..
        help_button = QDialogButtonBox.Help #16777216
        Utils.logMessage('help'+str(help_button))
        #QObject.connect(self.dlg_help.help_button, SIGNAL("clicked()"), self.help_open)
        #self.dlg_help.help_button.connect(self.help_open)
        #self.dlg_help.connect(help_button, SIGNAL("clicked()"), self.help_open)
        #Richiesta di Andrea del 17/10/2017 da GitHub: rimuovo il pulsante che rimanda ad un sito esterno:
        #self.dlg_help.help_btn.clicked.connect(self.help_open)
        
        #Popolo il menu a tendina con i layer da associare:
        for frompoint in self.FROM_POINT:
            self.dlg_compare.comboBoxFromPoint.addItem(frompoint)
        #Disabilito la prima opzione - come??
        idx = self.dlg_compare.comboBoxFromPoint.findText(self.FROM_POINT[0])
        self.dlg_compare.comboBoxFromPoint.setCurrentIndex(idx)
        
        #Proviamo a disabilitare/nascondere un item:
        #self.dlg.comboBoxToPoint.setItemData(2, False, -1); #niente...
        
    def pageProcessed(self, progressBar):
        """Increment the page progressbar."""
        progressBar.setValue(progressBar.value() + 1)
    
    '''Richiesta di Andrea del 17/10/2017 da GitHub: rimuovo il pulsante che rimanda ad un sito esterno:
    def help_open(self):
        #QMessageBox.information(self.dlg_help, self.dlg_help.windowTitle(), "Ciao help!")
        url = "http://webgis.map-hosting.it/enel/Help%20Qgis%20App.pdf"
        webbrowser.open(url, new=0, autoraise=True)
    '''
    
    def toggle_no_import(self):
        tab_attivo = self.dlg_config.no_import.isChecked()
        if (tab_attivo==True):
            self.dlg_config.si_import.setChecked(False)
            self.dlg_config.si_inizializza.setChecked(False)
            self.dlg_config.variabili_DB.setEnabled(True) #attivo il toolbox delle variabili
            self.dlg_config.importBtn.setEnabled(True) #attivo il pulsante di caricamento layer da DB sulla TOC
        else:
            self.dlg_config.si_import.setChecked(True) #insomma funziona alla stregua di un radio_button
            self.dlg_config.variabili_DB.setEnabled(False)
            self.dlg_config.importBtn.setEnabled(False)
            
    def toggle_si_import(self):
        tab_attivo = self.dlg_config.si_import.isChecked()
        if (tab_attivo==True):
            self.dlg_config.no_import.setChecked(False)
            self.dlg_config.si_inizializza.setChecked(False)
            self.dlg_config.variabili_DB.setEnabled(False)
            self.dlg_config.importBtn.setEnabled(False)
        else:
            self.dlg_config.no_import.setChecked(True) #insomma funziona alla stregua di un radio_button
            self.dlg_config.variabili_DB.setEnabled(True) #attivo il toolbox delle variabili
            self.dlg_config.importBtn.setEnabled(True) #attivo il pulsante di caricamento layer da DB sulla TOC
            
    def toggle_si_inizializza(self):
        tab_attivo = self.dlg_config.si_inizializza.isChecked()
        if (tab_attivo==True):
            self.dlg_config.no_import.setChecked(False)
            self.dlg_config.si_import.setChecked(False)
            self.dlg_config.variabili_DB.setEnabled(False)
            self.dlg_config.importBtn.setEnabled(False)
        else:
            self.dlg_config.no_import.setChecked(False)
            self.dlg_config.si_import.setChecked(False)
            self.dlg_config.variabili_DB.setEnabled(False) #attivo il toolbox delle variabili
            self.dlg_config.importBtn.setEnabled(False) #attivo il pulsante di caricamento layer da DB sulla TOC
    
    def inizializza_DB(self):
        #INIZIALIZZO UN NUOVO PROGETTO DA ZERO, importando solo lo shp delle scale
        msg = QMessageBox()
        global epsg_srid
        try:
            schemaDB = self.dlg_config.schemaDB.text()
            scala_shp = self.dlg_config.shpBrowse_txt.text()
            #cavo_shp = self.dlg_config.cavoBrowse_txt.text()
            codpop = int(self.dlg_config.codpopDB.text())
            comuneDB = self.dlg_config.comuneDB.text()
            codice_lotto = self.dlg_config.lottoDB.text()
            if ( (scala_shp is None) or (scala_shp=='') ):
                raise NameError('Specificare TUTTI i nomi degli shp e il percorso di origine!')
            #if ( (cavo_shp is None) or (cavo_shp=='') ):
            #    raise NameError('Specificare TUTTI i nomi degli shp e il percorso di origine!')
            if ( len(str(codpop))> 3):
                raise NameError('COD_POP: massimo 3 cifre')
            if ( (comuneDB is None) or (comuneDB=='') or (codpop is None) or (codpop=='') or (codice_lotto is None) or (codice_lotto=='') ):
                raise NameError('Specificare COMUNE LOTTO e COD_POP!')
            if ( len(codice_lotto)> 5 ):
                raise NameError('LOTTO: massimo 5 caratteri')
            if ( len(comuneDB)>4 ):
                raise NameError('COMUNE: massimo 4 caratteri')
            #se tutto ok proseguo...
        except NameError as err:
            msg.setText(err.args[0])
            msg.setIcon(QMessageBox.Critical)
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            self.dlg_config.txtFeedback_inizializza.setText(err.args[0])
            return 0
        except ValueError:
            self.dlg_config.txtFeedback_inizializza.setText('Specificare TUTTE le variabili')
            return 0
        except SystemError, e:
            Utils.logMessage('Errore di sistema!')
            self.dlg_config.txtFeedback_inizializza.setText('Errore di sistema!')
            return 0
        else: #...se tutto ok proseguo:
            #Recupero i layers dalla TOC per svuotarla:
            msg.setText("ATTENZIONE! Con questa azione svuoterai la TOC di QGis per caricare temporaneamente i nuovi shp ed importarli sul DB, inzializzando di fatto il nuovo progetto ed eliminando eventuali altre tabelle gia' presenti nello schema definito nella sezione A: proseguire?")
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Inizializzare lo schema sul DB?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            retval = msg.exec_()
            if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                return 0
            elif (retval == 16384): #l'utente HA CLICCATO YES. Svuoto la TOC
                layers = self.iface.legendInterface().layers()
                for layer in layers:
                    QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
            #Adesso recupero il percorso degli shp e li carico sulla TOC:
            #Utils.logMessage('scala_shp: ' + str(scala_shp))
            layer_scala = QgsVectorLayer(scala_shp, self.LAYER_NAME['SCALA'], "ogr")
            #layer_cavo = QgsVectorLayer(cavo_shp, self.LAYER_NAME['SOTTOT'], "ogr")
            lista_layer_to_load=[layer_scala]
            QgsMapLayerRegistry.instance().addMapLayers(lista_layer_to_load)
            #Li spengo di default e li importo direttamente sul DB:
            crs = None
            test_conn = None
            options = {}
            options['lowercaseFieldNames'] = True
            options['overwrite'] = True
            options['forceSinglePartGeometryType'] = True
            try:
                self.dlg_config.txtFeedback_inizializza.setText("Sto importando i dati...")
                for layer_loaded in lista_layer_to_load:
                    self.iface.legendInterface().setLayerVisible(layer_loaded, False)
                    layer_loaded_geom = layer_loaded.wkbType()
                    uri = None
                    '''
                    if layer_loaded_geom==4:
                        uri = "%s key=gid type=POINT table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_loaded.name().lower())
                    elif layer_loaded_geom==1:
                        uri = "%s key=gid type=MULTIPOINT table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_loaded.name().lower())
                    elif layer_loaded_geom==3:
                        uri = "%s key=gid type=MULTIPOLYGON table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_loaded.name().lower())
                    elif layer_loaded_geom==2:
                        uri = "%s key=gid type=MULTILINESTRING table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_loaded.name().lower())
                    '''
                    uri = "%s key=gid table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_loaded.name().lower())
                    Utils.logMessage('WKB: ' + str(layer_loaded_geom)+ '; DEST_DIR: ' + str(dest_dir))
                    crs = layer_loaded.crs()
                    error = QgsVectorLayerImport.importLayer(layer_loaded, uri, "postgres", crs, False, False, options)
                    if error[0] != 0:
                        iface.messageBar().pushMessage(u'Error', error[1], QgsMessageBar.CRITICAL, 5)
                        msg.setText("Errore nell'importazione. Vedere il dettaglio dell'errore, contattare l'amministratore")
                        msg.setDetailedText(error[1])
                        msg.setIcon(QMessageBox.Critical)
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.setWindowTitle("Errore nell'importazione!")
                        retval = msg.exec_()
                        self.dlg_config.txtFeedback_inizializza.setText(error[1])
                        return 0
                #apro il cursore per leggere/scrivere sul DB:
                test_conn = psycopg2.connect(dest_dir)
                cur = test_conn.cursor()
                #creo la tabella delle variabili di progetto, droppandola se esiste gia':
                query = "SET search_path = %s, pg_catalog;" % (schemaDB)
                Utils.logMessage('Adesso creo la tabella con le variabili in ' + str(schemaDB))
                cur.execute(query)
                sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_tab_variabili_progetto.sql'
                cur.execute(open(sql_file, "r").read())
                
                #Creo le altre tabelle e funzioni nello schema selezionato:
                sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_triggers.sql'
                cur.execute(open(sql_file, "r").read())
                sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_batch_schemi_e_tabelle.sql'
                cur.execute(open(sql_file, "r").read())
                
                epsg_srid = int(crs.postgisSrid())
                self.epsg_srid = epsg_srid
                query_insert = "INSERT INTO variabili_progetto_return (srid, id_pop, cod_belf, lotto) VALUES (%i, %i, '%s', '%s');" % (epsg_srid, codpop, comuneDB, codice_lotto)
                cur.execute(query_insert)
                
                #Modifico eventualmente il nome di alcuni campi, o ne aggiungo, richiamando una funzione:
                cur.execute("SELECT public.s_alter_table_fn('%s', %i);SELECT public.s_alter_scala_fn('%s', %i);" % (schemaDB, epsg_srid, schemaDB, epsg_srid))
                test_conn.commit()
                
                #Da mail di Gatti del 25/08/2017: risulta che caricando lo SHP delle SCALE non sempre il gid e' calcolato. Lo ricalcolo a prescindere:
                query_id_scala = "UPDATE scala SET id_scala = '%s'||'%s'||lpad(gid::text, 5, '0');" % (comuneDB, codice_lotto)
                Utils.logMessage('query creazione id scala = ' + str(query_id_scala));
                cur.execute(query_id_scala)
                test_conn.commit()

                #Dopodiche' aggiorno alcuni parametri sulle tabelle: il CODICE COMUNE lo faccio inserire a mano:
                query_alter_giunti = "ALTER TABLE giunti ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE giunti ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE giunti ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_giunti)
                query_alter_pd = "ALTER TABLE pd ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE pd ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE pd ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_pd)
                query_alter_pfs = "ALTER TABLE pfs ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE pfs ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE pfs ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_pfs)
                query_alter_pfp = "ALTER TABLE pfp ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE pfp ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE pfp ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_pfp)
                query_alter_pop = "ALTER TABLE pop ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE pop ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE pop ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_pop)
                query_alter_cavo = "ALTER TABLE cavo ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE cavo ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE cavo ALTER COLUMN id_pop_end SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_cavo)
                query_alter_pozzetto = "ALTER TABLE pozzetto ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE pozzetto ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE pozzetto ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_pozzetto)
                #Associo i trigger DELETE alle tabelle:
                query_trigger_delete = "CREATE TRIGGER delete_feature AFTER DELETE ON scala FOR EACH ROW EXECUTE PROCEDURE %s.delete_scala('%s'); CREATE TRIGGER delete_feature AFTER DELETE ON giunti FOR EACH ROW EXECUTE PROCEDURE %s.delete_giunto('%s'); CREATE TRIGGER delete_feature AFTER DELETE ON pd FOR EACH ROW EXECUTE PROCEDURE %s.delete_pd('%s'); CREATE TRIGGER delete_feature AFTER DELETE ON pfp FOR EACH ROW EXECUTE PROCEDURE %s.delete_pfp('%s'); CREATE TRIGGER delete_feature AFTER DELETE ON pfs FOR EACH ROW EXECUTE PROCEDURE %s.delete_pfs('%s');" % (schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB)
                cur.execute(query_trigger_delete)
                query_trigger_update = '''CREATE TRIGGER update_ids_giunto BEFORE INSERT ON giunti FOR EACH ROW EXECUTE PROCEDURE update_giunto('%s');
                CREATE TRIGGER update_ids_pd BEFORE INSERT ON pd FOR EACH ROW EXECUTE PROCEDURE update_pd('%s');
                CREATE TRIGGER update_ids_pfs BEFORE INSERT ON pfs FOR EACH ROW EXECUTE PROCEDURE update_pfs('%s');
                CREATE TRIGGER update_ids_pfp BEFORE INSERT ON pfp FOR EACH ROW EXECUTE PROCEDURE update_pfp('%s');
                CREATE TRIGGER update_ids_pop BEFORE INSERT ON pop FOR EACH ROW EXECUTE PROCEDURE update_pop('%s');
                CREATE TRIGGER update_ids_cavo BEFORE INSERT ON cavo FOR EACH ROW EXECUTE PROCEDURE update_cavo('%s');
                CREATE TRIGGER update_ids_pozzetto BEFORE INSERT ON pozzetto FOR EACH ROW EXECUTE PROCEDURE update_pozzetto('%s');'''  % (schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB)
                cur.execute(query_trigger_update)
                
                #sposto piu sopra
                #epsg_srid = int(crs.postgisSrid())
                #self.epsg_srid = epsg_srid
                #query_insert = "INSERT INTO variabili_progetto_return (srid, id_pop, cod_belf) VALUES (%i, %i, '%s');" % (epsg_srid, codpop, comuneDB)
                #cur.execute(query_insert)
                
                #Risetto il search_path originario perche forse se lo tiene in pancia quello vecchio:
                query_path = 'SET search_path = public;'
                cur.execute(query_path)
                # Make the changes to the database persistent
                test_conn.commit()
                #Aggiungo la geometry_column secondo lo SRID impostato nel lotto_base:
                query_update_srid_raw = "SELECT public.UpdateGeometrySRID ('%(schema)s', 'cavo', 'geom', %(srid)s); SELECT public.UpdateGeometrySRID ('%(schema)s', 'sottotratta', 'geom', %(srid)s); SELECT public.UpdateGeometrySRID ('%(schema)s', 'area_pfp', 'geom', %(srid)s); SELECT public.UpdateGeometrySRID ('%(schema)s', 'area_pfs', 'geom', %(srid)s); SELECT public.UpdateGeometrySRID ('%(schema)s', 'cavoroute', 'geom', %(srid)s); SELECT public.UpdateGeometrySRID ('%(schema)s', 'giunti', 'geom', %(srid)s); SELECT public.UpdateGeometrySRID ('%(schema)s', 'pd', 'geom', %(srid)s); SELECT public.UpdateGeometrySRID ('%(schema)s', 'pfs', 'geom', %(srid)s); SELECT public.UpdateGeometrySRID ('%(schema)s', 'pfp', 'geom', %(srid)s); SELECT public.UpdateGeometrySRID ('%(schema)s', 'pop', 'geom', %(srid)s); SELECT public.UpdateGeometrySRID ('%(schema)s', 'pozzetto', 'geom', %(srid)s);"
                query_update_srid = query_update_srid_raw % {'schema': schemaDB, 'srid': epsg_srid}
                cur.execute(query_update_srid)

                #creo la tabella, vuota, cavoroute, la droppo se eventualmente esiste gia':
                query_cavoroute_raw = """DROP TABLE IF EXISTS %(schema)s.cavoroute; CREATE TABLE IF NOT EXISTS %(schema)s.cavoroute (
                    gid serial NOT NULL PRIMARY KEY, id_cavo character varying(64), fibre_coun integer, n_ui integer, n_ui_reali integer, from_p character varying(64), to_p character varying(64), net_type character varying(255), length_m double precision, source integer, target integer, geom public.geometry(MultiLineString, %(epsg_srid)i), tipo_posa character varying(450)[], n_gnz_un smallint, n_gnz_tot integer, n_gnz_min8 smallint, n_gnz_mag8 smallint, n_gnz_min12 smallint, n_gnz_mag12 smallint, teste_cavo smallint, scorta smallint, terminaz integer, temp_cavo_label character varying(250)[], lung_ott double precision);
                TRUNCATE TABLE %(schema)s.cavoroute;
                """
                query_cavoroute = query_cavoroute_raw % {'schema': schemaDB, 'epsg_srid': epsg_srid}
                cur.execute(query_cavoroute)
                test_conn.commit()
                
                #Modifico eventualmente il nome di alcuni campi, o ne aggiungo, richiamando una funzione -- sposto questo richiamo piu sopra
                #cur.execute("SELECT public.s_alter_table_fn('%s', %i);SELECT public.s_alter_scala_fn('%s', %i);" % (schemaDB, epsg_srid, schemaDB, epsg_srid))
                #test_conn.commit()
                
                #Inoltre ho notato un errore nel routing nel caso in cui il campo GID non sia INTEGER ma ad esempio BIGINT...Se il problema si ripresenta forse si puo risolvere con un cast_to_integer nelle query con pgr_dijkstra
                query_gids_int_raw = """ALTER TABLE %(schema)s.area_pfp ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.area_pfs ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.cavo ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.cavoroute ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.giunti ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.pd ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.pfp ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.pfs ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.pozzetto ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.scala ALTER COLUMN gid TYPE integer;
                """
                query_gids_int = query_gids_int_raw % {'schema': schemaDB}
                cur.execute(query_gids_int)
                #se c'e' qualche errore, il plugin lo restituisce con l'except finale.
                test_conn.commit()
                
                cur.close()
                test_conn.close()
            except psycopg2.Error, e:
                Utils.logMessage(e.pgerror)
                self.dlg_config.txtFeedback_inizializza.setText("Errore su DB, vedere il log o contattare l'amministratore")
                test_conn.rollback()
                return 0
            except SystemError, e:
                Utils.logMessage('Errore di sistema!')
                self.dlg_config.txtFeedback_inizializza.setText('Errore di sistema!')
                test_conn.rollback()
                return 0
            else:
                self.dlg_config.txtFeedback_inizializza.setText("Dati importati con successo! Puoi passare alle sezioni C o D")
                #Abilito le restanti sezioni e pulsanti
                self.dlg_config.chkDB.setEnabled(False)
                self.dlg_config.import_DB.setEnabled(False)
                self.dlg_config.variabili_DB.setEnabled(True)
                self.dlg_config.importBtn.setEnabled(True)
            finally:
                if test_conn is not None:
                    try:
                        test_conn.close()
                    except:
                        msg.setText('server closed the connection unexpectedly')
                        msg.setIcon(QMessageBox.Critical)
                        msg.setStandardButtons(QMessageBox.Ok)
                        retval = msg.exec_()
            
        
    def import_shp2db(self):
        #dest_dir #percorso del DB SENZA lo schema pero'
        #bisogna prima importare gli shp sulla TOC di QGis...o almeno per semplificarsi la vita. Vedi:
        # http://ssrebelious.blogspot.it/2015/06/how-to-import-layer-into-postgis.html
        '''Se questo comando funziona potresti
        1-finestra in cui chiedi che andrai a svuotare la TOC
        2-svuoti la TOC
        3-carichi sulla TOC i vari shp
        4-li converti
        5-risvuoti la TOC
        '''
        #altrimenti devi importarti nel plugin l'eseguibile di shp2pgsql.exe. Pero a questo punto il plugin diventa piattaforma dipendente...
        
        self.dlg_config.import_progressBar.setValue(0)
        self.dlg_config.import_progressBar.setMaximum(9)
        self.dlg_config.txtFeedback_inizializza.setText("Sto caricando i dati, non interrompere, il processo potrebbe richiedere alcuni minuti...")
        global epsg_srid
        #importo gli shp su db. Controllo che tutti i campi siano compilati prima di procedere:
        msg = QMessageBox()
        try:
            schemaDB = self.dlg_config.schemaDB.text()
            dirname_text = self.dlg_config.dirBrowse_txt.text()
            scala_shp = self.dlg_config.scala_shp.text()
            giunto_shp = self.dlg_config.giunto_shp.text()
            pd_shp = self.dlg_config.pd_shp.text()
            pfs_shp = self.dlg_config.pfs_shp.text()
            pfp_shp = self.dlg_config.pfp_shp.text()
            pozzetto_shp = self.dlg_config.pozzetto_shp.text()
            areapfs_shp = self.dlg_config.areapfs_shp.text()
            areapfp_shp = self.dlg_config.areapfp_shp.text()
            cavo_shp = self.dlg_config.cavo_shp.text()
            codpop = int(self.dlg_config.codpopDB_2.text())
            comuneDB = self.dlg_config.comuneDB_2.text()
            codice_lotto = self.dlg_config.lottoDB_2.text()
            if ( (dirname_text is None) or (scala_shp is None) or (dirname_text=='') or (scala_shp=='') ):
                raise NameError('Specificare TUTTI i nomi degli shp e il percorso di origine!')
            if ( (giunto_shp is None) or (pd_shp is None) or (giunto_shp=='') or (pd_shp=='') ):
                raise NameError('Specificare TUTTI i nomi degli shp e il percorso di origine!')
            if ( (pfs_shp is None) or (pfp_shp is None) or (pfs_shp=='') or (pfp_shp=='') ):
                raise NameError('Specificare TUTTI i nomi degli shp e il percorso di origine!')
            if ( (pozzetto_shp is None) or (areapfs_shp is None) or (pozzetto_shp=='') or (areapfs_shp=='') ):
                raise NameError('Specificare TUTTI i nomi degli shp e il percorso di origine!')
            if ( (areapfp_shp is None) or (cavo_shp is None) or (areapfp_shp=='') or (cavo_shp=='') ):
                raise NameError('Specificare TUTTI i nomi degli shp e il percorso di origine!')
            if ( len(str(codpop))> 3):
                raise NameError('COD_POP: massimo 3 cifre')
            if ( (comuneDB is None) or (comuneDB=='') or (codpop is None) or (codpop=='') or (codice_lotto is None) or (codice_lotto=='') ):
                raise NameError('Specificare COMUNE LOTTO e COD_POP!')
            if ( len(codice_lotto)> 5 ):
                raise NameError('LOTTO: massimo 5 caratteri')
            if ( len(comuneDB)>4 ):
                raise NameError('COMUNE: massimo 4 caratteri')
            #VERIFICO che nella directory indicata vi siano TUTTI i layer indicati, cioe' gli shp:
            filepath = "%s/%s.shp" % (dirname_text, scala_shp)
            if not os.path.isfile(filepath):
                raise NameError("ATTENZIONE! Manca il file '%s' nel percorso indicato" % (os.path.basename(filepath)) )
            filepath = "%s/%s.shp" % (dirname_text, giunto_shp)
            if not os.path.isfile(filepath):
                raise NameError("ATTENZIONE! Manca il file '%s' nel percorso indicato" % (os.path.basename(filepath)) )
            filepath = "%s/%s.shp" % (dirname_text, pd_shp)
            if not os.path.isfile(filepath):
                raise NameError("ATTENZIONE! Manca il file '%s' nel percorso indicato" % (os.path.basename(filepath)) )
            filepath = "%s/%s.shp" % (dirname_text, pfs_shp)
            if not os.path.isfile(filepath):
                raise NameError("ATTENZIONE! Manca il file '%s' nel percorso indicato" % (os.path.basename(filepath)) )
            filepath = "%s/%s.shp" % (dirname_text, pfp_shp)
            if not os.path.isfile(filepath):
                raise NameError("ATTENZIONE! Manca il file '%s' nel percorso indicato" % (os.path.basename(filepath)) )
            filepath = "%s/%s.shp" % (dirname_text, pozzetto_shp)
            if not os.path.isfile(filepath):
                raise NameError("ATTENZIONE! Manca il file '%s' nel percorso indicato" % (os.path.basename(filepath)) )
            filepath = "%s/%s.shp" % (dirname_text, areapfs_shp)
            if not os.path.isfile(filepath):
                raise NameError("ATTENZIONE! Manca il file '%s' nel percorso indicato" % (os.path.basename(filepath)) )
            filepath = "%s/%s.shp" % (dirname_text, areapfp_shp)
            if not os.path.isfile(filepath):
                raise NameError("ATTENZIONE! Manca il file '%s' nel percorso indicato" % (os.path.basename(filepath)) )
            filepath = "%s/%s.shp" % (dirname_text, cavo_shp)
            if not os.path.isfile(filepath):
                raise NameError("ATTENZIONE! Manca il file '%s' nel percorso indicato" % (os.path.basename(filepath)) )
        except NameError as err:
            msg.setText(err.args[0])
            msg.setIcon(QMessageBox.Critical)
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            self.dlg_config.txtFeedback_import.setText(err.args[0])
            return 0
        except ValueError:
            self.dlg_config.txtFeedback_import.setText('Specificare TUTTE le variabili')
            return 0
        except SystemError, e:
            Utils.logMessage('Errore di sistema!')
            self.dlg_config.txtFeedback_import.setText('Errore di sistema!')
            return 0
        else: #...se tutto ok proseguo:
            #Recupero i layers dalla TOC per svuotarla:
            msg.setText("ATTENZIONE! Con questa azione svuoterai la TOC di QGis per caricare temporaneamente i nuovi shp, e se lo schema selezionato esiste gia' verra' SVUOTATO e ripopolato con gli shp selezionati: procedere?")
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Svuotare la TOC e lo schema dai layers attuali?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            retval = msg.exec_()
            if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                return 0
            elif (retval == 16384): #l'utente HA CLICCATO YES. Svuoto la TOC
                layers = self.iface.legendInterface().layers()
                for layer in layers:
                    QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
            #Adesso recupero il percorso degli shp e li carico sulla TOC:
            layer_scala = QgsVectorLayer(dirname_text+"\\"+scala_shp+".shp", self.LAYER_NAME['SCALA'], "ogr")
            layer_giunto = QgsVectorLayer(dirname_text+"\\"+giunto_shp+".shp", self.LAYER_NAME['GIUNTO'], "ogr")
            layer_pd = QgsVectorLayer(dirname_text+"\\"+pd_shp+".shp", self.LAYER_NAME['PD'], "ogr")
            layer_pfs = QgsVectorLayer(dirname_text+"\\"+pfs_shp+".shp", self.LAYER_NAME['PFS'], "ogr")
            layer_pfp = QgsVectorLayer(dirname_text+"\\"+pfp_shp+".shp", self.LAYER_NAME['PFP'], "ogr")
            layer_pozzetto = QgsVectorLayer(dirname_text+"\\"+pozzetto_shp+".shp", self.LAYER_NAME['Pozzetto'], "ogr")
            layer_areapfs = QgsVectorLayer(dirname_text+"\\"+areapfs_shp+".shp", self.LAYER_NAME['Area_PFS'], "ogr")
            layer_areapfp = QgsVectorLayer(dirname_text+"\\"+areapfp_shp+".shp", self.LAYER_NAME['Area_PFP'], "ogr")
            layer_cavo = QgsVectorLayer(dirname_text+"\\"+cavo_shp+".shp", self.LAYER_NAME['CAVO'], "ogr")
            lista_layer_to_load=[layer_scala, layer_giunto, layer_pd, layer_pfs, layer_pfp, layer_pozzetto, layer_areapfs, layer_areapfp, layer_cavo]
            QgsMapLayerRegistry.instance().addMapLayers(lista_layer_to_load)
            #Li spengo di default e li importo direttamente sul DB:
            crs = None
            test_conn = None
            options = {}
            options['lowercaseFieldNames'] = True
            options['overwrite'] = True
            options['forceSinglePartGeometryType'] = True
            try:
                self.dlg_config.txtFeedback_import.setText("Sto importando i dati...")
                for layer_loaded in lista_layer_to_load:
                    self.iface.legendInterface().setLayerVisible(layer_loaded, False)
                    layer_loaded_geom = layer_loaded.wkbType()
                    uri = None
                    '''
                    if layer_loaded_geom==4:
                        uri = "%s key=gid type=POINT table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_loaded.name().lower())
                    elif layer_loaded_geom==1:
                        uri = "%s key=gid type=MULTIPOINT table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_loaded.name().lower())
                    elif layer_loaded_geom==3:
                        uri = "%s key=gid type=MULTIPOLYGON table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_loaded.name().lower())
                    elif layer_loaded_geom==2:
                        uri = "%s key=gid type=MULTILINESTRING table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_loaded.name().lower())
                    '''
                    uri = "%s key=gid table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_loaded.name().lower())
                    Utils.logMessage('WKB: ' + str(layer_loaded_geom) + '; DEST_DIR: ' + str(dest_dir))
                    crs = layer_loaded.crs()
                    error = QgsVectorLayerImport.importLayer(layer_loaded, uri, "postgres", crs, False, False, options)
                    if error[0] != 0:
                        iface.messageBar().pushMessage(u'Error', error[1], QgsMessageBar.CRITICAL, 5)
                        msg.setText("Errore nell'importazione. Vedere il dettaglio dell'errore, contattare l'amministratore")
                        msg.setDetailedText(error[1])
                        msg.setIcon(QMessageBox.Critical)
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.setWindowTitle("Errore nell'importazione!")
                        retval = msg.exec_()
                        self.dlg_config.txtFeedback_import.setText(error[1])
                        return 0
                    self.pageProcessed(self.dlg_config.import_progressBar) #increase progressbar
                
                #apro il cursore per leggere/scrivere sul DB:
                test_conn = psycopg2.connect(dest_dir)
                cur = test_conn.cursor()
                #creo la tabella delle variabili di progetto, droppandola se esiste gia':
                query = "SET search_path = %s, pg_catalog;" % (schemaDB)
                Utils.logMessage('Adesso creo la tabella con le variabili in ' + str(schemaDB))
                cur.execute(query)
                sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_tab_variabili_progetto.sql'
                cur.execute(open(sql_file, "r").read())
                
                #Da mail di Gatti del 25/08/2017: risulta che caricando lo SHP delle SCALE non sempre il gid e' calcolato. Lo ricalcolo a prescindere.
                #Unisco un po' di query nella speranza di ridurre i tempi:
                epsg_srid = int(crs.postgisSrid())
                self.epsg_srid = epsg_srid
                query_id_scala = "UPDATE scala SET id_scala = '%s'||'%s'||lpad(gid::text, 5, '0'); INSERT INTO variabili_progetto_return (srid, id_pop, cod_belf, lotto) VALUES (%i, %i, '%s', '%s');" % (comuneDB, codice_lotto, epsg_srid, codpop, comuneDB, codice_lotto)
                cur.execute(query_id_scala)
                test_conn.commit()
                
                #query_insert = "INSERT INTO variabili_progetto_return (srid, id_pop, cod_belf) VALUES (%i, %i, '%s');" % (epsg_srid, codpop, comuneDB)
                #cur.execute(query_insert)
                
                #le uniche altre tabelle da creare sono POP e SOTTOTRATTA:
                sql_create_pop = """DROP TABLE IF EXISTS sottotratta;
                DROP TABLE IF EXISTS pop;
                CREATE TABLE IF NOT EXISTS pop
            (
            gid serial NOT NULL,
            id_pop character varying(10),
            coord_n double precision,
            coord_e double precision,
            area_pop character varying(50),
            cabina_pri character varying(50),
            nome character varying(50),
            n_ce integer,
            cod_belf character varying(4),
            lotto character varying(5),
            id_pop_num integer,
            tipo_posa character varying(10),
            cod_cft character varying(5),
            geom public.geometry(Point, %i),
            CONSTRAINT pop_pkey PRIMARY KEY (gid)
            );
                CREATE INDEX pop_geom_idx ON pop USING gist (geom);
                CREATE TABLE IF NOT EXISTS sottotratta
            (
            gid serial NOT NULL,
            id_sottotr character varying(30),
            id_sotto_1 character varying(30),
            shape_leng numeric,
            id_pozzett character varying(50),
            id_armadio character varying(50),
            id_facciat character varying(50),
            id_sostegn character varying(50),
            id_ce_endp character varying(50),
            id_pozze_1 character varying(50),
            id_armad_1 character varying(50),
            id_facci_1 character varying(50),
            id_soste_1 character varying(50),
            id_ce_en_1 character varying(50),
            id_ont_end character varying(50),
            lunghezza_ character varying(50),
            tipo_scavo character varying(50),
            num_minitu character varying(50),
            num_mini_1 character varying(50),
            tipo_minit character varying(50),
            costruttor character varying(50),
            modello_mi character varying(50),
            tipo_posa character varying(50),
            tipo_posa_ character varying(50),
            infrastrut character varying(50),
            codice_ins character varying(50),
            layer character varying(250),
            geom public.geometry(MultiLineString, %i),
            CONSTRAINT sottotratta_pkey PRIMARY KEY (gid)
            );
                CREATE INDEX sottotratta_geom_idx ON sottotratta USING gist (geom);""" %(epsg_srid, epsg_srid)
                cur.execute(sql_create_pop)
                
                #Creo le altre tabelle e funzioni nello schema selezionato:
                sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_triggers.sql'
                cur.execute(open(sql_file, "r").read())
                
                #Aggiungo alcune CONSTRAINTS alle tabelle:
                query_add_constraints = """ALTER TABLE giunti ADD UNIQUE (id_giunto);
                ALTER TABLE pd ADD UNIQUE (id_pd);
                ALTER TABLE pfs ADD UNIQUE (id_pfs);
                ALTER TABLE pfp ADD UNIQUE (id_pfp);
                ALTER TABLE pozzetto ADD UNIQUE (id_pozzett);
                ALTER TABLE scala ADD UNIQUE (id_scala);"""
                cur.execute(query_add_constraints)
                test_conn.commit()
                #se c'e' qualche errore, il plugin lo restituisce con l'except finale.
                
                #Dopodiche' aggiorno alcuni parametri sulle tabelle: il CODICE COMUNE lo faccio inserire a mano:
                query_alter_giunti = "ALTER TABLE giunti ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE giunti ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE giunti ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_giunti)
                query_alter_pd = "ALTER TABLE pd ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE pd ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE pd ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_pd)
                query_alter_pfs = "ALTER TABLE pfs ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE pfs ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE pfs ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_pfs)
                query_alter_pfp = "ALTER TABLE pfp ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE pfp ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE pfp ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_pfp)
                query_alter_pop = "ALTER TABLE pop ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE pop ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE pop ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_pop)
                query_alter_cavo = "ALTER TABLE cavo ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE cavo ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE cavo ALTER COLUMN id_pop_end SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_cavo)
                query_alter_pozzetto = "ALTER TABLE pozzetto ALTER COLUMN cod_belf SET DEFAULT '%s'; ALTER TABLE pozzetto ALTER COLUMN lotto SET DEFAULT '%s'; ALTER TABLE pozzetto ALTER COLUMN id_pop SET DEFAULT '%s';" % (comuneDB, codice_lotto, codpop)
                cur.execute(query_alter_pozzetto)
                #Associo i trigger DELETE alle tabelle:
                query_trigger_delete = "CREATE TRIGGER delete_feature AFTER DELETE ON scala FOR EACH ROW EXECUTE PROCEDURE %s.delete_scala('%s'); CREATE TRIGGER delete_feature AFTER DELETE ON giunti FOR EACH ROW EXECUTE PROCEDURE %s.delete_giunto('%s'); CREATE TRIGGER delete_feature AFTER DELETE ON pd FOR EACH ROW EXECUTE PROCEDURE %s.delete_pd('%s'); CREATE TRIGGER delete_feature AFTER DELETE ON pfp FOR EACH ROW EXECUTE PROCEDURE %s.delete_pfp('%s'); CREATE TRIGGER delete_feature AFTER DELETE ON pfs FOR EACH ROW EXECUTE PROCEDURE %s.delete_pfs('%s');" % (schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB)
                cur.execute(query_trigger_delete)
                query_trigger_update = '''CREATE TRIGGER update_ids_giunto BEFORE INSERT ON giunti FOR EACH ROW EXECUTE PROCEDURE update_giunto('%s');
                CREATE TRIGGER update_ids_pd BEFORE INSERT ON pd FOR EACH ROW EXECUTE PROCEDURE update_pd('%s');
                CREATE TRIGGER update_ids_pfs BEFORE INSERT ON pfs FOR EACH ROW EXECUTE PROCEDURE update_pfs('%s');
                CREATE TRIGGER update_ids_pfp BEFORE INSERT ON pfp FOR EACH ROW EXECUTE PROCEDURE update_pfp('%s');
                CREATE TRIGGER update_ids_pop BEFORE INSERT ON pop FOR EACH ROW EXECUTE PROCEDURE update_pop('%s');
                CREATE TRIGGER update_ids_cavo BEFORE INSERT ON cavo FOR EACH ROW EXECUTE PROCEDURE update_cavo('%s');
                CREATE TRIGGER update_ids_pozzetto BEFORE INSERT ON pozzetto FOR EACH ROW EXECUTE PROCEDURE update_pozzetto('%s');'''  % (schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB, schemaDB)
                cur.execute(query_trigger_update)
                
                #Risetto il search_path originario perche forse se lo tiene in pancia quello vecchio:
                query_path = 'SET search_path = public;'
                cur.execute(query_path)
                # Make the changes to the database persistent
                test_conn.commit()
                
                #creo la tabella, vuota, cavoroute, la droppo se eventualmente esiste gia':
                query_cavoroute_raw = """DROP TABLE IF EXISTS %(schema)s.cavoroute; CREATE TABLE IF NOT EXISTS %(schema)s.cavoroute (
                    gid serial NOT NULL PRIMARY KEY, id_cavo character varying(64), fibre_coun integer, n_ui integer, n_ui_reali integer, from_p character varying(64), to_p character varying(64), net_type character varying(255), length_m double precision, source integer, target integer, geom public.geometry(MultiLineString, %(epsg_srid)i), tipo_posa character varying(450)[], n_gnz_un smallint, n_gnz_tot integer, n_gnz_min8 smallint, n_gnz_mag8 smallint, n_gnz_min12 smallint, n_gnz_mag12 smallint, teste_cavo smallint, scorta smallint, terminaz integer, temp_cavo_label character varying(250)[], lung_ott double precision);
                TRUNCATE TABLE %(schema)s.cavoroute;
                """
                query_cavoroute = query_cavoroute_raw % {'schema': schemaDB, 'epsg_srid': epsg_srid}
                cur.execute(query_cavoroute)
                test_conn.commit()
                
                #Modifico eventualmente il nome di alcuni campi, o ne aggiungo, richiamando una funzione:
                cur.execute("SELECT public.s_alter_table_fn('%s', %i);SELECT public.s_alter_scala_fn('%s', %i);" % (schemaDB, epsg_srid, schemaDB, epsg_srid))
                test_conn.commit()
                '''
                #modifico il nome del campo totale_ui delle scale a n_ui:
                query_ui = """ALTER TABLE %s.scala RENAME COLUMN totale_ui TO n_ui;""" % (schemaDB)
                try:
                    cur.execute(query_ui)
                    test_conn.commit()
                except:
                    Utils.logMessage("Campo totale_ui non presente su scala")
                    test_conn.rollback()
                #aggiungo il campo n_ui_originali e id_sc_ref al layer scala se non esiste:
                query_add_length = """ALTER TABLE %s.scala ADD COLUMN n_ui_originali integer;""" % (schemaDB)
                try:
                    cur.execute(query_add_length)
                    test_conn.commit()
                except psycopg2.Error, e:
                    Utils.logMessage(e.pgerror)
                    test_conn.rollback()
                except:
                    Utils.logMessage("Campo n_ui_originali gia' presente su scala")
                    test_conn.rollback()
                query_add_length = """ALTER TABLE %s.scala ADD COLUMN id_sc_ref character varying(160);""" % (schemaDB)
                try:
                    cur.execute(query_add_length)
                    test_conn.commit()
                except psycopg2.Error, e:
                    Utils.logMessage(e.pgerror)
                    test_conn.rollback()
                except:
                    Utils.logMessage("Campi id_sc_ref gia' presente su scala")
                    test_conn.rollback()
                query_calc_orig = """UPDATE %s.scala SET n_ui_originali = n_ui;""" % (schemaDB)
                cur.execute(query_calc_orig)
                #modifico il nome del campo posa del cavo a tipo_posa:
                query_posa = """ALTER TABLE %s.cavo RENAME COLUMN posa TO tipo_posa;""" % (schemaDB)
                try:
                    cur.execute(query_posa)
                    test_conn.commit()
                except:
                    Utils.logMessage("Campo posa non presente su cavo")
                    test_conn.rollback()
                #per ultimo, aggiungo il campo length_m al layer cavo se non esiste:
                query_add_length = """ALTER TABLE %s.cavo ADD COLUMN length_m double precision;""" % (schemaDB)
                try:
                    cur.execute(query_add_length)
                    test_conn.commit()
                except psycopg2.Error, e:
                    Utils.logMessage(e.pgerror)
                    test_conn.rollback()
                except:
                    Utils.logMessage("Campo length_m gia' presente su cavo")
                    test_conn.rollback()
                test_conn.commit()
                '''
                
                #Nel caso in cui il campo esista gia', o cmq in ogni caso, lo trasformo in double:
                #query_double = "ALTER TABLE %s.cavo ALTER COLUMN length_m TYPE double precision;" % (schemaDB)
                #try:
                #    cur.execute(query_double)
                #    test_conn.commit()
                #except psycopg2.Error, e:
                #    Utils.logMessage(e.pgerror)
                #    Utils.logMessage("Campo length_m gia' double o non possibile trasformarlo in double")
                #Inoltre ho notato un errore nel routing nel caso in cui il campo GID non sia INTEGER ma ad esempio BIGINT...Se il problema si ripresenta forse si puo risolvere con un cast_to_integer nelle query con pgr_dijkstra
                query_gids_int_raw = """ALTER TABLE %(schema)s.area_pfp ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.area_pfs ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.cavo ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.cavoroute ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.giunti ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.pd ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.pfp ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.pfs ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.pozzetto ALTER COLUMN gid TYPE integer;
                ALTER TABLE %(schema)s.scala ALTER COLUMN gid TYPE integer;
                """
                query_gids_int = query_gids_int_raw % {'schema': schemaDB}
                cur.execute(query_gids_int)
                #se c'e' qualche errore, il plugin lo restituisce con l'except finale.
                test_conn.commit()
                
                cur.close()
                test_conn.close()
            except psycopg2.Error, e:
                Utils.logMessage(e.pgerror)
                self.dlg_config.txtFeedback_import.setText("Errore su DB, vedere il log o contattare l'amministratore")
                test_conn.rollback()
                return 0
            except SystemError, e:
                Utils.logMessage('Errore di sistema!')
                self.dlg_config.txtFeedback_import.setText('Errore di sistema!')
                test_conn.rollback()
                return 0
            else:
                self.dlg_config.txtFeedback_import.setText("Dati importati con successo! Puoi passare alle sezioni C o D")
                #Abilito le restanti sezioni e pulsanti
                self.dlg_config.chkDB.setEnabled(False)
                self.dlg_config.import_DB.setEnabled(False)
                self.dlg_config.variabili_DB.setEnabled(True)
                self.dlg_config.importBtn.setEnabled(True)
            finally:
                if test_conn is not None:
                    try:
                        test_conn.close()
                    except:
                        msg.setText('server closed the connection unexpectedly')
                        msg.setIcon(QMessageBox.Critical)
                        msg.setStandardButtons(QMessageBox.Ok)
                        retval = msg.exec_()
    
    def load_layers_from_db(self):
        schemaDB = self.dlg_config.schemaDB.text() #recupero lo schema da cui prelevare le tabelle
        nameDB = self.dlg_config.nameDB.text()
        global epsg_srid
        #svuoto la TOC:
        layers = self.iface.legendInterface().layers()
        for layer in layers:
            QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
        try:
            #ciclo dentro la variabile LAYER_NAME e carico i layer da DB:
            for key, value in sorted(self.LAYER_NAME.items()): #casualmente l'ordine alfabetico ci piace...altrimenti devi usare "from collections import OrderedDict, LAYER_NAME=OrderedDict(), LAYER_NAME['SCALA']='Scala'" etc..
                if ( (key=="GIUNTO_F_dev") | (key=="PTA") | (key=="SCALA_F") | (key=="PD_F") | (key=="SCALA_append") ):
                    continue #evito di caricare 2/3 volte il layer GIUNTO
                Utils.logMessage('nome layerDB da caricare: ' + value)
                uri = "%s key=gid table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, value.lower())
                #provo a caricare il layer da un service:
                #uri = "dbname='%s' service='%s_service_operatore' user='operatore' sslmode=disable key=gid table=\"%s\".\"%s\" (geom) sql=" % (nameDB, nameDB, schemaDB, value.lower())
                layer = QgsVectorLayer(uri, value, "postgres")
                QgsMapLayerRegistry.instance().addMapLayer(layer)
                layer.loadNamedStyle(os.getenv("HOME")+'/.qgis2/python/plugins/ProgettoFTTH_return/qml_base/%s.qml' % (value))
                crs = layer.crs()
            
            #ridefinisco la variabile SRID per il progetto:
            epsg_srid = int(crs.postgisSrid())
            self.epsg_srid = epsg_srid
        
        except SystemError, e:
            debug_text = "Qualcosa e' andata storta nel caricare i layer da DB. Forse il servizio per il DB indicato non esiste? Rivedere i dati e riprovare"
            #in realta' questo errore non viene gestito, inizia a chiedere la pwd del servizio prima!
            self.dlg_config.txtFeedback.setText(debug_text)
            return 0
        else:
            self.dlg_config.txtFeedback.setText('Caricamento layer da DB riuscito!')
            return 1
    
    
    #--------------------------------------------------------------------------
    #PARTE SUL ROUTING
    def check_grouping_from_user(self):
        #Richiamo la stessa funzione sotto "lancia_popola_cavo", ma qui la faccio lanciare all'utente quando vuole per controllare quali elementi ancora necessitano di un'associazione:
        connInfo = SCALE_layer.source()
        result_check_grouping = db_solid.check_grouping(self, connInfo, theSchema)
        if (result_check_grouping==0):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Alcuni punti della rete non risultano associati a PFS o nel caso di PFS a PFP. Controllare i log di QGis per maggiori dettagli')
            return 0
        else:
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Controllo grouping effettuato: nessuna anomalia')
            return
         
    '''
    #Nella versione 4.4 lancio la funzione "lancia_consolida_aree". questa sarebeb quella lanciata dal core_widget, la commento
    def lancia_consolida_aree_dlg(self):
        connInfo = SCALE_layer.source()
        dest_dir = self.estrai_param_connessione(connInfo)
        #lancio la funzione aggiungendo la finestra sulla quale riportare le info in modo tale da poter provare anche il bottone da un'altra GUI.
        #result_calcolo = db_solid.consolida_aree(self, connInfo, theSchema, self.dlg)
        result_calcolo = db_solid.consolida_aree(self, connInfo, theSchema, self.dockwidget)
        if (result_calcolo < 100 and result_calcolo > 0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Attenzione, trovata area PFS con tanti punti")
        elif (result_calcolo >= 100 and result_calcolo < 1000):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Attenzione, trovata area PFS senza punti")
        elif (result_calcolo >= 1000 and result_calcolo < 10000):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Attenzione, trovata area PFP con tanti punti")
        elif (result_calcolo >= 10000):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Attenzione, trovata area PFP senza punti")
        elif (result_calcolo == 0):
            QMessageBox.information(self.dock, self.dock.windowTitle(), "Aree PFS e PFP aggiornate con successo senza alcun eccezione!")
        elif (result_calcolo == -1):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), "Aree PFS e PFP aggiornate con successo! Qualche area PFS ha pero' superato le UI massime consentite. Vedere il messaggio nella finestra")
        elif (result_calcolo == -2):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), "Aree PFS e PFP aggiornate con successo!\n Qualche area PFP ha pero' superato il numero di PD massimo consentito. Vedere il messaggio nella finestra")
    '''
            
    def lancia_consolida_aree(self):
        connInfo = SCALE_layer.source()
        #lancio la funzione aggiungendo la finestra sulla quale riportare le info in modo tale da poter provare anche il bottone da un'altra GUI.
        continuo_coi_pozzetti = 0
        result_calcolo = db_solid.consolida_aree(self, connInfo, theSchema, self.dlg_solid)
        if (result_calcolo < 100 and result_calcolo > 0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Attenzione, trovata area PFS con tanti punti")
        elif (result_calcolo >= 100 and result_calcolo < 1000):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Attenzione, trovata area PFS senza punti")
        elif (result_calcolo >= 1000 and result_calcolo < 10000):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Attenzione, trovata area PFP con tanti punti")
        elif (result_calcolo >= 10000):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Attenzione, trovata area PFP senza punti")
        elif (result_calcolo == 0):
            QMessageBox.information(self.dock, self.dock.windowTitle(), "Aree PFS e PFP aggiornate con successo senza alcun eccezione!")
            continuo_coi_pozzetti = 1
        elif (result_calcolo == -1):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), "Aree PFS e PFP aggiornate con successo! Qualche area PFS ha pero' superato le UI massime consentite. Vedere il messaggio nella finestra")
            continuo_coi_pozzetti = 1
        elif (result_calcolo == -2):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), "Aree PFS e PFP aggiornate con successo!\n Qualche area PFP ha pero' superato il numero di PD massimo consentito. Vedere il messaggio nella finestra")
            continuo_coi_pozzetti = 1
        #Continuo con il popolamento del layer "pozzetti"?
        if (continuo_coi_pozzetti==1):
            result_pozzetti = db_solid.popola_pozzetti(self, connInfo, theSchema, self.dlg_solid)
            if (result_pozzetti==0):
                QMessageBox.critical(self.dock, self.dock.windowTitle(), "Attenzione, qualcosa e' andato storto nel popolare il layer pozzetto. Consultare i log di QGis.")
            elif (result_pozzetti==1):
                QMessageBox.information(self.dock, self.dock.windowTitle(), "Layer pozzetto popolato correttamente!")
        else:
            QMessageBox.warning(self.dock, self.dock.windowTitle(), "Layer 'pozzetti' NON popolato in quanto sono state riscontrate delle anomalie sulle aree PFS e PFP.")
        
    
    def lancia_calcola_fibre(self):
        #step intermedio per passare alcune variabili alla funzione finale:
        #Inizializzo un layer di QGis giusto solo per prendermi i parametri di connessione:
        #self.inizializza_layer();
        connInfo = SCALE_layer.source()
        self.dlg_solid.txtFeedback.setText("Elaborazione in corso NON chiudere il programma...")
        #QMessageBox.information(self.dock, self.dock.windowTitle(), "Il programma impieghera' un po' di tempo ad eseguire il routing: non chiudere il programma, e avere pazienza...")
        result_calcolo = db_solid.calcola_fibre(self, connInfo, theSchema, self.epsg_srid)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Routing non eseguito!')
            self.dlg_solid.txtFeedback.setText('Errore di sistema! Routing non eseguito!')
        elif (result_calcolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing avvenuto con successo!')
            self.dlg_solid.txtFeedback.setText('Routing avvenuto con successo!')
        elif (result_calcolo==2):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), "Routing effettuato ma qualche punto della rete non e' stato associato al cavo: possibile errore nella geometria del cavo. Vedere log per sintesi delle coppie sorgente-obiettivo non correttamente abbinate")
            self.dlg_solid.txtFeedback.setText("Routing effettuato ma qualche punto della rete non e' stato associato al cavo: possibile errore nella geometria del cavo. Vedere log per sintesi delle coppie sorgente-obiettivo non correttamente abbinate")
        elif (result_calcolo==3):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Calcolo delle fibre per i cavi NON eseguito! Uno o piu' elementi del layer SCALA hanno n_ui<=0")
            self.dlg_solid.txtFeedback.setText("Calcolo delle fibre per i cavi NON eseguito! Uno o piu' elementi del layer SCALA hanno n_ui<=0")
        elif (result_calcolo==4):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Calcolo delle fibre per i cavi NON eseguito! Uno o piu' elementi del layer SCALA hanno n_ui NULL")
            self.dlg_solid.txtFeedback.setText("Calcolo delle fibre per i cavi NON eseguito! Uno o piu' elementi del layer SCALA hanno n_ui NULL")
            
    def lancia_calcola_route(self):
        connInfo = SCALE_layer.source()
        self.dlg_solid.txtFeedback.setText("Elaborazione in corso NON chiudere il programma...")
        result_calcolo = db_solid.calcola_route(self, connInfo, theSchema)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), "Errore di sistema! Cavoroute non calcolato! Probabilmente e' gia' stato calcolato oppure il layer cavo non e' stato inizializzato con successo. Vedere il log di sistema per maggiori informazioni. Nel caso provare a resettare tutto e ripetere la procedura dall'inizio.")
            self.dlg_solid.txtFeedback.setText("Errore di sistema! Cavoroute non calcolato! Forse esiste gia'? Vedere log, o resettare per ripetere daccapo l'operazione.")
        elif (result_calcolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Cavoroute calcolato con successo!')
            self.dlg_solid.txtFeedback.setText('Cavoroute calcolato con successo!')

    def lancia_reset_all(self):
        connInfo = SCALE_layer.source()
        result_calcolo = db_solid.reset_all(self, connInfo, theSchema)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Reset del routing non eseguito!')
        elif (result_calcolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Reset del routing avvenuto con successo!')
    
    def lancia_popola_cavo(self):
        #popolo il layer cavo prendendo le geometrie da sottotratta. Svuoto e riempio ogni volta, elimino le colonne di troppo e di conseguenza resetto prima tutto:
        connInfo = SCALE_layer.source()
        
        msg = QMessageBox()
        msg.setText("Attenzione con questa operazione si procede al reset di tutto il routing!")
        msg.setInformativeText("Il layer CAVO viene svuotato e poi popolato prendendo le geometrie dal layer SOTTOTRATTA. Si desidera realmente continuare?")
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Reset completo del routing: continuare?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
            self.dlg_solid.txtFeedback.setText("Creazione del layer cavo non effettuata per scelta dell'utente")
            Utils.logMessage("Creazione del layer cavo non effettuata per scelta dell'utente")
            return 0
        #Prima di resettare il layer cavo faccio un controllo per verificare che tutti i punti della rete siano stati associati - controllo BLOCCANTE:
        result_check_grouping = db_solid.check_grouping(self, connInfo, theSchema)
        if (result_check_grouping==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Trovata anomalia! Creazione del cavo non eseguita - alcuni punti della rete non risultano associati a PFS o nel caso di PFS a PFP. Controllare i log di QGis.')
            return 0
        
        #adesso popolo il layer:
        result_popolo = db_solid.popola_cavo(self, connInfo, theSchema)
        if (result_popolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Creazione del cavo non eseguita - errore a livello di copia delle geometrie!')
        elif (result_popolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Creazione del cavo avvenuta con successo!')
            self.dlg_solid.txtFeedback.setText("Creazione del cavo avvenuta con successo!")
        
        #Resetto il layer cavo:
        result_calcolo = db_solid.reset_all(self, connInfo, theSchema)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Creazione del cavo non eseguita - errore a livello di reset!')
            return 0
        elif (result_calcolo==1):
            #QMessageBox.information(self.dock, self.dock.windowTitle(), 'Reset del routing avvenuto con successo!')
            Utils.logMessage("Reset del routing avvenuto con successo!")

    def lancia_inizializza_routing(self):
        connInfo = SCALE_layer.source()
        result_calcolo = db_solid.inizializza_routing(self, connInfo, theSchema)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Inizializzazione al routing non eseguito!')
        elif (result_calcolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Inizializzazione al routing avvenuto con successo!')
        elif (result_calcolo==2):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), "Inizializzazione al routing avvenuto con successo ma con qualche eccezione!\nSono stati ritrovati dei cavi il cui vertice d'origine coincide con la destinazione!\nQuesto puo' essere dovuto ad una errata vettorializzazione della linea.\nVedere il log di QGis per i dettagli.")
    
    def lancia_scale_routing(self):
        #Associo SCALA ai vertici pgr: in questo caso UN nodo pgr == UN nodo scala
        connInfo = SCALE_layer.source()
        result_calcolo = db_solid.scale_routing(self, connInfo, theSchema)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Routing su SCALA non eseguito!')
        elif (result_calcolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su SCALA avvenuto con successo!')
        elif (result_calcolo==2):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Routing su SCALA NON effettuato. Controllare il layer e rilanciare.')
        elif (result_calcolo==3):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su SCALA effettuato ma con qualche reticenza')
            
    def lancia_pta_routing(self):
        #Associo PTA ai vertici pgr: in questo caso ci possono essere più vertici pgr coincidenti con lo stesso PTA, penso come il caso dei GIUNTI
        connInfo = SCALE_layer.source()
        result_calcolo = db_solid.pta_routing(self, connInfo, theSchema)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Routing su PTA non eseguito!')
        elif (result_calcolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su PTA avvenuto con successo!')
        elif (result_calcolo==2):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Routing su PTA NON effettuato. Controllare il layer e rilanciare.')
        elif (result_calcolo==3):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su PTA effettuato ma con qualche reticenza')
       
    def lancia_giunti_routing(self):
        #Associo GIUNTO ai vertici pgr: in questo caso ci possono essere più vertici pgr coincidenti con lo stesso GIUNTO.
        connInfo = SCALE_layer.source()
        result_calcolo = db_solid.giunti_routing(self, connInfo, theSchema)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Routing su GIUNTO non eseguito!')
        elif (result_calcolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su GIUNTO avvenuto con successo!')
        elif (result_calcolo==2):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Routing su GIUNTO NON effettuato. Controllare il layer e rilanciare.')
        elif (result_calcolo==3):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su GIUNTO effettuato ma con qualche reticenza')
            
    def lancia_pd_routing(self):
        #Associo PD ai vertici pgr: in questo caso ci possono essere più vertici pgr coincidenti con lo stesso PD.
        connInfo = SCALE_layer.source()
        result_calcolo = db_solid.pd_routing(self, connInfo, theSchema)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Routing su PD non eseguito!')
        elif (result_calcolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su PD avvenuto con successo!')
        elif (result_calcolo==2):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Routing su PD NON effettuato. Controllare il layer e rilanciare.')
        elif (result_calcolo==3):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su PD effettuato ma con qualche reticenza')
            
    def lancia_pfs_routing(self):
        #Associo PFS ai vertici pgr: in questo caso ci possono essere più vertici pgr coincidenti con lo stesso PFS.
        connInfo = SCALE_layer.source()
        result_calcolo = db_solid.pfs_routing(self, connInfo, theSchema)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Routing su PFS non eseguito!')
        elif (result_calcolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su PFS avvenuto con successo!')
        elif (result_calcolo==2):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Routing su PFS NON effettuato. Controllare il layer e rilanciare.')
        elif (result_calcolo==3):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su PFS effettuato ma con qualche reticenza')
            
    def lancia_pfp_routing(self):
        #Associo PFP ai vertici pgr: in questo caso ci possono essere più vertici pgr coincidenti con lo stesso PFP.
        connInfo = SCALE_layer.source()
        result_calcolo = db_solid.pfp_routing(self, connInfo, theSchema)
        if (result_calcolo==0):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Routing su PFP non eseguito!')
        elif (result_calcolo==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su PFP avvenuto con successo!')
        elif (result_calcolo==2):
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Routing su PFP NON effettuato. Controllare il layer e rilanciare.')
        elif (result_calcolo==3):
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Routing su PFP effettuato ma con qualche reticenza')
        
    #--------------------------------------------------------------------------
    
    def select_output_dir(self):
        dirname = QFileDialog.getExistingDirectory(self.dlg_config, "Open source directory","", QFileDialog.ShowDirsOnly)
        self.dlg_config.dirBrowse_txt.setText(dirname)
        #Verifico di avere tutte le informazioni necessarie per decidere se abilitare o meno il pulsante IMPORT
        #self.activate_import()
        
    def select_shp_scala(self):
        filename = QFileDialog.getOpenFileName(self.dlg_config, "Load SCALA layer","", '*.shp')
        self.dlg_config.shpBrowse_txt.setText(filename)
        #Verifico di avere tutte le informazioni necessarie per decidere se abilitare o meno il pulsante IMPORT
        filename_check = self.dlg_config.shpBrowse_txt.text()
        if (filename_check):
            self.dlg_config.import_scala.setEnabled(True);
        else:
            self.dlg_config.import_scala.setEnabled(False);
        
    def select_shp_cavo(self):
        filename = QFileDialog.getOpenFileName(self.dlg_config, "Load CAVO layer","", '*.shp')
        self.dlg_config.cavoBrowse_txt.setText(filename)
        #Verifico di avere tutte le informazioni necessarie per decidere se abilitare o meno il pulsante IMPORT
        filename_check = self.dlg_config.cavoBrowse_txt.text()
        if (filename_check):
            self.dlg_config.import_scala.setEnabled(True);
        else:
            self.dlg_config.import_scala.setEnabled(False);
    
    def select_output_dir_export(self):
        dirname = QFileDialog.getExistingDirectory(self.dlg_export, "Open source directory","", QFileDialog.ShowDirsOnly)
        self.dlg_export.dirBrowse_txt.setText(dirname)
        
    def exportDB(self):
        dirname_text = self.dlg_export.dirBrowse_txt.text()
        home = expanduser("~")
        if (dirname_text): #salvo il progetto nella directory indicata dall'utente
            home = dirname_text
            dst="%s/%s/" % (home, theSchema)
        else: #salvo sotto $HOME
            dst="%s/%s/" % (home, theSchema)
        try:
            if not os.path.exists(dst):
                os.makedirs(dst)
            
            #Prima di esportare i layers li ricarico dal DB, in modo tale da ricaricare i dati ed eventuali nuovi campi aggiunti ai vari layers.
            #svuoto e ricarico tutta la TOC:
            layers = self.iface.legendInterface().layers()
            for layer in reversed(layers): #reversed order cosi mantengo l'ordine originale
                URI = layer.source()
                nome = layer.name()
                QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
                #ricarico:
                re_layer = QgsVectorLayer(URI, nome, "postgres")
                QgsMapLayerRegistry.instance().addMapLayer(re_layer)
                re_layer.loadNamedStyle( os.getenv("HOME")+'/.qgis2/python/plugins/ProgettoFTTH_return/qml_base/%s.qml' % (nome) )
                _writer = QgsVectorFileWriter.writeAsVectorFormat(re_layer, dst+nome+'.shp', "utf-8", None, "ESRI Shapefile")

            '''
            #Esporto i vari layers:
            _writer = QgsVectorFileWriter.writeAsVectorFormat(SCALE_layer, dst+SCALE_layer.name()+'.shp',"utf-8",None,"ESRI Shapefile")
            _writer = QgsVectorFileWriter.writeAsVectorFormat(GIUNTO_layer, dst+GIUNTO_layer.name()+'.shp',"utf-8",None,"ESRI Shapefile")
            _writer = QgsVectorFileWriter.writeAsVectorFormat(PD_layer, dst+PD_layer.name()+'.shp',"utf-8",None,"ESRI Shapefile")
            _writer = QgsVectorFileWriter.writeAsVectorFormat(PFS_layer, dst+PFS_layer.name()+'.shp',"utf-8",None,"ESRI Shapefile")
            _writer = QgsVectorFileWriter.writeAsVectorFormat(PFP_layer, dst+PFP_layer.name()+'.shp',"utf-8",None,"ESRI Shapefile")
            _writer = QgsVectorFileWriter.writeAsVectorFormat(CAVO_layer, dst+CAVO_layer.name()+'.shp',"utf-8",None,"ESRI Shapefile")
            _writer = QgsVectorFileWriter.writeAsVectorFormat(CAVOROUTE_layer, dst+CAVOROUTE_layer.name()+'.shp',"utf-8",None,"ESRI Shapefile")
            _writer = QgsVectorFileWriter.writeAsVectorFormat(APFS_layer, dst+APFS_layer.name()+'.shp',"utf-8",None,"ESRI Shapefile")
            _writer = QgsVectorFileWriter.writeAsVectorFormat(APFP_layer, dst+APFP_layer.name()+'.shp',"utf-8",None,"ESRI Shapefile")
            #per ultimo estraggo il "nuovo" layer cavoroute_labels, se esiste in mappa altrimenti niente:
            try:
                LABELS_layer = QgsMapLayerRegistry.instance().mapLayersByName('cavoroute_labels')[0]
                _writer = QgsVectorFileWriter.writeAsVectorFormat(LABELS_layer, dst+LABELS_layer.name()+'.shp', "utf-8", None, "ESRI Shapefile")
            except:
                Utils.logMessage('Layer cavoroute_labels non trovato vado avanti')
            '''
        except SystemError, e:
            Utils.logMessage('Errore di sistema!')
            self.dlg_export.txtFeedback.setText('Errore di sistema! Esportazione fallita')
            return 0
        else:
            Utils.logMessage('Estrazione avvenuta in ' + dst)
            self.dlg_export.txtFeedback.setText('Estrazione avvenuta in ' + dst)
            QMessageBox.information(self.dock, self.dock.windowTitle(), 'Estrazione avvenuta con successo!')
            return 1

    #def inizializzaDB(con):
    def inizializzaDB(self):
        codice_lotto = self.dlg_config.schemaDB.text()
        #comuneDB = self.dlg_config.comuneDB.text()
        #dirname_text = self.dlg_config.dirBrowse_txt.text()
        try:
            #codpop = int(self.dlg_config.codpopDB.text())
            UI_PTA_min = int(self.dlg_config.UI_PTA_min.text())
            UI_PTA_max = int(self.dlg_config.UI_PTA_max.text())
            CONT_PTA_max = int(self.dlg_config.CONT_PTA_max.text())
            UI_GI_min = int(self.dlg_config.UI_GI_min.text())
            UI_GI_max = int(self.dlg_config.UI_GI_max.text())
            CONT_GI_max = int(self.dlg_config.CONT_GI_max.text())
            UI_PD_min = int(self.dlg_config.UI_PD_min.text())
            UI_PD_max = int(self.dlg_config.UI_PD_max.text())
            CONT_PD_max = int(self.dlg_config.CONT_PD_max.text())
            UI_PFS_min = int(self.dlg_config.UI_PFS_min.text())
            UI_PFS_max = int(self.dlg_config.UI_PFS_max.text())
            CONT_PFS_max = int(self.dlg_config.CONT_PFS_max.text())
            UI_PFP_min = int(self.dlg_config.UI_PFP_min.text())
            UI_PFP_max = int(self.dlg_config.UI_PFP_max.text())
            CONT_PFP_max = int(self.dlg_config.CONT_PFP_max.text())
            
            scala_pta_f4 = int(self.dlg_config.scala_pta_f4.text())
            scala_pta_f12 = int(self.dlg_config.scala_pta_f12.text())
            scala_pta_f24 = int(self.dlg_config.scala_pta_f24.text())
            scala_pta_f48 = int(self.dlg_config.scala_pta_f48.text())
            scala_pta_f72 = int(self.dlg_config.scala_pta_f72.text())
            scala_pta_f96 = int(self.dlg_config.scala_pta_f96.text())
            scala_pta_f144 = int(self.dlg_config.scala_pta_f144.text())
            scala_pta_f192 = int(self.dlg_config.scala_pta_f192.text())
            
            scala_giunto_f4 = int(self.dlg_config.scala_giunto_f4.text())
            scala_giunto_f12 = int(self.dlg_config.scala_giunto_f12.text())
            scala_giunto_f24 = int(self.dlg_config.scala_giunto_f24.text())
            scala_giunto_f48 = int(self.dlg_config.scala_giunto_f48.text())
            scala_giunto_f72 = int(self.dlg_config.scala_giunto_f72.text())
            scala_giunto_f96 = int(self.dlg_config.scala_giunto_f96.text())
            scala_giunto_f144 = int(self.dlg_config.scala_giunto_f144.text())
            scala_giunto_f192 = int(self.dlg_config.scala_giunto_f192.text())
            
            scala_pd_f4 = int(self.dlg_config.scala_pd_f4.text())
            scala_pd_f12 = int(self.dlg_config.scala_pd_f12.text())
            scala_pd_f24 = int(self.dlg_config.scala_pd_f24.text())
            scala_pd_f48 = int(self.dlg_config.scala_pd_f48.text())
            scala_pd_f72 = int(self.dlg_config.scala_pd_f72.text())
            scala_pd_f96 = int(self.dlg_config.scala_pd_f96.text())
            scala_pd_f144 = int(self.dlg_config.scala_pd_f144.text())
            scala_pd_f192 = int(self.dlg_config.scala_pd_f192.text())
            
            scala_pfs_f4 = int(self.dlg_config.scala_pfs_f4.text())
            scala_pfs_f12 = int(self.dlg_config.scala_pfs_f12.text())
            scala_pfs_f24 = int(self.dlg_config.scala_pfs_f24.text())
            scala_pfs_f48 = int(self.dlg_config.scala_pfs_f48.text())
            scala_pfs_f72 = int(self.dlg_config.scala_pfs_f72.text())
            scala_pfs_f96 = int(self.dlg_config.scala_pfs_f96.text())
            scala_pfs_f144 = int(self.dlg_config.scala_pfs_f144.text())
            scala_pfs_f192 = int(self.dlg_config.scala_pfs_f192.text())
            
            giunto_pd_f4 = int(self.dlg_config.giunto_pd_f4.text())
            giunto_pd_f12 = int(self.dlg_config.giunto_pd_f12.text())
            giunto_pd_f24 = int(self.dlg_config.giunto_pd_f24.text())
            giunto_pd_f48 = int(self.dlg_config.giunto_pd_f48.text())
            giunto_pd_f72 = int(self.dlg_config.giunto_pd_f72.text())
            giunto_pd_f96 = int(self.dlg_config.giunto_pd_f96.text())
            giunto_pd_f144 = int(self.dlg_config.giunto_pd_f144.text())
            giunto_pd_f192 = int(self.dlg_config.giunto_pd_f192.text())
            
            pta_pd_f4 = int(self.dlg_config.pta_pd_f4.text())
            pta_pd_f12 = int(self.dlg_config.pta_pd_f12.text())
            pta_pd_f24 = int(self.dlg_config.pta_pd_f24.text())
            pta_pd_f48 = int(self.dlg_config.pta_pd_f48.text())
            pta_pd_f72 = int(self.dlg_config.pta_pd_f72.text())
            pta_pd_f96 = int(self.dlg_config.pta_pd_f96.text())
            pta_pd_f144 = int(self.dlg_config.pta_pd_f144.text())
            pta_pd_f192 = int(self.dlg_config.pta_pd_f192.text())
            
            pd_pfs_f4 = int(self.dlg_config.pd_pfs_f4.text())
            pd_pfs_f12 = int(self.dlg_config.pd_pfs_f12.text())
            pd_pfs_f24 = int(self.dlg_config.pd_pfs_f24.text())
            pd_pfs_f48 = int(self.dlg_config.pd_pfs_f48.text())
            pd_pfs_f72 = int(self.dlg_config.pd_pfs_f72.text())
            pd_pfs_f96 = int(self.dlg_config.pd_pfs_f96.text())
            pd_pfs_f144 = int(self.dlg_config.pd_pfs_f144.text())
            pd_pfs_f192 = int(self.dlg_config.pd_pfs_f192.text())
            
            pfs_pfp_f96 = int(self.dlg_config.pfs_pfp_f96.text())
        except ValueError:
            self.dlg_config.txtFeedback.setText('Specificare TUTTE le variabili come NUMERI INTERI!')
            return False
        Utils.logMessage('Selected schema: ' + codice_lotto)
        test_conn = None
        cur = None
        try:
            #if ( len(str(codpop))> 3):
            #    raise NameError('COD_POP: massimo 3 cifre')
            #Verifico che le variabili inserite siano numeri interi:
            if not( isinstance(UI_GI_min, (int, long)) ) or  not( isinstance(UI_GI_max, (int, long)) ) or  not( isinstance(CONT_GI_max, (int, long)) ):
                raise NameError('Specificare TUTTE le variabili per i GIUNTI come NUMERI INTERI!')
            if not( isinstance(UI_PD_min, (int, long)) ) or  not( isinstance(UI_PD_max, (int, long)) ) or  not( isinstance(CONT_PD_max, (int, long)) ):
                raise NameError('Specificare TUTTE le variabili per i PD come NUMERI INTERI!')
            if not( isinstance(UI_PFS_min, (int, long)) ) or  not( isinstance(UI_PFS_max, (int, long)) ) or  not( isinstance(CONT_PFS_max, (int, long)) ):
                raise NameError('Specificare TUTTE le variabili per i PFS come NUMERI INTERI!')
            if not( isinstance(UI_PFP_min, (int, long)) ) or  not( isinstance(UI_PFP_max, (int, long)) ) or  not( isinstance(CONT_PFP_max, (int, long)) ):
                raise NameError('Specificare TUTTE le variabili per i PFP come NUMERI INTERI!')

            test_conn = psycopg2.connect(dest_dir)
            cur = test_conn.cursor()
            
            #Aggiorno la tabella delle variabili di progetto: come costruire la query in modo intelligente nel caso di valori vuoti??
            query_variabili_progetto = """UPDATE %s.variabili_progetto_return SET
            pta_ui_min=%i, pta_ui_max=%i, pta_cont_max=%i, giunto_ui_min=%i, 
            giunto_ui_max=%i, giunto_cont_max=%i, pd_ui_min=%i, pd_ui_max=%i, 
            pd_cont_max=%i, pfs_ui_min=%i, pfs_ui_max=%i, pfs_pd_max=%i, pfp_ui_min=%i, 
            pfp_ui_max=%i, pfp_pfs_max=%i, scala_pta_f4=%i, scala_pta_f12=%i, 
            scala_pta_f24=%i, scala_pta_f48=%i, scala_pta_f72=%i, scala_pta_f96=%i, 
            scala_pta_f144=%i, scala_pta_f192=%i, scala_giunto_f4=%i, scala_giunto_f12=%i, 
            scala_giunto_f24=%i, scala_giunto_f48=%i, scala_giunto_f72=%i, scala_giunto_f96=%i, 
            scala_giunto_f144=%i, scala_giunto_f192=%i, scala_pd_f4=%i, scala_pd_f12=%i, 
            scala_pd_f24=%i, scala_pd_f48=%i, scala_pd_f72=%i, scala_pd_f96=%i, 
            scala_pd_f144=%i, scala_pd_f192=%i, scala_pfs_f4=%i, scala_pfs_f12=%i, 
            scala_pfs_f24=%i, scala_pfs_f48=%i, scala_pfs_f72=%i, scala_pfs_f96=%i, 
            scala_pfs_f144=%i, scala_pfs_f192=%i, giunto_pd_f4=%i, giunto_pd_f12=%i, 
            giunto_pd_f24=%i, giunto_pd_f48=%i, giunto_pd_f72=%i, giunto_pd_f96=%i, 
            giunto_pd_f144=%i, giunto_pd_f192=%i, pta_pd_f4=%i, pta_pd_f12=%i, 
            pta_pd_f24=%i, pta_pd_f48=%i, pta_pd_f72=%i, pta_pd_f96=%i, pta_pd_f144=%i, 
            pta_pd_f192=%i, pd_pfs_f4=%i, pd_pfs_f12=%i, pd_pfs_f24=%i, pd_pfs_f48=%i, 
            pd_pfs_f72=%i, pd_pfs_f96=%i, pd_pfs_f144=%i, pd_pfs_f192=%i, pfs_pfp_f96=%i""" % (codice_lotto, UI_PTA_min, UI_PTA_max, CONT_PTA_max, UI_GI_min, UI_GI_max, CONT_GI_max, UI_PD_min, UI_PD_max, CONT_PD_max, UI_PFS_min, UI_PFS_max, CONT_PFS_max, UI_PFP_min, UI_PFP_max, CONT_PFP_max, scala_pta_f4, scala_pta_f12, scala_pta_f24, scala_pta_f48, scala_pta_f72, scala_pta_f96, scala_pta_f144, scala_pta_f192, scala_giunto_f4, scala_giunto_f12, scala_giunto_f24, scala_giunto_f48, scala_giunto_f72, scala_giunto_f96, scala_giunto_f144, scala_giunto_f192, scala_pd_f4, scala_pd_f12, scala_pd_f24, scala_pd_f48, scala_pd_f72, scala_pd_f96, scala_pd_f144, scala_pd_f192, scala_pfs_f4, scala_pfs_f12, scala_pfs_f24, scala_pfs_f48, scala_pfs_f72, scala_pfs_f96, scala_pfs_f144, scala_pfs_f192, giunto_pd_f4, giunto_pd_f12, giunto_pd_f24, giunto_pd_f48, giunto_pd_f72, giunto_pd_f96, giunto_pd_f144, giunto_pd_f192, pta_pd_f4, pta_pd_f12, pta_pd_f24, pta_pd_f48, pta_pd_f72, pta_pd_f96, pta_pd_f144, pta_pd_f192, pd_pfs_f4, pd_pfs_f12, pd_pfs_f24, pd_pfs_f48, pd_pfs_f72, pd_pfs_f96, pd_pfs_f144, pd_pfs_f192, pfs_pfp_f96)
            cur.execute(query_variabili_progetto)
            # Make the changes to the database persistent
            test_conn.commit()
            cur.close()
            #Allo stesso tempo riaggiorno la variabile FROM_TO_RULES nel caso tenessi aperte alcune finestre:
            global FROM_TO_RULES
            FROM_TO_RULES = {
                'PTA': {'MIN_UI': UI_PTA_min, 'MAX_UI': UI_PTA_max, 'MAX_CONT': CONT_PTA_max},
                'GIUNTO': {'MIN_UI': UI_GI_min, 'MAX_UI': UI_GI_max, 'MAX_CONT': CONT_GI_max},
                'PD': {'MIN_UI': UI_PD_min, 'MAX_UI': UI_PD_max, 'MAX_CONT': CONT_PD_max},
                'PFS': {'MIN_UI': UI_PFS_min, 'MAX_UI': UI_PFS_max, 'MAX_CONT': CONT_PFS_max},
                'PFP': {'MIN_UI': UI_PFP_min, 'MAX_UI': UI_PFP_max, 'MAX_CONT': CONT_PFP_max}
            }
            FROM_TO_RULES['GIUNTO_F_dev'] = FROM_TO_RULES['GIUNTO']
            FROM_TO_RULES['SCALA'] = FROM_TO_RULES['PTA']
        except NameError as err:
            self.dlg_config.txtFeedback.setText(err.args[0])
            return 0;
        except psycopg2.Error, e:
            Utils.logMessage(e.pgerror)
            self.dlg_config.txtFeedback.setText(e.pgerror)
            return 0;
        except SystemError, e:
            Utils.logMessage('Errore di sistema!')
            self.dlg_config.txtFeedback.setText('Errore di sistema!')
            return 0
        else:
            self.dlg_config.txtFeedback.setText('Modifica delle variabili del nuovo progetto Inizializzazione avvenuta con successo!')
        finally:
            if test_conn:
                test_conn.close()


    def inizializza_layer(self):
        #Iniziamo col definire i layer che mi interessano andandoli a cercare nella legenda, visto che altrimenti non saprei come definirli:
        global SCALE_layer
        global PD_layer
        global GIUNTO_layer
        global GIUNTO_F_dev_layer
        global PFS_layer
        global PFP_layer
        global CAVO_layer
        global CAVOROUTE_layer
        global APFS_layer
        global APFP_layer
        global epsg_srid
        #layers_caricati = iface.legendInterface().layers()
        #ERRORE! Appena si avvia QGis non sa quali layer ha caricati, dunque da un errore perche queste LISTE sono VUOTE. Per questo motivo le richiamo all'interno di una funzione.
        msg = QMessageBox()
        msg.setWindowTitle("Aggiungere il layer mancante alla TOC di QGis")
        try:
            SCALE_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.LAYER_NAME['SCALA'])[0]
            crs = SCALE_layer.crs()
            epsg_srid = int(crs.postgisSrid())
            self.epsg_srid = epsg_srid
            #Utils.logMessage("Layer Scale: " + SCALE_layer.name())
            GIUNTO_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.LAYER_NAME['GIUNTO'])[0]
            #Utils.logMessage("Layer Giunto: " + GIUNTO_layer.name())
            GIUNTO_F_dev_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.LAYER_NAME['GIUNTO_F_dev'])[0]
            PD_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.LAYER_NAME['PD'])[0]
            #Utils.logMessage("Layer PD: " + PD_layer.name())
            PFS_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.LAYER_NAME['PFS'])[0]
            #Utils.logMessage("Layer PFS: " + PFS_layer.name())
            PFP_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.LAYER_NAME['PFP'])[0]
            #Utils.logMessage("Layer PFP: " + PFP_layer.name())
            
            #Altri layers che mi saranno utili per l'esportazione:
            CAVO_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.LAYER_NAME['CAVO'])[0]
            CAVOROUTE_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.LAYER_NAME['CAVOROUTE'])[0]
            APFS_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.LAYER_NAME['Area_PFS'])[0]
            APFP_layer = QgsMapLayerRegistry.instance().mapLayersByName(self.LAYER_NAME['Area_PFP'])[0]
        
        except IndexError as err:
            Utils.logMessage(err.args[0])
            msg.setText("Un layer fondamentale per il plugin manca nella TOC")
            msg.setDetailedText("I layer che servono al plugin sono elencati di seguito. Notare che le lettere maiuscole-minuscole devono essere rispettate nel nome del layer nella TOC, mentre invece l'ordine non ha importanza: Scala, Giunti, PD, PFS, PFP, Area_PFS, Area_PFP, Cavo, Cavoroute.")
            msg.setIcon(QMessageBox.Critical)
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            return 0
        
        else:
            Utils.logMessage("I layers necessari sono presenti sulla TOC di QGis. Posso proseguire")
            return 1
        
    '''def attivo_associazione(self):
        if (check_origine+check_dest==2):
            QMessageBox.information(self.dock, self.dock.windowTitle(),
                'I vincoli sembrano essere rispettati. Si puo\' procedere con l\'associazione di ' + str(TOT_UI_origine) + 'UI dai punti di origine con le ' + str(TOT_UI_dest) + 'UI del punto di destinazione')
            self.dlg.importBtn.setEnabled(True)
        elif (check_origine==1 and check_dest==0):
            QMessageBox.information(self.dock, self.dock.windowTitle(),
                "Per poter procedere con l'associazione occorre selezionare UN punto di destinazione valido")
            self.dlg.importBtn.setEnabled(False)
        elif (check_origine==0 and check_dest==1):
            QMessageBox.information(self.dock, self.dock.windowTitle(),
                "Per poter procedere con l'associazione occorre selezionare dei punti di origine validi")
            self.dlg.importBtn.setEnabled(False)
        else:
            self.dlg.importBtn.setEnabled(False)'''

    def casistica_layer(self, layer_da_attivare):
        if (layer_da_attivare == SCALE_layer.name()):
            iface.setActiveLayer(SCALE_layer)
            return SCALE_layer, 'SCALA'
        elif (layer_da_attivare == GIUNTO_layer.name()):
            iface.setActiveLayer(GIUNTO_layer)
            return GIUNTO_layer, 'GIUNTO'
        elif (layer_da_attivare == GIUNTO_F_dev_layer.name()):
            iface.setActiveLayer(GIUNTO_F_dev_layer)
            return GIUNTO_F_dev_layer, 'GIUNTO_F_dev'
        elif (layer_da_attivare == PD_layer.name()):
            iface.setActiveLayer(PD_layer)
            return PD_layer, 'PD'
        elif (layer_da_attivare == PFS_layer.name()):
            iface.setActiveLayer(PFS_layer)
            return PFS_layer, 'PFS'
        elif (layer_da_attivare == PFP_layer.name()):
            iface.setActiveLayer(PFP_layer)
            return PFP_layer, 'PFP'
    
    def updateFromSelection_compare(self):
        result_init = self.inizializza_layer()
        if (result_init==0):
            return 0
        layer_da_attivare = self.dlg_compare.comboBoxFromPoint.currentText()
        if (layer_da_attivare != self.FROM_POINT[0]):
            self.dlg_compare.fileBrowse_btn.setEnabled(True)
            Utils.logMessage("Layer origine da attivare: " + layer_da_attivare)
            chiave = self.casistica_layer(layer_da_attivare)[1]
        else:
            self.dlg_compare.fileBrowse_btn.setEnabled(False)
    
    def controlla_connessioni(self):
        global check_compare #variabile booleana che mi dice se e' tutto ok lato origine
        check_origine = 0
        global selected_features_compare
        global selected_features_ids_compare
        #In realta e' meglio forzare che il layer attivo sia quello selezionato nel menu a tendina o meglio che qui vengano presi gli elementi selezionati dal layer scelto:
        nomelayer_scelto = self.dlg_compare.comboBoxFromPoint.currentText()
        layer = self.casistica_layer(nomelayer_scelto)[0] #questo e' il layer scelto, che attivo e da cui prendo le selezioni
        chiave_compare = self.casistica_layer(nomelayer_scelto)[1] #chiave del layer scelto
        layername = layer.name()
        counted_selected = layer.selectedFeatureCount()
        Utils.logMessage(str(counted_selected))
        if (counted_selected<1):
            check_origine = 0
            QMessageBox.warning(self.dock_compare, self.dock_compare.windowTitle(),
                'ATTENZIONE! Non si e\' selezionato alcun elemento dal layer scelto! - \'' + layername + '\'')
        elif (counted_selected > 1):
            check_dest = 0
            QMessageBox.critical(self.dock_compare, self.dock_compare.windowTitle(), 'ATTENZIONE! Non e\' possibile selezionare piu di un punto sul quale eseguire la verifica delle connessioni!')
        else:
            #Recupero gli estremi di connessione del layer scelto:
            #connInfo = QgsDataSourceURI(fileName.dataProvider().dataSourceUri()).connectionInfo()
            connInfo = layer.source()
            Utils.logMessage(connInfo)
            selected_features_compare = layer.selectedFeatures()
            selected_features_ids_compare = layer.selectedFeaturesIds()
            for i in selected_features_compare:
                id_compare = i[self.ID_NAME[chiave_compare]]
            #Utils.logMessage("ID del punto destinazione = " + id_compare)
            id_giunti_figli, id_scale_figli, id_pd_padre, id_pfs_padre, n_cont, n_ui, n_giunti, gid_cavoroute, id_giunto_padre = db_compare.recupero_relazioni_punti(connInfo, id_compare, chiave_compare, self)
            Utils.logMessage(str(len(id_giunto_padre)))
            if (chiave_compare=='GIUNTO'):
                if (str(id_giunto_padre)=='[None]'): #si e' selezionato un padre: elenco i figli
                    feedback_text_raw = """ID elemento selezionato: %(id_compare)s
CONNESSIONI:
UI: %(n_ui)s
CONTATORI: %(n_cont)s
GIUNTI figli: %(n_giunti)s
PD: %(id_pd)s
PFS: %(id_pfs)s"""
                    feedback_text = feedback_text_raw % {'id_compare': id_compare, 'id_pd': id_pd_padre, 'id_pfs': id_pfs_padre, 'n_ui': n_ui, 'n_giunti': id_giunti_figli, 'n_cont': n_cont}
                else: #si e' selezionato un figlio: elenco IL padre
                    feedback_text_raw = """ID elemento selezionato: %(id_compare)s
CONNESSIONI:
UI: %(n_ui)s
CONTATORI: %(n_cont)s
GIUNTO padre: %(n_giunti)s
PD: %(id_pd)s
PFS: %(id_pfs)s"""
                    feedback_text = feedback_text_raw % {'id_compare': id_compare, 'id_pd': id_pd_padre, 'id_pfs': id_pfs_padre, 'n_ui': n_ui, 'n_giunti': id_giunto_padre, 'n_cont': n_cont}
            else:
                feedback_text_raw = """ID elemento selezionato: %(id_compare)s
CONNESSIONI:
UI: %(n_ui)s
CONTATORI: %(n_cont)s
GIUNTI: %(n_giunti)s
PD: %(id_pd)s
PFS: %(id_pfs)s"""
                feedback_text = feedback_text_raw % {'id_compare': id_compare, 'id_pd': id_pd_padre, 'id_pfs': id_pfs_padre, 'n_ui': n_ui, 'n_giunti': n_giunti, 'n_cont': n_cont}
            self.dlg_compare.txtFeedback.setText(feedback_text)
            #Svuoto le selezioni dagli altri layer e aggiungo quelle corrette:
            Utils.logMessage('id_pd_padre=' + str(type(id_pd_padre)))
            if not(chiave_compare=='SCALA'):
                SCALE_layer.removeSelection()
                if not(None in id_scale_figli):
                    SCALE_layer.setSelectedFeatures( id_scale_figli )
            if not(chiave_compare=='GIUNTO'):
                GIUNTO_layer.removeSelection()
                if not(None in id_giunti_figli):
                    GIUNTO_layer.setSelectedFeatures( id_giunti_figli )
            if not(chiave_compare=='PD'):
                PD_layer.removeSelection()
                if not(None in id_pd_padre): #evito che QGis faccia una selezione fittizia se la lista e' tutta vuota
                    PD_layer.setSelectedFeatures( id_pd_padre )
            if not(chiave_compare=='PFS'):
                PFS_layer.removeSelection()
                if not(None in id_pfs_padre):
                    PFS_layer.setSelectedFeatures( id_pfs_padre )
            #In ogni caso se il cavoroute e' gia' stato compilato, seleziono il tracciato di competenza:
            CAVOROUTE_layer.removeSelection()
            if not(None in gid_cavoroute):
                CAVOROUTE_layer.setSelectedFeatures( gid_cavoroute )
                #perche' non me lo seleziona???
    
    def associa_scala_scala(self):
        self.associa_punti_origine_gg('SCALA_F', 'SCALA')
    
    #def associa_scala_giunto(self):
    #    self.associa_punti_origine('SCALA', 'GIUNTO')
        
    def associa_scala_pta(self):
        self.associa_punti_origine('SCALA', 'PTA')
        
    def associa_scala_muffola(self):
        self.associa_punti_origine('SCALA', 'GIUNTO')
    
    def associa_scala_pd(self):
        self.associa_punti_origine('SCALA', 'PD')
        self.associa_punti_origine('GIUNTO', 'PD')
    
    def associa_scala_pfs(self):
        self.associa_punti_origine('SCALA', 'PFS')
        
    def associa_giunto_giunto_dev(self):
        self.associa_punti_origine_gg('GIUNTO_F_dev', 'GIUNTO')

    #porto tutto sotto un unico pulsante scala_pd
    #def associa_giunto_pd(self):
    #    self.associa_punti_origine('GIUNTO', 'PD')
    
    def associa_pta_pfs(self):
        self.associa_punti_origine('PTA', 'PFS')
    
    def associa_pd_pd(self):
        self.associa_punti_origine_gg('PD_F', 'PD')
    
    def associa_pd_pfs(self):
        self.associa_punti_origine('PD', 'PFS')
        
    def associa_pfs_pfp(self):
        self.associa_punti_origine('PFS', 'PFP')
    
    def associa_punti_origine_gg(self, chiave_origine, chiave_dest):
        #Connex giunto-giunto, scala-scala e pd-pd
        global check_origine #variabile booleana che mi dice se e' tutto ok lato origine
        check_origine = 0
        global selected_features_origine
        global selected_features_ids_origine
        global TOT_UI_origine
        global TOT_ncont_origine
        global ids_giunto
        ids_giunto = list()
        global dict_giunti_f
        dict_giunti_f = dict()
        global dict_giunto_p
        dict_giunto_p = dict()
        selected_features_ids_dest = list()
        layer = self.casistica_layer(self.LAYER_NAME[chiave_origine])[0] #questo e' il layer scelto, che attivo e da cui prendo le selezioni
        layername = layer.name()
        counted_selected = layer.selectedFeatureCount()
        if (counted_selected<1):
            check_origine = 0
            QMessageBox.warning(self.dlg, self.dlg.windowTitle(),
                'ATTENZIONE! Non si e\' selezionato alcun elemento dal layer di origine scelto! - \'' + layername + '\'')
        else:
            selected_features_origine = layer.selectedFeatures()
            TOT_UI_origine = 0
            TOT_ncont_origine = 0
            
            '''FACCIO SCEGLIERE PRIMA IL PADRE in modo da permettere l'associazione a punti gia' associati'''
            for i in selected_features_origine:
                id_campo_oggetto = self.ID_NAME[chiave_dest]
                #Utils.logMessage("id_campo_oggetto=" + str(id_campo_oggetto))
                #creo menu a tendina con ID di tutti i punti selezionati
                if ( i[id_campo_oggetto] ):
                    ids_giunto.append(i[id_campo_oggetto])
                    if (i['n_ui']):
                        dict_giunti_f[i[id_campo_oggetto]] = [i['gid'], i['n_ui']] #mi creo un dict dove associo ID_NAME al GID e UI
                    else:
                        dict_giunti_f[i[id_campo_oggetto]] = [i['gid'], 0]
                
            cippa = QInputDialog()
            cippa.setComboBoxItems(ids_giunto)
            cippa.setWindowTitle('Seleziona ID del Padre')
            cippa.setLabelText('Seleziona ID del Padre')
            retval = cippa.exec_()
            Utils.logMessage("retval="+str(retval))
            if (retval != 1): #l'utente NON ha cliccato ok: sceglie di fermarsi, esco
                return 0
            ID_GIUNTO_padre = str(cippa.textValue())
            #A questo punto CONOSCO IL GID PADRE: cosa faccio???
            #Lo rimuovo dalla selezione ma mi salvo l'ID:
            dict_giunto_p = dict_giunti_f[ID_GIUNTO_padre]
            del dict_giunti_f[ID_GIUNTO_padre]
            Utils.logMessage("ID padre=" + str(dict_giunto_p) + " - IDs figli=" + str(dict_giunti_f))
            #TOT_UI_origine = TOT_UI_origine - dict_giunto_p[1]
            #TOT_ncont_origine = counted_selected - 1
            #Deseleziono il giunto_padre cosi per i controlli successivi ho solo i figli:
            selected_features_ids_origine = layer.selectedFeaturesIds()
            if dict_giunto_p[0] in selected_features_ids_origine:
                idx_padre = selected_features_ids_origine.index(dict_giunto_p[0])
                selected_features_ids_dest.append(selected_features_ids_origine[idx_padre]) #contiene solo il padre
                selected_features_ids_origine.remove(dict_giunto_p[0]) #contiene tutti tranne il padre
                Utils.logMessage("Rimuovo il padre dalla selezione di origine con " + str(id_campo_oggetto) + " = " + str(dict_giunto_p[0]))
            #a questo punto devo pero' riselezionare i figli:
            layer.removeSelection() #ripulisco la selezione
            layer.setSelectedFeatures( selected_features_ids_origine )
            selected_features_origine = layer.selectedFeatures()
            
            #A questo punto ricontrollo il rispetto delle condizioni sul numero dei pti selezionati rimasti come figli:         
            for i in selected_features_origine:
                #Faccio un controllo se il punto di origine non sia gia' connesso con qualcosa.In realta' mi pare che se TUTTI i pti origine hanno ID_PFP non debbano venir connessi!
                if (i['id_pfp']):
                    QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Hai selezionato un elemento gia' connesso! Verra deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                    layer.deselect( i['gid'] )
                    continue
                #Se parto da GIUNTO non deve avere PD e non deve gia' avere un GIUNTO_FIGLIO:
                if (layername==self.LAYER_NAME['GIUNTO']):
                    if ( i['id_pd'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un giunto gia' associato a un PD! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                    elif ( i[self.ID_NAME[chiave_origine]] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un giunto gia' associato a un altro giunto! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                #Se parto da SCALA non deve avere GIUNTO o PD o PFS ne essere gia' connessa ad altra SCALA:
                if (layername==self.LAYER_NAME['SCALA']):
                    if ( i['id_giunto'] or i['id_pd'] or i['id_pfs'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare una scala gia' associata a un GIUNTO-PD-PFS! Verra' deselezionata e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                    elif ( i[self.ID_NAME[chiave_origine]] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare una scala gia' associata ad un'altra scala! Verra' deselezionata e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                #Se parto da PD non deve avere PFS ne essere gia' connesso ad altro PD:
                if (layername==self.LAYER_NAME['PD']):
                    if ( i['id_pfs'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un PD gia' associato a un PFS! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                    elif ( i[self.ID_NAME[chiave_origine]] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un PD gia' associato ad un altro PD! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                #RECUPERO I DATI dei punti origine rimasti validi:
                if (i['n_ui']):
                    TOT_UI_origine = TOT_UI_origine + i['n_ui']
                #recupero gli ID degli elementi di origine. Posso usare chiave_dest perche' in questo caso sto associando elementi dello stesso layer..!
                id_campo_oggetto = self.ID_NAME[chiave_dest]
                #Utils.logMessage("id_campo_oggetto=" + str(id_campo_oggetto))
                if ( i[id_campo_oggetto] ):
                    ids_giunto.append(i[id_campo_oggetto])
                    if (i['n_ui']):
                        dict_giunti_f[i[id_campo_oggetto]] = [i['gid'], i['n_ui']] #mi creo un dict dove associo ID_NAME al GID e UI
                    else:
                        dict_giunti_f[i[id_campo_oggetto]] = [i['gid'], 0]
            #A questo punto ricontrollo il rispetto delle condizioni sul numero dei pti selezionati:
            counted_selected = layer.selectedFeatureCount()
            selected_features_ids_origine = layer.selectedFeaturesIds()
            if (counted_selected<1):
                check_origine = 0
                QMessageBox.warning(self.dock, self.dock.windowTitle(),
                'ATTENZIONE! Non si e\' selezionato alcun elemento valido dal layer di origine scelto! - \'' + layername + '\'')
            else:
                #Ridefinisco la selezione origine:
                layer.removeSelection() #ripulisco la selezione
                layer.setSelectedFeatures( selected_features_ids_origine )
                Utils.logMessage("IDs origine selezionati=" + str(selected_features_ids_origine))
                selected_features_origine = layer.selectedFeatures()
                #A questo punto ricontrollo il rispetto delle condizioni sul numero dei pti selezionati:
                counted_selected = layer.selectedFeatureCount()
                if (counted_selected<1):
                    check_origine = 0
                    QMessageBox.warning(self.dock, self.dock.windowTitle(),
                        'ATTENZIONE! Non si e\' selezionato alcun elemento valido dal layer di origine scelto! - \'' + layername + '\'')
                    return 0
                TOT_ncont_origine = counted_selected
                layer.removeSelection() #ripulisco la selezione
                layer.setSelectedFeatures( selected_features_ids_dest )
                Utils.logMessage("ID destinazione selezionato=" + str(selected_features_ids_dest))
                check_origine = 1
                #A questo punto passo a verificare i punti destinazione:
                self.associa_punti_destinazione(chiave_origine, chiave_dest)
    
    def associa_punti_origine(self, chiave_origine, chiave_dest):
        #self.inizializza_layer() #provo a lanciarlo dal run cioe' appena si clicca sul pulsante del plugin
        Utils.logMessage("connessione %s-%s" % (chiave_origine, chiave_dest))
        Utils.logMessage("--- CHECK ORIGINE ---")
        global check_origine #variabile booleana che mi dice se e' tutto ok lato origine
        check_origine = 0
        global selected_features_origine
        global selected_features_ids_origine
        global TOT_UI_origine
        global TOT_ncont_origine
        global TOT_n_pd_origine
        global TOT_n_pfs_origine
        #In realta e' meglio forzare che il layer attivo sia quello selezionato nel menu a tendina o meglio che qui vengano presi gli elementi selezionati dal layer scelto:
        #nomelayer_scelto = self.dlg.comboBoxFromPoint.currentText()
        layer = self.casistica_layer(self.LAYER_NAME[chiave_origine])[0] #questo e' il layer scelto, che attivo e da cui prendo le selezioni
        layername = layer.name()
        counted_selected = layer.selectedFeatureCount()
        if (counted_selected<1):
            check_origine = 0
            QMessageBox.warning(self.dlg, self.dlg.windowTitle(),
                'ATTENZIONE! Non si e\' selezionato alcun elemento dal layer di origine scelto! - \'' + layername + '\'')
        else:
            selected_features_origine = layer.selectedFeatures()
            selected_features_ids_origine = layer.selectedFeaturesIds()
            #iface.mainWindow().statusBar().showMessage("Estraggo gli elementi selezionati") #fa vedere qualcosa nella barra in basso a sx
            TOT_UI_origine = 0
            TOT_ncont_origine = 0
            TOT_n_pd_origine = 0
            TOT_n_pfs_origine = 0
            for i in selected_features_origine:
                #attrs = i.attributes() #version 2, return a list
                
                #VERIFICHE SE IL PUNTO E' GIA' ASSOCIATO O MENO
                #Faccio un controllo se il punto di origine non sia gia' connesso con qualcosa.In realta' mi pare che se TUTTI i pti origine hanno ID_PFP non debbano venir connessi!
                if (i['id_pfp']):
                    QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Hai selezionato un elemento gia' connesso! Verra deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                    layer.deselect( i['gid'] )
                    continue
                #Se parto da SCALA non deve avere GIUNTO o PD o PFS ne' essere connessa ad altra SCALA:
                if (layername==self.LAYER_NAME['SCALA']):
                    if ( i['id_pd'] or i['id_giunto'] or i['id_pfs']):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un contatore gia' associato a un giunto o a un PD o a un PFS! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                    elif ( i['id_sc_ref'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare una scala gia' associata ad un'altra scala! Verra' deselezionata e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                #Se parto da GIUNTO non deve avere PD e non deve gia' avere un GIUNTO_FIGLIO:
                if (layername==self.LAYER_NAME['GIUNTO']):
                    if ( i['id_pd'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un giunto gia' associato a un PD! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                    elif ( i['id_g_ref'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un giunto gia' associato a un altro giunto! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                #Nel caso di PTA-PFS chiaramente il PTA non deve gia' essere collegato a un PFS:
                if (chiave_origine=='PTA' and chiave_dest=='PFS' and layername==self.LAYER_NAME['GIUNTO']):
                    if ( i['id_pfs'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un giunto gia' associato a un PFS! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                    if ( str(i['tipo_giunt']).lower()!='pta' ):
                        QMessageBox.critical(self.dock, self.dock.windowTitle(),
                            "Hai selezionato un elemento di origine che non e' PTA o che non e' stato definito nel campo tipo_giunt. Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                #Se parto da PD non deve avere PFS ne' essere connesso ad altro PD:
                if (layername==self.LAYER_NAME['PD']):
                    if ( i['id_pfs'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un PD gia' associato a un PFS! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                    elif ( i['id_pd_ref'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un PD gia' associato ad un altro PD! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                #Se parto da PFS non deve avere PFP:
                if (layername==self.LAYER_NAME['PFS']):
                    if ( i['id_pfp'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Non e' possibile associare un PFS gia' associato a un PFP! Verra' deselezionato e si continueranno ad analizzare gli altri elementi selezionati")
                        layer.deselect( i['gid'] )
                        continue
                
                #RECUPERO I DATI dei punti origine rimasti validi:
                if (i['n_ui']):
                    TOT_UI_origine = TOT_UI_origine + i['n_ui']
                #Controllo adesso nel caso di GIUNTO o PD se e' associato a quanti contatori - NO!! Questa propriet' NON SI SOMMA poiche' una volta connessi valgono entambi UN CONTATORE
                '''if ( (layername==self.LAYER_NAME['GIUNTO']) or (layername==self.LAYER_NAME['PD']) ):
                    if (i['n_cont']):
                        TOT_ncont_origine = TOT_ncont_origine + i['n_cont']'''
                #print i['denominazi'] #print field value - NON in questo modo ma con un indice INTERO!
                #print attrs #[49L, u'automatiche', u'RIFUGIOVACCARONE', 603.0, 336309.0, 5002391.0, 2745.0, u'vaccarone_aut.png', 4]
            
            #A questo punto ricontrollo il rispetto delle condizioni sul numero dei pti selezionati:
            counted_selected = layer.selectedFeatureCount()
            selected_features_ids_origine = layer.selectedFeaturesIds()
            if (counted_selected<1):
                check_origine = 0
                QMessageBox.warning(self.dock, self.dock.windowTitle(),
                'ATTENZIONE! Non si e\' selezionato alcun elemento valido dal layer di origine scelto! - \'' + layername + '\'')
            else:
                Utils.logMessage("TOT UI origine = " + str(TOT_UI_origine))
                #Controllo: nel caso di SCALA_PTA le UI non devono esser maggiori di 3:
                if (chiave_origine=='SCALA' and chiave_dest=='PTA' and TOT_UI_origine>3):
                    #QMessageBox.critical(self.dock, self.dock.windowTitle(), "ATTENZIONE! Non e' possibile portare piu' di 3UI ad un PTA!")
                    #return 0
                    #questo errore dovrebbe essere BLOCCANTE se una singola SCALA>3UI si collega ad un PTA, ma al momento non riesco a sviluppare questa cosa dunque metto solo un avviso generale:
                    msg = QMessageBox()
                    msg.setText("Stai associando un numero totale di UI>3 da SCALE ad un PTA: desideri comunque continuare?")
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Attenzione possibile errore: continuare?")
                    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    retval = msg.exec_()
                    #if (retval != 1024): #l'utente NON ha cliccato ok: sceglie di fermarsi, esco
                    if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                        return 0
                if (chiave_origine=='SCALA' and chiave_dest!='PTA' and TOT_UI_origine<=3):
                    msg = QMessageBox()
                    msg.setText("Stai associando delle SCALE con delle UI <=3 ad un punto della rete non PTA: desideri comunque continuare?")
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Vincoli di progetto non rispettati: continuare?")
                    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    retval = msg.exec_()
                    #if (retval != 1024): #l'utente NON ha cliccato ok: sceglie di fermarsi, esco
                    if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                        return 0                    
                    #QMessageBox.warning(self.dock, self.dock.windowTitle(), "Stai associando delle SCALE con delle UI <=3 ad un punto della rete non PTA: desideri comunque continuare?")
                    
                #A prescindere del tipo di origine, conto quanti punti ho selezionato che varranno poi in seguito come CONTATORI
                '''#ECCEZIONE nel caso di connex GIUNTO-GIUNTO - forse ho risolto la questione duplicando il layer GIUNTO e chiamandolo Giunto_Figlio:
                if (chiave_origine=='GIUNTO' and chiave_dest=='GIUNTO'):
                    #PONGO il vincolo di non selezionare piu' di 3 GIUNTI:
                    if (counted_selected > 2):
                        QMessageBox.critical(self.dock, self.dock.windowTitle(),
                            "Nel caso di selezione GIUNTO-GIUNTO selezionare solo 2 giunti alla volta!")
                        return
                    TOT_ncont_origine = counted_selected - 1 #quindi GIUNTO di origine sempre UNO
                    #Poi per non far uscir fuori la procedura nei punti successivi, in cui infatti controllo vi debba essere UN SOLO PUNTO destinazione selezionato, deseleziono questi GIUNTI ma come???
                else:
                    TOT_ncont_origine = counted_selected'''
                TOT_ncont_origine = counted_selected
                '''#Conto quanti GIUNTI o SCALE ho selezionato:
                if ( (layername==self.LAYER_NAME['GIUNTO']) or (layername==self.LAYER_NAME['SCALA']) ):
                    TOT_ncont_origine = counted_selected
                #Conto nel caso di PD quanti punti ho selezionato:
                if (layername==self.LAYER_NAME['PD']):
                    TOT_n_pd_origine = counted_selected
                #Conto nel caso di PFS quanti punti ho selezionato:
                if (layername==self.LAYER_NAME['PFS']):
                    TOT_n_pfs_origine = counted_selected'''
                
                check_origine = 1
                #QMessageBox.information(self.dock, self.dock.windowTitle(), 'Hai selezionato ' + str(counted_selected) + ' elementi dal layer "' + layername + '".\nIn totale corrispondono ' + str(TOT_UI_origine) + ' UI')
        
                #A questo punto passo a verificare i punti destinazione:
                self.associa_punti_destinazione(chiave_origine, chiave_dest)
                
        #self.attivo_associazione()

            
    def associa_punti_destinazione(self, chiave_origine, chiave_dest):
        #Con la nuova logica arrivo a questo punto SOLO se i PUNTI ORIGINE sono CORRETTI
        Utils.logMessage("--- CHECK DESTINAZIONE ---")
        global check_dest #variabile booleana che mi dice se e' tutto ok lato destinazione
        check_dest = 0
        global selected_features_dest
        global selected_features_ids_dest
        global TOT_UI_dest
        global TOT_giunti_dest
        global TOT_pd_dest
        global TOT_pfs_dest
        global TOT_ncont_dest
        #nomelayer_scelto = self.dlg.comboBoxToPoint.currentText()
        layer = self.casistica_layer(self.LAYER_NAME[chiave_dest])[0] #questo e' il layer scelto, che attivo e da cui prendo le selezioni
        #chiave_dest = self.casistica_layer(nomelayer_scelto)[1] #chiave del layer scelto
        layername = layer.name()
        counted_selected = layer.selectedFeatureCount()
        if (counted_selected < 1):
            check_dest = 0
            QMessageBox.warning(self.dock, self.dock.windowTitle(),
                'ATTENZIONE! Non si e\' selezionato alcun elemento dal layer di destinazione scelto! - \'' + layername + '\'')
        elif (counted_selected > 1):
            check_dest = 0
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'ATTENZIONE! Non e\' possibile selezionare piu di un punto destinazione!')
        else:
            selected_features_dest = layer.selectedFeatures()
            selected_features_ids_dest = layer.selectedFeaturesIds() #DEVE CONTENERE UN SOLO ID!!
            #iface.mainWindow().statusBar().showMessage("Estraggo gli elementi selezionati") #fa vedere qualcosa nella barra in basso a sx
            TOT_UI_dest = 0
            TOT_giunti_dest = 0
            TOT_pd_dest = 0
            TOT_pfs_dest = 0
            TOT_ncont_dest = 0
            devia_su_gia_associati = 0
            msg = QMessageBox()
            for i in selected_features_dest: #in realta' il punto dest DEVE ESSERE solo UNO
                #attrs = i.attributes() #version 2, return a list
                Utils.logMessage("ID del punto destinazione = " + i[self.ID_NAME[chiave_dest]])
                #VERIFICO che se scelgo di connettere al PTA, abbia selezionato veramente un PTA:
                if (chiave_dest=='PTA'):
                    if ( str(i['tipo_giunt']).lower()!='pta' ):
                        QMessageBox.critical(self.dock, self.dock.windowTitle(),
                            "Hai selezionato un elemento che non e' PTA o che non e' stato definito nel campo tipo_giunt. Risolvere l'errore per poter continuare")
                        return
                #controllo che la destinazione sia un giunto muffola solo nel caso in cui abbia scelto una connex scala-muffola:
                if (chiave_dest=='GIUNTO' and chiave_origine=='SCALA'):
                    if ( str(i['tipo_giunt']).lower()!='muffola' ):
                        QMessageBox.critical(self.dock, self.dock.windowTitle(),
                            "Hai selezionato un elemento che non e' MUFFOLA o che non e' stato definito nel campo tipo_giunt. Risolvere l'errore per poter continuare")
                        return
                #controllo che la destinazione NON sia un giunto PTA nel caso stia connettendo 2 giunti e quello di origine sia Muffola - difficile da controllare per cui faccio una domanda all'utente:
                if (chiave_dest=='GIUNTO' and chiave_origine=='GIUNTO_F_dev'):
                    if ( str(i['tipo_giunt']).lower()!='muffola' ):
                        msg.setText("Scusami, non riesco a reperire informazioni sui giunti di origine, ma stai associando dei giunti ad un elemento finale che non e' MUFFOLA o che non e' stato definito nel campo tipo_giunt: desideri continuare?")
                        msg.setIcon(QMessageBox.Warning)
                        msg.setWindowTitle("Attenzione possibile errore: continuare?")
                        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        retval = msg.exec_()
                        #if (retval != 1024): #l'utente NON ha cliccato ok: sceglie di fermarsi, esco
                        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                            return 0
                #PRIMA VERIFICA: il punto destinazione NON deve essere CONNESSO a qualche PADRE:
                #Da MAIL GATTI del 31 luglio 2017: chiedo all'utente cosa vuole fare nel caso la destinazione sia gia' connessa. Per semplificarmi la vita pero' lo rimando ad un'altra funzione se sceglie di continuare
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Attenzione possibile errore: continuare?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                if (layername!=self.LAYER_NAME['PFP']):
                    if (i['id_pfp']):
                        #QMessageBox.critical(self.dock, self.dock.windowTitle(),
                        #    "Hai selezionato un elemento gia' connesso a un PFP! Non e' possibile continuare.")
                        #return
                        msg.setText("Hai selezionato un elemento gia' connesso a un PFP! Desideri continuare?")
                        retval = msg.exec_()
                        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                            return 0
                        else:
                            #funzione che permette di associare con un elemento gia' associato:
                            Utils.logMessage("Utente continua a collegare anche se il punto dest e' gia' collegato")
                            self.associa_gia_associati(chiave_origine, chiave_dest, layername, layer, counted_selected, i)
                            return
                #Se arrivo al GIUNTO questo non deve avere PD ne' essere un giunto figlio:
                if (layername==self.LAYER_NAME['GIUNTO']):
                    if ( i['id_pd'] ):
                        #QMessageBox.critical(self.dock, self.dock.windowTitle(), "Hai selezionato un elemento gia' connesso a un PD! Non e' possibile continuare.")
                        #return
                        msg.setText("Hai selezionato un elemento gia' connesso a un PD! Desideri continuare?")
                        retval = msg.exec_()
                        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                            return 0
                        else:
                            #funzione che permette di associare con un elemento gia' associato:
                            Utils.logMessage("Utente continua a collegare anche se il punto dest e' gia' collegato")
                            self.associa_gia_associati(chiave_origine, chiave_dest, layername, layer, counted_selected, i)
                            return
                    if ( i['id_g_ref'] ):
                        #QMessageBox.critical(self.dock, self.dock.windowTitle(), "Hai selezionato un elemento gia' connesso ad un altro GIUNTO (PTA o Muffola)! Non e' possibile continuare.")
                        #return
                        msg.setText("Hai selezionato un elemento gia' connesso ad un altro GIUNTO (PTA o Muffola)! Desideri continuare?")
                        retval = msg.exec_()
                        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                            return 0
                        else:
                            #funzione che permette di associare con un elemento gia' associato:
                            Utils.logMessage("Utente continua a collegare anche se il punto dest e' gia' collegato")
                            self.associa_gia_associati(chiave_origine, chiave_dest, layername, layer, counted_selected, i)
                            return
                    #NUOVA VERSIONE CASCATA: elementi connessi ad libitum
                    '''
                    elif ( i['id_g_ref'] ):
                        QMessageBox.information(self.dock, self.dock.windowTitle(),
                        "Hai selezionato un elemento gia' connesso a un giunto! Non e' possibile continuare.")
                        return
                    '''
                #Se arrivo alla SCALA questa non deve avere GIUNTO o PD o PFS:
                if (layername==self.LAYER_NAME['SCALA']):
                    if ( i['id_giunto'] or i['id_pd'] or i['id_pfs'] ):
                        #QMessageBox.critical(self.dock, self.dock.windowTitle(), "Hai selezionato un elemento gia' connesso a un GIUNTO o PD o PFS! Non e' possibile continuare.")
                        #return
                        msg.setText("Hai selezionato un elemento gia' connesso a un GIUNTO o PD o PFS! Desideri continuare?")
                        retval = msg.exec_()
                        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                            return 0
                        else:
                            #funzione che permette di associare con un elemento gia' associato:
                            Utils.logMessage("Utente continua a collegare anche se il punto dest e' gia' collegato")
                            self.associa_gia_associati(chiave_origine, chiave_dest, layername, layer, counted_selected, i)
                            return
                    if ( i['id_sc_ref'] ):
                        #QMessageBox.critical(self.dock, self.dock.windowTitle(), "Hai selezionato un elemento gia' connesso ad un'altra SCALA! Non e' possibile continuare.")
                        #return
                        msg.setText("Hai selezionato un elemento gia' connesso ad un'altra SCALA! Desideri continuare?")
                        retval = msg.exec_()
                        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                            return 0
                        else:
                            #funzione che permette di associare con un elemento gia' associato:
                            Utils.logMessage("Utente continua a collegare anche se il punto dest e' gia' collegato")
                            self.associa_gia_associati(chiave_origine, chiave_dest, layername, layer, counted_selected, i)
                            return
                #Se arrivo al PD questo non deve avere PFS:
                if (layername==self.LAYER_NAME['PD']):
                    if ( i['id_pfs'] ):
                        #QMessageBox.critical(self.dock, self.dock.windowTitle(), "Hai selezionato un elemento gia' connesso a un PFS! Non e' possibile continuare.")
                        #return
                        msg.setText("Hai selezionato un elemento gia' connesso a un PFS! Desideri continuare?")
                        retval = msg.exec_()
                        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                            return 0
                        else:
                            #funzione che permette di associare con un elemento gia' associato:
                            Utils.logMessage("Utente continua a collegare anche se il punto dest e' gia' collegato")
                            self.associa_gia_associati(chiave_origine, chiave_dest, layername, layer, counted_selected, i)
                            return
                    if ( i['id_pd_ref'] ):
                        #QMessageBox.critical(self.dock, self.dock.windowTitle(), "Hai selezionato un elemento gia' connesso ad un altro PD! Non e' possibile continuare.")
                        #return
                        msg.setText("Hai selezionato un elemento gia' connesso ad un altro PD! Desideri continuare?")
                        retval = msg.exec_()
                        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                            return 0
                        else:
                            #funzione che permette di associare con un elemento gia' associato:
                            Utils.logMessage("Utente continua a collegare anche se il punto dest e' gia' collegato")
                            self.associa_gia_associati(chiave_origine, chiave_dest, layername, layer, counted_selected, i)
                            return
                if (i['n_ui']):
                    TOT_UI_dest = TOT_UI_dest + i['n_ui']
                #Controllo adesso nel caso di GIUNTO se e' associato a quanti contatori:
                if (layername==self.LAYER_NAME['GIUNTO']):
                    if (i['n_cont']):
                        TOT_ncont_dest = TOT_ncont_dest + i['n_cont']
                #Controllo adesso nel caso di PD se e' associato a qualche giunto e i contatori:
                if (layername==self.LAYER_NAME['PD']):
                    if (i['n_giunti']):
                        TOT_giunti_dest = TOT_giunti_dest + i['n_giunti']
                    if (i['n_cont']):
                        TOT_ncont_dest = TOT_ncont_dest + i['n_cont']
                #Controllo adesso nel caso di PFS a quanti PD e' gia' associato:
                if (layername==self.LAYER_NAME['PFS']):
                    if (i['n_pd']):
                        TOT_ncont_dest = TOT_ncont_dest + i['n_pd']
                    '''#Se si dovesse rendere necessario calcolare n_cont anche per i PFS:
                    if (i['n_pd']):
                        TOT_pd_dest = TOT_pd_dest + i['n_pd']
                    if (i['n_cont']):
                        TOT_ncont_dest = TOT_ncont_dest + i['n_cont']'''
                #Controllo adesso nel caso di PFP a quanti PFS e' gia' associato:
                if (layername==self.LAYER_NAME['PFP']):
                    if (i['n_pfs']):
                        TOT_ncont_dest = TOT_ncont_dest + i['n_pfs']
            
            Utils.logMessage("TOT UI gia' presenti in dest = " + str(TOT_UI_dest))
               
            '''#INFO origine e destinazione insieme:
            QMessageBox.information(self.dock, self.dock.windowTitle(), 
                    'ORIGINE: Selezionati ' + str(TOT_ncont_origine) + ' elementi dal layer "' + chiave_origine + '" con ' + str(TOT_UI_origine) + ' UI' +
                    '\nDESTINAZIONE: Selezionati ' + str(counted_selected) + ' elementi dal layer "' + chiave_dest + '" con associate: ' + str(TOT_UI_dest) + ' UI')'''
            #INFO destinazione:
            #QMessageBox.information(self.dock, self.dock.windowTitle(), '\nSelezionati ' + str(counted_selected) + ' elementi dal layer "' + chiave_dest + '". Questo punto ha gia\' associate: ' + str(TOT_UI_dest) + ' UI')
                
            #QUI DEVO VERIFICARE CHE I VINCOLI SIANO RISPETTATI
            #Ricarico le variabili dal progetto su DB:
            min_ui_dest = FROM_TO_RULES[chiave_dest]['MIN_UI']
            max_ui_dest = FROM_TO_RULES[chiave_dest]['MAX_UI']
            max_cont = FROM_TO_RULES[chiave_dest]['MAX_CONT']
            Utils.logMessage("Verifica layer dest: min_ui=" + str(min_ui_dest) + " - max_ui = " + str(max_ui_dest) + " - max_cont = " + str(max_cont))
            TOT_UI = TOT_UI_dest + TOT_UI_origine
            #La variaible CONTATORI acquisisce diversi significati. Se si tratta di SCALE, GIUNTO o PD come layer destinazione, rappresenta effettivamente il N_CONT. Nel caso di PFS come destinazione, rappresenta il numero di PD o SCALE di origine. Nel caso di PFP, rappresenta il numero di PFS di origine
            TOT_CONT = TOT_ncont_dest + TOT_ncont_origine
            #CONTROLLI:
            variabile_controllo = 1 #ipotizzo sia tutto ok
            #INFO origine e destinazione insieme:
            messaggio_controllo = 'ORIGINE: Selezionati ' + str(TOT_ncont_origine) + ' elementi dal layer "' + chiave_origine + '" con ' + str(TOT_UI_origine) + ' UI' + '\nDESTINAZIONE: Selezionati ' + str(counted_selected) + ' elementi dal layer "' + chiave_dest + '" con associate: ' + str(TOT_UI_dest) + ' UI'
            messaggio_warning = '' #inizialmente stringa vuota
            #PRIMO CONTROLLO: UI
            '''
            #Salto questo primo controllo sulle UI minime perche' nel caso di associazione sui PD questo puo' creare un po' di problemi. Magari lo trasformo in un "warning" piu' sotto:
            if (TOT_UI < min_ui_dest):
                QMessageBox.critical(self.dock, self.dock.windowTitle(), 
                    'ATTENZIONE! Pochi fabbricati associati. Il numero minimo di UI da associare a "' + layername + '" e\' ' + str(min_ui_dest) + ': ne sono stati associati solo ' + str(TOT_UI))
            #elif (TOT_UI > max_ui_dest):'''
            '''if (TOT_UI > max_ui_dest):
                QMessageBox.critical(self.dock, self.dock.windowTitle(), 'ATTENZIONE! Troppi fabbricati selezionati da "' + layername + '"! Sono stati selezionati ' + str(TOT_UI) + ' invece di ' + str(max_ui_dest) + 'UI')
            else: #ELSE finale: se tutto va bene concludo l'associazione'''
            #Il controllo che prima era bloccante sulle UI_max ora lo rendo con un warning:
            if (TOT_UI > max_ui_dest):
                QMessageBox.critical(self.dock, self.dock.windowTitle(), 'ATTENZIONE! Troppi fabbricati selezionati da "' + layername + '"! Sono stati selezionati ' + str(TOT_UI) + ' invece di ' + str(max_ui_dest) + 'UI.\nAssociazione NON eseguita.')
                #Questo vincolo torna ad essere VINCOLANTE quindi esco.
                return 0
                #variabile_controllo = 0
                #messaggio_warning = messaggio_warning + 'ATTENZIONE! Troppi fabbricati selezionati da "' + layername + '"! Sono stati selezionati ' + str(TOT_UI) + ' invece di ' + str(max_ui_dest) + 'UI\nSi desidera proseguire comunque con la associazione?\n'
            #Il controllo che prima era bloccante sulle UI_minime ora lo rendo con un warning:
            if (TOT_UI < min_ui_dest):
                #QMessageBox.warning(self.dock, self.dock.windowTitle(), 'ATTENZIONE! Pochi fabbricati associati. Il numero minimo di UI da associare a "' + layername + '" e\' ' + str(min_ui_dest) + ': ne sono stati associati solo ' + str(TOT_UI) + '.\nSi proseguira comunque nella associazione')
                variabile_controllo = 0
                messaggio_warning = messaggio_warning + 'ATTENZIONE! Pochi fabbricati associati. Il numero minimo di UI da associare a "' + layername + '" e\' ' + str(min_ui_dest) + ': ne sono stati associati solo ' + str(TOT_UI) + '.\nSi desidera proseguire comunque con la associazione?\n'
            #SECONDO CONTROLLO: CONTATORI/PD/PFS. Il controllo che prima era bloccante sui CONT_MAX ora lo rendo con una scelta da parte dell'utente:
            if (TOT_CONT > max_cont):
                variabile_controllo = 0
                #In ogni caso aggiungo questa frase come da scambio email con Gatti 10 novembre 2016:
                messaggio_warning = messaggio_warning + 'LIMITI DI PROGETTO: n. max 5 cavi in rete aerea n. max 8 cavi in rete interrata.\n'
                messaggio_warning = messaggio_warning + 'ATTENZIONE! Troppi elementi selezionati dal layer ORIGINE per il punto "' + layername + '"! Saranno previsti ' + str(TOT_CONT) + ' cavi in ingresso (invece di ' + str(max_cont) + '). Si desidera continuare?'
            #IN OGNI CASO genero una finestra con delle informazioni:
            msg = QMessageBox()
            msg.setText(messaggio_controllo)
            msg.setInformativeText(messaggio_warning)
            if (variabile_controllo==0):
                msg.setIcon(QMessageBox.Warning)
                #msg.setDetailedText("The details are as follows:")
                #msg.buttonClicked.connect(msgbtn)
                msg.setWindowTitle("Vincoli di progetto non rispettati: continuare?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                retval = msg.exec_()
                #if (retval != 1024): #l'utente NON ha cliccato ok: sceglie di fermarsi, esco
                if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                    return 0
            else:
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle(self.dock.windowTitle())
                msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec_()
            
            check_dest = 1
            #A questo punto HO TUTTI I VINCOLI RISPETTATI E POSSO PROCEDERE CON L'ASSOCIAZIONE:
            try:
                self.import_action(chiave_origine, chiave_dest, devia_su_gia_associati)
            except NameError as err:
                Utils.logMessage(err.args[0])
            except SystemError, e:
                self.casistica_layer(self.LAYER_NAME[chiave_origine])[0].rollBack()
                self.casistica_layer(self.LAYER_NAME[chiave_dest])[0].rollBack()
                Utils.logMessage(e)
                QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Associazione NON avvenuta dopo import_action')
                self.dlg.txtFeedback.setText('Errore di sistema! Associazione NON avvenuta')
            else:
                #layer_dest.commitChanges()
                #layer_origine.commitChanges()
                self.dlg.txtFeedback.setText('Associazione avvenuta con successo!')
                #QMessageBox.information(self.dock, self.dock.windowTitle(), 'Associazione avvenuta con successo!')
                
        #self.attivo_associazione()

        
    def associa_gia_associati(self, chiave_origine, chiave_dest, dest_layername, dest_layer, counted_selected, i):
        global TOT_UI_dest
        global TOT_giunti_dest
        global TOT_ncont_dest
        TOT_UI_dest = 0
        TOT_giunti_dest = 0
        TOT_ncont_dest = 0
        msg = QMessageBox()
        if (i['n_ui']):
            TOT_UI_dest = TOT_UI_dest + i['n_ui']
        #Controllo adesso nel caso di GIUNTO se e' associato a quanti contatori:
        if (dest_layername==self.LAYER_NAME['GIUNTO']):
            if (i['n_cont']):
                TOT_ncont_dest = TOT_ncont_dest + i['n_cont']
        #Controllo adesso nel caso di PD se e' associato a qualche giunto e i contatori:
        if (dest_layername==self.LAYER_NAME['PD']):
            if (i['n_giunti']):
                TOT_giunti_dest = TOT_giunti_dest + i['n_giunti']
            if (i['n_cont']):
                TOT_ncont_dest = TOT_ncont_dest + i['n_cont']
        #Controllo adesso nel caso di PFS a quanti PD e' gia' associato:
        if (dest_layername==self.LAYER_NAME['PFS']):
            if (i['n_pd']):
                TOT_ncont_dest = TOT_ncont_dest + i['n_pd']
            '''#Se si dovesse rendere necessario calcolare n_cont anche per i PFS:
            if (i['n_pd']):
                TOT_pd_dest = TOT_pd_dest + i['n_pd']
            if (i['n_cont']):
                TOT_ncont_dest = TOT_ncont_dest + i['n_cont']'''
        #Controllo adesso nel caso di PFP a quanti PFS e' gia' associato:
        if (dest_layername==self.LAYER_NAME['PFP']):
            if (i['n_pfs']):
                TOT_ncont_dest = TOT_ncont_dest + i['n_pfs']
        
        Utils.logMessage("TOT UI gia' presenti in dest = " + str(TOT_UI_dest))
    
        #Ricarico le variabili dal progetto su DB:
        min_ui_dest = FROM_TO_RULES[chiave_dest]['MIN_UI']
        max_ui_dest = FROM_TO_RULES[chiave_dest]['MAX_UI']
        max_cont = FROM_TO_RULES[chiave_dest]['MAX_CONT']
        Utils.logMessage("Verifica layer dest: min_ui=" + str(min_ui_dest) + " - max_ui = " + str(max_ui_dest) + " - max_cont = " + str(max_cont))
        TOT_UI = TOT_UI_dest + TOT_UI_origine
        #La variaible CONTATORI acquisisce diversi significati. Se si tratta di SCALE, GIUNTO o PD come layer destinazione, rappresenta effettivamente il N_CONT. Nel caso di PFS come destinazione, rappresenta il numero di PD o SCALE di origine. Nel caso di PFP, rappresenta il numero di PFS di origine
        TOT_CONT = TOT_ncont_dest + TOT_ncont_origine
        #CONTROLLI:
        variabile_controllo = 1 #ipotizzo sia tutto ok
        #INFO origine e destinazione insieme:
        messaggio_controllo = 'ORIGINE: Selezionati ' + str(TOT_ncont_origine) + ' elementi dal layer "' + chiave_origine + '" con ' + str(TOT_UI_origine) + ' UI' + '\nDESTINAZIONE: Selezionati ' + str(counted_selected) + ' elementi dal layer "' + chiave_dest + '" con associate: ' + str(TOT_UI_dest) + ' UI'
        messaggio_warning = '' #inizialmente stringa vuota
        #PRIMO CONTROLLO: UI
        #Il controllo che prima era bloccante sulle UI_max ora lo rendo con un warning:
        if (TOT_UI > max_ui_dest):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'ATTENZIONE! Troppi fabbricati selezionati da "' + dest_layername + '"! Sono stati selezionati ' + str(TOT_UI) + ' invece di ' + str(max_ui_dest) + 'UI.\nAssociazione NON eseguita.')
            #Questo vincolo torna ad essere VINCOLANTE quindi esco.
            return 0
        #Il controllo che prima era bloccante sulle UI_minime ora lo rendo con un warning:
        if (TOT_UI < min_ui_dest):
            #QMessageBox.warning(self.dock, self.dock.windowTitle(), 'ATTENZIONE! Pochi fabbricati associati. Il numero minimo di UI da associare a "' + dest_layername + '" e\' ' + str(min_ui_dest) + ': ne sono stati associati solo ' + str(TOT_UI) + '.\nSi proseguira comunque nella associazione')
            variabile_controllo = 0
            messaggio_warning = messaggio_warning + 'ATTENZIONE! Pochi fabbricati associati. Il numero minimo di UI da associare a "' + dest_layername + '" e\' ' + str(min_ui_dest) + ': ne sono stati associati solo ' + str(TOT_UI) + '.\nSi desidera proseguire comunque con la associazione?\n'
        #SECONDO CONTROLLO: CONTATORI/PD/PFS. Il controllo che prima era bloccante sui CONT_MAX ora lo rendo con una scelta da parte dell'utente:
        if (TOT_CONT > max_cont):
            variabile_controllo = 0
            #In ogni caso aggiungo questa frase come da scambio email con Gatti 10 novembre 2016:
            messaggio_warning = messaggio_warning + 'LIMITI DI PROGETTO: n. max 5 cavi in rete aerea n. max 8 cavi in rete interrata.\n'
            messaggio_warning = messaggio_warning + 'ATTENZIONE! Troppi elementi selezionati dal layer ORIGINE per il punto "' + dest_layername + '"! Saranno previsti ' + str(TOT_CONT) + ' cavi in ingresso (invece di ' + str(max_cont) + '). Si desidera continuare?'
        #IN OGNI CASO genero una finestra con delle informazioni:
        msg.setText(messaggio_controllo)
        msg.setInformativeText(messaggio_warning)
        if (variabile_controllo==0):
            msg.setIcon(QMessageBox.Warning)
            #msg.setDetailedText("The details are as follows:")
            #msg.buttonClicked.connect(msgbtn)
            msg.setWindowTitle("Vincoli di progetto non rispettati: continuare?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            retval = msg.exec_()
            #if (retval != 1024): #l'utente NON ha cliccato ok: sceglie di fermarsi, esco
            if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                return 0
        else:
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle(self.dock.windowTitle())
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            
        #CONTROLLI A CASCATA DELLE UI DAL BASSO VERSO L'ALTO PERO' -- BOTTOM-UP:
        TOT_UI_dest_up = 0
        #proviamo a fare un controllo scalare:
        TOT_UI_dest_up = self.verifica_bottom_up('PFP', PFP_layer, dest_layer, TOT_UI_origine)
        if (TOT_UI_dest_up > FROM_TO_RULES['PFP']['MAX_UI']):
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Troppe UI per il PFP finale!')
            return 0
        if (dest_layername in [self.LAYER_NAME['SCALA'], self.LAYER_NAME['GIUNTO'], self.LAYER_NAME['PD'] ] ):
            Utils.logMessage("Verifica layer dest bottom_up: PFS")
            TOT_UI_dest_up = self.verifica_bottom_up('PFS', PFS_layer, dest_layer, TOT_UI_origine)
            if (TOT_UI_dest_up > FROM_TO_RULES['PFS']['MAX_UI']):
                QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Troppe UI per il PFS finale!')
                return 0
        if (dest_layername in [ self.LAYER_NAME['SCALA'], self.LAYER_NAME['GIUNTO'] ] ):
            Utils.logMessage("Verifica layer dest bottom_up: PD")
            TOT_UI_dest_up = self.verifica_bottom_up('PD', PD_layer, dest_layer, TOT_UI_origine)
            Utils.logMessage("TOT_UI_dest_up="+str(TOT_UI_dest_up))
            if (TOT_UI_dest_up > FROM_TO_RULES['PD']['MAX_UI']):
                QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Troppe UI per il PD finale!')
                return 0
        if (dest_layername==self.LAYER_NAME['SCALA']):
            Utils.logMessage("Verifica layer dest bottom_up: GIUNTO")
            TOT_UI_dest_up = self.verifica_bottom_up('GIUNTO', GIUNTO_layer, dest_layer, TOT_UI_origine)
            Utils.logMessage("TOT_UI_dest_up="+str(TOT_UI_dest_up))
            if (TOT_UI_dest_up > FROM_TO_RULES['GIUNTO']['MAX_UI']):
                QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Troppe UI per il GIUNTO finale!')
                return 0
                #DA FARE!!!
        #SE I VINCOLI SONO RISPETTATI ALLORA:
        Utils.logMessage("Tutti vincoli sulle UI bottom_up rispettati!")
        check_dest = 1
        
        devia_su_gia_associati = 1
        
        #A questo punto HO TUTTI I VINCOLI RISPETTATI E POSSO PROCEDERE CON L'ASSOCIAZIONE:
        try:
            self.import_action(chiave_origine, chiave_dest, devia_su_gia_associati)
        except NameError as err:
            Utils.logMessage(err.args[0])
        except SystemError, e:
            self.casistica_layer(self.LAYER_NAME[chiave_origine])[0].rollBack()
            self.casistica_layer(self.LAYER_NAME[chiave_dest])[0].rollBack()
            Utils.logMessage(e)
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Associazione NON avvenuta dopo import_action')
            self.dlg.txtFeedback.setText('Errore di sistema! Associazione NON avvenuta')
        else:
            #layer_dest.commitChanges()
            #layer_origine.commitChanges()
            self.dlg.txtFeedback.setText('Associazione avvenuta con successo!')
            #QMessageBox.information(self.dock, self.dock.windowTitle(), 'Associazione avvenuta con successo!')
            
        
    def import_action(self, chiave_origine, chiave_dest, devia_su_gia_associati):
        Utils.logMessage("--- ESEGUO ASSOCIAZIONE ---")
        #A partire da qui eseguo la ASSOCIAZIONE vera e propria
        self.dlg.txtFeedback.setText('Attendi.....')
        #self.dlg.txtFeedback.setText(', '.join(str(x) for x in selected_features_ids_origine))
        #1343, 1348, 1349, 1350
        #self.dlg.txtFeedback.setText(str(TOT_UI_origine)) #ok
        #self.dlg.txtFeedback.setText(str(selected_features_ids_dest[0])) #[236L], e' una lista, pero come vincolo DEVE contenere UN SOLO oggetto
        
        #Recupero i layers:
        layer_origine = self.casistica_layer(self.LAYER_NAME[chiave_origine])[0]
        layer_dest = self.casistica_layer(self.LAYER_NAME[chiave_dest])[0]
        gid_feature_dest = int(selected_features_ids_dest[0])
        #Avvio le modifiche ai layers:
        layer_dest.startEditing()
        #Associo al layer_dest le UI:
        idx_dest_ui=layer_dest.fieldNameIndex('n_ui')
        Utils.logMessage("Id di dest da aggiornare = " + str(gid_feature_dest))
        layer_dest.changeAttributeValue(gid_feature_dest, idx_dest_ui, TOT_UI_origine+TOT_UI_dest)
        #Associo il numero contatori se si tratta di connessione SCALA-GIUNTO:
        if (layer_dest.name()==self.LAYER_NAME['GIUNTO'] and layer_origine.name()==self.LAYER_NAME['SCALA']):
            idx_dest=layer_dest.fieldNameIndex('n_cont')
            Utils.logMessage("Numero dei contatori = " + str(len(selected_features_ids_origine)))
            layer_dest.changeAttributeValue(gid_feature_dest, idx_dest, len(selected_features_ids_origine)+TOT_ncont_dest)
        #Associo il numero contatori se si tratta di connessione SCALA-PD:
        if (layer_dest.name()==self.LAYER_NAME['PD'] and layer_origine.name()==self.LAYER_NAME['SCALA']):
            idx_dest=layer_dest.fieldNameIndex('n_cont')
            Utils.logMessage("Numero dei contatori = " + str(len(selected_features_ids_origine)))
            layer_dest.changeAttributeValue(gid_feature_dest, idx_dest, len(selected_features_ids_origine)+TOT_ncont_dest)
        #Associo il numero contatori se si tratta di connessione GIUNTO-GIUNTO:
        if (layer_dest.name()==self.LAYER_NAME['GIUNTO'] and layer_origine.name()==self.LAYER_NAME['GIUNTO_F_dev']):
            idx_dest=layer_dest.fieldNameIndex('n_cont')
            Utils.logMessage("Numero dei contatori = " + str(len(selected_features_ids_origine)))
            layer_dest.changeAttributeValue(gid_feature_dest, idx_dest, len(selected_features_ids_origine)+TOT_ncont_dest)
        #Associo il numero dei Giunti e contatori se si tratta di connessione GIUNTO-PD:
        if (layer_dest.name()==self.LAYER_NAME['PD'] and layer_origine.name()==self.LAYER_NAME['GIUNTO']):
            idx_dest=layer_dest.fieldNameIndex('n_giunti')
            Utils.logMessage("Numero dei giunti = " + str(len(selected_features_ids_origine)))
            layer_dest.changeAttributeValue(gid_feature_dest, idx_dest, len(selected_features_ids_origine)+TOT_giunti_dest)
            idx_dest=layer_dest.fieldNameIndex('n_cont')
            Utils.logMessage("Numero dei contatori dall'origine = " + str(TOT_ncont_origine))
            #UN giunto vale UN contatore. Dunque:
            layer_dest.changeAttributeValue(gid_feature_dest, idx_dest, len(selected_features_ids_origine)+TOT_ncont_dest)
        #Associo il numero contatori se si tratta di connessione PD-PD:
        if (layer_dest.name()==self.LAYER_NAME['PD'] and layer_origine.name()==self.LAYER_NAME['PD_F']):
            idx_dest=layer_dest.fieldNameIndex('n_cont')
            Utils.logMessage("Numero dei contatori = " + str(len(selected_features_ids_origine)))
            layer_dest.changeAttributeValue(gid_feature_dest, idx_dest, len(selected_features_ids_origine)+TOT_ncont_dest)
        #Associo il numero dei PD se si tratta di connessione PD-PFS:
        if (layer_dest.name()==self.LAYER_NAME['PFS'] and layer_origine.name()==self.LAYER_NAME['PD']):
            idx_dest=layer_dest.fieldNameIndex('n_pd')
            Utils.logMessage("Numero dei PD = " + str(len(selected_features_ids_origine)))
            layer_dest.changeAttributeValue(gid_feature_dest, idx_dest, len(selected_features_ids_origine)+TOT_ncont_dest)
        #nello stesso campo n_pd conto SCALE e GIUNTI connessi direttamente al PFS:
        if (layer_dest.name()==self.LAYER_NAME['PFS'] and layer_origine.name()==self.LAYER_NAME['GIUNTO']):
            idx_dest=layer_dest.fieldNameIndex('n_pd')
            Utils.logMessage("Numero dei GIUNTI = " + str(len(selected_features_ids_origine)))
            layer_dest.changeAttributeValue(gid_feature_dest, idx_dest, len(selected_features_ids_origine)+TOT_ncont_dest)
        if (layer_dest.name()==self.LAYER_NAME['PFS'] and layer_origine.name()==self.LAYER_NAME['SCALA']):
            idx_dest=layer_dest.fieldNameIndex('n_pd')
            Utils.logMessage("Numero di SCALE = " + str(len(selected_features_ids_origine)))
            layer_dest.changeAttributeValue(gid_feature_dest, idx_dest, len(selected_features_ids_origine)+TOT_ncont_dest)
        #Associo il numero dei PFS se si tratta di connessione PFS-PFP:
        if (layer_dest.name()==self.LAYER_NAME['PFP'] and layer_origine.name()==self.LAYER_NAME['PFS']):
            idx_dest=layer_dest.fieldNameIndex('n_pfs')
            Utils.logMessage("Numero dei PFS = " + str(len(selected_features_ids_origine)))
            layer_dest.changeAttributeValue(gid_feature_dest, idx_dest, len(selected_features_ids_origine)+TOT_ncont_dest)
        #Committo:
        layer_dest.commitChanges()
        
        #Associo agli elementi del layer_origine l'ID dell'elemento selezionato dal layer_dest:
        layer_origine.startEditing()
        #recupero la posizione del campo ID_destinazione nella tabella di origine, ad esempio ID_GIUNTO per le connex GIUNTO-SCALA, con l'eccezione del GIUNTO-GIUNTO:
        if (layer_dest.name()==self.LAYER_NAME['GIUNTO'] and layer_origine.name()==self.LAYER_NAME['GIUNTO_F_dev']):
            idx_origine=layer_origine.fieldNameIndex(self.ID_NAME['GIUNTO_F_dev'])
        elif (layer_dest.name()==self.LAYER_NAME['SCALA'] and layer_origine.name()==self.LAYER_NAME['SCALA_F']):
            idx_origine=layer_origine.fieldNameIndex(self.ID_NAME['SCALA_F'])
        elif (layer_dest.name()==self.LAYER_NAME['PD'] and layer_origine.name()==self.LAYER_NAME['PD_F']):
            idx_origine=layer_origine.fieldNameIndex(self.ID_NAME['PD_F'])
        else:
            idx_origine=layer_origine.fieldNameIndex(self.ID_NAME[chiave_dest])
        #recupero l'ID e NON IL GID dell'elemento di destinazione CHE DEVE ESSERE SOLO UNO
        ID_DEST=selected_features_dest[0][self.ID_NAME[chiave_dest]]
        for ii in selected_features_ids_origine:
            Utils.logMessage("Id di origine da aggiornare = " + str(ii) + " ponendo id_dest=" + ID_DEST)
            layer_origine.changeAttributeValue(ii, idx_origine, ID_DEST)
            #MAIL di GATTI del 22 Giugno 2017: scrivere il valore "tipo" in SCALA:
            idx_tipo_origine = layer_origine.fieldNameIndex('tipo')
            if (chiave_dest=='PTA' and layer_origine.name()==self.LAYER_NAME['SCALA']):
                layer_origine.changeAttributeValue(ii, idx_tipo_origine, 'PTA')
            else:
                layer_origine.changeAttributeValue(ii, idx_tipo_origine, 'PTE')
        #Committo:
        layer_origine.commitChanges()
        
        
        #RICALCOLO le UI a cascata per eventuali PADRI - rimetto questo codice operativo dopo mail di Gatti del 31 luglio 2017:
        #DA VERIFICARE!! Soprattutto per le connessioni a cascata: cosa succede?
        if devia_su_gia_associati==1:
            Utils.logMessage("Ricalcolo le UI a cascata")
            if (layer_dest.name()==self.LAYER_NAME['SCALA']):
                self.associa_UI_bottom_up_figli('SCALA_F', SCALE_layer, layer_dest, 'SCALA')
                self.associa_UI_bottom_up('GIUNTO', GIUNTO_layer, layer_dest, 'GIUNTO_F_dev') #TEST: provo a recuperare anche eventuale GIUNTO PADRE
                #self.associa_UI_bottom_up('PD', PD_layer, layer_dest)
                self.associa_UI_bottom_up('PD', PD_layer, layer_dest, 'PD_F') #TEST: provo a recuperare anche eventuale PD PADRE
                self.associa_UI_bottom_up('PFS', PFS_layer, layer_dest)
                self.associa_UI_bottom_up('PFP', PFP_layer, layer_dest)
            if (layer_dest.name()==self.LAYER_NAME['GIUNTO']):
                self.associa_UI_bottom_up_figli('GIUNTO_F_dev', GIUNTO_layer, layer_dest, 'GIUNTO')
                self.associa_UI_bottom_up('PD', PD_layer, layer_dest, 'PD_F') #TEST: provo a recuperare anche eventuale PD PADRE
                self.associa_UI_bottom_up('PFS', PFS_layer, layer_dest)
                self.associa_UI_bottom_up('PFP', PFP_layer, layer_dest)
            if (layer_dest.name()==self.LAYER_NAME['PD']):
                self.associa_UI_bottom_up_figli('PD_F', PD_layer, layer_dest, 'PD')
                self.associa_UI_bottom_up('PFS', PFS_layer, layer_dest)
                self.associa_UI_bottom_up('PFP', PFP_layer, layer_dest)
            if (layer_dest.name()==self.LAYER_NAME['PFS']):
                self.associa_UI_bottom_up('PFP', PFP_layer, layer_dest)
        
        #Piu' in GENERALE dovrei scrivere delle funzioni che a CASCATA associano gli ID delle connessioni PADRI ai vari FIGLI: FUNZIONI TUTTE DA VERIFICARE!!!
        '''In realta questo passaggio e' richiesto solo al PRIMO LIVELLO up-bottom, dunque si potrebbe ridurre di molto il codice. Al momento lascio tutto attivo poiche' in ogni caso le relazioni super-up dovrebbero essere null e dunque non creare problemi'''
        '''RISCRIVO: in realta' con le nuove disposizioni devo permettere le connessioni anche a quei punti gia' connessi'''
        Utils.logMessage("Assegno gli ID dai padri ai figli in cascata")
        #SCALA-GIUNTO:
        if (layer_dest.name()==self.LAYER_NAME['GIUNTO'] and layer_origine.name()==self.LAYER_NAME['SCALA']):
            self.associa_padri('PD', chiave_origine, SCALE_layer)
            #Usando la stessa funzione, riesco ad associare anche ID_PFS del PD del GIUNTO alle SCALE?
            self.associa_padri('PFS', chiave_origine, SCALE_layer)
            self.associa_padri('PFP', chiave_origine, SCALE_layer)
            #nel caso in cui questa SCALA abbia delle scale associate in cascata, devo associare anche a loro l'id del giunto:
            self.associa_cascata_scala('GIUNTO', 'SCALA_F', SCALE_layer)
        #SCALA-PD:
        if (layer_dest.name()==self.LAYER_NAME['PD'] and layer_origine.name()==self.LAYER_NAME['SCALA']):
            self.associa_padri('PFS', chiave_origine, SCALE_layer)
            self.associa_padri('PFP', chiave_origine, SCALE_layer)
            #nel caso in cui questa SCALA abbia delle scale associate in cascata, devo associare anche a loro l'id del PD:
            self.associa_cascata_scala('PD', 'SCALA_F', SCALE_layer)
        #SCALA-PFS:
        if (layer_dest.name()==self.LAYER_NAME['PFS'] and layer_origine.name()==self.LAYER_NAME['SCALA']):
            self.associa_padri('PFP', chiave_origine, SCALE_layer)
            #nel caso in cui questa SCALA abbia delle scale associate in cascata, devo associare anche a loro l'id del PFS:
            self.associa_cascata_scala('PFS', 'SCALA_F', SCALE_layer)
        #GIUNTO-PD:
        if (layer_dest.name()==self.LAYER_NAME['PD'] and layer_origine.name()==self.LAYER_NAME['GIUNTO']):
            #Prima associo i vari ID del PD al GIUNTO:
            self.associa_padri('PFS', chiave_origine, GIUNTO_layer)
            self.associa_padri('PFP', chiave_origine, GIUNTO_layer)
            #Poi passo ad associare a cascata sui GIUNTI_FIGLI connessi al GIUNTO, e nella stessa funzione associo anche le SCALE del GIUNTO_FIGLIO al nuovo PD:
            self.associa_padri_giunti('PD', 'GIUNTO_F_dev', GIUNTO_layer)
            #...mi fermo al PRIMO LIVELLO up-bottom poiche' al momento non richiesta
            #Poi passo ad associare a cascata sulle SCALE connesse al GIUNTO:
            self.associa_padri('PD', chiave_origine, SCALE_layer)
            self.associa_padri('PFS', chiave_origine, SCALE_layer)
            self.associa_padri('PFP', chiave_origine, SCALE_layer)
        #GIUNTO-PFS:
        if (layer_dest.name()==self.LAYER_NAME['PFS'] and layer_origine.name()==self.LAYER_NAME['GIUNTO']):
            #Prima associo i vari ID del PFS al GIUNTO:
            self.associa_padri('PFP', chiave_origine, GIUNTO_layer)
            #nel caso in cui questa GIUNTO abbia dei GIUNTI associati in cascata, devo associare anche a loro l'id del PFS:
            self.associa_padri_giunti('PFS', 'GIUNTO_F_dev', GIUNTO_layer)
            #Poi passo ad associare a cascata sulle SCALE connesse al GIUNTO anche NON direttamente:
            self.associa_padri('PFS', chiave_origine, SCALE_layer)
            self.associa_padri('PFP', chiave_origine, SCALE_layer)
        #GIUNTO-GIUNTO: In questo caso non faccio nulla poiche' l'ID del GIUNTO_PADRE non si trasmette fino alle SCALE figli del GIUNTO_FIGLIO...ma gli altri campi UP si!
        if (layer_dest.name()==self.LAYER_NAME['GIUNTO'] and layer_origine.name()==self.LAYER_NAME['GIUNTO']):
            #DA TESTARE!!!
            #Prima associo i vari ID del GIUNTO_PADRE al GIUNTO_FIGLIO:
            self.associa_padri('PD', 'GIUNTO', GIUNTO_layer)
            self.associa_padri('PFS', 'GIUNTO', GIUNTO_layer)
            self.associa_padri('PFP', 'GIUNTO', GIUNTO_layer)
            #Poi passo ad associare a cascata sulle SCALE connesse al GIUNTO -- OK!
            self.associa_padri('PD', 'GIUNTO', SCALE_layer)
            self.associa_padri('PFS', 'GIUNTO', SCALE_layer)
            self.associa_padri('PFP', 'GIUNTO', SCALE_layer)
        #SCALA-SCALA:
        if (layer_dest.name()==self.LAYER_NAME['SCALA'] and layer_origine.name()==self.LAYER_NAME['SCALA']):
            #DA TESTARE!!!
            #Associo i vari ID della SCALA_PADRE alla SCALA_FIGLIO:
            self.associa_padri('GIUNTO', 'SCALA', SCALE_layer)
            self.associa_padri('PD', 'SCALA', SCALE_layer)
            self.associa_padri('PFS', 'SCALA', SCALE_layer)
            self.associa_padri('PFP', 'SCALA', SCALE_layer)
        #PD-PD:
        if (layer_dest.name()==self.LAYER_NAME['PD'] and layer_origine.name()==self.LAYER_NAME['PD']):
            #DA TESTARE!!!
            #Prima associo i vari ID del PD_PADRE al PD_FIGLIO:
            self.associa_padri('PFS', 'PD', PD_layer)
            self.associa_padri('PFP', 'PD', PD_layer)
            #Poi associo a cascata sui GIUNTI connessi al PD - anche per eventuali GIUNTI_F :
            self.associa_padri('PFS', chiave_origine, GIUNTO_layer)
            self.associa_padri('PFP', chiave_origine, GIUNTO_layer)
            #Poi passo ad associare a cascata sulle SCALE connesse al PD anche NON direttamente:
            self.associa_padri('PFS', chiave_origine, SCALE_layer)
            self.associa_padri('PFP', chiave_origine, SCALE_layer)
        #PD-PFS:
        if (layer_dest.name()==self.LAYER_NAME['PFS'] and layer_origine.name()==self.LAYER_NAME['PD']):
            #Prima associo i vari ID del PFS al PD:
            self.associa_padri('PFP', chiave_origine, PD_layer)
            #nel caso in cui questa PD abbia delle PD associate in cascata, devo associare anche a loro l'id del PFS:
            self.associa_cascata_pd('PFS', 'PD_F', PD_layer)
            #Poi associo a cascata sui GIUNTI connessi al PD - anche per eventuali GIUNTI_F :
            self.associa_padri('PFS', chiave_origine, GIUNTO_layer)
            self.associa_padri('PFP', chiave_origine, GIUNTO_layer)
            #Poi passo ad associare a cascata sulle SCALE connesse al PD anche NON direttamente:
            self.associa_padri('PFS', chiave_origine, SCALE_layer)
            self.associa_padri('PFP', chiave_origine, SCALE_layer)
        #PFS-PFP:
        if (layer_dest.name()==self.LAYER_NAME['PFP'] and layer_origine.name()==self.LAYER_NAME['PFS']):
            #Associo l'ID del PFP ai vari PD connessi al PFS:
            self.associa_padri('PFP', chiave_origine, PD_layer)
            #Poi associo a cascata sui GIUNTI connessi al PFS:
            self.associa_padri('PFP', chiave_origine, GIUNTO_layer)
            #Poi passo ad associare a cascata sulle SCALE connesse al PFS anche NON direttamente:
            self.associa_padri('PFP', chiave_origine, SCALE_layer)
        
        self.dlg.txtFeedback.setText('Associazione avvenuta con successo!')
        #return 1
        
        #pER CAMBIARE L'ATTRIBUTO AL LAYER dovrebbe esssere:
        #layer.changeAttributeValue(feature.id(), columnnumber, value)
        
    
    def verifica_bottom_up(self, chiave_padre_up, layer_dest_up, layer_dest, TOT_UI_origine):
        #l'unico controllo che faccio e' sulle UI perche' i contatori li controllo solo al PRIMO STEP
        UI_dest_up = 0
        #In questa funziona a cascata verifico che i vincoli sulle UI vengano rispettati fino al PADRE
        idx_PADRE=layer_dest.fieldNameIndex(self.ID_NAME[chiave_padre_up]) #indice del campo ID_padre_up sul layer_dest
        #recupero l'ID e NON IL GID dell'elemento 'up' CHE DEVE ESSERE SOLO UNO
        ID_DEST_up=selected_features_dest[0][self.ID_NAME[chiave_padre_up]] #ID del padre_'up'
        if not(ID_DEST_up):
            #Cioe' il layer_dest non e' associato ad alcun padre_up: esco
            return UI_dest_up
        #Adesso dovrei interrogare l'ID 'up' per capire quante UI ha gia' associate:
        expr_id_figlio_padre = QgsExpression( "\"" + self.ID_NAME[chiave_padre_up] + "\" = '" +  ID_DEST_up + "'")
        UP_selezionati = layer_dest_up.getFeatures( QgsFeatureRequest( expr_id_figlio_padre ) )
        #Ora mi dovrei ritrovare solo con UNA FEATURE selezionata dal layer_up. Ma devo per forza selezionarli?
        #Build a list of feature Ids from the result obtained in 2.:
        ids_UP = [i.id() for i in UP_selezionati]
        #Select features with the ids obtained in 3.:
        layer_dest_up.removeSelection() #ripulisco eventuali selezioni precedenti
        layer_dest_up.setSelectedFeatures( ids_UP )
        UP_layer_ids_selezionate = layer_dest_up.selectedFeaturesIds()
        UP_layer_feature_selezionate = layer_dest_up.selectedFeatures()
        #for j_ids_up in UP_layer_ids_selezionate: #questo j_ids contiene giusto solo i GID
            #UI_dest_up = i['n_ui'] #sicuro che sia corretto "i"? non "j_ids_up"??
        for j_ids_up in UP_layer_feature_selezionate: #dovrebbe comunque SOLO ESSERE UNO
            UI_dest_up = j_ids_up['n_ui'] #da testare!!!
        #layer_dest_up.removeSelection() #ripulisco
        return UI_dest_up+TOT_UI_origine
        
    def associa_padri(self, chiave_padre, chiave_origine, layer_figlio):
        #ESEMPIO: self.associa_padri('PD', 'GIUNTO_F_DEV', GIUNTO_layer)
        #ES.: self.associa_padri('GIUNTO', 'SCALA', SCALE_layer)
        try:
            #In questa funzione a CASCATA associo ID padri a tutti i figli connessi:
            layer_figlio.startEditing()
            idx_FIGLI=layer_figlio.fieldNameIndex(self.ID_NAME[chiave_padre]) #campo ID_PD su SCALE
            #recupero l'ID e NON IL GID dell'elemento di destinazione CHE DEVE ESSERE SOLO UNO
            ID_DEST=selected_features_dest[0][self.ID_NAME[chiave_padre]] #ID del PD
            if not(ID_DEST): #cioe' se non ho nessun padre allora esco
                layer_figlio.rollBack()
                Utils.logMessage("Nessun padre " + str(chiave_padre) + " da associare, ritorno")
                return
            #ciclo dentro i GIUNTI di origine per recuperarne l'ID e selezionare cosi' le SCALE relative
            #OVVERO ciclo dentro gli elementi di origine selezionati per recuperarne l'ID e selezionare cosi poi i FIGLI a cui sono connessi.
            Utils.logMessage("ID Padre " + str(chiave_padre) + " da associare = " + str(ID_DEST))
            for jj in selected_features_origine:
                ID_ORIGINE=jj[self.ID_NAME[chiave_origine]] #ID del GIUNTO di origine
                expr_id_padre_figlio = QgsExpression( "\"" + self.ID_NAME[chiave_origine] + "\" = '" + ID_ORIGINE + "'")
                Utils.logMessage("Query di selezione = '" + self.ID_NAME[chiave_origine] + "' = " + ID_ORIGINE)
                FIGLI_selezionati = layer_figlio.getFeatures( QgsFeatureRequest( expr_id_padre_figlio ) )
                #Build a list of feature Ids from the result obtained in 2.:
                ids_FIGLI = [i.id() for i in FIGLI_selezionati]
                #Select features with the ids obtained in 3.:
                layer_figlio.removeSelection() #ripulisco eventuali selezioni precedenti
                layer_figlio.setSelectedFeatures( ids_FIGLI )
                FIGLI_layer_ids_selezionate = layer_figlio.selectedFeaturesIds()
                for j_ids in FIGLI_layer_ids_selezionate:
                    layer_figlio.changeAttributeValue(j_ids, idx_FIGLI, ID_DEST)
        except SystemError, e:
            Utils.logMessage(str(e))
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Associazione NON avvenuta padri-figlio')
            layer_figlio.rollBack()
        else:
            #layer_figlio.removeSelection() #ripulisco
            layer_figlio.commitChanges()
    
    def associa_cascata_scala(self, chiave_padre, chiave_origine, layer_figlio):
        #Uso questa funzione per connex SCALA-SCALA.
        #Potrebbe essere uguale a associa_padri_giunti ma quest'ultima non la voglio modificare, visto he funzionava...!
        try:
            #In questa funzione a CASCATA associo ID padri a tutti i figli connessi. Pensato specificatamente per le connessioni SCALA-SCALA prendendo in considerazione le SCALE FIGLIE
            layer_figlio.startEditing()
            #SCALE_layer.startEditing()
            idx_FIGLI=layer_figlio.fieldNameIndex(self.ID_NAME[chiave_padre]) #campo ID_GIUNTO su SCALA_F
            #recupero l'ID e NON IL GID dell'elemento di destinazione CHE DEVE ESSERE SOLO UNO
            ID_DEST=selected_features_dest[0][self.ID_NAME[chiave_padre]] #ID del GIUNTO
            #ciclo dentro gli elementi di origine selezionati per recuperarne l'ID e selezionare cosi poi i FIGLI a cui sono connessi.
            for jj in selected_features_origine:
                ID_ORIGINE=jj[self.ID_NAME['SCALA']] #ID della SCALA_PADRE di origine, che sto associando al GIUNTO in questo momento
                expr_id_padre_figlio = QgsExpression( "\"" + self.ID_NAME[chiave_origine] + "\" = '" +  ID_ORIGINE + "'")
                Utils.logMessage("Query di selezione = '" + self.ID_NAME[chiave_origine] + "' = " +  ID_ORIGINE)
                FIGLI_selezionati = layer_figlio.getFeatures( QgsFeatureRequest( expr_id_padre_figlio ) )
                #Build a list of feature Ids from the result obtained in 2.:
                ids_FIGLI = [i.id() for i in FIGLI_selezionati]
                #Select features with the ids obtained in 3.:
                layer_figlio.removeSelection() #ripulisco eventuali selezioni precedenti
                layer_figlio.setSelectedFeatures( ids_FIGLI )
                FIGLI_layer_ids_selezionate = layer_figlio.selectedFeaturesIds()
                FIGLI_layer_feature_selezionate = layer_figlio.selectedFeatures()
                #for j_ids in FIGLI_layer_ids_selezionate: #questo j_ids contiene giusto solo i GID
                for j_ids in FIGLI_layer_feature_selezionate:
                    j_ids_gid = j_ids['gid']
                    layer_figlio.changeAttributeValue(j_ids_gid, idx_FIGLI, ID_DEST)
                    '''#A questo punto seleziono le SCALE connesse a questi GIUNTI_F:
                    idx_SCALE=SCALE_layer.fieldNameIndex(self.ID_NAME[chiave_padre]) #campo ID_PD su SCALE
                    ID_GIUNTO_F=j_ids[self.ID_NAME['GIUNTO']] #ID del GIUNTO_FIGLIO
                    expr_id_giuntof_scala = QgsExpression( "\"" + self.ID_NAME['GIUNTO'] + "\" = '" +  ID_GIUNTO_F + "'")
                    Utils.logMessage("Query di selezione SCALE da GIUNTO_F = '" + self.ID_NAME['GIUNTO'] + "' = " +  ID_GIUNTO_F)
                    SCALE_selezionate = SCALE_layer.getFeatures( QgsFeatureRequest( expr_id_giuntof_scala ) )
                    ids_scale = [i.id() for i in SCALE_selezionate]
                    SCALE_layer.removeSelection() #ripulisco eventuali selezioni precedenti
                    SCALE_layer.setSelectedFeatures( ids_scale )
                    SCALE_layer_ids_selezionate = SCALE_layer.selectedFeaturesIds()
                    for jj_ids in SCALE_layer_ids_selezionate:
                        SCALE_layer.changeAttributeValue(jj_ids, idx_SCALE, ID_DEST)'''
        except:
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Errore di sistema! Associazione del nuovo ID alle scale_figlie NON avvenuta. Se non vi sono scale_figlie, allora il problema non vi riguarda.')
            layer_figlio.rollBack()
            #SCALE_layer.rollBack()
        else:
            #layer_figlio.removeSelection() #ripulisco
            layer_figlio.commitChanges()
            #SCALE_layer.commitChanges()
    
    def associa_cascata_pd(self, chiave_padre, chiave_origine, layer_figlio):
        #Uso questa funzione per connex PD-PD.
        #Potrebbe essere uguale a associa_padri_giunti ma quest'ultima non la voglio modificare, visto he funzionava...!
        try:
            #In questa funzione a CASCATA associo ID padri a tutti i figli connessi. Pensato specificatamente per le connessioni PD-PD prendendo in considerazione le PD FIGLIE
            layer_figlio.startEditing()
            #SCALE_layer.startEditing()
            idx_FIGLI=layer_figlio.fieldNameIndex(self.ID_NAME[chiave_padre]) #campo ID_PFS su PD_F
            #recupero l'ID e NON IL GID dell'elemento di destinazione CHE DEVE ESSERE SOLO UNO
            ID_DEST=selected_features_dest[0][self.ID_NAME[chiave_padre]] #ID del PFS di destinazione
            #ciclo dentro gli elementi di origine selezionati per recuperarne l'ID e selezionare cosi poi i FIGLI a cui sono connessi.
            for jj in selected_features_origine:
                ID_ORIGINE=jj[self.ID_NAME['PD']] #ID del PD_PADRE di origine, che sto associando al PFS in questo momento
                expr_id_padre_figlio = QgsExpression( "\"" + self.ID_NAME[chiave_origine] + "\" = '" +  ID_ORIGINE + "'")
                Utils.logMessage("Query di selezione = '" + self.ID_NAME[chiave_origine] + "' = " +  ID_ORIGINE)
                FIGLI_selezionati = layer_figlio.getFeatures( QgsFeatureRequest( expr_id_padre_figlio ) )
                #Build a list of feature Ids from the result obtained in 2.:
                ids_FIGLI = [i.id() for i in FIGLI_selezionati]
                #Select features with the ids obtained in 3.:
                layer_figlio.removeSelection() #ripulisco eventuali selezioni precedenti
                layer_figlio.setSelectedFeatures( ids_FIGLI )
                FIGLI_layer_ids_selezionate = layer_figlio.selectedFeaturesIds()
                FIGLI_layer_feature_selezionate = layer_figlio.selectedFeatures()
                #for j_ids in FIGLI_layer_ids_selezionate: #questo j_ids contiene giusto solo i GID
                for j_ids in FIGLI_layer_feature_selezionate:
                    j_ids_gid = j_ids['gid']
                    layer_figlio.changeAttributeValue(j_ids_gid, idx_FIGLI, ID_DEST)
                    '''#A questo punto seleziono le SCALE connesse a questi GIUNTI_F:
                    idx_SCALE=SCALE_layer.fieldNameIndex(self.ID_NAME[chiave_padre]) #campo ID_PD su SCALE
                    ID_GIUNTO_F=j_ids[self.ID_NAME['GIUNTO']] #ID del GIUNTO_FIGLIO
                    expr_id_giuntof_scala = QgsExpression( "\"" + self.ID_NAME['GIUNTO'] + "\" = '" +  ID_GIUNTO_F + "'")
                    Utils.logMessage("Query di selezione SCALE da GIUNTO_F = '" + self.ID_NAME['GIUNTO'] + "' = " +  ID_GIUNTO_F)
                    SCALE_selezionate = SCALE_layer.getFeatures( QgsFeatureRequest( expr_id_giuntof_scala ) )
                    ids_scale = [i.id() for i in SCALE_selezionate]
                    SCALE_layer.removeSelection() #ripulisco eventuali selezioni precedenti
                    SCALE_layer.setSelectedFeatures( ids_scale )
                    SCALE_layer_ids_selezionate = SCALE_layer.selectedFeaturesIds()
                    for jj_ids in SCALE_layer_ids_selezionate:
                        SCALE_layer.changeAttributeValue(jj_ids, idx_SCALE, ID_DEST)'''
        except:
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Errore di sistema! Associazione del nuovo ID ai pd_figli NON avvenuta. Se non vi sono pd_figli, allora il problema non vi riguarda.')
            layer_figlio.rollBack()
            #SCALE_layer.rollBack()
        else:
            #layer_figlio.removeSelection() #ripulisco
            layer_figlio.commitChanges()
            #SCALE_layer.commitChanges()
    
    def associa_padri_giunti(self, chiave_padre, chiave_origine, layer_figlio):
        try:
            #In questa funzione a CASCATA associo ID padri a tutti i figli connessi. Pensato specificatamente per le connessioni GIUNTO-GIUNTO prendendo in considerazione anche le SCALE connesse ai GIUNTI_FIGLI
            layer_figlio.startEditing()
            SCALE_layer.startEditing()
            idx_FIGLI=layer_figlio.fieldNameIndex(self.ID_NAME[chiave_padre]) #campo ID_PD su GIUNTO_F
            #recupero l'ID e NON IL GID dell'elemento di destinazione CHE DEVE ESSERE SOLO UNO
            ID_DEST=selected_features_dest[0][self.ID_NAME[chiave_padre]] #ID del PD
            if not(ID_DEST): #cioe' se non ho nessun padre allora esco
                layer_figlio.rollBack()
                SCALE_layer.rollBack()
                Utils.logMessage("Nessun padre " + str(chiave_padre) + " da associare, ritorno")
                return
            #ciclo dentro i GIUNTI di origine per recuperarne l'ID e selezionare cosi' le SCALE relative
            #OVVERO ciclo dentro gli elementi di origine selezionati per recuperarne l'ID e selezionare cosi poi i FIGLI a cui sono connessi.
            for jj in selected_features_origine:
                ID_ORIGINE=jj[self.ID_NAME['GIUNTO']] #ID del GIUNTO_PADRE di origine
                expr_id_padre_figlio = QgsExpression( "\"" + self.ID_NAME[chiave_origine] + "\" = '" +  ID_ORIGINE + "'")
                Utils.logMessage("Query di selezione = '" + self.ID_NAME[chiave_origine] + "' = " +  ID_ORIGINE)
                FIGLI_selezionati = layer_figlio.getFeatures( QgsFeatureRequest( expr_id_padre_figlio ) )
                #Build a list of feature Ids from the result obtained in 2.:
                ids_FIGLI = [i.id() for i in FIGLI_selezionati]
                #Select features with the ids obtained in 3.:
                layer_figlio.removeSelection() #ripulisco eventuali selezioni precedenti
                layer_figlio.setSelectedFeatures( ids_FIGLI )
                FIGLI_layer_ids_selezionate = layer_figlio.selectedFeaturesIds()
                FIGLI_layer_feature_selezionate = layer_figlio.selectedFeatures()
                #for j_ids in FIGLI_layer_ids_selezionate: #questo j_ids contiene giusto solo i GID
                for j_ids in FIGLI_layer_feature_selezionate:
                    j_ids_gid = j_ids['gid']
                    layer_figlio.changeAttributeValue(j_ids_gid, idx_FIGLI, ID_DEST)
                    #A questo punto seleziono le SCALE connesse a questi GIUNTI_F:
                    idx_SCALE=SCALE_layer.fieldNameIndex(self.ID_NAME[chiave_padre]) #campo ID_PD su SCALE
                    ID_GIUNTO_F=j_ids[self.ID_NAME['GIUNTO']] #ID del GIUNTO_FIGLIO
                    expr_id_giuntof_scala = QgsExpression( "\"" + self.ID_NAME['GIUNTO'] + "\" = '" +  ID_GIUNTO_F + "'")
                    Utils.logMessage("Query di selezione SCALE da GIUNTO_F = '" + self.ID_NAME['GIUNTO'] + "' = " +  ID_GIUNTO_F)
                    SCALE_selezionate = SCALE_layer.getFeatures( QgsFeatureRequest( expr_id_giuntof_scala ) )
                    ids_scale = [i.id() for i in SCALE_selezionate]
                    SCALE_layer.removeSelection() #ripulisco eventuali selezioni precedenti
                    SCALE_layer.setSelectedFeatures( ids_scale )
                    SCALE_layer_ids_selezionate = SCALE_layer.selectedFeaturesIds()
                    for jj_ids in SCALE_layer_ids_selezionate:
                        SCALE_layer.changeAttributeValue(jj_ids, idx_SCALE, ID_DEST)
        except:
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Associazione delle scale dei giunti_figli NON avvenuta')
            layer_figlio.rollBack()
            SCALE_layer.rollBack()
        else:
            #layer_figlio.removeSelection() #ripulisco
            layer_figlio.commitChanges()
            SCALE_layer.commitChanges()
    
    
    def associa_UI_cascata(self, jj_ids_up, chiave_padre_up, layer_dest_up, idx_UI_up, TOT_UI_origine, ancora_padre):
        #ES. associa_UI_cascata(jj_ids_up, 'SCALA', SCALE_layer, idx_UI_up, TOT_UI_origine, 'SCALA_F')
        ID_DEST_super_up=jj_ids_up[self.ID_NAME[ancora_padre]]
        expr_id_super_padre = QgsExpression( "\"" + self.ID_NAME[chiave_padre_up] + "\" = '" +  ID_DEST_super_up + "'")
        super_UP_selezionati = layer_dest_up.getFeatures( QgsFeatureRequest( expr_id_super_padre ) )
        #Ora mi dovrei ritrovare solo con UNA FEATURE selezionata dal layer_up.
        ids_super_UP = [i.id() for i in super_UP_selezionati]
        Utils.logMessage("super UP selezionati da "+chiave_padre_up+": "+str(ids_super_UP))
        layer_dest_up.removeSelection() #ripulisco eventuali selezioni precedenti
        layer_dest_up.setSelectedFeatures( ids_super_UP )
        super_UP_layer_ids_selezionate = layer_dest_up.selectedFeaturesIds() #DEVE CONTENERE UN SOLO ID!!
        super_UP_selected_features_dest = layer_dest_up.selectedFeatures()
        for kk_ids_up in super_UP_selected_features_dest:
            Utils.logMessage("Oggetto super UP selezionato "+str(kk_ids_up))
            UI_dest_super_up = kk_ids_up['n_ui']
            layer_dest_up.changeAttributeValue(int(super_UP_layer_ids_selezionate[0]), idx_UI_up, UI_dest_super_up+TOT_UI_origine)
            if (kk_ids_up[self.ID_NAME[ancora_padre]]):
                return 1 #c'e ancora un padre
            else:
                return 0
    
    def associa_UI_bottom_up(self, chiave_padre_up, layer_dest_up, layer_dest, ancora_padre=None):
        #In questa funziona a cascata associo le UI dai figli a tutti i connessi:
        #ESEMPIO: associazione GI-PD chiamo associa_UI_bottom_up('PFS', PFS_layer, layer_dest)
        #ESEMPIO: per associare UI a eventuali GIUNTI_PADRI: associa_UI_bottom_up('GIUNTO_F_dev', GIUNTO_layer, layer_dest)
        #ESEMPIO: per cercare sotto_padri: associa_UI_bottom_up('GIUNTO', GIUNTO_layer, layer_dest, 'GIUNTO_F_dev')
        try:
            layer_dest_up.startEditing()
            UI_dest_up = 0
            idx_PADRE=layer_dest.fieldNameIndex(self.ID_NAME[chiave_padre_up]) #indice del campo ID_padre_up sul layer_dest
            idx_UI_up = layer_dest_up.fieldNameIndex('n_ui') #indice del campo 'n_ui' sul layer_dest_up
            #recupero l'ID e NON IL GID dell'elemento 'up' CHE DEVE ESSERE SOLO UNO
            ID_DEST_up=selected_features_dest[0][self.ID_NAME[chiave_padre_up]] #ID del padre_'up'
            if not(ID_DEST_up):
                #Cioe' il layer_dest non e' associato ad alcun padre_up: esco
                layer_dest_up.rollBack()
                return 0
            #Adesso dovrei interrogare l'ID 'up' per capire quante UI ha gia' associate:
            expr_id_figlio_padre = QgsExpression( "\"" + self.ID_NAME[chiave_padre_up] + "\" = '" +  ID_DEST_up + "'")
            UP_selezionati = layer_dest_up.getFeatures( QgsFeatureRequest( expr_id_figlio_padre ) )
            #Ora mi dovrei ritrovare solo con UNA FEATURE selezionata dal layer_up.
            #Build a list of feature Ids from the result obtained in 2.:
            ids_UP = [i.id() for i in UP_selezionati]
            Utils.logMessage("UP selezionati da "+chiave_padre_up+": "+str(ids_UP))
            #Select features with the ids obtained in 3.:
            layer_dest_up.removeSelection() #ripulisco eventuali selezioni precedenti
            layer_dest_up.setSelectedFeatures( ids_UP )
            UP_layer_ids_selezionate = layer_dest_up.selectedFeaturesIds() #DEVE CONTENERE UN SOLO ID!!
            UP_selected_features_dest = layer_dest_up.selectedFeatures()
            for jj_ids_up in UP_selected_features_dest:
                Utils.logMessage("Oggetto UP selezionato "+str(jj_ids_up))
                UI_dest_up = jj_ids_up['n_ui']
                layer_dest_up.changeAttributeValue(int(UP_layer_ids_selezionate[0]), idx_UI_up, UI_dest_up+TOT_UI_origine)
                #se l'oggetto in questione e' figlio di qualcuno:
                if (ancora_padre and jj_ids_up[self.ID_NAME[ancora_padre]]):
                    Utils.logMessage("Oggetto UP "+str(chiave_padre_up)+"ha ancora un padre")
                    #vuol dire che il padre ha a sua volta un altro padre. Lo individuo e gli attacco le UI degli elementi di origine:
                    #proviamo a lanciare una funzione esterna in modo da andare in loop e beccare tutta la cascata potenzialmente:
                    while self.associa_UI_cascata(jj_ids_up, chiave_padre_up, layer_dest_up, idx_UI_up, TOT_UI_origine, ancora_padre) != 0:
                        pass
                    '''ID_DEST_super_up=jj_ids_up[self.ID_NAME[ancora_padre]]
                    expr_id_super_padre = QgsExpression( "\"" + self.ID_NAME[chiave_padre_up] + "\" = '" +  ID_DEST_super_up + "'")
                    super_UP_selezionati = layer_dest_up.getFeatures( QgsFeatureRequest( expr_id_super_padre ) )
                    #Ora mi dovrei ritrovare solo con UNA FEATURE selezionata dal layer_up.
                    ids_super_UP = [i.id() for i in super_UP_selezionati]
                    Utils.logMessage("super UP selezionati da "+chiave_padre_up+": "+str(ids_super_UP))
                    layer_dest_up.removeSelection() #ripulisco eventuali selezioni precedenti
                    layer_dest_up.setSelectedFeatures( ids_super_UP )
                    super_UP_layer_ids_selezionate = layer_dest_up.selectedFeaturesIds() #DEVE CONTENERE UN SOLO ID!!
                    super_UP_selected_features_dest = layer_dest_up.selectedFeatures()
                    for kk_ids_up in super_UP_selected_features_dest:
                        Utils.logMessage("Oggetto super UP selezionato "+str(kk_ids_up))
                        UI_dest_super_up = kk_ids_up['n_ui']
                        layer_dest_up.changeAttributeValue(int(super_UP_layer_ids_selezionate[0]), idx_UI_up, UI_dest_super_up+TOT_UI_origine)'''
            #layer_dest_up.removeSelection() #ripulisco
        except:
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Associazione delle UI ai layer UP NON avvenuta')
            layer_dest_up.rollBack()
        else:
            layer_dest_up.commitChanges()
        #layer_dest_up.commitChanges()
        
    def associa_UI_bottom_up_figli(self, chiave_padre_up, layer_dest_up, layer_dest, campo_id_up):
        #In questa funziona a cascata associo le UI dai figli a tutti i PADRI connessi:
        #ESEMPIO: per associare UI a eventuali GIUNTI_PADRI: associa_UI_bottom_up('GIUNTO_F_dev', GIUNTO_layer, layer_dest, 'GIUNTO')
        #ES. associa_UI_bottom_up_figli('SCALA_F', SCALE_layer, layer_dest, 'SCALA')
        #ES. per beccare il PADRE del PADRE: self.associa_UI_bottom_up_figli('GIUNTO', GIUNTO_layer, layer_dest, 'GIUNTO')
        try:
            layer_dest_up.startEditing()
            UI_dest_up = 0        
            idx_PADRE=layer_dest.fieldNameIndex(self.ID_NAME[chiave_padre_up]) #indice del campo ID_padre_up sul layer_dest
            idx_UI_up = layer_dest_up.fieldNameIndex('n_ui') #indice del campo 'n_ui' sul layer_dest_up
            #recupero l'ID e NON IL GID dell'elemento 'up' CHE DEVE ESSERE SOLO UNO
            ID_DEST_up=selected_features_dest[0][self.ID_NAME[chiave_padre_up]] #ID del padre_'up'. ad es. valore di "id_g_ref"
            if not(ID_DEST_up):
                #Cioe' il layer_dest non e' associato ad alcun padre_up: esco
                Utils.logMessage("Layer non ha un ulteriore padre: "+chiave_padre_up)
                layer_dest_up.rollBack()
                return 0
            #Adesso dovrei interrogare l'ID 'up' per capire quante UI ha gia' associate:
            expr_id_figlio_padre = QgsExpression( "\"" + self.ID_NAME[campo_id_up] + "\" = '" +  ID_DEST_up + "'")
            UP_selezionati = layer_dest_up.getFeatures( QgsFeatureRequest( expr_id_figlio_padre ) )
            #Ora mi dovrei ritrovare solo con UNA FEATURE selezionata dal layer_up.
            #Build a list of feature Ids from the result obtained in 2.:
            ids_UP = [i.id() for i in UP_selezionati]
            Utils.logMessage("UP selezionati da "+campo_id_up+": "+str(ids_UP))
            #Select features with the ids obtained in 3.:
            layer_dest_up.removeSelection() #ripulisco eventuali selezioni precedenti
            layer_dest_up.setSelectedFeatures( ids_UP )
            UP_layer_ids_selezionate = layer_dest_up.selectedFeaturesIds() #DEVE CONTENERE UN SOLO ID!!
            UP_selected_features_dest = layer_dest_up.selectedFeatures()
            for jj_ids_up in UP_selected_features_dest:
                Utils.logMessage("Oggetto UP selezionato "+str(jj_ids_up))
                UI_dest_up = jj_ids_up['n_ui']
                layer_dest_up.changeAttributeValue(int(UP_layer_ids_selezionate[0]), idx_UI_up, UI_dest_up+TOT_UI_origine)
                #se l'oggetto in questione e' a sua volta figlio di qualcuno:
                if (jj_ids_up[self.ID_NAME[chiave_padre_up]]):
                    Utils.logMessage("Oggetto UP "+str(campo_id_up)+" con ID " + str(ids_UP) + "ha ancora un padre")
                    #proviamo a lanciare una funzione esterna in modo da andare in loop e beccare tutta la cascata potenzialmente e attaccargli le UI degli elementi di origine:
                    while self.associa_UI_cascata(jj_ids_up, campo_id_up, layer_dest_up, idx_UI_up, TOT_UI_origine, chiave_padre_up) != 0:
                    #ES. associa_UI_cascata(jj_ids_up, 'SCALA', SCALE_layer, idx_UI_up, TOT_UI_origine, 'SCALA_F')
                        pass
            #layer_dest_up.removeSelection() #ripulisco
        except SystemError, e:
            QMessageBox.critical(self.dock, self.dock.windowTitle(), 'Errore di sistema! Associazione delle UI ai layer UP NON avvenuta')
            layer_dest_up.rollBack()
        else:
            layer_dest_up.commitChanges()
        #layer_dest_up.commitChanges()
        
    
    #--------------------------------------------------------------------------

    def test_connection(self):
        self.dlg_config.testAnswer.clear()
        self.dlg_config.txtFeedback.clear()
        self.dlg_config.chkDB.setEnabled(True);
        userDB = self.dlg_config.usrDB.text()
        pwdDB = self.dlg_config.pwdDB.text()
        hostDB = self.dlg_config.hostDB.text()
        portDB = self.dlg_config.portDB.text()
        nameDB = self.dlg_config.nameDB.text()
        schemaDB = self.dlg_config.schemaDB.text()
        global dest_dir
        dest_dir = "dbname=%s host=%s port=%s user=%s password=%s" % (nameDB, hostDB, portDB, userDB, pwdDB)
        #open DB with psycopg2
        test_conn = None
        try:
            test_conn = psycopg2.connect(dest_dir)
            cur = test_conn.cursor()
            cur.execute( "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = '%s');" % (schemaDB) )
            msg = QMessageBox()
            if cur.fetchone()[0]==True:
                msg.setText("ATTENZIONE! Lo schema indicato e' gia' esistente, eventuali tabelle gia' presenti al suo interno verranno sovrascritte: si desidera continuare?\nN.B.: Le tabelle verranno eventualmente sovrascritte se si decidera' di importare nuovi dati nella sezione B.")
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Schema gia' esistente! Sovrascrivere dati con stesso nome?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                retval = msg.exec_()
                if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                    return False
                elif (retval == 16384): #l'utente HA CLICCATO YES. Posso continuare
                    debug_text = "OK! Puoi passare alla successiva sezione B"
                    self.dlg_config.testAnswer.setText(debug_text)
                    #Verifico di avere tutte le informazioni necessarie per decidere se abilitare o meno il pulsante INIZIALIZZA
                    #self.dlg_config.importBtn.setEnabled(True)
                    self.dlg_config.chkDB.setEnabled(False)
                    self.dlg_config.import_DB.setEnabled(True)
                    return retval
            else:
                msg.setText("ATTENZIONE! Lo schema indicato non e' presente sul DB: si desidera crearlo?")
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Schema non esistente: crearlo?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                retval = msg.exec_()
                if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                    return False
                elif (retval == 16384): #l'utente HA CLICCATO YES. Posso continuare
                    cur.execute( "CREATE SCHEMA IF NOT EXISTS %s AUTHORIZATION operatore;" % (schemaDB) )
                    test_conn.commit()
                    debug_text = "OK! Puoi passare alla successiva sezione B"
                    self.dlg_config.testAnswer.setText(debug_text)
                    #Verifico di avere tutte le informazioni necessarie per decidere se abilitare o meno il pulsante INIZIALIZZA
                    #self.dlg_config.importBtn.setEnabled(True)
                    self.dlg_config.chkDB.setEnabled(False)
                    self.dlg_config.import_DB.setEnabled(True)
                    return retval
        except psycopg2.Error, e:
            Utils.logMessage(str(e.pgcode) + str(e.pgerror)) #ERRORE: unsupported operand type(s) for +: 'NoneType' and 'NoneType'
            debug_text = "Connessione al DB fallita!! Rivedere i dati e riprovare"
            self.dlg_config.txtFeedback.setText(debug_text)
            self.dlg_config.testAnswer.setText("FAIL! Inserisci dei dati corretti e continua")
            self.dlg_config.importBtn.setEnabled(False)
            return 0
            '''except dbConnection.DbError, e:
            Utils.logMessage("dbname:" + dbname + ", " + e.msg)
            debug_text = "Connessione al DB fallita!! Rivedere i dati e riprovare"
            self.dlg_config.txtFeedback.setText(debug_text)'''
        except SystemError, e:
            debug_text = "Connessione al DB fallita!! Rivedere i dati e riprovare"
            self.dlg_config.txtFeedback.setText(debug_text)
            self.dlg_config.testAnswer.setText('FAIL!')
            self.dlg_config.importBtn.setEnabled(False)
            return 0
        finally:
            if test_conn:
                test_conn.close()
        

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ProgettoFTTH', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        #TEST: carico solo un primo pannello di prova da mostrare ad ANDREA:
        icon_path = ':/plugins/ProgettoFTTH/download_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Importa i dati da SHP sul DB e inizializza il nuovo progetto QGis'),
            callback=self.run_config,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/ProgettoFTTH/append_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'aggiungi delle SCALE al layer SCALA gia esistente'),
            callback=self.run_append,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/ProgettoFTTH/grouping_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Associa i punti tra loro: grouping'),
            callback=self.run_core,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/ProgettoFTTH/compare_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Verifica le connessioni'),
            callback=self.run_compare,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/ProgettoFTTH/cavo_route_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Consolida il progetto: routing'),
            callback=self.run_cavoroute,
            parent=self.iface.mainWindow())
            
        icon_path = ':/plugins/ProgettoFTTH/export_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Esporta il progetto in shp'),
            callback=self.run_export,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/ProgettoFTTH/computo_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Computo metrico'),
            callback=self.run_metrico,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/ProgettoFTTH/counting_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Numerazione punti rete'),
            callback=self.run_numerazione,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/ProgettoFTTH/razor_blade_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Taglia cavo alle intersezioni'),
            callback=self.run_cutcable,
            parent=self.iface.mainWindow())
            
        icon_path = ':/plugins/ProgettoFTTH/calc_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'calcola campi aggiuntivi su cavo'),
            callback=self.run_calcable,
            parent=self.iface.mainWindow())
            
        icon_path = ':/plugins/ProgettoFTTH/update_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'aggiorna le funzioni a livello di DB'),
            callback=self.run_updatedb,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/ProgettoFTTH/help_C83737.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Informazioni'),
            callback=self.run_help,
            parent=self.iface.mainWindow())


        #load the form
        path = os.path.dirname(os.path.abspath(__file__))
        self.dock = uic.loadUi(os.path.join(path, "progetto_ftth_dockwidget_base.ui")) #OK
        self.dock_compare = uic.loadUi(os.path.join(path, "progetto_ftth_compare_dockwidget_base.ui"))
        
        #se modifico il drop down faccio partire un'azione:
        QObject.connect(self.dlg_compare.comboBoxFromPoint, SIGNAL("currentIndexChanged(const QString&)"), self.updateFromSelection_compare)
        
        #----------------------------------------------------
        #TEST: aggiungo DockWidget: ridefinisco qui perche' dal run_core non sembrava prenderlo
        if self.dockwidget == None:
            # Create the dockwidget (after translation) and keep reference
            self.dockwidget = CoreDockWidget()
        #Per non riscrivere tutto il codice precedente, avendo eliminato il QDialog per sostituirlo con questo DockWidget, equiparo le 2 variaibli:
        self.dlg = self.dockwidget

        #Nella versione 4.4 metto qui il pulsante per la verifica delle associazioni:
        #QObject.connect(self.dockwidget.solid_btn_aree, SIGNAL("clicked()"), self.lancia_consolida_aree_dlg)
        QObject.connect(self.dockwidget.solid_btn_aree, SIGNAL("clicked()"), self.check_grouping_from_user)
        
        #Scelgo che punto voglio associare e faccio partire in qualche modo il controllo sulla selezione sulla mappa:
        QObject.connect(self.dockwidget.scala_scala_btn, SIGNAL("clicked()"), self.associa_scala_scala)
        #QObject.connect(self.dockwidget.scala_giunto_btn, SIGNAL("clicked()"), self.associa_scala_giunto)
        QObject.connect(self.dockwidget.scala_giunto_btn, SIGNAL("clicked()"), self.associa_scala_muffola)
        QObject.connect(self.dockwidget.scala_pta_btn, SIGNAL("clicked()"), self.associa_scala_pta)
        QObject.connect(self.dockwidget.scala_pd_btn, SIGNAL("clicked()"), self.associa_scala_pd)
        QObject.connect(self.dockwidget.scala_pfs_btn, SIGNAL("clicked()"), self.associa_scala_pfs)
        #QObject.connect(self.dockwidget.giunto_giunto_btn, SIGNAL("clicked()"), self.associa_giunto_giunto)
        QObject.connect(self.dockwidget.giunto_giunto_dev_btn, SIGNAL("clicked()"), self.associa_giunto_giunto_dev)
        #QObject.connect(self.dockwidget.giunto_pd_btn, SIGNAL("clicked()"), self.associa_giunto_pd)
        QObject.connect(self.dockwidget.pta_pfs_btn, SIGNAL("clicked()"), self.associa_pta_pfs)
        QObject.connect(self.dockwidget.pd_pd_btn, SIGNAL("clicked()"), self.associa_pd_pd)
        QObject.connect(self.dockwidget.pd_pfs_btn, SIGNAL("clicked()"), self.associa_pd_pfs)
        QObject.connect(self.dockwidget.pfs_pfp_btn, SIGNAL("clicked()"), self.associa_pfs_pfp)
        
        
        global check_origine #variabile booleana che mi dice se e' tutto ok lato origine
        check_origine = 0
        global check_dest #variabile booleana che mi dice se e' tutto ok lato destinazione
        check_dest = 0
        global selected_features_origine
        global selected_features_ids_origine
        global selected_features_dest
        global selected_features_ids_dest
        global TOT_UI_origine
        global TOT_UI_dest
        global TOT_giunti_dest
        global TOT_pd_dest
        global TOT_pfs_dest
        global TOT_ncont_dest
        global TOT_ncont_origine
        
        #ripulisco tutte le selezioni in mappa - NON FUNZIONA!
        #lg = iface.mainWindow().findChild(QTreeWidget, 'theMapLegend')
        #lg.selectionModel().clear()  # clear just selection
        #lg.setCurrentItem(None)  # clear selection and active layer

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Progetto ENEL'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

        '''for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Core'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar'''

    def run_config(self):
        # show the dialog
        self.dlg_config.show()
        # Run the dialog event loop
        result = self.dlg_config.exec_()
        self.dlg_config.txtFeedback.clear()
        self.dlg_config.txtFeedback_import.clear()
        self.dlg_config.dirBrowse_txt.clear()
        self.dlg_config.import_progressBar.setValue(0)
        #self.dlg_config.usrDB.clear()
        #self.dlg_config.pwdDB.clear()
        #self.dlg_config.hostDB.clear()
        #self.dlg_config.portDB.clear()
        #self.dlg_config.nameDB.clear()
        #self.dlg_config.schemaDB.clear()
        #self.dlg_config.comuneDB.clear()
        #self.dlg_config.codpopDB.clear()
        self.dlg_config.testAnswer.clear()
        self.dlg_config.chkDB.setEnabled(True);
        self.dlg_config.importBtn.setEnabled(False);
        
        self.dlg_config.import_DB.setEnabled(False);
        self.dlg_config.variabili_DB.setEnabled(False);
        self.dlg_config.si_import.setChecked(False)
        self.dlg_config.no_import.setChecked(False)
        self.dlg_config.modifica_variabili.setChecked(False)
        
        self.dlg_config.shpBrowse_txt.clear()
        #self.dlg_config.cavoBrowse_txt.clear()
        self.dlg_config.si_inizializza.setChecked(False)
        self.dlg_config.txtFeedback_inizializza.clear()
        
        
    def run_compare(self):
        # show the dialog
        self.dlg_compare.show()
        # Run the dialog event loop
        result = self.dlg_compare.exec_()
        self.dlg_compare.txtFeedback.clear()
        idx_1 = self.dlg_compare.comboBoxFromPoint.findText(self.FROM_POINT[0])
        self.dlg_compare.comboBoxFromPoint.setCurrentIndex(idx_1)
        
    def run_export(self):
        result_init = self.inizializza_layer()
        if (result_init==0):
            return 0
        #recupero le info di connex al DB da un qualunque dei layer:
        connInfo = SCALE_layer.source()
        db_dir = self.estrai_param_connessione(connInfo)
        # show the dialog
        self.dlg_export.show()
        # Run the dialog event loop
        result = self.dlg_export.exec_()
        self.dlg_export.txtFeedback.clear()
        
    def run_metrico(self):
        result_init = self.inizializza_layer()
        if (result_init==0):
            return 0
        #recupero le info di connex al DB da un qualunque dei layer:
        connInfo = SCALE_layer.source()
        db_dir = self.estrai_param_connessione(connInfo)
        result_metrico = computo_metrico.calc_computo_metrico(db_dir, self, theSchema)
        # show the dialog
        #self.dlg_export.show()
        # Run the dialog event loop
        #result = self.dlg_export.exec_()
        #self.dlg_export.txtFeedback.clear()
        
    def run_numerazione(self):
        result_init = self.inizializza_layer()
        if (result_init==0):
            return 0
        #recupero le info di connex al DB da un qualunque dei layer:
        connInfo = SCALE_layer.source()
        db_dir = self.estrai_param_connessione(connInfo)
        result_numerazione = numerazione_puntirete.numerazione_ftth(db_dir, self, theSchema)
    
    def run_append(self):
        #Appendo delle nuove scale ad un layer SCALE gia' esistente
        result_init = self.inizializza_layer()
        if (result_init==0):
            return 0        
        # show the dialog
        self.dlg_append.show()
        # Run the dialog event loop
        result = self.dlg_append.exec_()
        self.dlg_append.txtFeedback.clear()
        
    def select_shp_scala_append(self):
        filename = QFileDialog.getOpenFileName(self.dlg_append, "Append SCALA layer","", '*.shp')
        self.dlg_append.shpBrowse_txt.setText(filename)
        #Verifico di avere tutte le informazioni necessarie per decidere se abilitare o meno il pulsante IMPORT
        filename_check = self.dlg_append.shpBrowse_txt.text()
        if (filename_check):
            self.dlg_append.importBtn.setEnabled(True);
        else:
            self.dlg_append.importBtn.setEnabled(False);
    
    def append_scala_DbManager(self):
        #in questo caso do per assodato che le nuove SCALE siano gia state caricate su DB con DbManager in una tabella chiamata come LAYER_NAME['SCALA_append'], questo perche' la funzione append_scala da certi PC resttuisce un errore
        Utils.logMessage('APPEND: inizio...')
        msg = QMessageBox()
        #recupero le info di connex al DB da un qualunque dei layer:
        connInfo = SCALE_layer.source()
        dest_dir = self.estrai_param_connessione(connInfo)
        global epsg_srid
        schemaDB = theSchema
        test_conn = None
        try:
            self.dlg_append.txtFeedback.setText("Sto importando i dati...")            
            #apro il cursore per leggere/scrivere sul DB:
            test_conn = psycopg2.connect(dest_dir)
            cur = test_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            #recupero alcune variabili dal progetto:
            query_var = """SELECT cod_belf, lotto, srid FROM %s.variabili_progetto_return LIMIT 1;""" % (schemaDB)
            cur.execute(query_var)
            results_var = cur.fetchone()
            epsg_srid_var = results_var['srid']
            comuneDB = results_var['cod_belf']
            codice_lotto = results_var['lotto']
            
            #CONTROLLO SRID e GEOMETRIA:
            query_check = """SELECT st_srid(a.geom) AS srid, st_geometrytype(a.geom) AS wkb_new, st_geometrytype(b.geom) AS wkb_dest FROM %s.%s a, %s.scala b LIMIT 1;""" % (schemaDB, self.LAYER_NAME['SCALA_append'], schemaDB)
            cur.execute(query_check)
            results_check = cur.fetchone()
            epsg_srid = results_check['srid']
            new_point_type = results_check['wkb_new']
            dest_point_type = results_check['wkb_dest']
            
            if (epsg_srid_var != epsg_srid):
                msg.setText("Gli SRID delle scale non corrispondono, impossibile proseguire.")
                msg.setDetailedText('srid SCALE di riferimento=' + str(epsg_srid_var) + '; srid NUOVE scale=' + str(epsg_srid))
                msg.setIcon(QMessageBox.Critical)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setWindowTitle("Errore nell'importazione!")
                retval = msg.exec_()
                return 0
            
            if (dest_point_type != new_point_type):
                msg.setText("Le GEOMETRIE delle scale non corrispondono, impossibile proseguire.")
                if (dest_point_type=='ST_Point'):
                    msg.setDetailedText('Geometria SCALE di riferimento=' + str(dest_point_type) + '; geometria NUOVE scale=' + str(new_point_type) + '\nPer poter continuare, importare nuovamente le nuove scale tramite DBManager scegliendo la opzione "Crea geometrie a parti singole invece che multiple"')
                if (dest_point_type=='ST_MultiPoint'):
                    msg.setDetailedText('Geometria SCALE di riferimento=' + str(dest_point_type) + '; geometria NUOVE scale=' + str(new_point_type) + '\nPer poter continuare, importare nuovamente le nuove scale tramite DBManager senza scegliere la opzione "Crea geometrie a parti singole invece che multiple"')
                msg.setIcon(QMessageBox.Critical)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setWindowTitle("Errore nell'importazione!")
                retval = msg.exec_()
                return 0
            
            #Modifico eventualmente il nome di alcuni campi, o ne aggiungo, richiamando una funzione:
            cur.execute("SELECT public.s_alter_scala_fn('%s', %i, '%s');" % (schemaDB, epsg_srid, self.LAYER_NAME['SCALA_append']))
            test_conn.commit()
            
            #prima di aggiungere queste scale alla tabella finale, controllo non vi siano geometrie duplicate:
            query_doppioni = "SELECT count(*) AS cnt FROM %s.%s a, %s.scala b WHERE ST_Equals(a.geom, b.geom);" % (schemaDB, self.LAYER_NAME['SCALA_append'], schemaDB)
            cur.execute(query_doppioni)
            results_doppioni = cur.fetchone()
            cnt_doppioni = results_doppioni['cnt']
            if (cnt_doppioni>0):
                msg.setText( "Sono state trovate nello shp da importare %s geometrie duplicate con il layer di destinazione. Si desidera continuare comunque?" % (str(cnt_doppioni)) )
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Geometrie duplicate: continuare?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                retval = msg.exec_()
                if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                    self.dlg_append.txtFeedback.setText("Trovate geometrie duplicate. L'utente ha scelto di fermarsi.")
                    return 0
            #l'utente HA CLICCATO YES, continuo
            
            #ulteriore controllo sulle n_ui: il campo e' pieno di NULL?
            query_nulli = "SELECT count(*) AS totale, count(CASE WHEN n_ui IS NULL THEN 1 END) AS nulli FROM %s.%s;" % (schemaDB, self.LAYER_NAME['SCALA_append'])
            cur.execute(query_nulli)
            results_nulli = cur.fetchone()
            scale_totali = results_nulli['totale']
            scale_nulle = results_nulli['nulli']
            if (scale_nulle>0):
                msg.setText( "Sono state trovate nello shp da importare %s oggetti con n_ui NULLO su un totale di %s oggetti. Si desidera continuare comunque?" % ( str(scale_nulle), str(scale_totali) ) )
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Campo n_ui con valori nulli: continuare?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                retval = msg.exec_()
                if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                    self.dlg_append.txtFeedback.setText("Trovati oggetti con n_ui NULLO. L'utente ha scelto di fermarsi.")
                    return 0
            
            #a questo punto dovrei essere pronto per unire queste scale a quelle precedenti:
            query_append = """INSERT INTO %s.scala
            (geom, id_scala, id_pop, id_pfp, id_pfs, id_pd, id_giunto, particella, codice_via, nord, est, cod_cft, enabled, tipo, naming_of, id_sc_ref, n_ui, n_ui_originali, comune, provincia, frazione, indirizzo, id_buildin, regione, civico, ebw_propri, ebw_stato_, ebw_note)
            SELECT
            geom, id_scala, id_pop, id_pfp, id_pfs, id_pd, id_giunto, particella, codice_via, nord, est, cod_cft, enabled, tipo, naming_of, id_sc_ref, n_ui, n_ui_originali, comune, provincia, frazione, indirizzo, id_buildin, regione, civico, ebw_propri, ebw_stato_, ebw_note
            FROM %s.%s;""" % (schemaDB, schemaDB, self.LAYER_NAME['SCALA_append'])
            cur.execute(query_append)
            test_conn.commit()
            
            #Da mail di Gatti del 25/08/2017: risulta che caricando lo SHP delle SCALE non sempre il gid e' calcolato. Lo ricalcolo a prescindere per tutte le scale:
            query_id_scala = "UPDATE %s.scala SET id_scala = '%s'||'%s'||lpad(gid::text, 5, '0') WHERE id_scala IS NULL;" % (schemaDB, comuneDB, codice_lotto)
            Utils.logMessage('query creazione id scala = ' + str(query_id_scala));
            cur.execute(query_id_scala)
            test_conn.commit()
            
            cur.close()
        
        except psycopg2.Error, e:
            Utils.logMessage(e.pgerror)
            self.dlg_append.txtFeedback.setText("Errore su DB, vedere il log o contattare l'amministratore")
            msg.setText(e.pgerror)
            msg.setDetailedText("Se l'errore riguarda la violazione della chiave primaria sul campo gid, controllare che sulla tavola di destinazione tale campo e la sequence ad esso corrispondente non siano stati in qualche modo compromessi ovvero modificati manualmente perdendo dunque consistenza.")
            msg.setIcon(QMessageBox.Critical)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setWindowTitle("Errore nell'importazione!")
            retval = msg.exec_()                
            test_conn.rollback()
            return 0
        except SystemError, e:
            Utils.logMessage('Errore di sistema!')
            self.dlg_append.txtFeedback.setText('Errore di sistema!')
            msg.setText("Errore di sistema!")
            msg.setIcon(QMessageBox.Critical)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setWindowTitle("Errore nell'importazione!")
            retval = msg.exec_()    
            test_conn.rollback()
            return 0
        else:
            self.dlg_append.txtFeedback.setText("Scale appese con successo!")
            msg.setText("Scale appese con successo!")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setWindowTitle("Scale appese con successo!")
            retval = msg.exec_()
        finally:
            if test_conn is not None:
                test_conn.close()
        
    def append_scala(self):
        Utils.logMessage('APPEND: inizio...')
        msg = QMessageBox()
        #recupero le info di connex al DB da un qualunque dei layer:
        connInfo = SCALE_layer.source()
        dest_dir = self.estrai_param_connessione(connInfo)
        
        global epsg_srid
        schemaDB = theSchema
        try:
            scala_shp = self.dlg_append.shpBrowse_txt.text()
            if ( (scala_shp is None) or (scala_shp=='') ):
                raise NameError('Specificare correttamente il nome dello shp e il percorso di origine!')
        except NameError as err:
            msg.setText(err.args[0])
            msg.setIcon(QMessageBox.Critical)
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            self.dlg_append.txtFeedback.setText(err.args[0])
            return 0
        except ValueError:
            self.dlg_append.txtFeedback.setText('Specificare TUTTE le variabili')
            return 0
        except SystemError, e:
            Utils.logMessage('Errore di sistema!')
            self.dlg_append.txtFeedback.setText('Errore di sistema!')
            return 0
        
        else: #...se tutto ok proseguo:
            msg.setText("ATTENZIONE! Con questa azione aggiungerai le scale scelte da shapefile a quelle gia' presenti sul DB nel layer SCALA: proseguire?")
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Aggiungere altre SCALE sul DB?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            retval = msg.exec_()
            if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                return 0
            #l'utente HA CLICCATO YES, continuo:
            layer_scala = QgsVectorLayer(scala_shp, self.LAYER_NAME['SCALA_append'], "ogr")
            #lista_layer_to_load=[layer_scala]
            #problema: il layer deve venir caricato sulla TOC per esser importato sul DB:
            QgsMapLayerRegistry.instance().addMapLayer(layer_scala)
            self.iface.legendInterface().setLayerVisible(layer_scala, False)
            #Li spengo di default e li importo direttamente sul DB:
            crs = None
            test_conn = None
            options = {}
            options['lowercaseFieldNames'] = True
            options['overwrite'] = True
            #options['forceSinglePartGeometryType'] = True
            try:
                self.dlg_append.txtFeedback.setText("Sto importando i dati...")
                
                #apro il cursore per leggere/scrivere sul DB:
                test_conn = psycopg2.connect(dest_dir)
                #cur = test_conn.cursor()
                cur = test_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                
                '''#ripulisco il DB se esiste gia' una tabella scala_append
                query_rem = "DROP TABLE IF EXISTS %s.%s;" % (schemaDB, self.LAYER_NAME['SCALA_append'])
                cur.execute(query_rem)
                test_conn.commit()'''
                
                #recupero alcune variabili dal progetto:
                query_var = """SELECT cod_belf, lotto, srid FROM %s.variabili_progetto_return LIMIT 1;""" % (schemaDB)
                cur.execute(query_var)
                results_var = cur.fetchone()
                epsg_srid_var = results_var['srid']
                comuneDB = results_var['cod_belf']
                codice_lotto = results_var['lotto']

                #layer_loaded = layer_scala
                layer_loaded_geom = layer_scala.wkbType()
                uri = None
                #la chiave gid potrebbe non esserci. La aggiungo gia' allo shp, ma primo controllo non vi sia gia':
                field_names = [field.name() for field in layer_scala.pendingFields() ]
                gid_esistente = 'gid' in field_names
                Utils.logMessage(str(field_names))
                
                if (gid_esistente):
                    Utils.logMessage("campo gid su shp gia' esistente, continuo")
                else:
                    Utils.logMessage("campo gid su shp non esistente: lo creo")
                    res = layer_scala.dataProvider().addAttributes([QgsField("gid", QVariant.Int)])
                    layer_scala.updateFields()
                    idx = layer_scala.dataProvider().fieldNameIndex( "gid" )
                    n=1
                    for pt in layer_scala.getFeatures():
                        layer_scala.changeAttributeValue(pt.id(), idx, n)
                        n+=1
                
                uri = "%s key=gid table=\"%s\".\"%s\" (geom) sql=" % (dest_dir, schemaDB, layer_scala.name().lower())
                Utils.logMessage('WKB: ' + str(layer_loaded_geom)+ '; DEST_DIR: ' + str(dest_dir))
                crs = layer_scala.crs()
                
                epsg_srid = int(crs.postgisSrid())
                
                #CONTROLLO SRID:
                if (epsg_srid_var != epsg_srid):
                    msg.setText("Gli SRID delle scale non corrispondono, impossibile proseguire.")
                    msg.setDetailedText('srid SCALE gia sul DB=' + str(epsg_srid_var) + '; srid NUOVE scale=' + str(epsg_srid))
                    msg.setIcon(QMessageBox.Critical)
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.setWindowTitle("Errore nell'importazione!")
                    retval = msg.exec_()
                    return 0
                
                #Dovrei fare un altro controllo, cioe' il tipo di geometria delle SCALE di destinazione, in modo da evitare un fastidioso errore di MultiPoint-Point:
                query_point = "SELECT DISTINCT ST_GeometryType(geom) AS geomtype FROM %s.scala;" % (schemaDB)
                cur.execute(query_point)
                results_point = cur.fetchone()
                dest_point_type = results_point['geomtype']
                if (dest_point_type=='ST_Point'):
                    options['forceSinglePartGeometryType'] = True
                
                #import shp su DB:
                error = QgsVectorLayerImport.importLayer(layer_scala, uri, "postgres", crs, False, False, options)
                #TypeError: QgsVectorLayerImport.importLayer(QgsVectorLayer, QString uri, QString providerKey, QgsCoordinateReferenceSystem destCRS, bool onlySelected=False, bool skipAttributeCreation=False, dict-of-QString-QVariant options=None, QProgressDialog progress=None)
                if error[0] != 0:
                    iface.messageBar().pushMessage(u'Error', error[1], QgsMessageBar.CRITICAL, 5)
                    msg.setText("Errore nell'importazione. Vedere il dettaglio dell'errore, contattare l'amministratore")
                    msg.setDetailedText(error[1])
                    msg.setIcon(QMessageBox.Critical)
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.setWindowTitle("Errore nell'importazione!")
                    retval = msg.exec_()
                    self.dlg_append.txtFeedback.setText(error[1])
                    return 0
                #...shp importato con successo sul DB...
                
                #Modifico eventualmente il nome di alcuni campi, o ne aggiungo, richiamando una funzione:
                cur.execute("SELECT public.s_alter_scala_fn('%s', %i, '%s');" % (schemaDB, epsg_srid, self.LAYER_NAME['SCALA_append']))
                test_conn.commit()
                
                #prima di aggiungere queste scale alla tabella finale, controllo non vi siano geometrie duplicate:
                query_doppioni = "SELECT count(*) AS cnt FROM %s.%s a, %s.scala b WHERE ST_Equals(a.geom, b.geom);" % (schemaDB, self.LAYER_NAME['SCALA_append'], schemaDB)
                cur.execute(query_doppioni)
                results_doppioni = cur.fetchone()
                cnt_doppioni = results_doppioni['cnt']
                if (cnt_doppioni>0):
                    msg.setText( "Sono state trovate nello shp da importare %s geometrie duplicate con il layer di destinazione. Si desidera continuare comunque?" % (str(cnt_doppioni)) )
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Geometrie duplicate: continuare?")
                    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    retval = msg.exec_()
                    if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                        self.dlg_append.txtFeedback.setText("Trovate geometrie duplicate. L'utente ha scelto di fermarsi.")
                        return 0
                #l'utente HA CLICCATO YES, continuo
                
                #ulteriore controllo sulle n_ui: il campo e' pieno di NULL?
                query_nulli = "SELECT count(*) AS totale, count(CASE WHEN n_ui IS NULL THEN 1 END) AS nulli FROM %s.%s;" % (schemaDB, self.LAYER_NAME['SCALA_append'])
                cur.execute(query_nulli)
                results_nulli = cur.fetchone()
                scale_totali = results_nulli['totale']
                scale_nulle = results_nulli['nulli']
                if (scale_nulle>0):
                    msg.setText( "Sono state trovate nello shp da importare %s oggetti con n_ui NULLO su un totale di %s oggetti. Si desidera continuare comunque?" % ( str(scale_nulle), str(scale_totali) ) )
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Campo n_ui con valori nulli: continuare?")
                    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    retval = msg.exec_()
                    if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
                        self.dlg_append.txtFeedback.setText("Trovati oggetti con n_ui NULLO. L'utente ha scelto di fermarsi.")
                        return 0
                
                #a questo punto dovrei essere pronto per unire queste scale a quelle precedenti:
                '''query_append = """INSERT INTO %s.scala
                (geom, n_ui, n_ui_originali)
                SELECT geom, n_ui, n_ui_originali
                FROM %s.%s;""" % (schemaDB, schemaDB, self.LAYER_NAME['SCALA_append'])'''
                #se voglio riportarmi dietro piu' campi possibile:
                query_append = """INSERT INTO %s.scala
                (geom, id_scala, id_pop, id_pfp, id_pfs, id_pd, id_giunto, particella, codice_via, nord, est, cod_cft, enabled, tipo, naming_of, id_sc_ref, n_ui, n_ui_originali, comune, provincia, frazione, indirizzo, id_buildin, regione, civico, ebw_propri, ebw_stato_, ebw_note)
                SELECT
                geom, id_scala, id_pop, id_pfp, id_pfs, id_pd, id_giunto, particella, codice_via, nord, est, cod_cft, enabled, tipo, naming_of, id_sc_ref, n_ui, n_ui_originali, comune, provincia, frazione, indirizzo, id_buildin, regione, civico, ebw_propri, ebw_stato_, ebw_note
                FROM %s.%s;""" % (schemaDB, schemaDB, self.LAYER_NAME['SCALA_append'])
                cur.execute(query_append)
                test_conn.commit()
                
                #Da mail di Gatti del 25/08/2017: risulta che caricando lo SHP delle SCALE non sempre il gid e' calcolato. Lo ricalcolo a prescindere per tutte le scale:
                query_id_scala = "UPDATE %s.scala SET id_scala = '%s'||'%s'||lpad(gid::text, 5, '0') WHERE id_scala IS NULL;" % (schemaDB, comuneDB, codice_lotto)
                Utils.logMessage('query creazione id scala = ' + str(query_id_scala));
                cur.execute(query_id_scala)
                test_conn.commit()
                
                #elimino la tabella:
                '''query_rem = "DROP TABLE IF EXISTS %s.%s;" % (schemaDB, self.LAYER_NAME['SCALA_append'])
                cur.execute(query_rem)
                test_conn.commit()'''
                
                cur.close()
                #test_conn.close()
            
            except psycopg2.Error, e:
                Utils.logMessage(e.pgerror)
                self.dlg_append.txtFeedback.setText("Errore su DB, vedere il log o contattare l'amministratore")
                msg.setText(e.pgerror)
                msg.setDetailedText("Se l'errore riguarda la violazione della chiave primaria sul campo gid, controllare che sulla tavola di destinazione tale campo e la sequence ad esso corrispondente non siano stati in qualche modo compromessi ovvero modificati manualmente perdendo dunque consistenza.")
                msg.setIcon(QMessageBox.Critical)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setWindowTitle("Errore nell'importazione!")
                retval = msg.exec_()                
                test_conn.rollback()
                return 0
            except SystemError, e:
                Utils.logMessage('Errore di sistema!')
                self.dlg_append.txtFeedback.setText('Errore di sistema!')
                msg.setText("Errore di sistema!")
                msg.setIcon(QMessageBox.Critical)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setWindowTitle("Errore nell'importazione!")
                retval = msg.exec_()    
                test_conn.rollback()
                return 0
            else:
                self.dlg_append.txtFeedback.setText("Scale appese con successo!")
                msg.setText("Scale appese con successo!")
                msg.setIcon(QMessageBox.Information)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setWindowTitle("Scale appese con successo!")
                retval = msg.exec_()
            finally:
                #tolgo il layer dalla TOC:
                QgsMapLayerRegistry.instance().removeMapLayer(layer_scala.id())
                if test_conn is not None:
                    test_conn.close()
        
    
    def run_updatedb(self):
        result_init = self.inizializza_layer()
        if (result_init==0):
            return 0
        msg = QMessageBox()
        #recupero le info di connex al DB da un qualunque dei layer:
        connInfo = SCALE_layer.source()
        db_dir = self.estrai_param_connessione(connInfo)
        #apro il cursore per leggere/scrivere sul DB:
        conn_updatedb = psycopg2.connect(db_dir)
        cur_updatedb = conn_updatedb.cursor()
        Utils.logMessage('UPDATEDB: inizio la procedura')
        try:
            sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_funzione_scodificacable.sql'
            cur_updatedb.execute(open(sql_file, "r").read())
            conn_updatedb.commit()
            #In questo caso lancio la funzione per creare la tabella di decodifica:
            query_codifica_cable = "SELECT public.s_codifica_cable('%s', %i);" % (theSchema, self.epsg_srid)
            cur_updatedb.execute(query_codifica_cable)
            conn_updatedb.commit()
            
            sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_funzione_scalcable.sql'
            cur_updatedb.execute(open(sql_file, "r").read())
            conn_updatedb.commit()
            
            sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_funzione_splitlines.sql'
            cur_updatedb.execute(open(sql_file, "r").read())
            conn_updatedb.commit()
            
            sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_funzione_salterscala.sql'
            cur_updatedb.execute(open(sql_file, "r").read())
            conn_updatedb.commit()
            
            sql_file = os.getenv("HOME") + '/.qgis2/python/plugins/ProgettoFTTH_return/creazione_funzione_saltertable.sql'
            cur_updatedb.execute(open(sql_file, "r").read())
            conn_updatedb.commit()
            
        except psycopg2.Error, e:
            Utils.logMessage("Errore UPDATEDB: " + e.pgerror)
            conn_updatedb.rollback()
            msg.setText("Errore UPDATEDB: " + e.pgerror)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Errore!")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            return 0
        except SystemError, e:
            Utils.logMessage("Errore UPDATEDB. Contattare l'amministratore." + str(e))
            conn_updatedb.rollback()
            msg.setText("Errore UPDATEDB. Contattare l'amministratore. " + str(e))
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Errore!")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            return 0
        else:
            Utils.logMessage('UPDATEDB: fine della procedura con successo')
            msg.setText("UPDATEDB: effettuato con successo!")
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("UPDATEDB: effettuato con successo!")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            return 1
        finally:
            if conn_updatedb:
                conn_updatedb.close()
    
    def run_calcable(self):
        result_init = self.inizializza_layer()
        if (result_init==0):
            return 0
        msg = QMessageBox()
        #recupero le info di connex al DB da un qualunque dei layer:
        connInfo = SCALE_layer.source()
        db_dir = self.estrai_param_connessione(connInfo)
        #apro il cursore per leggere/scrivere sul DB:
        conn_calcable = psycopg2.connect(db_dir)
        cur_calcable = conn_calcable.cursor()
        Utils.logMessage('CALCABLE: inizio la procedura')
        try:
            #se invece le funzioni le vogliamo creare sotto public rendendole cosi' uguali per tutto un DB:
            query_calcable = "SELECT public.s_calc_cable('%s', %i);" % (theSchema, self.epsg_srid)
            #Utils.logMessage("query topo: " + query_calcable)
            cur_calcable.execute(query_calcable)
            conn_calcable.commit()
        
        except psycopg2.Error, e:
            Utils.logMessage("Errore CALCABLE: " + e.pgerror)
            conn_calcable.rollback()
            msg.setText("Errore CALCABLE: " + e.pgerror)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Errore!")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            return 0
        except SystemError, e:
            Utils.logMessage("Errore CALCABLE. Contattare l'amministratore." + str(e))
            conn_calcable.rollback()
            msg.setText("Errore CALCABLE. Contattare l'amministratore. " + str(e))
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Errore!")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            return 0
        else:
            Utils.logMessage('CALCABLE: fine della procedura con successo')
            msg.setText("CALCABLE: effettuato con successo!")
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("CALCABLE: effettuato con successo!")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            return 1
        finally:
            if conn_calcable:
                conn_calcable.close()
        
    
    def run_cutcable(self):
        result_init = self.inizializza_layer()
        if (result_init==0):
            return 0
        #recupero le info di connex al DB da un qualunque dei layer:
        connInfo = SCALE_layer.source()
        db_dir = self.estrai_param_connessione(connInfo)
        
        msg = QMessageBox()
        msg.setText("ATTENZIONE! Con questa azione spezzerai il layer cavo creando nuove geometrie laddove i nodi di una linea si sovrappongono ad i nodi di un'altra linea. Questo significa che se il routing e' gia' stato eseguito, occorrera' ricalcolarlo. Il progetto che verra' modificato sara': %s, schema: %s. Desideri davvero proseguire?" % (str(db_dir), theSchema))
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Correggere lo schema cavo?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        if (retval != 16384): #l'utente NON ha cliccato yes: sceglie di fermarsi, esco
            return 0
        elif (retval == 16384): #l'utente HA CLICCATO YES.
            #a questo punto lancio delle query che analizzano il layer cavo e lo spezzano dove i nodi di una linea intersecano i nodi di un'altra linea:
            #apro il cursore per leggere/scrivere sul DB:
            conn_cutcable = psycopg2.connect(db_dir)
            cur_cutcable = conn_cutcable.cursor()
            Utils.logMessage('CUTCABLE: inizio la procedura')

            #provare per eseguire funzioni:
            #http://www.postgresqltutorial.com/postgresql-python/call-stored-procedures/
            try:
                #query_topo = "SELECT %s.split_lines_to_lines_pulizia('%s', %i); SELECT %s.split_lines_to_lines_topo('%s', %i); SELECT %s.split_lines_to_lines_conclusivo('%s', %i);" % (theSchema, theSchema, self.epsg_srid, theSchema, theSchema, self.epsg_srid, theSchema, theSchema, self.epsg_srid)
                #se invece le funzioni le vogliamo creare sotto public rendendole cosi' uguali per tutto un DB:
                query_topo = "SELECT public.split_lines_to_lines_pulizia('%s', %i); SELECT public.split_lines_to_lines_topo('%s', %i); SELECT public.split_lines_to_lines_conclusivo('%s', %i);" % (theSchema, self.epsg_srid, theSchema, self.epsg_srid, theSchema, self.epsg_srid)
                #Utils.logMessage("query topo: " + query_topo)
                cur_cutcable.execute(query_topo)
                conn_cutcable.commit()
                '''query_topo = "SELECT %s.split_lines_to_lines_topo('%s', %i);" % (theSchema, theSchema, self.epsg_srid)
                cur_cutcable.execute(query_topo)
                query_conclusiva = "SELECT %s.split_lines_to_lines_conclusivo('%s', %i);" % (theSchema, theSchema, self.epsg_srid)
                cur_cutcable.execute(query_conclusiva)'''
            
            except psycopg2.Error, e:
                Utils.logMessage("Errore CUTCABLE: " + e.pgerror)
                conn_cutcable.rollback()
                msg.setText("Errore CUTCABLE: " + e.pgerror)
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Errore!")
                msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec_()
                return 0
            except SystemError, e:
                Utils.logMessage("Errore CUTCABLE. Contattare l'amministratore." + str(e))
                conn_cutcable.rollback()
                msg.setText("Errore pulizia CUTCABLE. Contattare l'amministratore. " + str(e))
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Errore!")
                msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec_()
                return 0
            else:
                Utils.logMessage('CUTCABLE: fine della procedura con successo')
                msg.setText("CUTCABLE: effettuato con successo! Potete procedere con il routing")
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("CUTCABLE: effettuato con successo!")
                msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec_()
                return 1
            finally:
                if conn_cutcable:
                    conn_cutcable.close()
            
    
    def run_help(self):
        #Prelevo il numero di versione dal file metadata.txt:
        nome_file = os.getenv("HOME")+'/.qgis2/python/plugins/ProgettoFTTH_return/metadata.txt'
        searchfile = open(nome_file, "r")
        for line in searchfile:
            if "version=" in line:
                version = str(line[8:13])
                #Utils.logMessage(str(line[8:]))
            if "release_date=" in line:
                release_date = str(line[13:23])
        searchfile.close()
        self.dlg_help.label_version.clear()
        self.dlg_help.label_version.setText("Versione: " + version + " - " + release_date)
        # show the dialog
        self.dlg_help.show()
        # Run the dialog event loop
        result = self.dlg_help.exec_()
    
    def run_cavoroute(self):
        #Prima di tutto se il CAVO e' gia' stato inizializzato disattivo il pulsante:
        result_init = self.inizializza_layer()
        if (result_init==0):
            return 0
        #theSchema = self.dlg_config.schemaDB.text()
        connInfo = SCALE_layer.source()
        db_dir = self.estrai_param_connessione(connInfo)
        test_conn = None
        global FROM_TO_RULES
        global FIBRE_CAVO
        global epsg_srid
        #global COD_POP
        #recupero le info di connex al DB da un qualunque dei layer:
        connInfo = SCALE_layer.source()
        dest_dir = self.estrai_param_connessione(connInfo)
        #A questo punto mi connetto al DB per recuperare le variabili di progetto:
        try:
            test_conn = psycopg2.connect(dest_dir)
            #cur_var = test_conn.cursor()
            dict_cur = test_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            query_var = """SELECT pta_ui_min, pta_ui_max, pta_cont_max, giunto_ui_min, giunto_ui_max, giunto_cont_max, pd_ui_min, pd_ui_max, pd_cont_max, pfs_ui_min, pfs_ui_max, pfs_pd_max, pfp_ui_min, pfp_ui_max, pfp_pfs_max, srid FROM %s.variabili_progetto_return LIMIT 1;""" % (theSchema)
            dict_cur.execute(query_var)
            results_var = dict_cur.fetchone()
            epsg_srid = results_var['srid']
            self.epsg_srid = epsg_srid
            #Recupero la variabile COD_POP:
            #COD_POP = results_var[12]
            Utils.logMessage(str(results_var['pta_ui_max']))
            #Ricostruisco il dict con le variabili:
            FROM_TO_RULES = {
                'PTA': {'MIN_UI': results_var['pta_ui_min'], 'MAX_UI': results_var['pta_ui_max'], 'MAX_CONT': results_var['pta_cont_max']},
                'GIUNTO': {'MIN_UI': results_var['giunto_ui_min'], 'MAX_UI': results_var['giunto_ui_max'], 'MAX_CONT': results_var['giunto_cont_max']},
                'GIUNTO_F_dev': {'MIN_UI': results_var['giunto_ui_min'], 'MAX_UI': results_var['giunto_ui_max'], 'MAX_CONT': results_var['giunto_cont_max']},
                'PD': {'MIN_UI': results_var['pd_ui_min'], 'MAX_UI': results_var['pd_ui_max'], 'MAX_CONT': results_var['pd_cont_max']},
                'PFS': {'MIN_UI': results_var['pfs_ui_min'], 'MAX_UI': results_var['pfs_ui_max'], 'MAX_CONT': results_var['pfs_pd_max']},
                'PFP': {'MIN_UI': results_var['pfp_ui_min'], 'MAX_UI': results_var['pfp_ui_max'], 'MAX_CONT': results_var['pfp_pfs_max']}
            }
            FROM_TO_RULES['SCALA'] = FROM_TO_RULES['PTA']
            
            #Mentre ci sono mi scarico anche le variabili di connessione delle fibre:
            query_fibre = """ SELECT scala_pta_f4, scala_pta_f12, scala_pta_f24, scala_pta_f48, scala_pta_f72, scala_pta_f96, scala_pta_f144, scala_pta_f192, scala_giunto_f4 , scala_giunto_f12, scala_giunto_f24, scala_giunto_f48, scala_giunto_f72, scala_giunto_f96, scala_giunto_f144, scala_giunto_f192, scala_pd_f4, scala_pd_f12, scala_pd_f24, scala_pd_f48, scala_pd_f72, scala_pd_f96, scala_pd_f144, scala_pd_f192, scala_pfs_f4, scala_pfs_f12, scala_pfs_f24, scala_pfs_f48, scala_pfs_f72, scala_pfs_f96, scala_pfs_f144, scala_pfs_f192, giunto_pd_f4, giunto_pd_f12, giunto_pd_f24, giunto_pd_f48, giunto_pd_f72, giunto_pd_f96, giunto_pd_f144, giunto_pd_f192, pta_pd_f4, pta_pd_f12, pta_pd_f24, pta_pd_f48, pta_pd_f72, pta_pd_f96, pta_pd_f144, pta_pd_f192, pd_pfs_f4, pd_pfs_f12, pd_pfs_f24, pd_pfs_f48, pd_pfs_f72, pd_pfs_f96, pd_pfs_f144, pd_pfs_f192, pfs_pfp_f96 FROM %s.variabili_progetto_return LIMIT 1; """ % (theSchema)
            dict_cur.execute(query_fibre)
            results_fibre = dict_cur.fetchone()
            '''FIBRE_CAVO = {
                'PD': {'F_4': results_fibre[0], 'F_12': results_fibre[1], 'F_24': results_fibre[2], 'F_48': results_fibre[3], 'F_72': results_fibre[4], 'F_96': results_fibre[5], 'F_144': results_fibre[6]},
                'PFS': {'F_4': results_fibre[7], 'F_12': results_fibre[8], 'F_24': results_fibre[9], 'F_48': results_fibre[10], 'F_72': results_fibre[11], 'F_96': results_fibre[12], 'F_144': results_fibre[13]}
            }'''
            #FIBRA CAVO CAMBIA COMPLETAMENTE RISPETTO A PRIMA!!! Dovrei valorizzare TUTTI i CAMPI delle FIBRE!
            FIBRE_CAVO = {
                'SCALA_PTA': {'F_4': results_fibre['scala_pta_f4'], 'F_12': results_fibre['scala_pta_f12'], 'F_24': results_fibre['scala_pta_f24'], 'F_48': results_fibre['scala_pta_f48'], 'F_72': results_fibre['scala_pta_f72'], 'F_96': results_fibre['scala_pta_f96'], 'F_144': results_fibre['scala_pta_f144'], 'F_192': results_fibre['scala_pta_f192']},
                'SCALA_GIUNTO': {'F_4': results_fibre['scala_giunto_f4'], 'F_12': results_fibre['scala_giunto_f12'], 'F_24': results_fibre['scala_giunto_f24'], 'F_48': results_fibre['scala_giunto_f48'], 'F_72': results_fibre['scala_giunto_f72'], 'F_96': results_fibre['scala_giunto_f96'], 'F_144': results_fibre['scala_giunto_f144'], 'F_192': results_fibre['scala_giunto_f192']},
                'SCALA_PD': {'F_4': results_fibre['scala_pd_f4'], 'F_12': results_fibre['scala_pd_f12'], 'F_24': results_fibre['scala_pd_f24'], 'F_48': results_fibre['scala_pd_f48'], 'F_72': results_fibre['scala_pd_f72'], 'F_96': results_fibre['scala_pd_f96'], 'F_144': results_fibre['scala_pd_f144'], 'F_192': results_fibre['scala_pd_f192']},
                'SCALA_PFS': {'F_4': results_fibre['scala_pfs_f4'], 'F_12': results_fibre['scala_pfs_f12'], 'F_24': results_fibre['scala_pfs_f24'], 'F_48': results_fibre['scala_pfs_f48'], 'F_72': results_fibre['scala_pfs_f72'], 'F_96': results_fibre['scala_pfs_f96'], 'F_144': results_fibre['scala_pfs_f144'], 'F_192': results_fibre['scala_pfs_f192']},
                'GIUNTO_PD': {'F_4': results_fibre['giunto_pd_f4'], 'F_12': results_fibre['giunto_pd_f12'], 'F_24': results_fibre['giunto_pd_f24'], 'F_48': results_fibre['giunto_pd_f48'], 'F_72': results_fibre['giunto_pd_f72'], 'F_96': results_fibre['giunto_pd_f96'], 'F_144': results_fibre['giunto_pd_f144'], 'F_192': results_fibre['giunto_pd_f192']},
                'PTA_PD': {'F_4': results_fibre['pta_pd_f4'], 'F_12': results_fibre['pta_pd_f12'], 'F_24': results_fibre['pta_pd_f24'], 'F_48': results_fibre['pta_pd_f48'], 'F_72': results_fibre['pta_pd_f72'], 'F_96': results_fibre['pta_pd_f96'], 'F_144': results_fibre['pta_pd_f144'], 'F_192': results_fibre['pta_pd_f192']},
                'PD_PFS': {'F_4': results_fibre['pd_pfs_f4'], 'F_12': results_fibre['pd_pfs_f12'], 'F_24': results_fibre['pd_pfs_f24'], 'F_48': results_fibre['pd_pfs_f48'], 'F_72': results_fibre['pd_pfs_f72'], 'F_96': results_fibre['pd_pfs_f96'], 'F_144': results_fibre['pd_pfs_f144'], 'F_192': results_fibre['pd_pfs_f192']},
                'PFS_PFP': {'F_96': results_fibre['pfs_pfp_f96']}
            }
            #Per non riscrivere il dictionary eseguo questa uguaglianza:
            FIBRE_CAVO['GIUNTO_GIUNTO'] = FIBRE_CAVO['GIUNTO_PD']
            FIBRE_CAVO['PTA_GIUNTO'] = FIBRE_CAVO['GIUNTO_PD']
            FIBRE_CAVO['PTA_PTA'] = FIBRE_CAVO['GIUNTO_PD']
            FIBRE_CAVO['PTA_PFS'] = FIBRE_CAVO['PTA_PD']
            FIBRE_CAVO['SCALA_SCALA'] = FIBRE_CAVO['SCALA_PTA']
            FIBRE_CAVO['PD_PD'] = FIBRE_CAVO['GIUNTO_PD']
            #Utils.logMessage(str(FIBRE_CAVO['PFS_PFP']['F_96']))
            
            #Utils.logMessage(str(FROM_TO_RULES['GIUNTO']))        
            dict_cur.close()
        except psycopg2.Error, e:
            Utils.logMessage(e.pgerror)
            FROM_TO_RULES = self.FROM_TO_RULES
            FIBRE_CAVO = self.FIBRE_CAVO
            #COD_POP = self.COD_POP
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Non sono riuscito a scaricare correttamente dal DB le variabili del progetto in uso. Carico quelle di default')
            return 0
        except SystemError, e:
            Utils.logMessage('Errore di sistema!')
            FROM_TO_RULES = self.FROM_TO_RULES
            FIBRE_CAVO = self.FIBRE_CAVO
            #COD_POP = self.COD_POP
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Non sono riuscito a scaricare correttamente dal DB le variabili del progetto in uso. Carico quelle di default')
            return 0
        else:
            self.FROM_TO_RULES = FROM_TO_RULES
            self.FIBRE_CAVO = FIBRE_CAVO
            #self.COD_POP = COD_POP
            Utils.logMessage('Variabili del progetto importate con successo!')
            #return 1
        finally:
            if test_conn:
                test_conn.close()
                
        result = db_solid.inizializza_gui(self, connInfo, theSchema)
        #Apro la finestra di dialogo:
        self.dlg_solid.show()
        # Run the dialog event loop
        result = self.dlg_solid.exec_()
        self.dlg_solid.txtFeedback.clear()
        
    def estrai_param_connessione(self, connInfo):
        global theSchema
        theSchema = None
        theDbName = None
        theHost = None
        thePort = None
        theUser = None
        thePassword = None
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
        test_conn = None
        cur = None
        dest_dir = "dbname=%s host=%s port=%s user=%s password=%s" % (theDbName, theHost, thePort, theUser, thePassword)
        return dest_dir
            
##########################################################################
    # TEST DOCKWIDGET
        
    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING Core"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    #--------------------------------------------------------------------------

    def run_core(self):
        """Run method that loads and starts the plugin"""
        global FROM_TO_RULES
        global COD_POP
        global epsg_srid
        result_init = self.inizializza_layer()
        if (result_init==0):
            return 0
        #recupero le info di connex al DB da un qualunque dei layer:
        connInfo = SCALE_layer.source()
        #A questo punto finalmente mi connetto al DB per recuperare le variabili di progetto:
        db_dir = self.estrai_param_connessione(connInfo)
        test_conn = None
        try:
            test_conn = psycopg2.connect(db_dir)
            dict_cur = test_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            query_var = """SELECT pta_ui_min, pta_ui_max, pta_cont_max,
                giunto_ui_min, giunto_ui_max, giunto_cont_max, 
                pd_ui_min, pd_ui_max, pd_cont_max,
                pfs_ui_min, pfs_ui_max, pfs_pd_max, 
                pfp_ui_min, pfp_ui_max, pfp_pfs_max, id_pop, srid
                FROM %s.variabili_progetto_return; """ % (theSchema)
       
            dict_cur.execute(query_var)
            results_var = dict_cur.fetchone()
            epsg_srid = results_var['srid']
            self.epsg_srid = epsg_srid
            #Recupero la variabile COD_POP e controllo se e' settata:
            COD_POP = results_var['id_pop']
            if not COD_POP:
                cippa = QInputDialog()
                cippa.setIntValue(0) #se non dovesse essere intero usa "setTextValue()"
                cippa.setWindowTitle('POP non settato!')
                cippa.setLabelText('POP nullo, settarlo ora per il progetto e poter proseguire')
                retval = cippa.exec_()
                COD_POP = str(cippa.intValue())
                #a questo punto lo inserirei nella tabella di progetto:
                query_pop = "UPDATE %s.variabili_progetto_return SET id_pop=%s;" % (theSchema, COD_POP)
                dict_cur.execute(query_pop)
                test_conn.commit()
    
            #Ricostruisco il dict con le variabili:
            FROM_TO_RULES = {
                'PTA': {'MIN_UI': results_var['pta_ui_min'], 'MAX_UI': results_var['pta_ui_max'], 'MAX_CONT': results_var['pta_cont_max']},
                'GIUNTO': {'MIN_UI': results_var['giunto_ui_min'], 'MAX_UI': results_var['giunto_ui_max'], 'MAX_CONT': results_var['giunto_cont_max']},
                'GIUNTO_F_dev': {'MIN_UI': results_var['giunto_ui_min'], 'MAX_UI': results_var['giunto_ui_max'], 'MAX_CONT': results_var['giunto_cont_max']},
                'PD': {'MIN_UI': results_var['pd_ui_min'], 'MAX_UI': results_var['pd_ui_max'], 'MAX_CONT': results_var['pd_cont_max']},
                'PFS': {'MIN_UI': results_var['pfs_ui_min'], 'MAX_UI': results_var['pfs_ui_max'], 'MAX_CONT': results_var['pfs_pd_max']},
                'PFP': {'MIN_UI': results_var['pfp_ui_min'], 'MAX_UI': results_var['pfp_ui_max'], 'MAX_CONT': results_var['pfp_pfs_max']}
            }
            FROM_TO_RULES['SCALA'] = FROM_TO_RULES['PTA']
            #Utils.logMessage(str(FROM_TO_RULES['GIUNTO']))
        
            dict_cur.close()
        except psycopg2.Error, e:
            Utils.logMessage(e.pgerror)
            #self.dlg_compare.txtFeedback.setText(e.pgerror)
            FROM_TO_RULES = self.FROM_TO_RULES
            COD_POP = self.COD_POP
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Non sono riuscito a scaricare correttamente dal DB le variabili del progetto in uso. Carico quelle di default')
            return 0;
        except SystemError, e:
            Utils.logMessage('Errore di sistema!')
            #self.dlg_compare.txtFeedback.setText('Errore di sistema!')
            FROM_TO_RULES = self.FROM_TO_RULES
            COD_POP = self.COD_POP
            QMessageBox.warning(self.dock, self.dock.windowTitle(), 'Non sono riuscito a scaricare correttamente dal DB le variabili del progetto in uso. Carico quelle di default')
            return 0
        else:
            self.FROM_TO_RULES = FROM_TO_RULES
            self.COD_POP = COD_POP
            #Utils.logMessage('Variabili del progetto importate con successo! '+str(sys.version)+" - QGIS Version: " + self.Qgis_sw_version)
            Utils.logMessage('Variabili del progetto importate con successo!')
            #self.dlg_compare.txtFeedback.setText('Variabili del progetto importate con successo!')
        finally:
            if test_conn:
                test_conn.close()
        
        global check_origine #variabile booleana che mi dice se e' tutto ok lato origine
        check_origine = 0
        global check_dest #variabile booleana che mi dice se e' tutto ok lato destinazione
        check_dest = 0

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING Core"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = CoreDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location        
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
