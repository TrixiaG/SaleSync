from flask import Blueprint, render_template, request, flash, jsonify
from .models import prodInventory  # Adjust this import based on your project structure
from . import db
from datetime import datetime
from flask_login import login_required, current_user

inventory = Blueprint('inventory', __name__)

# Route to add or update product
@inventory.route('/inventory', methods=['GET', 'POST'])
@login_required
def add_or_update_product():
    if request.method == 'POST':
        ptype = request.form.get('prodType')
        pcode = request.form.get('prodCode')
        pname = request.form.get('prodName')
        pstock = request.form.get('prodStock')
        pprice = request.form.get('prodPrice')

        ptimelog = datetime.utcnow()
        puserlog = current_user.eid

        # Check if product exists by pname (assuming pname is unique)
        existing_product = prodInventory.query.filter_by(pname=pname).first()

        if existing_product:
            # Update existing product details
            existing_product.ptype = ptype
            existing_product.pcode = pcode
            existing_product.pstock = pstock
            existing_product.ptimelog = ptimelog
            existing_product.puserlog = puserlog
            existing_product.pprice = pprice

        else:
            # Create new product
            new_product = prodInventory(ptype=ptype, pcode=pcode, pname=pname, pstock=pstock, ptimelog=ptimelog, puserlog=puserlog, pprice=pprice)
            db.session.add(new_product)

        db.session.commit()

        flash('Inventory Updated.', 'success')

    # Fetch all products after update
    products = prodInventory.query.all()
    return render_template("inventory.html", products=products)


# Route to search product by code
@inventory.route('/inventory/search_by_code', methods=['POST'])
@login_required
def search_by_code():
    try:
        data = request.json
        prodCode = data.get('prodCode')

        if not prodCode:
            return jsonify({'status': 'error', 'message': 'Product code not provided.'}), 400

        product = prodInventory.query.filter_by(pcode=prodCode).first()

        if product:
            response_data = {
                'status': 'success',
                'prodType': product.ptype,
                'prodName': product.pname,
                'prodStock': product.pstock
            }
            return jsonify(response_data), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error searching product: {str(e)}"}), 500


# Route to search product by name
@inventory.route('/inventory/search_by_name', methods=['POST'])
@login_required
def search_by_name():
    try:
        data = request.json
        prodName = data.get('prodName')

        if not prodName:
            return jsonify({'status': 'error', 'message': 'Product name not provided.'}), 400

        product = prodInventory.query.filter_by(pname=prodName).first()

        if product:
            response_data = {
                'status': 'success',
                'prodType': product.ptype,
                'prodCode': product.pcode,
                'prodStock': product.pstock,
                'prodName': product.pname
            }
            return jsonify(response_data), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error searching product: {str(e)}"}), 500


# Route to search products by type, code, or name
@inventory.route('/inventory/search', methods=['POST'])
@login_required
def search_inventory():
    try:
        data = request.json
        prodType = data.get('prodType', '').strip()
        prodCode = data.get('prodCode', '').strip()
        prodName = data.get('prodName', '').strip()

        query = prodInventory.query

        if prodType:
            query = query.filter(prodInventory.ptype.ilike(f'%{prodType}%'))
        if prodCode:
            query = query.filter(prodInventory.pcode.ilike(f'%{prodCode}%'))
        if prodName:
            query = query.filter(prodInventory.pname.ilike(f'%{prodName}%'))

        products = query.all()

        products_data = [
            {
                'ptype': product.ptype,
                'pcode': product.pcode,
                'pname': product.pname,
                'pstock': product.pstock
            }
            for product in products
        ]

        return jsonify({'status': 'success', 'products': products_data}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error searching inventory: {str(e)}"}), 500

