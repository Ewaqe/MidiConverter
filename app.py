import os
import pipeline
from asgiref.wsgi import WsgiToAsgi
from flask import Flask, render_template, request, redirect, flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'midi', 'mid'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

asgi_app = WsgiToAsgi(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/upload_midi', methods=['POST'])
def upload_midi():
    if 'file' not in request.files:
        print('file not')
        return redirect('/')

    file = request.files['file']
    if file.filename == '':
        print('filename empty')
        return redirect('/')

    if not allowed_file(file.filename):
        print('not allowed')
        return redirect('/')

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    rttl_strings = pipeline.generate(filepath)

    os.remove(filepath)
    return render_template('result.html', code=generate_code(rttl_strings))


def generate_code(rttl_strings: list):
    code = "#include <MusicWithoutDelay.h>\n"
    for i, rttl in enumerate(rttl_strings):
        code += f"const char song{i}[] PROGMEM = \"{rttl}\";\n"
    for i, rttl in enumerate(rttl_strings):
        code += f"MusicWithoutDelay instrument{i}(song{i})\n"
    code += "void setup() {\n"
    for i, rttl in enumerate(rttl_strings):
        if i == 0:
            code += f"instrument{i}.begin(CHA, TRIANGLE, ENVELOPE0, 0)\n"
        else:
            code += f"instrument{i}.begin(TRIANGLE, ENVELOPE0, 0)\n"
    code += "}\n\nvoid loop() {\n"
    for i, rttl in enumerate(rttl_strings):
        code += f"instrument{i}.update()\n"
    code += "}"
    return code


if __name__ == '__main__':
    app.run(debug=True)
