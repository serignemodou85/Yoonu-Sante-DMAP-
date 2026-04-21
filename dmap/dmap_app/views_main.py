from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password
from .forms import UtilisateurForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect, get_object_or_404
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
import plotly.graph_objs as go
import plotly.offline as opy
from collections import Counter
import uuid
from django.views.decorators.cache import never_cache
from datetime import datetime
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
import qrcode
from io import BytesIO
from django.http import HttpResponse
import uuid
from django.utils import timezone
from datetime import timedelta
import base64
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.password_validation import validate_password
import codecs
from django.http import HttpResponseForbidden
import hashlib
import random
import string
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.core.paginator import Paginator
import os
import plotly.graph_objs as go
from plotly.offline import plot
from django.db import models
from .decorators import login_required_custom
from django.core.paginator import Paginator
from .models import Administrateur, StructureSante, Utilisateur, Medecin, Service, Specialisation,Notification, Patient, Consultation, DossierMedical, ExamenMedical, Prescription, DocumentMedical, InfoConfidentielle, DemandeCarte, PasswordResetTokenMedecin,PasswordResetToken, AlerteSanitaire, RendezVous, AuditLog, Temoin, MessageVisiteur




# PAGE ACCUEIL(VITRINE)
def index(request):
    temoins = Temoin.objects.filter(affichage= True)
    return render(request, 'vitrine/index.html', {'temoins': temoins})

def ajouter_temoin(request):
    temoins = Temoin.objects.filter(affichage= True)
    if request.method == 'POST':
        nom = request.POST['nom']
        fonction = request.POST['fonction']
        description = request.POST['description']
        photo = request.FILES['photo']
        etoiles = request.POST['etoiles']

        temoin = Temoin(
            nom=nom,
            fonction=fonction,
            description=description,
            photo=photo,
            etoiles=int(etoiles),
            affichage=False
        )
        temoin.save()
        messages.success(request, f"Votre témoignage a été envoyé avec succès et sera publié après modération.")

        return redirect('index')

    return render(request, 'vitrine/index.html', {'temoins': temoins})


#PAGE MODIFIER PASSWORD(PASSWORD OUBLIER)
def password_oublie_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # Cherche l'utilisateur dans les différents modèles
        user = None
        for model in [Medecin, Utilisateur, StructureSante, Administrateur]:
            try:
                user = model.objects.get(email=email)
                break
            except model.DoesNotExist:
                continue

        if user:
            subject = "Modification de mot de passe"
            from_email = settings.EMAIL_HOST_USER
            to = [email]

            # Génération du token et uid
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = default_token_generator.make_token(user)

            # Domaine de l'application (http://127.0.0.1:8000)
            domaine = request.build_absolute_uri('/')[:-1]

            # Contexte pour le mail HTML
            context = {
                "email": email,
                "uid": uid,
                "token": token,
                "domaine": domaine
            }

            html_content = render_to_string("email.html", context)
            message = EmailMultiAlternatives(subject, "", from_email, to)
            message.attach_alternative(html_content, "text/html")
            message.send()

            messages.success(request, "Un e-mail de réinitialisation a été envoyé.")
        else:
            messages.error(request, "Vous n'avez pas de compte. Merci de vous inscrire.")

    return render(request, 'password_oublie.html')

# Regroupement des modèles dans une liste
CUSTOM_USERS = [Medecin, Utilisateur, StructureSante, Administrateur]

def update_password(request, token, uid):
    try:
        user_id = urlsafe_base64_decode(uid).decode("utf-8")
    except Exception:
        return HttpResponseForbidden("Lien invalide. UID incorrect.")

    user = None
    for model in CUSTOM_USERS:
        try:
            user = model.objects.get(id=user_id)
            break
        except model.DoesNotExist:
            continue

    if not user:
        return HttpResponseForbidden("Utilisateur introuvable.")

    if not default_token_generator.check_token(user, token):
        return HttpResponseForbidden("Token invalide ou expiré.")

    error = False
    success = False
    message = ""

    if request.method == "POST":
        password = request.POST.get("password")
        repassword = request.POST.get("repassword")

        if password == repassword:
            try:
                validate_password(password, user)
                if hasattr(user, 'set_password'):
                    user.set_password(password)
                else:
                    user.password = make_password(password)
                user.save()
                success = True
                message = "Votre mot de passe a été modifié avec succès !"
            except ValidationError as e:
                error = True
                message = " ".join(e.messages)
        else:
            error = True
            message = "Les deux mots de passe ne correspondent pas."

    context = {
        "error": error,
        "success": success,
        "message": message,
        'token': token,
        'uid': uid,
    }
    return render(request, "update_password.html", context)


# PAGE DE CONNEXION
def user_login(request):
    form = UtilisateurForm()
    return render(request, 'login.html',{ 
         'form': form
        })
