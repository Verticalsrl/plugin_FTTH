'''
Compilazione della tabella quantita_elementi
'''

from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pgRoutingLayer_utils as Utils
import os
import psycopg2
import psycopg2.extras


QUERY_INIZIALIZZA_METRICO = """INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (1, 'SCAVO - MINITRINCEA', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (2, 'SCAVO - NODIG', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (3, 'SCAVO - NODIG SUPPLEMENTO > 80 MML', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (4, 'SCAVO - NODIG ACQUA', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (5, 'SCAVO - TRADIZIONALE TERRENO', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (6, 'SCAVO - TRADIZIONALE ASFALTO', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (7, 'SCAVO - TRADIZIONALE MASEGNO', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (8, 'INFRASTRUTTURAZIONE PONTE TRACHITE', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (9, 'INFRASTRUTTURAZIONE PONTE ASFALTO', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (10, 'INFRASTRUTTURAZIONE PONTE LEGNO', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (11, 'INFRASTRUTTURAZIONE PONTE FERRO', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (12, 'SCAVO - TRADIZIONALE PAVIMENTAZIONE PREGIATA', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (13, 'ZANCATURA', 'NUOVE INFRASTRUTTURE', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (14, 'ED INTERRATA', 'INFRASTRUTTURE ESISTENTI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (15, 'ED AEREA (FACCIATA)', 'INFRASTRUTTURE ESISTENTI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (16, 'ED AEREA (PALIFICATA)', 'INFRASTRUTTURE ESISTENTI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (17, 'IP INTERRATA', 'INFRASTRUTTURE ESISTENTI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (18, 'IP AEREA', 'INFRASTRUTTURE ESISTENTI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (19, 'ALTRE INFRASTRUTTURE COMUNALI INTERRATE', 'INFRASTRUTTURE ESISTENTI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (20, 'CUNICOLO CALPESTABILE', 'INFRASTRUTTURE ESISTENTI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (21, 'MINITUBO 10/12', 'TUBAZIONI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (22, 'MINITUBO 10/14', 'TUBAZIONI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (23, 'TUBO 50 MM', 'TUBAZIONI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (24, 'TUBO 125 mm', 'TUBAZIONI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (25, 'FENDER 10/12', 'TUBAZIONI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (26, 'FENDER 10/14', 'TUBAZIONI', %(pfp)s);
INSERT INTO %(schema)s.quantita_elementi(id, descrizione, tipo, id_pfp) VALUES (27, 'BUNDLE x 7', 'TUBAZIONI', %(pfp)s);"""


