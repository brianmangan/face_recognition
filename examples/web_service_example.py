# This is a _very simple_ example of a web service that recognizes faces in uploaded images.
# Upload an image file and it will check if the image contains a picture of Barack Obama.
# The result is returned as json. For example:
#
# $ curl -XPOST -F "file=@obama2.jpg" http://127.0.0.1:5001
#
# Returns:
#
# {
#  "face_found_in_image": true,
#  "is_picture_of_obama": true
# }
#
# This example is based on the Flask file upload example: http://flask.pocoo.org/docs/0.12/patterns/fileuploads/

# NOTE: This example requires flask to be installed! You can install it with pip:
# $ pip3 install flask
from io import StringIO, BytesIO

import face_recognition
from flask import Flask, jsonify, request, redirect, send_file
from PIL import Image, ImageDraw, ExifTags
import numpy as np

# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_image():
    form_vars = request.form
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # The image file seems valid! Detect faces and return the result.
            for fv in form_vars:
                val = form_vars[fv]
                if fv == 'runFunction' and form_vars[fv] == 'detect_faces_in_image':
                    return detect_faces_in_image(file)

                if fv == 'runFunction' and form_vars[fv] == 'get_image_bound':
                    return get_image_bound(file, file.filename)

    # If no valid image file was uploaded, show the file upload form:
    return '''
    <!doctype html>
    <title>Is this a picture of Obama?</title>
    <h1>Upload a picture and see if it's a picture of Obama!</h1>
    <form method="POST" enctype="multipart/form-data">
      <input type="hidden" name="runFunction2" value="detect_faces_in_image"/>
      <input type="hidden" name="runFunction" value="get_image_bound"/>
      <input type="file" name="file">
      <input type="submit" value="Upload">
    </form>
    '''


def detect_faces_in_image(file_stream):

    # Load the uploaded image file
    img = face_recognition.load_image_file(file_stream)
    # Get face encodings for any faces in the uploaded image
    unknown_face_locations = face_recognition.face_locations(img, model="hog")

    return jsonify(unknown_face_locations)






def get_image_bound(file_stream, filename):
    max_size = 800, 800

    pillage = Image.open(file_stream)
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        exif = pillage._getexif()

        if exif[orientation] == 3:
            image = pillage.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = pillage.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = pillage.rotate(90, expand=True)

        # pillage.save(filepath)
        # pillage.close()
    except (AttributeError, KeyError, IndexError):
        # cases: image don't have getexif
        pass



    pillage.thumbnail(max_size)
    print(pillage.size)

    # Find all the faces  in the unknown image
    unknown_image = np.array(pillage)
    face_locations = face_recognition.face_locations(unknown_image)

    # Convert the image to a PIL-format image so that we can draw on top of it with the Pillow library
    # See http://pillow.readthedocs.io/ for more about PIL/Pillow
    pil_image = Image.fromarray(unknown_image)
    # Create a Pillow ImageDraw Draw instance to draw with
    draw = ImageDraw.Draw(pil_image)

    # Loop through each face found in the unknown image
    for (top, right, bottom, left) in face_locations:
        name = "Unknown"
        # Draw a box around the face using the Pillow module
        draw.rectangle(((left, top), (right, bottom)), outline=(0, 0, 255))

        # Draw a label with a name below the face
        text_width, text_height = draw.textsize(name)
        draw.rectangle(((left, bottom - text_height - 10), (right, bottom)), fill=(0, 0, 255), outline=(0, 0, 255))
        draw.text((left + 6, bottom - text_height - 5), name, fill=(255, 255, 255, 255))

    # Remove the drawing library from memory as per the Pillow docs
    del draw

    pil_image.save('./' + filename)
    return send_file('./' + filename, mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
