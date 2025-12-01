import spacy
import sqlite3
from difflib import get_close_matches
import re

class NLPProcessor:
    """Processeur NLP avancé avec meilleure compréhension"""
    
    def __init__(self):
        self.nlp = spacy.load("fr_core_news_sm")
        self.questions_frequentes = self.charger_faq()
        
    def charger_faq(self):
        """FAQ prédéfinies pour réponses rapides"""
        return {
            "bonjour": "Bonjour ! Je suis votre assistant agricole. Comment puis-je vous aider aujourd'hui ?",
            "merci": "De rien ! N'hésitez pas si vous avez d'autres questions.",
            "au revoir": "Au revoir ! Bonne continuation avec vos cultures. 🌾",
            
            # Questions fréquentes
            "comment ca marche": "Je peux vous aider avec :\n- Conseils de plantation\n- Prévisions météo\n- Lutte contre parasites\n- Irrigation\n- Gestion du sol\n\nPosez-moi vos questions !",
            
            "c'est quoi le zai": "Le Zaï est une technique traditionnelle burkinabè de récupération des sols dégradés. On creuse des poquets de 20-40cm, on y ajoute du compost et on plante dedans. Cette technique permet de capter l'eau et d'augmenter les rendements de 50-100% !",
            
            "periode plantation": "Les périodes de plantation dépendent de la culture :\n- Saison des pluies (Mai-Oct) : Maïs, Mil, Sorgho, Arachide\n- Saison sèche (Nov-Avr) : Cultures maraîchères avec irrigation\n\nQuelle culture vous intéresse ?",
        }
    
    def detecter_salutation(self, texte):
        """Détecte les salutations"""
        salutations = ['bonjour', 'bonsoir', 'salut', 'hello', 'hey', 'coucou']
        texte_lower = texte.lower()
        return any(sal in texte_lower for sal in salutations)
    
    def detecter_remerciement(self, texte):
        """Détecte les remerciements"""
        remerciements = ['merci', 'thank', 'thanks', 'merçi']
        texte_lower = texte.lower()
        return any(rem in texte_lower for rem in remerciements)
    
    def extraire_nombre(self, texte):
        """Extrait un nombre du texte"""
        nombres = re.findall(r'\d+', texte)
        return int(nombres[0]) if nombres else None
    
    def extraire_ville(self, texte):
        """Extrait le nom d'une ville"""
        villes_bf = ['ouagadougou', 'bobo-dioulasso', 'koudougou', 'ouahigouya', 
                     'banfora', 'dedougou', 'fada', 'kaya', 'tenkodogo', 'gaoua']
        
        doc = self.nlp(texte.lower())
        for token in doc:
            if token.text in villes_bf:
                return token.text.capitalize()
        
        # Recherche approximative
        mots = texte.lower().split()
        for mot in mots:
            matches = get_close_matches(mot, villes_bf, n=1, cutoff=0.7)
            if matches:
                return matches[0].capitalize()
        
        return None
    
    def analyser_contexte(self, texte, historique=[]):
        """Analyse le contexte de la conversation"""
        contexte = {
            'est_salutation': self.detecter_salutation(texte),
            'est_remerciement': self.detecter_remerciement(texte),
            'culture_mentionnee': self.extraire_culture(texte),
            'ville_mentionnee': self.extraire_ville(texte),
            'nombre_mention': self.extraire_nombre(texte),
            'ton': self.detecter_ton(texte),
            'urgence': self.detecter_urgence(texte)
        }
        
        # Utiliser l'historique pour le contexte
        if historique:
            derniere_question = historique[-1] if len(historique) > 0 else None
            if derniere_question:
                contexte['contexte_precedent'] = self.extraire_culture(derniere_question)
        
        return contexte
    
    def detecter_ton(self, texte):
        """Détecte le ton de la question (urgent, poli, neutre)"""
        urgence_mots = ['urgent', 'vite', 'rapidement', 'aide', 'problème', 'danger']
        politesse_mots = ['s\'il vous plaît', 'svp', 'merci', 'pourriez', 'pouvez-vous']
        
        texte_lower = texte.lower()
        
        if any(mot in texte_lower for mot in urgence_mots):
            return 'urgent'
        elif any(mot in texte_lower for mot in politesse_mots):
            return 'poli'
        else:
            return 'neutre'
    
    def detecter_urgence(self, texte):
        """Détecte si la question est urgente"""
        mots_urgents = ['urgent', 'vite', 'rapidement', 'aide', 'problème', 
                        'meurent', 'séchent', 'danger', 'attaque', 'invasion']
        texte_lower = texte.lower()
        return any(mot in texte_lower for mot in mots_urgents)
    
    def extraire_culture(self, texte):
        """Extrait la culture avec meilleure précision"""
        cultures = {
            'maïs': ['mais', 'maïs', 'maiz'],
            'mil': ['mil', 'millet'],
            'sorgho': ['sorgho', 'sorgo'],
            'riz': ['riz', 'paddy'],
            'tomate': ['tomate', 'tomates'],
            'oignon': ['oignon', 'oignons', 'ognon'],
            'arachide': ['arachide', 'arachides', 'cacahuète'],
            'niébé': ['niébé', 'niebe', 'haricot'],
            'coton': ['coton'],
            'sésame': ['sésame', 'sesame'],
            'chou': ['chou', 'choux'],
            'salade': ['salade', 'laitue']
        }
        
        texte_lower = texte.lower()
        
        for culture_std, variantes in cultures.items():
            for variante in variantes:
                if variante in texte_lower:
                    return culture_std
        
        return None
    
    def generer_reponse_contextuelle(self, question, contexte):
        """Génère une réponse basée sur le contexte"""
        
        # Gestion des salutations
        if contexte['est_salutation']:
            return self.questions_frequentes.get('bonjour')
        
        # Gestion des remerciements
        if contexte['est_remerciement']:
            return self.questions_frequentes.get('merci')
        
        # Gestion des urgences
        if contexte['urgence']:
            reponse = "⚠️ Je comprends que c'est urgent. "
            
            if contexte['culture_mentionnee']:
                culture = contexte['culture_mentionnee']
                reponse += f"Pour votre problème de {culture}, voici ce que vous devez faire immédiatement :\n\n"
                
                # Réponses d'urgence par type de problème
                if any(mot in question.lower() for mot in ['sécher', 'sèche', 'fane']):
                    reponse += "1. Vérifiez l'humidité du sol\n"
                    reponse += "2. Arrosez immédiatement si le sol est sec\n"
                    reponse += "3. Paillez le sol pour retenir l'humidité\n"
                    reponse += "4. Vérifiez qu'il n'y a pas d'attaque de parasites sur les racines"
                
                elif any(mot in question.lower() for mot in ['insecte', 'chenille', 'parasite']):
                    reponse += "1. Inspectez les plants pour identifier le parasite\n"
                    reponse += "2. Préparez une solution de neem (100g dans 1L d'eau)\n"
                    reponse += "3. Pulvérisez tôt le matin ou tard le soir\n"
                    reponse += "4. Répétez tous les 3 jours jusqu'à disparition"
                
                elif any(mot in question.lower() for mot in ['maladie', 'tache', 'pourri']):
                    reponse += "1. Isolez les plants malades\n"
                    reponse += "2. Retirez et brûlez les parties atteintes\n"
                    reponse += "3. Évitez d'arroser les feuilles\n"
                    reponse += "4. Améliorez l'aération entre les plants"
                
                return reponse
            else:
                return reponse + "Pouvez-vous me donner plus de détails sur votre problème ? Quelle culture est concernée ?"
        
        # Ton poli - réponse chaleureuse
        if contexte['ton'] == 'poli':
            prefixe = "Avec plaisir ! "
        else:
            prefixe = ""
        
        return None  # Retourne None pour utiliser le traitement normal
    
    def suggerer_questions_liees(self, question, reponse):
        """Suggère des questions liées"""
        suggestions = []
        
        culture = self.extraire_culture(question)
        
        if culture:
            suggestions.append(f"Quelle est la meilleure période pour planter du {culture} ?")
            suggestions.append(f"Comment lutter contre les parasites du {culture} ?")
            suggestions.append(f"Quel type de sol pour le {culture} ?")
        
        if 'météo' in question.lower():
            suggestions.append("Quelles sont les prévisions pour demain ?")
            suggestions.append("Y a-t-il des risques de sécheresse ?")
        
        return suggestions[:3] 