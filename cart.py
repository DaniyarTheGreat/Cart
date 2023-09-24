import requests,random,os
from flask import Flask, jsonify, request
from sqlalchemy import update
from flask_sqlalchemy import SQLAlchemy

PRODUCT_SERVICE_URL = 'http://127.0.0.1:5000'

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cart.sqlite')
db = SQLAlchemy(app)

class Cart(db.Model):
  user_id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(150), nullable = False)
  price = db.Column(db.Integer, primary_key = False)
  quantity = db.Column(db.Integer, primary_key = False)
    
# Endpoint 1: Get a list of all the products in the cart
@app.route('/cart', methods=['GET'])
def get_cart_products():
  cart_products = Cart.query.all()
  cart_product_list = [{"user_id": product.user_id, "name": product.name, "price": product.price, "quantity": product.quantity} for product in cart_products]
  return jsonify({"cart": cart_product_list})

# Endpoint 2: Add a new product to the cart
@app.route('/cart/<int:user_id>/add/<int:product_id>', methods=['POST'])
def add_product(user_id, product_id):
    data = request.get_json()
    quantity = data.get('quantity', 0)
    response = requests.get(f'{PRODUCT_SERVICE_URL}/products/{product_id}').json()

    decrement_response = requests.post(f"{PRODUCT_SERVICE_URL}/products/{product_id}/decrement/{quantity}")
    if decrement_response.status_code != 200:
      return jsonify({'message': 'Unable to add to cart'}), 400

    new_product_in_cart = Cart(user_id = user_id, name= response['product']['name'], price = response['product']['price'], quantity = quantity)
    db.session.add(new_product_in_cart)
    db.session.commit()
    
    return jsonify({"message": "Cart created", "cart": 
    	{"user_id": new_product_in_cart.user_id, "name": new_product_in_cart.name, "price": new_product_in_cart.price, "quantity": new_product_in_cart.quantity}}), 201

# # Endpoint 3: Remove a product from the cart
@app.route('/cart/<int:user_id>/remove/<int:product_id>', methods=['POST'])
def remove_product(user_id, product_id):
  data = request.get_json()
  quantity = data.get('quantity', 0)

  increment_response = requests.post(f"{PRODUCT_SERVICE_URL}/products/{product_id}/increment/{quantity}")
  if increment_response.status_code != 200:
    return jsonify({'message': 'Unable to remove from cart'}), 400
  
  cart = Cart.query.get(user_id)
  if cart.quantity <= quantity:
    db.session.delete(cart)
    db.session.commit()
    return jsonify({"message": "Deleted from cart", "product":
      {"user_id": cart.user_id, "name": cart.name, "price": cart.price, "quantity": cart.quantity}}), 201
  else:
    cart.quantity -= quantity
    db.session.commit()
    return jsonify({"message": "Number of product deleted from cart", "cart":
      {"user_id": cart.user_id, "name": cart.name, "price": cart.price, "quantity": cart.quantity}}), 201 

if __name__ == '__main__':
  # with app.app_context():
  #     db.create_all()
  app.run(debug=True, port=5002)