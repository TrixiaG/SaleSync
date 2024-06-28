from flask import Blueprint, render_template, request, jsonify
from .models import Transaction, IndivTransaction, prodInventory, db, User
from flask_login import current_user, login_required
from datetime import datetime

cashierops = Blueprint('cashierops', __name__)

@cashierops.route('/cashier-ops', methods=['GET', 'POST'])
@login_required
def user_cashier():
    logged_in_user = current_user.first_name  
    current_date = datetime.now().strftime("%Y-%m-%d")
    return render_template("cashierops.html", boolean=True, CashierStaff=logged_in_user, date=current_date)

# Route to get product details by product code
@cashierops.route('/get-product-details/<productCode>', methods=['GET'])
@login_required
def get_product_details(productCode):
    try:
        product = prodInventory.query.filter_by(pcode=productCode).first()
        if not product:
            return jsonify({"error": f"Product with code {productCode} not found"}), 404
        
        return jsonify({
            "pname": product.pname,
            "pprice": str(product.pprice),
            "ptype": product.ptype,
             "pcode": product.pcode
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#get product types
@cashierops.route('/get-product-types', methods=['GET'])
@login_required
def get_product_types():
    try:
        product_types = db.session.query(prodInventory.ptype).distinct().all()
        types_list = [ptype[0] for ptype in product_types]
        return jsonify({"product_types": types_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# get product names by product types
@cashierops.route('/get-product-names/<productType>', methods=['GET'])
@login_required
def get_product_names(productType):
    try:
        products = prodInventory.query.filter_by(ptype=productType).all()
        names_list = [{"name": product.pname, "code": product.pcode} for product in products]
        return jsonify({"product_names": names_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@cashierops.route('/create-transaction', methods=['POST', 'GET'])
@login_required
def create_transaction():
    try:
        # Create new transaction record with total_amount initialized to 0
        new_transaction = Transaction(total_amount=0)
        db.session.add(new_transaction)
        db.session.commit()
        
        return jsonify({
            "message": "Transaction created successfully", 
            "transaction_id": new_transaction.transaction_id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@cashierops.route('/add-product-to-transaction', methods=['POST'])
@login_required
def add_product_to_transaction():
    data = request.json
    try:
        transaction_id = data.get('transaction_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        # Fetch transaction and product
        transaction = Transaction.query.get(transaction_id)
        product = prodInventory.query.filter_by(pcode=product_id).first()
        
        if not transaction or not product:
            raise ValueError("Invalid transaction or product ID")
        
        # Calculate total price for this product
        total_price = quantity * product.pprice
        
        # Create individual transaction record
        transaction_item = IndivTransaction(
            transaction_id=transaction_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.pprice
        )
        
        db.session.add(transaction_item)
        
        # Update transaction total amount
        transaction.total_amount += total_price
        
        # Update product stock
        product.update_stock(quantity)
        
        db.session.commit()
        
        return jsonify({"message": "Product added successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@cashierops.route('/get-transaction-details/', methods=['GET'])
@login_required
def get_transaction_details():
    transaction_id = request.args.get('transaction_id')
    
    try:
        transaction = Transaction.query.get(transaction_id)
        
        if not transaction:
            raise ValueError("Invalid transaction ID")
        
        items = IndivTransaction.query.filter_by(transaction_id=transaction_id).all()
        item_details = [{
            'product_id': item.product_id,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total_price': item.quantity * item.unit_price
        } for item in items]
        
        return jsonify({
            'transaction_id': transaction_id,
            'total_amount': transaction.total_amount,
            'items': item_details
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@cashierops.route('/reset-transaction', methods=['POST'])
@login_required
def reset_transaction():
    data = request.json
    transaction_id = data.get('transaction_id')

    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError("Invalid transaction ID")

        IndivTransaction.query.filter_by(transaction_id=transaction_id).delete()

        db.session.delete(transaction)
        db.session.commit()

        return jsonify({"message": "Transaction reset successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@cashierops.route('/remove-product/<product_id>', methods=['POST'])
@login_required
def remove_product(product_id):
    try:
        current_transaction = Transaction.query.filter_by(user_eid=current_user.eid).first()

        if current_transaction:
            item_to_remove = IndivTransaction.query.filter_by(transaction_id=current_transaction.transaction_id, product_id=product_id).first()

            if item_to_remove:
                db.session.delete(item_to_remove)
                db.session.commit()
                return jsonify({'success': True}), 200
            else:
                return jsonify({'error': 'Product not found in your transaction.'}), 404
        else:
            return jsonify({'error': 'No active transaction found for the current user.'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
