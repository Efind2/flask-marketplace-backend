from flask import Blueprint, request, jsonify, g, current_app
from app.models.product import Product, Category, Brand, ProductImage, Inventory
from app.routes.users import token_required, role_required
from app.services.activity_service import ActivityService
from app.schemas.product_schema import product_schema, products_schema
from app import db
from functools import wraps
from app.services.auth_service import AuthService
from sqlalchemy import desc, asc
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone # <-- Correct import for datetime and timezone

products_bp = Blueprint('products', __name__)

# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         auth_header = request.headers.get('Authorization')
#         if not auth_header:
#             return jsonify({"message": "Header otorisasi tidak ditemukan"}), 401

#         try:
#             token_type, token = auth_header.split(' ', 1)
#             if token_type.lower() != 'bearer':
#                 raise ValueError("Tipe token tidak valid. Gunakan 'Bearer'.")
#         except ValueError:
#             return jsonify({"message": "Format header otorisasi tidak valid. Gunakan 'Bearer <token>'."}), 401

#         current_user = AuthService.verify_auth_token(token)

#         if not current_user:
#             return jsonify({"message": "Token tidak valid atau kadaluwarsa"}), 401

#         # Perbaiki bagian ini:
#         return f(current_user, *args, **kwargs)
#     return decorated



