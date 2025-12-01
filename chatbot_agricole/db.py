import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List


# Base SQLite simple dédiée au chatbot (ne modifie pas un ancien fichier database.db)
DB_PATH = Path("agri_data.db")


def get_connection() -> sqlite3.Connection:
    """Retourne une connexion SQLite vers la base locale."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crée les tables minimales si elles n'existent pas."""
    with get_connection() as conn:
        cur = conn.cursor()

        # Table des cultures de base
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cultures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT UNIQUE NOT NULL,
                type_culture TEXT,
                duree_cycle_jours INTEGER,
                description TEXT
            )
            """
        )

        # Périodes de plantation par culture / région simple
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS periodes_plantation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                culture_id INTEGER NOT NULL,
                region TEXT NOT NULL,          -- ex: 'Centre', 'Nord', 'Sud'
                mois_debut INTEGER NOT NULL,   -- 1-12
                mois_fin INTEGER NOT NULL,     -- 1-12
                conseils TEXT,
                FOREIGN KEY (culture_id) REFERENCES cultures (id)
            )
            """
        )

        # Types de sol simples
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT UNIQUE NOT NULL,      -- ex: 'sablonneux', 'argilo-limoneux'
                description TEXT
            )
            """
        )

        # Association cultures <-> sols
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS culture_sols (
                culture_id INTEGER NOT NULL,
                sol_id INTEGER NOT NULL,
                PRIMARY KEY (culture_id, sol_id),
                FOREIGN KEY (culture_id) REFERENCES cultures (id),
                FOREIGN KEY (sol_id) REFERENCES sols (id)
            )
            """
        )

        conn.commit()


def seed_basic_data() -> None:
    """
    Insère quelques cultures / périodes / sols d'exemple si la base est vide.
    Cette fonction est idempotente (ne duplique pas les données).
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # Vérifier s'il y a déjà des cultures
        cur.execute("SELECT COUNT(*) FROM cultures")
        count = cur.fetchone()[0]
        if count > 0:
            return

        # Cultures de base pour le Burkina (simplifiées)
        cultures = [
            ("Maïs", "céréale", 90, "Céréale de base très cultivée, sensible au manque d'eau au démarrage."),
            ("Sorgho", "céréale", 110, "Céréale résistante à la sécheresse, adaptée aux zones sèches."),
            ("Mil", "céréale", 100, "Céréale traditionnelle très résistante, pour sols pauvres."),
            ("Riz", "céréale", 120, "Culture de bas-fond demandant beaucoup d'eau."),
            ("Niébé", "légumineuse", 70, "Légumineuse qui fixe l'azote et enrichit le sol."),
            ("Arachide", "légumineuse", 110, "Culture de rente, apprécie les sols sablo-limoneux."),
            ("Tomate", "maraîchère", 80, "Culture maraîchère exigeante en eau et en suivi sanitaire."),
            ("Oignon", "maraîchère", 120, "Culture de saison sèche, sensible à l'excès d'eau."),
        ]

        cur.executemany(
            "INSERT OR IGNORE INTO cultures (nom, type_culture, duree_cycle_jours, description) "
            "VALUES (?, ?, ?, ?)",
            cultures,
        )

        # Récupérer les ids pour les lier aux périodes
        cur.execute("SELECT id, nom FROM cultures")
        culture_ids = {row["nom"]: row["id"] for row in cur.fetchall()}

        periodes = [
            # culture, region, mois_debut, mois_fin, conseils
            ("Maïs", "Centre", 5, 7, "Semer dès l'installation des pluies, sur sol bien préparé."),
            ("Sorgho", "Centre", 6, 7, "Semer après le maïs, tolère mieux les pauses pluviométriques."),
            ("Mil", "Nord", 6, 7, "Privilégier le mil dans les zones très sèches."),
            ("Riz", "Bas-fonds", 6, 7, "Planter dans les bas-fonds ou zones irriguées."),
            ("Niébé", "Centre", 7, 8, "Peut être associé avec le maïs pour enrichir le sol."),
            ("Arachide", "Centre", 5, 6, "Semer en début de saison des pluies sur sols légers."),
            ("Tomate", "Périmètre irrigué", 11, 2, "Culture de saison sèche avec irrigation régulière."),
            ("Oignon", "Périmètre irrigué", 11, 1, "Préférer des sols légers, bien drainés."),
        ]

        cur.executemany(
            """
            INSERT INTO periodes_plantation (culture_id, region, mois_debut, mois_fin, conseils)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (culture_ids[culture], region, debut, fin, conseils)
                for culture, region, debut, fin, conseils in periodes
                if culture in culture_ids
            ],
        )

        # Types de sols simples
        sols = [
            ("sablonneux", "Sols légers, pauvres en matière organique, se réchauffent vite mais retiennent peu l'eau."),
            ("argilo-limoneux", "Sols fertiles, bons pour de nombreuses cultures mais sensibles au tassement."),
            ("ferrugineux tropicaux", "Sols dominants au Burkina, souvent pauvres en matière organique."),
        ]
        cur.executemany(
            "INSERT OR IGNORE INTO sols (nom, description) VALUES (?, ?)",
            sols,
        )

        # Associer quelques cultures à des types de sols
        cur.execute("SELECT id, nom FROM sols")
        sol_ids = {row["nom"]: row["id"] for row in cur.fetchall()}

        culture_sols = [
            ("Maïs", "ferrugineux tropicaux"),
            ("Maïs", "argilo-limoneux"),
            ("Sorgho", "ferrugineux tropicaux"),
            ("Mil", "sablonneux"),
            ("Riz", "argilo-limoneux"),
            ("Tomate", "argilo-limoneux"),
            ("Oignon", "sablonneux"),
        ]

        cur.executemany(
            """
            INSERT OR IGNORE INTO culture_sols (culture_id, sol_id)
            VALUES (?, ?)
            """,
            [
                (culture_ids[culture], sol_ids[sol])
                for culture, sol in culture_sols
                if culture in culture_ids and sol in sol_ids
            ],
        )

        conn.commit()


