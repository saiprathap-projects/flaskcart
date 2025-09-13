from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DecimalField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from models import Base, User, Product, Order, OrderItem, get_engine
from forms import LoginForm, RegisterForm, ProductForm
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager = LoginManager(app)
    login_manager.login_view = "login"

    engine = get_engine(app.config["SQLALCHEMY_DATABASE_URI"])

    @login_manager.user_loader
    def load_user(user_id):
        with Session(engine) as db:
            return db.get(User, int(user_id))

    # --------------- Utilities ---------------
    def get_cart():
        return session.setdefault("cart", {})

    def save_cart(cart):
        session["cart"] = cart
        session.modified = True

    # --------------- Routes ---------------
    @app.get("/")
    def index():
        q = request.args.get("q", "").strip()
        with Session(engine) as db:
            stmt = select(Product)
            if q:
                stmt = stmt.where(func.lower(Product.name).contains(q.lower()))
            products = db.scalars(stmt.order_by(Product.created_at.desc())).all()
        return render_template("index.html", products=products, q=q)

    @app.get("/product/<int:pid>")
    def product_detail(pid):
        with Session(engine) as db:
            product = db.get(Product, pid)
            if not product:
                abort(404)
        return render_template("product_detail.html", product=product)

    @app.post("/cart/add/<int:pid>")
    def cart_add(pid):
        qty = int(request.form.get("qty", 1))
        with Session(engine) as db:
            product = db.get(Product, pid)
            if not product:
                abort(404)
        cart = get_cart()
        cart[str(pid)] = cart.get(str(pid), 0) + qty
        save_cart(cart)
        flash("Added to cart.", "success")
        return redirect(url_for("cart_view"))

    @app.get("/cart")
    def cart_view():
        cart = get_cart()
        product_ids = [int(pid) for pid in cart.keys()]
        items = []
        total = 0
        with Session(engine) as db:
            if product_ids:
                products = db.scalars(select(Product).where(Product.id.in_(product_ids))).all()
                product_map = {p.id: p for p in products}
                for pid_str, qty in cart.items():
                    pid = int(pid_str)
                    p = product_map.get(pid)
                    if p:
                        line_total = p.price * qty
                        total += line_total
                        items.append({"product": p, "qty": qty, "line_total": line_total})
        return render_template("cart.html", items=items, total=total)

    @app.post("/cart/update")
    def cart_update():
        cart = {}
        for key, val in request.form.items():
            if key.startswith("qty_"):
                pid = key.split("_", 1)[1]
                try:
                    qty = max(0, int(val))
                except ValueError:
                    qty = 0
                if qty > 0:
                    cart[pid] = qty
        save_cart(cart)
        flash("Cart updated.", "info")
        return redirect(url_for("cart_view"))

    @app.post("/cart/clear")
    def cart_clear():
        save_cart({})
        flash("Cart cleared.", "info")
        return redirect(url_for("cart_view"))

    @app.route("/checkout", methods=["GET", "POST"])
    @login_required
    def checkout():
        cart = get_cart()
        if request.method == "POST":
            if not cart:
                flash("Your cart is empty.", "warning")
                return redirect(url_for("index"))
            with Session(engine) as db:
                # mock payment success
                order = Order(user_id=current_user.id)
                db.add(order)
                db.flush()
                product_ids = [int(pid) for pid in cart.keys()]
                products = db.scalars(select(Product).where(Product.id.in_(product_ids))).all()
                product_map = {p.id: p for p in products}
                total = 0
                for pid_str, qty in cart.items():
                    pid = int(pid_str)
                    p = product_map.get(pid)
                    if p:
                        item = OrderItem(order_id=order.id, product_id=p.id, quantity=qty, unit_price=p.price)
                        db.add(item)
                        total += p.price * qty
                order.total_amount = total
                db.commit()
            save_cart({})
            return redirect(url_for("order_success", oid=order.id))
        # GET
        return render_template("checkout.html")

    @app.get("/order/success/<int:oid>")
    @login_required
    def order_success(oid):
        with Session(engine) as db:
            order = db.get(Order, oid)
            if not order or order.user_id != current_user.id:
                abort(404)
        return render_template("order_success.html", order=order)

    # --------------- Auth ---------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            with Session(engine) as db:
                user = db.scalars(select(User).where(User.email == form.email.data.lower())).first()
                if user and check_password_hash(user.password_hash, form.password.data):
                    login_user(user, remember=form.remember.data)
                    flash("Welcome back!", "success")
                    return redirect(request.args.get("next") or url_for("index"))
            flash("Invalid credentials.", "danger")
        return render_template("login.html", form=form)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        form = RegisterForm()
        if form.validate_on_submit():
            with Session(engine) as db:
                existing = db.scalars(select(User).where(User.email == form.email.data.lower())).first()
                if existing:
                    flash("Email already registered.", "warning")
                else:
                    user = User(
                        email=form.email.data.lower(),
                        name=form.name.data.strip(),
                        password_hash=generate_password_hash(form.password.data)
                    )
                    db.add(user)
                    db.commit()
                    flash("Registration successful. Please log in.", "success")
                    return redirect(url_for("login"))
        return render_template("register.html", form=form)

    @app.get("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out.", "info")
        return redirect(url_for("index"))

    # --------------- Admin ---------------
    def admin_required():
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)

    @app.get("/admin/products")
    @login_required
    def admin_products():
        admin_required()
        with Session(engine) as db:
            products = db.scalars(select(Product).order_by(Product.created_at.desc())).all()
        return render_template("admin_products.html", products=products)

    @app.route("/admin/products/new", methods=["GET", "POST"])
    @login_required
    def admin_product_new():
        admin_required()
        form = ProductForm()
        if form.validate_on_submit():
            with Session(engine) as db:
                product = Product(
                    name=form.name.data.strip(),
                    description=form.description.data.strip(),
                    price=form.price.data,
                    stock=form.stock.data,
                    image_url=form.image_url.data.strip() or None,
                )
                db.add(product)
                db.commit()
                flash("Product created.", "success")
                return redirect(url_for("admin_products"))
        return render_template("admin_product_form.html", form=form, mode="new")

    @app.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
    @login_required
    def admin_product_edit(pid):
        admin_required()
        with Session(engine) as db:
            product = db.get(Product, pid)
            if not product:
                abort(404)
            form = ProductForm(obj=product)
            if form.validate_on_submit():
                form.populate_obj(product)
                db.commit()
                flash("Product updated.", "success")
                return redirect(url_for("admin_products"))
        return render_template("admin_product_form.html", form=form, mode="edit", pid=pid)

    @app.post("/admin/products/<int:pid>/delete")
    @login_required
    def admin_product_delete(pid):
        admin_required()
        with Session(engine) as db:
            product = db.get(Product, pid)
            if product:
                db.delete(product)
                db.commit()
        flash("Product deleted.", "info")
        return redirect(url_for("admin_products"))

    return app

app = create_app()
