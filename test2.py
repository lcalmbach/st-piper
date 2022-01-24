"""
Diese App unterstützt die Prozesse rund um das Erstellen des Covid-19 Lageberichts mails der Medizinischen Dienste
des Kantons Basel-Stadt.

Kontakt: lukas.calmbach@bs.ch
"""

import pandas as pd
import streamlit as st
import altair as alt
import locale
from datetime import datetime, timedelta, date
import calendar
import json
import requests
import io
from io import BytesIO
import json
import os
import shutil
from passlib.context import CryptContext
import random
import socket
import logging
from st_aggrid import AgGrid
from streamlit_lottie import st_lottie
import time

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import locale
import db
import const
import tools
from queries import qry
import reports as rep
import mail_app


STYLE = """
<style>
img {
    max-width: 100%;
}
</style>
"""

__author__ = 'lukas calmbach'
__author_email__ = 'lukas.calmbach@bs.ch'
__version__ = '0.1.56'
version_date = '2022-01-04'
logger = {}
my_name = 'Covid-Lagebericht'
my_emoji = "📧"
LOTTIE_URL = 'https://assets1.lottiefiles.com/packages/lf20_0djafiny.json'

# App-Server auf dem die applikation gestartet wurde
app_server = socket.gethostname().lower()
db_server = const.host_dic[app_server]

def get_config():
    """
    Gibt die Konfiguration in Form eines Dataframes und eines dictionarys zurück.
    Der Dataframe wird verwendet um die Gesamtkonfiguration anzuzeigen und zu editieren.
    Das dictionary wird verwendet, um die records in der App zu verwenden, z.B.
    als config['schluessel']
    Params
    
    """

    sql = qry['get_konfig']
    cfg_df, ok, err_msg = db.get_recordset(db.conn,sql)
    if ok:
        cfg_df = cfg_df.set_index('schluessel')
        cfg_dic = cfg_df['wert'].to_dict()        
        logger.debug('Konfiguration geladen')
    else:
        logger.error('Konfiguration konnte nicht geladen werden')
    return cfg_df, cfg_dic, ok


def qs_check()->bool:
    """
    Diese Funktion führt alle im dict const.qs_regeln definierten Tests durch und gibt zurück, ob eine Regel mit Prio 1 verletzt wurde.
    Pro Test ist ein SQL command definiert, welches genau einen erwarteten Wert zurückgeben soll, z.b. die Zahl der Fälle ohne definierten
    Kanton. In einer zweiten Variablen ist der erwartete Wert definiert, in diesem Fall 0. wenn Resultat - erwarteter WErt <> 0 ist die Regel 
    verletzt. Ist ide Regel verletzt und die REgel hat Prio 1 wird der check abgebrochen und ok_continue = False zurückgegeben.
    """

    def handle_offended_rule(check, expected_result, result):       
        """
        Druckt die Information, wenn eine Regel verletzt wurde
        Params
        check           check object
        expected_result 
        result
        """ 
        st.warning(f'**Fehler** Erwarteter Wert = {expected_result} Wert gefunden = {result}')
        sql = const.qs_regeln[check]['sql_command_patient_id']
        if sql != None:
            df, ok, err_msg = db.get_recordset(db.conn,sql)
            if ok:
                id_name = const.qs_regeln[check]['listed_field_name'] # patient_id oder case_id
                # Spalte zu str konvertieren sonst funktioniert join nicht
                df[id_name] = df[id_name].astype(str)
                offending_records = ','.join(df[id_name].to_list())
                st.markdown(f'Bitte folgende {id_name}s prüfen: {offending_records}')
            else:
                logger.error(f"Fehler in QS-Check beim Lesen der Liste Patienten: {err_msg}")
    
    def verify_rule(check):
        """
        Überprüft eine Regel und gibt zurück zurück ob eine kritische Regel (Prio = 1) verletzt wurde
        """

        ok = True
        ok_continue = True
        err_msg = ''
        expected_result = const.qs_regeln[check]['expected_result']
        description = const.qs_regeln[check]['beschreibung']
        result_ok = (result - expected_result == 0)
        with st.expander(f'Regel: {title}', expanded= False):
            st.markdown(description)
        if result_ok:
            st.markdown('Ergebnis: ok')                 
        else:
            ok_continue = const.qs_regeln[check]['prio'] > 1
            handle_offended_rule(check, expected_result, result)
        return ok_continue

    ok = True
    err_msg = ''
    st.markdown(f'### QS Checks')
    ok_continue = True
    for check in const.qs_regeln:
        if ok_continue:
            title = const.qs_regeln[check]['bezeichnung']
            sql = const.qs_regeln[check]['sql_command_cnt']
            result, ok, err_msg = db.get_value(db.conn, sql)
            if ok:
                ok_continue = verify_rule(check)
            else:
                st.warning(f"Fehler in QS-Check beim Lesen des QS Resultats: {err_msg}")
                logger.error(f"Fehler in QS-Check beim Lesen des QS Resultats: {err_msg}")
    return ok_continue


def show_summary():  
    """
    Startscreen, zeigt ein paar allgemeine Infos zum aktuellen Stand sowie den Log der letzten 2 Tage und 
    den Stand der zu publizierenden Zahlen.
    """

    ok = True
    err_msg = ''
    st.markdown(f'### Log Einträge')
    
    sql = qry['log_today']
    df, ok, err_msg = db.get_recordset(db.conn,sql)
    if ok:
        AgGrid(df)
    else:
        pass


def import_file():    
    """
    Startet den Import der Einzeldaten
    """
    def save_csv_file():
        """
        obsolete
        """
        csv_file = f"imp_{date.today().strftime('%Y-%m-%d')}.csv"
        archive_file = const.config['source_path'] + archiv_folder + csv_file
        try:
            df.to_csv(archive_file, index=False)
        except Exception as ex:
            logger.error(f"Archivdatei '{archive_file} konnte nicht geschrieben werden:' {ex}")
    
    def save_file_to_archive():
        archiv_folder = 'archiv\\' if is_prod_server() else 'archiv_test\\'                                    
        archive_file = f"{const.config['source_path']}{archiv_folder}{date.today().strftime('%Y-%m-%d')}_{const.config['source_filename']}"
        sql = qry['rowcount_lagebericht_today']
        rows = db.get_value(db.conn, sql)
        try:
            shutil.copyfile(filename, archive_file)
        except Exception as ex:
            logger.error(f"Importdatei '{filename} konnte nicht archiviert werden:' {ex}")


    filename = const.config['source_path'] + const.config['source_filename']
    ok = True
    err_msg = ''
    try:
        save_reporting_time(start_time=None)
        st.info(f"{const.config['source_filename']} wird gelesen")
        try:
            df = pd.read_excel(filename)
        except Exception as ex:
            logger.error(f"Exceldatei '{const.config['source_filename']}' konnte nicht gelesen werden:{ex}")
        all_fields = ','.join(df.columns)
        sql = qry['db_fields']
        df_fields, ok, err_msg = db.get_recordset(db.conn, sql)
        if ok:
            # LC, 2021-01-23: wenn man eine Liste von Feldern übergibt, dann macht das Feld [Date of Death] Probleme: Index [Date of Death] does not exist
            # mit jedem anderen Feld geht es. Da die Daten eh gelöscht werden, kann man auf die Spaltenselektion verzichten und alles importieren
            raw_fields = df_fields['field_name'].to_list() 
            db_fields = df_fields['db_field_name'].to_list() 

            st.info('Import in DB wird gestartet, dies kann einige Minuten dauern.')
            ok, err_msg = db.exec_non_query(db.conn, qry['truncate_rohdaten'])
            ok, err_msg = db.append_pd_table(df, 'lagebericht_roh', raw_fields) # raw_fields, ergibt komischen Fehler, daher werden einfach alle Felder importiert
            if ok:
                st.info(f"{const.config['source_filename']} wurde in DB importiert: {len(df)} Zeilen")
            else:
                st.warning(f"Datei {const.config['source_filename']} konnte nicht in DB importiert werden: {err_msg}")
            if ok:
                # formatiert die list zu einem Komma separierten Text im Format [feld 1], [feld 2]...
                raw_fields_str = '[' + '], ['.join(raw_fields) + ']'
                db_fields_str = '[' + '], ['.join(db_fields) + ']'
                sql_cmd = qry['insert_lagebericht'].format(db_fields_str, raw_fields_str, st.session_state.user_name)
                ok, err_msg = db.exec_non_query(db.conn, sql_cmd)
                if ok:
                    st.info('Felder wurden in DB Tabelle formatiert')
                else:
                    st.warning(f'Felder konnten in der DB Tabelle nicht formatiert werden: {err_msg}')
                save_file_to_archive()
                
                # nie verwendet, bei Gelegenheit ganz entfernen
                # save_csv_file()
                
                try:
                     os.remove(filename)
                     st.info('Import Datei wurde gelöscht')
                except Exception as ex:
                    logger.error(f"Importdatei '{filename} konnte nicht gelöscht werden:' {ex}")
                                    
                
                return True
    except Exception as ex:
        st.warning(f'Die Datei konnte nicht importiert werden: {ex}')
        return False


