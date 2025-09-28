from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional
from wtforms import SelectField
from wtforms.validators import DataRequired, Length, Optional

class ProductoForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired(), Length(max=50)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Length(max=256)])

    # CAMBIO CLAVE: Usa coerce=str, NO int
    idcategoria = SelectField(
        'Categoría',
        coerce=str,           # ← Ahora es str
        validators=[Optional()],
        choices=[]
    )

    stock = IntegerField('Stock', validators=[DataRequired()])
    precio_venta = DecimalField('Precio de venta', validators=[DataRequired()], places=2)
    estado = SelectField(
        'Estado',
        choices=[('1', 'Activo'), ('0', 'Inactivo')],
        validators=[DataRequired()],
        coerce=str  # porque los valores vienen como strings desde el HTML
    )
    submit = SubmitField('Guardar')
    
class UsuarioForm(FlaskForm):
    nombres = StringField('Nombres', validators=[DataRequired()])
    apellidos = StringField('Apellidos', validators=[DataRequired()])
    idtipodoc = SelectField(
        'Tipo de Documento',
        choices=[],
        validators=[DataRequired("Selecciona un tipo de documento.")]
    )
    num_documento = StringField('Número de Documento', validators=[DataRequired()])
    telefono = StringField('Teléfono', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    direccion = StringField('Dirección', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message="La contraseña es obligatoria.")
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message="La confirmación de contraseña es obligatoria."),
        EqualTo('password', message="Las contraseñas deben coincidir.")
    ])
    idrol = SelectField(
        'Rol',
        choices=[],
        validators=[DataRequired("Selecciona un rol.")]
    )
    submit = SubmitField('Registrar')
    
class LoginForm(FlaskForm):
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')
    
class RolForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = StringField('Descripción')
    estado = SelectField('Estado', choices=[('1','Activo'),('0','Inactivo')])
    submit = SubmitField('Crear Rol')