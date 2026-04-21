from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from . import views_main
from .views import views_admin, views_medecin, views_patient, views_structuresante

urlpatterns = [
    path('', views_main.index, name='index'),
    path('login/', views_main.user_login, name='user_login'),
    path('patient/', views.patient, name='patient'),
    path('structure/', views.structure, name='structure'),
    path('super_admin_page/', views.super_admin_page, name='super_admin_page'),
    path('administrateur_page/', views.administrateur_page, name='administrateur_page'),
    path('medecin/', views.medecin, name='medecin'),
    path('logout/', views_main.logout_view, name='logout'),
    path('store/', views_main.store, name='store'),
    path('inscription/patient/', views_main.inscription_patient, name='inscription_patient'),
    path('password_oublie_view', views_main.password_oublie_view, name='password_oublie_view'),
    path('update_password/<str:token>/<str:uid>/', views_main.update_password, name='update_password'),
    path('ajouter_temoin/', views_main.ajouter_temoin, name='ajouter_temoin'),
    path('message_visiteur/', views_main.message_visiteur, name='message_visiteur'),
    path('solution_medecin/', views_main.solution_medecin, name='solution_medecin'),
    path('solution_structure/', views_main.solution_structure, name='solution_structure'),
    path('solution_patient/', views_main.solution_patient, name='solution_patient'),
    path('inscription_structure/', views_main.inscription_structure, name='inscription_structure'),

    ##PARTIE PATIENT
    path('chatbot/', views_patient.chatbot, name='chatbot'),
    path('chatbot/delete_history/', views_patient.delete_chat_history, name='delete_chat_history'),
    path('nouvelle-conversation/', views_patient.nouvelle_conversation, name='nouvelle_conversation'),
    path('charger-conversation/<int:conversation_id>/', views_patient.charger_conversation, name='charger_conversation'),
    path('consultation/', views.consultation, name='consultation'),
    path('demandecarte/', views.demandecarte, name='demandecarte'),
    path('documentmedical/', views.documentmedical, name='documentmedical'),
    path('dossiermedical/', views.dossiermedical, name='dossiermedical'),
    path('examenmedical/', views.examenmedical, name='examenmedical'),
    path('historiquesoin/', views.historiquesoin, name='historiquesoin'),
    path('prescription/', views.prescription, name='prescription'),
    path('profil/', views.profil, name='profil'),
    path('qrcode_view/', views.qrcode_view, name='qrcode_view'),
    path('generer-identifiant/', views.generer_identifiant, name='generer_identifiant'),
    path('demande_carte/', views.demande_carte_view, name='demande_carte'),
    path('changer_mot_de_passe_patient/', views.changer_mot_de_passe_patient, name='changer_mot_de_passe_patient'),
    path('modifier_infos_patient/', views.modifier_infos_patient, name='modifier_infos_patient'),
    path('modifier_photo_patient/', views.modifier_photo_patient, name='modifier_photo_patient'),
    path('notification_patient/', views.notification_patient, name='notification_patient'),
    path('historique_rendez_vous/', views.historique_rendez_vous, name='historique_rendez_vous'),
    path('partager_dossier/', views.partager_dossier, name='partager_dossier'),
    path('completer_profil/', views.completer_profil, name='completer_profil'),
    path('modifier_infos_supplementaire/', views.modifier_infos_supplementaire, name='modifier_infos_supplementaire'),


    ##PARTIE STRUCTURE
    path('profil_structure/', views.profil_structure, name='profil_structure'),
    path('listeMedecin/', views.listemedecin, name='listeMedecin'),
    path('notification_structure/', views.notification_structure, name='notification_structure'),
    path('ajouter_un_medecin/', views.ajouter_un_medecin, name='ajouter_un_medecin'),
    path('modifier-medecin/<int:id>/', views.modifier_medecin, name='modifier_medecin'),
    path('archiver_medecin_structure/<int:id>/', views.archiver_medecin_structure, name='archiver_medecin_structure'),
    path('desarchiver_medecin_structure/<int:id>/', views.desarchiver_medecin_structure, name='desarchiver_medecin_structure'),
    path('changer-mot-de-passe-structure/', views.changer_mot_de_passe_structure, name='changer_mot_de_passe_structure'),
    path('modifier-photo-structure/', views.modifier_photo_structure, name='modifier_photo_structure'),
    path('modifier-infos-structure/', views.modifier_infos_structure, name='modifier_infos_structure'),
    path('alerte_sante/', views.alerte_sante, name='alerte_sante'),
    path('ajouter_alerte_sante/', views.ajouter_alerte_sante, name='ajouter_alerte_sante'),
    path('modifier_alerte_sante/<int:id>/', views.modifier_alerte_sante, name='modifier_alerte_sante'),


    ##PARTIE MEDECIN 
    path('profil_medecin/', views.profil_medecin, name='profil_medecin'),
    path('accederdossiermedical/', views.accederdossiermedical, name='accederdossiermedical'),
    path('dossier_medical_patient/', views.dossier_medical_patient, name='dossier_medical_patient'),
    path('dossier/<int:dossier_id>/', views.voir_dossier, name='voir_dossier'),
    path('creer-dossier/<int:patient_id>/', views.creer_dossier, name='creer_dossier'),
    path('acceder-dossier/', views.acceder_dossier_via_code, name='acceder_dossier_via_code'),
    path('ajouter-consultation/', views.ajout_consultation, name='ajout_consultation'),
    path('ajouter-prescription/', views.ajout_prescription, name='ajout_prescription'),
    path('ajouter-examen/', views.ajout_examen, name='ajout_examen'),
    path('acceder_dossier_qr/', views.acceder_dossier_via_qrcode, name='acceder_dossier_via_qrcode'),
    path('notifications_medecin/', views.notifications_medecin, name='notifications_medecin'),
    path('changer-mot-de-passe-medecin/', views.changer_mot_de_passe_medecin, name='changer_mot_de_passe_medecin'),
    path('modifier-infos-medecin/', views.modifier_infos_medecin, name='modifier_infos_medecin'),
    path('modifier-photo-medecin/', views.modifier_photo_medecin, name='modifier_photo_medecin'),
    path('definir_password_medecin/<uuid:token>/', views.definir_password_medecin, name='definir_password_medecin'),
    path('ajout_rendez_vous/', views.ajout_rendez_vous, name='ajout_rendez_vous'),
    path('ajout_note/', views.ajout_note, name='ajout_note'),
    path('note/<int:note_id>/toggle_visibilite/', views.toggle_visibilite_note, name='toggle_visibilite_note'),
    path('ajout_document/', views.ajout_document, name='ajout_document'),
    path('info_medecin/', views.info_medecin, name='info_medecin'),

    






    ##PARTIE ADMIN
    path('liste_utilisateur/', views.liste_utilisateur, name='liste_utilisateur'),
    path('gerer_inscription/', views.gerer_inscription, name='gerer_inscription'),
    path('valider_inscription/<int:structure_id>/', views.valider_inscription, name='valider_inscription'),
    path('ajouter_Admin', views.ajout_admin, name='ajout_admin'),
    path('bloquer_medecin_admin/<int:id>/', views.bloquer_medecin_admin, name='bloquer_medecin_admin'),
    path('debloquer_medecin_admin/<int:id>/', views.debloquer_medecin_admin, name='debloquer_medecin_admin'),
    path('bloquer_patient_admin/<int:id>/', views.bloquer_patient_admin, name='bloquer_patient_admin'),
    path('debloquer_patient_admin/<int:id>/', views.debloquer_patient_admin, name='debloquer_patient_admin'),
    path('bloquer_structure_admin/<int:id>/', views.bloquer_structure_admin, name='bloquer_structure_admin'),
    path('debloquer_structure_admin/<int:id>/', views.debloquer_structure_admin, name='debloquer_structure_admin'),
    path('bloquer_admin/<int:id>/', views.bloquer_admin, name='bloquer_admin'),
    path('debloquer_admin/<int:id>/', views.debloquer_admin, name='debloquer_admin'),
    path('ajouter_un_admin', views.ajouter_un_admin, name='ajouter_un_admin'),
    path('profil_admin', views.profil_admin, name='profil_admin'),
    path('notification', views.notification, name='notification'),
    path('changer-mot-de-passe/', views.changer_mot_de_passe, name='changer_mot_de_passe'),
    path('modifier-infos-admin/', views.modifier_infos_admin, name='modifier_infos_admin'),
    path('modifier-photo/', views.modifier_photo, name='modifier_photo'),
    path('listeDemandeCarte/', views.listeDemandeCarte, name='listeDemandeCarte'),
    path('Demande-carte/<int:demande_id>/pdf/', views.carte_patient_pdf, name='carte_patient_pdf'),
    path('bloq_debloq_structure/<int:structure_id>/', views.bloq_debloq_structure, name='bloq_debloq_structure'),
    path('promouvoir_admin/<int:admin_id>/', views.promouvoir_admin, name='promouvoir_admin'),
    path('definir_password/<uuid:token>/', views.definir_password, name='definir_password'),

    path('gerer_inscription_admin/', views.gerer_inscription_admin, name='gerer_inscription_admin'),
    path('listeDemandeCarte_admin/', views.listeDemandeCarte_admin, name='listeDemandeCarte_admin'),
    path('notification_admin/', views.notification_admin, name='notification_admin'),
    path('profil_admin_page/', views.profil_admin_page, name='profil_admin_page'),
    path('audit_acces_dossier_medical/', views.audit_acces_dossier_medical, name='audit_acces_dossier_medical'),
    path('changer_mot_de_passe_admin/', views.changer_mot_de_passe_admin, name='changer_mot_de_passe_admin'),
    path('modifier_infos_administrateur/', views.modifier_infos_administrateur, name='modifier_infos_administrateur'),
    path('modifier_photo_admin/', views.modifier_photo_admin, name='modifier_photo_admin'),










] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

