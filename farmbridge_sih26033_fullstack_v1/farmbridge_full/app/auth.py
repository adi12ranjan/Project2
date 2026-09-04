from functools import wraps
from flask import request,jsonify,g
from itsdangerous import URLSafeTimedSerializer,BadSignature,SignatureExpired
SECRET='farmbridge-demo-secret-change-me'
def make_token(user_id): return URLSafeTimedSerializer(SECRET).dumps({'user_id':user_id})
def user_id_from_token():
    h=request.headers.get('Authorization','')
    if not h.startswith('Bearer '): return None
    try: return URLSafeTimedSerializer(SECRET).loads(h[7:].strip(),max_age=604800).get('user_id')
    except (BadSignature,SignatureExpired): return None
def login_required(fn):
    @wraps(fn)
    def w(*a,**kw):
        uid=user_id_from_token()
        if not uid:return jsonify({'error':'Authentication required'}),401
        g.user_id=int(uid); return fn(*a,**kw)
    return w
