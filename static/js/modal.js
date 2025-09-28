    //Script separado: pasamos la categoría como variable JS -->
        
    document.addEventListener('DOMContentLoaded', function () {
        var modalElement = document.getElementById('flashModal');
        var modal = new bootstrap.Modal(modalElement);
        modal.show();

        // Pasamos la categoría desde Jinja a JS
        var category = "{{ category }}";

        if (category === "success") {
            setTimeout(function() {
            modal.hide();
            window.location.href = "{{ url_for('dashboard') }}";
            }, 2000);
        }
    });
     