from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail, EmailMessage
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.urls import reverse
from dmap_app.decorators import login_required_custom
from datetime import datetime
import hashlib
import qrcode
from io import BytesIO
import base64
import random
import string
from ..models import (
    Patient, Consultation, ExamenMedical, Prescription, DocumentMedical, 
    InfoConfidentielle, DossierMedical, DemandeCarte, Notification, 
    RendezVous, ChatMessage, StructureSante, Conversation
)
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from datetime import datetime, timedelta
import hashlib
import qrcode
from io import BytesIO
import base64
import random
import string
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from dmap_app.decorators import login_required_custom
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from django.core.cache import cache
import json
from django.views.decorators.http import require_POST
import requests
from ..rag_utils import search_relevant_passages  # Import de la fonction RAG
admin_email = settings.EMAIL_HOST_USER




#########PARTIE PATIENT#########
#REDIRECTION VERS LA PAGE PATIENT
@login_required(login_url='user_login')
@login_required_custom
def patient(request):
    patient = get_object_or_404(Patient, id=request.user.id)
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    created_at = request.session.get('created_at')

    if not patient.qr_code_token or patient.qr_code_expire_at <= timezone.now():
        patient.generer_qr_code() 

    user_id = request.session.get('user_id')

    nombre_consultation = Consultation.objects.filter(patient=user_id).count()
    nombre_examen = ExamenMedical.objects.filter(patient=user_id).count()
    nombre_prescription = Prescription.objects.filter(patient=user_id).count()
    nombre_document = DocumentMedical.objects.filter(patient=user_id).count()
    nombre_rendez_vous = RendezVous.objects.filter(patient=user_id).count()
    nombre_rendez_termine = RendezVous.objects.filter(patient=user_id, statut='Terminé').count()
    rendez_vous_a_venir = RendezVous.objects.filter(
        patient=user_id,
        date_rendez_vous__gte=timezone.now().date()
    ).order_by('date_rendez_vous')

    return render(request, 'Patient/index.html', {
        'full_name': full_name,
        'image': image,
        'patient': patient,
        'nombre_consultation': nombre_consultation,
        'nombre_examen': nombre_examen,
        'nombre_prescription': nombre_prescription,
        'nombre_document': nombre_document,
        'created_at': created_at,
        'nombre_rendez_vous': nombre_rendez_vous,
        'nombre_rendez_termine': nombre_rendez_termine,
        'rendez_vous_a_venir': rendez_vous_a_venir,
    })