def calculate_values():
    """
    Aggregiert die Einzelwerte in die Zeitreihetabelle und berechnet die Inzidenzen.
    """

    ok = True
    err_msg = ''
    st.info('Inzidenzen und Differenzen zu Vortags-Werten werden berechnet')
    sql = qry['run_update'].format(st.session_state.user_name)
    ok, err_msg = db.exec_non_query(db.conn,sql)
    if ok:
        logger.debug('Calculate_values wurde ausgeführt')
        st.info('Berechnungen wurden durchgeführt, die wichtigsten Resultate sind in untenstehender Tabelle aufgelistet')
    else:
        st.error(f'Bei der Aufbereitung in Tabelle Zeitreihe_Publikation ist ein Problem aufgetreten: {err_msg}')
    sql = qry['inzidenzen_qs']
    df,ok,err_msg = db.get_recordset(db.conn,sql)
    if ok:
        AgGrid(df)
    else:
        pass
    return ok


def publish_results():
    """
    Versendet den scharfen Lagebericht mit den Optionen: Mail, SMS, OGD Export
    """

    ok = [True,True,True, True]
    if qs_check():
        if st.checkbox(f"QS durchgeführt ({st.session_state.user_name})", value=False):
            form = st.form(key= 'mail_send_form')
            with form:
                send_mail_sel = st.checkbox("Mail versenden an Mail Verteiler", value=True)
                send_sms_sel = st.checkbox("SMS versenden an SMS Verteiler", value=True)
                ogd_export_sel = st.checkbox("OGD Export durchführen", value=True)
                if form.form_submit_button('Versand starten'):        
                    if ogd_export_sel:
                        ok[0] = export_ogd(destination=const.config['export_csv_path'])
                    if send_mail_sel:
                        ok[1] = mail_app.send_mail('mail')
                    if send_sms_sel:
                        ok[2] = mail_app.send_sms('sms')
                    
    else:
        st.warning("Bei den QS-Checks wurden Fehler gefunden, die korrigiert werden müssen, bevor der Lagebericht versandt werden kann.")    
    return all(ok)


def show_configuration():
    """
    Zeigt eine html Tabelle mit allen Konfigurationseinträgen an
    """

    ok = True
    err_msg = ''
    sql = qry['get_html_table'].format('konfig')
    html, ok, err_msg = db.get_value(db.conn,sql)
    if ok:
        logger.debug("Konfiguration wird angezeigt")
        st.markdown(html, unsafe_allow_html=True)
    else:
        logger.warning("Konfiguration kann nicht angezeigt werden: {err_msg}")


def show_query_dataframe(sql):
    ok = True
    err_msg = ''
    df, ok, err_msg = db.get_recordset(db.conn,sql)
    if ok:
        AgGrid(df, key=str(datetime.now()) )
    else:
        st.warning("Ein Fehler ist aufgetreten bei der Anzeige der Tabelle: {err_msg}")


def get_vaccination_data_from_data_bs():
    """
    Einlesen der Geimpften BS über api von data.bs.ch
    """

    def synch_vaccination_data():
        """
        Ruft die stored procedure auf dem sql server auf, diese lädt die tabelle Impfdaten_roh in die Tabelle Publikation_Zeitreihe 
        und berechnet die kumulierten WErte
        """
        ok = True
        err_msg = ''
        sql = qry['synch_impfdaten'].format(st.session_state.user_name)
        ok, err_msg = db.exec_non_query(db.conn,sql)
        if  ok:
            st.info(f"Impdaten wurden in DB importiert und abgeglichen: {len(df)} Records")
        else:
            raise Exception(f"In der Abgleich-Prozedur ist ein Fehler aufgetreten: {err_msg}") 
        return ok

    ok = True
    err_msg = ''
    
    try:
        # https://data.bs.ch/explore/dataset/100111/download/?format=csv&timezone=Europe/Berlin&lang=de&use_labels_for_header=true&csv_separator=%3B
        url = const.config['url_impfungen']        
        s = requests.get(url, proxies=const.PROXY_DICT).text  
        df = pd.read_csv(io.StringIO(s), sep = ";")
        fields = [
            'Datum',
            'Total verabreichte Impfungen', 
            'Total verabreichte Impfungen pro Tag',
            'Total Personen mit zweiter Dosis',
            'Total Auffrischimpfungen (Booster)',
            'Total Drittimpfungen (oder mehr) als Teil der Grundimmunisierung',

            'Im Impfzentrum verabreichte Impfungen pro Tag',
            'Durch mobile Equipen verabreichte Impfungen pro Tag (APH etc.)',
            'Im Spital verabreichte Impfungen pro Tag',
            'Anderswo verabreichte Impfungen pro Tag',
            
            'Anderswo mit zweiter Dosis geimpfte Personen pro Tag',
            'Im Spital mit zweiter Dosis geimpfte Personen pro Tag',
            'Im Impfzentrum mit zweiter Dosis geimpfte Personen pro Tag',
            'Durch mobile Equipen mit zweiter Dosis geimpfte Personen pro Tag (APH etc.)',
            
            'Auffrischimpfungen (Booster) pro Tag',
            'Drittimpfungen (oder mehr) als Teil der Grundimmunisierung pro Tag',
        ]
        df = df[fields]   
        df['Datum'] = pd.to_datetime(df['Datum'])
        
        df = df.rename(columns={
            'Total verabreichte Impfungen': 'impfung_total_kum',
            'Total verabreichte Impfungen pro Tag': 'impfung_total',
            'Total Personen mit zweiter Dosis': 'impfung_2_kum',
            'Total Auffrischimpfungen (Booster)': 'booster_kum',
            'Total Drittimpfungen (oder mehr) als Teil der Grundimmunisierung': 'impfung_3_kum',

            'Im Impfzentrum verabreichte Impfungen pro Tag': 'impfzentrum_pro_tag',
            'Durch mobile Equipen verabreichte Impfungen pro Tag (APH etc.)': 'mob_equipen_pro_tag',
            'Im Spital verabreichte Impfungen pro Tag': 'spital_pro_tag',
            'Anderswo verabreichte Impfungen pro Tag': 'anderswo_pro_tag',
            
            'Anderswo mit zweiter Dosis geimpfte Personen pro Tag': 'dosis2_pro_tag_anderswo',
            'Im Spital mit zweiter Dosis geimpfte Personen pro Tag': 'dosis2_pro_tag_spital',
            'Im Impfzentrum mit zweiter Dosis geimpfte Personen pro Tag': 'dosis2_pro_tag_impfzentrum',
            'Durch mobile Equipen mit zweiter Dosis geimpfte Personen pro Tag (APH etc.)': 'dosis2_pro_tag_mobile',
            
            'Auffrischimpfungen (Booster) pro Tag':'booster_pro_tag',
            'Drittimpfungen (oder mehr) als Teil der Grundimmunisierung pro Tag': 'dosis_3_pro_tag',            
        })  
        ok, err_msg = db.append_pd_table(df, 'impfung_roh', [])
        if ok:
            AgGrid(df)               
            ok, err_msg = db.append_pd_table(df, 'impfung_roh', [])
            if ok:
                ok = synch_vaccination_data()              
    except Exception as ex:
        st.warning(f"Beim Einlesen der Impfungen ist ein Fehler aufgetreten: {ex}")
        ok = False
    return ok


def get_bl_cases():
    """
    Einlesen der Zahlen von BL über api von data.bs.ch
    """

    ok = True
    err_msg = ''
    url = const.config['url_covid_faelle_kantone'].format('BL')    
    try:
        s = requests.get(url, proxies=const.PROXY_DICT).text
        records = json.loads(s)
        records = records['records']
        df_json = pd.DataFrame(records)
        lst = df_json['fields']
        st.info("Datei mit BL-Fällen wurde geladen")

        for x in lst:
            cmd = qry['update_faelle_bl'].format(x['ncumul_conf'],x['date'])
            ok, err_msg = db.exec_non_query(db.conn, cmd)
            if not ok:
                st.markdown(f'Befehl `{cmd}` konnte nicht ausgeführt werden.')
                logger.warning(f'Befehl `{cmd}` konnte nicht ausgeführt werden: {err_msg}')
        st.info("BL Fälle wurden in der Datenbank gespeichert")
        show_query_dataframe(qry['show_bl_cases'])
    except Exception as ex:
        st.warning(f"Beim Einlesen der BL Zahlen ist ein Fehler aufgetreten: {ex}")
        ok = False
    return ok


def get_bs_cases():
    """
    Einlesen der Zahlen von BS (Hospitalisierte) über api von data.bs.ch
    """

    ok = True
    err_msg = ''
    url = const.config['url_bs_hospitalisierte']
    try:
        s = requests.get(url, proxies=const.PROXY_DICT).text
        records = json.loads(s)
        records = records['records']
        df_json = pd.DataFrame(records)
        lst = df_json['fields']
        st.info("Datei mit BS-Fällen wurde geladen")

        for x in lst:
            if 'current_hosp_resident' in x:
                # st.write(x['current_hosp_resident'],x['current_hosp'],x['current_icu'],x['date'])
                cmd = qry['update_faelle_bs'].format(x['current_hosp_resident'], 
                    x['current_hosp'], 
                    x['current_icu'], 
                    (1 if x['data_from_all_hosp'] == 'True' else 0),
                    x['date'] )
                ok, err_msg = db.exec_non_query(db.conn, cmd)
                if not ok:
                    st.markdown(f'Befehl `{cmd}` konnte nicht ausgeführt werden.')
        st.info("BS Hospitalisierte wurden in Datenbank gespeichert")
        show_query_dataframe(qry['show_bs_hospitalised'])
    except Exception as ex:
        st.warning(f"Beim Einlesen der Zahlen für Hospitalisierte ist ein Fehler aufgetreten: {ex}")
        ok = False
    return ok


