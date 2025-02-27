# run by typing python3 main.py in a terminal 
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from flask import Flask, flash, request, redirect, url_for, render_template
from flask import send_from_directory
from ai3 import get_yolo_net, yolo_forward, yolo_save_img
from utils import get_base_url, allowed_file, and_syntax

# setup the webserver
'''
    coding center code
    port may need to be changed if there are multiple flask servers running on same server
    comment out below three lines of code when ready for production deployment
'''
#port = 1000
#base_url = get_base_url(port)
#app = Flask(__name__, static_url_path=base_url+'static')

'''
    cv scaffold code
    uncomment below line when ready for production deployment
'''
base_url = ""
app = Flask(__name__)

UPLOAD_FOLDER = 'images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

# set up yolo net for prediction
# you will need to change names, weights, and configuration files.
names_path = os.path.join('yolo', 'nvidia.names')
LABELS = open(names_path).read().strip().split("\n")
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3), dtype="uint8")

weights_path = os.path.join('yolo', 'nvidia_final.weights')
cfg_path = os.path.join('yolo', 'nvidia.cfg')
net = get_yolo_net(cfg_path, weights_path)


@app.route('/')
#@app.route(base_url)
def home():
    return render_template('Home.html')


@app.route('/', methods=['POST'])
#@app.route(base_url, methods=['POST'])
def home_post():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
        # return redirect(url_for('home'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('results', filename=filename))

    return redirect(url_for('home'))


@app.route('/uploads/<filename>')
#@app.route(base_url + '/uploads/<filename>')
def results(filename): 
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image = cv2.imread(image_path)
    (class_ids, labels, boxes, confidences) = yolo_forward(net, LABELS, image, confidence_level=0.3)

    # if we detected something
    if len(class_ids) > 0:
        found = True
        new_filename = 'yolo_' + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        yolo_save_img(image, class_ids, boxes, labels, confidences, COLORS, file_path=file_path)

        # confidences: rounding and changing to percent, putting in  function
        format_confidences = []
        for percent in confidences:
            format_confidences.append(str(round(percent*100)) + '%')
        format_confidences = and_syntax(format_confidences)
        # labels: sorting and capitalizing, putting into function
        labels = set(labels)
        labels = [plant.capitalize() for plant in labels]
        labels = and_syntax(labels)
        return render_template('Results.html', confidences=format_confidences, labels=labels, 
            old_filename = filename, 
            filename=new_filename) 
    else:
        found = False
        # replace 'Objects' with whatever you are trying to detect
        return render_template('Results.html', labels='No Objects', old_filename=filename, filename=filename) 

@app.route('/files/<path:filename>')
#@app.route(base_url + '/files/<path:filename>')
def files(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route(base_url + '/ourcause')
def our_cause():
    return (render_template('OurCause.html'))

if __name__ == "__main__":
    '''
    coding center code
    '''
    # IMPORTANT: change the cocalcx.ai-camp.org to the site where you are editing this file.
    website_url = 'cocalc7.ai-camp.org'
    print(f"Try to open\n\n    https://{website_url}" + base_url + '\n\n')

    # remove debug=True when deploying it
    app.run(host = '0.0.0.0', port=port, debug=True)
    import sys; sys.exit(0)

    '''
    cv scaffold code
    '''
    # Only for debugging while developing
    # app.run(port=80, debug=True)
