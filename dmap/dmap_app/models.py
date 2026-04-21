from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django_countries.fields import CountryField
import uuid
import qrcode
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from datetime import timedelta

# ADMINISTRATEUR
class Administrateur(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin')
    ]

    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=200, null=True, blank=True)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    telephone = models.CharField(max_length=25)
    image = models.ImageField(upload_to='img/', null=True, blank=True)
    adresse = models.CharField(max_length=50)
    status = models.CharField(max_length=15)
    bloquer = models.BooleanField(default=False)
    role = models.CharField(max_length=15, default='Administrateur')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.status})"


# STRUCTURE DE SANTE
class StructureSante(models.Model):
    TYPE_CHOICES = [
        ('hopital', 'Hôpital'),
        ('clinique', 'Clinique'),
    ]

    nom = models.CharField(max_length=100)
    type_structure = models.CharField(max_length=20, choices=TYPE_CHOICES)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=200, null=True, blank=True)
    adresse = models.TextField()
    ville = models.CharField(max_length=30)
    region = models.CharField(max_length=30)
    telephone = models.CharField(max_length=25)
    site_web = models.URLField(blank=True, null=True)
    valide = models.BooleanField(default=False)
    bloquer = models.BooleanField(default=False)
    date_inscription = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to='img/', null=True, blank=True)
    created_by = models.ForeignKey(Administrateur, on_delete=models.SET_NULL, related_name='structuresante_created', null=True, blank=True)
    updated_by = models.ForeignKey(Administrateur, on_delete=models.SET_NULL, related_name='structuresante_updated', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} - {self.type_structure}"


# SPECIALISATION
class Specialisation(models.Model):
    nom = models.CharField(max_length=50)
    created_by = models.ForeignKey(Administrateur, on_delete=models.SET_NULL, related_name='specialisations_created', null=True, blank=True)
    updated_by = models.ForeignKey(Administrateur, on_delete=models.SET_NULL, related_name='specialisations_updated', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


# SERVICE
class Service(models.Model):
    nom = models.CharField(max_length=50)
    created_by = models.ForeignKey(Administrateur, on_delete=models.SET_NULL, related_name='services_created', null=True, blank=True)
    updated_by = models.ForeignKey(Administrateur, on_delete=models.SET_NULL, related_name='services_updated', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


# UTILISATEUR
class Utilisateur(AbstractUser):
    SEXE_CHOICES = [('M', 'Masculin'), ('F', 'Féminin')]
    ROLES = (
        ('medecin', 'Médecin'),
        ('patient', 'Patient'),
    )

    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=50)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    telephone = models.CharField(max_length=25)
    pays = CountryField( null=True)
    adresse = models.TextField()
    image = models.ImageField(upload_to='img/', blank=True, null=True)
    statut = models.CharField(max_length=20, choices=ROLES)
    bloquer = models.BooleanField(default=False)
    archiver = models.BooleanField(default=False)
    


    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'prenom', 'nom']

    def __str__(self):
        return f"{self.prenom} {self.nom}"


# MEDECIN
class Medecin(Utilisateur):
    specialisation = models.ForeignKey(Specialisation, on_delete=models.CASCADE)
    structure_sante = models.ForeignKey(StructureSante, on_delete=models.CASCADE)
    numero_licence = models.CharField(max_length=50)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(StructureSante, on_delete=models.SET_NULL, related_name='medecin_created', null=True, blank=True)
    updated_by = models.ForeignKey(StructureSante, on_delete=models.SET_NULL, related_name='medecin_updated', null=True, blank=True)

    def __str__(self):
        return f"Dr {self.prenom} {self.nom} - {self.specialisation.nom}"


