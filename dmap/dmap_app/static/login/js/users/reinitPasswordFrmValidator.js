
// Récupération des champs du formulaire
const newPassword = document.getElementById("new_password");
const confirmPassword = document.getElementById("confirm_password");

const frmReinitPassword = document.getElementById("reinitPasswordForm");
const btnSubmitReinitPassword = document.getElementById("btnSubmitReinit");

btnSubmitReinitPassword.disabled = true;


var isNewPasswordValid = false;
var isPasswordConfirmValid = false;

function checkFormValidity()
{
    console.log(isNewPasswordValid);
    console.log(isPasswordConfirmValid);
    if (isNewPasswordValid && isPasswordConfirmValid) {
        btnSubmitReinitPassword.removeAttribute("disabled");
    }
}

// Permet d'afficher ou masquer les message d'erreur
function showError(input, message)
{
    const baliseP = input.nextElementSibling;
    if (message) {
        baliseP.textContent = message;
        input.classList.add("is-invalid");
        // baliseP.style.color = "brown";
        baliseP.style.fontWeight = "bold";
    }
    else
    {
        baliseP.textContent = "";
        input.classList.remove("is-invalid");
    }
}

// Validation du nouveau mot de passe
newPassword.addEventListener("input", () => {
    const newPasswordValue = newPassword.value.trim();
    const newPasswordValidator = Validator.passwordValidator("Le password", newPasswordValue, 8);

    if (newPasswordValidator) {
        showError(newPassword, newPasswordValidator.message);
        isNewPasswordValid = false;
    }
    else
    {
        showError(newPassword, "");
        isNewPasswordValid = true;
    }
    checkFormValidity();
});


// Validation du mot de passe de confirmation
confirmPassword.addEventListener("input", () => {
    const confirmPasswordValue = confirmPassword.value.trim();
    const confirmPasswordValidator = Validator.passwordValidator("Le password de confirmation", confirmPasswordValue, 8);

    if (confirmPasswordValidator) {
        showError(confirmPassword, confirmPasswordValidator.message);
        isPasswordConfirmValid = false;
    }
    else if (confirmPasswordValue != newPassword.value.trim()) {
        showError(confirmPassword, "Les deux mot de passe ne sont pas conformes");
        isPasswordConfirmValid = false;
    }
    else
    {
        showError(confirmPassword, "");
        isPasswordConfirmValid = true;
    }
    checkFormValidity();
});


