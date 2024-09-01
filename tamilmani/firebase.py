import firebase_admin
from firebase_admin import credentials, storage
from google.cloud import storage as gcs_storage
from datetime import timedelta
import os
import json
# Initialize Firebase Admin SDK
cred = credentials.Certificate(json.loads(os.getenv('FIREBASE_SECRET_KEY')))
firebase_admin.initialize_app(cred, {
    "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET')
})


bucket = storage.bucket()



def upload_file(file, file_name):
    
    try:

        blob = bucket.blob(file_name)  # Create blob with file_name
        blob.upload_from_string(file.read(), content_type=file.content_type)
    except:
        print('error')
        pass



def get_file(file_name):
    
    try:
    
        bucket = storage.bucket()

        # Create a blob with the file name
        blob = bucket.blob(file_name)
        
        return blob.generate_signed_url(expiration=timedelta(minutes=1))
    except:
        return "<h1>404 File Not Found</h1>"
      

def delete_file(file_name):
    """
    Delete a file from Firebase Storage

    Args:
        file_name (str): Name of the file to be deleted
    """
    
    try:
        # Initialize Firebase Admin SDK (assuming it's already initialized globally)
        bucket = storage.bucket()

        # Delete the file
        blob = bucket.blob(file_name)
        blob.delete()
        
    except:
        pass
