
# FLASK ATTRIBUTES
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_file,
    flash
)
# ENVIRONMENT LOADER
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
# IMAGE BYTES HANDLER
import io

# DATABASE ORM HANDLER
from sqlalchemy import desc


# PAGINATION HANDLER
from flask_paginate import Pagination, get_page_args

# SECURITY HASH PASSWORD HANDLER
from werkzeug.security import check_password_hash, generate_password_hash

# DATABASE MODULE HANDLER ( OUR MODULE )
from database import db, Contact, Document, Category, ContactInfo, PageInformation,DocumentView,ProfileAbout,Youtube

# AUTHENTICATION AND LOGIN HANDLER
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user,login_required

# FLASK ADMIN HANDLER
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, Admin
# NOTE : FORM OPERATION 
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
import firebase



app = Flask(__name__, template_folder='template')

# Configuration
# app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///project.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# INITIALIZE DB
db.init_app(app)


login = LoginManager(app)



'''
ADMIN SECTION

'''
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# RE CONFIGURE MODELVIEW
class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class MyAdminIndexView(AdminIndexView):
    @login_required
    def is_accessible(self):
        return current_user.is_authenticated
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))



# ADMIN INITIALIZING
db_admin = Admin(app, name='Dashboard', template_mode='bootstrap3',index_view=MyAdminIndexView())

# NOTE : add_view used to add db_admin pannel inside model based CRUD operations.

db_admin.add_view(DocumentView(Document, db.session))
db_admin.add_view(ModelView(Category, db.session))
db_admin.add_view(ModelView(Contact, db.session))
db_admin.add_view(ModelView(PageInformation, db.session))
db_admin.add_view(ModelView(ContactInfo, db.session))
db_admin.add_view(ModelView(ProfileAbout, db.session))
db_admin.add_view(ModelView(Youtube, db.session))
db_admin.add_view(MyModelView(User, db.session))




@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
'''
END OF ADMIN SECTION

'''


# HOME PAGE
@app.route('/')
def home():
    
    page_data = PageInformation.query.first()
    contact_info_data = ContactInfo.query.all()
    categories = Category.query.all()
    youtube =   Youtube.query.order_by(desc(Youtube.id)).limit(4).all()
    
    return render_template('home.html', categories=categories, contact=contact_info_data, page_info=page_data,youtube=youtube)



# THANKYOU FOR CONTACT US
@app.route('/thank_you')
def thank_you():
    return "<h1>Thank you for your message! We'll get back to you soon.</h1>"


# DOCUMENT GETTING
def get_documents(page, per_page, category_id=None, search_term=None):
    query = Document.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    if search_term:
        query = query.filter(Document.document_filename.ilike(f'%{search_term}%'))
    return query.paginate(page=page, per_page=per_page, error_out=False)

# YOUTUBE URL GETTING
def get_urls(page=1, per_page=10, search_term=None):
    
    if search_term:
        print('serch_term : ',search_term)
        return Youtube.query.filter(Youtube.title.ilike(f'%{search_term}%'))
    
    # Apply pagination to the filtered (or unfiltered) query
    pagination =  Youtube.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return pagination

# DOWNLOAD PAGE
@app.route('/download_page')
def download_page():
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page',1,type=int)
    per_page = request.args.get('per_page',9,type=int)
    documents = get_documents(page, per_page, category_id)
    
    return render_template('download_page.html', documents=documents.items, pagination=documents,  current_category=category_id)

# DOWNLOAD PAGE

@app.route('/youtube_page')
def youtube_page():
    
    page = request.args.get('page',1,type=int)
    per_page = request.args.get('per_page',9,type=int)
   
    # Note : documents_query holds items and pagination object
    documents_query = get_urls(page,per_page,search_term=None)
    print('document : ',documents_query)
   
    return render_template('youtube_page.html', documents=documents_query.items, pagination=documents_query, current_category=None)

# SEARCH ROUTE
@app.route('/search')
def search_documents():
    search_term = request.args.get('q', '').strip()
    if not search_term:
        return render_template('document_list.html', documents=None)
    
    documents=get_documents(1,2,search_term=search_term)
    
    return render_template('document_list.html', documents=documents)


# SEARCH ROUTE
@app.route('/youtube_search')
def youtube_search():
    search_term = request.args.get('q', '').strip()
    if not search_term:
        return render_template('document_list.html', documents=None)
    documents=get_urls(search_term=search_term)

    
    return render_template('youtube_com.html', documents=documents)

# DOCUMENT GETTING WITH ID FOR DOWNLOAD
@app.route('/get_document', methods=['GET'])
def get_document():
    document_id = request.args.get('document_id')
    if not document_id:
        return jsonify({'error': 'No document ID provided'}), 400
    
    document_detail = Document.query.get(document_id)
    document = firebase.get_file(document_detail.document_filename)
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    return redirect(document)



# CONTACT US PAGE TO DB ROUTE
@app.route('/submit_contact_form', methods=['POST'])
def submit_contact_form():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    if name and email and message:
        new_contact = Contact(name=name, email=email, message=message)
        db.session.add(new_contact)
        db.session.commit()
    return redirect(url_for('thank_you'))
    

# NOTE : PROFILE ABOUT PAGE
# -------------------------
@app.route('/profile')
def profile():

    profiles = ProfileAbout.query.all()
    
    formatted_profiles = []
    

    for profile in profiles:
        formatted_profile = {
            'title': profile.title,
            # Replace \n with <br> tags
            'detail': profile.detail.split('/n')
        }
        print(formatted_profile)
        formatted_profiles.append(formatted_profile)
    
    return render_template('profile.html', profiles=formatted_profiles)


# NOTE : LOGIN FORM
# ------------------
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, max=25)])
    submit = SubmitField('Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            
            return redirect(url_for('admin.index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)



# LOGOUT ROUTE
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home')) 

@app.route('/settup')
def settup():
    with app.app_context():
        db.create_all()
        print("Database Created Successfully")
        if not User.query.filter_by(username='tm').first():
            new_user = User(username=os.getenv('ADMIN_USERNAME'), password = generate_password_hash(os.getenv('ADMIN_PASSWORD')))
            db.session.add(new_user)
            db.session.commit()
    return "Success"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database Created Successfully")
        if not User.query.filter_by(username='tm').first():
            new_user = User(username=os.getenv('ADMIN_USERNAME'), password = generate_password_hash(os.getenv('ADMIN_PASSWORD')))
            db.session.add(new_user)
            db.session.commit()
    app.run(debug=False,host="0.0.0.0")
