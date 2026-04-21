// Récupération des champs du formulaire
var idEditInput = document.getElementById("edit-user-id");
var nomEditInput = document.getElementById("edit-user-nom");
var adresseEditInput = document.getElementById("edit-user-adresse");
var telephoneEditInput = document.getElementById("edit-user-telephone");
var emailEditInput = document.getElementById("edit-user-email");
var photoEditInput = document.getElementById("edit-user-photo");
var roleEditInput = document.getElementById("edit-user-role");
var frmEditUser = document.getElementById("editUserForm");
var btnEditSubmit = frmEditUser.querySelector("button[type='submit']");
var photoEditPreview = document.getElementById("photo-edit-preview");

var isNameEditValid = false;
var isAdresseEditValid = false;
var isTelephoneEditValid = false;
var isEmailEmailValid = false;
var isPhotoEditValid = false;
var isRoleEditValid = false;

// Désactive le bouton de soumission par defaut
btnEditSubmit.disabled = true;

// Permet d'afficher ou masquer les message d'erreur
function showError(input, message)
{
    const baliseP = input.nextElementSibling;
    if (message) {
        baliseP.textContent = message;
        input.classList.add("is-invalid");
        baliseP.style.color = "brown";
        baliseP.style.fontWeight = "bold";
    }
    else
    {
        baliseP.textContent = "";
        input.classList.remove("is-invalid");
    }
}

function checkFormValidity()
{

    if ( isNameEditValid
         && isAdresseEditValid
         && isTelephoneEditValid
         && isEmailEmailValid
         && photo && photo.type.startsWith("image/") || photoEditPreview.src !== ""
         && isRoleEditValid) {
        
         btnEditSubmit.removeAttribute("disabled");
        
     }
}


// Validation du champ nom à la saisie
nomEditInput.addEventListener("input", () => {
    const nom = nomEditInput.value.trim();
    const nomValidator = Validator.nameValidator("Le nom", 5, 40, nom);

    if (nomValidator) {
        showError(nomEditInput, nomValidator.message);
        isNameEditValid = false;
    }
    else
    {
        showError(nomEditInput, "");
        isNameEditValid = true;
    }
    checkFormValidity();
});

// Validation du champ adresse à la saisie
adresseEditInput.addEventListener("input", () => {
    const adresse = adresseEditInput.value.trim();
    const adresseValidator = Validator.adresseValidator("L'adresse", 5, 50, adresse);

    if (adresseValidator) {
        showError(adresseEditInput, adresseValidator.message);
        isAdresseEditValid = false;
    }
    else
    {
        showError(adresseEditInput, "");
        isAdresseEditValid = true;
    }
    checkFormValidity();
});

// Validation du champ telephone à la saisie
telephoneEditInput.addEventListener("input", () => {
    const telephone = telephoneEditInput.value.trim();
    const telephoneValidator = Validator.phoneValidator("Le numéro de téléphone", 9, 17, telephone);

    if (telephoneValidator) {
        showError(telephoneEditInput, telephoneValidator.message);
        isTelephoneEditValid = false;
    }
    else
    {
        showError(telephoneEditInput, "");
        isTelephoneEditValid = true;
    }
    checkFormValidity();
});


// Validation du champ email à la saisie
emailEditInput.addEventListener("input", () => {
    const email = emailEditInput.value.trim();
    const emailValidator = Validator.emailValidator("L'email", email);

    if (emailValidator) {
        showError(emailEditInput, emailValidator.message);
        isEmailEmailValid = false;
    }
    else
    {
        showError(emailEditInput, "");
        isEmailEmailValid = true;
    }
    checkFormValidity();
});


// // Validation du champ photo à la selection
photoEditInput.addEventListener("change", () => {
    const file = photoEditInput.files[0];
    if (!file && !photoEditPreview.src) {
        showError(photoInput, "La photo est obligatoire.");
    }
    else if (!file.type.startsWith("image/")) {
        showError(photoInput, "Le fichier doit être une image.");
    }
    else {
        showError(photoInput, "");
    }
    checkFormValidity();
});


frmEditUser.addEventListener("reset", () => {
    isNameEditValid = false;
    isAdresseEditValid = false;
    isTelephoneEditValid = false;
    isEmailEmailValid = false;
    isPhotoEditValid = false;
    isRoleEditValid = false;
    btnEditSubmit.disabled = true;
});


 const editButtonsUser = document.querySelectorAll('.btn-edit-User');

 editButtonsUser.forEach(button => {
    button.addEventListener("click", () => {
        // Récupération des données depuis les attributs data-edit-*
        const id = button.getAttribute("data-edit-id");
        const nom = button.getAttribute("data-edit-nom");
        const adresse = button.getAttribute("data-edit-adresse");
        const telephone = button.getAttribute("data-edit-telephone");
        const email = button.getAttribute("data-edit-email");
        const photo = button.getAttribute("data-edit-photo");

        // Vérification des valeurs récupérées
        console.log(id, nom, adresse, telephone, email, photo);

        // Remplir les champs du formulaire avec les données récupérées
        idEditInput.value = id;
        nomEditInput.value = nom;
        adresseEditInput.value = adresse;
        telephoneEditInput.value = telephone;
        emailEditInput.value = email;

        // Mettre à jour la source de l'aperçu de la photo
        if (photo) {
            photoEditPreview.src = `public/images/users/${photo}`;
        } else {
            photoEditPreview.src = "public/images/users/default.png";
        }

        // Validation du formulaire
        isNameEditValid = Validator.nameValidator("Le nom", 5, 40, nom) == null;
        isAdresseEditValid = Validator.adresseValidator("L'adresse", 5, 50, adresse) == null;
        isTelephoneEditValid = Validator.phoneValidator("Le numéro de téléphone", 9, 17, telephone) == null;
        isEmailEmailValid = Validator.emailValidator("L'email", email) == null;
        isPhotoEditValid = photo != null;

        // Activer ou désactiver le bouton de soumission
        btnEditSubmit.disabled = !(isNameEditValid && isAdresseEditValid && isTelephoneEditValid && isEmailEmailValid && isPhotoEditValid);
    });
});
