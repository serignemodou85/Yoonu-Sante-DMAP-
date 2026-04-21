
// Récupération des champs du formulaire
const nomInputUser = document.getElementById("user-nom");
const adresseInputUser = document.getElementById("user-adresse");
const telephoneInputUser = document.getElementById("user-telephone");
const emailInputUser = document.getElementById("user-email");
const passwordInputUser = document.getElementById("user-password");
const photoInputUser = document.getElementById("user-photo");
const frmAddUser = document.getElementById("addUserForm");
const btnSubmitUser = frmAddUser.querySelector("button[type='submit']");

let isNameValidUser = false;
let isAdresseValidUser = false;
let isTelephoneValidUser = false;
let isEmailValidUser = false;
let isPasswordValidUser = false;
let isPhotoValidUser = false;

// Désactive le bouton de soumission par defaut
// btnSubmitUser.disabled = true;

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

function checkFormValidity() {
    if (isNameValidUser && isAdresseValidUser && isTelephoneValidUser && isEmailValidUser && isPasswordValidUser && isPhotoValidUser) {
        btnSubmitUser.removeAttribute("disabled");
    } else {
        btnSubmitUser.setAttribute("disabled", "true");
    }
}

// Validation du champ nom à la saisie
nomInputUser.addEventListener("input", () => {
    const nom = nomInputUser.value.trim();
    const nomValidator = Validator.nameValidator("Le nom", 5, 40, nom);

    if (nomValidator) {
        showError(nomInputUser, nomValidator.message);
        isNameValidUser = false;
    }
    else
    {
        showError(nomInputUser, "");
        isNameValidUser = true;
    }
    checkFormValidity();
});

// Validation du champ adresse à la saisie
adresseInputUser.addEventListener("input", () => {
    const adresse = adresseInputUser.value.trim();
    const adresseValidator = Validator.adresseValidator("L'adresse", 5, 50, adresse);

    if (adresseValidator) {
        showError(adresseInputUser, adresseValidator.message);
        isAdresseValidUser = false;
    }
    else
    {
        showError(adresseInputUser, "");
        isAdresseValidUser = true;
    }
    checkFormValidity();
});

// Validation du champ telephone à la saisie
telephoneInputUser.addEventListener("input", () => {
    const telephone = telephoneInputUser.value.trim();
    const telephoneValidator = Validator.phoneValidator("Le numéro de téléphone", 9, 17, telephone);

    if (telephoneValidator) {
        showError(telephoneInputUser, telephoneValidator.message);
        isTelephoneValidUser = false;
    }
    else
    {
        showError(telephoneInputUser, "");
        isTelephoneValidUser = true;
    }
    checkFormValidity();
});


// Validation du champ email à la saisie
emailInputUser.addEventListener("input", () => {
    const email = emailInputUser.value.trim();
    const emailValidator = Validator.emailValidator("L'email", email);

    if (emailValidator) {
        showError(emailInputUser, emailValidator.message);
        isEmailValidUser = false;
    }
    else
    {
        showError(emailInputUser, "");
        isEmailValidUser = true;
    }
    checkFormValidity();
});

// Validation du champ mot de passe
passwordInputUser.addEventListener("input", () => {
    const password = passwordInputUser.value.trim();
    isPasswordValidUser = password.length >= 6;
    showError(passwordInputUser, isPasswordValidUser ? "" : "Le mot de passe doit contenir au moins 6 caractères.");
    checkFormValidity();
});

// Validation du champ photo à la selection
photoInputUser.addEventListener("change", () => {
    const file = photoInputUser.files[0];
    if (!file) {
        showError(photoInputUser, "La photo est obligatoire.");
        isPhotoValidUser = false;
    }
    else if (!file.type.startsWith("image/")) {
        showError(photoInputUser, "Le fichier doit être une image.");
        isPhotoValidUser = false;
    }
    else {
        showError(photoInputUser, "");
        isPhotoValidUser = true;
    }
    checkFormValidity();
});


// Réinitialisation du formulaire
frmAddUser.addEventListener("reset", () => {
    isNameValidUser = false;
    isAdresseValidUser = false;
    isTelephoneValidUser = false;
    isEmailValidUser = false;
    isPasswordValidUser = false;
    isPhotoValidUser = false;
    btnSubmitUser.setAttribute("disabled", "true");
});