@products_bp.route('/', methods=['GET'])
def list_products():
    """
    Endpoint untuk menampilkan daftar produk dengan pagination, sorting, dan multi-filter.
    Parameter query:
    - page (int): Nomor halaman. Default 1.
    - per_page (int): Jumlah item per halaman. Default dari config.
    - category_id (int): Filter berdasarkan ID kategori.
    - brand_id (int): Filter berdasarkan ID merek.
    - min_price (float): Filter harga minimal.
    - max_price (float): Filter harga maksimal.
    - search (str): Pencarian berdasarkan nama atau deskripsi produk (case-insensitive).
    - sort_by (str): Kolom untuk sorting (contoh: 'name', 'price', 'created_at', 'stock'). Bisa multiple, dipisahkan koma.
    - sort_order (str): Urutan sorting ('asc' atau 'desc'). Bisa multiple, dipisahkan koma, sesuai dengan sort_by.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config['DEFAULT_PAGE_SIZE'], type=int)

    if per_page > current_app.config['MAX_PAGE_SIZE']:
        per_page = current_app.config['MAX_PAGE_SIZE']
    elif per_page < 1:
        per_page = 1

    query = Product.query

    category_id = request.args.get('category_id', type=int)
    brand_id = request.args.get('brand_id', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    search_term = request.args.get('search', type=str)

    if category_id:
        query = query.filter_by(category_id=category_id)
    if brand_id:
        query = query.filter_by(brand_id=brand_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if search_term:
        search_pattern = f"%{search_term}%"
        query = query.filter(
            (Product.name.ilike(search_pattern)) |
            (Product.description.ilike(search_pattern))
        )

    sort_by_param = request.args.get('sort_by', 'created_at')
    sort_order_param = request.args.get('sort_order', 'desc')

    ALLOWED_SORT_COLUMNS = {
        'name': Product.name,
        'price': Product.price,
        'created_at': Product.created_at,
        'stock': Inventory.quantity
    }
    ALLOWED_SORT_ORDERS = {'asc': asc, 'desc': desc}

    sort_columns = [col.strip() for col in sort_by_param.split(',')]
    sort_orders = [order.strip() for order in sort_order_param.split(',')]

    if len(sort_columns) != len(sort_orders) and len(sort_orders) == 1:
        sort_orders = [sort_orders[0]] * len(sort_columns)
    elif len(sort_columns) != len(sort_orders):
        return jsonify({"message": "Jumlah kolom sort_by dan sort_order tidak cocok."}), 400

    order_by_clauses = []
    for i, col_name in enumerate(sort_columns):
        if col_name in ALLOWED_SORT_COLUMNS:
            order_func = ALLOWED_SORT_ORDERS.get(sort_orders[i].lower(), desc)
            order_by_clauses.append(order_func(ALLOWED_SORT_COLUMNS[col_name]))
        else:
            return jsonify({"message": f"Kolom sorting '{col_name}' tidak valid."}), 400
    
    if 'stock' in sort_columns or any(col in ALLOWED_SORT_COLUMNS for col in sort_columns if ALLOWED_SORT_COLUMNS[col] == Inventory.quantity):
        query = query.join(Inventory, Product.id == Inventory.product_id)

    if order_by_clauses:
        query = query.order_by(*order_by_clauses)

    query = query.options(
        joinedload(Product.category),
        joinedload(Product.brand),
        joinedload(Product.images),
        joinedload(Product.inventory)
    )

    products_pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    products_list = products_schema.dump(products_pagination.items)
    
    return jsonify({
        "products": products_list,
        "total_items": products_pagination.total,
        "total_pages": products_pagination.pages,
        "current_page": products_pagination.page,
        "per_page": products_pagination.per_page,
        "has_next": products_pagination.has_next,
        "has_prev": products_pagination.has_prev
    }), 200


# @products_bp.route('/products/create', methods=['POST'])
# @token_required()
# def create_product():
#     current_user_id = get_jwt_identity()

#     brand = Brand.query.filter_by(user_id=current_user_id).first()
#     if not brand:
#         return jsonify({"message": "Hanya penjual yang dapat membuat produk. Anda belum memiliki brand."}), 403

#     data = request.get_json()
#     if not data:
#         return jsonify({"message": "Permintaan harus dalam format JSON."}), 400

#     name = data.get('name')
#     description = data.get('description')
#     price = data.get('price')
#     stock = data.get('stock')
#     image_url = data.get('image_url') # Tangkap URL gambar

#     # Validasi dasar
#     if not name or not price or price <= 0 or not image_url:
#         return jsonify({"message": "Nama produk, harga, dan URL gambar wajib diisi."}), 400
#     if not isinstance(price, (int, float)):
#         return jsonify({"message": "Harga harus berupa angka."}), 400
#     if stock is not None and not isinstance(stock, int):
#         return jsonify({"message": "Stok harus berupa bilangan bulat atau kosong."}), 400

#     try:
#         new_product = Product(
#             name=name,
#             description=description,
#             price=price,
#             stock=stock if stock is not None else 0,
#             image_url=image_url,
#             brand_id=brand.id # Kaitkan dengan brand penjual
#         )
#         db.session.add(new_product)
#         db.session.commit()
#         return jsonify({"message": "Produk berhasil dibuat!", "product_id": new_product.id}), 201
#     except Exception as e:
#         db.session.rollback()
#         print(f"Error creating product: {e}")
#         return jsonify({"message": "Terjadi kesalahan server saat membuat produk."}), 500


@products_bp.route('/<int:product_id>', methods=['GET'])
@token_required
def get_product_detail(current_user, product_id):
    """
    Endpoint untuk mendapatkan detail produk berdasarkan ID.
    """
    product = Product.query.options(
        joinedload(Product.category),
        joinedload(Product.brand),
        joinedload(Product.images),
        joinedload(Product.inventory)
    ).get(product_id)

    if not product:
        return jsonify({"message": "Produk tidak ditemukan"}), 404
    
    if hasattr(g, 'current_user'):
        ActivityService.log_user_activity(
            user_id=g.current_user.id,
            activity_type='view_product',
            related_type='product',
            related_id=product.id
        )

    response_data = product_schema.dump(product)
    
    return jsonify(response_data), 200

@products_bp.route('/create', methods=['POST']) # Mungkin lebih jelas pakai /create
@token_required
@role_required('penjual') # Asumsi role_required decorator Anda berfungsi
def create_product(current_user_from_decorator):
    try:
        user = current_user_from_decorator
        user_from_g = g.current_user # User object dari decorator token_required

        # Cek apakah user memiliki brand (role penjual)
        brand = Brand.query.filter_by(owner_id=user.id).first() # Asumsi 'owner_id' di Brand model
        if not brand:
            return jsonify({"message": "Penjual belum memiliki brand"}), 400

        # Menerima data dari form-data (bukan JSON)
        name = request.form.get('name')
        description = request.form.get('description')
        price_str = request.form.get('price') # Ambil sebagai string
        category_id_str = request.form.get('category_id') # Ambil sebagai string
        initial_stock_str = request.form.get('stock') # SESUAIKAN DENGAN NAMA DI ANDROID: 'stock'
        # main_image_url_input sekarang akan diganti dengan file
        main_image_file = request.files.get('main_image') # NAMA FIELD FILE: 'main_image'

        # Validasi Input Dasar
        if not name or not price_str or not initial_stock_str or not main_image_file:
            return jsonify({"message": "Nama produk, harga, stok awal, dan gambar utama wajib diisi."}), 400

        try:
            price = float(price_str)
            initial_stock = int(initial_stock_str)
        except ValueError:
            return jsonify({"message": "Harga atau Stok tidak valid. Pastikan berupa angka."}), 400

        category_id = int(category_id_str) if category_id_str else None

        # Cek kategori valid
        if category_id and not Category.query.get(category_id):
            return jsonify({"message": "category_id tidak valid."}), 400
            
        # LOGIKA UPLOAD GAMBAR UTAMA
        image_url = None
        if main_image_file:
            # TODO: Implementasikan logika penyimpanan file di sini
            # 1. Validasi ekstensi file (misal: .jpg, .png)
            # 2. Hasilkan nama file unik (UUID + ekstensi)
            # 3. Simpan file ke lokasi penyimpanan (server lokal, S3, GCS, Cloudinary, dll.)
            #    Untuk proyek kecil/dev: bisa simpan di folder static/uploads di Flask
            #    Untuk produksi: sangat direkomendasikan layanan penyimpanan awan
            
            # Contoh sederhana penyimpanan lokal (untuk DEVELOPMENT SAJA)
            # Pastikan Anda punya folder 'static/uploads' di root proyek Flask Anda
            # dan pastikan file 'config.py' memiliki UPLOAD_FOLDER
            try:
                from werkzeug.utils import secure_filename
                import os
                import uuid

                # Dapatkan ekstensi file asli
                ext = os.path.splitext(main_image_file.filename)[1]
                # Buat nama file unik
                unique_filename = str(uuid.uuid4()) + ext
                # Path lengkap untuk menyimpan file
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                main_image_file.save(upload_path)
                image_url = f"{request.url_root.strip('/')}/static/uploads/{unique_filename}" # URL yang akan disimpan
                
            except Exception as e:
                current_app.logger.error(f"Error saving image: {e}")
                return jsonify({"message": "Gagal menyimpan gambar produk."}), 500

        if not image_url:
            return jsonify({"message": "Gagal mendapatkan URL gambar setelah upload."}), 500

        new_product = Product(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            brand_id=brand.id # Kaitkan dengan brand penjual
        )
        db.session.add(new_product)
        db.session.flush() # Mendapatkan new_product.id sebelum commit

        new_inventory = Inventory(
            product_id=new_product.id,
            quantity=initial_stock
        )
        db.session.add(new_inventory)

        new_image = ProductImage( # Simpan URL gambar utama ke tabel ProductImage
            product_id=new_product.id,
            image_url=image_url,
            is_main=True
        )
        db.session.add(new_image)

        db.session.commit()

        ActivityService.log_user_activity(user.id, 'create_product', 'product', new_product.id)

        # Mengembalikan respons yang sederhana dan informatif untuk klien mobile
        return jsonify({
            "message": "Produk berhasil dibuat!",
            "product_id": new_product.id,
            "product_name": new_product.name,
            "main_image_url": image_url # Mengembalikan URL gambar yang disimpan
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Gagal membuat produk. Nama produk mungkin sudah dipakai."}), 409
    except Exception as e:
        db.session.rollback()
        print("ERROR (create_product):", e)
        current_app.logger.error(f"Error creating product: {e}")
        return jsonify({"message": f"Terjadi kesalahan server: {e}"}), 500

@products_bp.route('/my-brand', methods=['GET'])
@token_required
def get_products_by_my_brand(current_user):
    brand = Brand.query.filter_by(owner_id=current_user.id).first()
    if not brand:
        return jsonify({"message": "Brand not found"}), 404

    products = Product.query.filter_by(brand_id=brand.id).all()

    result = []
    for product in products:
        result.append({
    "id": product.id,
    "name": product.name,
    "description": product.description,
    "price": float(product.price),
    "stock": product.inventory.quantity if product.inventory else 0,
    "brand": {
        "id": product.brand.id,
        "name": product.brand.name,
        "description": product.brand.description
    },
    "images": [
        {
            "id": img.id,
            "image_url": img.image_url,
            "is_main": img.is_main
        } for img in product.images
    ]
})

    return jsonify(result), 200
