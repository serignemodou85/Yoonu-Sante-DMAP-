from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import datetime
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
import os
from django.conf import settings
from ..models import Administrateur, StructureSante, Medecin, Patient, DemandeCarte, DossierMedical, Notification, AuditLog
import plotly.graph_objects as go
from plotly.offline import plot
from django.contrib.auth.hashers import check_password, make_password
from ..models import PasswordResetToken
from dmap_app.decorators import admin_required_custom




#PAGE SUPER ADMINISTRATEUR
def super_admin_page(request):
    # RÃ©cupÃ¨re les donnÃ©es
    valides = StructureSante.objects.filter(valide=True).count()
    refuses = StructureSante.objects.filter(valide=False).count()

    # Graphe circulaire (Structures)
    labels = ['Structures ValidÃ©es', 'Structures RefusÃ©es']
    values = [valides, refuses]
    trace = go.Pie(labels=labels, values=values, hole=0.4)
    layout = go.Layout(
        title='Statistiques des structures de santÃ©',
        width=400,
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig = go.Figure(data=[trace], layout=layout)
    graph_div = plot(fig, output_type='div', include_plotlyjs=True)

    # Autres donnÃ©es
    nom_complet = request.session.get('nom_complet', 'Admin')
    nom = request.session.get('nom')
    prenom = request.session.get('prenom')
    image = request.session.get('image')
    user_type = request.session.get('user_type')
    email = request.session.get('email')
    adresse = request.session.get('adresse')
    telephone = request.session.get('telephone')
    date_creation = request.session.get('date_creation')

    nombre_medecin = Medecin.objects.count()
    nombre_patient = Patient.objects.count()
    nombre_structure = StructureSante.objects.count()
    nombre_admin = Administrateur.objects.count()
    nombre_demande = DemandeCarte.objects.count()
    nombre_dossier = DossierMedical.objects.count()

    admin_id = request.session.get('admin_id')
    notifications_non_lues = Notification.objects.filter(recepteur=admin_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    return render(request, 'Administrateur/index.html', {
        'nom_complet': nom_complet,
        'image': image,
        'nombre_medecin': nombre_medecin,
        'nombre_patient': nombre_patient,
        'nombre_structure': nombre_structure,
        'nombre_admin': nombre_admin,
        'nombre_demande': nombre_demande,
        'nombre_dossier': nombre_dossier,
        'user_type': user_type,
        'date_creation': date_creation,
        'email': email,
        'adresse': adresse,
        'telephone': telephone,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
        'graph_div': graph_div, 
        'nom': nom,
        'prenom': prenom,
    })

##PAGE GERER LISTE INSCRIPTION STRUCTURE
def gerer_inscription(request):
    structures_list = StructureSante.objects.filter(valide=False)
    structures_valide_list = StructureSante.objects.filter(valide=True)

    paginator_non_valide = Paginator(structures_list, 3)  # 3 par page
    paginator_valide = Paginator(structures_valide_list, 3)  # 3 par page

    page_non_valide = request.GET.get('page_non_valide')
    page_valide = request.GET.get('page_valide')

    structures = paginator_non_valide.get_page(page_non_valide)
    structures_valide = paginator_valide.get_page(page_valide)

    image = request.session.get('image')
    nom_complet = request.session.get('nom_complet', 'Admin')

    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Administrateur, id=admin_id) if admin_id else None

    admin_id = request.session.get('admin_id')
    notifications_non_lues = Notification.objects.filter(recepteur=admin_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    table_to_show = 'valide' if page_valide else 'non_valide'

    return render(request, 'Administrateur/page/gererInscription.html', {
        'structures': structures,
        'structures_valide': structures_valide,
        'image': image,
        'nom_complet': nom_complet,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
        'table_to_show': table_to_show
    })

##METHODE POUR VALIDER OU REFUSE UNE STRUSTURE DE SANTE
def valider_inscription(request, structure_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        structure = get_object_or_404(StructureSante, pk=structure_id)
        
        admin_id = request.session.get('admin_id')
        admin = get_object_or_404(Administrateur, id=admin_id) if admin_id else None

        if action == 'valider':
            structure.valide = True
            messages.success(request, "Inscription validÃ©e avec succÃ¨s !")
            
        elif action == 'refuser':
            structure.valide = False
            messages.error(request, "Inscription refusÃ©e avec succÃ¨s !")
            

        if admin:
            structure.created_by = admin

        structure.save()
        return redirect('gerer_inscription')

##METHODE POUR BLOQUER OU DEBLOQUER UNE STRUCTURE DE SANTE
def bloq_debloq_structure(request, structure_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        structure = get_object_or_404(StructureSante, pk=structure_id)
        
        admin_id = request.session.get('admin_id')
        admin = get_object_or_404(Administrateur, id=admin_id) if admin_id else None

        if action == 'bloquer':
            structure.bloquer = True
            messages.success(request, "Structure bloquÃ©e avec succÃ¨s !")

            send_mail(
                subject="Structure bloquÃ©e",
                message=f"Â« {getattr(admin, 'nom', 'Balla')} {getattr(admin, 'prenom', 'BEYE')} Â» vous a bloquÃ©",
                from_email="beyeballa04@gmail.com",
                recipient_list=[structure.email]
            )
        elif action == 'debloquer':
            structure.bloquer = False
            messages.success(request, "Structure dÃ©bloquÃ©e avec succÃ¨s !")
            send_mail(
                subject="Structure dÃ©bloquÃ©e",
                message=f"Â« {getattr(admin, 'nom', 'Balla')} {getattr(admin, 'prenom', 'BEYE')} Â» vous a dÃ©bloquÃ©",
                from_email="beyeballa04@gmail.com",
                recipient_list=[structure.email]
            )

        if admin:
            structure.updated_by = admin

        structure.save()
        return redirect('gerer_inscription')

##AFFICHAGE DE LA LISTE DES UTILISATEURS(MEDECIN-STRUCTURE-PATIENT)
def liste_utilisateur(request):
    medecins = Medecin.objects.filter(archiver=False, bloquer=False)
    patients = Patient.objects.filter(archiver=False , bloquer=False)
    structures = StructureSante.objects.filter(valide=True, bloquer=False)
    administrateurs = Administrateur.objects.filter(bloquer=False, role="Administrateur")

    medecins_archive = Medecin.objects.filter(archiver=True)
    patients_archive = Patient.objects.filter(archiver=True)

    medecins_bloque = Medecin.objects.filter(bloquer=True)
    patients_bloque = Patient.objects.filter(bloquer=True)
    administrateurs_bloque = Administrateur.objects.filter(bloquer=True)
    structures_bloque = StructureSante.objects.filter(bloquer=True)

    image = request.session.get('image')
    nom_complet = request.session.get('nom_complet', 'Admin')

    admin_id = request.session.get('admin_id')
    notifications_non_lues = Notification.objects.filter(recepteur=admin_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    return render(request, 'Administrateur/page/listeutilisateur.html', {
        'medecins': medecins,
        'patients': patients,
        'structures': structures,
        'medecins_archive': medecins_archive,
        'patients_archive': patients_archive,
        'medecins_bloque': medecins_bloque,
        'patients_bloque': patients_bloque,
        'administrateurs_bloque': administrateurs_bloque,
        'structures_bloque': structures_bloque,
        'image': image,
        'nom_complet': nom_complet,
        'administrateurs': administrateurs,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
        })

def ajout_admin(request):
    image = request.session.get('image')
    nom_complet = request.session.get('nom_complet', 'Admin')

    admin_id = request.session.get('admin_id')
    notifications_non_lues = Notification.objects.filter(recepteur=admin_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    return render(request, 'Administrateur/page/ajoutAdmin.html',{
        'image': image,
        'nom_complet': nom_complet,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
    })

def bloquer_medecin_admin(request, id):
    medecin = get_object_or_404(Medecin, pk=id)
    medecin.bloquer = True
    medecin.save()
    messages.success(request, f"Le mÃ©decin {medecin.nom} {medecin.prenom} a Ã©tÃ© bloquer.")
    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Administrateur, id=admin_id) if admin_id else None
    send_mail(
        subject="MÃ©decin bloquÃ©",
        message=f" Â« {getattr(admin, 'nom', 'Balla')} {getattr(admin, 'prenom', 'BEYE')} Â» vous a bloquÃ© ",
        from_email="beyeballa04@gmail.com",
        recipient_list=[medecin.email]
    )
    return redirect('liste_utilisateur')

def debloquer_medecin_admin(request, id):
    medecin = get_object_or_404(Medecin, pk=id)
    medecin.bloquer = False
    medecin.save()
    messages.success(request, f"Le mÃ©decin {medecin.nom} {medecin.prenom} a Ã©tÃ© debloquer.")
    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Administrateur, id=admin_id) if admin_id else None
    send_mail(
        subject="MÃ©decin dÃ©bloquÃ©",
        message=f" Â« {getattr(admin, 'nom', 'Balla')} {getattr(admin, 'prenom', 'BEYE')} Â» vous a dÃ©bloquÃ© ",
        from_email="beyeballa04@gmail.com",
        recipient_list=[medecin.email]
    )
    return redirect('liste_utilisateur')

def bloquer_patient_admin(request, id):
    patient = get_object_or_404(Patient, pk=id)
    patient.bloquer = True
    patient.save()
    messages.success(request, f"Le Patient {patient.nom} {patient.prenom} a Ã©tÃ© bloquer.")
    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Administrateur, id=admin_id) if admin_id else None
    send_mail(
        subject="Patient bloquÃ©",
        message=f" Â« {getattr(admin, 'nom', 'Balla')} {getattr(admin, 'prenom', 'BEYE')} Â» vous a bloquÃ© ",
        from_email="beyeballa04@gmail.com",
        recipient_list=[patient.email]
    )
    return redirect('liste_utilisateur')

def debloquer_patient_admin(request, id):
    patient = get_object_or_404(Patient, pk=id)
    patient.bloquer = False
    patient.save()
    messages.success(request, f"Le Patient {patient.nom} {patient.prenom} a Ã©tÃ© debloquer.")
    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Administrateur, id=admin_id) if admin_id else None
    send_mail(
        subject="Patient dÃ©bloquÃ©",
        message=f" Â« {getattr(admin, 'nom', 'Balla')} {getattr(admin, 'prenom', 'BEYE')} Â» vous a dÃ©bloquÃ© ",
        from_email="beyeballa04@gmail.com",
        recipient_list=[patient.email]
    )
    return redirect('liste_utilisateur')

def bloquer_structure_admin(request, id):
    structure = get_object_or_404(StructureSante, pk=id)
    structure.bloquer = True
    structure.save()
    messages.success(request, f"La structure {structure.nom} a Ã©tÃ© bloque.")
    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Administrateur, id=admin_id) if admin_id else None
    send_mail(
        subject="Structure bloquÃ©e",
        message=f" Â« {getattr(admin, 'nom', 'Balla')} {getattr(admin, 'prenom', 'BEYE')} Â» vous a bloquÃ© ",
        from_email="beyeballa04@gmail.com",
        recipient_list=[structure.email]
    )
    return redirect('liste_utilisateur')

def debloquer_structure_admin(request, id):
    structure = get_object_or_404(StructureSante, pk=id)
    structure.bloquer = False
    structure.save()
    messages.success(request, f"La structure {structure.nom} a Ã©tÃ© debloque.")
    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Administrateur, id=admin_id) if admin_id else None
    send_mail(
        subject="Structure dÃ©bloquÃ©e",
        message=f" Â« {getattr(admin, 'nom', 'Balla')} {getattr(admin, 'prenom', 'BEYE')} Â» vous a dÃ©bloquÃ© ",
        from_email="beyeballa04@gmail.com",
        recipient_list=[structure.email]
    )
    return redirect('liste_utilisateur')

