
PASOS DE INSTALACIÓN (Windows CMD/Powershell)

1) Crear entorno e instalar dependencias
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt

2) Crear base de datos MySQL desde CMD (tras entrar a mysql):
   mysql -u root -p
   CREATE DATABASE videla_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
   CREATE USER 'videla_user'@'localhost' IDENTIFIED BY 'videla_pass';
   GRANT ALL PRIVILEGES ON videla_db.* TO 'videla_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;

3) Copiar .env.example a .env y ajustar valores (SITE_URL y MP_ACCESS_TOKEN).

4) Migraciones y superusuario
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser

5) Ejecutar servidor
   python manage.py runserver

6) Cargar datos
   - Entra al /admin y crea Categorías, Productos (con imagen) y Promociones.
   - Las promociones aparecen en la portada y en /promociones
   - Usa el carrito, checkout y serás redirigido a Mercado Pago.
