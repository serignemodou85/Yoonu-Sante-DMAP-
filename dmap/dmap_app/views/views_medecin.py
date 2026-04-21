from django.core.mail import send_mail
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from ..models import Medecin, Patient, DossierMedical, Consultation, Prescription, ExamenMedical, Notification, RendezVous, InfoConfidentielle, DocumentMedical
from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from dmap_app.decorators import login_required_custom
import hashlib



##########################PARTIE MEDECIN #########################################################
@login_required(login_url='user_login')
@login_required_custom
def medecin(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    created_at = request.session.get('created_at')
    user_id = request.session.get('user_id')
    notifications_non_lues = Notification.objects.filter(recepteur=user_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    nb_rdv_du_jour = RendezVous.objects.filter(date_rendez_vous=timezone.now().date()).count()

    nb_consultations= Consultation.objects.filter(medecin=user_id).count()
    nb_examen= ExamenMedical.objects.filter(medecin=user_id).count()
    nb_prescription= Prescription.objects.filter(medecin=user_id).count()
    nb_dossier= DossierMedical.objects.filter(medecin=user_id).count()


    return render(request, 'Medecin/index.html', {
        'full_name': full_name,
        'image': image,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
        'nb_rdv_du_jour': nb_rdv_du_jour,
        'nb_consultations': nb_consultations,
        'nb_examen': nb_examen,
        'nb_prescription': nb_prescription,
        'nb_dossier': nb_dossier,
    })

@login_required(login_url='user_login')
@login_required_custom
def notifications_medecin(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    user_id = request.session.get('user_id')

    # Marquer toutes les notifications comme lues
    Notification.objects.filter(recepteur=user_id, lu=False).update(lu=True)

    # Récupérer toutes les notifications
    all_notifications = Notification.objects.filter(recepteur=user_id).order_by('-created_at')

    # Pagination (par exemple, 10 notifications par page)
    paginator = Paginator(all_notifications, 4)  # 10 par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Notifications non lues (pour affichage rapide, ex : menu)
    notifications_non_lues = Notification.objects.filter(recepteur=user_id, lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications_non_lues.count()

    return render(request, 'Medecin/page/notifications.html', {
        'page_obj': page_obj,
        'full_name': full_name,
        'image': image,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
    })

@login_required(login_url='user_login')
@login_required_custom
def profil_medecin(request):
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
    return render(request, 'Medecin/page/profil.html',{
        'full_name': full_name,
        'image': image,
        'email': email,
        'telephone': telephone,
        'adresse': adresse,
        'notifications_non_lues': notifications_non_lues,
        'total_non_lues': total_non_lues,
        'nom': nom,
        'prenom': prenom,
    })

@login_required(login_url='user_login')
@login_required_custom
def changer_mot_de_passe_medecin(request):
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
            medecin = Medecin.objects.get(email=email)
        except Medecin.DoesNotExist:
            messages.error(request, "Médecin introuvable.")
            return redirect('profil_medecin')
        
        if not check_password(old_password, medecin.password):
            messages.error(request, "Ancien mot de passe incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            medecin.password = make_password(new_password)
            medecin.save()
            Notification.objects.create(
                type_notification="Mot de passe changé",
                description=f"Vous avez changé votre mot de passe",
                recepteur=user_id
            )
            messages.success(request, "Mot de passe changé avec succès.")
            return redirect('profil_medecin')  # redirige vers le profil

    user_id = request.session.get('user_id')
    notifications = Notification.objects.filter(recepteur=user_id,lu=False).order_by('-created_at')[:4]
    total_non_lues = notifications.count()
    return render(request, 'Medecin/page/profil.html', {
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
def modifier_infos_medecin(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Médecin non authentifié.")
        return redirect('user_login') 

    medecin = get_object_or_404(Medecin, id=user_id)
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        medecin.nom = nom
        medecin.prenom = prenom
        medecin.email = email
        medecin.telephone = telephone
        medecin.adresse = adresse
        medecin.save()

         # Mise à jour de la session
        request.session['nom'] = medecin.nom
        request.session['prenom'] = medecin.prenom
        request.session['email'] = medecin.email
        request.session['telephone'] = medecin.telephone
        request.session['adresse'] = medecin.adresse

        Notification.objects.create(
            type_notification="Informations mises à jour",
            description=f"Vous avez modifié vos informations",
            recepteur=user_id
        )
        messages.success(request, "Informations mises à jour avec succès.")
        return redirect('profil_medecin')
    return render(request, 'Medecin/page/profil.html', {
        'medecin': medecin,
    })

@login_required(login_url='user_login')
@login_required_custom
def modifier_photo_medecin(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Médecin non authentifié.")
        return redirect('user_login') 
    
    medecin = get_object_or_404(Medecin, id=user_id)
    if request.method == 'POST':
        image = request.FILES.get('photo')
        if image:
            medecin.image = image
            medecin.save()  

            request.session['image'] = medecin.image.url if medecin.image else None
           
            messages.success(request, "Photo de profil mise à jour avec succès.")
            Notification.objects.create(
                type_notification="Photo de profil mise à jour",
                description=f"Vous avez modifié votre photo de profil",
                recepteur=user_id
            )
        else:
            messages.warning(request, "Aucune image n'a été sélectionnée.")
        
        return redirect('profil_medecin')
    return render(request, 'Medecin/page/profil.html', {'medecin': medecin})

@login_required(login_url='user_login')
@login_required_custom
def creedossiermedical(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    return render(request, 'Medecin/page/profil.html',{
        'full_name': full_name,
        'image': image,
    })

@login_required(login_url='user_login')
@login_required_custom
def accederdossiermedical(request):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    return render(request, 'Medecin/page/accederdossiermedical.html',{
        'full_name': full_name,
        'image': image,
    })

@login_required(login_url='user_login')
@login_required_custom
def dossier_medical_patient(request):
    token = request.GET.get('token')
    user_id = request.GET.get('user_id')

    if not token or not user_id:
        messages.error(request, "QR code invalide.")
        return HttpResponseForbidden("QR code invalide.")

    current_block = int(datetime.utcnow().timestamp() // 120)
    for delta in [-1, 0, 1]:
        check_block = current_block + delta
        expected = hashlib.sha256(f"{user_id}-{check_block}-{settings.QR_SECRET_KEY}".encode()).hexdigest()
        if token == expected:
            try:
                patient = Patient.objects.get(id=user_id)
                return render(request, "Medecin/page/dossierMedicalPatient.html", {"patient": patient})
            except Patient.DoesNotExist:
                messages.error(request, "Patient introuvable.")
                return HttpResponseForbidden("Patient introuvable.")
    
    return HttpResponseForbidden("QR code expiré ou non valide.")

@login_required(login_url='user_login')
@login_required_custom
def acceder_dossier_via_code(request):
    if request.method == 'POST':
        identifiant = request.POST.get('identifiant')

        try:
            patient = Patient.objects.get(identifiant=identifiant)

            dossier_existe = DossierMedical.objects.filter(patient=patient).exists()

            if dossier_existe:
                dossier = DossierMedical.objects.get(patient=patient)
                Notification.objects.create(
                    type_notification="Dossier Medical accédé",
                    description=f"Le medecin {request.session.get('full_name')} a accédé au dossier médical ",
                    recepteur=patient.id
                )
                return redirect('voir_dossier', dossier_id=dossier.id)  
            else:
                return redirect('creer_dossier', patient_id=patient.id)  
        except Patient.DoesNotExist:
            messages.error(request, "Aucun patient trouvé avec cet identifiant.")
            return redirect('accederdossiermedical')

    return redirect('accederdossiermedical')

@login_required(login_url='user_login')
@login_required_custom
def voir_dossier(request, dossier_id):
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    dossier = get_object_or_404(DossierMedical, id=dossier_id)
    patient = dossier.patient

    consultations_all = Consultation.objects.filter(patient=patient).order_by('-date_consultation')
    prescriptions_all = Prescription.objects.filter(patient=patient).order_by('-created_at')
    examen_all = ExamenMedical.objects.filter(patient=patient).order_by('-date_examen')
    notes_all = InfoConfidentielle.objects.filter(patient=patient).order_by('-created_at')
    documents_all = DocumentMedical.objects.filter(patient=patient).order_by('-created_at')

    # Pagination
    consultation_paginator = Paginator(consultations_all, 4)  # 5 consultations par page
    prescription_paginator = Paginator(prescriptions_all, 4)
    examen_paginator = Paginator(examen_all, 4)
    note_paginator = Paginator(notes_all, 4)
    document_paginator = Paginator(documents_all, 4)
    consultation_page = request.GET.get('consultation_page')
    prescription_page = request.GET.get('prescription_page')
    examen_page = request.GET.get('examen_page')
    document_page = request.GET.get('document_page')
    note_page = request.GET.get('note_page')

    consultations = consultation_paginator.get_page(consultation_page)
    prescriptions = prescription_paginator.get_page(prescription_page)
    examens = examen_paginator.get_page(examen_page)
    notes = note_paginator.get_page(note_page)
    documents = document_paginator.get_page(document_page)
    return render(request, 'Medecin/page/dossierMedicalPatient.html', {
        'dossier': dossier,
        'patient': patient,
        'consultations': consultations,
        'prescriptions': prescriptions,
        'examens': examens,
        'notes': notes,
        'documents': documents,
        'full_name': full_name,
        'image': image,
    })

@login_required(login_url='user_login')
@login_required_custom
def creer_dossier(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        medecin = request.user.medecin  
        dossier = DossierMedical.objects.create(
            medecin=medecin,
            patient=patient,
            created_by=medecin,
            updated_by=medecin,
            created_at=timezone.now()
        )

        patient.a_dossierMedical = True
        Notification.objects.create(
            type_notification="Dossier Medical créé",
            description=f"Le dossier médical du patient {patient.nom} {patient.prenom} a été créé",
            recepteur=medecin.id
        )
        Notification.objects.create(
            type_notification="Dossier Medical créé",
            description=f"Le medecin {medecin.nom} {medecin.prenom} vous a créé un dossier médical",
            recepteur=patient.id
        )
        patient.save()
        return redirect('voir_dossier', dossier_id=dossier.id)
    
    full_name = request.session.get('full_name')
    image = request.session.get('image')
    return render(request, 'Medecin/page/creeDossier.html', {
        'patient': patient,
        'full_name': full_name,
        'image': image,
    })

@login_required(login_url='user_login')
@login_required_custom
def ajout_consultation(request):
    if request.method == 'POST':
        date = request.POST.get('date_consultation')
        motif = request.POST.get('motif')
        temperature = request.POST.get('temperature') or 0
        taille = request.POST.get('taille') or 0
        poids = request.POST.get('poids') or 0
        resultat = request.POST.get('resultat', '')

        patient_id = request.POST.get('patient_id')
        medecin_id = request.user.id

        patient = get_object_or_404(Patient, id=patient_id)
        medecin = get_object_or_404(Medecin, id=medecin_id)

        Consultation.objects.create(
            date_consultation=date,
            motif=motif,
            temperature=temperature,
            taille=taille,
            poids=poids,
            resultat=resultat,
            patient=patient,
            medecin=medecin,
            updated_by=medecin,
            created_at=timezone.now()
        )

        messages.success(request, "Consultation ajoutée avec succès.")
        Notification.objects.create(
            type_notification="Consultation ajoutée",
            description=f"Vous avez ajouté une consultation au patient {patient.nom} {patient.prenom}",
            recepteur=medecin.id
        )
        Notification.objects.create(
            type_notification="Consultation ajoutée",
            description=f"Le medecin {medecin.nom} {medecin.prenom} vous a ajouté une consultation",
            recepteur=patient.id
        )
        dossier = get_object_or_404(DossierMedical, patient=patient)
        return redirect('voir_dossier', dossier_id=dossier.id)

    # Si la requête n'est pas POST, on redirige simplement vers une liste de dossiers ou une page d'erreur
    messages.error(request, "Méthode non autorisée.")
    return redirect('medecin')

@login_required(login_url='user_login')
@login_required_custom
def acceder_dossier_via_qrcode(request):
    user_id = request.GET.get('user_id')
    token = request.GET.get('token')

    if not user_id or not token:
        messages.error(request, "QR code invalide.")
        return redirect('medecin') 

    current_block = int(datetime.utcnow().timestamp() // 120)
    token_valide = False
    for delta in [-1, 0, 1]:
        check_block = current_block + delta
        expected = hashlib.sha256(
            f"{user_id}-{check_block}-{settings.QR_SECRET_KEY}".encode()
        ).hexdigest()
        if token == expected:
            token_valide = True
            break

    if not token_valide:
        messages.error(request, "QR code expiré ou non valide.")
        return redirect('medecin')

    try:
        patient = Patient.objects.get(id=user_id)

        dossier_existe = DossierMedical.objects.filter(patient=patient).exists()

        if dossier_existe:
            dossier = DossierMedical.objects.get(patient=patient)
            Notification.objects.create(
                type_notification="Dossier Medical accédé",
                description=f"Le medecin {request.session.get('full_name')} a accédé au dossier médical ",
                recepteur=patient.id
            )
            return redirect('voir_dossier', dossier_id=dossier.id)
        else:
            return redirect('creer_dossier', patient_id=patient.id)

    except Patient.DoesNotExist:
        messages.error(request, "Aucun patient trouvé avec cet identifiant.")
        return redirect('medecin')
    
@login_required(login_url='user_login')
@login_required_custom
def ajout_prescription(request):
    if request.method == 'POST':
        medicament = request.POST.get('medicament')
        duree = request.POST.get('duree')
        posologie = request.POST.get('posologie')
        mode_admin = request.POST.get('mode_admin')


        patient_id = request.POST.get('patient_id')
        medecin_id = request.user.id

        patient = get_object_or_404(Patient, id=patient_id)
        medecin = get_object_or_404(Medecin, id=medecin_id)

        Prescription.objects.create(
            medicament=medicament,
            duree=duree,
            posologie=posologie,
            mode_administration=mode_admin,
            patient=patient,
            medecin=medecin,
            updated_by=medecin,
            created_at=timezone.now()
        )

        messages.success(request, "Prescription ajoutée avec succès.")
        Notification.objects.create(
            type_notification="Prescription ajoutée",
            description=f"Vous avez ajouté une prescription au patient {patient.nom} {patient.prenom}",
            recepteur=medecin.id
        )
        Notification.objects.create(
            type_notification="Prescription ajoutée",
            description=f"Le medecin {medecin.nom} {medecin.prenom} vous a ajouté une prescription",
            recepteur=patient.id
        )
        dossier = get_object_or_404(DossierMedical, patient=patient)
        return redirect('voir_dossier', dossier_id=dossier.id)

    # Si la requête n'est pas POST, on redirige simplement vers une liste de dossiers ou une page d'erreur
    messages.error(request, "Méthode non autorisée.")
    return redirect('medecin')

@login_required(login_url='user_login')
@login_required_custom
def ajout_examen(request):
    if request.method == 'POST':
        date_examen = request.POST.get('date_examen')
        type_examen = request.POST.get('type_examen')
        resultat = request.POST.get('resultat')
        diagnostic = request.POST.get('diagnostic')
        lieu = request.POST.get('lieu')


        patient_id = request.POST.get('patient_id')
        medecin_id = request.user.id

        patient = get_object_or_404(Patient, id=patient_id)
        medecin = get_object_or_404(Medecin, id=medecin_id)

        ExamenMedical.objects.create(
            date_examen=date_examen,
            type_examen=type_examen,
            resultat=resultat,
            diagnostic=diagnostic,
            lieu=lieu,
            patient=patient,
            medecin=medecin,
            updated_by=medecin,
            created_at=timezone.now()
        )

        messages.success(request, "Examen ajoutée avec succès.")
        Notification.objects.create(
            type_notification="Examen ajouté",
            description=f"Vous avez ajouté un examen au patient {patient.nom} {patient.prenom}",
            recepteur=medecin.id
        )
        Notification.objects.create(
            type_notification="Examen ajouté",  
            description=f"Le medecin {medecin.nom} {medecin.prenom} vous a ajouté un examen",
            recepteur=patient.id
        )
        dossier = get_object_or_404(DossierMedical, patient=patient)
        return redirect('voir_dossier', dossier_id=dossier.id)

        Notification.objects.create(
            type_notification="Examen ajouté",
            description=f"Vous avez ajouté un examen",
            recepteur=user_id
        )

    # Si la requête n'est pas POST, on redirige simplement vers une liste de dossiers ou une page d'erreur
    messages.error(request, "Méthode non autorisée.")
    return redirect('medecin')

@login_required(login_url='user_login')
@login_required_custom
def ajout_rendez_vous(request):
    if request.method == 'POST':
        try:
            date_rendez_vous = request.POST.get('date_rendez_vous')
            type_rendez_vous = request.POST.get('type_rendez_vous')
            description = request.POST.get('description')
            patient_id = request.POST.get('patient_id')

            medecin_id = request.user.id
            patient = get_object_or_404(Patient, id=patient_id)
            medecin = get_object_or_404(Medecin, id=medecin_id)

            # Création du rendez-vous
            rendez_vous = RendezVous.objects.create(
                date_rendez_vous=date_rendez_vous,
                type_rendez_vous=type_rendez_vous,
                description=description,
                patient=patient,
                medecin=medecin,
                created_by=medecin,
                updated_by=medecin,
                created_at=timezone.now()
            )

            # Notifications
            Notification.objects.create(
                type_notification="Rendez-vous ajouté",
                description=f"Vous avez ajouté un rendez-vous au patient {patient.nom} {patient.prenom}.",
                recepteur=medecin.id
            )
            Notification.objects.create(
                type_notification="Rendez-vous ajouté",  
                description=f"Le médecin {medecin.nom} {medecin.prenom} vous a ajouté un rendez-vous.",
                recepteur=patient.id
            )

            # Redirection vers le dossier médical
            dossier = DossierMedical.objects.filter(patient=patient).first()
            if dossier:
                messages.success(request, "Rendez-vous ajouté avec succès.")
                return redirect('voir_dossier', dossier_id=dossier.id)
            else:
                messages.warning(request, "Rendez-vous enregistré mais aucun dossier médical trouvé.")
                return redirect('liste_patients')

        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout du rendez-vous : {str(e)}")
            return redirect('liste_patients')

    messages.error(request, "Méthode non autorisée.")
    return redirect('medecin')

@login_required(login_url='user_login')
@login_required_custom
def ajout_note(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        patient_id = request.POST.get('patient_id')
        medecin_id = request.user.id

        patient = get_object_or_404(Patient, id=patient_id) 
        medecin = get_object_or_404(Medecin, id=medecin_id)
        
        InfoConfidentielle.objects.create(
            description=description,
            patient=patient,
            medecin=medecin,
            created_by=medecin,
            updated_by=medecin,
            created_at=timezone.now()
        )
        dossier = get_object_or_404(DossierMedical, patient=patient)

        messages.success(request, "Note ajoutée avec succès.")
        return redirect('voir_dossier', dossier_id=dossier.id)

    messages.error(request, "Méthode non autorisée.")
    return redirect('medecin')

@login_required(login_url='user_login')
@login_required_custom
def ajout_document(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        image = request.FILES.get('image')
        patient_id = request.POST.get('patient_id')
        medecin_id = request.user.id
        
        patient = get_object_or_404(Patient, id=patient_id)
        medecin = get_object_or_404(Medecin, id=medecin_id)
        
        DocumentMedical.objects.create(
            description=description,
            image=image,
            patient=patient,
            medecin=medecin,
            created_by=medecin,
            updated_by=medecin,
            created_at=timezone.now()
        )
        dossier = get_object_or_404(DossierMedical, patient=patient)
        messages.success(request, "Document ajouté avec succès.")
        return redirect('voir_dossier', dossier_id=dossier.id)

    messages.error(request, "Méthode non autorisée.")
    return redirect('medecin')

@login_required(login_url='user_login')
@login_required_custom
def toggle_visibilite_note(request, note_id):
    note = get_object_or_404(InfoConfidentielle, id=note_id)
    note.visible_par_patient = not note.visible_par_patient
    note.save()
    
    if note.visible_par_patient:
        messages.success(request, "La note est maintenant visible par le patient.")
    else:
        messages.info(request, "La note est maintenant invisible pour le patient.")
    
    # Redirige vers la page d'où provient la requête
    return redirect(request.META.get('HTTP_REFERER', 'medecin'))
