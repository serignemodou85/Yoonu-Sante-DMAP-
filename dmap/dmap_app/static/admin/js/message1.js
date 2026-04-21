document.querySelectorAll('.confirm-action').forEach(button => {
    button.addEventListener('click', function () {
        const form = this.closest('form');
        const message = form.getAttribute('data-message');

        Swal.fire({
            title: "Voulez vous valider cette demande ?",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Oui, confirmer',
            cancelButtonText: 'Annuler'
        }).then((result) => {
            if (result.isConfirmed) {
                form.submit();
            }
        });
    });
});