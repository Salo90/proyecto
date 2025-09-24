// static/js/dashboard.js
$(document).ready(function () {
    // Cargar datos iniciales
    loadProductos();

    // Conexión Socket.IO
    const socket = io();

    socket.on('update_dashboard', function(data) {
        console.log("Actualizando dashboard:", data);
        // Aquí puedes actualizar tarjetas si es necesario
        // Por ahora solo carga tabla
        loadProductos();
    });

    function loadProductos() {
        $.get("/api/dashboard", function(data) {
            let tbody = $('#productos-table');
            tbody.empty();

            data.ultimos_productos.forEach(function(producto) {
                let row = $('<tr>');

                let stockStatus = '';
                if (producto.stock === 0) {
                    stockStatus = '<span class="badge bg-danger">AGOTADO</span>';
                } else if (producto.stock <= producto.stock_minimo) {
                    stockStatus = '<span class="badge bg-warning">POR AGOTARSE</span>';
                } else if (producto.stock === producto.stock_minimo) {
                    stockStatus = '<span class="badge bg-info">EN MÍNIMO</span>';
                } else {
                    stockStatus = `<td>${producto.stock}</td>`;
                }

                row.append(
                    $('<td>').text(producto.codigo),
                    $('<td>').text(producto.nombre),
                    $('<td>').text(producto.descripcion),
                    $('<td>').text(producto.categoria),
                    $('<td>').append(stockStatus),
                    $('<td>').text(producto.precio_venta)
                );

                tbody.append(row);
            });
        }).fail(function() {
            alert("Error al cargar productos");
        });
    }
});