#POUR LA DECONNEXION
def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, "Déconnexion réussie")
    return redirect('user_login')

# PAGE D'INSCRIPTION
def inscription_view(request):
    return render(request, 'inscription.html')

def inscription_structure(request):
    if request.method == 'POST':
        try:
            nom = request.POST.get('nom')
            structureType = request.POST.get('structureType')
            email = request.POST.get('email')
            password = request.POST.get('password')
            adresse = request.POST.get('adresse')
            ville = request.POST.get('ville')
            region = request.POST.get('region')
            telephone = request.POST.get('telephone')

            hashed_password = make_password(password)

            structure = StructureSante(
                nom=nom,
                type_structure=structureType,
                email=email,
                password=hashed_password,
                adresse=adresse,
                ville=ville,
                region=region,
                telephone=telephone,
            )
            structure.save()

            # Créer une notification interne
            Notification.objects.create(
                type_notification="Notification",
                description=f"Bienvenue sur notre plateforme : {structure.nom}",
                recepteur=structure.id
            )
            

            # Envoyer email à l'admin
            sujet_admin = f"Nouvelle inscription de structure : {structure.nom}"
            message_admin = f"""
                Une nouvelle structure de santé s'est inscrite sur la plateforme.

                Nom : {structure.nom}
                Type : {structure.type_structure}
                Email : {structure.email}
                Adresse : {structure.adresse}, {structure.ville}, {structure.region}
                Téléphone : {structure.telephone}

                Merci de valider l'inscription depuis l'interface d'administration.
            """

            send_mail(
                sujet_admin,
                message_admin,
                settings.EMAIL_HOST_USER,
                [settings.SYSTEM_ADMIN_EMAIL],
                fail_silently=False,
            )

            # Envoyer email à la structure
            sujet_structure = "Merci de patienter pour la validation de votre compte"
            message_structure = f"""
                Bonjour {structure.nom},

                Merci de patienter pour la validation de votre compte. Nous vous informerons dès que votre inscription sera validée par l'administrateur.

                Cordialement,
                L'équipe de gestion
            """

            send_mail(
                sujet_structure,
                message_structure,
                settings.EMAIL_HOST_USER,
                [structure.email],  # Email du structure qui vient de s'inscrire
                fail_silently=False,
            )

            messages.success(request, "Inscription reussie. Vous pouvez attendre la validation de l'admin")
            return redirect('user_login')  # doit correspondre au nom de ta vue de login

        except Exception as e:
            print("Erreur pendant l'inscription :", e)
            return render(request, 'login.html', {'erreur': str(e)})

    return render(request, 'login.html')

