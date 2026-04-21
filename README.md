# DMAP - Plateforme de Gestion des Dossiers Médicaux

Une plateforme Django pour la gestion centralisée des dossiers médicaux numériques, avec support pour patients, médecins, structures de santé et administrateurs.

## 🔧 Configuration

### 1. Installation

Clone le projet et navigue dans le répertoire:
```bash
cd c:\Users\MODOU\DMAP
```

### 2. Configuration de l'environnement

Crée un fichier `.env` basé sur `.env.example`:
```bash
cp .env.example .env
```

Édite `.env` avec tes paramètres:
```env
SECRET_KEY=ta-clé-secrète-très-sécurisée
DEBUG=False
DB_PASSWORD=ton-mot-de-passe-mysql
EMAIL_HOST_USER=ton-email@gmail.com
EMAIL_HOST_PASSWORD=ton-app-password-gmail
```

### 3. Installation des dépendances

Utilise ton environnement virtuel:
```bash
# Activate virtual environment
my_venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Base de données

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Démarrer le serveur

```bash
python manage.py runserver
```

Accède à l'application sur: `http://localhost:8000`  
Accède à l'admin Django sur: `http://localhost:8000/admin`

---

## 🔒 Corrections de Sécurité Apportées

### ✅ **1. Secrets Gérés par Variables d'Environnement**
- **Avant**: SECRET_KEY, identifiants MySQL et Gmail en dur dans `settings.py`
- **Après**: Tous les secrets chargés via `python-decouple` depuis `.env`
- **Impact**: Empêche l'exposition de credentials en cas de fuite Git

### ✅ **2. DEBUG désactivé en production**
- **Avant**: `DEBUG = True` en permanence
- **Après**: `DEBUG = config('DEBUG', default=False, cast=bool)` depuis `.env`
- **Impact**: Empêche la divulgation de stacktraces en production

### ✅ **3. Admin Django configuré**
- **Avant**: `admin.py` vide, aucun modèle enregistré
- **Après**: Tous les 24 modèles enregistrés avec recherche et filtrage avancés
- **Impact**: Interface d'administration complètement fonctionnelle

### ✅ **4. Bugs de typage corrigés**
- **Avant**: `def _str_(self):` dans AuditLog, Conversation, ChatMessage
- **Après**: `def __str__(self):` correct
- **Impact**: Représentation correct des modèles en admin et dans les logs

### ✅ **5. Code nettoyé**
- **Avant**: Imports dupliqués dans `views_patient.py`
- **Après**: Imports centralisés et organisés
- **Impact**: Code plus maintenable et performant

### ✅ **6. requirements.txt ajouté**
- **Après**: Fichier complet listant toutes les dépendances
- **Impact**: Environnement reproductible et versionnage des dépendances

### ✅ **7. .gitignore ajouté**
- **Après**: Fichier configuré pour exclure fichiers sensibles et temporaires
- **Impact**: Prévient l'accidentelle push de `.env` et fichiers volumineux

---

## 📦 Architecture

### Modèles Principaux (24)
- **Authentification**: Administrateur, StructureSante, Medecin, Patient, Utilisateur
- **Dossiers Médicaux**: DossierMedical, Consultation, ExamenMedical, Prescription
- **Documents**: DocumentMedical, InfoConfidentielle
- **Système**: Notification, DemandeCarte, RendezVous, AlerteSanitaire
- **IA**: ChatMessage, Conversation (chatbot médical)
- **Audit**: AuditLog, PasswordResetToken(s)
- **Public**: Temoin, MessageVisiteur

### Technologies
- **Backend**: Django 5.2, MySQL
- **IA**: Ollama + LangChain + FAISS (RAG)
- **Frontend**: Django Templates, Bootstrap, jQuery, Plotly
- **Sécurité**: python-decouple, CSRF, XSS protection

---

## 🚀 Fonctionnalités

✅ Gestion complète des dossiers médicaux  
✅ Consultations et rendez-vous  
✅ Prescriptions et examens médicaux  
✅ Chatbot IA médical avec RAG  
✅ Authentification multi-rôles  
✅ Cartes de santé QR code  
✅ Alertes sanitaires (don de sang)  
✅ Audit des accès aux dossiers  

---

## ⚠️ À Faire Avant Production

- [ ] Générer une nouvelle `SECRET_KEY` robuste
- [ ] Configurer un mot de passe MySQL fort
- [ ] Mettre en place SSL/HTTPS
- [ ] Configurer un système de cache (Redis)
- [ ] Implémenter les tests unitaires
- [ ] Tester avec une vraie instance Ollama
- [ ] Configurer la sauvegarde des bases de données
- [ ] Mettre en place le monitoring
- [ ] Documenter les API endpoints
- [ ] Implémenter la pagination complète

---

## 🤝 Support

Pour les questions ou issues, créer un issue ou contacter l'équipe de développement.

---

**Dernière mise à jour**: 21 avril 2026