def get_bag_daily_datasets():
    
    """
    Zuerst wird das json file mit den heutig gültigfen Links geladen: https://www.covid19.admin.ch/api/data/context
    Über die Kaskade data['sources']['individual']['csv']['daily'] und dem Tag: daily['cases'] wird anschliessend das csv
    der heutigen Fälle direkt in ein DataFrame geladen und die Tagesrecords werden je über ein insert command in die DAtenbank geschrieben.
    """

    def save_table(url, table_name):
        region = 'ch'
        urlData = requests.get(url,proxies=const.PROXY_DICT).content # create HTTP response object 
        df = pd.read_csv(io.StringIO(urlData.decode('utf-8')))
        df_region = df[df['geoRegion'].isin(['BS', 'BL', 'CH'])]
        ok, err_msg = db.append_pd_table(df, table_name, [])
        return ok

    ok = True
    err_msg = ''
    url = const.config['url_bag_context']    
    try:
        urlData = requests.get(url, proxies=const.PROXY_DICT) # create HTTP response object 
        files_metadata = urlData.json()
        daily = files_metadata['sources']['individual']['csv']['daily']
        #werden im Moment nicht gebraucht, 
        #url = daily['hosp']
        #ok = save_table(url, 'bag_hosp')
        #if ok:
        #    st.info("Hospitalisierte (Quelle BAG) wurden in Datenbank gespeichert")
        #
        #url = daily['hospCapacity']
        #ok = save_table(url, 'bag_hospCapacity')
        #if ok:
        #    st.info("Kapazität der Spitäler (Quelle BAG) wurden in Datenbank gespeichert")
        
        url = daily['cases']
        ok = save_table(url, 'bag_cases')
        if ok:
            st.info("Fälle (Quelle BAG, alle Regionen) wurden in Datenbank gespeichert")

    except Exception as ex:
        st.warning(f"Beim Einlesen der Fallzahlen der Schweiz ist ein Fehler aufgetreten: {ex}")
        ok = False
    return ok


def get_ch_cases():
    
    """
    Speichert den BAG lagebericht lokal ab, öffnet die Excel Datei und speichert die CH-Fälle. Da pd.read_excel keinen proxys parameter kennt, muss die 
    Datei zuerst geladen und lokal im Verzeichnis data abgespeichert werden.
    zuerst wird das json file mit den heutig gültigfen Links geladen: https://www.covid19.admin.ch/api/data/context
    Über die Kaskade data['sources']['individual']['csv']['daily'] und dem Tag: daily['cases'] wird anschliessend das csv
    der heutigen Fälle direkt in ein DataFrame geladen und die Tagesrecords werden je über ein insert command in die DAtenbank geschrieben.
    """

    def save_cases(url):
        region = 'ch'
        urlData = requests.get(url,proxies=const.PROXY_DICT).content # create HTTP response object 
        df = pd.read_csv(io.StringIO(urlData.decode('utf-8')))
        df_region = df[df['geoRegion'] == region.upper()]
        for i in range(len(df_region)): 
            datum = df_region.loc[i, "datum"]
            value = df_region.loc[i, "sumTotal"]
            cmd = qry['update_faelle_ch'].format(value, datum)
            ok, err_msg = db.exec_non_query(db.conn, cmd)
            if not ok:
                st.markdown(f'Befehl `{cmd}` konnte nicht ausgeführt werden.')
        st.info("CH Fälle wurden in Datenbank gespeichert")
        # dies löst einen Fehler aus There are multiple identical st.st_aggrid.agGrid widgets with key='2021-09-02 13:37:11.356624'.
        # keine Ahnung warum, ich versuche as später zu lösen, die PReview ist nicht wichtig
        # show_query_dataframe(qry['show_ch_faelle'])
        return ok

    ok = True
    err_msg = ''
    url = const.config['url_bag_context']    
    try:
        urlData = requests.get(url, proxies=const.PROXY_DICT) # create HTTP response object 
        files_metadata = urlData.json()
        daily = files_metadata['sources']['individual']['csv']['daily']
        url = daily['cases']
        ok = save_cases(url)
        if ok:
            st.info("CH Fälle wurden in Datenbank gespeichert")
            show_query_dataframe(qry['show_ch_faelle'])
    except Exception as ex:
        st.warning(f"Beim Einlesen der Fallzahlen der Schweiz ist ein Fehler aufgetreten: {ex}")
        ok = False
    return ok


def get_re_werte():
    
    """
    Zuerst wird das json file mit den heutig gültigfen Links geladen: https://www.covid19.admin.ch/api/data/context
    Über die Kaskade data['sources']['individual']['csv']['daily'] und dem Tag: daily['cases'] wird anschliessend das csv
    der heutigen Fälle direkt in ein DataFrame geladen und die Tagesrecords werden je über ein insert command in die DAtenbank geschrieben.
    """


    def get_data(data_type, df_list):
        url_dic = {}
        url_dic['BL'] = url_base.format('BL', estim_type, data_type)   
        url_dic['BS'] = url_base.format('BS', estim_type, data_type)     
        url_dic['CHE'] = url_base.format('CHE', estim_type, data_type)   
        for key, url in url_dic.items():
            data = requests.get(url, proxies=const.PROXY_DICT).json()
            data = data['records']
            df = pd.DataFrame(data)['fields']
            df = pd.DataFrame(x for x in df)
            df_list.append(df)
           
        return df_list
    
    df_list = []
    url_base = const.config['url_re_werte_ogd'] 
    try:
        estim_type = "Cori_slidingWindow"
        data_type = 'Confirmed+cases'
        df_list = get_data(data_type, df_list)
        data_type = 'Hospitalized+patients'
        df_list = get_data(data_type, df_list)
        df = pd.concat(df_list)
        ok, err_msg = db.append_pd_table(df, 're_werte', [])
        
        
    except Exception as ex:
        st.warning(f"Beim Einlesen der Reproduktionszahlen ist ein Fehler aufgetreten: {ex}")
        ok = False
    return ok


def edit_values():
    """
    Erlaubt die manuell zu erfassenden Werte inzidenz07_loerrach, inzidenz07_haut_rhin und isoliert_aph_bs
    zu erfassen und speichern.
    """

    ok = True
    err_msg = ''
    with st.expander('Stand Datenbank'):
        show_query_dataframe(qry['edit_values_view'])

    st.markdown('#### Werte editieren')
    datum = st.date_input('Wähle Datum aus, welches editiert werden soll:')
    #datum = st.text_input('Datum (JJJJ-MM-TT')
    sql = qry['get_manual_edit_fields'].format(datum)
    df, ok, err_msg = db.get_recordset(db.conn,sql)
    form = st.form(key='my_values_form')
    with form:
        if ok and len(df) > 0: 
            val_loerrach = df.iloc[0]['inzidenz07_loerrach'] 
            val_haut_rhin = df.iloc[0]['inzidenz07_haut_rhin']
            val_aph = df.iloc[0]['isoliert_aph_bs']
        else:
            val_loerrach = None
            val_haut_rhin = None
            val_aph = None
        inzidenz07_loerrach = st.text_input('7-Tage Inzidenz Landeskreis Lörrach', val_loerrach)
        inzidenz07_haut_rhin = st.text_input('7-Tage Inzidenz Département Haut-Rhin', val_haut_rhin)
        #todo: implementieren wie vorher: Typ übergeben
        isoliert_aph_bs = st.text_input('Isolierte in APHs', int(float(val_aph)) if val_aph != None else None)
        
        if form.form_submit_button(label='Speichern'):
            inzidenz07_loerrach = db.format_db_value(inzidenz07_loerrach, const.FLOAT)
            inzidenz07_haut_rhin = db.format_db_value(inzidenz07_haut_rhin, const.FLOAT)
            isoliert_aph_bs = db.format_db_value(isoliert_aph_bs, const.INT) if isoliert_aph_bs != None else None
            cmd = qry['manual_update'].format(inzidenz07_loerrach, inzidenz07_haut_rhin, isoliert_aph_bs, datum)
            ok, err_msg = db.exec_non_query(db.conn,cmd)
            text_placeholder = st.empty()
            tools.display_temp_text(ok,"Datensatz wurde gespeichert.",
                f"Datensatz konnte nicht gespeichert werden: {err_msg}.",
                text_placeholder)