# PATIENT
class Patient(Utilisateur):
    SITUATION_FAMILIALE = (
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié'),
    )
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=50)
    groupe_sanguin = models.CharField(max_length=5)
    situation_familiale = models.CharField(max_length=15, choices=SITUATION_FAMILIALE)
    a_dossierMedical = models.BooleanField(default=False)

    identifiant = models.CharField(max_length=15, null= True, unique=True)

    profession = models.CharField(max_length=100)
    contact_urgence = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(StructureSante, on_delete=models.SET_NULL, related_name='utilisateurs_updated', null=True, blank=True)

    qr_code_token = models.CharField(max_length=100, blank=True, null=True)
    qr_code_expire_at = models.DateTimeField(blank=True, null=True)

    # Méthode pour générer un token QR
    def generer_qr_token(self):
        # Générer un token unique
        self.qr_code_token = str(uuid.uuid4())

        # Définir une expiration du token dans 24 heures
        self.qr_code_expire_at = timezone.now() + timedelta(days=1)

        # Sauvegarder l'objet patient avec le nouveau token
        self.save()
    
    # Méthode pour générer le QR code
    def generer_qr_code(self):
        # Vérifie si le token existe et n'est pas expiré
        if not self.qr_code_token or self.qr_code_expire_at <= timezone.now():
            self.generer_qr_token()  # Génère un nouveau token si nécessaire
        
        qr = qrcode.make(self.qr_code_token)  # Générer le QR code avec le token

        # Convertir l'image en BytesIO
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        # Sauvegarder l'image dans un champ ImageField ou un champ personnalisé
        image_file = InMemoryUploadedFile(img_io, None, f"{self.qr_code_token}.png", 'image/png', img_io.tell(), None)
        return image_file


    def __str__(self):
        return f"{self.prenom} {self.nom} - Patient"


# DOSSIER MEDICAL
class DossierMedical(models.Model):
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    complet = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='dossiers_created', null=True, blank=True)
    updated_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='dossiers_updated', null=True, blank=True)

    def __str__(self):
        return f"Dossier de {self.created_at} {self.created_by}"

# EXAMEN MEDICAL
class ExamenMedical(models.Model):
    type_examen = models.CharField(max_length=50)
    resultat = models.CharField(max_length=255)
    diagnostic = models.TextField()
    date_examen = models.DateField()
    lieu = models.CharField(max_length=255)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='examens_created', null=True, blank=True)
    updated_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='examens_updated', null=True, blank=True)

    def __str__(self):
        return f"Examen {self.type_examen} de {self.patient.prenom} {self.patient.nom}"
    

# CONSULTATION
class Consultation(models.Model):
    date_consultation = models.DateField()
    temperature = models.FloatField()
    taille = models.FloatField()
    poids = models.FloatField()
    motif = models.CharField(max_length=100)
    resultat = models.TextField()
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='consultations_updated', null=True, blank=True)

    def __str__(self):
        return f"Consultation du {self.date_consultation} - {self.patient.prenom} {self.patient.nom}"


# PRESCRIPTION
class Prescription(models.Model):
    medicament = models.CharField(max_length=255)
    duree = models.IntegerField(help_text="Durée du traitement en jours")
    posologie = models.CharField(max_length=255, help_text="Exemple : 2 comprimés par jour")
    mode_administration = models.CharField(max_length=255, help_text="Exemple : Oral, Intraveineuse, etc.")

    date_debut = models.DateField(default=timezone.now, null=True, blank=True)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='prescriptions_created', null=True, blank=True)
    updated_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='prescriptions_updated', null=True, blank=True)

    def date_fin(self):
        return self.date_debut + timedelta(days=self.duree)

    def jours_restants(self):
        today = timezone.now().date()
        return max((self.date_fin() - today).days, 0)

    def en_cours(self):
        today = timezone.now().date()
        return self.date_debut <= today <= self.date_fin()

    def est_terminee(self):
        return timezone.now().date() > self.date_fin()

    def __str__(self):
        return f"Prescription de {self.medicament} pour {self.patient.prenom} {self.patient.nom}"


# DOCUMENT MEDICAL 
class DocumentMedical(models.Model):
    image = models.ImageField(upload_to='img/', blank=True, null=True)
    description = models.CharField(max_length=255)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='documents_created', null=True, blank=True)
    updated_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='documents_updated', null=True, blank=True)

    def __str__(self):
        return f"Document {self.description} pour {self.patient.prenom} {self.patient.nom}"
    
# INFO CONFIDENTIEL 
class InfoConfidentielle(models.Model):
    description = models.CharField(max_length=255)
    visible_par_patient = models.BooleanField(default=False)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='infos_created', null=True, blank=True)
    updated_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='infos_updated', null=True, blank=True)

    def __str__(self):
        return f"Info Confidentielle de {self.patient.prenom} {self.patient.nom}" 


