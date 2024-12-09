import MySQLdb
from flask import Flask, jsonify, render_template, request, redirect, send_file, url_for, flash, make_response
from flask_mysqldb import MySQL
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

# Configuración de la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Marquesitas'
app.config['MYSQL_DB'] = 'marquesitas'
app.secret_key = 'supersecretkey'

mysql = MySQL(app)

# Ruta para generar reporte de empleados
@app.route('/admin/generar_reporte_empleados')
def generar_reporte_empleados():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM personal")
    empleados = cursor.fetchall()
    cursor.close()

    # Crear un objeto en memoria para el PDF
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setFont("Helvetica", 12)

    # Agregar título
    c.drawString(100, 750, "Reporte de Empleados")

    # Definir encabezados de la tabla
    c.drawString(100, 730, "RFC Empleado")
    c.drawString(200, 730, "Nombre")
    c.drawString(300, 730, "Puesto")
    c.drawString(400, 730, "Sueldo")
    c.drawString(500, 730, "Teléfono")

    # Agregar datos de los empleados
    y_position = 710
    for empleado in empleados:
        c.drawString(100, y_position, empleado[0])
        c.drawString(200, y_position, empleado[1])
        c.drawString(300, y_position, empleado[2])
        c.drawString(400, y_position, str(empleado[3]))
        c.drawString(500, y_position, str(empleado[4]))
        y_position -= 20

    c.save()

    # Preparar la respuesta
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte_empleados.pdf'
    return response

# Ruta para generar reporte de turnos
@app.route('/admin/generar_reporte_turnos')
def generar_reporte_turnos():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM turnos")
    turnos = cursor.fetchall()
    cursor.close()

    # Crear un objeto en memoria para el PDF
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setFont("Helvetica", 12)

    # Agregar título
    c.drawString(100, 750, "Reporte de Turnos")

    # Definir encabezados de la tabla
    c.drawString(100, 730, "RFC Empleado")
    c.drawString(200, 730, "Turno")

    # Agregar datos de los turnos
    y_position = 710
    for turno in turnos:
        c.drawString(100, y_position, turno[0])
        c.drawString(200, y_position, turno[1])
        y_position -= 20

    c.save()

    # Preparar la respuesta
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte_turnos.pdf'
    return response

# Ruta principal
@app.route('/')
def inicio():
    return render_template('sitio/index.html')

# Ruta para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Cuentas predefinidas
        cuentas = {
            'admin': 'admin123',
            'inventario': 'inventario123',
            'pedidos': 'pedidos123'
        }

        # Verificar si el usuario y la contraseña son correctos
        if username in cuentas and cuentas[username] == password:
            return redirect(url_for('menu', user=username))  # Redirige al menú correspondiente
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('login'))
    
    return render_template('sitio/login.html')

# Ruta para el menú de usuario
@app.route('/menu/<user>')
def menu(user):
    if user == 'admin':
        return render_template('sitio/admin_menu.html', user=user)
    elif user == 'inventario':
        return render_template('sitio/empleados.html', user=user)
    elif user == 'pedidos':
        return render_template('sitio/clientes.html', user=user)
    else:
        return redirect(url_for('login'))
    
"""# Ruta para obtener los productos (para la tabla)
@app.route('/admin/inventario')
def productos():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos")
    productos = cur.fetchall()
    return render_template('sitio/inventario.html', productos=productos)"""

@app.route('/admin/inventario')
def productos_e_inventario():
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM productos")
    productos = cur.fetchall()
    cur.execute("SELECT * FROM inventario")
    inventario = cur.fetchall()
    cur.close()
    return render_template('sitio/inventario.html', productos=productos, inventario=inventario)

    