def edit_config():
    """
    Erlaubt dem User Parameter der Konfiguration zu editieren. Es muss jeweils der zu editierende Parameter 
    ausgewählt werden, anschliessend kann ein neuer Wert erfasst udn gespeichert werden.
    """

    ok = True
    err_msg = ''
    sql = qry['get_konfig']
    df_config, ok, err_msg = db.get_recordset(db.conn,sql)
    if ok:
        df_config = df_config.set_index('schluessel')
        key = st.selectbox("Wähle Parameter aus", options = df_config.index.to_list())
        value = st.text_input(key, df_config.loc[key]['wert'])
        st.markdown(df_config.loc[key]['beschreibung'])
        if st.button('Speichern'):
            value = db.format_db_value(value, const.STRING)
            cmd = qry['update_config'].format(value, key)
            ok, err_msg = db.exec_non_query(db.conn, cmd)
            if ok:
                st.info('Der Wert wurde gespeichert')
                logger.debug(f"Der Wert '{value}'' wurde in Feld {key} gespeichert.")
            else:
                logger.warning(f"Der Wert '{value}' konnte nicht in Feld {key} gespeichert werden: {err_msg}")
                st.warning(f'Der Wert konnte nicht gespeichert werden: {err_msg}')


def make_plots():
    """
    Erstellt die 2 Grafiken (attachment des Mailversands): 
    Fig 1. Neue Fälle als Barchart, 7 Tagesmittel als Linie
    Fig 2: Fälle BS kumuliert.
    """

    ok = True
    err_msg = ''
    meldezeit, ok, err_msg = db.get_value(db.conn, qry['meldezeit_today'])
    heute = datetime.strftime(datetime.now(), const.DATE_FORMAT)
    sql = qry['plot_data']
    df, ok, err_msg = db.get_recordset(db.conn,sql)
    if ok:
        df['datum'] = pd.to_datetime(df['datum'])
        

        # round to nearest years.
        datemin = list(df['datum'])[0]
        datemax = list(df['datum'])[-1]
        # LC: heutigen Wert drin lassen, auf Wunsch von SF, neuste Daten sind bei rasantem Anwachsen wichtig
        # df = df[df['datum'] < datemax]
        years = mdates.YearLocator()  # every month
        months = mdates.MonthLocator()  # every month
        years_fmt = mdates.DateFormatter(const.YEAR_FORMAT)
        months_fmt = mdates.DateFormatter(const.MONTH_FORMAT)
        plt.ticklabel_format(axis='y', useLocale=True)
        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(10,12))
        ax1.bar('datum', 'faelle_bs', data=df, color = 'orange', linewidth=1)
        ax1.plot('datum', 'mittel_07_tage_bs', data=df, color = 'blue', linewidth=2)
        ax1.set_title(f'Neumeldungen BS, Stand: {heute} {meldezeit}', fontsize=10)
        ax2.set_title(f'Meldungen kumulativ BS, Stand: {heute}  {meldezeit}', fontsize=10)
        ax2.plot('datum', 'faelle_bs_kum', data=df, color = 'blue', linewidth=2)
        ax1.legend(['7-Tage Mittel','Fälle'], loc=2,fontsize=8)
        ax2.legend(['Kumulierte Fälle'], loc=2,fontsize=8)
        # format the ticks
        ax1.xaxis.set_major_locator(months)
        ax1.xaxis.set_major_formatter(months_fmt)
        ax1.xaxis.set_minor_locator(months)
        
        ax2.xaxis.set_major_locator(months)
        ax2.xaxis.set_major_formatter(months_fmt)
        ax2.xaxis.set_minor_locator(months)

        ax1.tick_params(axis='x', labelsize=8) 
        ax1.tick_params(axis='y', labelsize=8) 
        ax2.tick_params(axis='x', labelsize=8) 
        ax2.tick_params(axis='y', labelsize=8) 

        ax1.grid(True)
        ax2.grid(True)

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        fig.autofmt_xdate()
        fig.savefig(fname=const.config['temp_figuren_lokal'], dpi=300, format='png')
        
        # fig.savefig(fname='figur.pdf', format='pdf', dpi=1200, bbox_inches='tight')
        st.pyplot(fig)

    return ok

            
def get_steps() -> list:
    """
    Zeigt die Prozesse als checkboxen an und gibt eine Boolean list zurück mit den gewählten Optionen 
    """

    def complete_mail_text():
        ok = True
        err_msg = ''
        comment_text, ok, err_msg = db.get_value(db.conn, qry['mail_comment_today'])
        if ok:
            comment_text = st.text_area("Begleittext-Zusatz für den Mailversand", comment_text)
            cmd = qry['update_mail_comment'].format(comment_text)
            ok, err_msg = db.exec_non_query(db.conn, cmd)
            if not ok:
                logger.warning("Kommentar '{comment_text}' konnte nicht gespeichert werden")
                st.warning('Kommentar konnte nicht gespeichert werden')

    ok = True
    err_msg = ''
    selected_steps = {}
    form = st.form(key='steps_form')
    with form:
        selected_steps['import'] = st.checkbox("Import Excel Datei in Datenbank", False)
        selected_steps['extern'] = st.checkbox("Externe Datenquellen importieren", True)
        selected_steps['update'] = st.checkbox("Zeitreihe erstellen", True)
        selected_steps['plots'] = st.checkbox("Grafiken erzeugen", True)
        selected_steps['test_mail']= st.checkbox("Test-Mail verschicken", True)
        selected_steps['test_sms']= st.checkbox("Test-SMS verschicken", True)
        selected_steps['test_ogd_export'] = st.checkbox("Test-OGD-Export durchführen", value=True)
            
        st.markdown('**Anpassungen in der Mail**')
        meldezeit, ok, err_msg = db.get_value(db.conn, qry['meldezeit_today'])
        if ok:
            meldezeit = st.text_input("Meldezeit", meldezeit)
        if meldezeit not in ('', 'None'):
            cmd = qry['update_meldezeit'].format(meldezeit)
            ok, err_msg = db.exec_non_query(db.conn, cmd)

            if ok:
                complete_mail_text()
            else:
                st.warning(f"Meldezeit konnte nicht gespeichert werden: {err_msg}")
        if form.form_submit_button(label='Submit'):
            run_selected_steps(selected_steps)


def get_rounded_time_string(t: datetime, interval: int)-> str:
    """
    Gibt einen Zeitstempel zurück, wobei die Minuten auf die nächsten 15 Minuten 
    gerundet sind. z.B. 9:03 > 9:15
    """

    t = datetime(t.year, t.month, t.day, t.hour, (t.minute - (t.minute % interval)) ) 
    return t.strftime(const.TIME_FORMAT)


def save_reporting_time(start_time = None):
    """
    Speichert die Meldezeit in das Feld meldezeit in der Tabelle Zeitreihe_publiziert.
    """

    ok = True
    err_msg = ''
    if start_time == None:
        start_time = get_rounded_time_string(datetime.now(), const.ROUNDED_MINUTES)        
    sql = qry['save_reporting_time'].format(start_time)
    ok, err_msg = db.exec_non_query(db.conn,sql)
    if not ok:
        logger.warning("Meldezeit konnte nicht gespeichert werden: {err_msg}")
        ok = False
    return ok


def show_upload_personen():
    """
    Diese Funktion erlaubt das Laden der Personen-Excel Datei, die unter MD\Admin abegelegt ist.
    """

    def synch_personen():
        """
        Führt die stored procedure aus welche die eingelesenen Personen von der Rohdaten in die verwendete Personentabelle
        überträgt und die Verteilerlisten füllt. 
        """

        ok = True
        err_msg = ''
        st.info(f"Personen werden eingelesen")
        try:           
            df = pd.read_excel(filename)   
            
            s = df.to_json()
            # nach json und zurück um alle typen als string zu konvertieren
            # todo: geht ev. noch eleganter, aber ohne das werden Telnr als 7.98374646+10 geladen 
            df = pd.read_json(s)
            st.info('Import in DB wird gestartet.')
            ok, err_msg = db.append_pd_table(df, 'person_roh', [])
            if ok:
                sql = qry['synch_person_list']
                ok, err_msg = db.exec_non_query(db.conn,sql)
                if  ok:
                    st.balloons()
                    st.info(f"Adressen wurden in DB importiert und abgeglichen: {len(df)} Personen")
                else:
                    raise Exception(f"In der Abgleich-Prozedur ist ein Fehler aufgetreten: {err_msg}") 
            else:
                raise Exception(f"Beim Einlesen der Personen-Datei ist ein Fehler aufgetreten: {err_msg}") 
        except Exception as ex:
            st.warning(f"Beim Einlesen der Personen ist ein Problem aufgetreten: {ex}")
        return ok

    ok = True
    err_msg = ''
    st.set_option('deprecation.showfileUploaderEncoding', False)
    try:
        uploaded_file = BytesIO()
    except Exception as ex:
        st.warning(f"Personenliste konnte nicht geladen werden: {tools.error_message(ex)}")
        logger.warning(f"Personenliste konnte nicht geladen werden: {tools.error_message(ex)}")

    with st.expander('', expanded= False):
        st.markdown("""Hier können Personen geladen werden. Ziehe eine Excel Datei mit allen Personen in untenstehendes Feld.
Bereits in der Datenbank bestehende Personen werden aktualisiert (Identifikation mittels Emailadresse) neue Personen werden angefügt. Bei 
Personen, die auch ein Benutzerkonto haben sollen, muss das Feld Benutzer-Kürzel gefüllt sein.""")
    uploaded_file = st.file_uploader(f"Personen für Verteiler", type=['xlsx'])
        
    if uploaded_file:
        filename = './data/personen.xlsx'   # r'.\data\personen.xlsx'
        with open(filename, 'wb') as f: # Excel File
            f.write(uploaded_file.read()) 
    if st.button("Personenliste abgleichen") and uploaded_file:
        ok = synch_personen()


