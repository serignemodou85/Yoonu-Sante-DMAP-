from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.conf import settings
from datetime import datetime
import uuid
from ..forms import UtilisateurForm
from ..models import Administrateur, StructureSante, Utilisateur, Medecin, Service, Specialisation,Notification, Patient, Consultation, DossierMedical, ExamenMedical, Prescription, DocumentMedical, InfoConfidentielle, DemandeCarte, PasswordResetTokenMedecin,PasswordResetToken, AlerteSanitaire, RendezVous, AuditLog
from dmap_app.decorators import login_required_custom



##########################PARTIE STRUCTURE DE SANTE #########################################################
def structure(request):
    nom = request.session.get('nom')
    structure_id = request.session.get('structure_id')
    image = request.session.get('image')
    type_structure = request.session.get('type_structure')
    date_str = request.session.get('date_inscription')
    if date_str:
        date_inscription = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

    structure_id = request.session.get('structure_id')
    notifications_non_lues = Notification.objects.filter(recepteur=structure_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    nombre_medecins = Medecin.objects.filter(structure_sante=structure_id).count()
    nombre_alerte_sanitaire = AlerteSanitaire.objects.filter(structure_sante=structure_id).count()

    medecins_structure = Medecin.objects.filter(structure_sante=structure_id)
    consultations_structure = Consultation.objects.filter(medecin__in=medecins_structure).count()
    prescriptions_structure = Prescription.objects.filter(medecin__in=medecins_structure).count()
    examens_structure = ExamenMedical.objects.filter(medecin__in=medecins_structure).count()

    return render(request, 'Structure/index.html', {
        'nom': nom,
        'structure_id': structure_id,
        'nombre_medecins': nombre_medecins,
        'image': image,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
        'type_structure': type_structure,
        'date_inscription': date_inscription,
        'nombre_alerte_sanitaire': nombre_alerte_sanitaire,
        'consultations_structure': consultations_structure,
        'prescriptions_structure': prescriptions_structure,
        'examens_structure': examens_structure,
    })

def notification_structure(request):
    nom = request.session.get('nom')
    image = request.session.get('image')
    admin_id = request.session.get('admin_id')
    type_structure = request.session.get('type_structure')
    structure_id = request.session.get('structure_id')

    # Marquer toutes les notifications comme lues
    Notification.objects.filter(recepteur=structure_id, lu=False).update(lu=True)

    # Récupérer toutes les notifications
    notifications_all = Notification.objects.filter(recepteur=structure_id).order_by('-created_at')

    # Pagination
    paginator = Paginator(notifications_all, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 4 dernières notifications non lues
    notifications_non_lues = Notification.objects.filter(recepteur=structure_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    return render(request, 'Structure/page/notification.html', {
        'page_obj': page_obj,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
        'nom': nom,
        'image': image,
        'type_structure': type_structure,
    })

def listemedecin(request):
    nom = request.session.get('nom')
    structure_id = request.session.get('structure_id')
    structure = StructureSante.objects.get(id=structure_id)
    image = request.session.get('image')
    type_structure = request.session.get('type_structure')

    listemedecins= Medecin.objects.filter(structure_sante=structure, archiver=False)
    paginator = Paginator(listemedecins, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    medecins_archives = Medecin.objects.filter(structure_sante=structure, archiver=True)
    paginator_archives = Paginator(medecins_archives, 5)
    page_number_archives = request.GET.get('page_archives')
    page_obj_archives = paginator_archives.get_page(page_number_archives)

    services= Service.objects.all()
    specialisations= Specialisation.objects.all()
    form = UtilisateurForm()

    notifications_non_lues = Notification.objects.filter(recepteur=structure_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()
    return render(request, 'Structure/page/listemedecin.html',{ 
        'listemedecins': listemedecins,
        'medecins_archives': medecins_archives,
         "services": services,
         "specialisations": specialisations,
         'form': form,
         'nom': nom,
         'image': image,
         'notifications_non_lues': notifications_non_lues,
         'total_non_lues': total_non_lues,
         'type_structure': type_structure,
         'page_obj': page_obj,
         'page_number': page_number,
         'paginator': paginator,
         'page_obj_archives': page_obj_archives,
         'page_number_archives': page_number_archives,
         'paginator_archives': paginator_archives,
        })

def ajouter_un_medecin(request):
    structure_id = request.session.get('structure_id')
    structure = StructureSante.objects.get(id=structure_id)
    image = request.session.get('image')

    medecins = Medecin.objects.all()
    specialisations = Specialisation.objects.all()
    services = Service.objects.all()

    nom = request.session.get('nom')

    if request.method == 'POST':
        email = request.POST['email']

        # Vérification si l'email existe déjà dans une autre table
        email_exists = (
            Medecin.objects.filter(email=email).exists()
        )

        if email_exists:
            messages.error(request, "Cet email existe deja")
            form = UtilisateurForm()
            return render(request, 'Structure/page/listemedecin.html', {
                'listemedecins': medecins,
                'services': services,
                'specialisations': specialisations,
                'form': form,
                'nom': nom
            })

        # Si email disponible : continuer la création
        nom = request.POST['nom']
        prenom = request.POST['prenom']
        sexe = request.POST['sexe']
        pays = request.POST['pays']
        telephone = request.POST['telephone']
        adresse = request.POST['adresse']
        image = request.FILES.get('image')
        specialisation_id = request.POST['specialisation']
        service_id = request.POST['service']

        username = f"{nom.lower()}{prenom.lower()}{uuid.uuid4().hex[:6]}"
        while Medecin.objects.filter(username=username).exists():
            username = f"{nom.lower()}{prenom.lower()}{uuid.uuid4().hex[:6]}"

        numero_licence = request.POST.get('numero_licence')
        if not numero_licence:
            numero_licence = f"LIC-{uuid.uuid4().hex[:10].upper()}"

        medecin = Medecin(
            username=username,
            nom=nom,
            prenom=prenom,
            sexe=sexe,
            telephone=telephone,
            pays=pays,
            adresse=adresse,
            image=image,
            email=email,
            statut="medecin",
            numero_licence=numero_licence,
            specialisation_id=specialisation_id,
            service_id=service_id,
            structure_sante=structure,
            created_by=structure,
            updated_by=structure
        )
        medecin.password = make_password('temporary_password123')
        medecin.save()

        # Création du token custom
        reset_token = PasswordResetTokenMedecin.objects.create(medecin=medecin)

        reset_password_link = request.build_absolute_uri(
            f'/definir_password_medecin/{reset_token.token}/'
        )

        # Envoi de l'email
        subject = "Définissez votre mot de passe"
        message = (f"Bonjour {medecin.prenom} {medecin.nom},\n\n"
                f"Vous avez été ajouté comme médecin.\n"
                f"Votre email est : {medecin.email}\n"
                f"Veuillez définir votre mot de passe en cliquant sur le lien suivant :\n{reset_password_link}\n\n"
                "Cordialement.")
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [medecin.email]

        send_mail(subject, message, from_email, recipient_list)


        messages.success(request, f"Le médecin {medecin.nom} {medecin.prenom} a été ajouté avec succès.")

        structure_id = request.session.get('structure_id')
        notifications_non_lues = Notification.objects.filter(recepteur=structure_id, lu=False).order_by('-created_at')[:4]
        total_non_lues = notifications_non_lues.count()

        Notification.objects.create(
            type_notification="Ajout Médecin",
            description=f"Vous avez ajouté un médecin : {medecin.nom}",
            recepteur=structure_id
        )

        return redirect('structure')

    form = UtilisateurForm()
    return render(request, 'Structure/page/listemedecin.html', {
        'listemedecins': medecins,
        'services': services,
        'specialisations': specialisations,
        'form': form,
        'image': image,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
    })

def definir_password_medecin(request, token):
    reset_token = get_object_or_404(PasswordResetTokenMedecin, token=token)

    # Vérifie si le token est encore valide
    if not reset_token.is_valid():
        messages.error(request, "Le lien de réinitialisation a expiré.")
        return redirect('user_login')  # ou une autre page

    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'Administrateur/Page/definir_password.html')

        # Change le mot de passe de l'admin
        medecin = reset_token.medecin
        medecin.password = make_password(new_password)
        medecin.save()

        # Supprime ou invalide le token pour sécurité
        reset_token.delete()

        messages.success(request, "Mot de passe mis à jour avec succès.")
        return redirect('user_login')  # ou page d'accueil
    context = {
        'token': token,  # <- Assure-toi que tu passes bien ça ici
        'message': '',
        'success': False,
    }
    return render(request, 'Structure/page/definir_password_medecin.html', context)

def archiver_medecin_structure(request, id):
    medecin = get_object_or_404(Medecin, id=id)
    medecin.archiver = True  
    medecin.save()
    messages.success(request, f"Le médecin {medecin.nom} {medecin.prenom} a été archivé.")
    structure_id = request.session.get('structure_id')

    Notification.objects.create(
        type_notification="Archivage Médecin",
        description=f"Vous avez archivé le médecin : {medecin.nom}",
        recepteur=structure_id
    )
    send_mail(
        subject="Médecin archivé",
        message=f" « {medecin.nom} {medecin.prenom} » vous a archivé ",
        from_email="beyeballa04@gmail.com",
        recipient_list=[medecin.email]
    )
    return redirect('listeMedecin')

def desarchiver_medecin_structure(request, id):
    medecin = get_object_or_404(Medecin, id=id)
    medecin.archiver = False  
    medecin.save()
    messages.success(request, f"Le médecin {medecin.nom} {medecin.prenom} a été desarchivé.")
    structure_id = request.session.get('structure_id')
    Notification.objects.create(
        type_notification="Désarchivage Médecin",
        description=f"Vous avez désarchivé le médecin : {medecin.nom}",
        recepteur=structure_id
    )
    send_mail(
        subject="Médecin désarchivé",
        message=f" « {medecin.nom} {medecin.prenom} » vous a désarchivé ",
        from_email="beyeballa04@gmail.com",
        recipient_list=[medecin.email]
    )
    return redirect('listeMedecin')

def modifier_medecin(request, id):
    medecin = get_object_or_404(Medecin, id=id)

    if request.method == 'POST':
        medecin.nom = request.POST['nom']
        medecin.prenom = request.POST['prenom']
        medecin.email = request.POST['email']
        # Ajoute d'autres champs selon le formulaire
        medecin.save()
        messages.success(request, "Médecin modifié avec succès.")
        structure_id = request.session.get('structure_id')
        Notification.objects.create(
            type_notification="Modification Médecin",
            description=f"Vous avez modifié le médecin : {medecin.nom}",
            recepteur=structure_id
        )
        send_mail(
            subject="Médecin modifié",
            message=f" « {medecin.nom} {medecin.prenom} » vous a modifié ",
            from_email="beyeballa04@gmail.com",
            recipient_list=[medecin.email]
        )

        return redirect('profil_structure')

    # En cas de GET (non prévu ici, mais utile en fallback)
    return redirect('profil_structure')

def changer_mot_de_passe_structure(request):
    structure_id = request.session.get('structure_id')
    image = request.session.get('image')
    nom = request.session.get('nom')
    email = request.session.get('email')
    adresse = request.session.get('adresse')
    telephone = request.session.get('telephone')
    if not structure_id:
        messages.error(request, "Structure non authentifié.")
        return redirect('user_login')  
    
    if request.method == 'POST':
        email = request.session.get('email')
        old_password = request.POST.get('oldPassword')
        new_password = request.POST.get('newPassword')
        confirm_password = request.POST.get('confirmPassword')

        try:
            structure = StructureSante.objects.get(email=email)
        except StructureSante.DoesNotExist:
            messages.error(request, "Structure introuvable.")
            return redirect('profil_structure')
        
        if not check_password(old_password, structure.password):
            messages.error(request, "Ancien mot de passe incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            structure.password = make_password(new_password)
            structure.save()
            messages.success(request, "Mot de passe changé avec succès.")
            return redirect('profil_structure')  # redirige vers le profil

    structure_id = request.session.get('structure_id')
    notifications = Notification.objects.filter(recepteur=structure_id,lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications.count()
    return render(request, 'Structure/page/profil.html', {
        'notifications': notifications,
        'nom': nom,
        'email': email,
        'image': image,
        'total_non_lues': total_non_lues,
        })

def modifier_infos_structure(request):
    structure_id = request.session.get('structure_id')
    if not structure_id:
        messages.error(request, "Structure non authentifié.")
        return redirect('user_login')  

    structure = get_object_or_404(StructureSante, id=structure_id)

    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        # Mise à jour des champs
        structure.nom = nom
        structure.email = email
        structure.telephone = telephone
        structure.adresse = adresse
        structure.save()

        # Mise à jour de la session
        request.session['nom'] = structure.nom
        request.session['email'] = structure.email
        request.session['telephone'] = structure.telephone
        request.session['adresse'] = structure.adresse

        messages.success(request, "Informations mises à jour avec succès.")
        Notification.objects.create(
            type_notification="Informations mises à jour",
            description=f"Vous avez modifié vos informations",
            recepteur=structure_id
        )
        return redirect('profil_structure')

    return render(request, 'Structure/page/profil.html', {'structure': structure})

def modifier_photo_structure(request):
    structure_id = request.session.get('structure_id')
    if not structure_id:
        messages.error(request, "Structure non authentifié.")
        return redirect('login')

    structure = get_object_or_404(StructureSante, id=structure_id)

    if request.method == 'POST':
        image = request.FILES.get('photo')
        if image:
            structure.image = image
            structure.save()  # 🛠️ Il manquait le save() pour enregistrer l'image dans la base de données

            # Mise à jour de la session avec l'URL de l'image
            request.session['image'] = structure.image.url if structure.image else None

            messages.success(request, "Photo de profil mise à jour avec succès.")
        else:
            messages.warning(request, "Aucune image n'a été sélectionnée.")
        
        return redirect('profil_structure')

    return render(request, 'Structure/page/profil.html', {'structure': structure})

def profil_structure(request):
    nom = request.session.get('nom')
    structure_id = request.session.get('structure_id')
    structure = StructureSante.objects.get(id=structure_id)
    email = request.session.get('email')
    telephone = request.session.get('telephone')
    adresse = request.session.get('adresse')  
    password = request.session.get('password')
    image = request.session.get('image')
    ville = request.session.get('ville')  
    region = request.session.get('region')
    site_web = request.session.get('site_web')

    structure_id = request.session.get('structure_id')
    notifications_non_lues = Notification.objects.filter(recepteur=structure_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()


    return render(request, 'Structure/page/profil.html',{
        'nom': nom,
         "structure": structure,
         "telephone": telephone,
         'email': email,
         'adresse': adresse,
         'image': image,
         'ville': ville,
         'region': region,
         'site_web': site_web,
         'notifications_non_lues': notifications_non_lues,
         'total_non_lues': total_non_lues,
    })

def alerte_sante(request):
    structure_id = request.session.get('structure_id')
    if not structure_id:
        messages.error(request, "Structure non authentifiée.")
        return redirect('user_login')
    
    image = request.session.get('image')
    nom = request.session.get('nom')
    email = request.session.get('email')
    structure = get_object_or_404(StructureSante, id=structure_id)
    
    alertes = AlerteSanitaire.objects.filter(structure_sante=structure)
    
    if request.GET.get('urgence'):
        alertes = alertes.filter(urgence=True)
    
    # Pagination
    paginator = Paginator(alertes, 4)  # 4 alertes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'Structure/page/alerte_sante.html', {
        'image': image,
        'nom': nom,
        'email': email,
        'page_obj': page_obj,  # liste paginée
    })

def ajouter_alerte_sante(request):
    structure_id = request.session.get('structure_id')
    if not structure_id:
        messages.error(request, "Structure non authentifiée.")
        return redirect('user_login')

    # Récupération de la structure
    structure = get_object_or_404(StructureSante, id=structure_id)

    image = request.session.get('image')
    nom = request.session.get('nom')

    if request.method == 'POST':
        justification = request.POST.get('justification')
        groupe_sanguin = request.POST.get('groupe_sanguin')
        quantite = request.POST.get('quantite')
        type_don = request.POST.get('type_don')
        urgence_str = request.POST.get('urgence')
        urgence = True if urgence_str == 'Oui' else False

        fichier_joint = request.FILES.get('fichier_joint')

        try:
            alerte = AlerteSanitaire(
                structure_sante=structure,
                justification=justification,
                groupe_sanguin=groupe_sanguin,
                quantite=int(quantite),
                type_don=type_don,
                urgence=urgence,
                created_by=structure,
                updated_by=structure,
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            # Ajouter le fichier que s’il existe
            if fichier_joint:
                alerte.fichier_joint = fichier_joint
            
            alerte.save()

            patients_cibles = Patient.objects.filter(groupe_sanguin=groupe_sanguin)
            for patient in patients_cibles:
                Notification.objects.create(
                type_notification="Alerte Sanitaire",
                description=(
                    f"Une alerte a été lancée par la structure **{structure.nom}** "
                    f"pour un besoin de sang de groupe **{groupe_sanguin}**.\n"
                    f"Contact : {structure.telephone}\n"
                    f"Justification : {justification}"
                ),
                recepteur=patient.id,  # ou patient.email / username selon votre design
                created_at=timezone.now(),
                lu=False
            )
            messages.success(request, "Alerte Sanitaire a été lancée avec succès.")
            return redirect('alerte_sante')
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout : {str(e)}")

    return render(request, 'Structure/page/alerte_sante.html', {
        'image': image,
        'nom': nom
    })

def modifier_alerte_sante(request, id):
    structure_id = request.session.get('structure_id')
    if not structure_id:
        messages.error(request, "Structure non authentifiée.")
        return redirect('user_login')

    # Récupération de la structure
    structure = get_object_or_404(StructureSante, id=structure_id)

    image = request.session.get('image')
    nom = request.session.get('nom')

    alerte = get_object_or_404(AlerteSanitaire, id=id)

    if request.method == 'POST':
        alerte.titre = request.POST.get('titre')
        alerte.description = request.POST.get('description')
        alerte.justification = request.POST.get('justification')
        alerte.groupe_sanguin = request.POST.get('groupe_sanguin')
        alerte.quantite = request.POST.get('quantite')
        alerte.type_don = request.POST.get('type_don')

        urgence_str = request.POST.get('urgence')
        alerte.urgence = True if urgence_str == 'Oui' else False

        fichier_joint = request.FILES.get('fichier_joint')
        if fichier_joint:
            alerte.fichier_joint = fichier_joint

        alerte.save()
        messages.success(request, "Alerte Sanitaire modifiée avec succès.")
        return redirect('alerte_sante')

    return render(request, 'Structure/page/modifier_alerte_sante.html', {
        'alerte': alerte,
        'image': image,
        'nom': nom
    })


_STRUCTURE_PROTECTED_VIEWS = (
    'structure',
    'notification_structure',
    'listemedecin',
    'ajouter_un_medecin',
    'archiver_medecin_structure',
    'desarchiver_medecin_structure',
    'modifier_medecin',
    'changer_mot_de_passe_structure',
    'modifier_infos_structure',
    'modifier_photo_structure',
    'profil_structure',
    'alerte_sante',
    'ajouter_alerte_sante',
    'modifier_alerte_sante',
)

for _view_name in _STRUCTURE_PROTECTED_VIEWS:
    globals()[_view_name] = login_required_custom(login_required(login_url='user_login')(globals()[_view_name]))
