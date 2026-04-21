const emailInputReinit = document.getElementById("confirmEmailreinit");
const frmConfirmMail = document.getElementById("reinitConfirmMailForm");
const btnSubmit = frmConfirmMail.querySelector("button[type='submit']");

let isEmailConfirmValid = false;


// Désactive le bouton de soumission par defaut
btnSubmit.disabled = false;

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

function checkFormValidity()
{
    if (isEmailConfirmValid) {
        btnSubmit.removeAttribute("disabled");
    }
}

// Validation du champ email à la saisie
emailInputReinit.addEventListener("input", () => {
    const email = emailInputReinit.value.trim();
    const emailValidator = Validator.emailValidator("L'email", email);

    if (emailValidator) {
        showError(emailInputReinit, emailValidator.message);
        isEmailConfirmValid = false;
    }
    else
    {
        showError(emailInputReinit, "");
        isEmailConfirmValid = true;
    }
    checkFormValidity();
});
