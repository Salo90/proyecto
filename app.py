from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from conexion.conexion import conexion, cerrar_conexion
from werkzeug.security import generate_password_hash, check_password_hash
from forms import ProductoForm, UsuarioForm, LoginForm
from flask_login import LoginManager, UserMixin, login_user, current_user
from datetime import datetime
import mysql.connector
import threading
import time
from flask_socketio import SocketIO, emit
from forms import RolForm

# CONFIGURACIÓN DE LA APP
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Inyectar "now" para usar {{ now().year }} en templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# ¡ESTO ES CLAVE!
login_manager = LoginManager()
login_manager.init_app(app)  # ← SIN ESTO, current_user NO EXISTE
login_manager.login_view = 'login'

# FUNCIONES GLOBALES
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
# Cargar usuario (obligatorio para Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        conn = None
        try:
            conn = conexion()
            cursor = conn.cursor(dictionary=True)

            # Buscamos el usuario por email
            cursor.execute("""
                SELECT u.*, r.nombre AS rol_nombre 
                FROM usuario u 
                INNER JOIN rol r ON u.idrol = r.idrol 
                WHERE u.email = %s 
            """, (form.email.data,))

            usuario = cursor.fetchone()

            # Validar: usuario existe, contraseña correcta Y estado = 1 (activo)
            if usuario:
                if usuario['estado'] == 0:
                    # Usuario deshabilitado
                    flash("Tu cuenta está deshabilitada. Contacta al administrador.", "warning")
                elif check_password_hash(usuario['password_hash'], form.password.data):
                    # Todo correcto: iniciar sesión
                    session['usuario_id'] = usuario['idusuario']
                    session['usuario_email'] = usuario['email']
                    session['usuario_rol'] = usuario['rol_nombre']
                    session['rol_id'] = usuario['idrol']

                    # En lugar de:
                    # return redirect(url_for("dashboard"))

                    # Haz:
                    flash(f"Bienvenido ...", "success")
                    return render_template("usuarios/login.html", form=form)
                else:
                    # Contraseña incorrecta
                    flash("Correo o contraseña incorrectos", "danger")
            else:
                # Usuario no encontrado
                flash("Correo o contraseña incorrectos", "danger")

        except Exception as e:
            app.logger.error(f"Error en login: {e}")
            flash("Ocurrió un error. Inténtalo más tarde.", "danger")
        finally:
            if conn:
                cerrar_conexion(conn)

    return render_template("usuarios/login.html", form=form)

@app.route('/logout')
def logout():
    session.clear()
    #flash("Has cerrado sesión correctamente.")
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

        # Comentado temporalmente hasta crear tabla 'creditos'
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
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if session.get('usuario_rol') != 'Administrador':
        flash("No tienes permisos para acceder a Usuarios", "danger")
        return redirect(url_for('dashboard'))

    conn = conexion()
    cursor = conn.cursor(dictionary=True)

    # JOIN con tabla rol + manejo de estado
    cursor.execute("""
        SELECT 
            u.idusuario,
            CONCAT(u.nombres, ' ', u.apellidos) AS nombre_completo,  -- Nombre completo
            u.email,
            COALESCE(r.nombre, 'Sin rol') AS rol,                   -- Rol (o "Sin rol" si no tiene)
            CASE 
                WHEN u.estado = 1 THEN 'Activo'
                ELSE 'Inactivo'
            END AS estado                                       -- Estado como texto
        FROM usuario u
        LEFT JOIN rol r ON u.idrol = r.idrol
    """)
    
    usuarios = cursor.fetchall()
    cerrar_conexion(conn)
    return render_template("usuarios/listaUsuario.html", usuarios=usuarios)

from flask import session, flash, redirect, url_for, render_template
from werkzeug.security import generate_password_hash

