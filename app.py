from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///menu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


class Dish(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   title = db.Column(db.String(50), nullable=False)
   image = db.Column(db.String(100))
   price = db.Column(db.String(500), nullable=False)
   text = db.Column(db.Text, nullable=False)
   
   def __repr__(self):
    return '<Dish %r>' % self.id

with app.app_context():
   db.create_all()
   db.session.commit()


@app.route('/')
@app.route('/index')
def index():
  return render_template ("index.html")

@app.route('/menu')
def menu():
    dishes = Dish.query.all()
    return render_template('menu.html', dishes=dishes)

@app.route('/menu/<int:id>')
def menu_detail(id):
    dish = Dish.query.get(id)
    return render_template('menu_detail.html', dish=dish)

@app.route('/first-meal')
def first_meal():
    return render_template('first-meal.html')

@app.route('/delete')
def dish_del():
    menu = Dish.query.all()
    return render_template('delete.html', menu=menu)

@app.route('/add', methods=['POST', 'GET'])
def add():
    if request.method == "POST":
       title = request.form['title']
       image = request.files['image']
       price = request.form['price']
       text = request.form['text']

       dish = Dish(title=title, image=image.filename, price=price, text=text)

       try:
          db.session.add(dish)
          db.session.commit()
          return redirect('/add')
       except:
          return "При добавлении блюда произошла ошибка"
    else:
       return render_template('add.html')

   
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


if __name__ == '__main__':
  app.run(debug=True)