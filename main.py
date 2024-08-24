from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, Date
from datetime import date
from forms import ToDoForm, RegisterForm, LoginForm, NewToDoForm


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class ToDo(db.Model):
    __tablename__ = "todoList"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    erased: Mapped[bool] = mapped_column(Boolean, nullable=False)
    color: Mapped[str] = mapped_column(String(10), default="grey")
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="todos")
    list_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("lists.id"))
    list_name = relationship("List", back_populates="todos")

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    todos = relationship("ToDo", back_populates="user")
    lists = relationship("List", back_populates="user")


class List(db.Model):
    __tablename__ = "lists"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_name: Mapped[str] = mapped_column(String(250), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="lists")
    todos = relationship("ToDo", back_populates="list_name")


with app.app_context():
    db.create_all()


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("saved_lists"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('saved_lists'))

    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/lists', methods=['GET', 'POST'])
@login_required
def saved_lists():
    result = db.session.execute(db.select(List).where(List.user == current_user))
    all_lists = result.scalars().all()
    return render_template("lists.html", lists=all_lists, current_user=current_user)


@app.route('/todos/<int:list_id>', methods=['GET', 'POST'])
@login_required
def home_lists(list_id):
    form = ToDoForm()
    user_list = db.session.execute(db.select(List).where(List.id == list_id, List.user == current_user)).scalar()

    if not user_list:
        flash("You are not allowed to see this list.")
        return redirect(url_for('saved_lists'))

    if form.validate_on_submit():
        to_do_item = form.to_do.data
        date_to_do = form.date_to_do.data
        new_todo = ToDo(name=to_do_item, date=date_to_do, erased=False, user=current_user, list_id=list_id)
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for('home_lists', list_id=list_id))

    todos = db.session.execute(db.select(ToDo).where(ToDo.list_id == list_id)).scalars().all()

    print(f"Fetched {len(todos)} todos for list_id {list_id}")

    return render_template('index.html', form=form, todos=todos, current_user=current_user, list=user_list)


@app.route('/new_list', methods=['GET', 'POST'])
@login_required
def home():
    form = NewToDoForm()
    if form.validate_on_submit():
        list_name = form.list_name.data
        to_do_item = form.to_do.data
        date_to_do = form.date_to_do.data
        list_instance = db.session.query(List).filter_by(list_name=list_name, user=current_user).first()
        if list_instance is None:
            list_instance = List(list_name=list_name, user=current_user)
            db.session.add(list_instance)
            db.session.commit()

        new_todo = ToDo(name=to_do_item, date=date_to_do, erased=False, user=current_user, list_name=list_instance)
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for('home_lists', list_id=list_instance.id))

    return render_template('new_list.html', form=form, current_user=current_user)


@app.route('/done/<int:todo_id>/<int:list_id>', methods=['GET', 'POST'])
@login_required
def done_todo(todo_id, list_id):
    todo_to_done = db.session.query(ToDo).get(todo_id)
    todo_to_done.erased = True
    db.session.commit()
    return redirect(url_for('home_lists', user=current_user, list_id=list_id))


@app.route('/undone/<int:todo_id>/<int:list_id>>', methods=['GET', 'POST'])
@login_required
def undo(todo_id, list_id):
    todo_to_undo = db.session.query(ToDo).get(todo_id)
    todo_to_undo.erased = False
    db.session.commit()
    return redirect(url_for('home_lists', user=current_user, list_id=list_id))


@app.route('/delete/<int:list_id>')
@login_required
def delete(list_id):
    todo_id = request.args.get('id')
    todo_to_delete = db.session.execute(db.select(ToDo).where(ToDo.id == todo_id)).scalar()
    db.session.delete(todo_to_delete)
    db.session.commit()
    return redirect(url_for('home_lists', user=current_user, list_id=list_id))


@app.route('/delete_list')
@login_required
def delete_list():
    list_id = request.args.get('id')
    todos_to_delete = db.session.execute(db.select(ToDo).where(ToDo.list_id == list_id)).scalars().all()
    for todo in todos_to_delete:
        db.session.delete(todo)
    list_to_delete2 = db.session.execute(db.select(List).where(List.id == list_id)).scalar()
    db.session.delete(list_to_delete2)
    db.session.commit()
    return redirect(url_for('saved_lists', user=current_user))


@app.route('/change_color/<int:todo_id>/<int:list_id>', methods=['POST'])
@login_required
def change_color(todo_id, list_id):
    todo = db.session.get(ToDo, todo_id)
    if todo:
        new_color = request.form['color']
        todo.color = new_color
        db.session.commit()
    return redirect(url_for('home_lists', user=current_user, list_id=list_id))


if __name__ == '__main__':
    app.run(debug=True, port=5003)
