# app.py - Dashboard GesNet - Organizado y corregido
# Autor: [Tu nombre]
# Fecha: 2025

# ================================
# IMPORTS
# ================================
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from conexion.conexion import conexion, cerrar_conexion
from werkzeug.security import generate_password_hash, check_password_hash
from forms import ProductoForm, UsuarioForm, LoginForm
from datetime import datetime
import mysql.connector
import threading
import time
from flask_socketio import SocketIO, emit

# ================================
# CONFIGURACIÓN DE LA APP
# ================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Inyectar "now" para usar {{ now().year }} en templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# ================================
# FUNCIONES GLOBALES
# ================================

def update_dashboard_data():
    """Actualiza los datos del dashboard en tiempo real cada 10 segundos."""
    while True:
        time.sleep(10)
        with app.app_context():
            data = {
                "pen_en_caja": 0.0,
                "compras_mes": 932.23,
                "ventas_dia": 0.0,
                "inversion_stock": 24999286090.50,
                "proveedores": 6,
                "marcas": 19,
                "presentaciones": 12,
                "productos_ingresados": 90,
                "perecederos": 62,
                "vencen_30_dias": 0,
                "clientes": 41,
                "creditos_pendientes": 21
            }
            socketio.emit('update_dashboard', data)

# Iniciar hilo de actualización en segundo plano
threading.Thread(target=update_dashboard_data, daemon=True).start()

# ================================
# RUTAS PRINCIPALES
# ================================

@app.route('/')
def index():
    return render_template('index.html', title='Inicio')

@app.route('/about/')
def about():
    return render_template('about.html', title='Acerca de')

