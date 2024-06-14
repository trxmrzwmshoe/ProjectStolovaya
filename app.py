from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from datetime import date, datetime
from sqlalchemy.types import Enum
from wtforms import StringField, DecimalField, IntegerField, TextAreaField, FileField, SelectField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange, Length, Regexp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///menu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=False)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    fats = db.Column(db.Integer, nullable=False)
    proteins = db.Column(db.Integer, nullable=False) 
    carbs = db.Column(db.Integer, nullable=False)  
    calories = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Dish %r>' % self.id
    
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

class OrderDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(150), nullable=False)
    pickup_location = db.Column(db.String(100), nullable=False, default='Студенческая столовая')
    status = db.Column(db.Enum('В ожидании', 'Выполняется', 'Отправлен', 'Выполнен', 'Отменен', name='order_status'), default='В ожидании')
    details = db.relationship('OrderDetail', backref='order', lazy=True)


    def __repr__(self):
        return '<Order %r>' % self.id

class RegistrationForm(FlaskForm):
    username = StringField('ФИО', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя занято. Пожалуйста, выберите другое.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email занят. Пожалуйста, выберите другой.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class EditProfileForm(FlaskForm):
    username = StringField('ФИО', validators=[DataRequired(), Length(min=2, max=50)])
    city = StringField('Город', validators=[Length(max=100)])
    country = StringField('Страна', validators=[Length(max=100)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Сохранить изменения')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Это имя занято. Пожалуйста, выберите другое.')

class AddDishForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired(), Length(max=50)])
    image = FileField('Изображение', validators=[DataRequired()])
    price = FloatField('Цена', validators=[DataRequired(message="Пожалуйста, введите числовое значение для цены.")])
    text = TextAreaField('Описание', validators=[DataRequired()])
    category = SelectField('Категория', choices=[
        ("bakery", "Выпечка"), 
        ("first-dishes", "Первые блюда"), 
        ("second-dishes", "Вторые блюда"), 
        ("salads", "Салаты"), 
        ("drinks", "Напитки")
    ], validators=[DataRequired()])
    fats = IntegerField('Жиры', validators=[DataRequired(message="Пожалуйста, введите числовое значение для жиров.")])
    proteins = IntegerField('Белки', validators=[DataRequired(message="Пожалуйста, введите числовое значение для белков.")])
    carbs = IntegerField('Углеводы', validators=[DataRequired(message="Пожалуйста, введите числовое значение для углеводов.")])
    calories = IntegerField('Калории', validators=[DataRequired(message="Пожалуйста, введите числовое значение для калорий.")])
    submit = SubmitField('Добавить блюдо')

with app.app_context():
    db.create_all()

menu_categories = ["bakery", "first-dishes", "second-dishes", "salads", "drinks"]

@app.route('/category/<category>')
def category(category):
    dishes = Dish.query.filter_by(category=category).all()
    return render_template('category.html', category=category, dishes=dishes)

@app.route('/')
@app.route('/menu')
def menu():
    dishes = Dish.query.all()
    return render_template('menu.html', dishes=dishes, categories=menu_categories)

@app.route('/menu/<int:id>')
def menu_detail(id):
    dish = Dish.query.get(id)
    return render_template('menu_detail.html', dish=dish)

@app.route('/delete')
def dish_del():
    menu = Dish.query.all()
    return render_template('delete.html', menu=menu)

@app.route('/add', methods=['POST', 'GET'])
def add():
    form = AddDishForm()
    if form.validate_on_submit():
        title = form.title.data
        image = form.image.data
        price = form.price.data
        text = form.text.data
        category = form.category.data
        fats = form.fats.data
        proteins = form.proteins.data
        carbs = form.carbs.data
        calories = form.calories.data

        image_path = os.path.join('static/images', image.filename)
        image.save(image_path)

        dish = Dish(
            title=title,
            image=image.filename,
            price=price,
            text=text,
            category=category,
            fats=int(fats), 
            proteins=int(proteins),  
            carbs=int(carbs), 
            calories=calories
        )
        db.session.add(dish)
        db.session.commit()
        flash('Блюдо добавлено в меню', 'success')
        return redirect(url_for('menu'))
    return render_template('add.html', form=form, category=menu_categories)

