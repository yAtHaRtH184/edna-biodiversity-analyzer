import os
import requests
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def download_blast_database(database_url, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    response = requests.get(database_url)
    database_file = os.path.join(output_directory, database_url.split('/')[-1])
    
    with open(database_file, 'wb') as file:
        file.write(response.content)
    
    return database_file

def upload_to_google_drive(file_path):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Creates a local webserver and automatically handles authentication.

    drive = GoogleDrive(gauth)
    gfile = drive.CreateFile({'title': os.path.basename(file_path)})
    gfile.SetContentFile(file_path)
    gfile.Upload()

if __name__ == "__main__":
    # Example usage
    database_url = "https://example.com/path/to/blast/database"  # Replace with actual database URL
    output_directory = "blast_databases"

    downloaded_file = download_blast_database(database_url, output_directory)
    upload_to_google_drive(downloaded_file)