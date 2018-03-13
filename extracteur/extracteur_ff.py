'''
Created on 28 nov. 2017

@author: jerome.guillaume

Module de tests pour les fonctions à utiliser dans l'extracteur ff django
test script pour extraire les tables principales des Fichiers fonciers en format
postgreSQL / PostGIS sur un périmètre type liste de communes (code insee en csv)
le script posera plusieurs questions:
- la liste de code insee en entrée
- le nom du champ contenant les codes insee dans le csv
- le nom du périmètre
- le millésime
- l'emplacement de l'extraction (sous forme de répertoire)
'''

from pg.pgbasics import PgOutils
from collections import namedtuple
import os, csv
from zipfile import ZipFile as zip


TABLES_FF = ['propro',
             'fzegz']
 
def schema_ff(millesime, departement):
    return 'ff_d{0}_{1}'.format(departement, millesime)
 
def table_final(table):
    return table.split('_', 2)[2]

def departements(communes):
    departements = []
    for commune in communes:
        if departement(commune) not in departements:
            departements.append(departement(commune))
    return departements

def departement(commune):
    return commune[:3] if commune[:2]=='97' else commune[:2]

def inserer_donnees(communes, millesime, perimetre, tables, pgoutils):
    for commune in communes:
        for table in tables:
            data = {'schema_source': schema_ff(millesime, departement(commune)),
                    'table_source':'d{2}_{1}_{0}'.format(table_final(table),millesime, departement(commune)),
                    'code_insee':commune,
                    'schema_dest':'ff_{0}_{1}'.format(perimetre, millesime),
                    'table_dest':table_final(table)}
            sql = '''INSERT INTO  {schema_dest}.{table_dest} SELECT * FROM {schema_source}.{table_source} WHERE idcom = '{code_insee}';'''.format(**data)
            pgoutils.execution(sql, 1)
    print('insertion des données effectuée')
    
def creation_schema_extraction(perimetre,millesime, pgoutils):
    pgoutils.effacer_et_creer_schema('ff_{0}_{1}'.format(perimetre, millesime))
    print('schéma d''extraction créé')
    
def creation_tables_vides_in_schemas_extraction(perimetre, millesime, communes, schema_dest, pgoutils):
    '''lister tables présentes dans le schéma origine
    et les copier vides dans le schémas d'extractions
    '''
    dep = departements(communes)[0]
    print(dep)
    schema_modele = 'ff_d{0}_{1}'.format(dep,millesime)
    print(schema_modele)
    tables = pgoutils.lister_tables(schema_modele)
    for table in tables:
        sql= '''CREATE TABLE {0}.{1} AS SELECT * FROM {3}.{2} WITH NO DATA;'''.format(schema_dest, table_final(table), table, schema_modele)
        pgoutils.execution(sql, 1)
    return tables
     
def export_schema_sql(schema_dest, chemin_sauvegarde, pgoutils, host, user, base):
    command = 'pg_dump -v -x -O -n {0} -f {1} -h {2} -U {3} {4}'.format(schema_dest, chemin_sauvegarde, host, user, base)
    print(command)
    print('travail en cours...')
    os.system(command)
    print('suppression du schéma d''extraction après sauvegarde')
    sql= '''
    drop schema if exists {0} cascade;
    '''.format(schema_dest)
    pgoutils.execution(sql, 1)
    print('export sql et suppression schema extraction effectués')
    
def lister_codes_communes(fichier_liste, chp_idcom):
    """fonction permettant la création d'une liste de code insee depuis un csv
    """    
    try :
        liste_codes_commune = [] 
        with open(fichier_liste, newline = '', encoding = 'UTF-8') as f:
            reader = csv.reader(f)
            champs = ",".join(next(reader))
            Headers = namedtuple('Headers', champs)
            for header in map(Headers._make, reader):
                liste_codes_commune.append(getattr(header, chp_idcom))# getattr(header, chp_idcom) <-> header.idcom
        if not verif_idcom(liste_codes_commune):
            return None, "Les codes Insee spécifiés dans le fichier communal ne sont pas conformes."
        return liste_codes_commune, None
    except FileNotFoundError as e:
        print(e)
        return None, "Fichier communal non trouvé"
    except AttributeError as e:
        print(e)
        return None, "Le fichier spécifié n'a pas d'attribut 'idcom'."
    except Exception as e:
        print(e)
        return None, e
        
def  verif_idcom(communes):
    """
    Fonction qui vérifie que les idcom de la liste sont des codes Insee correct
    """
    return True
    

def zipper(source,dest):
    """
    zippe une source depuis une cible vers une destination
    """
    commande = "7z a -y -r %s %s" %(dest,source)
    os.system(commande)
    
def zipper_interne(source,dest):
    """
    zippe une source depuis une cible vers une destination avc lemodul zipfile interne à python
    """
    with zip(dest,'w', compression=14) as myzipfile:
        myzipfile.write(source)
    

def extract_fonction_unique(host, base, user, password, perimetre, liste_idcom, millesime, chemin):
    params = {'hote':host, 'base':base, 'port':'5432','utilisateur':user,'motdepasse':password}
    pgoutils = PgOutils(**params)
    dpts = departements(liste_idcom)
    print('détermination des départements du périmètre...OK')
    schema_dest='ff_{0}_{1}'.format(perimetre, millesime)
    creation_schema_extraction(perimetre, millesime, pgoutils)
    print('création du schéma d''accueil des données à extraire...OK') 
    tables = creation_tables_vides_in_schemas_extraction(perimetre, millesime, dpts, schema_dest, pgoutils)
    print('création des tables vides à partir du schéma départemntal d''origine...OK')
    inserer_donnees(liste_idcom, millesime, perimetre, tables, pgoutils)
    print('insertion des données dans les tables en fonction de la liste d''idcom...OK')
    export_schema_sql(schema_dest, '{0}{1}.sql'.format(chemin, schema_dest), pgoutils, host, user, base)
    print('extraction au format sql du schéma alimenté...OK')
    print('début de compression...')
    zipper_interne('{0}{1}.sql'.format(chemin, schema_dest), '{0}{1}.7z'.format(chemin, schema_dest))
    print('compression du fichier sql...OK')
    os.remove('{0}{1}.sql'.format(chemin, schema_dest)) 
    print('suppression du fichier sql après compression...OK')
    print('TRAVAIL TERMINE ;p')
    return True


    
    
    