# aplicacion en flask
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    #return '¡Hola! Bienvenido a mi aplicación Flask.'
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

if __name__ == '__main__':
    app.run(debug=True)
#rutas en flask