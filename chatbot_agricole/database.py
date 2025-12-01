import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import os

class DatabaseManager:
    """Gestionnaire de base de données pour l'application d'agriculture"""
    
    def __init__(self, db_path: str = 'agriculture_burkina.db'):
        """Initialise la connexion à la base de données"""
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self):
        """Établit une connexion à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par leur nom
        return conn
    
    def _init_db(self):
        """Initialise les tables de la base de données"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table des cultures
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cultures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    nom_scientifique TEXT,
                    type_culture TEXT NOT NULL,  # fruit, légume, céréale, etc.
                    description TEXT,
                    peut_cultiver_burkina BOOLEAN NOT NULL DEFAULT 1,
                    raison_non_culture TEXT,
                    besoins_eau TEXT,  # Faible, Modéré, Élevé
                    type_sol TEXT,  # JSON array des types de sols
                    conditions_climatiques TEXT,  # JSON array
                    conseils_generaux TEXT,  # JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(nom)
                )
            ''')
            
            # Table des variétés
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS varietes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    culture_id INTEGER NOT NULL,
                    nom TEXT NOT NULL,
                    description TEXT,
                    duree_cycle_jours INTEGER,
                    rendement_attendu TEXT,
                    resistance_maladies TEXT,  # JSON array
                    FOREIGN KEY (culture_id) REFERENCES cultures(id) ON DELETE CASCADE,
                    UNIQUE(culture_id, nom)
                )
            ''')
            
            # Table des périodes de plantation
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS periodes_plantation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    culture_id INTEGER NOT NULL,
                    saison TEXT NOT NULL,  # Sèche, Pluie, Fraîche
                    mois_debut INTEGER NOT NULL,  # 1-12
                    mois_fin INTEGER NOT NULL,   # 1-12
                    region TEXT,  # Optionnel: si spécifique à une région
                    conseils TEXT,  # Conseils spécifiques pour cette période
                    FOREIGN KEY (culture_id) REFERENCES cultures(id) ON DELETE CASCADE
                )
            ''')
            
            # Table des maladies
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maladies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    type_agent TEXT NOT NULL,  # Champignon, Bactérie, Virus, Nématode, Acarien
                    description TEXT,
                    symptomes TEXT,  # JSON array
                    conditions_favorables TEXT,  # Conditions qui favorisent la maladie
                    UNIQUE(nom, type_agent)
                )
            ''')
            
            # Table de liaison entre cultures et maladies
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS culture_maladies (
                    culture_id INTEGER NOT NULL,
                    maladie_id INTEGER NOT NULL,
                    frequence TEXT,  # Fréquent, Occasionnel, Rare
                    gravite TEXT,   # Faible, Modérée, Élevée
                    stade_sensible TEXT,  # Jeune plante, Floraison, etc.
                    PRIMARY KEY (culture_id, maladie_id),
                    FOREIGN KEY (culture_id) REFERENCES cultures(id) ON DELETE CASCADE,
                    FOREIGN KEY (maladie_id) REFERENCES maladies(id) ON DELETE CASCADE
                )
            ''')
            
            # Table des traitements
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traitements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    type_traitement TEXT NOT NULL,  # Chimique, Biologique, Culturel
                    description TEXT,
                    mode_application TEXT,
                    delai_attente_jours INTEGER,  # Pour les traitements chimiques
                    precautions TEXT,  # Précautions d'emploi
                    UNIQUE(nom, type_traitement)
                )
            ''')
            
            # Table de liaison entre maladies et traitements
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maladie_traitements (
                    maladie_id INTEGER NOT NULL,
                    traitement_id INTEGER NOT NULL,
                    efficacite TEXT,  # Élevée, Moyenne, Faible
                    type_usage TEXT,  # Curatif, Préventif, Les deux
                    posologie TEXT,   # Dosage et fréquence
                    PRIMARY KEY (maladie_id, traitement_id),
                    FOREIGN KEY (maladie_id) REFERENCES maladies(id) ON DELETE CASCADE,
                    FOREIGN KEY (traitement_id) REFERENCES traitements(id) ON DELETE CASCADE
                )
            ''')
            
            # Table des engrais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS engrais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    type_engrais TEXT NOT NULL,  # Organique, Minéral, Organo-minéral
                    composition TEXT,  # NPK ou composition
                    description TEXT,
                    mode_application TEXT,
                    precautions TEXT,
                    UNIQUE(nom, type_engrais)
                )
            ''')
            
            # Table de liaison entre cultures et engrais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS culture_engrais (
                    culture_id INTEGER NOT NULL,
                    engrais_id INTEGER NOT NULL,
                    stade_application TEXT,  # Pré-plantation, Démarrage, Croissance, Floraison, Fructification
                    dose_recommandee TEXT,   # Ex: 200 kg/ha
                    frequence_application TEXT,  # Ex: Tous les 15 jours
                    methode_application TEXT,    # Enfouissement, Épandage, Fertigation
                    PRIMARY KEY (culture_id, engrais_id),
                    FOREIGN KEY (culture_id) REFERENCES cultures(id) ON DELETE CASCADE,
                    FOREIGN KEY (engrais_id) REFERENCES engrais(id) ON DELETE CASCADE
                )
            ''')
            
            # Table des parasites
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parasites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    nom_scientifique TEXT,
                    type_organisme TEXT NOT NULL,  # Insecte, Acarien, Nématode, etc.
                    description TEXT,
                    plantes_hotes TEXT,  # JSON array des plantes couramment attaquées
                    symptomes TEXT,      # Dégâts causés
                    UNIQUE(nom, type_organisme)
                )
            ''')
            
            # Table de liaison entre cultures et parasites
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS culture_parasites (
                    culture_id INTEGER NOT NULL,
                    parasite_id INTEGER NOT NULL,
                    frequence TEXT,    # Fréquent, Occasionnel, Rare
                    gravite TEXT,      # Faible, Modérée, Élevée
                    stade_sensible TEXT,  # Stade de la plante le plus sensible
                    PRIMARY KEY (culture_id, parasite_id),
                    FOREIGN KEY (culture_id) REFERENCES cultures(id) ON DELETE CASCADE,
                    FOREIGN KEY (parasite_id) REFERENCES parasites(id) ON DELETE CASCADE
                )
            ''')
            
            # Table des méthodes de lutte contre les parasites
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS methodes_lutte_parasites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parasite_id INTEGER NOT NULL,
                    type_lutte TEXT NOT NULL,  # Chimique, Biologique, Culturelle, Physique
                    description TEXT,
                    efficacite TEXT,  # Élevée, Moyenne, Faible
                    delai_attente_jours INTEGER,  # Pour les traitements chimiques
                    precautions TEXT,  # Précautions d'emploi
                    FOREIGN KEY (parasite_id) REFERENCES parasites(id) ON DELETE CASCADE
                )
            ''')
            
            # Table des associations bénéfiques (compagnonnage)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS associations_benefiques (
                    culture_id_1 INTEGER NOT NULL,
                    culture_id_2 INTEGER NOT NULL,
                    benefices TEXT NOT NULL,  # Description des bénéfices
                    type_association TEXT,    # Répulsif, Attractif, Amélioration sol, etc.
                    notes TEXT,               # Notes complémentaires
                    PRIMARY KEY (culture_id_1, culture_id_2),
                    FOREIGN KEY (culture_id_1) REFERENCES cultures(id) ON DELETE CASCADE,
                    FOREIGN KEY (culture_id_2) REFERENCES cultures(id) ON DELETE CASCADE
                )
            ''')
            
            # Table des conversations (conservée pour la compatibilité)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_question TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des alertes météo (conservée pour la compatibilité)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alertes_meteo ( 
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    region TEXT NOT NULL,
                    type_alerte TEXT,
                    message TEXT,
                    date_alerte DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    # ==============================================
    # MÉTHODES D'INSERTION DE DONNÉES
    # ==============================================
    
    def ajouter_culture(self, culture_data: Dict[str, Any]) -> int:
        """
        Ajoute ou met à jour une culture dans la base de données.
        
        Args:
            culture_data: Dictionnaire contenant les données de la culture
                {
                    "nom": str,
                    "nom_scientifique": str,
                    "type_culture": str,
                    "description": str,
                    "peut_cultiver_burkina": bool,
                    "raison_non_culture": Optional[str],
                    "besoins_eau": str,
                    "type_sol": List[str],
                    "conditions_climatiques": List[str],
                    "conseils_generaux": List[str]
                }
        
        Returns:
            int: L'ID de la culture ajoutée ou mise à jour
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Préparer les données pour l'insertion
            data = {
                "nom": culture_data["nom"],
                "nom_scientifique": culture_data.get("nom_scientifique"),
                "type_culture": culture_data["type_culture"],
                "description": culture_data.get("description", ""),
                "peut_cultiver_burkina": 1 if culture_data.get("peut_cultiver_burkina", True) else 0,
                "raison_non_culture": culture_data.get("raison_non_culture"),
                "besoins_eau": culture_data.get("besoins_eau"),
                "type_sol": json.dumps(culture_data.get("type_sol", []), ensure_ascii=False) if isinstance(culture_data.get("type_sol"), list) else culture_data.get("type_sol", "[]"),
                "conditions_climatiques": json.dumps(culture_data.get("conditions_climatiques", []), ensure_ascii=False) if isinstance(culture_data.get("conditions_climatiques"), list) else culture_data.get("conditions_climatiques", "[]"),
                "conseils_generaux": json.dumps(culture_data.get("conseils_generaux", []), ensure_ascii=False) if isinstance(culture_data.get("conseils_generaux"), list) else culture_data.get("conseils_generaux", "[]"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Vérifier si la culture existe déjà
            cursor.execute("SELECT id FROM cultures WHERE LOWER(nom) = LOWER(?)", (culture_data["nom"],))
            existing = cursor.fetchone()
            
            if existing:
                # Mise à jour de la culture existante
                culture_id = existing[0]
                set_clause = ", ".join(f"{key} = ?" for key in data.keys())
                values = list(data.values()) + [culture_id]
                cursor.execute(f"UPDATE cultures SET {set_clause} WHERE id = ?", values)
            else:
                # Insertion d'une nouvelle culture
                placeholders = ", ".join("?" * len(data))
                columns = ", ".join(data.keys())
                cursor.execute(
                    f"INSERT INTO cultures ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )
                culture_id = cursor.lastrowid
            
            conn.commit()
            return culture_id
    
    def ajouter_variete(self, variete_data: Dict[str, Any]) -> int:
        """
        Ajoute ou met à jour une variété de culture.
        
        Args:
            variete_data: {
                "culture_id": int,
                "nom": str,
                "description": Optional[str],
                "duree_cycle_jours": Optional[int],
                "rendement_attendu": Optional[str],
                "resistance_maladies": Optional[List[str]]
            }
        
        Returns:
            int: L'ID de la variété ajoutée ou mise à jour
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si la variété existe déjà
            cursor.execute(
                "SELECT id FROM varietes WHERE culture_id = ? AND LOWER(nom) = LOWER(?)",
                (variete_data["culture_id"], variete_data["nom"])
            )
            existing = cursor.fetchone()
            
            data = {
                "culture_id": variete_data["culture_id"],
                "nom": variete_data["nom"],
                "description": variete_data.get("description"),
                "duree_cycle_jours": variete_data.get("duree_cycle_jours"),
                "rendement_attendu": variete_data.get("rendement_attendu"),
                "resistance_maladies": json.dumps(variete_data.get("resistance_maladies", []), ensure_ascii=False) if isinstance(variete_data.get("resistance_maladies"), list) else variete_data.get("resistance_maladies", "[]")
            }
            
            if existing:
                # Mise à jour de la variété existante
                variete_id = existing[0]
                set_clause = ", ".join(f"{key} = ?" for key in data.keys())
                values = list(data.values()) + [variete_id]
                cursor.execute(f"UPDATE varietes SET {set_clause} WHERE id = ?", values)
            else:
                # Insertion d'une nouvelle variété
                placeholders = ", ".join("?" * len(data))
                columns = ", ".join(data.keys())
                cursor.execute(
                    f"INSERT INTO varietes ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )
                variete_id = cursor.lastrowid
            
            conn.commit()
            return variete_id
    
    def ajouter_periode_plantation(self, periode_data: Dict[str, Any]) -> int:
        """
        Ajoute ou met à jour une période de plantation pour une culture.
        
        Args:
            periode_data: {
                "culture_id": int,
                "saison": str,
                "mois_debut": int,
                "mois_fin": int,
                "region": Optional[str],
                "conseils": Optional[str]
            }
        
        Returns:
            int: L'ID de la période de plantation ajoutée ou mise à jour
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si la période existe déjà
            cursor.execute("""
                SELECT id FROM periodes_plantation 
                WHERE culture_id = ? AND saison = ? AND 
                      ((mois_debut BETWEEN ? AND ?) OR (mois_fin BETWEEN ? AND ?) OR 
                       (? BETWEEN mois_debut AND mois_fin) OR (? BETWEEN mois_debut AND mois_fin))
            """, (
                periode_data["culture_id"], periode_data["saison"],
                periode_data["mois_debut"], periode_data["mois_fin"],
                periode_data["mois_debut"], periode_data["mois_fin"],
                periode_data["mois_debut"], periode_data["mois_fin"]
            ))
            
            existing = cursor.fetchone()
            
            data = {
                "culture_id": periode_data["culture_id"],
                "saison": periode_data["saison"],
                "mois_debut": periode_data["mois_debut"],
                "mois_fin": periode_data["mois_fin"],
                "region": periode_data.get("region"),
                "conseils": periode_data.get("conseils")
            }
            
            if existing:
                # Mise à jour de la période existante
                periode_id = existing[0]
                set_clause = ", ".join(f"{key} = ?" for key in data.keys())
                values = list(data.values()) + [periode_id]
                cursor.execute(f"UPDATE periodes_plantation SET {set_clause} WHERE id = ?", values)
            else:
                # Insertion d'une nouvelle période
                placeholders = ", ".join("?" * len(data))
                columns = ", ".join(data.keys())
                cursor.execute(
                    f"INSERT INTO periodes_plantation ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )
                periode_id = cursor.lastrowid
            
            conn.commit()
            return periode_id
    
    def ajouter_maladie(self, maladie_data: Dict[str, Any]) -> int:
        """
        Ajoute ou met à jour une maladie dans la base de données.
        
        Args:
            maladie_data: {
                "nom": str,
                "type_agent": str,
                "description": Optional[str],
                "symptomes": List[str],
                "conditions_favorables": List[str]
            }
        
        Returns:
            int: L'ID de la maladie ajoutée ou mise à jour
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si la maladie existe déjà
            cursor.execute(
                "SELECT id FROM maladies WHERE LOWER(nom) = LOWER(?) AND LOWER(type_agent) = LOWER(?)",
                (maladie_data["nom"], maladie_data["type_agent"])
            )
            existing = cursor.fetchone()
            
            data = {
                "nom": maladie_data["nom"],
                "type_agent": maladie_data["type_agent"],
                "description": maladie_data.get("description"),
                "symptomes": json.dumps(maladie_data.get("symptomes", []), ensure_ascii=False) if isinstance(maladie_data.get("symptomes"), list) else maladie_data.get("symptomes", "[]"),
                "conditions_favorables": json.dumps(maladie_data.get("conditions_favorables", []), ensure_ascii=False) if isinstance(maladie_data.get("conditions_favorables"), list) else maladie_data.get("conditions_favorables", "[]")
            }
            
            if existing:
                # Mise à jour de la maladie existante
                maladie_id = existing[0]
                set_clause = ", ".join(f"{key} = ?" for key in data.keys())
                values = list(data.values()) + [maladie_id]
                cursor.execute(f"UPDATE maladies SET {set_clause} WHERE id = ?", values)
            else:
                # Insertion d'une nouvelle maladie
                placeholders = ", ".join("?" * len(data))
                columns = ", ".join(data.keys())
                cursor.execute(
                    f"INSERT INTO maladies ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )
                maladie_id = cursor.lastrowid
            
            conn.commit()
            return maladie_id
    
    def associer_maladie_culture(self, culture_id: int, maladie_id: int, 
                                frequence: str = None, gravite: str = None, 
                                stade_sensible: str = None) -> bool:
        """
        Établit une association entre une culture et une maladie.
        
        Args:
            culture_id: ID de la culture
            maladie_id: ID de la maladie
            frequence: Fréquence d'apparition (Fréquent, Occasionnel, Rare)
            gravite: Gravité des dégâts (Faible, Modérée, Élevée)
            stade_sensible: Stade de la plante sensible (optionnel)
        
        Returns:
            bool: True si l'association a été créée ou mise à jour avec succès
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si l'association existe déjà
            cursor.execute(
                "SELECT 1 FROM culture_maladies WHERE culture_id = ? AND maladie_id = ?",
                (culture_id, maladie_id)
            )
            exists = cursor.fetchone() is not None
            
            if exists:
                # Mise à jour de l'association existante
                update_data = []
                update_values = []
                
                if frequence is not None:
                    update_data.append("frequence = ?")
                    update_values.append(frequence)
                if gravite is not None:
                    update_data.append("gravite = ?")
                    update_values.append(gravite)
                if stade_sensible is not None:
                    update_data.append("stade_sensible = ?")
                    update_values.append(stade_sensible)
                
                if update_data:
                    update_values.extend([culture_id, maladie_id])
                    cursor.execute(
                        f"""
                        UPDATE culture_maladies 
                        SET {', '.join(update_data)}
                        WHERE culture_id = ? AND maladie_id = ?
                        """,
                        update_values
                    )
            else:
                # Création d'une nouvelle association
                cursor.execute(
                    """
                    INSERT INTO culture_maladies 
                    (culture_id, maladie_id, frequence, gravite, stade_sensible)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (culture_id, maladie_id, frequence, gravite, stade_sensible)
                )
            
            conn.commit()
            return True
    
    def ajouter_traitement(self, traitement_data: Dict[str, Any]) -> int:
        """
        Ajoute ou met à jour un traitement dans la base de données.
        
        Args:
            traitement_data: {
                "nom": str,
                "type_traitement": str,
                "description": Optional[str],
                "mode_application": Optional[str],
                "delai_attente_jours": Optional[int],
                "precautions": Optional[str]
            }
        
        Returns:
            int: L'ID du traitement ajouté ou mis à jour
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si le traitement existe déjà
            cursor.execute(
                "SELECT id FROM traitements WHERE LOWER(nom) = LOWER(?) AND LOWER(type_traitement) = LOWER(?)",
                (traitement_data["nom"], traitement_data["type_traitement"])
            )
            existing = cursor.fetchone()
            
            data = {
                "nom": traitement_data["nom"],
                "type_traitement": traitement_data["type_traitement"],
                "description": traitement_data.get("description"),
                "mode_application": traitement_data.get("mode_application"),
                "delai_attente_jours": traitement_data.get("delai_attente_jours"),
                "precautions": traitement_data.get("precautions")
            }
            
            if existing:
                # Mise à jour du traitement existant
                traitement_id = existing[0]
                set_clause = ", ".join(f"{key} = ?" for key in data.keys())
                values = list(data.values()) + [traitement_id]
                cursor.execute(f"UPDATE traitements SET {set_clause} WHERE id = ?", values)
            else:
                # Insertion d'un nouveau traitement
                placeholders = ", ".join("?" * len(data))
                columns = ", ".join(data.keys())
                cursor.execute(
                    f"INSERT INTO traitements ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )
                traitement_id = cursor.lastrowid
            
            conn.commit()
            return traitement_id
    
    def associer_traitement_maladie(self, maladie_id: int, traitement_id: int, 
                                   efficacite: str = None, type_usage: str = None, 
                                   posologie: str = None) -> bool:
        """
        Établit une association entre une maladie et un traitement.
        
        Args:
            maladie_id: ID de la maladie
            traitement_id: ID du traitement
            efficacite: Efficacité du traitement (Élevée, Moyenne, Faible)
            type_usage: Type d'utilisation (Curatif, Préventif, Les deux)
            posologie: Posologie recommandée
        
        Returns:
            bool: True si l'association a été créée ou mise à jour avec succès
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si l'association existe déjà
            cursor.execute(
                "SELECT 1 FROM maladie_traitements WHERE maladie_id = ? AND traitement_id = ?",
                (maladie_id, traitement_id)
            )
            exists = cursor.fetchone() is not None
            
            if exists:
                # Mise à jour de l'association existante
                update_data = []
                update_values = []
                
                if efficacite is not None:
                    update_data.append("efficacite = ?")
                    update_values.append(efficacite)
                if type_usage is not None:
                    update_data.append("type_usage = ?")
                    update_values.append(type_usage)
                if posologie is not None:
                    update_data.append("posologie = ?")
                    update_values.append(posologie)
                
                if update_data:
                    update_values.extend([maladie_id, traitement_id])
                    cursor.execute(
                        f"""
                        UPDATE maladie_traitements 
                        SET {', '.join(update_data)}
                        WHERE maladie_id = ? AND traitement_id = ?
                        """,
                        update_values
                    )
            else:
                # Création d'une nouvelle association
                cursor.execute(
                    """
                    INSERT INTO maladie_traitements 
                    (maladie_id, traitement_id, efficacite, type_usage, posologie)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (maladie_id, traitement_id, efficacite, type_usage, posologie)
                )
            
            conn.commit()
            return True
    
    def ajouter_engrais(self, engrais_data: Dict[str, Any]) -> int:
        """
        Ajoute ou met à jour un engrais dans la base de données.
        
        Args:
            engrais_data: {
                "nom": str,
                "type_engrais": str,
                "composition": Optional[str],
                "description": Optional[str],
                "mode_application": Optional[str],
                "precautions": Optional[str]
            }
        
        Returns:
            int: L'ID de l'engrais ajouté ou mis à jour
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si l'engrais existe déjà
            cursor.execute(
                "SELECT id FROM engrais WHERE LOWER(nom) = LOWER(?) AND LOWER(type_engrais) = LOWER(?)",
                (engrais_data["nom"], engrais_data["type_engrais"])
            )
            existing = cursor.fetchone()
            
            data = {
                "nom": engrais_data["nom"],
                "type_engrais": engrais_data["type_engrais"],
                "composition": engrais_data.get("composition"),
                "description": engrais_data.get("description"),
                "mode_application": engrais_data.get("mode_application"),
                "precautions": engrais_data.get("precautions")
            }
            
            if existing:
                # Mise à jour de l'engrais existant
                engrais_id = existing[0]
                set_clause = ", ".join(f"{key} = ?" for key in data.keys())
                values = list(data.values()) + [engrais_id]
                cursor.execute(f"UPDATE engrais SET {set_clause} WHERE id = ?", values)
            else:
                # Insertion d'un nouvel engrais
                placeholders = ", ".join("?" * len(data))
                columns = ", ".join(data.keys())
                cursor.execute(
                    f"INSERT INTO engrais ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )
                engrais_id = cursor.lastrowid
            
            conn.commit()
            return engrais_id
    
    def associer_engrais_culture(self, culture_id: int, engrais_id: int, 
                                stade_application: str = None, dose_recommandee: str = None, 
                                frequence_application: str = None, methode_application: str = None) -> bool:
        """
        Établit une association entre une culture et un engrais.
        
        Args:
            culture_id: ID de la culture
            engrais_id: ID de l'engrais
            stade_application: Stade d'application (Pré-plantation, Démarrage, Croissance, Floraison, Fructification)
            dose_recommandee: Dose recommandée (ex: "200 kg/ha")
            frequence_application: Fréquence d'application (ex: "Tous les 15 jours")
            methode_application: Méthode d'application (Enfouissement, Épandage, Fertigation)
        
        Returns:
            bool: True si l'association a été créée ou mise à jour avec succès
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si l'association existe déjà
            cursor.execute(
                "SELECT 1 FROM culture_engrais WHERE culture_id = ? AND engrais_id = ?",
                (culture_id, engrais_id)
            )
            exists = cursor.fetchone() is not None
            
            if exists:
                # Mise à jour de l'association existante
                update_data = []
                update_values = []
                
                if stade_application is not None:
                    update_data.append("stade_application = ?")
                    update_values.append(stade_application)
                if dose_recommandee is not None:
                    update_data.append("dose_recommandee = ?")
                    update_values.append(dose_recommandee)
                if frequence_application is not None:
                    update_data.append("frequence_application = ?")
                    update_values.append(frequence_application)
                if methode_application is not None:
                    update_data.append("methode_application = ?")
                    update_values.append(methode_application)
                
                if update_data:
                    update_values.extend([culture_id, engrais_id])
                    cursor.execute(
                        f"""
                        UPDATE culture_engrais 
                        SET {', '.join(update_data)}
                        WHERE culture_id = ? AND engrais_id = ?
                        """,
                        update_values
                    )
            else:
                # Création d'une nouvelle association
                cursor.execute(
                    """
                    INSERT INTO culture_engrais 
                    (culture_id, engrais_id, stade_application, dose_recommandee, frequence_application, methode_application)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (culture_id, engrais_id, stade_application, dose_recommandee, frequence_application, methode_application)
                )
            
            conn.commit()
            return True
    
    def ajouter_parasite(self, parasite_data: Dict[str, Any]) -> int:
        """
        Ajoute ou met à jour un parasite dans la base de données.
        
        Args:
            parasite_data: {
                "nom": str,
                "nom_scientifique": Optional[str],
                "type_organisme": str,
                "description": Optional[str],
                "plantes_hotes": List[str],
                "symptomes": List[str]
            }
        
        Returns:
            int: L'ID du parasite ajouté ou mis à jour
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si le parasite existe déjà
            cursor.execute(
                "SELECT id FROM parasites WHERE LOWER(nom) = LOWER(?) AND LOWER(type_organisme) = LOWER(?)",
                (parasite_data["nom"], parasite_data["type_organisme"])
            )
            existing = cursor.fetchone()
            
            data = {
                "nom": parasite_data["nom"],
                "nom_scientifique": parasite_data.get("nom_scientifique"),
                "type_organisme": parasite_data["type_organisme"],
                "description": parasite_data.get("description"),
                "plantes_hotes": json.dumps(parasite_data.get("plantes_hotes", []), ensure_ascii=False) if isinstance(parasite_data.get("plantes_hotes"), list) else parasite_data.get("plantes_hotes", "[]"),
                "symptomes": json.dumps(parasite_data.get("symptomes", []), ensure_ascii=False) if isinstance(parasite_data.get("symptomes"), list) else parasite_data.get("symptomes", "[]")
            }
            
            if existing:
                # Mise à jour du parasite existant
                parasite_id = existing[0]
                set_clause = ", ".join(f"{key} = ?" for key in data.keys())
                values = list(data.values()) + [parasite_id]
                cursor.execute(f"UPDATE parasites SET {set_clause} WHERE id = ?", values)
            else:
                # Insertion d'un nouveau parasite
                placeholders = ", ".join("?" * len(data))
                columns = ", ".join(data.keys())
                cursor.execute(
                    f"INSERT INTO parasites ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )
                parasite_id = cursor.lastrowid
            
            conn.commit()
            return parasite_id
    
    def associer_parasite_culture(self, culture_id: int, parasite_id: int, 
                                 frequence: str = None, gravite: str = None, 
                                 stade_sensible: str = None) -> bool:
        """
        Établit une association entre une culture et un parasite.
        
        Args:
            culture_id: ID de la culture
            parasite_id: ID du parasite
            frequence: Fréquence d'apparition (Fréquent, Occasionnel, Rare)
            gravite: Gravité des dégâts (Faible, Modérée, Élevée)
            stade_sensible: Stade de la plante sensible (optionnel)
        
        Returns:
            bool: True si l'association a été créée ou mise à jour avec succès
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si l'association existe déjà
            cursor.execute(
                "SELECT 1 FROM culture_parasites WHERE culture_id = ? AND parasite_id = ?",
                (culture_id, parasite_id)
            )
            exists = cursor.fetchone() is not None
            
            if exists:
                # Mise à jour de l'association existante
                update_data = []
                update_values = []
                
                if frequence is not None:
                    update_data.append("frequence = ?")
                    update_values.append(frequence)
                if gravite is not None:
                    update_data.append("gravite = ?")
                    update_values.append(gravite)
                if stade_sensible is not None:
                    update_data.append("stade_sensible = ?")
                    update_values.append(stade_sensible)
                
                if update_data:
                    update_values.extend([culture_id, parasite_id])
                    cursor.execute(
                        f"""
                        UPDATE culture_parasites 
                        SET {', '.join(update_data)}
                        WHERE culture_id = ? AND parasite_id = ?
                        """,
                        update_values
                    )
            else:
                # Création d'une nouvelle association
                cursor.execute(
                    """
                    INSERT INTO culture_parasites 
                    (culture_id, parasite_id, frequence, gravite, stade_sensible)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (culture_id, parasite_id, frequence, gravite, stade_sensible)
                )
            
            conn.commit()
            return True
    
    def ajouter_methode_lutte_parasite(self, methode_data: Dict[str, Any]) -> int:
        """
        Ajoute ou met à jour une méthode de lutte contre un parasite.
        
        Args:
            methode_data: {
                "parasite_id": int,
                "type_lutte": str,
                "description": str,
                "efficacite": str,
                "delai_attente_jours": Optional[int],
                "precautions": Optional[str]
            }
        
        Returns:
            int: L'ID de la méthode de lutte ajoutée ou mise à jour
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si la méthode existe déjà
            cursor.execute(
                """
                SELECT id FROM methodes_lutte_parasites 
                WHERE parasite_id = ? AND LOWER(description) = LOWER(?)
                """,
                (methode_data["parasite_id"], methode_data["description"])
            )
            existing = cursor.fetchone()
            
            data = {
                "parasite_id": methode_data["parasite_id"],
                "type_lutte": methode_data["type_lutte"],
                "description": methode_data["description"],
                "efficacite": methode_data.get("efficacite"),
                "delai_attente_jours": methode_data.get("delai_attente_jours"),
                "precautions": methode_data.get("precautions")
            }
            
            if existing:
                # Mise à jour de la méthode existante
                methode_id = existing[0]
                set_clause = ", ".join(f"{key} = ?" for key in data.keys())
                values = list(data.values()) + [methode_id]
                cursor.execute(f"UPDATE methodes_lutte_parasites SET {set_clause} WHERE id = ?", values)
            else:
                # Insertion d'une nouvelle méthode
                placeholders = ", ".join("?" * len(data))
                columns = ", ".join(data.keys())
                cursor.execute(
                    f"INSERT INTO methodes_lutte_parasites ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )
                methode_id = cursor.lastrowid
            
            conn.commit()
            return methode_id
    
    def ajouter_association_benefique(self, culture_id_1: int, culture_id_2: int, 
                                    benefices: str, type_association: str = None, 
                                    notes: str = None) -> bool:
        """
        Ajoute ou met à jour une association bénéfique entre deux cultures.
        
        Args:
            culture_id_1: ID de la première culture
            culture_id_2: ID de la deuxième culture
            benefices: Description des bénéfices de l'association
            type_association: Type d'association (Répulsif, Attractif, Amélioration sol, etc.)
            notes: Notes complémentaires
        
        Returns:
            bool: True si l'association a été créée ou mise à jour avec succès
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si l'association existe déjà (dans un sens ou dans l'autre)
            cursor.execute(
                """
                SELECT 1 FROM associations_benefiques 
                WHERE (culture_id_1 = ? AND culture_id_2 = ?)
                OR (culture_id_1 = ? AND culture_id_2 = ?)
                """,
                (culture_id_1, culture_id_2, culture_id_2, culture_id_1)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Mise à jour de l'association existante
                cursor.execute(
                    """
                    UPDATE associations_benefiques 
                    SET benefices = ?, type_association = ?, notes = ?
                    WHERE (culture_id_1 = ? AND culture_id_2 = ?)
                    OR (culture_id_1 = ? AND culture_id_2 = ?)
                    """,
                    (benefices, type_association, notes, 
                     culture_id_1, culture_id_2, culture_id_2, culture_id_1)
                )
            else:
                # Insertion d'une nouvelle association
                cursor.execute(
                    """
                    INSERT INTO associations_benefiques 
                    (culture_id_1, culture_id_2, benefices, type_association, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (culture_id_1, culture_id_2, benefices, type_association, notes)
                )
            
            conn.commit()
            return True
    
    # ==============================================
    # MÉTHODES DE RECHERCHE ET DE RÉCUPÉRATION
    # ==============================================
    
    def rechercher_culture_par_nom(self, nom: str) -> Optional[Dict]:
        """
        Recherche une culture par son nom (insensible à la casse).
        
        Args:
            nom: Nom de la culture à rechercher
            
        Returns:
            Optional[Dict]: Dictionnaire contenant les informations de la culture, ou None si non trouvée
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Rechercher la culture par nom
            cursor.execute("""
                SELECT * FROM cultures 
                WHERE LOWER(nom) = LOWER(?)
            """, (nom,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # Convertir la ligne en dictionnaire
            culture = dict(result)
            
            # Décoder les champs JSON
            for field in ['type_sol', 'conditions_climatiques', 'conseils_generaux']:
                if culture[field]:
                    try:
                        culture[field] = json.loads(culture[field])
                    except (json.JSONDecodeError, TypeError):
                        culture[field] = []
                else:
                    culture[field] = []
            
            # Récupérer les variétés
            cursor.execute("""
                SELECT id, nom, description, duree_cycle_jours, 
                       rendement_attendu, resistance_maladies 
                FROM varietes 
                WHERE culture_id = ?
                ORDER BY nom
            """, (culture['id'],))
            
            varietes = []
            for row in cursor.fetchall():
                variete = dict(row)
                if variete.get('resistance_maladies'):
                    try:
                        variete['resistance_maladies'] = json.loads(variete['resistance_maladies'])
                    except (json.JSONDecodeError, TypeError):
                        variete['resistance_maladies'] = []
                else:
                    variete['resistance_maladies'] = []
                varietes.append(variete)
            
            culture['varietes'] = varietes
            
            # Récupérer les périodes de plantation
            cursor.execute("""
                SELECT id, saison, mois_debut, mois_fin, region, conseils 
                FROM periodes_plantation 
                WHERE culture_id = ?
                ORDER BY mois_debut
            """, (culture['id'],))
            
            culture['periodes_plantation'] = [dict(row) for row in cursor.fetchall()]
            
            # Récupérer les maladies associées
            cursor.execute("""
                SELECT m.*, cm.frequence, cm.gravite, cm.stade_sensible
                FROM maladies m
                JOIN culture_maladies cm ON m.id = cm.maladie_id
                WHERE cm.culture_id = ?
                ORDER BY cm.gravite DESC, cm.frequence DESC
            """, (culture['id'],))
            
            maladies = []
            for row in cursor.fetchall():
                maladie = dict(row)
                
                # Décoder les champs JSON
                for field in ['symptomes', 'conditions_favorables']:
                    if maladie.get(field):
                        try:
                            maladie[field] = json.loads(maladie[field])
                        except (json.JSONDecodeError, TypeError):
                            maladie[field] = []
                    else:
                        maladie[field] = []
                
                # Récupérer les traitements pour cette maladie
                cursor.execute("""
                    SELECT t.*, mt.efficacite, mt.type_usage, mt.posologie
                    FROM traitements t
                    JOIN maladie_traitements mt ON t.id = mt.traitement_id
                    WHERE mt.maladie_id = ?
                    ORDER BY mt.efficacite DESC
                """, (maladie['id'],))
                
                maladie['traitements'] = [dict(row) for row in cursor.fetchall()]
                
                maladies.append(maladie)
            
            culture['maladies'] = maladies
            
            # Récupérer les engrais recommandés
            cursor.execute("""
                SELECT e.*, ce.stade_application, ce.dose_recommandee, 
                       ce.frequence_application, ce.methode_application
                FROM engrais e
                JOIN culture_engrais ce ON e.id = ce.engrais_id
                WHERE ce.culture_id = ?
                ORDER BY ce.stade_application
            """, (culture['id'],))
            
            culture['engrais'] = [dict(row) for row in cursor.fetchall()]
            
            # Récupérer les parasites
            cursor.execute("""
                SELECT p.*, cp.frequence, cp.gravite, cp.stade_sensible
                FROM parasites p
                JOIN culture_parasites cp ON p.id = cp.parasite_id
                WHERE cp.culture_id = ?
                ORDER BY cp.gravite DESC, cp.frequence DESC
            """, (culture['id'],))
            
            parasites = []
            for row in cursor.fetchall():
                parasite = dict(row)
                
                # Décoder les champs JSON
                for field in ['plantes_hotes', 'symptomes']:
                    if parasite.get(field):
                        try:
                            parasite[field] = json.loads(parasite[field])
                        except (json.JSONDecodeError, TypeError):
                            parasite[field] = []
                    else:
                        parasite[field] = []
                
                # Récupérer les méthodes de lutte
                cursor.execute("""
                    SELECT * FROM methodes_lutte_parasites
                    WHERE parasite_id = ?
                    ORDER BY type_lutte, efficacite DESC
                """, (parasite['id'],))
                
                parasite['methodes_lutte'] = [dict(row) for row in cursor.fetchall()]
                
                parasites.append(parasite)
            
            culture['parasites'] = parasites
            
            # Récupérer les associations bénéfiques
            cursor.execute("""
                SELECT c2.id, c2.nom, ab.benefices, ab.type_association, ab.notes
                FROM associations_benefiques ab
                JOIN cultures c1 ON ab.culture_id_1 = c1.id
                JOIN cultures c2 ON ab.culture_id_2 = c2.id
                WHERE ab.culture_id_1 = ?
                UNION
                SELECT c1.id, c1.nom, ab.benefices, ab.type_association, ab.notes
                FROM associations_benefiques ab
                JOIN cultures c1 ON ab.culture_id_1 = c1.id
                JOIN cultures c2 ON ab.culture_id_2 = c2.id
                WHERE ab.culture_id_2 = ?
            """, (culture['id'], culture['id']))
            
            culture['associations_benefiques'] = [dict(row) for row in cursor.fetchall()]
            
            return culture
    
    def rechercher_cultures_par_type(self, type_culture: str) -> List[Dict]:
        """
        Recherche les cultures par type (fruit, légume, céréale, etc.).
        
        Args:
            type_culture: Type de culture à rechercher
            
        Returns:
            List[Dict]: Liste des cultures correspondantes
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nom, description, type_culture
                FROM cultures 
                WHERE LOWER(type_culture) = LOWER(?)
                ORDER BY nom
            """, (type_culture,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def rechercher_maladie_par_nom(self, nom: str) -> Optional[Dict]:
        """
        Recherche une maladie par son nom.
        
        Args:
            nom: Nom de la maladie à rechercher
            
        Returns:
            Optional[Dict]: Dictionnaire contenant les informations de la maladie, ou None si non trouvée
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Rechercher la maladie par nom (recherche partielle insensible à la casse)
            cursor.execute("""
                SELECT * FROM maladies 
                WHERE LOWER(nom) LIKE LOWER(?)
                LIMIT 1
            """, (f"%{nom}%",))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            maladie = dict(result)
            
            # Décoder les champs JSON
            for field in ['symptomes', 'conditions_favorables']:
                if maladie.get(field):
                    try:
                        maladie[field] = json.loads(maladie[field])
                    except (json.JSONDecodeError, TypeError):
                        maladie[field] = []
                else:
                    maladie[field] = []
            
            # Récupérer les cultures affectées
            cursor.execute("""
                SELECT c.id, c.nom, cm.frequence, cm.gravite, cm.stade_sensible
                FROM cultures c
                JOIN culture_maladies cm ON c.id = cm.culture_id
                WHERE cm.maladie_id = ?
                ORDER BY cm.gravite DESC, cm.frequence DESC
            """, (maladie['id'],))
            
            maladie['cultures_affectees'] = [dict(row) for row in cursor.fetchall()]
            
            # Récupérer les traitements
            cursor.execute("""
                SELECT t.*, mt.efficacite, mt.type_usage, mt.posologie
                FROM traitements t
                JOIN maladie_traitements mt ON t.id = mt.traitement_id
                WHERE mt.maladie_id = ?
                ORDER BY mt.efficacite DESC
            """, (maladie['id'],))
            
            maladie['traitements'] = [dict(row) for row in cursor.fetchall()]
            
            return maladie
    
    def rechercher_parasite_par_nom(self, nom: str) -> Optional[Dict]:
        """
        Recherche un parasite par son nom.
        
        Args:
            nom: Nom du parasite à rechercher
            
        Returns:
            Optional[Dict]: Dictionnaire contenant les informations du parasite, ou None si non trouvé
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Rechercher le parasite par nom (recherche partielle insensible à la casse)
            cursor.execute("""
                SELECT * FROM parasites 
                WHERE LOWER(nom) LIKE LOWER(?)
                LIMIT 1
            """, (f"%{nom}%",))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            parasite = dict(result)
            
            # Décoder les champs JSON
            for field in ['plantes_hotes', 'symptomes']:
                if parasite.get(field):
                    try:
                        parasite[field] = json.loads(parasite[field])
                    except (json.JSONDecodeError, TypeError):
                        parasite[field] = []
                else:
                    parasite[field] = []
            
            # Récupérer les cultures affectées
            cursor.execute("""
                SELECT c.id, c.nom, cp.frequence, cp.gravite, cp.stade_sensible
                FROM cultures c
                JOIN culture_parasites cp ON c.id = cp.culture_id
                WHERE cp.parasite_id = ?
                ORDER BY cp.gravite DESC, cp.frequence DESC
            """, (parasite['id'],))
            
            parasite['cultures_affectees'] = [dict(row) for row in cursor.fetchall()]
            
            # Récupérer les méthodes de lutte
            cursor.execute("""
                SELECT * FROM methodes_lutte_parasites
                WHERE parasite_id = ?
                ORDER BY type_lutte, efficacite DESC
            """, (parasite['id'],))
            
            parasite['methodes_lutte'] = [dict(row) for row in cursor.fetchall()]
            
            return parasite
    
    def rechercher_par_mot_cle(self, mot_cle: str, limite: int = 10) -> Dict[str, List[Dict]]:
        """
        Recherche des cultures, maladies et parasites par mot-clé.
        
        Args:
            mot_cle: Mot-clé à rechercher
            limite: Nombre maximum de résultats par catégorie
            
        Returns:
            Dict[str, List[Dict]]: Dictionnaire contenant les résultats par catégorie
        """
        resultats = {
            'cultures': [],
            'maladies': [],
            'parasites': []
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Rechercher les cultures
            cursor.execute("""
                SELECT id, nom, type_culture, description
                FROM cultures
                WHERE LOWER(nom) LIKE LOWER(?) 
                OR LOWER(description) LIKE LOWER(?)
                OR LOWER(type_culture) LIKE LOWER(?)
                LIMIT ?
            """, (f"%{mot_cle}%", f"%{mot_cle}%", f"%{mot_cle}%", limite))
            
            resultats['cultures'] = [dict(row) for row in cursor.fetchall()]
            
            # Rechercher les maladies
            cursor.execute("""
                SELECT id, nom, type_agent, description
                FROM maladies
                WHERE LOWER(nom) LIKE LOWER(?) 
                OR LOWER(description) LIKE LOWER(?)
                OR LOWER(type_agent) LIKE LOWER(?)
                LIMIT ?
            """, (f"%{mot_cle}%", f"%{mot_cle}%", f"%{mot_cle}%", limite))
            
            resultats['maladies'] = [dict(row) for row in cursor.fetchall()]
            
            # Rechercher les parasites
            cursor.execute("""
                SELECT id, nom, type_organisme, description
                FROM parasites
                WHERE LOWER(nom) LIKE LOWER(?) 
                OR LOWER(description) LIKE LOWER(?)
                OR LOWER(type_organisme) LIKE LOWER(?)
                LIMIT ?
            """, (f"%{mot_cle}%", f"%{mot_cle}%", f"%{mot_cle}%", limite))
            
            resultats['parasites'] = [dict(row) for row in cursor.fetchall()]
            
            return resultats
    
    # ==============================================
    # MÉTHODES D'IMPORT/EXPORT DE DONNÉES
    # ==============================================
    
    def exporter_vers_json(self, fichier_sortie: str) -> bool:
        """
        Exporte toutes les données de la base de données vers un fichier JSON.
        
        Args:
            fichier_sortie: Chemin vers le fichier de sortie
            
        Returns:
            bool: True si l'exportation a réussi, False sinon
        """
        try:
            # Récupérer toutes les données
            donnees = {
                'cultures': [],
                'maladies': [],
                'parasites': [],
                'traitements': [],
                'engrais': [],
                'associations': []
            }
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Exporter les cultures
                cursor.execute("""
                    SELECT * FROM cultures
                """)
                
                for row in cursor.fetchall():
                    culture = dict(row)
                    
                    # Décoder les champs JSON
                    for field in ['type_sol', 'conditions_climatiques', 'conseils_generaux']:
                        if culture.get(field):
                            try:
                                culture[field] = json.loads(culture[field])
                            except (json.JSONDecodeError, TypeError):
                                culture[field] = []
                        else:
                            culture[field] = []
                    
                    # Récupérer les variétés
                    cursor.execute("""
                        SELECT * FROM varietes 
                        WHERE culture_id = ?
                    """, (culture['id'],))
                    
                    varietes = []
                    for var_row in cursor.fetchall():
                        variete = dict(var_row)
                        if variete.get('resistance_maladies'):
                            try:
                                variete['resistance_maladies'] = json.loads(variete['resistance_maladies'])
                            except (json.JSONDecodeError, TypeError):
                                variete['resistance_maladies'] = []
                        else:
                            variete['resistance_maladies'] = []
                        varietes.append(variete)
                    
                    culture['varietes'] = varietes
                    
                    # Récupérer les périodes de plantation
                    cursor.execute("""
                        SELECT * FROM periodes_plantation 
                        WHERE culture_id = ?
                    """, (culture['id'],))
                    
                    culture['periodes_plantation'] = [dict(row) for row in cursor.fetchall()]
                    
                    # Récupérer les engrais
                    cursor.execute("""
                        SELECT e.*, ce.stade_application, ce.dose_recommandee, 
                               ce.frequence_application, ce.methode_application
                        FROM engrais e
                        JOIN culture_engrais ce ON e.id = ce.engrais_id
                        WHERE ce.culture_id = ?
                    """, (culture['id'],))
                    
                    culture['engrais'] = [dict(row) for row in cursor.fetchall()]
                    
                    donnees['cultures'].append(culture)
                
                # Exporter les maladies et traitements
                cursor.execute("""
                    SELECT * FROM maladies
                """)
                
                for row in cursor.fetchall():
                    maladie = dict(row)
                    
                    # Décoder les champs JSON
                    for field in ['symptomes', 'conditions_favorables']:
                        if maladie.get(field):
                            try:
                                maladie[field] = json.loads(maladie[field])
                            except (json.JSONDecodeError, TypeError):
                                maladie[field] = []
                        else:
                            maladie[field] = []
                    
                    # Récupérer les traitements
                    cursor.execute("""
                        SELECT t.*, mt.efficacite, mt.type_usage, mt.posologie
                        FROM traitements t
                        JOIN maladie_traitements mt ON t.id = mt.traitement_id
                        WHERE mt.maladie_id = ?
                    """, (maladie['id'],))
                    
                    maladie['traitements'] = [dict(row) for row in cursor.fetchall()]
                    
                    # Récupérer les cultures affectées
                    cursor.execute("""
                        SELECT c.id, c.nom, cm.frequence, cm.gravite, cm.stade_sensible
                        FROM cultures c
                        JOIN culture_maladies cm ON c.id = cm.culture_id
                        WHERE cm.maladie_id = ?
                    """, (maladie['id'],))
                    
                    maladie['cultures_affectees'] = [dict(row) for row in cursor.fetchall()]
                    
                    donnees['maladies'].append(maladie)
                
                # Exporter les parasites
                cursor.execute("""
                    SELECT * FROM parasites
                """)
                
                for row in cursor.fetchall():
                    parasite = dict(row)
                    
                    # Décoder les champs JSON
                    for field in ['plantes_hotes', 'symptomes']:
                        if parasite.get(field):
                            try:
                                parasite[field] = json.loads(parasite[field])
                            except (json.JSONDecodeError, TypeError):
                                parasite[field] = []
                        else:
                            parasite[field] = []
                    
                    # Récupérer les méthodes de lutte
                    cursor.execute("""
                        SELECT * FROM methodes_lutte_parasites
                        WHERE parasite_id = ?
                    """, (parasite['id'],))
                    
                    parasite['methodes_lutte'] = [dict(row) for row in cursor.fetchall()]
                    
                    # Récupérer les cultures affectées
                    cursor.execute("""
                        SELECT c.id, c.nom, cp.frequence, cp.gravite, cp.stade_sensible
                        FROM cultures c
                        JOIN culture_parasites cp ON c.id = cp.culture_id
                        WHERE cp.parasite_id = ?
                    """, (parasite['id'],))
                    
                    parasite['cultures_affectees'] = [dict(row) for row in cursor.fetchall()]
                    
                    donnees['parasites'].append(parasite)
                
                # Exporter les traitements (sans doublons)
                cursor.execute("""
                    SELECT DISTINCT t.*
                    FROM traitements t
                    LEFT JOIN maladie_traitements mt ON t.id = mt.traitement_id
                    WHERE mt.traitement_id IS NOT NULL
                """)
                
                donnees['traitements'] = [dict(row) for row in cursor.fetchall()]
                
                # Exporter les engrais (sans doublons)
                cursor.execute("""
                    SELECT DISTINCT e.*
                    FROM engrais e
                    JOIN culture_engrais ce ON e.id = ce.engrais_id
                """)
                
                donnees['engrais'] = [dict(row) for row in cursor.fetchall()]
                
                # Exporter les associations bénéfiques
                cursor.execute("""
                    SELECT c1.nom AS culture_1, c2.nom AS culture_2, 
                           ab.benefices, ab.type_association, ab.notes
                    FROM associations_benefiques ab
                    JOIN cultures c1 ON ab.culture_id_1 = c1.id
                    JOIN cultures c2 ON ab.culture_id_2 = c2.id
                """)
                
                donnees['associations'] = [dict(row) for row in cursor.fetchall()]
            
            # Écrire les données dans le fichier JSON
            with open(fichier_sortie, 'w', encoding='utf-8') as f:
                json.dump(donnees, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'exportation des données : {str(e)}")
            return False
    
    def importer_depuis_json(self, fichier_entree: str) -> bool:
        """
        Importe des données depuis un fichier JSON dans la base de données.
        
        Args:
            fichier_entree: Chemin vers le fichier d'entrée
            
        Returns:
            bool: True si l'importation a réussi, False sinon
        """
        try:
            with open(fichier_entree, 'r', encoding='utf-8') as f:
                donnees = json.load(f)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Désactiver temporairement les contraintes de clé étrangère
                cursor.execute("PRAGMA foreign_keys = OFF")
                
                # Vider les tables existantes (en commençant par les tables de liaison)
                tables = [
                    'culture_maladies', 'maladie_traitements', 'culture_engrais',
                    'culture_parasites', 'methodes_lutte_parasites', 'associations_benefiques',
                    'periodes_plantation', 'varietes', 'cultures', 'maladies', 
                    'traitements', 'engrais', 'parasites'
                ]
                
                for table in tables:
                    try:
                        cursor.execute(f"DELETE FROM {table}")
                    except sqlite3.OperationalError:
                        pass  # La table n'existe pas encore
                
                # Réactiver les contraintes de clé étrangère
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Réinitialiser les séquences d'auto-incrémentation
                cursor.execute("DELETE FROM sqlite_sequence")
                
                # Importer les cultures
                for culture_data in donnees.get('cultures', []):
                    # Sauvegarder les données liées qui seront ajoutées après
                    varietes = culture_data.pop('varietes', [])
                    periodes_plantation = culture_data.pop('periodes_plantation', [])
                    engrais = culture_data.pop('engrais', [])
                    
                    # Ajouter la culture
                    culture_id = self.ajouter_culture(culture_data)
                    
                    # Ajouter les variétés
                    for variete in varietes:
                        variete['culture_id'] = culture_id
                        self.ajouter_variete(variete)
                    
                    # Ajouter les périodes de plantation
                    for periode in periodes_plantation:
                        periode['culture_id'] = culture_id
                        self.ajouter_periode_plantation(periode)
                    
                    # Ajouter les engrais
                    for engrais_data in engrais:
                        # Vérifier si l'engrais existe déjà
                        cursor.execute(
                            "SELECT id FROM engrais WHERE LOWER(nom) = LOWER(?) AND LOWER(type_engrais) = LOWER(?)",
                            (engrais_data['nom'], engrais_data.get('type_engrais', ''))
                        )
                        existing = cursor.fetchone()
                        
                        if existing:
                            engrais_id = existing[0]
                        else:
                            # Créer un nouvel engrais
                            engrais_id = self.ajouter_engrais({
                                'nom': engrais_data['nom'],
                                'type_engrais': engrais_data.get('type_engrais', 'Minéral'),
                                'composition': engrais_data.get('composition'),
                                'description': engrais_data.get('description'),
                                'mode_application': engrais_data.get('mode_application'),
                                'precautions': engrais_data.get('precautions')
                            })
                        
                        # Associer l'engrais à la culture
                        self.associer_engrais_culture(
                            culture_id=culture_id,
                            engrais_id=engrais_id,
                            stade_application=engrais_data.get('stade_application'),
                            dose_recommandee=engrais_data.get('dose_recommandee'),
                            frequence_application=engrais_data.get('frequence_application'),
                            methode_application=engrais_data.get('methode_application')
                        )
                
                # Importer les maladies et traitements
                for maladie_data in donnees.get('maladies', []):
                    # Sauvegarder les données liées
                    traitements = maladie_data.pop('traitements', [])
                    
                    # Ajouter la maladie
                    maladie_id = self.ajouter_maladie(maladie_data)
                    
                    # Ajouter les associations avec les cultures
                    for culture in maladie_data.get('cultures_affectees', []):
                        self.associer_maladie_culture(
                            culture_id=culture['id'],
                            maladie_id=maladie_id,
                            frequence=culture.get('frequence'),
                            gravite=culture.get('gravite'),
                            stade_sensible=culture.get('stade_sensible')
                        )
                    
                    # Ajouter les traitements
                    for traitement_data in traitements:
                        # Vérifier si le traitement existe déjà
                        cursor.execute(
                            "SELECT id FROM traitements WHERE LOWER(nom) = LOWER(?) AND LOWER(type_traitement) = LOWER(?)",
                            (traitement_data['nom'], traitement_data.get('type_traitement', ''))
                        )
                        existing = cursor.fetchone()
                        
                        if existing:
                            traitement_id = existing[0]
                        else:
                            # Créer un nouveau traitement
                            traitement_id = self.ajouter_traitement({
                                'nom': traitement_data['nom'],
                                'type_traitement': traitement_data.get('type_traitement', 'Chimique'),
                                'description': traitement_data.get('description'),
                                'mode_application': traitement_data.get('mode_application'),
                                'delai_attente_jours': traitement_data.get('delai_attente_jours'),
                                'precautions': traitement_data.get('precautions')
                            })
                        
                        # Associer le traitement à la maladie
                        self.associer_traitement_maladie(
                            maladie_id=maladie_id,
                            traitement_id=traitement_id,
                            efficacite=traitement_data.get('efficacite'),
                            type_usage=traitement_data.get('type_usage'),
                            posologie=traitement_data.get('posologie')
                        )
                
                # Importer les parasites
                for parasite_data in donnees.get('parasites', []):
                    # Sauvegarder les données liées
                    methodes_lutte = parasite_data.pop('methodes_lutte', [])
                    
                    # Ajouter le parasite
                    parasite_id = self.ajouter_parasite(parasite_data)
                    
                    # Ajouter les associations avec les cultures
                    for culture in parasite_data.get('cultures_affectees', []):
                        self.associer_parasite_culture(
                            culture_id=culture['id'],
                            parasite_id=parasite_id,
                            frequence=culture.get('frequence'),
                            gravite=culture.get('gravite'),
                            stade_sensible=culture.get('stade_sensible')
                        )
                    
                    # Ajouter les méthodes de lutte
                    for methode in methodes_lutte:
                        self.ajouter_methode_lutte_parasite({
                            'parasite_id': parasite_id,
                            'type_lutte': methode.get('type_lutte', 'Culturelle'),
                            'description': methode.get('description', ''),
                            'efficacite': methode.get('efficacite'),
                            'delai_attente_jours': methode.get('delai_attente_jours'),
                            'precautions': methode.get('precautions')
                        })
                
                # Importer les associations bénéfiques
                for assoc in donnees.get('associations', []):
                    # Trouver les IDs des cultures
                    cursor.execute("SELECT id FROM cultures WHERE LOWER(nom) = LOWER(?)", (assoc['culture_1'],))
                    culture_1 = cursor.fetchone()
                    
                    cursor.execute("SELECT id FROM cultures WHERE LOWER(nom) = LOWER(?)", (assoc['culture_2'],))
                    culture_2 = cursor.fetchone()
                    
                    if culture_1 and culture_2:
                        self.ajouter_association_benefique(
                            culture_id_1=culture_1[0],
                            culture_id_2=culture_2[0],
                            benefices=assoc['benefices'],
                            type_association=assoc.get('type_association'),
                            notes=assoc.get('notes')
                        )
                
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'importation des données : {str(e)}")
            return False
    
    # ==============================================
    # MÉTHODES D'EXEMPLE POUR LA MIGRATION
    # ==============================================
    
    def ajouter_culture_exemple(self):
        """Ajoute des exemples de données pour le maïs"""
        # Ajouter la culture du maïs
        culture_id = self.ajouter_culture({
            "nom": "Maïs",
            "nom_scientifique": "Zea mays",
            "type_culture": "céréale",
            "description": "Le maïs est une céréale de la famille des Poacées, largement cultivée pour ses grains riches en amidon.",
            "peut_cultiver_burkina": True,
            "besoins_eau": "Modéré à élevé (500-800 mm/cycle)",
            "type_sol": ["Profond", "Bien drainé", "Riche en matière organique", "pH 5.5-7.0"],
            "conditions_climatiques": [
                "Température optimale: 25-30°C",
                "Sensible au gel",
                "Nécessite un ensoleillement important"
            ],
            "conseils_generaux": [
                "Semer au début de la saison des pluies (mai-juin)",
                "Espacement recommandé: 80 cm entre les lignes, 40 cm sur la ligne",
                "Appliquer de l'engrais de fond avant le semis",
                "Désherber régulièrement pendant les 6 premières semaines"
            ]
        })
        
        # Ajouter des variétés de maïs
        self.ajouter_variete({
            "culture_id": culture_id,
            "nom": "Sotubaka",
            "description": "Variété locale à cycle court (80-85 jours), résistante à la sécheresse.",
            "duree_cycle_jours": 85,
            "rendement_attendu": "1.5-2 t/ha",
            "resistance_maladies": ["Striga", "Pyrale du maïs"]
        })
        
        self.ajouter_variete({
            "culture_id": culture_id,
            "nom": "Komsaya",
            "description": "Variété améliorée à haut rendement, cycle moyen (90-100 jours).",
            "duree_cycle_jours": 95,
            "rendement_attendu": "3-4 t/ha",
            "resistance_maladies": ["Rouille", "Charbon du maïs"]
        })
        
        # Ajouter des périodes de plantation
        self.ajouter_periode_plantation({
            "culture_id": culture_id,
            "saison": "Pluie",
            "mois_debut": 5,  # Mai
            "mois_fin": 7,    # Juillet
            "region": "Toutes les régions",
            "conseils": "Semer dès les premières pluies bien établies pour profiter de toute la saison des pluies."
        })
        
        # Ajouter des maladies courantes
        maladie_id = self.ajouter_maladie({
            "nom": "Striure du maïs",
            "type_agent": "Virus",
            "description": "Maladie virale transmise par des cicadelles.",
            "symptomes": [
                "Stries chlorotiques parallèles aux nervures",
                "Réduction de la taille des plantes",
                "Épis mal formés"
            ],
            "conditions_favorables": ["Présence de cicadelles", "Températures élevées"]
        })
        
        # Associer la maladie au maïs
        self.associer_maladie_culture(
            culture_id=culture_id,
            maladie_id=maladie_id,
            frequence="Fréquent",
            gravite="Modérée",
            stade_sensible="Jeune plante"
        )
        
        # Ajouter un traitement pour la maladie
        traitement_id = self.ajouter_traitement({
            "nom": "Traitement des semences",
            "type_traitement": "Chimique",
            "description": "Traitement des semences avec un insecticide systémique pour lutter contre les cicadelles vectrices.",
            "mode_application": "Enrobage des semences",
            "delai_attente_jours": 0,
            "precautions": "Porter des gants et un masque lors de l'application."
        })
        
        # Associer le traitement à la maladie
        self.associer_traitement_maladie(
            maladie_id=maladie_id,
            traitement_id=traitement_id,
            efficacite="Élevée",
            type_usage="Préventif",
            posologie="Suivre les recommandations du fabricant pour le dosage."
        )
        
        # Ajouter un engrais recommandé
        engrais_id = self.ajouter_engrais({
            "nom": "NPK 15-15-15",
            "type_engrais": "Minéral",
            "composition": "15% N, 15% P2O5, 15% K2O",
            "description": "Engrais complet équilibré pour les céréales.",
            "mode_application": "Localisé au semis ou en couverture",
            "precautions": "Éviter le contact direct avec les graines."
        })
        
        # Associer l'engrais au maïs
        self.associer_engrais_culture(
            culture_id=culture_id,
            engrais_id=engrais_id,
            stade_application="Semis",
            dose_recommandee="200-300 kg/ha",
            frequence_application="Une seule application au semis",
            methode_application="Localisé dans le sillon de semis"
        )
        
        # Ajouter un parasite courant
        parasite_id = self.ajouter_parasite({
            "nom": "Pyrale du maïs",
            "nom_scientifique": "Ostrinia nubilalis",
            "type_organisme": "Insecte",
            "description": "La pyrale est un papillon dont les chenilles creusent des galeries dans les tiges et les épis de maïs.",
            "plantes_hotes": ["Maïs", "Sorgho", "Millet"],
            "symptomes": [
                "Galeries dans les tiges",
                "Chute des épis",
                "Affaiblissement des plantes"
            ]
        })
        
        # Associer le parasite au maïs
        self.associer_parasite_culture(
            culture_id=culture_id,
            parasite_id=parasite_id,
            frequence="Fréquent",
            gravite="Élevée",
            stade_sensible="Tous les stades"
        )
        
        # Ajouter une méthode de lutte contre le parasite
        self.ajouter_methode_lutte_parasite({
            "parasite_id": parasite_id,
            "type_lutte": "Biologique",
            "description": "Lâcher de trichogrammes (micro-hyménoptères parasitoïdes des œufs de pyrale).",
            "efficacite": "Élevée",
            "precautions": "À effectuer dès les premiers vols de pyrales."
        })
        
        # Ajouter une association bénéfique avec le haricot
        # D'abord, vérifier si le haricot existe dans la base
        cursor = self._get_connection().cursor()
        cursor.execute("SELECT id FROM cultures WHERE LOWER(nom) = LOWER('Haricot')")
        haricot = cursor.fetchone()
        
        if haricot:
            haricot_id = haricot[0]
            self.ajouter_association_benefique(
                culture_id_1=culture_id,
                culture_id_2=haricot_id,
                benefices="Le haricot fixe l'azote atmosphérique, ce qui profite au maïs gourmand en azote.",
                type_association="Amélioration sol",
                notes="Semer les deux cultures en association ou en rotation."
            )
        
        return culture_id

# Fonctions de compatibilité avec l'ancien code
def init_database():
    """Initialise la base de données (fonction de compatibilité)"""
    db = DatabaseManager()
    print("Base de données initialisée avec succès")

def ajouter_conversation(question, reponse):
    """Enregistre une conversation (fonction de compatibilité)"""
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (user_question, bot_response)
            VALUES (?, ?)
        ''', (question, reponse))
        conn.commit()

def ajouter_culture_exemple():
    """Ajoute des données d'exemple sur les cultures"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cultures = [
        ("Maïs", "Avril-Juin", "Sol profond, bien drainé", 90, "Arrosage régulier, désherbage important"),
        ("Tomate", "Mars-Mai", "Sol riche en humus", 70, "Tuteurer les plants, surveiller le mildiou"),
        ("Oignon", "Février-Avril", "Sol léger, bien drainé", 120, "Éviter l'excès d'eau, butter les plants"),
        ("Mil", "Mai-Juillet", "Sol sablonneux", 90, "Résistant à la sécheresse, peu d'entretien"),
        ("Arachide", "Avril-Juin", "Sol sableux, bien drainé", 120, "Butter après floraison, rotation des cultures")
    ]
    
    for culture in cultures:
        cursor.execute('''
            INSERT OR IGNORE INTO cultures (nom, periode_plantation, type_sol, duree_croissance, conseils)
            VALUES (?, ?, ?, ?, ?)
        ''', culture)
    
    conn.commit()
    conn.close()
    print("Cultures d'exemple ajoutées")