@app.route('/contact/')
def contact():
    return render_template('contact.html', title='Contactos')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        conn = conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuario WHERE email = %s", (form.email.data,))
        usuario = cursor.fetchone()
        cerrar_conexion(conn)

        if usuario and check_password_hash(usuario['password_hash'], form.password.data):
            session['usuario_id'] = usuario['idusuario']
            session['usuario_email'] = usuario['email']
            flash("Inicio de sesión exitoso", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Correo o contraseña incorrectos", "danger")

    return render_template("usuarios/login.html", form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for('login'))

# ================================
# RUTA DEL DASHBOARD (API)
# ================================

@app.route('/panel')
def panel():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para acceder al panel.", "warning")
        return redirect(url_for('login'))
    return render_template('panel.html', title='Panel de Control')

@app.route('/dashboard')
def dashboard():
    # Verificar si el usuario está autenticado
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para acceder al dashboard.", "warning")
        return redirect(url_for('login'))

    # Renderizar la plantilla del dashboard
    return render_template('panel.html', title='Dashboard')

@app.route('/api/dashboard')
def dashboard_api():
    conn = conexion()
    if not conn:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Datos de resumen
        cursor.execute("SELECT SUM(stock) AS total_stock FROM producto WHERE stock < 10")
        perecederos = cursor.fetchone()['total_stock']

        cursor.execute("SELECT COUNT(*) AS count FROM producto")
        productos_ingresados = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) AS count FROM cliente")
        clientes = cursor.fetchone()['count']

        # ⚠️ Comentado temporalmente hasta crear tabla 'creditos'
        # cursor.execute("SELECT COUNT(*) AS count FROM creditos WHERE estado = 'pendiente'")
        # creditos_pendientes = cursor.fetchone()['count']

        # Últimos productos con categoría
        cursor.execute("""
            SELECT 
                p.codigo,
                p.nombre,
                p.descripcion,
                p.precio_venta,
                COALESCE(c.nombre, 'Sin categoría') AS categoria
            FROM producto p
            LEFT JOIN categoria c ON p.idcategoria = c.idcategoria   -- ← ¡CORREGIDO! Tabla = categorias
            ORDER BY p.idproducto DESC
            LIMIT 10
        """)
        ultimos_productos = cursor.fetchall()

        conn.close()

        return jsonify({
            'perecederos': perecederos or 0,
            'productos_ingresados': productos_ingresados or 0,
            'clientes': clientes or 0,
            # 'creditos_pendientes': creditos_pendientes or 0,
            'ultimos_productos': ultimos_productos
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print('Cliente conectado al SocketIO')

# ================================
# RUTAS DE USUARIOS
# ================================
@app.route('/usuarios')
def listaUsuario():
    """Lista todos los usuarios del sistema."""
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))

    conn = conexion()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            u.idusuario,
            u.email,
            u.estado,
            r.nombre as rol_nombre,
            r.idrol as rol_id,
            u.nombres,
            u.apellidos
        FROM usuario u
        LEFT JOIN rol r ON u.idrol = r.idrol
        ORDER BY u.email ASC
    """)
    usuarios = cursor.fetchall()
    cerrar_conexion(conn)

    return render_template('usuarios/listaUsuario.html', usuarios=usuarios, title='Usuarios')

@app.route('/usuarios/crear', methods=['GET', 'POST'])
def crearUsuario():
    form = UsuarioForm()

    # ----- Cargar catálogos -----
    try:
        conn = conexion()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT idrol, nombre FROM rol WHERE estado = 1")
        form.idrol.choices = [(r['idrol'], r['nombre']) for r in cur.fetchall()]

        cur.execute("SELECT idtipodoc, nombre FROM tipo_documento")
        form.idtipodoc.choices = [(t['idtipodoc'], t['nombre']) for t in cur.fetchall()]

    except Exception as e:
        flash("Error al cargar datos de referencia", "danger")
        app.logger.error(f"Error cargando roles/tipo docs: {e}")
    finally:
        cerrar_conexion(conn)

    # ----- Procesar formulario -----
    if form.validate_on_submit():
        try:
            conn = conexion()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO usuario (
                    nombres, apellidos, idtipodoc, num_documento, telefono, email,
                    direccion, password_hash, idrol
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                form.nombres.data.strip(),
                form.apellidos.data.strip(),
                form.idtipodoc.data,
                form.num_documento.data.strip(),
                form.telefono.data.strip(),
                form.email.data.lower(),
                form.direccion.data.strip(),
                generate_password_hash(form.password.data),
                form.idrol.data
            ))
            conn.commit()

            flash("Usuario registrado exitosamente ✅", "success")
            return redirect(url_for("lista_usuarios"))

        except Exception as e:
            conn.rollback()
            flash("Ocurrió un error al registrar el usuario.", "danger")
            app.logger.error(f"Error al registrar usuario: {e}")
        finally:
            cerrar_conexion(conn)

    return render_template(
        "usuarios/crearUsuario.html",
        title="Nuevo Usuario",
        form=form
    )

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conexion()
    cursor = conn.cursor(dictionary=True)
    
    # Obtener empleados y roles
    cursor.execute("SELECT CONCAT(nombres, ' ', apellidos) as nombre_completo FROM usuario WHERE estado = 1")
    empleados = cursor.fetchall()
    cursor.execute("SELECT idrol, nombre FROM rol WHERE estado = 1")
    roles = cursor.fetchall()
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form.get('password', '')
        idrol = request.form.get('idrol', 2)
        estado = request.form.get('estado', 1)
        
        if password:  # Solo actualizar contraseña si se proporciona
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(password)
            cursor.execute("""
                UPDATE usuario SET 
                    email=%s, password_hash=%s, idrol=%s, estado=%s 
                WHERE idusuario=%s
            """, (email, password_hash, idrol, estado, id))
        else:
            cursor.execute("""
                UPDATE usuario SET 
                    email=%s, idrol=%s, estado=%s 
                WHERE idusuario=%s
            """, (email, idrol, estado, id))
            
        conn.commit()
        flash("Usuario actualizado correctamente", "success")
        cerrar_conexion(conn)
        return redirect(url_for('listaUsuario'))
    
    cursor.execute("SELECT * FROM usuario WHERE idusuario = %s", (id,))
    usuario = cursor.fetchone()
    cerrar_conexion(conn)
    
    return render_template('usuarios/editar.html', usuario=usuario, empleados=empleados, roles=roles, title='Editar Usuario')

@app.route('/usuarios/eliminar/<int:id>')
def eliminar_usuario(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuario WHERE idusuario = %s", (id,))
    conn.commit()
    cerrar_conexion(conn)
    
    flash("Usuario eliminado correctamente", "success")
    return redirect(url_for('listaUsuario'))

# ================================
# RUTAS DE empleado
# ================================

@app.route('/empleados')
def listaEmpleados():
    conn = conexion()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM empleado WHERE estado = 1")
    empleados = cursor.fetchall()
    cerrar_conexion(conn)
    return render_template('empleados/lista.html', empleados=empleados, title="Lista de Empleados")

# ================================
# RUTAS DE roles
# ================================

@app.route('/roles')
def listaRoles():
    conn = conexion()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT idrol, nombre, descripcion, estado 
        FROM rol 
        ORDER BY nombre ASC
    """)
    roles = cursor.fetchall()
    cerrar_conexion(conn)
    return render_template('usuarios/roles.html', roles=roles)

