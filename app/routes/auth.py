from flask import Blueprint, request, jsonify, g
from functools import wraps
from app.services.auth_service import AuthService
from app.schemas.user_schema import UserSchema
from app import db 
from app.models.product import Brand

auth_bp = Blueprint('auth', __name__)
user_schema = UserSchema()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"message": "Header otorisasi tidak ditemukan"}), 401

        try:
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                raise ValueError("Tipe token tidak valid. Gunakan 'Bearer'.")
        except ValueError:
            return jsonify({"message": "Format header otorisasi tidak valid. Gunakan 'Bearer <token>'."}), 401

        current_user = AuthService.verify_auth_token(token)

        if not current_user:
            return jsonify({"message": "Token tidak valid atau kadaluwarsa"}), 401

        # Perbaiki bagian ini:
        return f(current_user, *args, **kwargs)
    return decorated

# --- Decorator untuk otorisasi peran ---
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({"message": "Pengguna tidak terotentikasi"}), 401
            
            if g.current_user.role != required_role:
                return jsonify({"message": "Tidak diizinkan. Peran tidak sesuai."}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Endpoint untuk registrasi pengguna baru.
    Menerima password plain-text melalui HTTPS.
    """
    try:
        user_data = user_schema.load(request.get_json())
        email = user_data['email']
        password = user_data['password']
        name = user_data.get('name')

        user, error_message = AuthService.register_user(email, password, name)

        if user:
            user_response = {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
            return jsonify({
                "message": "Registrasi berhasil",
                "user": user_response
            }), 201
        else:
            return jsonify({"message": error_message}), 409

    except Exception as e:
        return jsonify({"message": str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint untuk login pengguna.
    Menerima password plain-text melalui HTTPS dan mengembalikan token mobile.
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    client_type = data.get('client_type', 'mobile')

    if not email or not password:
        return jsonify({"message": "Email dan password wajib diisi"}), 400

    if client_type not in ["mobile"]:
        return jsonify({"message": "Jenis klien tidak valid atau tidak didukung"}), 400

    auth_result, error_message = AuthService.login_user(email, password, client_type)

    if auth_result:
        user = auth_result['user']
        return jsonify({
            "message": "Login berhasil",
            "user_role": auth_result['role'],
            "auth_token": auth_result['token'],
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }), 200
    else:
        return jsonify({"message": error_message}), 401

@auth_bp.route('/open_store', methods=['POST'])
@token_required
def open_store(current_user):
    user = current_user

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    if not name:
        return jsonify({"message": "Nama brand wajib diisi"}), 400

    # Cek apakah nama brand sudah dipakai
    existing_brand = Brand.query.filter_by(name=name).first()
    if existing_brand:
        return jsonify({"message": "Nama brand sudah digunakan"}), 409

    # Update role user jadi penjual kalau belum
    if user.role != 'penjual':
        user.role = 'penjual'
        db.session.commit()

    # Buat brand baru
    brand = Brand(name=name, description=description, owner_id=user.id)
    db.session.add(brand)
    db.session.commit()

    return jsonify({
        "message": "Brand berhasil dibuat dan role pengguna diperbarui",
        "brand": {
            "id": brand.id,
            "name": brand.name,
            "description": brand.description
        },
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role
        }
    }), 201

@auth_bp.route('/brands/my', methods=['GET'])
@token_required
def get_my_brand(current_user):
    brand = Brand.query.filter_by(owner_id=current_user.id).first()
    if brand:
        return jsonify({
            'id': brand.id,
            'name': brand.name,
            'description': brand.description
        }), 200
    else:
        return jsonify({'message': 'Brand not found'}), 404
