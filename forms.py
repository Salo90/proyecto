from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional
from wtforms import SelectField
from wtforms.validators import DataRequired, Length, Optional

class ProductoForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired(), Length(max=50)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Length(max=256)])

    # ✅ CAMBIO CLAVE: Usa coerce=str, NO int
    idcategoria = SelectField(
        'Categoría',
        coerce=str,           # ← Ahora es str
        validators=[Optional()],
        choices=[]
    )

    stock = IntegerField('Stock', validators=[DataRequired()])
    precio_venta = DecimalField('Precio de venta', validators=[DataRequired()], places=2)
    submit = SubmitField('Guardar')


class UsuarioForm(FlaskForm):
    nombres = StringField('Nombres', validators=[DataRequired(), Length(min=2, max=100)])
    apellidos = StringField('Apellidos', validators=[DataRequired(), Length(min=2, max=100)])
    idtipodoc = SelectField('Tipo de Documento', coerce=int, validators=[DataRequired()], choices=[])
    num_documento = StringField('Número de Documento', validators=[DataRequired(), Length(min=5, max=20)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(min=7, max=15)])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    direccion = StringField('Dirección', validators=[DataRequired(), Length(min=5, max=200)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    idrol = SelectField('Rol', coerce=int, validators=[DataRequired()], choices=[])
    submit = SubmitField('Registrar')


class LoginForm(FlaskForm):
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')