def import_test_data():
    """
    Auf dieser Seite wird der Upload gestartet
    """

    def save_file():
        filename = const.config['source_path'] + const.config['source_filename']
        ok = False    
        with open(filename, 'wb') as f: ## Excel File
            f.write(uploaded_file.read()) 
            st.info(f'Die Datei wurde gespeichert unter {filename}, der Import kann gestartet werden.')
            ok = True
        return ok

    def get_steps():
        if auto_import:
            steps = {'import': True, 'update': True, 'extern': True, 'plots': True,
                    'test_mail': True, 'test_sms': True, 'test_ogd_export': True}
        else:
            steps = {'import': True, 'update': False, 'extern': False, 'plots': False,
                'test_mail': False, 'test_sms': False, 'test_ogd_export': False}    
        return steps

    ok = True
    err_msg = ''
    st.set_option('deprecation.showfileUploaderEncoding', False)
    try:
        uploaded_file = BytesIO()
        uploaded_file = st.file_uploader(f"Excel Export Datei ({const.config['source_filename']})", type=['xlsx'])
        auto_import = st.checkbox('Import nach upload automatisch starten', True)
        if uploaded_file:
            if save_file(): 
                if st.button('Import Starten'):
                    st.info("Testdaten Import wird gestartet")
                    ok = run_selected_steps(get_steps())
        if not ok:
            raise Exception("") 
    except Exception as ex:
        st.warning(f"Beim Laden der Testdaten sind Fehler aufgetreten: {tools.error_message(ex)}")
        logger.warning(f"Beim Laden der Testdaten sind Fehler aufgetreten: {tools.error_message(ex)}")
    
    return ok
    

def is_prod_server()->bool:
    """
    Gibt zurück ob der aktuelle Appserver der prod-server ist. Ist dies der FAll, so wird z.B. das Testdaten file in ein
    test Archiv verschoben
    """

    return socket.gethostname().lower() == const.PROD_SERVER.lower()

def export_ogd(destination: str):
    """
    Exportiert verschiedene Views in das OGD Prod oder Testverzeichnis je nach gesetzter Destination
    Parameters:
    destination:    Zielverzeichnis
    """

    err_msg = ''

    # wenn der ausführende host nicht der prodserver ist, oder das develop flag explizit gesetzt ist
    # dann ogd-export immer nach test leiten
    if (not is_prod_server()) or (st.session_state.develop_flag==1):
        destination = const.config['export_csv_path_test']
    st.info(f'Prozess OGD Export wurde gestartet, Zielverzeichnis: {destination}')
    try:
        ok = [True] * len(const.ogd_exports.items())
        i = 0
        for key, value in const.ogd_exports.items():
            st.info(f"'{value['title']}' werden exportiert.")
            sql = value['sql']
            df, ok[i], err_msg = db.get_recordset(db.conn, sql)
            if ok[i]:
                # AgGrid(df, key=i)
                filename = destination + value['filename']
                df.to_csv(filename, sep=';', index=False)
            else:
                st.warning(f"Datei {value['filename']} konnte nicht auf {destination} exportiert werden: {err_msg}")
                logger.warning(f"Datei {value['filename']} konnte nicht nach {destination} exportiert werden: {err_msg}")
            i += 1
        if all(ok):
            st.info(f'OGD Dateien wurden erstellt und auf {destination} gespeichert.')
            if destination != const.config['export_csv_path_test']:
                mail_app.send_ogd_mail(success=True, err_msg='')
        else:
            ok[len(ok)-1]=False
            mail_app.send_ogd_mail(success=False, err_msg=err_msg)
        return all(ok)
        
    except Exception as ex:
        st.warning(f'Beim Export der OGD Dateien ist ein Problem aufgetreten: {repr(ex)}')
        if destination != const.config['export_csv_path_test']:
            mail_app.send_ogd_mail(success=False, err_msg=repr(ex))
    return all(ok)

def insert_today_record():
    """
    Fügt den heutigen Tag in die Tabelle Publikation_zeitreihe ein, falls er dort noch nicht 
    vorhanden ist.
    """

    ok = True
    err_msg = ''
    sql = qry['add_today_record']
    ok, err_msg = db.exec_non_query(db.conn, sql)
    if ok:
        logger.debug(f'Der heutige Record wurde leer erstellt')
    else:
        st.warning(f'Beim Erstellen des heutigen records ist ein PRoblem aufgetreten: {repr(ex)}')
    return ok

def run_selected_steps(steps):
    """
    Führt alle Schritte aus, die im dictonary steps übergeben werden.  
    """

    num_sel_steps = 0
    ok = [True] * 11 # externe dateien haben 2 steps
    import_ok = True
    err_msg = ''
    if insert_today_record():
        if steps['import']:
            import_ok = import_file()
            num_sel_steps +=1
        if import_ok and steps['extern']:
            ok[0] = get_bs_cases()
            ok[1] = get_bl_cases()
            ok[2] = get_ch_cases()
            ok[3] = get_vaccination_data_from_data_bs()
            ok[4] = get_re_werte()
            ok[5] = get_bag_daily_datasets()
            num_sel_steps +=1
        if import_ok and steps['update']:
            ok[6] = calculate_values()
            num_sel_steps +=1
        if import_ok and steps['plots']:
            ok[7] = make_plots()
            num_sel_steps +=1
        if import_ok and steps['test_mail']:
            ok[8] = mail_app.send_mail('test-mail')
            num_sel_steps +=1
        if import_ok and steps['test_sms']:
            ok[9] = mail_app.send_sms('test-sms')
            num_sel_steps +=1
        if import_ok and steps['test_ogd_export']:            
            ok[10] = export_ogd(destination=const.config['export_csv_path_test'])
            num_sel_steps +=1
        
        if num_sel_steps > 0:
            if all(ok):
                st.success('Alle selektierten Prozesse wurden erfolgreich ausgeführt')
            else:
                st.warning('Die Testdaten wurden importiert, bei den Folgeprozess-Schritten sind Fehler aufgetreten.')
                logger.warning('Die Testdaten wurden importiert, bei den Folgeprozess-Schritten sind Fehler aufgetreten.')
        else:
            st.info('Es sind keine Prozesse selektiert, es wurden keine Prozesse ausgeführt.')
        
        ok = (all(ok) and import_ok)
        if ok:
            st.balloons()
        return ok

def change_password():
    """
    Auf dieser Seite kann der eingeloggte User sein Passwort ändern.
    """

    ok = True
    err_msg = ''
    sql = qry['user_info'].format(st.session_state.user_name)
    df, ok, err_msg = db.get_recordset(db.conn, sql)
    if ok:
        row = df.iloc[0]
        form = st.form(key= 'pwd_form')
        with form:
            st.markdown(f'Benutzer: {row.nachname} {row.vorname}')
            pwd1 = st.text_input('Neues Passwort',type='password')
            pwd2 = st.text_input('Passwort bestätigen',type='password')
            if form.form_submit_button(label='Passwort ändern'): 
                if pwd1 == pwd2 and len(pwd1) > 0:
                    context = get_crypt_context()
                    sql = qry['change_pwd'].format(context.hash(pwd1), row['benutzer'])
                    ok, err_msg = db.exec_non_query(db.conn, sql)
                    text_placeholder = st.empty()
                    tools.display_temp_text(ok,"Passwort wurde erfolgreich geändert",
                        f"Das Passwort konnte leider nicht geändert werden, kontaktieren sie den technischen Support: {err_msg}.",
                        text_placeholder)
                else:
                    text_placeholder = st.empty()
                    tools.display_temp_text(False,"",
                        f"Passwörter stimmen nicht überein, versuchen sie es nochmals",
                        text_placeholder)
    else:
        st.warning(f"Es wurde kein User {st.session_state.user_name} in der Datenbank gefunden.")
        logger.warning(f"Es wurde kein User {st.session_state.user_name} in der Datenbank gefunden: {err_msg}")

def delete_person(person_id: int):
    """
    Löscht eine Person aus der Tabelle Person und falls Benutzer aus der Tabelle User.
    """

    ok = True
    err_msg = ''
    sql = qry['person_delete'].format(person_id)
    ok, err_msg = db.exec_non_query(db.conn, sql)
    if ok:
        st.info('Der Datensatz wurde erfolgreich gelöscht')
    else:
        st.warning('Der Datensatz konnte nicht gelöscht werden.')
        logger.warning(f'Der Datensatz {person_id} konnte nicht gelöscht werden: {err_msg}')

