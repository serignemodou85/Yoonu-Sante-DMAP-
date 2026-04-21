// Séléctionner les champs du formulaire
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const form = document.querySelector("form");
const btnSubmit = form.querySelector("button[type='submit']");

let isEmailValid = false;
let isPasswordValid = false;

// Désactiver le bouton de soumission par défaut
btnSubmit.disabled = true;

// Permet d'afficher ou masquer les messages d'erreur
function showError(input, message, isValid) {
    const baliseP = input.nextElementSibling;
    if (message) {
        baliseP.textContent = message;
        input.classList.add("is-invalid");
        input.classList.remove("is-valid");
    } else {
        baliseP.textContent = "";
        input.classList.remove("is-invalid");
        input.classList.add("is-valid");
    }
}

// Validation de l'email à la saisie
emailInput.addEventListener("input", () => {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    isEmailValid = emailPattern.test(emailInput.value);
    showError(emailInput, isEmailValid ? "" : "Veuillez entrer un email valide.", isEmailValid);
    checkFormValidity();
});

// Validation du mot de passe à la saisie
passwordInput.addEventListener("input", () => {
    isPasswordValid = passwordInput.value.trim().length >= 8;
    showError(passwordInput, isPasswordValid ? "" : "Le mot de passe doit contenir au moins 8 caractères.", isPasswordValid);
    checkFormValidity();
});

// Active le bouton de connexion si les deux champs sont valides
function checkFormValidity() {
    if (isEmailValid && isPasswordValid) {
        btnSubmit.removeAttribute("disabled");
    } else {
        btnSubmit.disabled = true;
    }
}

// Réinitialisation du formulaire
form.addEventListener("reset", () => {
    isEmailValid = isPasswordValid = false;
    btnSubmit.disabled = true;
});