@app.route('/usuarios/crear', methods=['GET', 'POST'])
def crearUsuario():
    # Verificar autenticación y autorización
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))
    
    if session.get('usuario_rol') != 'Administrador':
        flash("No tienes permisos para crear usuarios.", "danger")
        return redirect(url_for('dashboard'))

    form = UsuarioForm()

    # ===== Cargar catálogos =====
    conn = None
    try:
        conn = conexion()
        cur = conn.cursor(dictionary=True)
        
        # Cargar roles
        cur.execute("SELECT idrol, nombre FROM rol WHERE estado = 1 ORDER BY nombre")
        roles = cur.fetchall()
        form.idrol.choices = [('', 'Selecciona un rol')] + [(str(r['idrol']), r['nombre']) for r in roles]
        
        # Cargar tipos de documento
        cur.execute("SELECT idtipodoc, nombre FROM tipo_documento ORDER BY nombre")
        docs = cur.fetchall()
        form.idtipodoc.choices = [('', 'Selecciona')] + [(str(t['idtipodoc']), t['nombre']) for t in docs]
        
    except Exception as e:
        app.logger.error(f"Error al cargar catálogos: {e}")
        flash("Error al cargar los datos necesarios.", "danger")
        return redirect(url_for('listaUsuario'))
    finally:
        if conn:
            cerrar_conexion(conn)

    # ===== Procesar formulario =====
    if form.validate_on_submit():
        # Validar que los selects tengan valor
        if not form.idrol.data or form.idrol.data == '':
            flash("Por favor, selecciona un rol.", "danger")
            return render_template("usuarios/crearUsuario.html", title="Nuevo Usuario", form=form)
            
        if not form.idtipodoc.data or form.idtipodoc.data == '':
            flash("Por favor, selecciona un tipo de documento.", "danger")
            return render_template("usuarios/crearUsuario.html", title="Nuevo Usuario", form=form)

        # Validar unicidad del email Y del número de documento
        conn = None
        try:
            conn = conexion()
            cur = conn.cursor()
            
            # Validar email duplicado
            cur.execute("SELECT idusuario FROM usuario WHERE email = %s", (form.email.data.lower(),))
            if cur.fetchone():
                flash("El correo electrónico ya está registrado.", "warning")
                return render_template("usuarios/crearUsuario.html", title="Nuevo Usuario", form=form)

            # VALIDAR CÉDULA (NUM_DOCUMENTO) DUPLICADA
            cur.execute("""
                SELECT idusuario 
                FROM usuario 
                WHERE num_documento = %s AND idtipodoc = %s
            """, (form.num_documento.data.strip(), int(form.idtipodoc.data)))
            
            if cur.fetchone():
                flash("El número de documento ya está registrado con este tipo de documento.", "warning")
                return render_template("usuarios/crearUsuario.html", title="Nuevo Usuario", form=form)

            # Registrar usuario
            cur.execute("""
                INSERT INTO usuario (
                    nombres, apellidos, idtipodoc, num_documento, telefono, email,
                    direccion, password_hash, idrol, estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                form.nombres.data.strip(),
                form.apellidos.data.strip(),
                int(form.idtipodoc.data),
                form.num_documento.data.strip(),
                form.telefono.data.strip(),
                form.email.data.lower(),
                form.direccion.data.strip(),
                generate_password_hash(form.password.data),
                int(form.idrol.data),
                1  # estado activo
            ))
            conn.commit()
            flash("Usuario registrado exitosamente.", "success")
            return redirect(url_for('listaUsuario'))
            
        except Exception as e:
            if conn:
                conn.rollback()
            app.logger.error(f"Error al registrar usuario: {e}")
            flash("Ocurrió un error al registrar el usuario. Intente nuevamente.", "danger")
        finally:
            if conn:
                cerrar_conexion(conn)
    
    # Renderizar formulario
    return render_template("usuarios/crearUsuario.html", title="Nuevo Usuario", form=form)

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def actualizarUsuario(id):
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
        nombre_completo = request.form['nombre']  # viene del input "Usuario"
        idrol = request.form.get('idrol', 2)
        estado = request.form.get('estado', 1)

        # separar nombre completo
        partes = nombre_completo.strip().split(" ", 1)
        nombres = partes[0]
        apellidos = partes[1] if len(partes) > 1 else ""

        if password:  # Solo actualizar contraseña si se proporciona
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(password)
            cursor.execute("""
                UPDATE usuario SET 
                    email=%s, password_hash=%s, nombres=%s, apellidos=%s, idrol=%s, estado=%s 
                WHERE idusuario=%s
            """, (email, password_hash, nombres, apellidos, idrol, estado, id))
        else:
            cursor.execute("""
                UPDATE usuario SET 
                    email=%s, nombres=%s, apellidos=%s, idrol=%s, estado=%s 
                WHERE idusuario=%s
            """, (email, nombres, apellidos, idrol, estado, id))
            
        conn.commit()
        flash("Usuario actualizado correctamente", "success")
        cerrar_conexion(conn)
        return redirect(url_for('listaUsuario'))
    
    # Cargar datos del usuario para el formulario
    cursor.execute("""
        SELECT *, CONCAT(nombres, ' ', apellidos) as nombre_completo 
        FROM usuario 
        WHERE idusuario = %s
    """, (id,))
    usuario = cursor.fetchone()
    cerrar_conexion(conn)
    
    return render_template(
        'usuarios/actualizarUsuario.html',
        usuario=usuario,
        roles=roles,
        title='Editar Usuario'
    )

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
    return render_template('roles/listaRoles.html', roles=roles) 
    from forms import RolForm

@app.route('/roles/crear', methods=['GET', 'POST'])
def crearRol():
    # Verifica que el usuario esté logueado
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    form = RolForm()

    if form.validate_on_submit():
        nombre = form.nombre.data
        descripcion = form.descripcion.data
        estado = int(form.estado.data)  # Asegúrate de convertir a entero si tu DB lo necesita

        conn = conexion()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO rol (nombre, descripcion, estado) 
                VALUES (%s, %s, %s)
            """, (nombre, descripcion, estado))
            conn.commit()
            flash("Rol creado correctamente", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Ocurrió un error: {e}", "danger")
        finally:
            cursor.close()
            cerrar_conexion(conn)

        return redirect(url_for('listaRoles'))

    # Renderiza el formulario en GET o si la validación falla
    return render_template('roles/crearRol.html', title='Crear Rol', form=form)

@app.route('/roles/editar/<int:idrol>', methods=['GET', 'POST'])
def actualizarRol(idrol):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    form = RolForm()

    conn = conexion()
    cursor = conn.cursor(dictionary=True)

    # Obtener datos del rol existente
    cursor.execute("SELECT * FROM rol WHERE idrol = %s", (idrol,))
    rol = cursor.fetchone()

    if not rol:
        cerrar_conexion(conn)
        flash("El rol no existe", "warning")
        return redirect(url_for('listaRoles'))

    # Rellenar el formulario con los datos existentes en GET
    if request.method == 'GET':
        form.nombre.data = rol['nombre']
        form.descripcion.data = rol['descripcion']
        form.estado.data = str(rol['estado'])  # SelectField necesita str

    if form.validate_on_submit():
        nombre = form.nombre.data
        descripcion = form.descripcion.data
        estado = int(form.estado.data)

        try:
            cursor.execute("""
                UPDATE rol
                SET nombre=%s, descripcion=%s, estado=%s
                WHERE idrol=%s
            """, (nombre, descripcion, estado, idrol))
            conn.commit()
            flash("Rol actualizado correctamente", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Ocurrió un error: {e}", "danger")
        finally:
            cursor.close()
            cerrar_conexion(conn)

        return redirect(url_for('listaRoles'))

    cursor.close()
    cerrar_conexion(conn)
    return render_template('roles/actualizarRol.html', title='Actualizar Rol', form=form, idrol=idrol)

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
    # Verificar inicio de sesión
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip()
    conn = conexion()
    cur = conn.cursor(dictionary=True)
    
    if q:
        cur.execute("""
            SELECT 
                p.idproducto, p.codigo, p.nombre, p.descripcion, 
                c.nombre AS categoria, p.stock, p.precio_venta 
            FROM producto p
            LEFT JOIN categoria c ON p.idcategoria = c.idcategoria
            WHERE p.nombre LIKE %s
        """, (f"%{q}%",))
    else:
        cur.execute("""
            SELECT 
                p.idproducto, p.codigo, p.nombre, p.descripcion, 
                c.nombre AS categoria, p.stock, p.precio_venta 
            FROM producto p
            LEFT JOIN categoria c ON p.idcategoria = c.idcategoria
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

    # Inicializar el formulario con los datos actuales del producto, incluyendo 'estado'
    form = ProductoForm(data={
        'codigo': prod['codigo'],
        'nombre': prod['nombre'],
        'descripcion': prod['descripcion'],
        'idcategoria': prod['idcategoria'],
        'stock': prod['stock'],
        'precio_venta': prod['precio_venta'],
        'estado': str(prod['estado'])  # ← Asegúrate de convertir a string si tus choices son strings
    })
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT idcategoria, nombre FROM categoria WHERE estado = 1 ORDER BY nombre")
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
                SET codigo = %s, nombre = %s, descripcion = %s, idcategoria = %s, 
                    stock = %s, precio_venta = %s, estado = %s
                WHERE idproducto = %s
            """, (
                form.codigo.data,
                form.nombre.data,
                form.descripcion.data,
                form.idcategoria.data,
                form.stock.data,
                float(form.precio_venta.data),
                int(form.estado.data),  # ← Guardar como entero (1 o 0)
                pid
            ))
            conn.commit()
            flash('Producto actualizado correctamente.', 'success')
            return redirect(url_for('listaProducto'))
        except Exception as e:
            conn.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
        finally:
            cerrar_conexion(conn)

    return render_template('productos/actualizar.html', title='Editar producto', form=form, modo='editar', pid=pid)

@app.route('/productos/<int:pid>/eliminar', methods=['POST'])
def eliminar_producto(pid):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
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