def calc_computo_metrico(dest_dir, self, theSchema):
    test_conn = None    
    test_conn = psycopg2.connect(dest_dir)
    cursor_metrico = test_conn.cursor()
    
    #QUERY TEMPORANEA DI CREAZIONE DELLA TABELLA: in futuro forse e' meglio crearla da subito..
    query_create_raw = """CREATE TABLE IF NOT EXISTS %(schema)s.quantita_elementi ( id integer NOT NULL, descrizione character varying(120), tipo character varying(120), id_pfp integer NOT NULL, primaria double precision, secondaria double precision, totale double precision, CONSTRAINT quantita_elementi_pkey PRIMARY KEY (id, id_pfp) );"""
    query_create = query_create_raw % {'schema': theSchema}
    cursor_metrico.execute(query_create)
    test_conn.commit()
    
    #Prima tronco la tabella:
    query_trunc = "TRUNCATE %s.quantita_elementi;" % (theSchema)
    cursor_metrico.execute(query_trunc)
    test_conn.commit()
    
    query_pfp = "SELECT DISTINCT id_pfp::integer FROM %s.cavo ORDER BY id_pfp::integer" % (theSchema)
    cursor_metrico.execute(query_pfp)
    results_metrico = cursor_metrico.fetchall() #tira fuori un dictionary
    msg = QMessageBox()
    try:
        for result in results_metrico:
            id_pfp = result[0]
            if id_pfp==None:
                continue
            query_iniziale = QUERY_INIZIALIZZA_METRICO % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_iniziale)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'minitrincea' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'minitrincea' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE descrizione = 'SCAVO - MINITRINCEA' AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'no-dig' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'no-dig' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE descrizione = 'SCAVO - NODIG' AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'tradizionale' AND tipo_pav ~* 'TERRENO' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'tradizionale' AND tipo_pav ~* 'TERRENO' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=5 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'tradizionale' AND tipo_pav ~* 'ASFALTO' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'tradizionale' AND tipo_pav ~* 'ASFALTO' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=6 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'tradizionale' AND tipo_pav ~* 'MASEGNO' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'tradizionale' AND tipo_pav ~* 'MASEGNO' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=7 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'tradizionale' AND tipo_pav ~* 'PREGIAT' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE tipo_scavo ~* 'tradizionale' AND tipo_pav ~* 'PREGIAT' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=12 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf ~* '37-001-RAMO_BT_-_CAVO_INTERRAT|ED INTERRATA DA VERIFICARE' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf ~* '37-001-RAMO_BT_-_CAVO_INTERRAT|ED INTERRATA DA VERIFICARE' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=14 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf ~* '37-004-RAMO_BT_-_CAVO_AEREO' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf ~* '37-004-RAMO_BT_-_CAVO_AEREO' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=15 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf ~* 'RAMO_BT_-_PALO_AEREO' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf ~* 'RAMO_BT_-_PALO_AEREO' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=16 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf = 'ILLUMINAZIONE PUBBLICA' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf = 'ILLUMINAZIONE PUBBLICA' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=17 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf ~* 'ILLUMINAZIONE PUBBLICA AEREA NUDA' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf ~* 'ILLUMINAZIONE PUBBLICA AEREA NUDA' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=18 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf IN ('VENIS', 'TRAM', 'FO APS') AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(length_m) FROM %(schema)s.cavo WHERE codice_inf IN ('VENIS', 'TRAM', 'FO APS') AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=19 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(coalesce(n_mt_occ::numeric, 0)*length_m) FROM %(schema)s.cavo WHERE codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(coalesce(n_mt_occ::numeric, 0)*length_m) FROM %(schema)s.cavo WHERE codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=21 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(coalesce(n_tubi::numeric, 0)*length_m) FROM %(schema)s.cavo WHERE codice_inf = 'TRINCEA NORMALE_ATT' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(coalesce(n_tubi::numeric, 0)*length_m) FROM %(schema)s.cavo WHERE codice_inf = 'TRINCEA NORMALE_ATT' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=23 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(coalesce(n_tubi::numeric, 0)*length_m) FROM %(schema)s.cavo WHERE codice_inf = 'RACCORDO' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(coalesce(n_tubi::numeric, 0)*length_m) FROM %(schema)s.cavo WHERE codice_inf = 'RACCORDO' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=24 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(coalesce(btrim(n_mtubo, 'x7')::numeric, 0)*length_m) FROM %(schema)s.cavo WHERE codice_inf IN ('TRINCEA NORMALE', 'MINITRINCEA') AND n_mtubo ~* 'x7' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(coalesce(btrim(n_mtubo, 'x7')::numeric, 0)*length_m) FROM %(schema)s.cavo WHERE codice_inf IN ('TRINCEA NORMALE', 'MINITRINCEA') AND n_mtubo ~* 'x7' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=26 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()
            
            query_up = "UPDATE %(schema)s.quantita_elementi SET primaria=(SELECT sum(coalesce(btrim(n_mtubo, 'x7')::numeric, 0)*length_m) FROM %(schema)s.cavo WHERE codice_inf = 'NO DIG' AND n_mtubo ~* 'x7' AND codice_ins ~* 'PR' AND id_pfp='%(pfp)s'), secondaria=(SELECT sum(coalesce(btrim(n_mtubo, 'x7')::numeric, 0)*length_m) FROM %(schema)s.cavo WHERE codice_inf = 'NO DIG' AND n_mtubo ~* 'x7' AND codice_ins !~* 'PR' AND id_pfp='%(pfp)s') WHERE id=27 AND id_pfp=%(pfp)s;" % {'schema': theSchema, 'pfp': id_pfp}
            cursor_metrico.execute(query_up)
            test_conn.commit()        
            
        
        #Alla fine calcolo i totali:
        query_totali = "UPDATE %(schema)s.quantita_elementi SET totale = coalesce(primaria,0) + coalesce(secondaria,0);" % {'schema': theSchema}
        cursor_metrico.execute(query_totali)
        test_conn.commit()     
    
		#se si volesse esportare la tabella la query potrebbe essere:
		#query = "psql.exe -p 5433 -U postgres -d Enel_Test -c \"\COPY areacavo1_mestre_bis.quantita_elementi TO 'quantita_elementi.csv' CSV HEADER\""
		
    except psycopg2.Error, e:
        msg.setText(e.pgerror)
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
        
        
    
    
    
    