def show_person(person_dic: dict):
    """
    Personen können nicht editiert, nur angezeigt werden. Personendaten werden per Excel-Datei eingelesen und können
    nur über dieses mutiert werden.
    """

    ok = True
    err_msg = ''
    person_id = st.selectbox('Person auswählen:',  options=list(person_dic.keys()),
                   format_func=lambda x: person_dic[x])                   
    sql = qry['person_info'].format(person_id)

    person,ok,err_msg = db.get_recordset(db.conn, sql)
    if ok:
        person = person.iloc[0]

        person_str = f"""Nachname:\t{person['nachname']}\n 
Vorname:\t{person['vorname']}\n
Email:\t{person['email']}\n
Mobile:\t{person['mobile']}"""
        st.info(person_str)
        #ist_benutzer = 1 if st.checkbox('Ist Operator/in', value = (person['ist_benutzer'] == 1)) else 0
        
        #col1, col2, col3 = st.columns([0.1, 0.1, 0.5])
        
        #if col1.button('Speichern'):
        #    sql = qry['person_update'].format(nachname, vorname, email, mobile, ist_benutzer, person_id)
        #    if db.exec_non_query(db.conn, sql) == 1:
        #        st.info('Der Datensatz wurde erfolgreich gespeichert')
        #        st.experimental_rerun()
        #    else:
        ##        st.warning(f'Der Datensatz konnte nicht gespeichert werden.')
        #elif col2.button('Neu'):
        #    sql = qry['person_new']
        #    if db.exec_non_query(db.conn, sql) == 1:
        #        st.info('Es wurde eine neue Person angelegt')
        #        st.experimental_rerun()
        #    else:
        #        st.warning(f'Die Person konnte nicht angelegt werden.')
        if st.button('Person Löschen'):
            ok = delete_person(person_id)
    
def verteiler_speichern(verteiler_id: int, person_liste:list):
    """
    Speichert die Beziehung Person/Verteiler in der Tabelle person_verteiler_bez.
    """

    ok = True
    err_msg = ''
    sql = qry['verteiler_person_empty'].format(verteiler_id)
    ok, err_msg = db.exec_non_query(db.conn, sql) 
    if ok:
        all_ok = True
        for pers_id in person_liste:
            sql = qry['verteiler_person_insert'].format(pers_id, verteiler_id)
            ok, err_msg = db.exec_non_query(db.conn, sql) 
            all_ok = all_ok and ok
            if not ok:
                logger.warning(f"Person {pers_id} konnte nicht gespeichert werden")
        if all_ok:        
            st.info(f'Der Verteiler wurde gespeichert.')
        else:
            st.warning(f'Beim Speichern des Verteilers sind Fehler aufgetreten.')
    else:
        st.warning(f'Der Verteiler wurde refolgreich gespeichert.')


def show_verteiler_verwalten():
    """
    Zeigt eine Seite auf welcher der Verteiler im Excel Format per File Uploader in die Datenbank 
    geladen werden kann. Dabei werden sie automatisch den Verteilern zugewiesen und für PErsonen mit IT-Kürzeln wird
    ein Benutzer-record angelegt.
    """

    def get_personen_dic() -> dict:
        """
        Gibt ein dict von Personen zurück, der für die Selectbox im GUI verwendet wird
        """
        ok = True
        err_msg = ''
        sql = qry['person_list'].format(st.session_state.user_name)
        person_df, ok, err_msg = db.get_recordset(db.conn, sql)
        if ok:
            person_df = person_df.set_index('id')['name']
            person_dic = person_df.to_dict()
        else:
            logger.warning(f"Beim Erstellen der Personen Auswahlliste ist ein Fehler aufgetreten: {err_msg}")
            person_dic = {}
        return person_dic, ok

    def get_verteiler_dic():
        ok = True
        err_msg = ''
        sql = qry['lookup_code_list'].format(4)

        verteiler_df,ok,err_msg = db.get_recordset(db.conn, sql)
        if ok:
            verteiler_df = verteiler_df.set_index('id')['name']
            verteiler_dic = verteiler_df.to_dict()
        else:
            logger.warning(f"Beim Erstellen der Verteiler Auswahlliste ist ein Fehler aufgetreten: {err_msg}")
            verteiler_dic = {}
        return verteiler_dic, ok
        
    ok = True
    err_msg = ''
    sql = qry['person_all'].format(st.session_state.user_name)
    df, ok, err_msg = db.get_recordset(db.conn, sql)
    if ok:
        st.markdown("**Liste der im System erfassten Personen**")
        AgGrid(df)
        person_dic, ok = get_personen_dic()
        if ok:
            # Editieren/Inserten von Personen kann man wieder einfügen, wenn das nötig ist.
            show_person(person_dic)
            show_upload_personen()

    st.markdown('---')

    st.markdown('**Verteiler**')

    verteiler_dic, ok = get_verteiler_dic()
    if ok:
        verteiler = st.selectbox('Auswahl Verteiler',options=list(verteiler_dic.keys()),
                   format_func=lambda x: verteiler_dic[x])
    
    sql = qry['verteiler_person_bez'].format(verteiler)
    verteiler_pers_df, ok, err_msg =  db.get_recordset(db.conn, sql)
    if ok:
        verteiler_pers_list = verteiler_pers_df['person_id'].to_list()
        verteiler_person = st.multiselect(f'Personen zuweisen zu {verteiler_dic[verteiler]} ({len(verteiler_pers_list)})',options=list(person_dic.keys()),
                   format_func=lambda x: person_dic[x], default=verteiler_pers_list)  
        if st.button('Speichern', key='speichern_verteiler'):
            verteiler_speichern(verteiler, verteiler_person)


def plot(df):
    """
    Erstellt eine Zeitreihen-Grafik mit dem dataframe df. df muss eine Spalte Datum enthalten.
    """

    # fetch & enable German format & timeFormat locales.
    s = requests.get('https://raw.githubusercontent.com/d3/d3-format/master/locale/de-DE.json', proxies=const.PROXY_DICT).text
    de_format = json.loads(s)
    s = requests.get('https://raw.githubusercontent.com/d3/d3-time-format/master/locale/de-DE.json', proxies=const.PROXY_DICT).text
    de_time_format = json.loads(s)
    alt.renderers.set_embed_options(formatLocale=de_format, timeFormatLocale=de_time_format)

    # locale.setlocale(locale.LC_ALL, "de_CH")
    df['datum'] = df['datum'].apply(lambda x: 
        datetime.strptime(x,const.DATE_FORMAT_ENG))
    df['7-Tage Schnitt'] = '7-Tage Mittel'
    df['Neumeldungen'] = 'Neumeldungen'

    # calculate the 
    min_date = '2020-02-29'

    max_date = max(df['datum'].to_list()) 
    day=calendar.monthrange(max_date.year, max_date.month)[1]
    max_date = datetime(max_date.year,max_date.month,day) + timedelta(days=1)
    domain_pd = pd.to_datetime([min_date, max_date]).astype(int) / 10 ** 6
    today = datetime.now().strftime(const.DATE_FORMAT_LONG)

    line = alt.Chart(data=df, title='Covid Lagebericht App, Stand: ' + today).encode().mark_line().encode(
        x=alt.X('datum:T', axis=alt.Axis(title="",format="%b %y"), scale = alt.Scale(domain=list(domain_pd) )),
        y=alt.Y('value:Q', axis=alt.Axis(title="Anzahl Fälle")),
        tooltip=['datum', 'variable', 'value'],
        color=alt.Color('variable:N', legend=alt.Legend(title=""))
        )

    fig = (line).properties(width=1000).interactive()
    st.write(fig)


