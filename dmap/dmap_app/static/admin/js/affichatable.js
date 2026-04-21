function toggleTables() {
    const tableNonValide = document.getElementById("table-non-valide");
    const tableValide = document.getElementById("table-valide");

    const filtreValide = document.getElementById("filtre-valide");

    const paginationNonValide = document.getElementById("pagination-non-valide-id");
    const paginationValide = document.getElementById("pagination-valide");

    const btnToggleText = document.getElementById("btn-toggle-text");
    const btnRetour = document.getElementById("btn-retour");

    const isShowingNonValide = tableNonValide.style.display !== "none";

    if (isShowingNonValide) {
        // Afficher table des comptes valides
        tableNonValide.style.display = "none";
        paginationNonValide.style.display = "none";

        tableValide.style.display = "";
        filtreValide.style.display = "";
        paginationValide.style.display = "";

        btnToggleText.innerHTML = '<i class="fa fa-folder-open"></i> Compte Non Validé';
        btnRetour.style.display = "";
    } else {
        // Afficher table des comptes non validés
        tableNonValide.style.display = "";
        paginationNonValide.style.display = "";

        tableValide.style.display = "none";
        filtreValide.style.display = "none";
        paginationValide.style.display = "none";

        btnToggleText.innerHTML = '<i class="fa fa-folder"></i> Compte Valide';
        btnRetour.style.display = "none";
    }
}