@app.route('/roles/crear', methods=['GET', 'POST'])
def crear_rol():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form.get('descripcion', '')
        estado = request.form.get('estado', 1)
        
        conn = conexion()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rol (nombre, descripcion, estado) 
            VALUES (%s, %s, %s)
        """, (nombre, descripcion, estado))
        conn.commit()
        cerrar_conexion(conn)
        
        flash("Rol creado correctamente", "success")
        return redirect(url_for('listaRoles'))
    
    return render_template('usuarios/crear_rol.html', title='Crear Rol')

@app.route('/roles/editar/<int:id>', methods=['GET', 'POST'])
def editar_rol(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conexion()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form.get('descripcion', '')
        estado = request.form.get('estado', 1)
        
        cursor.execute("""
            UPDATE rol SET nombre=%s, descripcion=%s, estado=%s WHERE idrol=%s
        """, (nombre, descripcion, estado, id))
        conn.commit()
        flash("Rol actualizado correctamente", "success")
        cerrar_conexion(conn)
        return redirect(url_for('listaRoles'))
    
    cursor.execute("SELECT * FROM rol WHERE idrol = %s", (id,))
    rol = cursor.fetchone()
    cerrar_conexion(conn)
    
    return render_template('usuarios/editar_rol.html', rol=rol, title='Editar Rol')

@app.route('/roles/eliminar/<int:id>')
def eliminar_rol(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rol WHERE idrol = %s", (id,))
    conn.commit()
    cerrar_conexion(conn)
    
    flash("Rol eliminado correctamente", "success")
    return redirect(url_for('listaRoles'))

# ================================
# RUTAS DE PRODUCTOS
# ================================

@app.route('/productos')
def listaProducto():
    q = request.args.get('q', '').strip()
    conn = conexion()
    cur = conn.cursor(dictionary=True)
    
    if q:
        cur.execute("""
            SELECT 
                p.idproducto, p.codigo, p.nombre, p.descripcion, 
                c.nombre AS categoria, p.stock, p.precio_venta 
            FROM producto p
            LEFT JOIN categoria c ON p.idcategoria = c.idcategoria   -- ← ¡CORREGIDO!
            WHERE p.nombre LIKE %s
        """, (f"%{q}%",))
    else:
        cur.execute("""
            SELECT 
                p.idproducto, p.codigo, p.nombre, p.descripcion, 
                c.nombre AS categoria, p.stock, p.precio_venta 
            FROM producto p
            LEFT JOIN categoria c ON p.idcategoria = c.idcategoria   -- ← ¡CORREGIDO!
        """)
    
    productos = cur.fetchall()
    cerrar_conexion(conn)
    return render_template('productos/listaProducto.html', title='Productos', productos=productos, q=q)

@app.route('/productos/nuevo', methods=['GET', 'POST'])
def crear_producto():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))

    form = ProductoForm()
    conn = conexion()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT idcategoria, nombre FROM categoria WHERE estado = 1 ORDER BY nombre")  # ← ¡CORREGIDO!
        categorias = cur.fetchall()
        form.idcategoria.choices = [('', 'Selecciona una categoría')] + \
            [(str(cat['idcategoria']), cat['nombre']) for cat in categorias]
    except Exception as e:
        flash(f"Error al cargar categorías: {str(e)}", "danger")
    finally:
        cerrar_conexion(conn)

    if form.validate_on_submit():
        if not form.idcategoria.data or form.idcategoria.data == '':
            flash("Por favor, selecciona una categoría.", "danger")
            return render_template('productos/nuevo.html', title='Nuevo producto', form=form, modo='crear')

        try:
            idcategoria_int = int(form.idcategoria.data)
        except (ValueError, TypeError):
            flash("Categoría inválida.", "danger")
            return render_template('productos/nuevo.html', title='Nuevo producto', form=form, modo='crear')

        conn = conexion()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO producto 
                (codigo, nombre, descripcion, idcategoria, stock, precio_venta) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                form.codigo.data,
                form.nombre.data,
                form.descripcion.data,
                idcategoria_int,
                form.stock.data,
                float(form.precio_venta.data)
            ))
            conn.commit()
            flash('Producto agregado correctamente.', 'success')
            return redirect(url_for('listaProducto'))
        except Exception as e:
            conn.rollback()
            if 'Duplicate entry' in str(e) and 'codigo' in str(e).lower():
                form.codigo.errors.append(f'El código "{form.codigo.data}" ya existe.')
            elif 'Duplicate entry' in str(e) and 'nombre' in str(e).lower():
                form.nombre.errors.append(f'El nombre "{form.nombre.data}" ya existe.')
            else:
                form.nombre.errors.append(f'No se pudo guardar: {str(e)}')
        finally:
            cerrar_conexion(conn)
    return render_template('productos/nuevo.html', title='Nuevo producto', form=form, modo='crear')

@app.route('/productos/<int:pid>/editar', methods=['GET', 'POST'])
def editar_producto(pid):
    conn = conexion()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM producto WHERE idproducto = %s", (pid,))
    prod = cursor.fetchone()
    if not prod:
        cerrar_conexion(conn)
        return "Producto no encontrado", 404

    form = ProductoForm(data={
        'codigo': prod['codigo'],
        'nombre': prod['nombre'],
        'descripcion': prod['descripcion'],
        'idcategoria': prod['idcategoria'],
        'stock': prod['stock'],
        'precio_venta': prod['precio_venta'],
    })
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT idcategoria, nombre FROM categoria WHERE estado = 1 ORDER BY nombre")  # ← ¡CORREGIDO!
        categorias = cur.fetchall()
        form.idcategoria.choices = [('', 'Selecciona una categoría')] + \
            [(cat['idcategoria'], cat['nombre']) for cat in categorias]
    except Exception as e:
        flash(f"Error al cargar categorías: {str(e)}", "danger")
    finally:
        cerrar_conexion(conn)

    if form.validate_on_submit():
        conn = conexion()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE producto
                SET codigo = %s, nombre = %s, descripcion = %s, idcategoria = %s, stock = %s, precio_venta = %s
                WHERE idproducto = %s
            """, (
                form.codigo.data,
                form.nombre.data,
                form.descripcion.data,
                form.idcategoria.data,
                form.stock.data,
                float(form.precio_venta.data),
                pid
            ))
            conn.commit()
            flash('Producto actualizado correctamente.', 'success')
            return redirect(url_for('listaProducto'))
        except Exception as e:
            conn.rollback()
            form.nombre.errors.append(f'Error al actualizar: {str(e)}')
        finally:
            cerrar_conexion(conn)

    return render_template('productos/actualizar.html', title='Editar producto', form=form, modo='editar', pid=pid)

