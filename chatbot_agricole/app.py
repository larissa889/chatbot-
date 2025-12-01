from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
import re

from db import find_culture_in_text, get_planting_info, get_soil_recommendations

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_ici_123456'  # Changez ceci en production

# Initialiser la conversation dans la session
def get_conversation():
    if 'conversation' not in session:
        session['conversation'] = []
    return session['conversation']

@app.route('/')
def index():
    """Page d'accueil du chatbot"""
    conversation = get_conversation()
    # Ajouter la date et l'heure actuelles pour le message de bienvenue
    return render_template('index.html', 
                         conversation=conversation,
                         now=datetime.now())

@app.route('/', methods=['POST'])
def chat():
    """Traiter les messages de l'utilisateur"""
    user_input = request.form.get('input', '').strip()
    
    if not user_input:
        return redirect(url_for('index'))
    
    # Traiter le message
    bot_response, confidence, source = process_user_message(user_input)
    
    # Ajouter à la conversation
    conversation = get_conversation()
    conversation.append({
        'user': user_input,
        'bot': bot_response,
        'score': round(confidence * 100, 1),
        'source': source,
        'timestamp': datetime.now().strftime('%H:%M')
    })
    session['conversation'] = conversation
    
    # Si la requête est une requête AJAX, renvoyer une réponse JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'bot_response': bot_response,
            'confidence': f"{confidence:.2f}",
            'timestamp': datetime.now().strftime('%H:%M')
        })
    
    return redirect(url_for('index'))

@app.route('/reset')
def reset():
    """Réinitialiser la conversation"""
    session.pop('conversation', None)
    return redirect(url_for('index'))


def format_response(text: str) -> str:
    """
    Formate une réponse simple en HTML :
    - transforme les sauts de ligne en <br>
    - transforme **gras** en <strong>gras</strong>
    """
    if not text:
        return ""
    html = text.replace("\n", "<br>")
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    return html