def find_culture_in_text(text: str) -> Optional[str]:
    """Essaie de retrouver le nom d'une culture mentionnée dans le texte."""
    text_lower = text.lower()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT nom FROM cultures")
        for (nom,) in cur.fetchall():
            if nom.lower() in text_lower:
                return nom
    return None


def get_planting_info(culture_name: str) -> Optional[List[Dict[str, Any]]]:
    """Retourne les périodes de plantation pour une culture donnée."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.region, p.mois_debut, p.mois_fin, p.conseils,
                   c.duree_cycle_jours
            FROM periodes_plantation p
            JOIN cultures c ON c.id = p.culture_id
            WHERE LOWER(c.nom) = LOWER(?)
            ORDER BY p.region
            """,
            (culture_name,),
        )
        rows = cur.fetchall()
        if not rows:
            return None
        return [dict(row) for row in rows]


def get_soil_recommendations(text: str) -> Optional[str]:
    """
    Si l'utilisateur mentionne un type de sol, renvoie une brève description
    et des cultures adaptées.
    """
    text_lower = text.lower()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nom, description FROM sols")
        sols = cur.fetchall()

        for sol in sols:
            if sol["nom"] in text_lower:
                # cultures associées
                cur.execute(
                    """
                    SELECT c.nom
                    FROM cultures c
                    JOIN culture_sols cs ON cs.culture_id = c.id
                    WHERE cs.sol_id = ?
                    ORDER BY c.nom
                    """,
                    (sol["id"],),
                )
                cultures = [row["nom"] for row in cur.fetchall()]
                cultures_txt = ", ".join(cultures) if cultures else "plusieurs cultures adaptées"
                return (
                    f"🌱 **Sol {sol['nom']}**\n\n"
                    f"{sol['description']}\n\n"
                    f"✅ Cultures adaptées : {cultures_txt}."
                )
    return None


# Initialiser la base au premier import
init_db()
seed_basic_data()