def show_werte_ueberpruefen():
    """
    Diese Seite erlaubt es dem User, alle Werte aus der Tabelle Zeitreihe_Publikation tabellarisch und graphisch zu überprüfen.
    """

    ok = True
    err_msg = ''
    
    def mutationen():
        st.markdown(f"#### Mutationen")
        sql = qry['mutationen_table']
        df, ok, err_msg = db.get_recordset(db.conn, sql)
        return df, pd.DataFrame()

    def zeitreihen():
        st.markdown(f"#### Zeitreihe")
        selected_fields  = st.multiselect('Auswahl Felder', const.FELDER_ZEITREIHE, default = const.FELDER_ZEITREIHE[:3])
        selected_fields_csv = ','.join(selected_fields)
        sql = qry['check_values_table'].format(selected_fields_csv)
        df, ok, err_msg = db.get_recordset(db.conn, sql)
        df_melted = pd.melt(df,id_vars=['datum'], value_vars=selected_fields)
        return df, df_melted

    def verstorbene():
        st.markdown(f"#### Verstorbene")
        sql = qry['verstorbene']    
        df, ok, err_msg  = db.get_recordset(db.conn, sql)
        return df, pd.DataFrame()

    def inzidenzen():
        st.markdown(f"#### Inzidenzen")
        selected_fields  = st.multiselect('Auswahl Inzidenz-Felder', const.FELDER_INZIDENZEN, default = const.FELDER_INZIDENZEN[:7])
        selected_fields_csv = ','.join(selected_fields)
        sql = qry['inzidenzen'].format(selected_fields_csv)
        df, ok, err_msg = db.get_recordset(db.conn, sql)
        df_melted = pd.melt(df,id_vars=['datum'], value_vars=selected_fields)
        return df, df_melted

    def reentry_faelle():
        """
        hier werden 2 Tabellen gezeigt: Einzeldaten
        """

        sql = qry['reentries_last_update']
        last_update, ok, err_msg  = db.get_value(db.conn, sql)
        st.markdown(f"#### Reentries")
        st.markdown(f"Personen, die weniger als 15 Tage nach Beginn der Quarantäne zu einem aktiven Fall wurden. Letzte Aktualisierung am {last_update}")
        # todo, LC: damit könnten sie die Aktualisierung selbst laufen lassen,  es kommen aber nur wenige REcords zurück, wie wenn die 
        # routine zu früh verlassen wurde.
        # if st.button("Daten aktualisieren"):
        #    sql = qry['update_reentries']    
        #    st.write(sql)
        #    ok, err_msg = db.exec_non_query(db.conn,sql)
        #    if ok:
        #        st.success("Die Reentries wurden erfolgreich mit den aktuellsten Daten berechnet ")
        #    else:
        #        st.warning(f"Beim Berechnen der Reentries ist ein Fehler aufgetreten, kontaktiere bitte den technischen Support {err_msg}")
        
        st.markdown('Einzeldaten')
        sql = qry['reentries']    
        df, ok, err_msg  = db.get_recordset(db.conn, sql)
        AgGrid(df)
        href = tools.download_link(df, 'werte.csv', f'Daten herunterladen ({len(df)} Datensätze)')
        st.markdown(href,unsafe_allow_html=True)

        st.markdown('Zusammenfassung nach Monat und Jahr')
        sql = qry['reentries_summary']    
        df, ok, err_msg  = db.get_recordset(db.conn, sql)
        AgGrid(df)
        href = tools.download_link(df, 'werte.csv', f'Daten herunterladen ({len(df)} Datensätze)')
        st.markdown(href,unsafe_allow_html=True)

        st.markdown('Anzahl Reentry-Fälle innerhalb eines definierten Zeitintervalls')
        col1, col2 = st.columns(2)
        von = col1.date_input('von Datum', datetime.now() - timedelta(30))
        bis = col2.date_input('bis Datum', datetime.now())
        sql = qry['reentries_intervall'].format(von, bis)    
        df, ok, err_msg  = db.get_recordset(db.conn, sql)
        return df, pd.DataFrame()

    def isolierte():
        st.markdown(f"### Isolierte")
        sql = qry['isolated']
        df, ok, err_msg = db.get_recordset(db.conn, sql)
        return df, pd.DataFrame()
    
    def kontaktpersonen():
        st.markdown(f"### Kontaktpersonen")
        sql = qry['quarantened']
        df, ok, err_msg = db.get_recordset(db.conn, sql)
        return df, pd.DataFrame()
    
    def impf_durchbrueche():
        st.markdown(f"### Impfdurchbrüche")
        st.markdown("Einzeldaten: alle Fälle, bei welchen ein Impfdatum oder ein Impfstoff eingetragen ist.")
        sql = qry['impf_durchbrueche_detail']
        df, ok, err_msg = db.get_recordset(db.conn, sql)
        AgGrid(df)
        href = tools.download_link(df, 'werte.csv', f'Daten herunterladen ({len(df)} Datensätze)')
        st.markdown(href, unsafe_allow_html=True)

        st.markdown('Zusammenfassung, nur Fälle mit definierter Anzahl Tage zwischen Impfung und Infektion')
        tage = st.number_input('Mindest Tage zwischen Impfung und Infektion', 0, 100, const.DEFAULT_TAGE_IMPFDURCHBRUCH, help=const.help_text['tage_impfdurchbruch'])
        sql = qry['impf_durchbrueche_summary'].format(tage)    
        df, ok, err_msg  = db.get_recordset(db.conn, sql)
        return df, pd.DataFrame()

    def find_zombies():
        st.markdown(f"### Zombie Fälle")
        sql = qry['find_zombies']
        df, ok, err_msg = db.get_recordset(db.conn, sql)
        if len(df)>0:
            st.markdown("Folgende Patienten haben den Status 'd' von gestern auf heute geändert, sie sind heute aktiv oder recovered.")
            zombies = ",".join(list(df['patient_id']))
            st.markdown(zombies)
            st.markdown("Willst du den Status dieser Patienten für heute wieder mit 'd' überschreiben?")
            if st.button("Ausführen"):
                sql = qry['undo_zombie']
                ok, err_msg = db.exec_non_query(db.conn, sql)
                text_placeholder = st.empty()
                tools.display_temp_text(ok, "Der gestrige Zustand 'gestorben' wurde erfolgreich für heute zurückgesetzt.", 
                    "Der gestrige Zustand 'gestorben' konnte nicht zurückgesetzt werden", text_placeholder)
                if ok:
                    st.markdown("""Nun musst du unter 'Prozesssteuerung manuell' den Schritt 'Zeitreihe erstellen' nochmals ausführen und auch das Testmail nochmals auslösen. 
Die Diskrepanz bei den Gestorbenen zum gestrigen Tag sollte dann nicht mehr auftreten. Bitte vergiss nicht, den Zustand auch im Fallerfassungssystem zu korrigieren.""")

        else:
            st.markdown("Es gibt keine Patienten, bei denen der Status 'd' seit gestern geändert wurde")
        return pd.DataFrame(), pd.DataFrame()

    lst_auswertungen = ['Mutationen', 'Zeitreihen', 'Verstorbene','Inzidenzen','Reentry Fälle', 
        'Isolierte', 'Kontaktpersonen', 'Impfdurchbrüche', 'Zombie-Fälle']
    menu_item = st.sidebar.selectbox("Auswertung", options=lst_auswertungen)
    if menu_item == lst_auswertungen[0]:
        df, plot_df = mutationen()
    if menu_item == lst_auswertungen[1]:
        df, plot_df = zeitreihen()
    if menu_item == lst_auswertungen[2]:
        df, plot_df = verstorbene()
    if menu_item == lst_auswertungen[3]:
        df, plot_df = inzidenzen()
    if menu_item == lst_auswertungen[4]:
        df, plot_df = reentry_faelle()
    if menu_item == lst_auswertungen[5]:
        df, plot_df = isolierte()
    if menu_item == lst_auswertungen[6]:
        df, plot_df = kontaktpersonen()
    if menu_item == lst_auswertungen[7]:
        df, plot_df = impf_durchbrueche()
    if menu_item == lst_auswertungen[8]:
        df, plot_df = find_zombies()

    if len(df) > 0:    
        AgGrid(df)
        href = tools.download_link(df, 'werte.csv', f'Daten herunterladen ({len(df)} Datensätze)')
        st.markdown(href,unsafe_allow_html=True)
    if len(plot_df)>0:
        plot(plot_df)


def menu_action():
    """
    Diese Funktion wird aufgerufen, wenn der User ein Menuitem auswählt
    """

    menu = st.sidebar.selectbox('Menu:',  options=const.MENU_OPTIONS)
    st.markdown(f'## {menu}')
    with st.expander('Anleitung', expanded= False):
        if menu == 'Werte erfassen':
            source_elsass = const.config['url_source_haut_rhin']
            source_loerrach = const.config['url_source_loerrach']
            text = const.MENU_DESC[menu].format(source_loerrach, source_elsass)
        else:
            text = const.MENU_DESC[menu]
        st.markdown(text, unsafe_allow_html=True)
    selected_steps = {}
    
    if menu == 'Info':
        show_summary()
    elif menu =='impfungen-neu':
        get_vaccination_data_from_data_bs()
    elif menu == 'Testdaten laden':
        import_test_data()
    elif menu == 'Prozesssteuerung manuell':
        selected_steps = get_steps()
    elif menu == 'Versand Lagebericht':
        publish_results()
    elif menu == 'Info Mail/SMS Versand':
        mail_app.send_info_mail()    
    elif menu == 'Konfiguration zeigen':
        show_configuration()
    elif menu == 'Werte erfassen':  
        edit_values()     
    elif menu == 'Konfiguration editieren':
        edit_config()
    elif menu == 'Passwort ändern':
        change_password()
    elif menu == 'Verteiler verwalten':
        show_verteiler_verwalten()
    elif menu == 'Werte überprüfen':
        show_werte_ueberpruefen()
    elif menu == 'Auswertungen':
        rep.conn = db.conn
        rep.show_reports()
    elif menu == 'BAG-Werte Einlesen':
        ok = get_re_werte()
    elif menu == 'test':
        mail_app.send_infection_source_report("testmail")
    
        
def get_crypt_context():
    return CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=50000
    )


def is_valid_password(usr: str, pwd: str)->bool:
    """
    Passwörter werden gehasht in der DB abgelegt
    """
    
    ok = True
    err_msg = ''
    context = get_crypt_context()
    sql = qry['get_usr_pwd'].format(usr)
    hashed_db_password, ok, err_msg = db.get_value(db.conn,sql)
    if ok:
        if hashed_db_password != const.ERROR_CODE and hashed_db_password != None:
            ok = context.verify(pwd, hashed_db_password)
        else:
            ok = False
    else:
        ok = False
    return ok