def process_user_message(user_input):
    """
    Traite le message de l'utilisateur et retourne une réponse
    
    Args:
        user_input (str): Message de l'utilisateur
    
    Returns:
        tuple: (réponse, score_confiance, source)
    """
    user_input_lower = user_input.lower()
    
    # Réponses personnalisées pour les salutations
    salutations = ['bonjour', 'salut', 'coucou', 'hello', 'hey', 'bonsoir']
    if any(salut in user_input_lower for salut in salutations):
        resp = "Bonjour ! Comment puis-je vous aider avec votre exploitation agricole aujourd'hui ? 🚜"
        return format_response(resp), 0.95, "salutation"

    # 1) Conseils de plantation personnalisés basés sur SQLite
    plantation_keywords = ['planter', 'plantation', 'semer', 'semis', 'quand', 'période']
    if any(kw in user_input_lower for kw in plantation_keywords):
        culture_name = find_culture_in_text(user_input_lower)
        if culture_name:
            periods = get_planting_info(culture_name)
            if periods:
                mois_noms = [
                    "", "janvier", "février", "mars", "avril", "mai", "juin",
                    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
                ]
                lignes = []
                duree = periods[0].get("duree_cycle_jours")
                for p in periods:
                    debut = mois_noms[p["mois_debut"]]
                    fin = mois_noms[p["mois_fin"]]
                    lignes.append(
                        f"• **Région {p['region']}** : {debut.capitalize()} - {fin}."
                    )
                    if p.get("conseils"):
                        lignes.append(f"  → {p['conseils']}")

                duree_txt = f"\n\n⏱️ Durée approximative du cycle : **{duree} jours**." if duree else ""
                réponse = (
                    f"📅 **Périodes de plantation pour le {culture_name} :**\n\n"
                    + "\n".join(lignes)
                    + duree_txt
                )
                return format_response(réponse), 0.96, "base SQLite (cultures)"

    # 2) Conseils en fonction du type de sol (SQLite)
    sol_response = get_soil_recommendations(user_input_lower)
    if sol_response:
        return format_response(sol_response), 0.93, "base SQLite (sols)"
    
    # Base de connaissances agricoles (générique, hors plantation ciblée)
    knowledge_base = {
        'maladies': {
            'keywords': ['maladie', 'signes', 'symptôme', 'feuille', 'jaune', 'tache', 'malade'],
            'response': """🌿 **Signes courants de maladies des plantes:**

• **Feuilles jaunies**: Manque d'azote ou problème d'arrosage
• **Taches brunes/noires**: Infections fongiques
• **Flétrissement**: Maladies vasculaires ou déshydratation
• **Moisissure blanche**: Oïdium (champignon)
• **Déformation des feuilles**: Virus ou carences

💡 **Conseil**: Inspectez régulièrement vos plants et isolez immédiatement les plants malades.""",
            'confidence': 0.92,
            'source': 'Base de données agricole'
        },
        'meteo': {
            'keywords': ['météo', 'temps', 'pluie', 'sécheresse', 'prévision', 'climat', 'température'],
            'response': """🌤️ **Prévisions météorologiques:**

📍 **Ouagadougou, Centre:**
• **Aujourd'hui**: Ensoleillé, 32-35°C
• **Cette semaine**: Temps sec, pas de pluie
• **Tendance**: Période sèche continue

⚠️ **Alerte sécheresse**: 
• Irrigation recommandée 2-3x/semaine
• Paillage pour conserver l'humidité
• Surveillance accrue des cultures""",
            'confidence': 0.88,
            'source': 'Service météo'
        },
        'parasites': {
            'keywords': ['parasite', 'insecte', 'lutte', 'protection', 'ravageur', 'chenille', 'puceron', 'criquet'],
            'response': """🐛 **Lutte contre les parasites:**

**Méthodes naturelles:**
• Rotation des cultures (espacer 3-4 ans)
• Plantes répulsives: basilic, œillets d'Inde
• Savon noir dilué (15ml/L)
• Coccinelles contre les pucerons

**Méthodes biologiques:**
• Neem (margousier) - insecticide naturel
• Bacillus thuringiensis (chenilles)

**Prévention:**
• Inspection 2x/semaine
• Élimination plants infectés
• Espacement correct (aération)""",
            'confidence': 0.91,
            'source': 'Guide phytosanitaire'
        },
        'irrigation': {
            'keywords': ['eau', 'arrosage', 'irrigation', 'arroser', 'goutte', 'pompe'],
            'response': """💧 **Gestion de l'irrigation:**

**Besoins en eau (Burkina Faso):**
• Saison sèche: 20-30L/m²/semaine
• Saison des pluies: Selon précipitations

**Techniques recommandées:**
• Goutte-à-goutte: économie 40-60%
• Irrigation matinale (5h-8h)
• Paillage: réduit évaporation de 70%
• Bassins de rétention d'eau

**Fréquence:**
• Légumes: 2-3x/semaine
• Céréales: 1-2x/semaine
• Arbres fruitiers: 1x/semaine""",
            'confidence': 0.93,
            'source': 'Manuel irrigation'
        },
        'sol': {
            'keywords': ['sol', 'terre', 'compost', 'engrais', 'fertilisant', 'ph', 'amendement'],
            'response': """🌱 **Gestion et amélioration du sol:**

**Sols du Burkina Faso:**
• Ferrugineux tropicaux (80%)
• Argilo-limoneux (bas-fonds)
• pH: 5.5-7.0

**Amélioration:**
• Compost: 3-5 kg/m² annuellement
• Fumier bien décomposé: 2-4 kg/m²
• Paillage permanent
• Légumineuses (fixation azote)

**Test sol simple:**
• Vinaigre = pétille → sol calcaire
• Ne pétille pas → sol acide""",
            'confidence': 0.90,
            'source': 'Pédologie agricole'
        },
        'recolte': {
            'keywords': ['récolte', 'récolter', 'cueillir', 'maturité', 'rendement', 'conservation'],
            'response': """🌾 **Guide de récolte:**

**Signes de maturité:**
• **Maïs**: Soies brunies, grains fermes
• **Sorgho**: Grains durs, panicules courbées
• **Tomates**: Couleur uniforme, légèrement souples
• **Oignons**: Feuillage sec, couché

**Bonnes pratiques:**
• Récolter par temps sec
• Matin ou soir (éviter chaleur)
• Outils propres et désinfectés
• Stockage ventilé et sec

**Conservation:**
• Greniers surélevés (rongeurs)
• Température fraîche
• Inspection régulière""",
            'confidence': 0.89,
            'source': 'Guide post-récolte'
        }
    }
    
    # Recherche de la meilleure correspondance
    best_match = None
    max_matches = 0
    
    for category, data in knowledge_base.items():
        matches = sum(1 for keyword in data['keywords'] if keyword in user_input_lower)
        if matches > max_matches:
            max_matches = matches
            best_match = data
    
    # Retourner la réponse appropriée
    if best_match and max_matches > 0:
        return format_response(best_match['response']), best_match['confidence'], best_match['source']
    else:
        # Réponse par défaut simple
        default_response = (
            "🤔 Je ne suis pas sûr de bien comprendre votre question.\n\n"
            "**Je peux vous aider sur :**\n"
            "• 📅 Calendrier de plantation\n"
            "• 🌿 Maladies des plantes\n"
            "• 🌤️ Météo et sécheresse\n"
            "• 🐛 Lutte contre les parasites\n"
            "• 💧 Irrigation\n"
            "• 🌱 Amélioration du sol\n"
            "• 🌾 Récolte\n\n"
            "Posez-moi une question précise sur l'un de ces sujets."
        )
        return format_response(default_response), 0.50, 'Système'

@app.template_filter('format_datetime')
def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Filtre de template pour formater les dates"""
    if not value:
        return ""
    return value.strftime(format)

# Ajout du filtre à l'application
app.jinja_env.filters['datetime'] = format_datetime

if __name__ == '__main__':
    print("🌾 Démarrage du Chatbot Agriculture Intelligente...")
    print("📍 URL: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)