@app.route('/productos/<int:pid>/eliminar', methods=['POST'])
def eliminar_producto(pid):
    conn = conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM producto WHERE idproducto = %s", (pid,))
    if cursor.rowcount > 0:
        conn.commit()
        flash('Producto eliminado correctamente.', 'success')
    else:
        flash('Producto no encontrado.', 'warning')
    cerrar_conexion(conn)
    return redirect(url_for('listaProducto'))

# ================================
# API PARA CATEGORÍAS
# ================================

@app.route('/categoria', methods=['POST'])
def crear_categoria():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Datos en formato JSON requeridos'}), 400

        nombre = data.get('nombre')
        descripcion = data.get('descripcion')
        usuario_modifico = data.get('usuario_modifico')

        if not nombre or usuario_modifico is None:
            return jsonify({'error': 'Faltan campos requeridos: nombre o usuario_modifico'}), 400

        conn = conexion()
        cursor = conn.cursor()

        sql = """
        INSERT INTO categoria (nombre, descripcion, usuario_modifico)   -- ← ¡CORREGIDO!
        VALUES (%s, %s, %s)
        """
        valores = (nombre, descripcion, usuario_modifico)

        cursor.execute(sql, valores)
        conn.commit()

        return jsonify({'mensaje': 'Categoría creada correctamente'}), 201

    except mysql.connector.IntegrityError as e:
        if "Duplicate entry" in str(e):
            return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 409
        return jsonify({'error': 'Error de integridad: ' + str(e)}), 400

    except Exception as e:
        return jsonify({'error': 'Error al conectar o insertar: ' + str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

@app.route('/categoria/<int:idcategoria>', methods=['PUT'])
def actualizar_categoria(idcategoria):
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Datos en formato JSON requeridos'}), 400

        nombre = data.get('nombre')
        descripcion = data.get('descripcion')
        estado = data.get('estado')
        usuario_modifico = data.get('usuario_modifico')

        if usuario_modifico is None:
            return jsonify({'error': 'El campo usuario_modifico es requerido'}), 400

        conn = conexion()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM categoria WHERE idcategoria = %s", (idcategoria,))  # ← ¡CORREGIDO!
        categoria = cursor.fetchone()
        if not categoria:
            return jsonify({'error': 'Categoría no encontrada'}), 404

        campos = []
        valores = []

        if nombre is not None:
            campos.append("nombre = %s")
            valores.append(nombre)
        if descripcion is not None:
            campos.append("descripcion = %s")
            valores.append(descripcion)
        if estado is not None:
            if estado not in [0, 1, True, False]:
                return jsonify({'error': 'El estado debe ser 0 o 1'}), 400
            campos.append("estado = %s")
            valores.append(int(estado))

        campos.append("usuario_modifico = %s")
        valores.append(usuario_modifico)
        valores.append(idcategoria)

        sql = f"UPDATE categoria SET {', '.join(campos)} WHERE idcategoria = %s"  # ← ¡CORREGIDO!
        cursor.execute(sql, tuple(valores))
        conn.commit()

        return jsonify({'mensaje': 'Categoría actualizada correctamente'}), 200

    except mysql.connector.IntegrityError as e:
        if "Duplicate entry" in str(e):
            return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 409
        return jsonify({'error': 'Error de integridad: ' + str(e)}), 400

    except Exception as e:
        return jsonify({'error': 'Error al actualizar: ' + str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

# ================================
# EJECUCIÓN
# ================================

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)