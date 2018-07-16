import os, csv, re
import subprocess
from collections import namedtuple
from zipfile import ZipFile as zip
from pg.pgbasics import *

class Extracteur(PgOutils):
        
    SCHEMA_EXTRACTION = 'ff_{0}_{1}'
    SCHEMA_FF = 'ff_d{0}_{1}'
    TABLES_FF = ['d{0}_{1}_proprietaire_droit',
                 'd{0}_{1}_fantoir_commune',
                 'd{0}_{1}_fantoir_voie',
                 'd{0}_{1}_lotslocaux',
                 'd{0}_{1}_pb30_pevexoneration',
                 'd{0}_{1}_pb36_pevtaxation',
                 'd{0}_{1}_pb40_pevprincipale',
                 'd{0}_{1}_pb50_pevprofessionnelle',
                 'd{0}_{1}_pb60_pevdependance',
                 'd{0}_{1}_pdl10_pdl',
                 'd{0}_{1}_pdl20_parcellecomposante',
                 'd{0}_{1}_pdl30_lots',
                 'd{0}_{1}_re00',
                 'd{0}_{1}_pnb21_suf',
                 'd{0}_{1}_pnb30_sufexoneration',
                 'd{0}_{1}_pnb36_suftaxation',
                 'd{0}_{1}_pb21_pev',
                 'd{0}_{1}_pb0010_local',
                 'd{0}_{1}_pnb10_parcelle']
    
    def __init__(self, hote=None, base=None, port=None, utilisateur=None, mdp=None, millesime=2016, perimetre='tmp', liste_idcom=None, chemin=None):
        super().__init__(hote, base, port, utilisateur, mdp)
        self.hote = hote
        self.base = base
        self.utilisateur = utilisateur
        self.mdp = mdp
        self.millesime = millesime
        self.perimetre = perimetre
        self.chemin = chemin
        self.communes = Communes(liste_idcom)
        
    @property    
    def schema(self):
        return self.SCHEMA_EXTRACTION.format(self.perimetre, str(self.millesime))
    
    @property
    def chemin_dump(self):
        return os.path.join(self.chemin, '{0}.sql'.format(self.schema))
    
    def table_extract(self, table):
        return table.split('_', 2)[2]
    
    @property
    def arborescence_ff(self):
        arborescence = {}
        for departement in self.communes.departements_associes:
            schema_dep = self.SCHEMA_FF.format(departement, str(self.millesime))
            tables_references_ff = [table.format(departement, str(self.millesime)) for table in self.TABLES_FF]
            if schema_dep in self.lister_schemas():
                tables_existantes = self.lister_tables(schema_dep)
                arborescence[(schema_dep, departement)] = list(set(tables_existantes).intersection(tables_references_ff))
        print(arborescence)
        return arborescence
    
    def creation_schema_extraction(self):
        #if not self.schema in self.lister_schemas():
        success, _ = self.creer_schema_si_inexistant(self.schema)
        if not success:
            return False, 'Impossible de créer le schéma {0}'.format(self.schema)
        #else:
            #return False, 'Le schéma {0} est déjà présent dans la base'. format(self.schema)
        return True, 'Création schéma extraction réussie'
    
    def creation_tables_vides(self):
        tables_crees = []
        for schema, tables in self.arborescence_ff.items():
            if len(tables) > 0:
                for table in tables:
                    if not self.table_extract(table) in tables_crees:
                        success, _ = self.creer_table_vide(self.schema, self.table_extract(table), schema[0], table)
                        tables_crees.append(self.table_extract(table))
                        print(tables_crees)
                        if not success:
                            return False, 'Erreur lors de la création des tables vides'
        return True, 'Création des tables vides réussie'
    
    def insertion_donnees(self):
        for schema, tables in self.arborescence_ff.items():
            departement = schema[1]
            communes_dep = self.communes.get(departement=departement)
            for table in tables:
                success, _ = self.inserer_donnees_communales(self.schema, self.table_extract(table), schema[0], table, communes_dep)
                if not success:
                    return False, "Erreur lors de l'insertion des données"
        return True, 'Insertion des données réussie'
    
    def dumper(self):
        export = ExportDump(self.hote, self.utilisateur, self.base, self.mdp, self.schema)
        
        if not export.test_pg_dump():
            return False, "La commande pg_dump n'a pas été trouvée"        
        try:
            export.dump(self.chemin_dump)
            self.effacer_schema(self.schema)
            return True, 'Dump réussi'
        except Exception as e:
            print(e)
            self.effacer_schema(self.schema)
            return False, 'Erreur lors de la création du dump'
        
#         A FINIR POUR V2
#     def zipper(self):
#         compress = Compresseur(self.chemin_dump)
#         try:
#             compress.zipper_interne()
#             return True, 'Compression des données effectuée'
#         except Exception as e:
#             print(e)
#             return False, "Erreur lors de la compression des données extraites"
#         
                
    @requete_sql
    def creer_table_vide(self, schema_final, table_finale, schema_ini, table_ini):
        pass
    
    @requete_sql_avec_modification_args
    def inserer_donnees_communales(self, schema_final, table_finale, schema_ini, table_ini, communes):
        return schema_final, table_finale, schema_ini, table_ini, "', '".join(communes).upper()
                                    