@login_required(login_url='user_login')
def chatbot(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Vous devez être connecté pour accéder au chat.")
        return redirect('user_login')

    patient = get_object_or_404(Patient, id=user_id)

    # Logique pour la soumission de message (POST)
    if request.method == 'POST':
        message = request.POST.get('message')
        conversation_id = request.POST.get('conversation_id')
        conversation = get_object_or_404(Conversation, id=conversation_id, patient=patient)

        if message:
            chat_messages = ChatMessage.objects.filter(conversation=conversation)
            if chat_messages.count() >= 50:
                conversation.is_active = False
                conversation.save()
                conversation = Conversation.objects.create(
                    patient=patient,
                    title=f"Conversation du {timezone.now().strftime('%d/%m/%Y %H:%M')}"
                )

            ChatMessage.objects.create(
                conversation=conversation, patient=patient, message=message, est_utilisateur=True
            )
            
            urgence_response = rediriger_si_urgence(message, patient)
            if urgence_response:
                ChatMessage.objects.create(
                    conversation=conversation, patient=patient, message=urgence_response, 
                    est_utilisateur=False, reponse=urgence_response, is_urgent=True
                )
                return JsonResponse({'status': 'success', 'response': urgence_response, 'is_urgent': True})
            
            response = generate_response(message, patient)
            ChatMessage.objects.create(
                conversation=conversation, patient=patient, message=response,
                est_utilisateur=False, reponse=response
            )
            return JsonResponse({'status': 'success', 'response': response, 'is_urgent': False})
        else:
            return JsonResponse({'status': 'error', 'response': 'Le message ne peut pas être vide.'}, status=400)

    # Logique pour l'affichage de la page (GET)
    try:
        full_name = request.session.get('full_name')
        image = request.session.get('image')

        conversation = Conversation.objects.filter(
            patient=patient, is_active=True
        ).first() or Conversation.objects.create(
            patient=patient, title=f"Conversation du {timezone.now().strftime('%d/%m/%Y %H:%M')}"
        )

        chat_messages = ChatMessage.objects.filter(conversation=conversation).order_by('horodatage')
        messages_page = paginate_queryset(chat_messages, request.GET.get('page', 1), 10)
        conversations = Conversation.objects.filter(patient=patient).order_by('-updated_at')

        return render(request, 'Patient/page/chatbot.html', {
            'messages': messages_page,
            'full_name': full_name,
            'image': image,
            'patient': patient,
            'conversation': conversation,
            'conversations': conversations,
            'has_next': messages_page.has_next(),
            'has_previous': messages_page.has_previous(),
            'next_page': int(request.GET.get('page', 1)) + 1 if messages_page.has_next() else None,
            'previous_page': int(request.GET.get('page', 1)) - 1 if messages_page.has_previous() else None,
        })
    except Exception as e:
        print(f"Erreur dans chatbot (GET): {e}")
        messages.error(request, "Une erreur est survenue lors de l'accès au chat. Veuillez réessayer.")
        return redirect('patient')


@login_required(login_url='user_login')
@login_required_custom
def consultation(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    user_id = request.session.get('user_id')

    patient = get_object_or_404(Patient, id=user_id)
    consultations_list = Consultation.objects.filter(patient=patient).order_by('-date_consultation')

    paginator = Paginator(consultations_list, 10)
    page_number = request.GET.get('page')
    consultations = paginator.get_page(page_number)

    return render(request, 'Patient/page/consultation.html', {
        'consultations': consultations,
        'full_name': full_name,
        'image': image,
    })

@login_required(login_url='user_login')
@login_required_custom
def examenmedical(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    user_id = request.session.get('user_id')

    patient = get_object_or_404(Patient, id=user_id)
    examens_list = ExamenMedical.objects.filter(patient=patient).order_by('-date_examen')

    paginator = Paginator(examens_list, 10)
    page_number = request.GET.get('page')
    examens = paginator.get_page(page_number)

    return render(request, 'Patient/page/examenmedicaux.html', {
        'examens': examens,
        'full_name': full_name,
        'image': image,
    })

@login_required(login_url='user_login')
@login_required_custom
def prescription(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    user_id = request.session.get('user_id')

    patient = get_object_or_404(Patient, id=user_id)
    prescriptions_list = Prescription.objects.filter(patient=patient).order_by('-created_at')

    # Éviter les doublons de notifications
    for prescription in prescriptions_list:
        message = f"Rappel : prenez votre médicament **{prescription.medicament}** à l’heure prévue ({prescription.posologie})."
        
        if not Notification.objects.filter(
            type_notification="ALERTE_MEDICAMENT",
            description=message,
            recepteur=patient
        ).exists():
            Notification.objects.create(
                type_notification="ALERTE_MEDICAMENT",
                description=message,
                recepteur=patient
            )

    paginator = Paginator(prescriptions_list, 5)
    page_number = request.GET.get('page')
    prescriptions = paginator.get_page(page_number)

    return render(request, 'Patient/page/prescription.html', {
        'prescriptions': prescriptions,
        'full_name': full_name,
        'image': image,
    })

@login_required(login_url='user_login')
@login_required_custom
def demandecarte(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    return render(request, 'Patient/page/demandecarte.html', {
        'full_name': full_name,
        'image': image,
        })

@login_required(login_url='user_login')
@login_required_custom
def documentmedical(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    user_id = request.session.get('user_id')

    patient = get_object_or_404(Patient, id=user_id)
    documentmedicals_list = DocumentMedical.objects.filter(patient=patient).order_by('-created_at')

    paginator = Paginator(documentmedicals_list, 5)
    page_number = request.GET.get('page')
    documentmedicals = paginator.get_page(page_number)

    return render(request, 'Patient/page/documentMedical.html', {
        'documentmedicals': documentmedicals,
        'full_name': full_name,
        'image': image,
    })

@login_required(login_url='user_login')
@login_required_custom
def info_medecin(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    user_id = request.session.get('user_id')

    patient = get_object_or_404(Patient, id=user_id)
    info_medecin = InfoConfidentielle.objects.filter(patient=patient, visible_par_patient=True).order_by('-created_at')

    paginator = Paginator(info_medecin, 5)
    page_number = request.GET.get('page')
    info_medecin = paginator.get_page(page_number)

    return render(request, 'Patient/page/info_medecin.html', {
        'info_medecin': info_medecin,
        'full_name': full_name,
        'image': image,
    })


@login_required(login_url='user_login')
@login_required_custom
def dossiermedical(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    patient_id = request.session.get('patient_id')
    dossiermedicals = DossierMedical.objects.filter(patient=patient_id)
    return render(request, 'Patient/page/dossierMedicalComplet.html', {
        'dossiermedicals': dossiermedicals,
        'full_name': full_name,
        'image': image,
        })

@login_required(login_url='user_login')
@login_required_custom
def historiquesoin(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    return render(request, 'Patient/page/historiquesoins.html', {
        'full_name': full_name,
        'image': image,
        })

@login_required(login_url='user_login')
@login_required_custom
def profil(request):
    user_id = request.session.get('user_id')
    full_name = request.session.get('full_name')
    nom = request.session.get('nom')
    prenom = request.session.get('prenom')
    image = request.session.get('image')
    email = request.session.get('email')
    telephone = request.session.get('telephone')
    adresse = request.session.get('adresse')
    user_id = request.session.get('user_id')
    notifications_non_lues = Notification.objects.filter(recepteur=user_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    patient = get_object_or_404(Patient, id=user_id)
    profil_complet = all([
        patient.lieu_naissance,
        patient.date_naissance,
        patient.groupe_sanguin,
        patient.situation_familiale,
        patient.profession,
        patient.contact_urgence
    ])
    groupe_sanguin_choices = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    situation_familiale_choices = ["Célibataire", "Marié(e)", "Divorcé(e)", "Veuf(ve)"]
    return render(request, 'Patient/page/profil.html', {
        'full_name': full_name,
        'image': image,
        'nom': nom,
        'prenom': prenom,
        'email': email,
        'telephone': telephone,
        'adresse': adresse,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
        'profil_complet': profil_complet,
        'patient': patient,
        'groupe_sanguin_choices': groupe_sanguin_choices,
        'situation_familiale_choices': situation_familiale_choices,
        })

@login_required(login_url='user_login')
@login_required_custom
def qrcode_view(request):
    user_id = request.session.get('user_id')
    full_name = request.session.get('full_name', 'Utilisateur')
    email = request.session.get('email')
    telephone = request.session.get('telephone')
    adresse = request.session.get('adresse')

    if not user_id:
        return HttpResponseForbidden("Non autorisé")

    now = datetime.utcnow()
    time_block = int(now.timestamp() // 120)  
    token_str = f"{user_id}-{time_block}-{settings.QR_SECRET_KEY}"
    token = hashlib.sha256(token_str.encode()).hexdigest()

    # Générer l'URL vers la vue du dossier médical avec token
    qr_url = (
        f"http://127.0.0.1:8000{reverse('acceder_dossier_via_qrcode')}"
        f"?user_id={user_id}&token={token}"
    )


    # Générer le QR code
    qr = qrcode.make(qr_url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    img_data = f"data:image/png;base64,{qr_img}"

     # Récupérer le patient lié à l'utilisateur connecté
    try:
        patient = Patient.objects.get(id=user_id)  # Trouver le patient par l'id de l'utilisateur
    except Patient.DoesNotExist:
        patient = None

    return render(request, 'Patient/page/qrcode.html', {
        'full_name': full_name,
        'user_id': user_id,
        'email': email,
        'telepho': telephone,
        'adresse': adresse,
        'qr_code': img_data,
        'qr_url': qr_url,
        'patient': patient
    })

def generer_identifiant_unique():
    while True:
        identifiant = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        if not Patient.objects.filter(identifiant=identifiant).exists():
            return identifiant
        
@login_required(login_url='user_login')

def generer_identifiant(request):
    if request.method == 'POST':
        user = request.user  # Utilisation de l'utilisateur connecté
        try:
            patient = Patient.objects.get(id=user.id)  # Trouver le patient par l'id de l'utilisateur
            patient.identifiant = generer_identifiant_unique()  # Générer un identifiant unique
            patient.save()
            messages.success(request, 'Votre identifiant a ete regenerer'),
        except Patient.DoesNotExist:
            pass  

    return redirect('qrcode_view')  # Rediriger vers la vue qrcode_view pour afficher l'identifiant

@login_required(login_url='user_login')
@login_required_custom
def demande_carte_view(request):
    user_id = request.session.get('user_id')
    full_name = request.session.get('full_name', 'Utilisateur')
    email = request.session.get('email')

    if not user_id:
        return HttpResponseForbidden("Non autorisé")

    # Vérifie si une demande existe déjà en attente
    patient = Patient.objects.get(id=user_id)
    if DemandeCarte.objects.filter(patient=patient, statut='En attente').exists():
        messages.error(request, 'Vous avez déjà une demande en attente.'),
        return render(request, 'Patient/index.html')

    # Générer le token et le QR URL
    time_block = int(datetime.utcnow().timestamp() // 120)
    token_str = f"{user_id}-{time_block}-{settings.QR_SECRET_KEY}"
    token = hashlib.sha256(token_str.encode()).hexdigest()
    qr_url = (
        f"http://127.0.0.1:8000{reverse('acceder_dossier_via_qrcode')}"
        f"?user_id={user_id}&token={token}"
    )

    # Génération du QR code
    qr = qrcode.make(qr_url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)

    # Création d'une nouvelle demande de carte
    demande = DemandeCarte(patient=patient)
    demande.save()
    messages.success(request, 'Votre demande a été envoyée avec succès. '),

    # Enregistrer le QR code dans le champ ImageField
    filename = f'qrcode_{demande.id}.png'
    demande.qr_code_image.save(filename, buffer, save=True)

    # Email à l'administrateur avec pièce jointe du QR code
    admin_email = settings.EMAIL_HOST_USER  # À définir dans settings.py
    mail = EmailMessage(
        subject='Nouvelle Demande de Carte Patient',
        body=f"""
            Bonjour,

            Une nouvelle demande de carte a été faite par {full_name} ({email}).

            Lien direct via QR : {qr_url}

            Veuillez trouver le QR code en pièce jointe pour l’impression ou la génération de la carte.

            Cordialement,
            Système DMAP
                    """,
        from_email=settings.EMAIL_HOST_USER,
        to=[admin_email],
    )

    # Attacher le QR code image (buffer doit être au début)
    buffer.seek(0)
    mail.attach('qr_code_patient.png', buffer.read(), 'image/png')

    mail.send()

    return render(request, 'Patient/index.html')

@login_required(login_url='user_login')
@login_required_custom
def changer_mot_de_passe_patient(request):
    user_id = request.session.get('user_id')
    image = request.session.get('image')
    nom = request.session.get('nom')
    prenom = request.session.get('prenom')
    full_name = request.session.get('full_name')
    email = request.session.get('email')
    adresse = request.session.get('adresse')
    telephone = request.session.get('telephone')
    if not user_id:
        messages.error(request, "Médecin non authentifié.")
        return redirect('user_login')  
    
    if request.method == 'POST':
        email = request.session.get('email')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        try:
            patient = Patient.objects.get(email=email)
        except Patient.DoesNotExist:
            messages.error(request, "Médecin introuvable.")
            return redirect('profil')
        
        if not check_password(old_password, patient.password):
            messages.error(request, "Ancien mot de passe incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            patient.password = make_password(new_password)
            patient.save()
            Notification.objects.create(
                type_notification="Mot de passe changé",
                description=f"Vous avez changé votre mot de passe",
                recepteur=user_id
            )
            messages.success(request, "Mot de passe changé avec succès.")
            return redirect('profil')  # redirige vers le profil

    user_id = request.session.get('user_id')
    notifications = Notification.objects.filter(recepteur=user_id,lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications.count()
    return render(request, 'Patient/page/profil.html', {
        'notifications': notifications,
        'nom': nom,
        'email': email,
        'image': image,
        'total_non_lues': total_non_lues,
        'prenom': prenom,
        'full_name': full_name,

        })

@login_required(login_url='user_login')
@login_required_custom
def modifier_infos_patient(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Patient non authentifié.")
        return redirect('user_login') 

    patient = get_object_or_404(Patient, id=user_id)
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        patient.nom = nom
        patient.prenom = prenom
        patient.email = email
        patient.telephone = telephone
        patient.adresse = adresse
        patient.save()

         # Mise à jour de la session
        request.session['nom'] = patient.nom
        request.session['prenom'] = patient.prenom
        request.session['email'] = patient.email
        request.session['telephone'] = patient.telephone
        request.session['adresse'] = patient.adresse

        Notification.objects.create(
            type_notification="Informations mises à jour",
            description=f"Vous avez modifié vos informations",
            recepteur=user_id
        )
        messages.success(request, "Informations mises à jour avec succès.")
        return redirect('profil')
    return render(request, 'Patient/page/profil.html', {
        'patient': patient,
    })

@login_required(login_url='user_login')
@login_required_custom
def modifier_photo_patient(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Patient non authentifié.")
        return redirect('user_login') 
    
    patient = get_object_or_404(Patient, id=user_id)
    if request.method == 'POST':
        image = request.FILES.get('photo')
        if image:
            patient.image = image
            patient.save()  

            request.session['image'] = patient.image.url if patient.image else None
           
            messages.success(request, "Photo de profil mise à jour avec succès.")
            Notification.objects.create(
                type_notification="Photo de profil mise à jour",
                description=f"Vous avez modifié votre photo de profil",
                recepteur=user_id
            )
        else:
            messages.warning(request, "Aucune image n'a été sélectionnée.")
        
        return redirect('profil')
    return render(request, 'Patient/page/profil.html', {'patient': patient})

@login_required(login_url='user_login')
@login_required_custom
def notification_patient(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Patient non authentifié.")
        return redirect('user_login')               
    
    patient = get_object_or_404(Patient, id=user_id)
    notifications_list = Notification.objects.filter(recepteur=user_id,lu=False).order_by('-created_at')
    paginator = Paginator(notifications_list, 10)
    page_number = request.GET.get('page')
    notifications = paginator.get_page(page_number)
    total_non_lues = notifications_list.count()
    return render(request, 'Patient/page/notification.html', {
        'notifications': notifications,
        'total_non_lues': total_non_lues,
    })

@login_required(login_url='user_login')
@login_required_custom
def historique_rendez_vous(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Patient non authentifié.")
        return redirect('user_login') 

    full_name = request.session.get('full_name', 'Utilisateur')
    email = request.session.get('email')              
    
    patient = get_object_or_404(Patient, id=user_id)
    notifications = Notification.objects.filter(recepteur=user_id,lu=False).order_by('-created_at')
    total_non_lues = notifications.count()
    rendez_vous_list = RendezVous.objects.filter(patient=patient)
    paginator = Paginator(rendez_vous_list, 10)
    page_number = request.GET.get('page')
    rendez_vous = paginator.get_page(page_number)
    return render(request, 'Patient/page/historique_rendez_vous.html', {
        'notifications': notifications,
        'total_non_lues': total_non_lues,
        'rendez_vous': rendez_vous,
        'full_name' : full_name,
        'email' : email
    })

@login_required(login_url='user_login')
@login_required_custom
def partager_dossier(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Patient non authentifié.")
        return redirect('user_login')               
    
    patient = get_object_or_404(Patient, id=user_id)
    notifications = Notification.objects.filter(recepteur=user_id,lu=False).order_by('-created_at')
    total_non_lues = notifications.count()
    return render(request, 'Patient/page/partager_dossier.html', {
        'notifications': notifications,
        'total_non_lues': total_non_lues,
    })

@login_required(login_url='user_login')
@login_required_custom
def completer_profil(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Patient non authentifié.")
        return redirect('user_login')
    
    patient = get_object_or_404(Patient, id=user_id)
    if patient.lieu_naissance and patient.date_naissance and patient.groupe_sanguin and patient.situation_familiale and patient.profession and patient.contact_urgence:
        messages.success(request, "Profil déjà complété.")
        return redirect('profil')
        
    if request.method == 'POST':
        lieu_naissance = request.POST.get('lieu_naissance')
        date_naissance = request.POST.get('date_naissance')
        groupe_sanguin = request.POST.get('groupe_sanguin')
        situation_familiale = request.POST.get('situation_familiale')
        profession = request.POST.get('profession')
        contact_urgence = request.POST.get('contact_urgence')
    
        if lieu_naissance:
            patient.lieu_naissance = lieu_naissance
        if date_naissance:
            patient.date_naissance = date_naissance
        if groupe_sanguin:
            patient.groupe_sanguin = groupe_sanguin
        if situation_familiale:
            patient.situation_familiale = situation_familiale
        if profession:
            patient.profession = profession
        if contact_urgence:
            patient.contact_urgence = contact_urgence

        patient.save()

         # Mise à jour de la session
        request.session['lieu_naissance'] = patient.lieu_naissance
        request.session['date_naissance'] = patient.date_naissance
        request.session['groupe_sanguin'] = patient.groupe_sanguin
        request.session['situation_familiale'] = patient.situation_familiale
        request.session['profession'] = patient.profession
        request.session['contact_urgence'] = patient.contact_urgence

        messages.success(request, "Profil complété avec succès.")
        return redirect('profil')

    notifications = Notification.objects.filter(recepteur=user_id,lu=False).order_by('-created_at')
    total_non_lues = notifications.count()
    return render(request, 'Patient/page/profil.html', {
        'notifications': notifications,
        'total_non_lues': total_non_lues,
    })

@login_required(login_url='user_login')
@login_required_custom
def modifier_infos_supplementaire(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Patient non authentifié.")
        return redirect('user_login')
    
    patient = get_object_or_404(Patient, id=user_id)
    
    if request.method == "POST":
        patient.lieu_naissance = request.POST.get("lieu_naissance")
        patient.date_naissance = request.POST.get("date_naissance")
        patient.groupe_sanguin = request.POST.get("groupe_sanguin")
        patient.situation_familiale = request.POST.get("situation_familiale")
        patient.profession = request.POST.get("profession")
        patient.contact_urgence = request.POST.get("contact_urgence")
        patient.save()
        messages.success(request, "Informations mises à jour avec succès.")
        return redirect('profil')  # redirige vers la page principale

    return redirect('profil')




#Récupère une réponse en cache si elle existe
def get_cached_response(message, patient_id):
    cache_key = f"chat_response_{patient_id}_{hashlib.md5(message.encode()).hexdigest()}"
    return cache.get(cache_key)

def cache_response(message, response, patient_id, timeout=3600):  # Cache pour 1 heure
    """Met en cache une réponse"""
    cache_key = f"chat_response_{patient_id}_{hashlib.md5(message.encode()).hexdigest()}"
    cache.set(cache_key, response, timeout)

@login_required(login_url='user_login')
@login_required_custom
def charger_conversation(request, conversation_id):
    user_id = request.session.get('user_id')
    patient = get_object_or_404(Patient, id=user_id)
    
    # Désactiver toutes les conversations actives
    Conversation.objects.filter(patient=patient, is_active=True).update(is_active=False)
    
    # Activer la conversation sélectionnée
    conversation = get_object_or_404(Conversation, id=conversation_id, patient=patient)
    conversation.is_active = True
    conversation.save()
    
    return redirect('chatbot')

@login_required(login_url='user_login')
@login_required_custom
def nouvelle_conversation(request):
    user_id = request.session.get('user_id')
    patient = get_object_or_404(Patient, id=user_id)
    
    # Désactiver la conversation active
    Conversation.objects.filter(patient=patient, is_active=True).update(is_active=False)
    
    # Créer une nouvelle conversation
    conversation = Conversation.objects.create(
        patient=patient,
        title=f"Conversation du {timezone.now().strftime('%d/%m/%Y %H:%M')}"
    )
    
    return redirect('chatbot')

def generate_response(message, patient):
    """Génère une réponse pour le chatbot"""
    message = message.lower()
    print(f"Génération de réponse pour le message: {message}")

    # Vérification que patient est bien un objet Patient
    if not isinstance(patient, Patient):
        print(f"Erreur: patient n'est pas un objet Patient valide")
        return "Je suis désolé, une erreur est survenue. Pourriez-vous reformuler votre question ?"

    # Cache pour les réponses fréquentes
    cache_key = f"chat_response_{patient.id}_{hashlib.md5(message.encode()).hexdigest()}"
    cached_response = cache.get(cache_key)
    if cached_response:
        print("Réponse récupérée du cache")
        return cached_response

    # Gestion des réponses de suivi
    if any(mot in message for mot in ['oui', 'oui pourquoi pas', 'd\'accord', 'ok', 'bien sûr']):
        try:
            print("Détection d'une réponse positive")
            # Récupérer les 5 derniers messages de la conversation
            derniers_messages = ChatMessage.objects.filter(
                conversation__patient=patient,
                conversation__is_active=True
            ).order_by('horodatage')[:5]
            
            print(f"Nombre de messages récupérés: {derniers_messages.count()}")
            
            # Vérifier si le dernier message contient une mention de mal de tête
            for msg in reversed(derniers_messages):
                print(f"Vérification du message: {msg.message}")
                if msg.est_utilisateur and any(symptome in msg.message.lower() for symptome in ['mal à la tête', 'mal de tête', 'céphalée', 'migraine']):
                    print("Détection d'une mention de mal de tête dans l'historique")
                    reponse = f"""Je suis ravi que vous soyez ouvert à mes conseils. Pour mieux vous aider, pourriez-vous me donner plus de détails sur votre mal de tête ?

Par exemple :
- Depuis quand avez-vous mal à la tête ?
- La douleur est-elle localisée à un endroit particulier ?
- Avez-vous d'autres symptômes associés (nausées, sensibilité à la lumière) ?

Ces informations m'aideront à vous donner des conseils plus précis."""
                    cache.set(cache_key, reponse, 300)
                    return reponse
            
            # Si aucun message précédent ne mentionne de mal de tête, donner une réponse générique
            print("Aucune mention de mal de tête trouvée dans l'historique")
            reponse = f"""Je suis ravi de pouvoir continuer à vous aider. Pourriez-vous me donner plus de détails sur ce qui vous préoccupe ? 

Je suis là pour vous écouter et vous aider au mieux."""
            cache.set(cache_key, reponse, 300)
            return reponse

        except Exception as e:
            print(f"Erreur lors de la récupération des messages: {e}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            # En cas d'erreur, donner une réponse générique
            return "Je suis ravi de pouvoir continuer à vous aider. Comment puis-je vous être utile ?"

    # Gestion des réponses de suivi NÉGATIVES
    if any(mot in message for mot in ['non', 'non merci', 'pas maintenant', 'ça ira', 'non, merci']):
        reponse = "D'accord. N'hésitez pas si vous avez d'autres questions. Je reste à votre disposition pour vous aider."
        cache.set(cache_key, reponse, 300)
        return reponse

    # Gestion des symptômes (à vérifier en premier)
    symptomes = {
        'mal à la tête': ['mal à la tête', 'mal de tête', 'céphalée', 'migraine', 'j\'ai mal à la tête', 'j\'ai mal à la tete'],
        'fièvre': ['fièvre', 'fiévreux', 'température'],
        'douleur': ['douleur', 'mal', 'souffre'],
        'fatigue': ['fatigue', 'fatigué', 'épuisé'],
        'nausée': ['nausée', 'nausées', 'vomissement'],
    }

    # Vérifier si le message contient des symptômes
    symptome_detecte = None
    for symptome, mots in symptomes.items():
        if any(mot in message for mot in mots):
            symptome_detecte = symptome
            break

    # Si un symptôme est détecté, donner une réponse appropriée
    if symptome_detecte:
        if symptome_detecte == 'mal à la tête':
            reponse = f"""Bonjour {patient.prenom},

Je vois que vous avez un mal de tête. D'après votre dossier médical, vous avez déjà eu des maux de tête similaires et vous prenez actuellement du Doliprane.

Quelques conseils :
1. Reposez-vous dans un endroit calme et sombre
2. Prenez votre traitement prescrit (Doliprane) selon la posologie indiquée
3. Hydratez-vous bien
4. Évitez les écrans et les bruits forts

Si les symptômes persistent ou s'aggravent, je vous recommande de consulter votre médecin.

Souhaitez-vous me donner plus de détails sur votre mal de tête pour que je puisse mieux vous aider ?"""
            cache.set(cache_key, reponse, 300)
            return reponse

    # Gestion des conversations simples (uniquement si aucun symptôme n'est détecté)
    salutations = ['bonjour', 'salut', 'hello', 'hi']
    if not symptome_detecte and message.strip() in salutations:
        reponse = f"Bonjour {patient.prenom} ! Je suis votre assistant médical. Comment puis-je vous aider aujourd'hui ?"
        cache.set(cache_key, reponse, 300)
        return reponse

    # Gestion des questions sur les consultations et rendez-vous
    if any(mot in message for mot in ['consultation', 'rendez-vous', 'rdv', 'rendez vous', 'prochain', 'prochaine', 'à faire', 'à venir']):
        try:
            rendez_vous_a_venir = RendezVous.objects.filter(
                patient=patient,
                date_rendez_vous__gte=timezone.now().date(),
                statut__in=['En attente', 'Confirmé']
            ).order_by('date_rendez_vous')
            if rendez_vous_a_venir.exists():
                prochain_rdv = rendez_vous_a_venir.first()
                reponse = f"Votre prochain rendez-vous :\n- Date : {prochain_rdv.date_rendez_vous.strftime('%d/%m/%Y')}\n- Heure : {prochain_rdv.heure_rendez_vous}\n- Médecin : {prochain_rdv.medecin.nom} {prochain_rdv.medecin.prenom}\n- Motif : {prochain_rdv.motif}\n- Statut : {prochain_rdv.statut}"
            else:
                reponse = "Actuellement, vous n'avez pas de rendez-vous prévus dans votre agenda."
            cache.set(cache_key, reponse, 300)
            return reponse
        except Exception as e:
            print(f"Erreur lors de la récupération des rendez-vous: {e}")
            # En cas d'erreur, continuer vers la logique générique

    # Gestion des questions sur les traitements et prescriptions
    if any(mot in message for mot in ['traitement', 'médicament', 'prescription', 'ordonnance', 'prendre', 'posologie', 'pilule', 'cachet']):
        try:
            # Récupérer les prescriptions actives
            prescriptions_actives = Prescription.objects.filter(
                patient=patient,
                created_at__gte=timezone.now() - timedelta(days=90)  # Prescriptions des 3 derniers mois
            ).order_by('-created_at')
            
            if prescriptions_actives.exists():
                reponse = f"""Bonjour {patient.prenom},

Voici vos traitements en cours :

Médicaments prescrits :
"""
                for prescription in prescriptions_actives[:5]:  # Limiter à 5 prescriptions
                    reponse += f"- *{prescription.medicament}* : {prescription.posologie}\n"
                
                if prescriptions_actives.count() > 5:
                    reponse += f"\n... et {prescriptions_actives.count() - 5} autres prescriptions.\n"
                
                reponse += f"""

⚠ Rappels importants :
- Respectez scrupuleusement la posologie prescrite
- Ne modifiez jamais votre traitement sans avis médical
- Contactez votre médecin en cas d'effets secondaires

Avez-vous des questions sur un médicament en particulier ?"""
            else:
                reponse = f"""Bonjour {patient.prenom},

Actuellement, vous n'avez pas de traitements actifs dans votre dossier.

Si vous pensez avoir besoin d'un traitement, je vous recommande de consulter votre médecin.

Avez-vous d'autres questions ?"""
            
            cache.set(cache_key, reponse, 300)
            return reponse
            
        except Exception as e:
            print(f"Erreur lors de la récupération des prescriptions: {e}")
            # En cas d'erreur, continuer vers la logique générique

    # Gestion des questions sur les examens médicaux
    if any(mot in message for mot in ['examen', 'analyse', 'test', 'résultat', 'laboratoire', 'radio', 'échographie', 'scanner']):
        try:
            # Récupérer les examens récents
            examens_recents = ExamenMedical.objects.filter(
                patient=patient
            ).order_by('-date_examen')[:5]
            
            if examens_recents.exists():
                reponse = f"""Bonjour {patient.prenom},

Voici vos examens médicaux récents :

🔬 Examens effectués :
"""
                for examen in examens_recents:
                    reponse += f"- *{examen.type_examen}* (le {examen.date_examen.strftime('%d/%m/%Y')})\n"
                    if examen.resultat:
                        reponse += f"  Résultat : {examen.resultat}\n"
                    reponse += "\n"
                
                reponse += f"""Vous avez au total {ExamenMedical.objects.filter(patient=patient).count()} examens dans votre dossier.

Souhaitez-vous des détails sur un examen particulier ou avez-vous d'autres questions ?"""
            else:
                reponse = f"""Bonjour {patient.prenom},

Vous n'avez pas encore d'examens médicaux enregistrés dans votre dossier.

Si vous avez récemment effectué des examens, ils seront bientôt disponibles ici.

Avez-vous d'autres questions ?"""
            
            cache.set(cache_key, reponse, 300)
            return reponse
            
        except Exception as e:
            print(f"Erreur lors de la récupération des examens: {e}")
            # En cas d'erreur, continuer vers la logique générique

    # Gestion des questions sur le profil et informations personnelles
    if any(mot in message for mot in ['profil', 'informations', 'données', 'personnelles', 'groupe sanguin', 'naissance', 'profession', 'contact']):
        try:
            reponse = f"""Bonjour {patient.prenom},

Voici un aperçu de vos informations personnelles :

👤 Profil médical :
- Nom complet : {patient.prenom} {patient.nom}
- Groupe sanguin : {patient.groupe_sanguin or 'Non renseigné'}
- Lieu de naissance : {patient.lieu_naissance or 'Non renseigné'}
- Date de naissance : {patient.date_naissance or 'Non renseignée'}
- Situation familiale : {patient.situation_familiale or 'Non renseignée'}
- Profession : {patient.profession or 'Non renseignée'}

📞 Coordonnées :
- Téléphone : {patient.telephone or 'Non renseigné'}
- Contact d'urgence : {patient.contact_urgence or 'Non renseigné'}
- Adresse : {patient.adresse or 'Non renseignée'}

Pour modifier ces informations, vous pouvez aller dans votre profil depuis le menu principal.

Avez-vous besoin d'aide pour mettre à jour certaines informations ?"""
            
            cache.set(cache_key, reponse, 300)
            return reponse
            
        except Exception as e:
            print(f"Erreur lors de la récupération du profil: {e}")
            # En cas d'erreur, continuer vers la logique générique

    # Gestion des questions sur les notifications
    if any(mot in message for mot in ['notification', 'message', 'alerte', 'rappel', 'nouveau', 'nouvelle']):
        try:
            # Récupérer les notifications non lues
            notifications_non_lues = Notification.objects.filter(
                recepteur=patient,
                lu=False
            ).order_by('-created_at')[:5]
            
            if notifications_non_lues.exists():
                reponse = f"""Bonjour {patient.prenom},

Vous avez {notifications_non_lues.count()} notification(s) non lue(s) :

🔔 Notifications récentes :
"""
                for notif in notifications_non_lues:
                    reponse += f"- *{notif.type_notification}* : {notif.description}\n"
                
                reponse += f"""

Vous pouvez consulter toutes vos notifications depuis le menu principal.

Avez-vous besoin d'aide pour comprendre une notification en particulier ?"""
            else:
                reponse = f"""Bonjour {patient.prenom},

Vous n'avez actuellement aucune notification non lue.

Toutes vos notifications sont à jour ! 

Avez-vous d'autres questions ?"""
            
            cache.set(cache_key, reponse, 300)
            return reponse
            
        except Exception as e:
            print(f"Erreur lors de la récupération des notifications: {e}")
            # En cas d'erreur, continuer vers la logique générique

    # Préparation du contexte médical
    relevant_passages = search_relevant_passages(message, patient)
    
    # Récupérer l'historique de la conversation
    derniers_messages = ChatMessage.objects.filter(
        conversation__patient=patient,
        conversation__is_active=True
    ).order_by('horodatage')[:5]

    historique = ""
    for msg in reversed(derniers_messages):
        role = "Patient" if msg.est_utilisateur else "Assistant"
        historique += f"{role}: {msg.message}\n"

    # Préparation du prompt
    prompt = f"""Tu es un assistant médical professionnel et empathique spécialisé dans l'accompagnement des patients. Voici les informations du patient :

Patient: {patient.prenom} {patient.nom}
Groupe sanguin: {patient.groupe_sanguin or 'Non spécifié'}

---
Contexte Pertinent de son Dossier Médical (utilise ces informations en priorité pour répondre):
{relevant_passages}
---

Historique de la conversation:
{historique}

Question actuelle du patient: {message}

Instructions spécifiques:
1. Base ta réponse PRINCIPALEMENT sur le "Contexte Pertinent" fourni. C'est l'information la plus fiable.
2. Si le contexte ne contient pas la réponse, tu peux utiliser l'historique de la conversation.
3. Sois empathique et conversationnel, utilise le prénom du patient.
4. Ne pose jamais de diagnostic formel.
5. Propose des actions concrètes quand c'est approprié (ex: "Vous pouvez consulter les détails dans la section 'Mes Examens'").
6. Si tu ne trouves aucune information pertinente, admets-le poliment au lieu d'inventer une réponse. Dis par exemple : "Je n'ai pas trouvé d'information précise à ce sujet dans votre dossier. Pouvez-vous reformuler votre question ?"
7. Reste professionnel tout en étant chaleureux. Utilise des emojis appropriés pour rendre la conversation plus agréable.

Réponds de manière naturelle et conversationnelle, comme un médecin qui discute avec son patient."""

    # Appel direct à l'API Ollama
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'mistral',
            'prompt': prompt,
            'stream': False,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if 'response' in result:
            reponse = result['response'].strip()
            cache.set(cache_key, reponse, 300)
            return reponse
        else:
            return "Je suis désolé, je n'ai pas pu générer une réponse appropriée. Pourriez-vous reformuler votre question ?"
    else:
        print(f"Erreur API Ollama: {response.status_code} - {response.text}")
        return "Je suis désolé, le service est temporairement indisponible. Pourriez-vous réessayer dans quelques instants ?"

def chercher_structures_proches(region=None, ville=None):
    structures = StructureSante.objects.filter(valide=True)
    if region:
        structures = structures.filter(region__icontains=region)
    if ville:
        structures = structures.filter(ville__icontains=ville)
    return structures[:3]

def rediriger_si_urgence(message, patient):
    if any(m in message.lower() for m in ["urgence", "urgent", "samu", "très mal", "grave"]):
        structures = chercher_structures_proches(patient.adresse, patient.pays)
        if structures.exists():
            infos = "\n".join([f"{s.nom} - {s.ville}, {s.telephone}" for s in structures])
            return f"🚨 Symptôme critique détecté. Voici des structures proches de vous :\n{infos}"
        return "🚨 Symptôme critique détecté. Veuillez contacter le 15 (SAMU)."
    return None

def get_patient_context(request):
    """Récupère le contexte commun pour les vues patient"""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Patient non authentifié.")
        return None, None
    
    patient = get_object_or_404(Patient, id=user_id)
    context = {
        'full_name': request.session.get('full_name'),
        'image': request.session.get('image'),
        'patient': patient
    }
    return patient, context

def get_notifications_context(user_id):
    """Récupère le contexte des notifications"""
    notifications = Notification.objects.filter(recepteur=user_id, lu=False).order_by('-created_at')[:4]
    return {
        'notifications_non_lues': notifications,
        'total_non_lues': notifications.count()
    }

def paginate_queryset(queryset, page_number, per_page=10):
    """Pagination générique pour les querysets"""
    paginator = Paginator(queryset, per_page)
    try:
        return paginator.page(page_number)
    except:
        return paginator.page(1)

# Vues pour la conformité RGPD
@require_POST
@login_required(login_url='user_login')
def delete_chat_history(request):
    """Supprime tout l'historique de chat pour le patient."""
    patient = get_object_or_404(Patient, id=request.user.id)
    
    # Supprimer toutes les conversations et les messages associés
    Conversation.objects.filter(patient=patient).delete()
    
    messages.success(request, "Votre historique de conversation a été supprimé avec succès.")
    return redirect('chatbot')
