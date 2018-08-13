# imports
from flask import Flask, render_template, request,jsonify
from flask.ext.uploads import UploadSet, configure_uploads, IMAGES
import io
from google.cloud import vision
from google.cloud.vision import types
import re
import pickle
app = Flask(__name__)
# UploadSet used for storing a collection of files
photos = UploadSet('photos', IMAGES)
# setting image storage destination
app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
# configure_uploads will store the configuration of the UploadSet used, will load it into the app.
configure_uploads(app, photos)
#google api function
def detect_text(file):
    """Detects text in the file."""
# used for passing credentials
    client = vision.ImageAnnotatorClient()

    with io.open(file, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)
# calling text detection method via client
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0]
@app.route('/receipt_process', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        text=detect_text('static/img/'+filename)
        text=str(text)
        text=",".join(str(text).split('\n')[1].split('\\n'))
        mfg=regno=class_vehicle=chassis_no=fuel_used=Mk_name="Not found"
# Maker's name dictionary
        d=pickle.load(open('dict.pkl','rb'))
# list of first 2 characters of registration number corresponding to cities.
        cities=['TN','DL','MH']  
# chassis number ranges from MA TO ME in India.
        mylist_chassis=['MA','MB','MC','MD','ME'] 
# common fuels used
        fuel_list=['PETROL','DIESEL','CNG']
# classes from documents provided
        classes=['MOTOR CYCLE','SCOOTER']
# fuel and class provided in files as both upper and lower case.
        fuel_used=",".join(list(i for i in fuel_list if i.lower() in text.lower()))
        class_vehicle=",".join(list(i for i in classes if i.lower() in text.lower()))
        try:
#re expression for a common manufacturing format for eg: 07/2014, number followed by number starting with 20.
            mfg=re.findall(r'(\d+/20\d\d)',(text))[0]
        except:
            pass
        for veh in mylist_chassis:
            try:
# re expression to extract chassis number of length(10,20). Actual length is 17 but due to issues in google vision sometimes characters are missed leading to a change in length. /w matches an alphanumeric character i.e. letters, numbers,etc.
# 'r' in re is used to skip escape sequences, so that they can be used as patterns. for eg: \n will remain \n  instead of a new line so that we can use that it in an re expression.
                chassis=re.findall(r''+(veh)+'\w{10,20}', (text))
                if len(chassis)>0:
                    chassis_no=chassis[0]
                    break
            except:
                pass
        for city in cities:
# find location of city code
            loc=text.find(city)
            if loc>0:
                regno=str(text[loc:])
# removing anything except letters,numbers to clean the output. 
                regno=re.sub(r'[^\w]', '',regno[0:12])
                break
            else:    
                pass
# first 3 letters of chassis number correspond to maker's name. File obtained from web and used to construct a dictionary nd then used to find maker.
        for key in d.keys():
            if key in chassis_no:
                Mk_name=d[key]
# returned json
        return jsonify({"Registration No.":regno,"Month & Year":mfg,"Class Of Vehicle":class_vehicle,"Fuel Used":fuel_used,"Chassis Number":chassis_no,"Seating Capacity":2,"Maker's Name":Mk_name})
    return render_template('upload.html')
if __name__ == '__main__':
    app.run(host='0.0.0.0')