def bloquer_admin(request, id):
    admin_bloque = get_object_or_404(Administrateur, pk=id)
    admin_bloque.bloquer = True
    admin_bloque.save()

    # admin connectÃ© qui effectue l'action
    admin_id = request.session.get('admin_id')
    admin_action = get_object_or_404(Administrateur, id=admin_id) if admin_id else None

    # CrÃ©ation du log
    audit_log = AuditLog.objects.create(
        administrateur=admin_action,
        action="Bloquage",
        description=f"L'administrateur {admin_action.prenom} {admin_action.nom} a bloquÃ© {admin_bloque.prenom} {admin_bloque.nom}"
    )

    messages.success(request, f"Administrateur {admin_bloque.prenom} {admin_bloque.nom} a Ã©tÃ© bloquÃ©.")

    # Envoi de mail Ã  l'administrateur bloquÃ©
    send_mail(
        subject="Administrateur bloquÃ©",
        message=f"Â« {admin_action.nom} {admin_action.prenom} Â» vous a bloquÃ©.",
        from_email="beyeballa04@gmail.com",
        recipient_list=[admin_bloque.email]
    )
    

    return redirect('liste_utilisateur')

def debloquer_admin(request, id):
    admin_cible = get_object_or_404(Administrateur, pk=id)
    admin_cible.bloquer = False
    admin_cible.save()
    messages.success(request, f"Administrateur {admin_cible.prenom} {admin_cible.nom} a Ã©tÃ© debloquer.")
    admin_id = request.session.get('admin_id')
    admin_action = get_object_or_404(Administrateur, id=admin_id) if admin_id else None
    send_mail(
        subject="Administrateur dÃ©bloquÃ©",
        message=f" Â« {getattr(admin_action, 'nom', 'Balla')} {getattr(admin_action, 'prenom', 'BEYE')} Â» vous a dÃ©bloquÃ© ",
        from_email="beyeballa04@gmail.com",
        recipient_list=[admin_cible.email]
    )
    return redirect('liste_utilisateur')

