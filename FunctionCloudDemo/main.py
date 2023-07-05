import datetime
import logging

import azure.functions as func
import logging
from datetime import datetime,timedelta, date, timezone
# import configparser 
import psycopg2
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import re
import io
import pandas as pd
import psycopg2.extras as extras


def execute_values(conn, df, table):
  
    tuples = [tuple(x) for x in df.to_numpy()]
  
    cols = ','.join(list(df.columns))
    # SQL query to execute
    query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
    cursor = conn.cursor()
    try:
        extras.execute_values(cursor, query, tuples)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    print("the dataframe is inserted")
    cursor.close()

def lambda_handler():
    # TODO implement
    # config = configparser.ConfigParser()
    # config.read('config.cfg')
    # KEY = config.get('Blob','KEY')
    # accounturl = config.get('Blob','accounturl')
    KEY = 'xxxxx'
    accounturl = 'xxxxx' 
    # accsss to blob storage
    blob_service_client = BlobServiceClient(account_url=accounturl, credential=KEY)

    # see blobs in container
    filelist = blob_service_client.get_container_client('shipmentlist').list_blobs()

# extract file name with specific regular expression that include versandliste_ digits and end with .xls

    list2 = []  # include only files with specific regular expression (required files)
    for i in filelist:
    # begin with versandliste_ numbers or spaces and end with .xls
        if re.match(r'Versandliste_[0-9 _]+.xls', i.name):
            list2.append(i.name)
#extract date from list of strings and convert to datetime format
    list4 = []
    for i in list2:
        try:
            list4.append(datetime.strptime(i.split('_')[1], '%Y %m %d'))
        except:
            list4.append(datetime.strptime(i.split('_')[1], '%Y%m%d'))

    # connect to database
    # host = config.get('Postgres','host')
    # port = config.get('Postgres','port')
    # database = config.get('Postgres','database')
    # username = config.get('Postgres','username')
    # password = config.get('Postgres','password')
    host = 'xxx'
    port =  5432
    database = 'xxx'
    username = 'xxxx'
    password = 'xxxx'


    conn = psycopg2.connect(
        database=database, user=username, password=password, host=host, port= port
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # fetch last date from our database
    cursor.execute(
        """
        SELECT value 
        FROM "Keypairs" u
        WHERE u.key = %s;
        """,
        ['last_date',]
    )
    res = cursor.fetchall()
    last_date = res[0][0]
    last_date = datetime.strptime(last_date,'%Y-%m-%d')
    logging.info('last_date: %s', last_date)
    # find new files 
    requried_files = []
    for i in range(1,len(list4)):
        if list4[i] > last_date:
            requried_files.append(list2[i])

    if(len(requried_files) == 0):
        print("No new files")
        return 0
    else:
        df = pd.read_excel(io.BytesIO(blob_service_client.get_blob_client('shipmentlist',requried_files[0]).download_blob().readall()),skiprows=5)
        df = df.dropna(subset=['ID'])
        df['trackinglinks'] = df[df.columns[df.columns.str.match(r'Trackinglink\d+')]].apply(
            lambda x: ','.join(x.dropna().astype(str)),
            axis=1
        )
        # drop columns that contain trackinglinks
        df = df.loc[:,df.columns.str.match(r'Trackinglink\d+') == False]

    # join files if there are more than one file
    for i in range(1,len(requried_files)):
        df2 = pd.read_excel(io.BytesIO(blob_service_client.get_blob_client('shipmentlist',requried_files[i]).download_blob().readall()),skiprows=5)
        df2 = df2.dropna(subset=['ID'])
        df2['trackinglinks'] = df2[df2.columns[df2.columns.str.match(r'Trackinglink\d+')]].apply(
            lambda x: ','.join(x.dropna().astype(str)),
            axis=1
        )
        # drop columns that contain trackinglinks
        df2 = df2.loc[:,df2.columns.str.match(r'Trackinglink\d+') == False]
        df = pd.concat([df,df2],ignore_index=True)

    # clean data 
    df.columns= ['ID', 'Artikelnummer', 'Größe', 'Charge', 'PorticAartikelNummer','Gewicht', 'Höhe', 'Breite', 'Tiefe', 'Volumen', 'Lager', 'ArtikelBezeichnung', 'VKE', 'Menge', 'Einzel_VK_Netto', 'Gesamt_VK_Netto', 'LieferscheinNummer', 'RS_Nr', 'LieferscheinDatum', 'Waagedatum', 'Packanteil', 'AuftragsNummer', 'Bestelldatum', 'AngebotsBezeichnung', 'EMail_Besteller', 'KundennummerRechnung', 'KundennummerLieferung', 'Lieferempfänger', 'Lieferstr', \
                'Liefer_PLZ', 'Lieferort', 'Lieferland', 'NichtEU', 'Bestellweg','trackinglinks']

    # casting varialbes to correct data type
    df['Waagedatum'] = pd.to_datetime(df['Waagedatum'], format='%d.%m.%Y')
    df['LieferscheinDatum'] = pd.to_datetime(df['LieferscheinDatum'], format='%d.%m.%Y')
    df['Bestelldatum'] = pd.to_datetime(df['Bestelldatum'], format='%d.%m.%Y')
    # conver Artikelnummer to integer
    df['ID'] = df['ID'].astype(int)
    df['KundennummerRechnung'] = df['KundennummerRechnung'].astype(int)
    df['KundennummerLieferung'] = df['KundennummerLieferung'].astype(int)
    df['LieferscheinNummer'] = df['LieferscheinNummer'].astype(int)
    df['Menge'] = df['Menge'].astype(int)
    df['VKE'] = df['VKE'].astype(int)
    df = df.drop('ID',axis=1) # drop ID column because it is not required,serial in our data base
    execute_values(conn, df, 'versandliste')
    # df_fact = df[['Artikelnummer','ArtikelBezeichnung','VKE','Menge','Einzel_VK_Netto','Gesamt_VK_Netto','LieferscheinDatum','KundennummerRechnung','KundennummerLieferung','Lieferempfänger','Lieferstr','Liefer_PLZ','Lieferort','Lieferland','NichtEU']]
    # execute_values(conn, df_fact, 'versandliste_fact')
    # find max date in new files 
    max_date = df['Waagedatum'].max()
    max_date = max_date.strftime('%Y-%m-%d')
    cursor.execute(
    """
    Update "Keypairs" u
    set value = %s
    WHERE u.key = 'last_date';
    """,
    [max_date]
    )
def hello_world(request):
   
    print('begin work')
    lambda_handler()


