from flask import Flask, render_template, request, redirect, url_for, flash, session
from conexion.conexion import conexion, cerrar_conexion
from werkzeug.security import generate_password_hash, check_password_hash
from forms import ProductoForm, UsuarioForm, LoginForm
from datetime import datetime
import mysql.connector  # ← Importa esto para usar Error
from flask import jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

# Inyectar "now" para usar {{ now().year }} en templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# --- Rutas existentes ---
@app.route('/')
def index():
    return render_template('index.html', title='Inicio')

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
            return redirect(url_for("productos_list"))
        else:
            flash("Correo o contraseña incorrectos", "danger")

    return render_template("usuarios/login.html", form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for('login'))

@app.route('/usuarios/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    form = UsuarioForm()

    # Cargar dinámicamente los roles y tipos de documento desde la BD
    conn = conexion()
    cur = conn.cursor(dictionary=True)
    
    cur.execute("SELECT idrol, nombre FROM rol WHERE estado = 1")
    roles = cur.fetchall()
    form.idrol.choices = [(r['idrol'], r['nombre']) for r in roles]

    cur.execute("SELECT idtipodoc, nombre FROM tipo_documento")
    tipodocs = cur.fetchall()
    form.idtipodoc.choices = [(t['idtipodoc'], t['nombre']) for t in tipodocs]

    if form.validate_on_submit():
        try:
            cur.execute("""
                INSERT INTO usuario (
                    nombres, apellidos, idtipodoc, num_documento, telefono, email,
                    direccion, password_hash, idrol
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                form.nombres.data,
                form.apellidos.data,
                form.idtipodoc.data,
                form.num_documento.data,
                form.telefono.data,
                form.email.data,
                form.direccion.data,
                generate_password_hash(form.password.data),
                form.idrol.data
            ))
            conn.commit()
            flash("Usuario registrado exitosamente.", "success")
            return redirect(url_for("index"))
        except Exception as e:
            conn.rollback()
            flash(f"Error al registrar: {e}", "danger")
        finally:
            cerrar_conexion(conn)  # ← Solo una vez aquí
    else:
        cerrar_conexion(conn)  # ← Cierra conexión si no se valida

    return render_template('usuarios/crear_usuario.html', title="Nuevo Usuario", form=form)

@app.route('/about/')
def about():
    return render_template('about.html', title='Acerca de')

@app.route('/contact/')
def contact():
    return render_template('contact.html', title='Contactos')

# ---- Productos ----
# Listar / Buscar
@app.route('/productos')
def productos_list():
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
    return render_template('productos/productos_list.html', title='Productos', productos=productos, q=q)

# Crear producto
@app.route('/productos/nuevo', methods=['GET', 'POST'])
def crear_producto():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))

    form = ProductoForm()

    # Cargar categorías
    conn = conexion()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT idcategoria, nombre FROM categoria WHERE estado = 1 ORDER BY nombre")
        categorias = cur.fetchall()
        
        # ✅ Las opciones son tuplas (str, str) — pero idcategoria es INT en DB
        # Convertimos idcategoria a string para que funcione con coerce=str
        form.idcategoria.choices = [('', 'Selecciona una categoría')] + \
            [(str(cat['idcategoria']), cat['nombre']) for cat in categorias]  # ← ¡IMPORTANTE! str(idcategoria)

    except Exception as e:
        flash(f"Error al cargar categorías: {str(e)}", "danger")
    finally:
        cerrar_conexion(conn)

    if form.validate_on_submit():
        # ✅ VALIDACIÓN MANUAL: ¿se eligió categoría?
        if not form.idcategoria.data or form.idcategoria.data == '':
            flash("Por favor, selecciona una categoría.", "danger")
            return render_template('productos/formulario.html', title='Nuevo producto', form=form, modo='crear')

        # ✅ CONVERSIÓN MANUAL A ENTERO — ¡AHORA ES SEGURA!
        try:
            idcategoria_int = int(form.idcategoria.data)  # ← Aquí sí es seguro
        except (ValueError, TypeError):
            flash("Categoría inválida.", "danger")
            return render_template('productos/nuevo.html', title='Nuevo producto', form=form, modo='crear')

        # ✅ ¡Ahora puedes usar idcategoria_int como entero!
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
                idcategoria_int,   # ✅ Entero seguro
                form.stock.data,
                float(form.precio_venta.data)
            ))
            conn.commit()
            flash('Producto agregado correctamente.', 'success')
            return redirect(url_for('productos_list'))
        except Exception as e:
            conn.rollback()
            if 'Duplicate entry' in str(e) and 'codigo' in str(e).lower():
                form.codigo.errors.append(f'El código "{form.codigo.data}" ya existe. Por favor, use uno diferente.')
            elif 'Duplicate entry' in str(e) and 'nombre' in str(e).lower():
                form.nombre.errors.append(f'El nombre "{form.nombre.data}" ya existe. Por favor, use otro.')
            else:
                form.nombre.errors.append(f'No se pudo guardar: {str(e)}')
        finally:
            cerrar_conexion(conn)

    return render_template('productos/nuevo.html', title='Nuevo producto', form=form, modo='crear')


# Editar producto existente
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

    # Cargar categorías para el select
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
            return redirect(url_for('productos_list'))
        except Exception as e:
            conn.rollback()
            form.nombre.errors.append(f'Error al actualizar el producto: {str(e)}')
        finally:
            cerrar_conexion(conn)

    return render_template('productos/actualizar.html', title='Editar producto', form=form, modo='editar', pid=pid)

# Eliminar producto
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
    return redirect(url_for('productos_list'))

# --- API para Categorías ---

# Crear categoría (POST)
@app.route('/categoria', methods=['POST'])
def crear_categoria():
    try:
        data = request.get_json(silent=True)  # ← silent=True evita crash si no es JSON
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
        INSERT INTO categoria (nombre, descripcion, usuario_modifico)
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
        return jsonify({'error': 'Error al conectar o insertar en la base de datos: ' + str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

# Actualizar categoría (PUT)
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

        # Verificar que la categoría existe
        cursor.execute("SELECT * FROM categoria WHERE idcategoria = %s", (idcategoria,))
        categoria = cursor.fetchone()
        if not categoria:
            return jsonify({'error': 'Categoría no encontrada'}), 404

        # Construir actualización dinámica
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
        valores.append(idcategoria)  # Para el WHERE

        sql = f"UPDATE categoria SET {', '.join(campos)} WHERE idcategoria = %s"
        cursor.execute(sql, tuple(valores))
        conn.commit()

        return jsonify({'mensaje': 'Categoría actualizada correctamente'}), 200

    except mysql.connector.IntegrityError as e:
        if "Duplicate entry" in str(e):
            return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 409
        return jsonify({'error': 'Error de integridad: ' + str(e)}), 400

    except Exception as e:
        return jsonify({'error': 'Error al actualizar la categoría: ' + str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)