def definir_password(request, token):
    reset_token = get_object_or_404(PasswordResetToken, token=token)

    # VÃ©rifie si le token est encore valide
    if not reset_token.is_valid():
        messages.error(request, "Le lien de rÃ©initialisation a expirÃ©.")
        return redirect('user_login')

    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'Administrateur/page/definir_password.html')

        # Change le mot de passe de l'admin
        admin = reset_token.admin
        admin.password = make_password(new_password)
        admin.save()

        # Supprime ou invalide le token pour sÃ©curitÃ©
        reset_token.delete()

        messages.success(request, "Mot de passe mis Ã  jour avec succÃ¨s.")
        return redirect('user_login')  # ou page d'accueil
    context = {
        'token': token,  # <- Assure-toi que tu passes bien Ã§a ici
        'message': '',
        'success': False,
    }
    return render(request, 'Administrateur/page/definir_password.html', context)

def ajouter_un_admin(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # VÃ©rifie si email existe dÃ©jÃ 
        if Administrateur.objects.filter(email=email).exists():
            messages.error(request, "Cet email existe dÃ©jÃ  dans le systÃ¨me.")
            return render(request, 'Administrateur/page/ajoutAdmin.html')

        # Lecture des autres champs
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        sexe = request.POST.get('sexe')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')
        image = request.FILES.get('image')

        # CrÃ©ation de l'administrateur SANS mot de passe dÃ©fini (peut Ãªtre vide ou un hash quelconque)
        admin = Administrateur(
            nom=nom,
            prenom=prenom,
            email=email,
            sexe=sexe,
            telephone=telephone,
            adresse=adresse,
            image=image,
            status="admin",
        )
        admin.password = make_password('temporary_password123')  # mot de passe temporaire (obligatoire pour le User model)
        admin.save()

        # CrÃ©ation du token custom
        reset_token = PasswordResetToken.objects.create(admin=admin)

        reset_password_link = request.build_absolute_uri(
            f'/definir_password/{reset_token.token}/'
        )

        # Envoi de l'email
        subject = "DÃ©finissez votre mot de passe"
        message = (f"Bonjour {admin.prenom} {admin.nom},\n\n"
                f"Vous avez Ã©tÃ© ajoutÃ© comme administrateur.\n"
                f"Votre email est : {admin.email}\n"
                f"Veuillez dÃ©finir votre mot de passe en cliquant sur le lien suivant :\n{reset_password_link}\n\n"
                "Cordialement.")
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [admin.email]

        send_mail(subject, message, from_email, recipient_list)

        messages.success(request, "Administrateur ajoutÃ© avec succÃ¨s. Un email lui a Ã©tÃ© envoyÃ© pour dÃ©finir son mot de passe.")
        return redirect('ajout_admin')

    return render(request, 'Administrateur/page/ajoutAdmin.html')

def promouvoir_admin(request, admin_id):
    admin = get_object_or_404(Administrateur, id=admin_id)
    admin.role = "super_admin"
    admin.save()
    messages.success(request, f"Administrateur {admin.prenom} {admin.nom} a Ã©tÃ© promu en Super Admin.")
    return redirect('liste_utilisateur')

def profil_admin(request):
    image = request.session.get('image')
    nom_complet = request.session.get('nom_complet', 'Admin')
    email = request.session.get('email')
    adresse = request.session.get('adresse')
    telephone = request.session.get('telephone')
    nom = request.session.get('nom')
    prenom = request.session.get('prenom')

    admin_id = request.session.get('admin_id')
    notifications_non_lues = Notification.objects.filter(recepteur=admin_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    return render(request, 'Administrateur/page/profilAdmin.html', {
        'image': image,
        'nom_complet': nom_complet,
        'email': email,
        'adresse': adresse,
        'telephone': telephone,
        'nom': nom,
        'prenom': prenom,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
        })

def changer_mot_de_passe(request):
    image = request.session.get('image')
    nom_complet = request.session.get('nom_complet', 'Admin')
    email = request.session.get('email')
    adresse = request.session.get('adresse')
    telephone = request.session.get('telephone')
    if request.method == 'POST':
        email = request.session.get('email')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        try:
            admin = Administrateur.objects.get(email=email)
        except Administrateur.DoesNotExist:
            messages.error(request, "Administrateur introuvable.")
            return redirect('profil_admin')
        
        if not check_password(old_password, admin.password):
            messages.error(request, "Ancien mot de passe incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            admin.password = make_password(new_password)
            admin.save()
            Notification.objects.create(
                recepteur=admin.id,
                type_notification="Validation",
                description="Vous avez changÃ© votre mot de passe"
            )
            messages.success(request, "Mot de passe changÃ© avec succÃ¨s.")
            return redirect('profil_admin')  # redirige vers le profil
    admin_id = request.session.get('admin_id')
    notifications = Notification.objects.filter(recepteur=admin_id,lu=False).order_by('-created_at')[:4]

    return render(request, 'Administrateur/page/profilAdmin.html', {
        'image': image,
        'nom_complet': nom_complet,
        'email': email,
        'adresse': adresse,
        'telephone': telephone,
        'notifications': notifications,
        })

def modifier_infos_admin(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        messages.error(request, "Admin non authentifiÃ©.")
        return redirect('user_login')  

    admin = get_object_or_404(Administrateur, id=admin_id)

    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        # Mise Ã  jour des champs
        admin.nom = nom
        admin.prenom = prenom
        admin.email = email
        admin.telephone = telephone
        admin.adresse = adresse
        admin.save()

        # Mise Ã  jour de la session
        request.session['nom_complet'] = f"{admin.prenom} {admin.nom}"
        request.session['email'] = admin.email
        request.session['telephone'] = admin.telephone
        request.session['adresse'] = admin.adresse

        messages.success(request, "Informations mises Ã  jour avec succÃ¨s.")
        Notification.objects.create(
            recepteur=admin.id,
            type_notification="Validation",
            description="Vous avez modifiÃ© vos informations"
        )
        return redirect('profil_admin')

    return render(request, 'Administrateur/page/profilAdmin.html', {'admin': admin})


def modifier_photo(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        messages.error(request, "Admin non authentifiÃ©.")
        return redirect('user_login')

    admin = get_object_or_404(Administrateur, id=admin_id)

    if request.method == 'POST':
        image = request.FILES.get('photo')
        if image:
            admin.image = image
            admin.save()
            request.session['image'] = admin.image.url if admin.image else None
            Notification.objects.create(
                recepteur=admin.id,
                type_notification="Validation",
                description="Vous avez modifiÃ© votre photo de profil"
            )
            messages.success(request, "Photo de profil mise Ã  jour avec succÃ¨s.")
        else:
            messages.warning(request, "Aucune image n'a Ã©tÃ© sÃ©lectionnÃ©e.")

        return redirect('profil_admin')

    return render(request, 'Administrateur/page/profilAdmin.html', {'admin': admin})

def audit_acces_dossier_medical(request):
    audit_logs = AuditLog.objects.all()

    nom_complet = request.session.get('nom_complet', 'Admin')
    image = request.session.get('image')
    user_type = request.session.get('user_type')
    email = request.session.get('email')
    adresse = request.session.get('adresse')

    return render(request, 'Administrateur/page/audit.html', {
        'audit_logs': audit_logs,
        'nom_complet': nom_complet,
        'image': image,
        'user_type': user_type,
        'email': email,
        'adresse': adresse,
    })

def link_callback(uri, rel):
    path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    return path

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def carte_patient_pdf(request, demande_id):
    demande = get_object_or_404(DemandeCarte, id=demande_id)
    image = request.session.get('image')
    context = {
        'demande': demande,
        'date_emission': datetime.today().strftime("%d/%m/%Y"),
        'image': image
    }
    return render_to_pdf('Administrateur/page/carte_patient.html', context)

def listeDemandeCarte(request):
    nom_complet = request.session.get('nom_complet', 'Admin')
    image = request.session.get('image')
    demande_carte = DemandeCarte.objects.all()

    admin_id = request.session.get('admin_id')
    notifications_non_lues = Notification.objects.filter(recepteur=admin_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()
    return render(request, 'Administrateur/page/listedemandecarte.html', {
        'demande_carte': demande_carte,
        'nom_complet': nom_complet,
        'image': image,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
        })

def notification(request):
    nom_complet = request.session.get('nom_complet', 'Admin')
    image = request.session.get('image')
    admin_id = request.session.get('admin_id')

    Notification.objects.filter(recepteur=admin_id, lu=False).update(lu=True)
    notifications = Notification.objects.filter(recepteur=admin_id).order_by('-created_at')

    return render(request, 'Administrateur/page/notification.html', {
        'notifications': notifications,
        'nom_complet': nom_complet,
        'image': image,
    })

#PAGE ADMINISTRATEUR
def administrateur_page(request):
    nom_complet = request.session.get('nom_complet', 'Admin')
    image = request.session.get('image')
    user_type = request.session.get('user_type')
    email = request.session.get('email')
    adresse = request.session.get('adresse')
    telephone = request.session.get('telephone')
    date_creation = request.session.get('date_creation')

    return render(request, 'Administrateur/index1.html', {
        'nom_complet': nom_complet,
        'image': image,
        'user_type': user_type,
        'email': email,
        'adresse': adresse,
        'telephone': telephone,
        'date_creation': date_creation,
    })

def gerer_inscription_admin(request):
    structures_list = StructureSante.objects.filter(valide=False)
    structures_valide_list = StructureSante.objects.filter(valide=True)

    paginator_non_valide = Paginator(structures_list, 3)  # 3 par page
    paginator_valide = Paginator(structures_valide_list, 3)  # 3 par page

    page_non_valide = request.GET.get('page_non_valide')
    page_valide = request.GET.get('page_valide')

    structures = paginator_non_valide.get_page(page_non_valide)
    structures_valide = paginator_valide.get_page(page_valide)

    image = request.session.get('image')
    nom_complet = request.session.get('nom_complet', 'Admin')

    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Administrateur, id=admin_id) if admin_id else None

    admin_id = request.session.get('admin_id')
    notifications_non_lues = Notification.objects.filter(recepteur=admin_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    table_to_show = 'valide' if page_valide else 'non_valide'

    nom_complet = request.session.get('nom_complet', 'Admin')
    image = request.session.get('image')
    user_type = request.session.get('user_type')
    email = request.session.get('email')
    adresse = request.session.get('adresse')
    telephone = request.session.get('telephone')
    date_creation = request.session.get('date_creation')

    return render(request, 'Administrateur/page/gerer_inscription_admin.html', {
        'structures': structures,
        'structures_valide': structures_valide,
        'page_non_valide': page_non_valide,
        'page_valide': page_valide,
        'table_to_show': table_to_show,
        'nom_complet': nom_complet,
        'image': image,
        'user_type': user_type,
        'email': email,
        'adresse': adresse,
        'telephone': telephone,
        'date_creation': date_creation,
    })

def listeDemandeCarte_admin(request):
    demande_carte = DemandeCarte.objects.all()

    nom_complet = request.session.get('nom_complet', 'Admin')
    image = request.session.get('image')
    user_type = request.session.get('user_type')
    email = request.session.get('email')
    adresse = request.session.get('adresse')

    return render(request, 'Administrateur/page/listeDemandeCarte_admin.html', {
        'demande_carte': demande_carte,
        'nom_complet': nom_complet,
        'image': image,
        'user_type': user_type,
        'email': email,
        'adresse': adresse,
    })

def notification_admin(request):
    nom_complet = request.session.get('nom_complet', 'Admin')
    image = request.session.get('image')
    admin_id = request.session.get('admin_id')

    Notification.objects.filter(recepteur=admin_id, lu=False).update(lu=True)
    notifications = Notification.objects.filter(recepteur=admin_id).order_by('-created_at')

    return render(request, 'Administrateur/page/notification_admin.html', {
        'notifications': notifications,
        'nom_complet': nom_complet,
        'image': image,
    })

def profil_admin_page(request):
    image = request.session.get('image')
    nom_complet = request.session.get('nom_complet', 'Admin')
    email = request.session.get('email')
    adresse = request.session.get('adresse')
    telephone = request.session.get('telephone')
    nom = request.session.get('nom')
    prenom = request.session.get('prenom')

    admin_id = request.session.get('admin_id')
    notifications_non_lues = Notification.objects.filter(recepteur=admin_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()
    return render(request, 'Administrateur/page/profil_admin_page.html', {
        'image': image,
        'nom_complet': nom_complet,
        'email': email,
        'adresse': adresse,
        'telephone': telephone,
        'nom': nom,
        'prenom': prenom,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,

    })

def changer_mot_de_passe_admin(request):
    image = request.session.get('image')
    nom_complet = request.session.get('nom_complet', 'Admin')
    email = request.session.get('email')
    adresse = request.session.get('adresse')
    telephone = request.session.get('telephone')
    if request.method == 'POST':
        email = request.session.get('email')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        try:
            admin = Administrateur.objects.get(email=email)
        except Administrateur.DoesNotExist:
            messages.error(request, "Administrateur introuvable.")
            return redirect('profil_admin_page')
        
        if not check_password(old_password, admin.password):
            messages.error(request, "Ancien mot de passe incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            admin.password = make_password(new_password)
            admin.save()
            Notification.objects.create(
                recepteur=admin.id,
                type_notification="Validation",
                description="Vous avez changÃ© votre mot de passe"
            )
            messages.success(request, "Mot de passe changÃ© avec succÃ¨s.")
            return redirect('profil_admin_page')  # redirige vers le profil
    admin_id = request.session.get('admin_id')
    notifications = Notification.objects.filter(recepteur=admin_id,lu=False).order_by('-created_at')[:4]

    return render(request, 'Administrateur/page/profil_admin_page.html', {
        'image': image,
        'nom_complet': nom_complet,
        'email': email,
        'adresse': adresse,
        'telephone': telephone,
        'notifications': notifications,
        })

def modifier_infos_administrateur(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        messages.error(request, "Admin non authentifiÃ©.")
        return redirect('user_login')  

    admin = get_object_or_404(Administrateur, id=admin_id)

    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        # Mise Ã  jour des champs
        admin.nom = nom
        admin.prenom = prenom
        admin.email = email
        admin.telephone = telephone
        admin.adresse = adresse
        admin.save()

        # Mise Ã  jour de la session
        request.session['nom_complet'] = f"{admin.prenom} {admin.nom}"
        request.session['email'] = admin.email
        request.session['telephone'] = admin.telephone
        request.session['adresse'] = admin.adresse

        messages.success(request, "Informations mises Ã  jour avec succÃ¨s.")
        Notification.objects.create(
            recepteur=admin.id,
            type_notification="Validation",
            description="Vous avez modifiÃ© vos informations"
        )
        return redirect('profil_admin_page')

    return render(request, 'Administrateur/page/profil_admin_page.html', {'admin': admin})


def modifier_photo_admin(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        messages.error(request, "Admin non authentifiÃ©.")
        return redirect('user_login')

    admin = get_object_or_404(Administrateur, id=admin_id)

    if request.method == 'POST':
        image = request.FILES.get('photo')
        if image:
            admin.image = image
            admin.save()
            request.session['image'] = admin.image.url if admin.image else None
            Notification.objects.create(
                recepteur=admin.id,
                type_notification="Validation",
                description="Vous avez modifiÃ© votre photo de profil"
            )
            messages.success(request, "Photo de profil mise Ã  jour avec succÃ¨s.")
        else:
            messages.warning(request, "Aucune image n'a Ã©tÃ© sÃ©lectionnÃ©e.")

        return redirect('profil_admin_page')

    return render(request, 'Administrateur/page/profil_admin_page.html', {'admin': admin})


_ADMIN_PROTECTED_VIEWS = (
    'super_admin_page',
    'gerer_inscription',
    'valider_inscription',
    'bloq_debloq_structure',
    'liste_utilisateur',
    'ajout_admin',
    'bloquer_medecin_admin',
    'debloquer_medecin_admin',
    'bloquer_patient_admin',
    'debloquer_patient_admin',
    'bloquer_structure_admin',
    'debloquer_structure_admin',
    'bloquer_admin',
    'debloquer_admin',
    'ajouter_un_admin',
    'promouvoir_admin',
    'profil_admin',
    'changer_mot_de_passe',
    'modifier_infos_admin',
    'modifier_photo',
    'audit_acces_dossier_medical',
    'carte_patient_pdf',
    'listeDemandeCarte',
    'notification',
    'administrateur_page',
    'gerer_inscription_admin',
    'listeDemandeCarte_admin',
    'notification_admin',
    'profil_admin_page',
    'changer_mot_de_passe_admin',
    'modifier_infos_administrateur',
    'modifier_photo_admin',
)

for _view_name in _ADMIN_PROTECTED_VIEWS:
    globals()[_view_name] = admin_required_custom(globals()[_view_name])

