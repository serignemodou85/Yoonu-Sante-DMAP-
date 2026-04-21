// Recupération des éléments
const tableListeUser = document.getElementById("table-liste-user");
const tableCorbeilleUser = document.getElementById("table-corbeille-user");

const btnShowListeUser = document.getElementById("btn-show-liste-users");
const btnShowCorbeilleUser = document.getElementById("btn-show-corbeille-users");


tableCorbeilleUser.setAttribute("hidden", "hidden");
btnShowListeUser.setAttribute("hidden", "hidden");


btnShowCorbeilleUser.addEventListener("click", function (event) {
    this.setAttribute("hidden", "hidden"); //masquer
    btnShowListeUser.removeAttribute("hidden"); //afficher

    tableListeUser.setAttribute("hidden", "hidden");
    tableCorbeilleUser.removeAttribute("hidden");
});


btnShowListeUser.addEventListener("click", function (event) {
    this.setAttribute("hidden", "hidden");
    btnShowCorbeilleUser.removeAttribute("hidden");

    tableListeUser.removeAttribute("hidden");
    tableCorbeilleUser.setAttribute("hidden", "hidden");
});