from flask import Blueprint,request,jsonify,g
from werkzeug.security import generate_password_hash,check_password_hash
from .db import get_db
from .auth import make_token,login_required
api=Blueprint('api',__name__)
def d(r): return dict(r) if r else None
@api.post('/auth/register')
def register():
 x=request.get_json(silent=True) or {}; name=str(x.get('name','')).strip(); phone=str(x.get('phone','')).strip(); pw=str(x.get('password','')); role=str(x.get('role','')).lower().strip(); loc=str(x.get('location','')).strip()
 if not name or not phone or len(pw)<6 or role not in ('farmer','consumer'): return jsonify({'error':'name, phone, role and password (6+ chars) are required'}),400
 db=get_db()
 try: c=db.execute('INSERT INTO users(name,phone,password_hash,role,location) VALUES(?,?,?,?,?)',(name,phone,generate_password_hash(pw),role,loc)); db.commit()
 except Exception:return jsonify({'error':'Phone number is already registered'}),409
 return jsonify({'message':'Registration successful','token':make_token(c.lastrowid),'user':{'id':c.lastrowid,'name':name,'phone':phone,'role':role,'location':loc}}),201
@api.post('/auth/login')
def login():
 x=request.get_json(silent=True) or {}; u=get_db().execute('SELECT * FROM users WHERE phone=?',(str(x.get('phone','')).strip(),)).fetchone()
 if not u or not check_password_hash(u['password_hash'],str(x.get('password',''))):return jsonify({'error':'Invalid phone or password'}),401
 return jsonify({'message':'Login successful','token':make_token(u['id']),'user':{k:u[k] for k in ('id','name','phone','role','location')}})
@api.get('/me')
@login_required
def me(): return jsonify(d(get_db().execute('SELECT id,name,phone,role,location,created_at FROM users WHERE id=?',(g.user_id,)).fetchone()))
@api.get('/produce')
def produce():
 crop=request.args.get('crop','').strip(); loc=request.args.get('location','').strip(); sql="SELECT p.*,u.name farmer_name FROM produce p JOIN users u ON u.id=p.farmer_id WHERE p.status='available'"; ps=[]
 if crop:sql+=' AND LOWER(p.crop_name) LIKE LOWER(?)';ps.append('%'+crop+'%')
 if loc:sql+=' AND LOWER(p.location) LIKE LOWER(?)';ps.append('%'+loc+'%')
 rows=get_db().execute(sql+' ORDER BY p.created_at DESC',ps).fetchall(); return jsonify([d(r) for r in rows])
@api.post('/produce')
@login_required
def add_produce():
 db=get_db();u=db.execute('SELECT role,location FROM users WHERE id=?',(g.user_id,)).fetchone()
 if not u or u['role']!='farmer':return jsonify({'error':'Only farmers can list produce'}),403
 x=request.get_json(silent=True) or {}
 try:q=float(x['quantity_kg']);p=float(x['asking_price'])
 except(KeyError,TypeError,ValueError):return jsonify({'error':'quantity_kg and asking_price must be numbers'}),400
 crop=str(x.get('crop_name','')).strip()
 if not crop or q<=0 or p<0:return jsonify({'error':'Valid crop, quantity and price are required'}),400
 c=db.execute('INSERT INTO produce(farmer_id,crop_name,quantity_kg,asking_price,description,location) VALUES(?,?,?,?,?,?)',(g.user_id,crop,q,p,str(x.get('description','')),str(x.get('location',u['location'] or ''))));db.commit()
 return jsonify(d(db.execute('SELECT p.*,u.name farmer_name FROM produce p JOIN users u ON u.id=p.farmer_id WHERE p.id=?',(c.lastrowid,)).fetchone())),201
@api.get('/produce/mine')
@login_required
def mine():return jsonify([d(r) for r in get_db().execute('SELECT * FROM produce WHERE farmer_id=? ORDER BY created_at DESC',(g.user_id,)).fetchall()])
@api.get('/price-suggestion')
def price():
 crop=request.args.get('crop','').lower().strip()
 try:q=max(float(request.args.get('quantity_kg','1')),1)
 except:q=1
 ref={'cabbage':42,'tomato':44,'tomatoes':44,'sweet corn':52,'corn':52,'potato':32,'onion':36,'rice':48,'maize':30}; base=ref.get(crop,40); s=round(base*(1-min(q/5000,.08)),2)
 return jsonify({'crop':crop,'quantity_kg':q,'suggested_price_per_kg':s,'currency':'INR','source':'demo-estimator','note':'Replace with the trained AGMARKNET price model.'})
@api.post('/orders')
@login_required
def order():
 db=get_db();u=db.execute('SELECT role FROM users WHERE id=?',(g.user_id,)).fetchone()
 if not u or u['role']!='consumer':return jsonify({'error':'Only consumers can place orders'}),403
 x=request.get_json(silent=True) or {}
 try:pid=int(x['produce_id']);q=float(x['quantity_kg'])
 except(KeyError,TypeError,ValueError):return jsonify({'error':'produce_id and quantity_kg are required'}),400
 item=db.execute("SELECT * FROM produce WHERE id=? AND status='available'",(pid,)).fetchone()
 if not item:return jsonify({'error':'Produce is unavailable'}),404
 if q<=0 or q>item['quantity_kg']:return jsonify({'error':'Invalid quantity or insufficient stock'}),400
 total=round(q*item['asking_price'],2); c=db.execute('INSERT INTO orders(produce_id,consumer_id,quantity_kg,total_amount) VALUES(?,?,?,?)',(pid,g.user_id,q,total)); rem=item['quantity_kg']-q;db.execute('UPDATE produce SET quantity_kg=?,status=? WHERE id=?',(rem,'sold' if rem<=0 else 'available',pid));db.commit()
 return jsonify({'id':c.lastrowid,'produce_id':pid,'quantity_kg':q,'total_amount':total,'status':'placed'}),201
@api.get('/orders')
@login_required
def orders():
 rows=get_db().execute('''SELECT o.*,p.crop_name,p.location,f.name farmer_name,c.name consumer_name FROM orders o JOIN produce p ON p.id=o.produce_id JOIN users f ON f.id=p.farmer_id JOIN users c ON c.id=o.consumer_id WHERE o.consumer_id=? OR p.farmer_id=? ORDER BY o.created_at DESC''',(g.user_id,g.user_id)).fetchall();return jsonify([d(r) for r in rows])
@api.patch('/orders/<int:oid>')
@login_required
def update(oid):
 s=str((request.get_json(silent=True) or {}).get('status','')).lower(); allowed={'accepted','packed','shipped','delivered','cancelled'}
 if s not in allowed:return jsonify({'error':'Invalid status'}),400
 db=get_db();o=db.execute('SELECT o.*,p.farmer_id FROM orders o JOIN produce p ON p.id=o.produce_id WHERE o.id=?',(oid,)).fetchone()
 if not o:return jsonify({'error':'Order not found'}),404
 if g.user_id not in (o['consumer_id'],o['farmer_id']):return jsonify({'error':'Not allowed'}),403
 db.execute('UPDATE orders SET status=? WHERE id=?',(s,oid));db.commit();return jsonify({'message':'Order updated','status':s})
