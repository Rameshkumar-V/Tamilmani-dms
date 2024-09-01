from flask import request, Flask,flash
import os
# ADMIN HANDLER
from flask_admin.contrib.sqla import ModelView

# ADMIN INSIDE FORM EDITORS
from wtforms.fields import SelectField
from flask_admin.form import Select2Widget

# DATABASE HANDLER
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from wtforms.fields import FileField

# FIRE BASE FOR CLOUD STORAGE
import firebase

import threading


app = Flask(__name__)

# CONFIGURATIONS
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] =os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Temporary upload folder

db = SQLAlchemy(app)
#
# NOTE : This line help me for temporarily filefieldupload pdf stored and upl to db.
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# CONTACT MODEL
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

# CATEGORY MODEL
class Category(db.Model):
    c_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.String(30), unique=True, nullable=False)

    def __repr__(self):
        return f"Category('{self.category}')"

# DOCUMENT MODEL
class Document(db.Model):
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_filename = db.Column(db.String(100), nullable=False)  # Storing original filename
    category_id = db.Column(db.Integer, db.ForeignKey('category.c_id'), nullable=False)
    upl_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category = db.relationship('Category', backref=db.backref('documents', lazy=True))

    def __repr__(self):
        return f"Document('{self.document_filename}', '{self.upl_date}', '{self.category.category}')"

# PAGE INFORMATION MODEL
class PageInformation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    job = db.Column(db.String(100), nullable=False)
    slogan = db.Column(db.Text, nullable=False)
    aboutme = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"PageInformation('{self.name}', '{self.job}')"

# CONTACT INFO MODEL
class ContactInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"ContactInfo('{self.app_name}', '{self.link}')"
    

# PROFILE ABOUT MODEL
class ProfileAbout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.Text, nullable=False)



class Youtube(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.Text, nullable=False)
    
'''
 CUSTOMLY I AM SHOWING 
 ----------------------
'''


# for DOCUMENT
class DocumentView(ModelView):
    column_list = ['id', 'document_filename']
    form_overrides = {'document_filename': FileField}
    
    column_labels = {
        'document_filename': 'Upload Document  here',
      
    }
    form_excluded_columns = ['upl_date','signed_url']  # Excluded items

    def scaffold_form(self):
        # THIS FUNCTION SHOWING CATEGORY
        form_class = super(DocumentView, self).scaffold_form()
        form_class.category_id = SelectField('Category', widget=Select2Widget())
        return form_class
 

    def edit_form(self, obj=None):
        # THIS FUNCTION FOR EDITING AREA CATEGORY SHOWING
        form = super(DocumentView, self).edit_form(obj)
        form.category_id.choices = [(c.c_id, c.category) for c in Category.query.all()]
        return form

    def create_form(self, obj=None):
        # CATEGORIES VALUES CHOICES FOR INPUt OR CREATE AREA
        form = super(DocumentView, self).create_form(obj)
        form.category_id.choices = [(c.c_id, c.category) for c in Category.query.all()]
        return form

    def on_model_change(self, form, model, is_created):
        # AFTER FORM SUBMISSTION
        file = request.files.get('document_filename')

        if file:
               
            file_name = file.filename
            threading.Thread(target= firebase.upload_file, args=(file, file_name)).start()
            # firebase.upload_file(file, file_name)    
            model.document_filename = file.filename
    def on_model_delete(self, model):
        try:
      
            file_path =  model.document_filename
            
            try:
                threading.Thread(target= firebase.delete_file, args=(file_path)).start()
                
            except:
                flash("File Deleted")
                pass
         
        except Exception as e:
            print(f"Error deleting file: {e}")


            







