# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from dataclasses import dataclass
from models import db, Producto  # Ajusta según tu estructura
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import PasswordField, BooleanField
from wtforms.validators import Email


# === 1. Crear db SIN app ===
db = SQLAlchemy()

# === 2. Crear la app ===
app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-change-this-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventario.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# === 3. Registrar db con la app ===
db.init_app(app)

# === 4. Activar claves foráneas en SQLite (dentro del contexto) ===
with app.app_context():
    @event.listens_for(db.engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# ---------------------------------------------
# Modelos
# ---------------------------------------------
class Categoria(db.Model):
    __tablename__ = "categoria"
    id = db.Column("idCategoria", db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text, nullable=False)

class Producto(db.Model):
    __tablename__ = "producto"
    id = db.Column("idProducto", db.Integer, primary_key=True, autoincrement=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.idCategoria"), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False, default="")
    precio_unitario = db.Column("precioUnitario", db.Numeric(10, 2), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)

    categoria = db.relationship("Categoria", backref="productos")

class Usuario(db.Model):
    __tablename__ = "usuario"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ---------------------------------------------
# Caché en memoria
# ---------------------------------------------
@dataclass
class ProductoDTO:
    id: int
    nombre: str
    cantidad: int
    precio_unitario: float

class InventarioCache:
    def __init__(self):
        self._by_id: dict[int, ProductoDTO] = {}
        self._by_name_index: dict[str, set[int]] = {}

    def cargar(self, productos: list[Producto]):
        self._by_id.clear()
        self._by_name_index.clear()
        for p in productos:
            dto = ProductoDTO(p.id, p.nombre, int(p.cantidad), float(p.precio_unitario))
            self._by_id[p.id] = dto
            key = p.nombre.lower()
            self._by_name_index.setdefault(key, set()).add(p.id)

    def buscar_por_nombre(self, nombre: str) -> list[ProductoDTO]:
        clave = nombre.lower()
        resultados = []
        for k, ids in self._by_name_index.items():
            if clave in k:
                for pid in ids:
                    resultados.append(self._by_id[pid])
        return resultados

inventario_cache = InventarioCache()

# ---------------------------------------------
# Formularios
# ---------------------------------------------
class ProductoForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[DataRequired()])
    cantidad = IntegerField("Cantidad", validators=[DataRequired(), NumberRange(min=0)])
    precio_unitario = DecimalField(
        "Precio Unitario", 
        places=2, 
        rounding=None, 
        validators=[DataRequired(), NumberRange(min=0)]
    )
    categoria_id = SelectField("Categoría", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Guardar")

class LoginForm(FlaskForm):
    email = StringField("Correo electrónico", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    remember = BooleanField("Recordarme")
    submit = SubmitField("Iniciar sesión")

# ---------------------------------------------
# Rutas
# ---------------------------------------------
@app.route('/')
def index():
    return render_template('index.html', title='Inicio')

@app.route('/usuario/<nombre>')
def usuario(nombre):
    return f'Bienvenido, {nombre}!'

@app.route('/about/')
def about():
    return render_template('about.html', title='Acerca de')

@app.route('/contact/')
def contact():
    return render_template('contact.html', title='Contactos')

@app.route('/productos')
def productos_list():
    # Obtener el término de búsqueda
    q = request.args.get('q', '').strip()

    # Construir consulta
    query = Producto.query

    if q:
        query = query.filter(Producto.nombre.ilike(f'%{q}%'))

    productos = query.all()  # Puedes usar .paginate() si deseas paginación

    return render_template('productos_list.html', productos=productos)

@app.route("/productos/nuevo", methods=["GET", "POST"])
def productos_new_wtf():
    form = ProductoForm()
    form.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.order_by(Categoria.nombre).all()]
    
    if form.validate_on_submit():
        p = Producto(
            nombre=form.nombre.data.strip(),
            descripcion=form.descripcion.data,
            cantidad=form.cantidad.data,
            precio_unitario=form.precio_unitario.data,
            categoria_id=form.categoria_id.data
        )
        db.session.add(p)
        db.session.commit()
        flash("Producto creado correctamente.", "success")
        return redirect(url_for("productos_list"))
    
    return render_template("formulario.html", form=form, titulo="Nuevo producto")



@app.route("/productos/<int:pid>/editar", methods=["GET", "POST"])
def productos_edit(pid):
    p = Producto.query.get_or_404(pid)
    form = ProductoForm(obj=p)
    form.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.order_by(Categoria.nombre).all()]
    
    if form.validate_on_submit():
        form.populate_obj(p)
        db.session.commit()
        flash("Producto actualizado.", "success")
        return redirect(url_for("productos_list"))
    
    return render_template("formulario.html", form=form, titulo=f"Editar producto #{p.id}")

@app.route("/productos/<int:pid>/eliminar")
def productos_delete(pid):
    p = Producto.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash("Producto eliminado.", "success")
    return redirect(url_for("productos_list"))

# ---------------------------------------------
# === Inicialización de la base de datos ===
# ---------------------------------------------
with app.app_context():
    db.create_all()  # ✅ Crear tablas primero

    # Insertar categorías iniciales si no existen
    if Categoria.query.first() is None:
        categorias = [
            Categoria(nombre="Fútbol", descripcion="Uniformes y accesorios"),
            Categoria(nombre="Básquet", descripcion="Uniformes y accesorios"),
            Categoria(nombre="Voleibol", descripcion="Uniformes y accesorios"),
        ]
        db.session.add_all(categorias)
        db.session.commit()
        print("✅ Categorías iniciales creadas.")
    else:
        print("ℹ️  Categorías ya existen.")

# Crear usuario admin si no existe
    if Usuario.query.filter_by(email="admin@admin.com").first() is None:
        admin = Usuario(email="admin@admin.com")
        admin.set_password("1234")  # Puedes cambiar la contraseña
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuario admin creado.")
    else:
        print("ℹ️ Usuario admin ya existe.")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario and usuario.check_password(form.password.data):
            flash("Inicio de sesión exitoso", "success")
            return redirect(url_for("index"))
        else:
            flash("Correo o contraseña incorrectos", "danger")
    return render_template('login.html', form=form)

# Iniciar app
if __name__ == '__main__':
    app.run(debug=True)