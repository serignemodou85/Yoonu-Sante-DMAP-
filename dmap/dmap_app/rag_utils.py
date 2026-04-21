import hashlib
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from django.core.cache import cache
from .models import Consultation, Prescription, ExamenMedical, InfoConfidentielle
import os

# Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
EMBEDDING_MODEL = "mistral"
# on recupere les documents textuels pertinents pour un patient.
def get_patient_documents(patient):
    docs = []
    
    consultations = Consultation.objects.filter(patient=patient).order_by('-date_consultation')
    for item in consultations:
        docs.append(f"Consultation du {item.date_consultation.strftime('%d/%m/%Y')}:\nMotif: {item.motif}\nRésultat: {item.resultat}\n")

    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
    for item in prescriptions:
        docs.append(f"Prescription du {item.created_at.strftime('%d/%m/%Y')}:\nMédicament: {item.medicament}\nPosologie: {item.posologie}\n")

    examens = ExamenMedical.objects.filter(patient=patient).order_by('-date_examen')
    for item in examens:
        docs.append(f"Examen du {item.date_examen.strftime('%d/%m/%Y')}:\nType: {item.type_examen}\nRésultat: {item.resultat}\n")

    infos = InfoConfidentielle.objects.filter(patient=patient, visible_par_patient=True).order_by('-created_at')
    for item in infos:
        docs.append(f"Note médicale du {item.created_at.strftime('%d/%m/%Y')}:\n{item.description}\n")

    return "\n\n".join(docs)

def get_vector_store(patient):
    """
    Crée ou récupère un VectorStore FAISS pour les documents d'un patient.
    Utilise le stockage sur disque pour accélérer les requêtes suivantes.
    """
    documents_text = get_patient_documents(patient)
    if not documents_text:
        return None

    # Dossier pour stocker les index FAISS
    index_dir = os.path.join('faiss_indexes')
    os.makedirs(index_dir, exist_ok=True)
    index_path = os.path.join(index_dir, f'patient_{patient.id}')

    # Si l'index existe déjà, on le charge
    if os.path.exists(index_path):
        try:
            print(f"Chargement de l'index FAISS depuis {index_path}")
            embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
            vector_store = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
            return vector_store
        except Exception as e:
            print(f"Erreur lors du chargement de l'index FAISS : {e}")
            # Si erreur, on reconstruit l'index

    print("Création d'un nouveau VectorStore.")
    # 1. Segmenter les documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = text_splitter.split_text(documents_text)

    # 2. Créer les embeddings
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    # 3. Créer et sauvegarder le VectorStore
    try:
        vector_store = FAISS.from_texts(texts=chunks, embedding=embeddings)
        vector_store.save_local(index_path)
        print(f"VectorStore créé et sauvegardé dans {index_path}.")
        return vector_store
    except Exception as e:
        print(f"Erreur lors de la création du VectorStore FAISS : {e}")
        return None

def search_relevant_passages(query, patient, k=3):
    """
    Effectue une recherche sémantique pour trouver les passages les plus pertinents.
    """
    vector_store = get_vector_store(patient)
    if not vector_store:
        return ""

    try:
        results = vector_store.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in results])
    except Exception as e:
        print(f"Erreur lors de la recherche de similarité : {e}")
        return "" 