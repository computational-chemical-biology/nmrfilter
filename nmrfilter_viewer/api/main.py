from flask import Flask
from flask_dropzone import Dropzone
from api.app import personal

app = Flask(__name__)
app.register_blueprint(personal, url_prefix='/nmrfilter')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

app.config.update(
    UPLOADED_PATH= 'api/static/uploads',
    # Flask-Dropzone config:
    #DROPZONE_ALLOWED_FILE_TYPE='text',
    DROPZONE_ALLOWED_FILE_CUSTOM = True,
    DROPZONE_ALLOWED_FILE_TYPE = '.smi,.csv,.txt,.xlsx',
    DROPZONE_MAX_FILE_SIZE=3,
    DROPZONE_MAX_FILES=30,
)

dropzone = Dropzone(app)


if __name__ == '__main__':
    #app.run(debug=True)
    app.run()