#inscription patient 
def inscription_patient(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')

        email_exists = (
            Patient.objects.filter(email=email).exists() or
            Medecin.objects.filter(email=email).exists() or
            Utilisateur.objects.filter(email=email).exists() or
            StructureSante.objects.filter(email=email).exists() or
            Administrateur.objects.filter(email=email).exists()
        )

        telephone_exists = Patient.objects.filter(telephone=telephone).exists()

        if email_exists:
            messages.error(request, "Cet email est déjà utilisé.")
            return redirect('inscription_patient')

        if telephone_exists:
            messages.error(request, "Ce numéro de téléphone est déjà utilisé.")
            return redirect('inscription_patient')

        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        sexe = request.POST.get('sexe')
        adresse = request.POST.get('adresse')
        date_naissance = request.POST.get('date_naissance')
        image = request.FILES.get('image')
        password = request.POST.get('password')
        hashed_password = make_password(password)

        username = f"{nom.lower()}{prenom.lower()}{uuid.uuid4().hex[:6]}"

        patient = Patient(
            username=username,
            nom=nom,
            prenom=prenom,
            sexe=sexe,
            telephone=telephone,
            adresse=adresse,
            date_naissance=date_naissance,
            email=email,
            image=image,
            password=hashed_password,
            statut="patient"
        )
        patient.save()

        Notification.objects.create(
            type_notification=f"Bienvenue sur notre plateforme{patient.nom}",
            description=f"Vous pouvez consulter votre dossier medical en toute securite",
            recepteur=patient
    
        )

        messages.success(request, "Compte créé avec succès. Vous pouvez maintenant vous connecter.")
        return redirect('user_login')

    return render(request, 'login.html')


# METHODE POUR GERER L'AUTHENTIFICATION DES UTILISATEURS
def store(request):
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")

        # ADMIN PAR DEFAUT (1er utilisateur)
        if email == "admin2025@gmail.com" and password == "Passer@2025":
            request.session['user_type'] = 'super_admin'
            request.session['admin_id'] = 0  
            request.session['email'] = email
            request.session['nom_complet'] = "Balla BEYE"
            request.session['nom'] = "BEYE"
            request.session['prenom'] = "Balla"
            return redirect('super_admin_page')

        # AUTHENTIFICATION ADMIN OU SUPER ADMIN(depuis BDD)
        try:
            admin = Administrateur.objects.get(email=email)
            if check_password(password, admin.password):
                # Vérification si l'administrateur est bloqué
                if admin.bloquer:
                    messages.error(request, "Votre compte a été bloqué.")
                    return render(request, "login.html")

                request.session['user_type'] = 'admin'
                request.session['admin_id'] = admin.id
                request.session['email'] = admin.email
                request.session['adresse'] = admin.adresse
                request.session['telephone'] = admin.telephone
                request.session['nom'] = admin.nom
                request.session['role'] = admin.role
                request.session['prenom'] = admin.prenom
                request.session['date_creation'] = admin.created_at.isoformat()
                request.session['nom_complet'] = f"{admin.prenom} {admin.nom}"
                request.session['image'] = admin.image.url if admin.image else None

                if admin.role == 'Administrateur':
                    messages.success(request, f"Bienvenue sur notre plateforme {admin.prenom} {admin.nom}!")
                    return redirect('administrateur_page')
                elif admin.role == 'super_admin':
                    messages.success(request, f"Bienvenue sur notre plateforme {admin.prenom} {admin.nom}!")
                    return redirect('super_admin_page')
                else:
                    messages.error(request, "Votre compte n'a pas de role.")
                    return render(request, "login.html")

        except Administrateur.DoesNotExist:
            pass

        # AUTHENTIFICATION STRUCTURE DE SANTE
        try:
            structure = StructureSante.objects.get(email=email)
            if check_password(password, structure.password):
                # Vérification si la structure est bloquée
                if structure.bloquer:
                    messages.error(request, "Votre structure de santé a été bloquée.")
                    return render(request, "login.html")

                if not structure.valide:
                    messages.error(request, "Votre structure n'est pas encore validée.")
                    return render(request, "login.html")
                
                request.session['type_structure'] = structure.type_structure
                request.session['structure_id'] = structure.id
                request.session['email'] = structure.email
                request.session['nom'] = structure.nom
                request.session['image'] = structure.image.url if structure.image else None
                request.session['ville'] = structure.ville
                request.session['region'] = structure.region
                request.session['site_web'] = structure.site_web
                request.session['telephone'] = structure.telephone
                request.session['adresse'] = structure.adresse
                request.session['date_inscription'] = structure.date_inscription.strftime('%Y-%m-%d %H:%M:%S')
                request.session['created_at'] = structure.created_at.isoformat()


                messages.success(request, f"Bienvenue sur notre plateforme {structure.nom}!")
                return redirect('structure')
        except StructureSante.DoesNotExist:
            pass

        # AUTHENTIFICATION UTILISATEUR
        try:
            user = Utilisateur.objects.get(email=email)
            if check_password(password, user.password):
                # Vérification si l'utilisateur est archivé ou bloqué
                if user.archiver or user.bloquer:
                    messages.error(request, "Votre compte a été désactivé ou bloqué.")
                    return render(request, "login.html")

                login(request, user)
                request.session['user_type'] = user.statut
                request.session['user_id'] = user.id
                request.session['full_name'] = f"{user.nom} {user.prenom}"
                request.session['telephone'] = user.telephone
                request.session['adresse'] = user.adresse
                request.session['email'] = user.email
                request.session['nom'] = user.nom
                request.session['prenom'] = user.prenom
                request.session['image'] = user.image.url if user.image else None

                if user.statut == "patient":
                    messages.success(request, f"Bienvenue sur notre plateforme {user.prenom} {user.nom}!")
                    return redirect('patient')
                elif user.statut == "medecin":
                    messages.success(request, f"Bienvenue sur notre plateforme {user.prenom} {user.nom} !")
                    return redirect('medecin')
        except Utilisateur.DoesNotExist:
            pass

        # AUCUNE CORRESPONDANCE
        error_message = "Email ou mot de passe incorrect."
        messages.error(request, "Email ou mot de passe incorrect.")
        return render(request, "login.html", {"error_message": error_message})

    return render(request, "login.html")

def message_visiteur(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        contenu_message = request.POST.get('message')
        type_utilisateur = request.POST.get('type_utilisateur')

        message_obj = MessageVisiteur(
            nom=nom,
            email=email,
            telephone=telephone,
            message=contenu_message,
            type_utilisateur=type_utilisateur
        )
        message_obj.save()
        messages.success(request, "✅ Votre message a été envoyé avec succès.")
        return redirect('index') 
    return render(request, 'vitrine/index.html')

#PAGE SOLUTION MEDECIN
def solution_medecin(request):
    return render(request, 'vitrine/page/solution_medecin.html')

#PAGE SOLUTION STRUCTURE
def solution_structure(request):
    return render(request, 'vitrine/page/solution_structure.html')

#PAGE SOLUTION PATIENT
def solution_patient(request):
    return render(request, 'vitrine/page/solution_patient.html')




