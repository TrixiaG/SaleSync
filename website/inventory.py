from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import prodInventory
from . import db
from datetime import datetime
from flask_login import login_required, current_user

inventory = Blueprint('inventory', __name__)

@inventory.route('/inventory', methods=['GET', 'POST'])
@login_required
def addProduct():
    if request.method == 'POST':
        ptype = request.form.get('prodType')
        pcode = request.form.get('prodCode')
        pname = request.form.get('prodName')
        pstock = request.form.get('prodStock')

        ptimelog = datetime.utcnow()
        puserlog = current_user.eid 

        if ptype:
            products = prodInventory.query.filter_by(ptype=ptype).all()
        elif pcode:
            products = prodInventory.query.filter_by(pcode=pcode).all()
        elif pname:
            products = prodInventory.query.filter_by(pname=pname).all()
        else:
            products = prodInventory.query.all()
        
        existing_product = prodInventory.query.filter_by(pname=pname).first()

        if existing_product:
            # Update existing product details
            existing_product.ptype = ptype
            existing_product.pcode = pcode
            existing_product.pstock = pstock
            existing_product.ptimelog = ptimelog
            existing_product.puserlog = puserlog
        else:   
            new_product = prodInventory(ptype=ptype, pcode=pcode, pname=pname, pstock=pstock, ptimelog=ptimelog, puserlog=puserlog)
            db.session.add(new_product)

        db.session.commit()

        flash('Inventory Updated.', 'success')

        products = prodInventory.query.all()

        return render_template("inventory.html", products=products)

    elif request.method == 'GET':
        products = prodInventory.query.all()

    return render_template("inventory.html", products=products)
#SEARCH
@inventory.route('/inventory/search_by_code', methods=['POST'])
@login_required
def search_product_by_code():
    try:
        pcode = request.json.get('prodCode')
        
        # Log the request
        print(f"Search request received: prodCode={pcode}")

        if not pcode:
            return jsonify({
                'status': 'error',
                'message': 'Product code not provided.'
            }), 400

        product = prodInventory.query.filter_by(pcode=pcode).first()

        if product:
            return jsonify({
                'status': 'success',
                'prodType': product.ptype,
                'prodName': product.pname,
                'prodStock': product.pstock,
                'prodCode': product.pcode
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Product not found.'
            }), 404
    except Exception as e:
        print(f"Error searching product: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"An error occurred: {str(e)}"
        }), 500


# SEARCH FUNCTION ----------------
@inventory.route('/inventory/search_by_name', methods=['POST'])
@login_required
def search_product_by_name():
    pname = request.json.get('prodName')
    
    # Log the request
    print(f"Search request received: prodName={pname}")

    if pname:
        product = prodInventory.query.filter_by(pname=pname).first()

        if product:
            return jsonify({
                'status': 'success',
                'prodType': product.ptype,
                'prodCode': product.pcode,
                'prodStock': product.pstock,
                'prodName': product.pname
            })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Product name not provided.'
        })


#DELETE FUNCTION ------------------------
@inventory.route('/inventory/delete_product', methods=['POST'])
@login_required
def delete_product():
    try:
        req_data = request.get_json()
        pcode = req_data.get('prodCode')
        pname = req_data.get('prodName')

        if not pcode and not pname:
            return jsonify({'status': 'error', 'message': 'Product code or name not provided.'})

        print(f"Delete request received: prodCode={pcode}, prodName={pname}")

        product = None
        if pcode:
            product = prodInventory.query.filter_by(pcode=pcode).first()
        elif pname:
            product = prodInventory.query.filter_by(pname=pname).first()

        if product:
            db.session.delete(product)
            db.session.commit()

            deleted_product = prodInventory.query.filter_by(pcode=pcode).first() if pcode else prodInventory.query.filter_by(pname=pname).first()
            if deleted_product is None:
                print("Product successfully deleted.")
                return jsonify({'status': 'success', 'message': 'Product deleted successfully.'})
            else:
                print("Product deletion failed.")
                return jsonify({'status': 'error', 'message': 'Product deletion failed.'})
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'})
    except Exception as e:
        db.session.rollback()
        # Log the error
        print(f"Error deleting product: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error deleting product: {str(e)}'})



#UPDATE PRODUCT -------------------------------------------
@inventory.route('/inventory/update_product', methods=['POST'])
@login_required
def update_product():
    req_data = request.json
    pcode = req_data.get('prodCode')

    if pcode:
        product = prodInventory.query.filter_by(pcode=pcode).first()

        if product:
            try:
                product.ptype = req_data.get('prodType')
                product.pname = req_data.get('prodName')
                product.pstock = req_data.get('prodStock')
                product.ptimelog = datetime.utcnow()
                product.puserlog = current_user.eid 

                db.session.commit()
                return jsonify({'status': 'success', 'message': 'Product updated successfully.'})
            except Exception as e:
                db.session.rollback()
                return jsonify({'status': 'error', 'message': 'Error updating product in database.'})
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'})
    else:
        return jsonify({'status': 'error', 'message': 'Product code not provided.'})
    
#ADD/REMOVE STOCKS

@inventory.route('/inventory/addreducestocks', methods=['POST'])
@login_required
def add_stocks():
    try:
        req_data = request.get_json()
        pcode = req_data.get('prodCode')
        additional_stock = req_data.get('additionalStock')

        if not pcode or not additional_stock:
            return jsonify({'status': 'error', 'message': 'Product code and additional stock must be provided.'}), 400

        product = prodInventory.query.filter_by(pcode=pcode).first()

        if product:
            try:
                product.pstock += int(additional_stock)
                product.ptimelog = datetime.utcnow()
                product.puserlog = current_user.eid

                db.session.commit()
                return jsonify({'status': 'success', 'message': 'Stocks added successfully.'})
            except Exception as e:
                db.session.rollback()
                return jsonify({'status': 'error', 'message': 'Error adding stocks to the database.'}), 500
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error adding stocks: {str(e)}'}), 500

#DROPDOWN SUGGESTION FOR PRODUCT TYPE
@inventory.route('/inventory/get_product_types', methods=['GET'])
@login_required
def get_product_types():
    try:
        product_types = db.session.query(prodInventory.ptype).distinct().all()
        product_types_list = [ptype[0] for ptype in product_types]
        return jsonify({'status': 'success', 'productTypes': product_types_list}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error fetching product types: {str(e)}"}), 500
    

#DROPDOWN SUGGESTION FOR PRODUCT NAME
@inventory.route('/inventory/get_product_names', methods=['POST'])
@login_required
def get_product_names():
    try:
        data = request.json 
        ptype = data.get('prodType')

        if not ptype:
            return jsonify({'status': 'error', 'message': 'Product type not provided.'}), 400

        product_names = prodInventory.query.filter_by(ptype=ptype).distinct(prodInventory.pname).all()
        product_names_list = [product.pname for product in product_names]

        return jsonify({'status': 'success', 'productNames': product_names_list}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error fetching product names: {str(e)}"}), 500