# Ruta para agregar o editar productos
@app.route('/admin/inventario/agregar', methods=['POST'])
@app.route('/admin/inventario/editar', methods=['POST'])
def agregar_editar_producto():
    data = request.get_json()
    if data['id_producto']:
        # Editar producto
        cur = mysql.connection.cursor()
        cur.execute('''UPDATE productos SET nombre_producto = %s, descripcion = %s, precio = %s, existencias = %s WHERE id_producto = %s''',
                    (data['nombre_producto'], data['descripcion'], data['precio'], data['existencias'], data['id_producto']))
        mysql.connection.commit()
        return jsonify({"message": "Producto actualizado correctamente"})
    else:
        # Agregar nuevo producto
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO productos (nombre_producto, descripcion, precio, existencias) VALUES (%s, %s, %s, %s)''',
                    (data['nombre_producto'], data['descripcion'], data['precio'], data['existencias']))
        mysql.connection.commit()
        return jsonify({"message": "Producto agregado correctamente"})

# Ruta para eliminar producto
@app.route('/admin/inventario/eliminar/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM productos WHERE id_producto = %s", (id,))
    mysql.connection.commit()
    return jsonify({"message": "Producto eliminado correctamente"})

# Ruta para la sección de empleados
@app.route('/admin/empleados', methods=['GET', 'POST'])
def empleados():
    cursor = mysql.connection.cursor()
    
    if request.method == 'POST':
        action = request.form['action']
        
        # Añadir un empleado
        if action == 'agregar':
            rfc_emp = request.form['rfc_emp']
            nombre = request.form['nombre']
            puesto = request.form['puesto']
            sueldo = request.form['sueldo']
            telefono = request.form['telefono']
            cursor.execute(
                "INSERT INTO personal (rfc_emp, nombre, puesto, sueldo, telefono) VALUES (%s, %s, %s, %s, %s)",
                (rfc_emp, nombre, puesto, sueldo, telefono)
            )
            mysql.connection.commit()
            flash('Empleado añadido exitosamente', 'success')

        # Modificar un empleado
        elif action == 'modificar':
            rfc_emp = request.form['rfc_emp']
            nombre = request.form['nombre']
            puesto = request.form['puesto']
            sueldo = request.form['sueldo']
            telefono = request.form['telefono']
            cursor.execute(
                "UPDATE personal SET nombre=%s, puesto=%s, sueldo=%s, telefono=%s WHERE rfc_emp=%s",
                (nombre, puesto, sueldo, telefono, rfc_emp)
            )
            mysql.connection.commit()
            flash('Empleado modificado exitosamente', 'success')

    # Obtener todos los empleados
    cursor.execute("SELECT * FROM personal")
    empleados = cursor.fetchall()

    # Obtener todos los turnos
    cursor.execute("SELECT * FROM turnos")
    turnos = cursor.fetchall()
    cursor.close()

    return render_template('sitio/empleados.html', empleados=empleados, turnos=turnos)

# Ruta para eliminar un empleado
@app.route('/admin/empleados/eliminar/<string:rfc_emp>')
def eliminar_empleado(rfc_emp):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM personal WHERE rfc_emp = %s", (rfc_emp,))
    mysql.connection.commit()
    cursor.close()
    flash('Empleado eliminado exitosamente', 'danger')
    return redirect(url_for('empleados'))

# Ruta para la sección de turnos
@app.route('/admin/turnos', methods=['GET', 'POST'])
def turnos():
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        action = request.form['action']
        
        # Añadir un turno
        if action == 'agregar':
            rfc_emp = request.form['rfc_emp']
            turno = request.form['turno']
            cursor.execute(
                "INSERT INTO turnos (rfc_emp, turno) VALUES (%s, %s)",
                (rfc_emp, turno)
            )
            mysql.connection.commit()
            flash('Turno añadido exitosamente', 'success')

        # Modificar un turno
        elif action == 'modificar':
            rfc_emp = request.form['rfc_emp']
            turno = request.form['turno']
            cursor.execute(
                "UPDATE turnos SET turno=%s WHERE rfc_emp=%s",
                (turno, rfc_emp)
            )
            mysql.connection.commit()
            flash('Turno modificado exitosamente', 'success')

    # Obtener todos los turnos
    cursor.execute("SELECT * FROM turnos")
    turnos = cursor.fetchall()
    cursor.close()

    return render_template('sitio/empleados.html', turnos=turnos)

# Ruta para eliminar un turno
@app.route('/admin/turnos/eliminar/<string:id_turno>')
def eliminar_turno(id_turno):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM turnos WHERE id_turno = %s", (id_turno,))
    mysql.connection.commit()
    cursor.close()
    flash('Turno eliminado exitosamente', 'danger')
    return redirect(url_for('turnos'))

"""@app.route('/admin/inventario')
def inventario():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM inventario")
    inventario = cur.fetchall()
    return render_template('sitio/inventario.html', inventario=inventario)"""

# Ruta para obtener los clientes y los pedidos
@app.route('/admin/clientes')
def clientes_y_pedidos():
    cur = mysql.connection.cursor()
    
    # Obtener todos los clientes
    cur.execute("SELECT * FROM clientes")
    clientes = cur.fetchall()

    # Obtener todos los pedidos
    cur.execute("SELECT * FROM pedidos")
    pedidos = cur.fetchall()

    cur.close()

    # Pasar los clientes y pedidos a la plantilla
    return render_template('sitio/clientes.html', clientes=clientes, pedidos=pedidos)

# Ruta para agregar cliente
@app.route('/admin/agregar_cliente', methods=['GET', 'POST'])
def agregar_cliente():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form['nombre']
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO clientes (nombre) VALUES (%s)", (nombre,))
        mysql.connection.commit()
        flash('Cliente agregado exitosamente', 'success')
        return redirect(url_for('clientes_y_pedidos'))
    
    return render_template('sitio/agregar_cliente.html')

# Ruta para agregar pedido
@app.route('/admin/agregar_pedido', methods=['GET', 'POST'])
def agregar_pedido():
    if request.method == 'POST':
        # Obtener los datos del formulario
        id_cliente = request.form['id_cliente']
        fecha_pedido=request.form['fecha_pedido']
        id_producto = request.form['id_producto']
        total_venta = request.form['total_venta']
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO pedidos (id_cliente, fecha_pedido, id_producto,  total_venta) VALUES (%s, %s, %s, %s)", 
                    (id_cliente, fecha_pedido, id_producto, total_venta))
        mysql.connection.commit()
        flash('Pedido agregado exitosamente', 'success')
        return redirect(url_for('clientes_y_pedidos'))
    
    # Obtener los productos disponibles para seleccionar
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos")
    productos = cur.fetchall()
    cur.close()

    return render_template('sitio/agregar_pedido.html', productos=productos)

"""def obtener_pedidos():
    # Asumiendo que ya tienes la conexión a la base de datos configurada
    cursor = mysql.connection.cursor()
    query = "SELECT p.id_pedido, c.nombre, p.fecha_pedido, pr.nombre, p.total_venta FROM pedidos p JOIN clientes c ON p.id_cliente = c.id_cliente JOIN productos pr ON p.id_producto = pr.id_producto"
    cursor.execute(query)
    pedidos = cursor.fetchall()
    cursor.close()
    return pedidos"""
    
@app.route('/admin/generar_reporte_pedidos')
def generar_reporte_pedidos():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM pedidos")
    pedidos = cursor.fetchall()
    cursor.close()
    
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setFont("Helvetica", 12)

    # Agregar título
    c.drawString(100, 750, "Reporte de Pedidos")

    # Definir encabezados de la tabla
    c.drawString(100, 730, "id_pedido")
    c.drawString(200, 730, "id_cliente")
    c.drawString(300, 730, "Fecha")
    c.drawString(400, 730, "id_producto")
    c.drawString(500, 730, "Total")

    y_position = 710
    for pedido in pedidos:
        c.drawString(100, y_position, str(pedido[0]))
        c.drawString(200, y_position, str(pedido[1]))
        c.drawString(300, y_position, str(pedido[2]))
        c.drawString(400, y_position, str(pedido[3]))
        c.drawString(500, y_position, f"${pedido[4]}")
        y_position -= 20

    c.save()

    # Preparar la respuesta
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte_pedidos.pdf'
    return response
"""

@app.route('/admin/generar_reporte_pedidos')
def generar_reporte_pedidos():
    # Crear un archivo en memoria
    buffer = io.BytesIO()

    # Crear un objeto canvas (PDF)
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Título del reporte
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 40, "Reporte de Pedidos")

    # Subtítulo
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 70, "Listado de pedidos realizados:")

    # Llamar a la base de datos para obtener los pedidos
    pedidos = obtener_pedidos()  # Aquí debes definir cómo obtener tus pedidos desde la base de datos

    y_position = height - 100  # Posición inicial en Y

    # Encabezados de la tabla
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y_position, "ID Pedido")
    c.drawString(150, y_position, "Cliente")
    c.drawString(250, y_position, "Producto")
    c.drawString(350, y_position, "Fecha Pedido")
    c.drawString(450, y_position, "Total Venta")

    # Dibujar los pedidos
    y_position -= 20
    c.setFont("Helvetica", 10)
    for pedido in pedidos:
        c.drawString(50, y_position, str(pedido[0]))  # ID Pedido
        c.drawString(150, y_position, pedido[1])  # Cliente
        c.drawString(250, y_position, pedido[3])  # Producto
        c.drawString(350, y_position, str(pedido[2]))  # Fecha
        c.drawString(450, y_position, f"${pedido[4]}")  # Total Venta
        y_position -= 15

        if y_position < 50:
            c.showPage()  # Crear una nueva página si es necesario
            y_position = height - 40

    # Guardar el PDF en el buffer
    c.save()

    # Mover el puntero del buffer al inicio para poder leerlo
    buffer.seek(0)

    # Devolver el archivo PDF como respuesta
    return send_file(buffer, as_attachment=True, download_name="reporte_pedidos.pdf", mimetype="application/pdf")
"""
@app.route('/inventario/agregar', methods=['POST'])
def agregar_ingrediente():
    data = request.json
    cur = mysql.connection.cursor()
    query = "INSERT INTO Inventario (ingrediente, cantidad, fecha_actualizacion) VALUES (%s, %s, %s)"
    cur.execute(query, (data['ingrediente'], data['cantidad'], data['fecha_actualizacion']))
    mysql.connection.commit()
    cur.close()
    mysql.connection.close()
    return jsonify({"message": "Ingrediente agregado exitosamente"})

@app.route('/inventario/editar/<int:id>', methods=['POST'])
def editar_ingrediente(id):
    data = request.json
    cur = mysql.connection.cursor()
    query = "UPDATE Inventario SET ingrediente = %s, cantidad = %s, fecha_actualizacion = %s WHERE id_ingrediente = %s"
    cur.execute(query, (data['ingrediente'], data['cantidad'], data['fecha_actualizacion'], id))
    mysql.connection.commit()
    cur.close()
    mysql.connection.close()
    return jsonify({"message": "Ingrediente actualizado exitosamente"})

@app.route('/inventario/eliminar/<int:id>', methods=['DELETE'])
def eliminar_ingrediente(id):
    cur = mysql.connection.cursor()
    query = "DELETE FROM Inventario WHERE id_ingrediente = %s"
    cur.execute(query, (id,))
    mysql.connection.commit()
    cur.close()
    mysql.connection.close()
    return jsonify({"message": "Ingrediente eliminado exitosamente"})


if __name__ == '__main__':
    app.run(debug=True)