def reset_password():
    """
    Zeigt eine Seite, auf der der User sein Passwort zurücksetzen kann. Die App erzeugt eine Zufallszahl und verschickt diese
    per mail an den User (email ist hinterlegt). Anschliessend hasht sie die Zahl und legt sie im Passwortfeld unter dem Userrecord ab.
    """

    ok = True
    err_msg = ''
    logger.debug("Reset Passwort Seite wird gezeigt")
    sql = qry['user_info'].format(st.session_state.user_name)
    df, ok, err_msg = db.get_recordset(db.conn,sql)
    if ok and len(df) > 0:
        mailadresse = df.iloc[0]['email']
        begruessung = df.iloc[0]['begruessung']
        subject = 'Das Passwort für die Covid-19 Lagebericht App wurde zurückgesetzt'
        pwd_neu = '{:07d}'.format(random.randint(0, 999999))
        context = get_crypt_context()
        sql = qry['change_pwd'].format(context.hash(pwd_neu), st.session_state.user_name)
        ok, err_msg = db.exec_non_query(db.conn, sql)
        if ok:
            if db.exec_non_query(db.conn, sql):
                text = f"""{begruessung},<br>Dein Passwort wurde zurückgesetzt auf <br><b>{pwd_neu}</b><br>
                Bitte verwende nach dem ersten Login die Option `Passwort zurücksetzen` und setze dein eigenes Passwort.
                """
                sql = qry['send_reset_mail'].format(mailadresse,subject,text)                
                ok, err_msg = db.exec_non_query(db.conn, sql)
                if ok:
                    text = f"""{begruessung},<br>dein neues Passwort wurde an deine Mailadresse ({mailadresse}) geschickt. Bitte verwende nach dem ersten Login die
                    Menuoption `Passwort ändern`."""
                    st.markdown(text, unsafe_allow_html=True)
        else:
            st.warning('Beim reset des Passwortes gab es Probleme, kontaktieren sie bitte den Systemadministrator')
    else:
        st.warning('Achte darauf, dass im Feld Benutzername dein Benutzerkürzel steht, z.B. sghxyz')

def log_entry(prozess_typ_id, result_id, fehlermeldung):
    """
    Macht einen Eintrag in die Tabelle Lagebericht. In Fällen, wo der gesamte Prozess über eine SQL-Server stored procedure läuft
    wird der logeintrag über die stored procedure ausgeführt, da diese besser weiss, ob der Prozess richtig abgelaufen ist.
    
    Parameters:
    prozess_typ_id: Prozess-Id, siehe const.PROCESS dict
    result_id       Erfolg oder Error
    fehlermeldung:  Fehlermeldung
    """
    
    ok = True
    err_msg = ''
    cmd = qry["log_entry"].format(prozess_typ_id, st.session_state.user_name, result_id, fehlermeldung)
    ok, err_msg = db.exec_non_query(db.conn,cmd)
    if not ok:
        logger.warning(f"DB-Logeintrag konnte nicht angefügt werden. {err_msg}")


def show_login():
    """
    Zeigt die Login Maske mit den Feldern user/passwort
    """

    ok = True
    err_msg = ''
    logger.debug("Zeigt Login Maske")
    st.markdown('## Login')
    st.session_state.user_name = st.text_input('Benutzername', value = st.session_state.user_name)
    st.session_state.pwd = st.text_input('Passwort', value=st.session_state.pwd, type='password')
    col1, col2 = st.columns((1,12))
    
    if col1.button('Login'):
        if is_valid_password(st.session_state.user_name, st.session_state.pwd):
            logger.debug(f"User {st.session_state.user_name} hat richtiges Passwort eingegegeben")
            st.info('Willkommen beim Covid-Mailgenerator')
            st.session_state.logged_in = True
            sql = qry['user_info'].format(st.session_state.user_name)
            df, ok, err_msg = db.get_recordset(db.conn, sql)
            if ok:
                st.session_state.email = df.iloc[0]['email']
                st.session_state.mobile = df.iloc[0]['mobile']
                st.session_state.user = df.iloc[0]['benutzer']
                log_entry(const.PROCESS['login'], const.RESULT_SUCCESS, '')
            else:
                logger.warning(f"Beim Lesen des User-Info Records ist ein Fehler aufgetreten: {err_msg}")
            st.experimental_rerun()
        else:
            warning = 'Benutzername oder Passwort stimmen nicht'
            logger.warning("User {st.session_state.user_name} hat falsches Passwort eingegegeben")
            log_entry(const.PROCESS['login'], const.RESULT_ERROR, warning)
            st.warning(warning)
    if col2.button('Passwort zurücksetzen'):
        logger.info("User {st.session_state.user_name} hat Passwort zurücksetzen geklickt")
        reset_password()


def display_app_info():
    """
    Zeigt die Applikations-Infos sowie Kontaktdaten bei Fragen in einer Info-box in der sidebar an.
    """

    #logger.debug("zeigt App Info an")
    logged_in_user = f"Benutzer: {st.session_state.user_name if st.session_state.user_name > '' else ''}<br>"
    server_name, ok, err_msg = db.get_server_name(db.conn)
    develop_text = """<b><span style="color:red">Mode=DEVELOP!</span><b>"""
    develop_info = develop_text if st.session_state.develop_flag == 1 else ''
    text = f"""
    <style>
        #appinfo {{
        font-size: 11px;
        background-color: lightblue;
        padding-top: 10px;
        padding-right: 10px;
        padding-bottom: 10px;
        padding-left: 10px;
        border-radius: 10px;
    }}
    </style>
    <div id ="appinfo">
    App-Version: {__version__} ({version_date})<br>
    Implementierung App: Statistisches Amt Basel-Stadt<br>
    DB-Server: {server_name}<br>{logged_in_user}
    Kontakt:<br>
    - <a href="{const.config['kontakt_fachlich']}">bei fachlichen Fragen</a><br>
    - <a href="{const.config['kontakt_technisch']}">bei technischen Fragen</a><br>
    {develop_info}</div>
    """
    st.sidebar.markdown(text, unsafe_allow_html=True)


def display_help():
    """
    Zeigt ein Hilfedokument an
    todo: add help
    """

    pass #st.sidebar.markdown(f"### [📘]({const.URL_ANLEITUNG})")


def init_logger():
    """
    Initialisiert das Logger Objekt
    """
    global logger

    # setzt logging level für 
    logging_level = logging.INFO if socket.gethostname().lower() == const.PROD_SERVER.lower() else logging.DEBUG
    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M")
    file_handler = logging.FileHandler(f"{my_name}.log", "w", encoding = "UTF-8")
    file_handler.setFormatter(formatter)
    logger = logging.getLogger(f'{my_name}-logger')
    logger.addHandler(file_handler)
    logger.setLevel(logging_level)


def display_news():
    """
    Wenn ein Konfig-Parameter 'startup_info' erfasst wurde, gib den Text als Infostring aus.
    """
    user_info = const.config['startup_info']
    if not user_info in ('None',''):
        st.info(user_info)


def main():
    """
    Initialisiert das Session state Objekt und führt die Streamlit Applikation aus.
    """
    @st.experimental_memo()
    def get_lottie():
        ok=True
        r=''
        try:
            r = requests.get(LOTTIE_URL, proxies=const.PROXY_DICT).json()
        except:
            ok = False
        return r,ok
    
    def get_develop_flag():
        """
        Develop_flag kann an Prozeduren wie Mailversand oder smsversand übergeben werden und schickt dann die mails/smsm 
        nur an den entwickler. auch an anderen Stellen im Code können verschiedene Aktionen verhindert werden, die während dem 
        development nicht gewünscht sind.
        """
        flag = 1 if (app_server not in [const.PROD_SERVER, const.TEST_SERVER]) and (const.FORCE_PROD == 0) else 0
        return flag

    
    def init_app():
        st.set_page_config(
            page_title="COVID-19 Lagebericht",
            page_icon="📧",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        db.conn, ok, err_msg = db.get_connection(db_server, const.DATABASE)
        if ok:
            const.df_config, const.config, ok = get_config()
            display_news()
            if not('user_name' in st.session_state):
                st.session_state.user_name=''
                st.session_state.pwd = ''
                st.session_state.logged_in = False
                st.session_state.develop_flag = get_develop_flag()
            
            st.markdown(STYLE, unsafe_allow_html=True)
            lottie_search_names, ok = get_lottie()
            with st.sidebar:
                st_lottie(lottie_search_names, height=60, loop=20)
            st.sidebar.markdown(f"### {my_emoji} {my_name}")
        
        return ok, err_msg

    ok, err_msg = init_app()
    if ok:
        if st.session_state.logged_in:
            menu_action()
        else:
            show_login()
        display_app_info() 
        display_help()
    else:
        st.error(f'Es konnte keine Verbindung zur Datenbank {db_server}.{const.DATABASE} aufgebaut werden:{err_msg}')

if __name__ == '__main__':
    init_logger()
    locale.setlocale(locale.LC_ALL, 'deu_deu')
    logger.info(f"{my_name}-Prozess gestartet, server: {db_server}")
    main()