class Notification(models.Model):
    recepteur = models.CharField(max_length=255)
    type_notification= models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.recepteur}"

    class Meta:
        ordering = ['-created_at']

class DemandeCarte(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date_demande = models.DateTimeField(auto_now_add=True)
    qr_code_image = models.ImageField(upload_to='qrcodes/', null=True, blank=True)
    statut = models.CharField(max_length=20, default='En attente')

    def __str__(self):
        return f"Demande de carte - {self.patient.username}"

class PasswordResetToken(models.Model):
    admin = models.ForeignKey(Administrateur, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        # Exemple : token valable 1 jour
        return timezone.now() - self.created_at < timezone.timedelta(days=1)

class PasswordResetTokenMedecin(models.Model):
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        # Exemple : token valable 1 jour
        return timezone.now() - self.created_at < timezone.timedelta(days=1)

class RendezVous(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    date_rendez_vous = models.DateTimeField()
    description = models.TextField()
    type_rendez_vous = models.CharField(max_length=20, default='Consultation')
    statut = models.CharField(max_length=20, default='En attente')
    rappel_envoye = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='rendez_vous_created', null=True, blank=True)
    updated_by = models.ForeignKey(Medecin, on_delete=models.SET_NULL, related_name='rendez_vous_updated', null=True, blank=True)


    def __str__(self):
        return f"Rendez-vous de {self.patient.prenom} {self.patient.nom} avec {self.medecin.prenom} {self.medecin.nom}"


class AlerteSanitaire(models.Model):
    structure_sante = models.ForeignKey(StructureSante, on_delete=models.CASCADE)
    date_alerte = models.DateTimeField(default=timezone.now)
    justification = models.TextField()
    groupe_sanguin = models.CharField(max_length=5,null=True, blank=True)
    quantite = models.IntegerField(null=True, blank=True)
    statut = models.CharField(max_length=20, default='En attente')
    type_don = models.CharField(max_length=20)
    urgence = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(StructureSante, on_delete=models.SET_NULL, related_name='alertes_created', null=True, blank=True)
    updated_by = models.ForeignKey(StructureSante, on_delete=models.SET_NULL, related_name='alertes_updated', null=True, blank=True)
    fichier_joint = models.FileField(upload_to='img/', null=True, blank=True)


    def __str__(self):
        return f"{self.structure_sante.nom}"
    

class AuditLog(models.Model):
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    administrateur = models.ForeignKey(Administrateur, on_delete=models.CASCADE, null=True, blank=True)
    structure_sante = models.ForeignKey(StructureSante, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=30)
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.medecin} a fait {self.action} sur {self.patient} le {self.date.strftime('%d/%m/%Y %H:%M')}"
    
    def get_utilisateur(self):
        if self.medecin:
            return self.medecin
        elif self.patient:
            return self.patient
        elif self.administrateur:
            return self.administrateur
        elif self.structure_sante:
            return self.structure_sante


class Temoin(models.Model):
    nom = models.CharField(max_length=100)
    fonction = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(upload_to='img/')
    etoiles = models.PositiveSmallIntegerField(default=5)
    affichage = models.BooleanField(default=False)


    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

class MessageVisiteur(models.Model):
    nom= models.CharField(max_length=100)
    email= models.EmailField()
    telephone= models.CharField(max_length=100)
    message= models.TextField()
    type_utilisateur= models.CharField(max_length=50)
    created_at= models.DateTimeField(auto_now_add=True)

# CHATBOT
class Conversation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    title = models.CharField(max_length=200, default="Nouvelle conversation")

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation de {self.patient} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

class ChatMessage(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    message = models.TextField()
    reponse = models.TextField(null=True, blank=True)
    horodatage = models.DateTimeField(auto_now_add=True)
    est_utilisateur = models.BooleanField(default=True)
    intention = models.CharField(max_length=255, null=True, blank=True)
    is_urgent = models.BooleanField(default=False)

    class Meta:
        ordering = ['horodatage']

    def __str__(self):
        return f'Message de {self.patient.get_full_name()} à {self.horodatage.strftime("%Y-%m-%d %H:%M")}'
