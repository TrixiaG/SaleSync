from flask import Blueprint, render_template, request, flash, jsonify, send_file, current_app
from .models import prodInventory  # Adjust this import based on your project structure
from . import db
from datetime import datetime, time
from flask_login import login_required, current_user

#for pdf generating
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle


inventory = Blueprint('inventory', __name__)

# Route to add or update product
@inventory.route('/inventory', methods=['GET', 'POST'])
@login_required
def add_or_product():
    if request.method == 'POST':

        ptype = request.form.get('prodType','').strip()
        pcode = request.form.get('prodCode','').strip()
        pname = request.form.get('prodName','').strip()
        pstock = request.form.get('prodStock','').strip()
        pprice = request.form.get('prodPrice','').strip()

        try:
            pstock = int(pstock)
        except ValueError:
            pstock = 0
        try:
            pprice = float(pprice)
        except ValueError:
            pprice = 0.0

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

#DELETE PRODUCT
@inventory.route('/inventory/delete_product', methods=['POST'])
@login_required
def delete_product():
    try:
        data = request.json
        prodCode = data.get('prodCode')

        # Fetch existing product by prodCode
        product = prodInventory.query.filter_by(pcode=prodCode).first()

        if product:
            db.session.delete(product)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Product deleted successfully.'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error deleting product: {str(e)}"}), 500
    
#update product
@inventory.route('/inventory/update_product', methods=['POST'])
@login_required
def update_product():
    try:
        data = request.json
        prodCode = data.get('prodCode')

        # Fetch existing product by prodCode
        product = prodInventory.query.filter_by(pcode=prodCode).first()

        if product:
            # Update existing product details
            product.ptype = data.get('prodType')
            product.pname = data.get('prodName')
            product.pstock = data.get('prodStock')
            product.pprice = data.get('prodPrice')
            product.ptimelog = datetime.utcnow()
            product.puserlog = current_user.eid

            db.session.commit()

            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    except Exception as e:
        return None
    
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
                'prodStock': product.pstock,
                'prodPrice' : product.pprice

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
                'prodName': product.pname,
                'prodPrice' : product.pprice
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

@inventory.route('/inventory/pdf', methods=['POST'])
def generate_pdf():
    prodType = request.json.get('prodType')
    prodCode = request.json.get('prodCode')
    prodName = request.json.get('prodName')
    
    # Fetch data from database
    query = prodInventory.query
    if prodType:
        query = query.filter(prodInventory.ptype == prodType)
    if prodCode:
        query = query.filter(prodInventory.pcode == prodCode)
    if prodName:
        query = query.filter(prodInventory.pname == prodName)
    
    inventory_data = query.all()

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    fileName = f"TCFM_Inventory_Report_{current_time}.pdf"

    # Log the filename
    current_app.logger.info(f"Generated file name: {fileName}")

    testid = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    documentTitle = 'TCFM Inventory Report'
    subTitle = f"Report Generated at {testid}"
    
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    pdf.setTitle(documentTitle)
    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawCentredString(300, 750, "THE CRAZY FISH MAN")
    pdf.drawCentredString(300, 735, "Inventory Report")
    pdf.setFont('Helvetica', 10)
    pdf.drawCentredString(300, 700, subTitle)
    
    data = [['Product Type', 'Product Code', 'Product Name', 'Stock', 'Price']]
    for item in inventory_data:
        data.append([
            item.ptype,
            item.pcode,
            item.pname,
            str(item.pstock),
            str(item.pprice)
        ])
    
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ])
    
    column_widths = [100, 100, 200, 50, 50] 

    table = Table(data, colWidths=column_widths)
    table.setStyle(table_style)
    table.wrapOn(pdf, 500, 600)
    table.drawOn(pdf, 72, 600)

    pdf.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='TCFM_Inventory_Report', mimetype='application/pdf')

#AddorReduceStocks
@inventory.route('/inventory/addreducestocks', methods=['POST'])
@login_required
def add_reduce_stocks():
    try:
        data = request.json  # Assuming data is sent as JSON from frontend

        prodCode = data.get('prodCode')
        additionalStock = data.get('additionalStock')
        prodPrice = data.get('prodPrice')

        # Fetch existing product by product code
        product = prodInventory.query.filter_by(pcode=prodCode).first()

        if product:
            # Update product stock
            product.pstock += int(additionalStock)
            product.ptimelog = datetime.utcnow()
            product.puserlog = current_user.eid
            # Update other relevant fields if needed (e.g., price)
            if prodPrice:
                product.pprice = float(prodPrice)

            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Stocks updated successfully.'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error updating stocks: {str(e)}"}), 500