class Communes:
    
    def __init__(self, liste_idcom):
        self.communes = liste_idcom
        print(self.communes)   
    
    @classmethod    
    def departement(cls, commune):
        return commune[:3] if commune[:2]=='97' else commune[:2]
         
    @property    
    def departements_associes(self):
        deps = []
        for commune in self.communes:
            dep = Communes.departement(commune)
            if dep not in deps:
                deps.append(dep)
        return deps

    def get(self, departement=None):
        return [commune for commune in self.communes if commune.startswith(departement)]


class ExportDump:
    
    def __init__(self, hote, utilisateur, base, mdp, schema):
        self.hote = hote
        self.utilisateur = utilisateur
        self.base = base
        self.mdp = mdp
        self.schema = schema
    
    def test_pg_dump(self):
        cmd = ['pg_dump', '--version']
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if p.returncode == 0 and p.stdout.startswith('pg_dump'):
            print('OK')
            return True
        return False    
    
    def dump(self, chemin_dump):
        commande = 'pg_dump -v -x -O -n {0} -f {1} -h {2} -U {3} {4}'.format(self.schema, chemin_dump, self.hote, self.utilisateur, self.base)
        os.system(commande)
        
# A FINIR POUR V2
# class Compresseur:
#     
#     def __init__(self, chemin_dump):
#         self.chemin_dump = chemin_dump
#         self.chemin_dest = self.chemin_dump.replace('sql','zip')
#         
#     def zipper_interne(self):
#         """
#         zippe une source depuis une cible vers une destination avec le module zipfile interne à python
#         """
#         # attention utiliser os.chdir(chemin) pour changer l'origine d'éxecution du script de compression afin d'avoir un zip sans arborescence complète
#         os.chdir(self.chemin_dest)
#         with zip(self.chemin_dest,'w', compression=14) as myzipfile:
#             myzipfile.write(self.chemin_dump)
#         os.remove(self.chemin_dump)
#         
        
            
     
    
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
            return None, "Les codes Insee spécifiés dans le fichier communal ne sont pas conformes ou aucun code insee n'a été trouvé."
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
    if len(communes) == 0:
        return False
    pattern = re.compile(r'[0-9][0-9aAbB][0-9]{3}')
    for item in communes:
        if pattern.match(item):
            return True
        return False
           
    
def zipper_interne(source,dest):
    """
    zippe une source depuis une cible vers une destination avec le module zipfile interne à python
    """
    # attention utiliser os.chdir(chemin) pour changer l'origine d'éxecution du script de compression afin d'avoir un zip sans arborescence complète
    with zip(dest,'w', compression=14) as myzipfile:
        myzipfile.write(source)
        
def test_pg_dump():
    """
    permet de tester la présence de pg_dump sur le poste et s'il est directement accéssible par le script
    à savoir s'il est dans le PATH de windows par exemple
    """
    cmd = ['pg_dump', '--version']
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if p.returncode == 0 and p.stdout.startswith('pg_dump'):
            return True
    except Exception as e:
        print(e)
        return False
   
    
def test_schema_a_creer(host, base, user, password, perimetre, liste_idcom, millesime, chemin):
    """
    permet de tester la présence du schema qui va être créer par l'application
    en fonction du nom de périmètre qui aura été entré dans le formulaire
    """
    params = {'hote':host, 'base':base, 'port':'5432','utilisateur':user,'motdepasse':password}
    pgoutils = PgOutils(**params)
    liste_schemas = pgoutils.lister_schemas()
    schema_ext = ['ff_{0}_{1}'.format(perimetre, millesime),]
    if schema_ext in liste_schemas:
        msg = "le schéma d'extraction qui devrait être créé existe déjà, merci de le supprimer ou de changer le nom du périmètre..."
        print(msg)
        return False, msg
    return True, "schéma d'extraction non-préexistant"
        
   
def extract_fonction_unique(host, base, user, password, perimetre, liste_idcom, millesime, chemin):
    params = {'hote':host, 
              'base':base, 
              'port':'5432',
              'utilisateur':user,
              'motdepasse':password,
              'millesime': millesime,
              'perimetre': perimetre,
              'liste_idcom': liste_idcom}
    extracteur = Extracteur(**params)
    success, msg = extracteur.creation_schema_extraction()
    if not success:
        return msg
    success, _ = extracteur.creation_tables_vides()
    if not success:
        return msg
    success, msg = extracteur.insertion_donnees()
    if not success:
        return msg
    success, _ = extracteur.dumper('{0}/{1}.sql'.format(chemin, extracteur.schema))
    if not success:
        return msg
    zipper_interne('{0}/{1}.sql'.format(chemin, extracteur.schema), '{0}/{1}.7z'.format(chemin, extracteur.schema))
    os.remove('{0}/{1}.sql'.format(chemin, extracteur.schema)) 
    print('TRAVAIL TERMINE ;p')
    return True