@app.route('/remove_dish', methods=['POST'])
def remove_dish():
    dish_id = request.form['dish_id']
    dish = Dish.query.get_or_404(dish_id)
    db.session.delete(dish)
    db.session.commit()
    image_path = os.path.join('static/images', dish.image)
    if os.path.exists(image_path):
        os.remove(image_path)
    return redirect('/delete')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Ваш аккаунт был создан!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            flash('Вы вошли в систему!', 'success')
            return redirect(url_for('menu'))
        else:
            flash('Вход неуспешный. Пожалуйста, проверьте электронную почту и пароль', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы!', 'success')
    return redirect(url_for('menu'))

@app.route('/profile/<username>')
@login_required
def profile(username):
    if current_user.username != username:
        flash('Вы не можете просматривать профили других пользователей\' войдите в систему.', 'danger')
        return redirect(url_for('menu'))
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.city = form.city.data
        current_user.country = form.country.data
        if form.password.data:
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
            current_user.password = hashed_password
        db.session.commit()
        flash('Ваш профиль был обновлен!', 'success')
        return redirect(url_for('profile', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.city.data = current_user.city
        form.country.data = current_user.country
    return render_template('edit_profile.html', form=form)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Вы не имеете доступа к этой странице.', 'danger')
            return redirect(url_for('menu'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
def admin():
    orders = Order.query.all()
    return render_template('admin.html', orders=orders)

@app.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    new_status = request.form.get('status')
    order = Order.query.get_or_404(order_id)
    if new_status in ['В ожидании', 'Выполняется', 'Отправлен', 'Выполнен', 'Отменен']:
        order.status = new_status
        db.session.commit()
        flash('Статус заказа обновлен!', 'success')
    else:
        flash('Неверный статус заказа!', 'danger')
    return redirect(url_for('staff'))

@app.route('/delete_user', methods=['POST'])
@login_required
@admin_required
def delete_user():
    user_id = request.form['user_id']
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    dishes = []
    total_price = 0.0  # Убедитесь, что это float
    for item in cart_items:
        dish = Dish.query.get(item.dish_id)
        dish.quantity = item.quantity
        dishes.append(dish)
        total_price += float(dish.price) * item.quantity
    return render_template('cart.html', dishes=dishes, total_price=round(total_price, 2))

@app.route('/add_to_cart/<int:dish_id>', methods=['POST'])
@login_required
def add_to_cart(dish_id):
    quantity = request.form.get('quantity', 1, type=int)  # Получаем количество из формы
    existing_item = Cart.query.filter_by(user_id=current_user.id, dish_id=dish_id).first()
    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = Cart(user_id=current_user.id, dish_id=dish_id, quantity=quantity)
        db.session.add(new_item)
    db.session.commit()
    flash('Блюдо добавлено в корзину', 'success')
    return redirect(url_for('menu'))

@app.route('/remove_from_cart/<int:dish_id>', methods=['POST'])
@login_required
def remove_from_cart(dish_id):
    item = Cart.query.filter_by(user_id=current_user.id, dish_id=dish_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Блюдо удалено из корзины', 'success')
    return redirect(url_for('cart'))

@app.route('/update_cart/<int:dish_id>', methods=['POST'])
@login_required
def update_cart(dish_id):
    quantity = int(request.form['quantity'])
    if quantity < 1:
        quantity = 1
    item = Cart.query.filter_by(user_id=current_user.id, dish_id=dish_id).first()
    if item:
        item.quantity = quantity
        db.session.commit()
        flash('Количество обновлено', 'success')
    return redirect(url_for('cart'))

@app.route('/remove_one_from_cart/<int:dish_id>', methods=['POST'])
@login_required
def remove_one_from_cart(dish_id):
    item = Cart.query.filter_by(user_id=current_user.id, dish_id=dish_id).first()
    if item:
        if item.quantity > 1:
            item.quantity -= 1
            db.session.commit()
            flash('Одно блюдо удалено', 'success')
        else:
            db.session.delete(item)
            db.session.commit()
            flash('Блюдо удалено из корзины', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        order_date = date.today()
        email = current_user.email
        total_price = float(request.form['total_price'])
        pickup_location = 'Студенческая столовая'
        
        new_order = Order(
            user_id=current_user.id, 
            total_price=total_price, 
            order_date=order_date, 
            email=email, 
            pickup_location=pickup_location,
            status='В ожидании'
        )
        db.session.add(new_order)
        db.session.flush()  # Это нужно для получения ID нового заказа

        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        for item in cart_items:
            order_detail = OrderDetail(
                order_id=new_order.id,
                dish_id=item.dish_id,
                quantity=item.quantity
            )
            db.session.add(order_detail)
        
        Cart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('Заказ успешно сделан', 'success')
        return redirect(url_for('menu'))
    else:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        dishes = []
        total_price = 0
        for item in cart_items:
            dish = Dish.query.get(item.dish_id)
            dish.quantity = item.quantity
            dishes.append(dish)
            total_price += dish.price * item.quantity
        return render_template('checkout.html', dishes=dishes, total_price=total_price, email=current_user.email, order_date=date.today(), order_time=datetime.now().time())


@app.route('/my_orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/staff')
def staff():
    orders = Order.query.all()
    order_details = {order.id: db.session.query(OrderDetail, Dish).join(Dish).filter(OrderDetail.order_id == order.id).all() for order in orders}
    return render_template('staff.html', orders=orders, order_details=order_details)

if __name__ == '__main__':
    app.run(debug=True)
