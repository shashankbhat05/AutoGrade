from datetime import datetime
import pathlib
from MailSent import send_email, getDateTime
from pypdf import PdfReader
import os
import time
import base64
import tensorflow as tf
import transformers
from flask import Flask, request, render_template, session, redirect, url_for
import numpy as np
from huggingface_hub import from_pretrained_keras
import tensorflow_hub as hub
import firebase_admin
import random
from firebase_admin import credentials, firestore
from PIL import Image
from pytesseract import pytesseract
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred)
app = Flask(__name__)
app.secret_key = "OnlineAutomatedEvaluation@123"
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['.png', '.jpg', '.jpeg', '.gif'])
questions=['Question1','Question2','Question3','Question4','Question5','Question6']
depts=["ISE","CSE","ECE","EEE"]
classnames = ['SEM3', 'SEM4', 'SEM5', 'SEM6','SEM7' ,'SEM8']
class1subjects = ['M3', 'DSA','ADE','CO','Java','Kannadda']
class2subjects = ['M4', 'DAA','MES','OS','Python','CIP']
class3subjects = ['ATC', 'CN','DBMS','AIML','RMIPR','EVS']
class4subjects = ['SEPM', 'FS','DMDW','OSHA','ST','Agile']
class5subjects = ['CNS', 'CC','Iot','UID','RPA','EPM']
class6subjects = ['DS', 'BD','BT','DIP','FS','PE']

@app.route('/userviewreports', methods=['POST','GET'])
def userviewreports():
    try:
        userid = session['userid']
        print("User Id : ", userid)
        db = firestore.client()
        studentdata = db.collection('newuser').document(userid).get().to_dict()
        print("Student Data : ", studentdata)
        class_name = studentdata['ClassName']
        class_subjects = []
        if (class_name == classnames[0]):
            class_subjects = class1subjects
        elif (class_name == classnames[1]):
            class_subjects = class2subjects
        elif (class_name == classnames[2]):
            class_subjects = class3subjects
        elif (class_name == classnames[3]):
            class_subjects = class4subjects
        elif (class_name == classnames[4]):
            class_subjects = class5subjects
        elif (class_name == classnames[5]):
            class_subjects = class6subjects
        print("Subjects : ", class_subjects)
        newdata_ref = db.collection('newreport')
        reportdata = newdata_ref.get()
        data = []
        overallresult,overalltotal,passcount,failcount='Pass',0,0,0
        for subject in class_subjects:
            tempdata={}
            tempdata['StudentId'] = userid
            tempdata['StudentName'] = studentdata['FirstName'] + " " + studentdata['LastName']
            tempdata['ClassName'] = class_name
            tempdata['SubjectName'] = subject
            print("TempData : ", tempdata)
            questioncol=[]
            total=0
            for question in questions:
                for doc in reportdata:
                    temp=doc.to_dict()
                    print("Temp : ", temp)
                    if(str(temp['StudentId'])==str(userid) and temp['ClassName']==class_name and
                        subject==temp['SubjectName'] and question==temp['SlNo']):
                        questioncol.append(temp['Question'] + " " + str(temp['ObtainedMarks']))
                        total+=int(temp['ObtainedMarks'])
            tempdata['Question'] = questioncol
            tempdata['Total'] = total
            #tempdata['Result'] = "Pass"
            if(total<35):
                tempdata['Result'] = "Fail"
                overallresult='Fail'
                failcount+=1
            else:
                passcount+=1
                tempdata['Result'] = "Pass"
            print("Temp Data : ",tempdata)
            data.append(tempdata)
            overalltotal+=total
        print("Student Data ", data)
        graph_data = [
            {"label": "Pass", "y": passcount},
            {"label": "Fail", "y": failcount}
        ]        
        print("Report Data " , data)        
        return render_template("userviewreports.html", data=data,
            graph_data=graph_data, overallresult=overallresult,overalltotal=overalltotal)
    except Exception as e:
        return str(e)

@app.route('/teacherviewresult', methods=['POST', 'GET'])
def teacherviewresult():
    try:
        id=request.args['id']
        print("Student Id : ", id)
        db = firestore.client()
        studentdata = db.collection('newuser').document(id).get().to_dict()
        print("Student Data : ", studentdata)
        class_name = studentdata['ClassName']
        class_subjects = []
        if (class_name == classnames[0]):
            class_subjects = class1subjects
        elif (class_name == classnames[1]):
            class_subjects = class2subjects
        elif (class_name == classnames[2]):
            class_subjects = class3subjects
        elif (class_name == classnames[3]):
            class_subjects = class4subjects
        elif (class_name == classnames[4]):
            class_subjects = class5subjects
        elif (class_name == classnames[5]):
            class_subjects = class6subjects
        newdata_ref = db.collection('newreport')
        reportdata = newdata_ref.get()
        data = []
        overallresult,overalltotal,passcount,failcount='Pass',0,0,0
        for subject in class_subjects:
            tempdata={}
            tempdata['StudentId'] = id
            tempdata['StudentName'] = studentdata['FirstName'] + " " + studentdata['LastName']
            tempdata['ClassName'] = class_name
            tempdata['SubjectName'] = subject
            questioncol=[]
            total=0
            for question in questions:
                for doc in reportdata:
                    temp=doc.to_dict()
                    print("Temp : ", temp)
                    if(str(temp['StudentId'])==str(id) and temp['ClassName']==class_name and
                        subject==temp['SubjectName'] and question==temp['SlNo']):
                        questioncol.append(temp['Question'] + " " + str(temp['ObtainedMarks']))
                        total+=int(temp['ObtainedMarks'])
            tempdata['Question'] = questioncol
            tempdata['Total'] = total
            #tempdata['Result'] = "Pass"
            if(total<35):
                tempdata['Result'] = "Fail"
                overallresult='Fail'
                failcount+=1
            else:
                passcount+=1
                tempdata['Result'] = "Pass"
            data.append(tempdata)
            overalltotal+=total
        print("Student Data ", data)
        graph_data = [
            {"label": "Pass", "y": passcount},
            {"label": "Fail", "y": failcount}
        ]
        print("Graph Data : ", graph_data)
        cnt=getNotificationCnt()
        return render_template("teacherviewresult.html", data=data,
                               overallresult=overallresult, overalltotal=overalltotal, 
                               graph_data=graph_data,cnt=cnt)
    except Exception as e:
        return str(e)

@app.route('/adminviewresult', methods=['POST', 'GET'])
def adminviewresult():
    try:
        id=request.args['id']
        db = firestore.client()
        studentdata = db.collection('newuser').document(id).get().to_dict()
        class_name = studentdata['ClassName']
        class_subjects = []
        if (class_name == classnames[0]):
            class_subjects = class1subjects
        elif (class_name == classnames[1]):
            class_subjects = class2subjects
        elif (class_name == classnames[2]):
            class_subjects = class3subjects
        elif (class_name == classnames[3]):
            class_subjects = class4subjects
        elif (class_name == classnames[4]):
            class_subjects = class5subjects
        elif (class_name == classnames[5]):
            class_subjects = class6subjects
        newdata_ref = db.collection('newreport')
        reportdata = newdata_ref.get()
        data = []
        overallresult,overalltotal,passcount,failcount='Pass',0,0,0
        for subject in class_subjects:
            tempdata={}
            tempdata['StudentId'] = id
            tempdata['StudentName'] = studentdata['FirstName'] + " " + studentdata['LastName']
            tempdata['ClassName'] = class_name
            tempdata['SubjectName'] = subject
            questioncol=[]
            total=0
            for question in questions:
                for doc in reportdata:
                    temp=doc.to_dict()
                    if(str(temp['StudentId'])==str(id) and temp['ClassName']==class_name and
                    subject==temp['SubjectName'] and question==temp['SlNo']):
                        questioncol.append(temp['Question'] + " " + str(temp['ObtainedMarks']))
                        total+=int(temp['ObtainedMarks'])
            tempdata['Question'] = questioncol
            tempdata['Total'] = total
            #tempdata['Result'] = "Pass"
            if(total<35):
                tempdata['Result'] = "Fail"
                overallresult='Fail'
                failcount+=1
            else:
                passcount+=1
                tempdata['Result'] = "Pass"
            data.append(tempdata)
            overalltotal+=total
        print("Student Data ", data)
        graph_data = [
            {"label": "Pass", "y": passcount},
            {"label": "Fail", "y": failcount}
        ]
        print("Graph Data : ", graph_data)        
        return render_template("adminviewresult.html", data=data,
                               overallresult=overallresult, overalltotal=overalltotal,
                               graph_data=graph_data)
    except Exception as e:
        return str(e)

@app.route('/adminmainpage')
def adminmainpage():
    try:
        db = firestore.client()
        newdata_ref = db.collection('newuser')
        studentdata=newdata_ref.get()
        newdata_ref = db.collection('newreport')
        reportdata = newdata_ref.get()
        newdata_ref = db.collection('newteacher')
        teacherdata = newdata_ref.get()
        newdata_ref = db.collection('newquestion')
        questiondata = newdata_ref.get()
        data=[]
        passcount, failcount, studentcount, teachercount, questioncount = 0, 0, 0, 0, 0
        for x in teacherdata:
            teachercount+=1
        for x in questiondata:
            questioncount+=1
        for student in studentdata:
            temp={}
            studentcount+=1
            tempstudent = student.to_dict()
            classname = tempstudent['ClassName']
            class_subjects = []
            if (classname == classnames[0]):
                class_subjects = class1subjects
            elif (classname == classnames[1]):
                class_subjects = class2subjects
            elif (classname == classnames[2]):
                class_subjects = class3subjects
            elif (classname == classnames[3]):
                class_subjects = class4subjects
            elif (classname == classnames[4]):
                class_subjects = class5subjects
            elif (classname == classnames[5]):
                class_subjects = class6subjects
            total=0
            print("Class Subjects : ", class_subjects)
            for subject in class_subjects:
                for report in reportdata:
                    tempreport = report.to_dict()
                    if(str(tempreport['StudentId'])==str(tempstudent['id']) and classname==tempreport['ClassName']
                        and tempreport['SubjectName']==subject):
                        total+=int(tempreport['ObtainedMarks'])
            if(total>=35):
                temp['Result'] = "Pass"
                passcount+=1
            else:
                temp['Result'] = "Fail"
                failcount += 1
        print("Report Data " , data)
        return render_template("adminmainpage.html", studentcount=studentcount,
                               teachercount=teachercount,questioncount=questioncount,
                               passcount=passcount,failcount=failcount)
    except Exception as e:
        return str(e)

"""
@app.route('/teacherviewreports', methods=['POST','GET'])
def teacherviewreports():
    try:
        cnt = getNotificationCnt()
        db = firestore.client()
        newdata_ref = db.collection('newuser')
        studentdata=newdata_ref.get()
        newdata_ref = db.collection('newreport')
        reportdata = newdata_ref.get()
        data=[]
        passcount, failcount = 0, 0
        for student in studentdata:
            temp={}
            tempstudent = student.to_dict()
            temp['StudentId'] = tempstudent['id']
            temp['Department'] = tempstudent['Department']
            temp['StudentName'] = tempstudent['FirstName']+" "+tempstudent['LastName']
            temp['ClassName'] = tempstudent['ClassName']
            classname = tempstudent['ClassName']
            class_subjects = []
            if (classname == classnames[0]):
                class_subjects = class1subjects
            elif (classname == classnames[1]):
                class_subjects = class2subjects
            elif (classname == classnames[2]):
                class_subjects = class3subjects
            elif (classname == classnames[3]):
                class_subjects = class4subjects
            elif (classname == classnames[4]):
                class_subjects = class5subjects
            elif (classname == classnames[5]):
                class_subjects = class6subjects
            total=0
            print("Class Subjects : ", class_subjects)
            for subject in class_subjects:
                for report in reportdata:
                    tempreport = report.to_dict()
                    if(str(tempreport['StudentId'])==str(tempstudent['id']) and classname==tempreport['ClassName']
                        and tempreport['SubjectName']==subject):
                        total+=int(tempreport['ObtainedMarks'])
                temp['SubjectName'] = subject
            temp['ObtainedMarks'] = total
            temp['TotalMarks'] = 100
            if(total>=35):
                temp['Result'] = "Pass"
                passcount+=1
            else:
                temp['Result'] = "Fail"
                failcount += 1
            data.append(temp)
        graph_data = [
            {"label": "Pass", "y": passcount},
            {"label": "Fail", "y": failcount}
        ]
        print("Report Data " , data)
        return render_template("teacherviewreports.html", data=data,
                               graph_data=graph_data,cnt=cnt)
    except Exception as e:
        return str(e)
"""
@app.route('/teacherselectsubject', methods=['POST','GET'])
def teacherselectsubject():
    try:
        notifycnt=getNotificationCnt()
        studentid = request.args['id']
        updatestatus=['NotUpdated','NotUpdated','NotUpdated',
                      'NotUpdated','NotUpdated','NotUpdated']
        db = firestore.client()
        reportdata = db.collection('newreport').get()
        studentdata = db.collection('newuser').document(studentid).get().to_dict()
        session['studentid']=studentid
        classname=studentdata['ClassName']
        print("Student Data : ", studentdata)
        class_subjects=[]
        if(classname==classnames[0]):
            class_subjects=class1subjects
        elif (classname == classnames[1]):
            class_subjects = class2subjects
        elif (classname == classnames[2]):
            class_subjects = class3subjects
        elif (classname == classnames[3]):
            class_subjects = class4subjects
        elif (classname == classnames[4]):
            class_subjects = class5subjects
        elif (classname == classnames[5]):
            class_subjects = class6subjects
        data=[]
        cnt=0
        for subject in class_subjects:
            flag=True
            for x in reportdata:
                temp=x.to_dict()
                if(str(temp['StudentId'])==str(studentid) and
                        str(temp['ClassName'])==classname and
                        str(temp['SubjectName'])==subject):
                    flag=False
            if(not flag):
                updatestatus[cnt]='Updated'
            cnt+=1
        cnt=0
        for subject in class_subjects:
            temp={}
            temp['StudentId']=studentid
            temp['StudentName'] = studentdata['FirstName']+" "+studentdata['LastName']
            temp['EmailId'] = studentdata['EmailId']
            temp['PhoneNumber'] = studentdata['PhoneNumber']
            temp['ClassName'] = studentdata['ClassName']
            temp['SubjectName'] = subject
            temp['UpdateStatus'] = updatestatus[cnt]
            cnt+=1
            data.append(temp)
        print("Data : ", data)
        return render_template("teacherselectsubject.html", data=data,
                               cnt=notifycnt)
    except Exception as e:
        return str(e)

@app.route('/teacherupdateanswers2', methods=["POST","GET"])
def teacherupdateanswers2():
    try:
        userid = session['userid']
        username = session['username']
        studentid=session['studentid']
        dept = session['dept']
        file_names, given_marks, questions,SlNo,class_names,subject_names=[],[],[],[],[],[]
        db = firestore.client()
        newdata = session['questiondata']
        newdata_ref = db.collection('newuser')
        studentdata = newdata_ref.document(studentid).get().to_dict()
        data = []
        print("Question Data : ", newdata)
        for temp in newdata:
            #temp=doc
            data.append(temp)
            file_names.append(str(temp['FileName']))
            given_marks.append(str(temp['Marks']))
            questions.append(str(temp['Question']))
            SlNo.append(str(temp['SlNo']))
            class_names.append(str(temp['ClassName']))
            subject_names.append(str(temp['SubjectName']))
        if request.method == 'POST':
            # Get the list of files from webpage
            files = request.files.getlist("file")
            print("Files : ", files)
            # Iterate for each file in the files List, and Save them
            cnt=0
            # current date and time
            now = datetime.now()
            date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
            # mm/dd/YY H:M:S format
            for file in files:
                con_val, per_val, obtainedmarks=0,0,0
                if(len(file.filename)>0):
                    file_extension = pathlib.Path(file.filename).suffix
                    filename = "File" + str(round(time.time())) + file_extension
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    # file.save(file.filename)
                    print("File Name : ", filename, " File : ", file)
                    student_ans, model_ans = "", ""
                    time.sleep(3)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    if (file_extension.lower() in ALLOWED_EXTENSIONS):
                        student_ans = readTextFromImage(file_path)
                    elif (file_extension == ".pdf"):
                        student_ans = readTextFromPdf(file_path)

                    file_extension = pathlib.Path(file_names[cnt]).suffix
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_names[cnt])
                    if (file_extension.lower() in ALLOWED_EXTENSIONS):
                        model_ans = readTextFromImage(file_path)
                    elif (file_extension == ".pdf"):
                        model_ans = readTextFromPdf(file_path)

                    print("==============")
                    print("Model Ans : \n", model_ans)
                    print("==============")

                    print("==============")
                    print("Student Ans : \n", student_ans)
                    print("==============")

                    time.sleep(3)

                    text = check_similarity(student_ans, model_ans)
                    print("Text : ", text)

                    con_val = round(text["Contradiction"] * 100, 2)
                    per_val = float(round(text["Perfect"] * 100, 2))
                    neu_val = round(text["Neutral"] * 100, 2)

                    dict = {}
                    dict['Contradiction'] = con_val
                    dict['Perfect'] = per_val
                    dict['Neutral'] = neu_val
                    dict['student_ans'] = student_ans
                    dict['model_ans'] = model_ans
                    dict['marks'] = per_val
                    modelmarks = int(given_marks[cnt])
                    obtainedmarks = int(round((modelmarks * per_val) / 100, 0))
                id = str(random.randint(1000, 9999))
                json = {'id': id, 'TeacherId': userid, 'TeacherName': username,
                            'Question': questions[cnt],'StudentId':studentid,
                            'Dept':dept,
                            'StudentName':studentdata['FirstName'] + " " + studentdata['LastName'],
                            'Contradiction': con_val, 'Perfect': per_val,
                            'ObtainedPercentage': per_val,
                            'ObtainedMarks': obtainedmarks,
                            'Marks': given_marks[cnt],'SlNo':SlNo[cnt],
                            'ClassName':class_names[cnt],'SubjectName':subject_names[cnt],
                            'DateTime': date_time}
                db = firestore.client()
                newdb_ref = db.collection('newreport')
                newdb_ref.document(id).set(json)
                cnt+=1
            return redirect(url_for("teacherviewreports"))
        return render_template("teacherupdateanswers1.html",data=data,msg="")
    except Exception as e:
        print("Exception : ", e)
        return render_template("teacherupdateanswers1.html", msg=e)

@app.route('/teacheruploadanswers', methods=['POST','GET'])
def teacheruploadanswers():
    try:
        studentid = request.args['id']
        subname = request.args['subname']
        db = firestore.client()
        studentdata = db.collection('newuser').document(studentid).get().to_dict()
        msg,flag,cnt="",False,0
        newdata_ref = db.collection('newquestion')
        newdata = newdata_ref.get()
        dept=studentdata['Department']
        classname=studentdata['ClassName']
        data=[]
        for x in newdata:
            temp=x.to_dict()
            if(temp['ClassName']==classname and temp['Department']==dept and temp['SubjectName']==subname
            and temp['Status']=='Updated'):
                data.append(temp)
                cnt+=1
        if(cnt<5):
            flag=True
            msg="Not Enough Question Uploaded Min Questions = 5"
        session['questiondata']=data
        return render_template("teacherupdateanswers1.html", data=data, msg=msg, flag=flag)
    except Exception as e:
        return str(e)

@app.route('/teacherupdateanswers1', methods=['POST','GET'])
def teacherupdateanswers1():
    try:
        db = firestore.client()
        studentid = request.args['id']
        session['studentid']=studentid
        #teacherid=session['userid']
        dept=session['dept']
        classname=session['classname']
        subjectname = session['subjectname']
        newdata_ref = db.collection('newquestion')
        newdata = newdata_ref.get()
        data=[]
        for doc in newdata:
            temp=doc.to_dict()
            if(temp['Department']==dept and temp['ClassName']==classname and
                temp['SubjectName'] == subjectname and temp['Status'] == 'Updated'):
                data.append(doc.to_dict())
        print("Question Data " , data)
        return render_template("teacherupdateanswers1.html", data=data)
    except Exception as e:
        return str(e)

@app.route('/useranswerquestions', methods=["POST","GET"])
def useranswerquestions():
    try:
        userid = session['userid']
        username = session['username']
        file_names, given_marks, questions=[],[],[]
        db = firestore.client()
        newdata_ref = db.collection('newquestion')
        newdata = newdata_ref.get()
        data = []
        for doc in newdata:
            temp=doc.to_dict()
            data.append(temp)
            file_names.append(str(temp['FileName']))
            given_marks.append(str(temp['Marks']))
            questions.append(str(temp['Question']))
        if request.method == 'POST':
            # Get the list of files from webpage
            files = request.files.getlist("file")
            print("Files : ", files)
            # Iterate for each file in the files List, and Save them
            cnt=0
            # current date and time
            now = datetime.now()
            date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
            # mm/dd/YY H:M:S format
            for file in files:
                con_val, per_val, obtainedmarks=0,0,0
                if(len(file.filename)>0):
                    file_extension = pathlib.Path(file.filename).suffix
                    filename = "File" + str(round(time.time())) + file_extension
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    # file.save(file.filename)
                    print("File Name : ", filename, " File : ", file)
                    student_ans, model_ans = "", ""
                    time.sleep(3)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    if (file_extension.lower() in ALLOWED_EXTENSIONS):
                        student_ans = readTextFromImage(file_path)
                    elif (file_extension == ".pdf"):
                        student_ans = readTextFromPdf(file_path)

                    file_extension = pathlib.Path(file_names[cnt]).suffix
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_names[cnt])
                    if (file_extension.lower() in ALLOWED_EXTENSIONS):
                        model_ans = readTextFromImage(file_path)
                    elif (file_extension == ".pdf"):
                        model_ans = readTextFromPdf(file_path)

                    print("==============")
                    print("Model Ans : \n", model_ans)
                    print("==============")

                    print("==============")
                    print("Student Ans : \n", student_ans)
                    print("==============")

                    time.sleep(3)

                    text = check_similarity(student_ans, model_ans)
                    print("Text : ", text)

                    con_val = round(text["Contradiction"] * 100, 2)
                    per_val = float(round(text["Perfect"] * 100, 2))
                    neu_val = round(text["Neutral"] * 100, 2)

                    dict = {}
                    dict['Contradiction'] = con_val
                    dict['Perfect'] = per_val
                    dict['Neutral'] = neu_val
                    dict['student_ans'] = student_ans
                    dict['model_ans'] = model_ans
                    dict['marks'] = per_val
                    modelmarks = int(given_marks[cnt])
                    obtainedmarks = int(round((modelmarks * per_val) / 100, 0))
                id = str(random.randint(1000, 9999))
                json = {'id': id, 'UserId': userid, 'UserName': username,
                            'Question': questions[cnt],
                            'Contradiction': con_val, 'Perfect': per_val,
                            'ObtainedPercentage': per_val,
                            'ObtainedMarks': obtainedmarks,
                            'Marks': given_marks[cnt],
                            'DateTime': date_time}
                db = firestore.client()
                newdb_ref = db.collection('newreport')
                newdb_ref.document(id).set(json)
                cnt+=1
            return redirect(url_for("userviewreports"))
        return render_template("useranswerquestions.html",data=data,msg="")
    except Exception as e:
        print("Exception : ", e)
        return render_template("useranswerquestions.html", msg=e)

class BertSemanticDataGenerator(tf.keras.utils.Sequence):
    def __init__(
            self,
            sentence_pairs,
            labels,
            batch_size=32,
            shuffle=True,
            include_targets=True,
    ):
        self.sentence_pairs = sentence_pairs
        self.labels = labels
        self.shuffle = shuffle
        self.batch_size = batch_size
        self.include_targets = include_targets
        # Load our BERT Tokenizer to encode the text.
        # We will use base-base-uncased pretrained model.
        self.tokenizer = transformers.BertTokenizer.from_pretrained(
            "bert-base-uncased", do_lower_case=True
        )
        self.indexes = np.arange(len(self.sentence_pairs))
        self.on_epoch_end()

    def __len__(self):
        # Denotes the number of batches per epoch.
        return len(self.sentence_pairs) // self.batch_size

    def __getitem__(self, idx):
        # Retrieves the batch of index.
        indexes = self.indexes[idx * self.batch_size: (idx + 1) * self.batch_size]
        sentence_pairs = self.sentence_pairs[indexes]

        # With BERT tokenizer's batch_encode_plus batch of both the sentences are
        # encoded together and separated by [SEP] token.
        encoded = self.tokenizer.batch_encode_plus(
            sentence_pairs.tolist(),
            add_special_tokens=True,
            max_length=128,
            return_attention_mask=True,
            return_token_type_ids=True,
            pad_to_max_length=True,
            return_tensors="tf",
        )

        # Convert batch of encoded features to numpy array.
        input_ids = np.array(encoded["input_ids"], dtype="int32")
        attention_masks = np.array(encoded["attention_mask"], dtype="int32")
        token_type_ids = np.array(encoded["token_type_ids"], dtype="int32")

        # Set to true if data generator is used for training/validation.
        if self.include_targets:
            labels = np.array(self.labels[indexes], dtype="int32")
            return [input_ids, attention_masks, token_type_ids], labels
        else:
            return [input_ids, attention_masks, token_type_ids]

def readTextFromImage(image_path):
    # Defining paths to tesseract.exe
    # and the image we would be using
    path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    # Opening the image & storing it in an image object
    img = Image.open(image_path)
    # Providing the tesseract executable
    # location to pytesseract library
    pytesseract.tesseract_cmd = path_to_tesseract
    # Passing the image object to image_to_string() function
    # This function will extract the text from the image
    text = pytesseract.image_to_string(img)
    # Displaying the extracted text
    #print(text[:-1])
    return text[:-1]

def readTextFromPdf(pdf_path):
    # creating a pdf reader object
    reader = PdfReader(pdf_path)
    # printing number of pages in pdf file
    # print(len(reader.pages))
    # getting a specific page from the pdf file
    page = reader.pages[0]
    # extracting text from page
    text = ""
    pages_len = len(reader.pages)
    for x in range(0, pages_len + 1):
        temp = page.extract_text()
        text += temp
    #print(text)
    return text

@app.route("/checkMyAnswer")
def checkMyAnswer():
    return render_template("checkMyAnswer.html")

@app.route("/answers")
def answers():
    return render_template("answers.html")

model = from_pretrained_keras("keras-io/bert-semantic-similarity")
# model = tf.keras.models.load_model('saved_model_pooja.h5')
# model = tf.keras.models.load_model(
#        ('saved_model_pooja.h5'),
#        custom_objects={'TFBertMainLayer':hub.TFBertMainLayer}
# )
labels = ["Contradiction", "Perfect", "Neutral"]

def check_similarity(sentence1, sentence2):
    sentence_pairs = np.array([[str(sentence1), str(sentence2)]])
    test_data = BertSemanticDataGenerator(
        sentence_pairs, labels=None, batch_size=1, shuffle=False, include_targets=False,
    )
    probs = model.predict(test_data[0])[0]

    labels_probs = {labels[i]: float(probs[i]) for i, _ in enumerate(labels)}
    return labels_probs

    # idx = np.argmax(proba)
    # proba = f"{proba[idx]*100:.2f}%"
    # pred = labels[idx]
    # return f'The semantic similarity of two input sentences is {pred} with {proba} of probability'

@app.route("/predict", methods=["POST"])
def predict():
    if request.method == 'POST':
        student_ans = request.form.get('student_ans')
        model_ans = request.form.get('model_ans')
        print(student_ans)
        print(model_ans)
        text = check_similarity(student_ans, model_ans)
        print(text)

        con_val = int(text["Contradiction"] * 100)
        per_val = int(text["Perfect"]*100)
        neu_val = int(text["Neutral"]*100)

        dict = {}
        dict['Contradiction'] = con_val
        dict['Perfect'] = per_val
        dict['Neutral'] = neu_val
        dict['student_ans'] = student_ans
        dict['model_ans'] = model_ans
        dict['marks'] = per_val
        return render_template('answers.html', dict=dict)
    return render_template("index.html")

@app.route("/result")
def result():
    return render_template("result.html")

@app.route('/')
def index():
    try:
        return render_template("index.html")
    except Exception as e:
        return str(e)

@app.route('/usermainpage')
def usermainpage():
    try:
        return render_template("usermainpage.html")
    except Exception as e:
        return str(e)

@app.route('/index')
def indexpage():
    try:
        return render_template("index.html")
    except Exception as e:
        return str(e)

@app.route('/logout')
def logoutpage():
    try:
        session['id']=None
        return render_template("index.html")
    except Exception as e:
        return str(e)

@app.route('/about')
def aboutpage():
    try:
        return render_template("about.html")
    except Exception as e:
        return str(e)

@app.route('/services')
def servicespage():
    try:
        return render_template("services.html")
    except Exception as e:
        return str(e)

@app.route('/gallery')
def gallerypage():
    try:
        return render_template("gallery.html")
    except Exception as e:
        return str(e)

@app.route('/adminlogin', methods=['GET','POST'])
def adminloginpage():
    msg=""
    if request.method == 'POST':
        uname = request.form['uname'].lower()
        pwd = request.form['pwd'].lower()
        print("Uname : ", uname, " Pwd : ", pwd)
        if uname == "admin" and pwd == "admin":
            return redirect(url_for("adminmainpage"))
        else:
            msg = "UserName/Password is Invalid"
    return render_template("adminlogin.html", msg=msg)

@app.route('/userlogin', methods=['GET','POST'])
def userloginpage():
    msg=""
    if request.method == 'POST':
        uname = request.form['uname']
        pwd = request.form['pwd']

        db = firestore.client()
        dbref = db.collection('newuser')
        userdata = dbref.get()
        data = []
        for doc in userdata:
            print(doc.to_dict())
            print(f'{doc.id} => {doc.to_dict()}')
            data.append(doc.to_dict())
        flag = False
        for temp in data:
            print("Pwd : ", temp['Password'])
            decode = base64.b64decode(temp['Password']).decode("utf-8")
            if uname == temp['UserName'] and pwd == decode:
                session['userid'] = temp['id']
                session['username'] = temp['FirstName'] + " " + temp['LastName']
                flag = True
                break
        if (flag):
            return render_template("usermainpage.html")
        else:
            msg = "UserName/Password is Invalid"
    return render_template("userlogin.html", msg=msg)

@app.route('/teacherlogin', methods=['GET','POST'])
def teacherlogin():
    msg=""
    if request.method == 'POST':
        uname = request.form['uname']
        pwd = request.form['pwd']

        db = firestore.client()
        dbref = db.collection('newteacher')
        userdata = dbref.get()
        data = []
        for doc in userdata:
            print(doc.to_dict())
            print(f'{doc.id} => {doc.to_dict()}')
            data.append(doc.to_dict())
        flag = False
        for temp in data:
            print("Pwd : ", temp['Password'])
            decode = base64.b64decode(temp['Password']).decode("utf-8")
            if uname == temp['UserName'] and pwd == decode:
                session['userid'] = temp['id']
                session['dept'] = temp['Department']
                session['username'] = temp['FirstName'] + " " + temp['LastName']
                session['classname']=temp['ClassName']
                session['subjectname']=temp['SubjectName']
                flag = True
                break
        if (flag):
            cnt=getNotificationCnt()
            return render_template("teachermainpage.html",cnt=cnt)
        else:
            msg = "UserName/Password is Invalid"
    return render_template("teacherlogin.html", msg=msg)

@app.route('/userviewprofile')
def userviewprofile():
    try:
        id=session['userid']
        db = firestore.client()
        data = db.collection('newuser').document(id).get().to_dict()
        print("User Data ", data)
        return render_template("userviewprofile.html", data=data)
    except Exception as e:
        return str(e)

@app.route('/teacheraddquestion1')
def teacheraddquestion1():
    try:
        id=request.args['id']
        db = firestore.client()
        cnt = getNotificationCnt()
        data = db.collection('newquestion').document(id).get().to_dict()
        """
        newdata_ref = db.collection('newquestion')        
        newdata = newdata_ref.get()
        data = []
        for doc in newdata:
            temp=doc.to_dict()
            if(str(temp['TeacherId'])==str(id) and str(temp['Status'])=='NotUpdated'):
                data.append(doc.to_dict())
                print(temp)
        """
        print("Question Data ", data)
        return render_template("teacheraddquestion1.html", data=data,cnt=cnt)
    except Exception as e:
        return str(e)

def updateQuestion(id,question,filename,file_extension,marks):
    answer = ""
    time.sleep(3)
    flag = False
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if (file_extension.lower() in ALLOWED_EXTENSIONS):
        answer = readTextFromImage(file_path)
        flag = True
    elif (file_extension == ".pdf"):
        answer = readTextFromPdf(file_path)
        flag = True
    time.sleep(3)
    if (flag):
        db = firestore.client()
        db_ref = db.collection('newquestion').document(id)
        db_ref.update({u'Question': question})
        db_ref.update({u'FileName': filename})
        db_ref.update({u'Marks': marks})
        db_ref.update({u'Answer': answer})
        db_ref.update({u'Status': 'Updated'})
        msg = "New Question Added Success"
        db_ref.update({u'Reason': msg})
    else:
        msg = "Uploaded File should be either Image/PDF"
        db = firestore.client()
        db_ref = db.collection('newquestion').document(id)
        db_ref.update({u'Reason': msg})
    print(msg)


@app.route('/teacheraddquestion2', methods=['POST','GET'])
def teacheraddquestion2():
    try:
        msg=""
        print("Add New Question page")
        if request.method == 'POST':
            question = request.form['question']
            file = request.files['file']
            marks = request.form['marks']
            id = request.form['id']
            # function to return the file extension
            file_extension = pathlib.Path(file.filename).suffix
            filename = "File" + str(round(time.time())) + file_extension
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            updateQuestion(id, question, filename, file_extension, marks)
            """
            question = request.form['question2']
            file = request.files['file2']
            marks = request.form['marks2']
            id = request.form['id2']
            # function to return the file extension
            file_extension = pathlib.Path(file.filename).suffix
            filename = "File" + str(round(time.time())) + file_extension
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            updateQuestion(id, question, filename, file_extension, marks)

            question = request.form['question3']
            file = request.files['file3']
            marks = request.form['marks3']
            id = request.form['id3']
            # function to return the file extension
            file_extension = pathlib.Path(file.filename).suffix
            filename = "File" + str(round(time.time())) + file_extension
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            updateQuestion(id, question, filename, file_extension, marks)

            question = request.form['question4']
            file = request.files['file4']
            marks = request.form['marks4']
            id = request.form['id4']
            # function to return the file extension
            file_extension = pathlib.Path(file.filename).suffix
            filename = "File" + str(round(time.time())) + file_extension
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            updateQuestion(id, question, filename, file_extension, marks)

            question = request.form['question5']
            file = request.files['file5']
            marks = request.form['marks5']
            id = request.form['id5']
            # function to return the file extension
            file_extension = pathlib.Path(file.filename).suffix
            filename = "File" + str(round(time.time())) + file_extension
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            updateQuestion(id, question, filename, file_extension, marks)
            """
        return redirect(url_for("teacheraddquestion"))
    except Exception as e:
        return str(e)

@app.route('/adminnotifyteacher2', methods=['POST','GET'])
def adminnotifyteacher2():
    try:
        msg, flag = "", True
        print("Add New Teacher page")

        if request.method == 'POST':
            # Retrieve form data using get() to avoid KeyError
            teacherid = request.form.get('teacherid')
            fname = request.form.get('fname')
            lname = request.form.get('lname')
            email = request.form.get('email')
            phnum = request.form.get('phnum')
            dept = request.form.get('dept')
            address = request.form.get('address')
            classname = request.form.get('classname')
            subjectname = request.form.get('subjectname')

            print("Class Name: ", classname)
            print("Subject Name: ", subjectname)

            db = firestore.client()
            newdb_ref = db.collection('newquestion')
            reportdata = newdb_ref.get()

            for doc in reportdata:
                temp = doc.to_dict()
                if temp['ClassName'] == classname and temp['SubjectName'] == subjectname:
                    flag = False
                    break

            if flag:
                for x in range(1, 6):
                    slno = "Question" + str(x)
                    date_time = getDateTime()
                    id = str(random.randint(1000, 9999))
                    json = {
                        'id': id, 
                        'FirstName': fname, 
                        'LastName': lname,
                        'TeacherId': teacherid,
                        'EmailId': email, 
                        'PhoneNumber': phnum,
                        'Address': address, 
                        'Department': dept,
                        'ClassName': classname, 
                        'SubjectName': subjectname,
                        'Question': "", 
                        'FileName': "", 
                        'SlNo': slno,
                        'Marks': "", 
                        'Answer': "", 
                        "Status": 'NotUpdated',
                        'DateTime': date_time
                    }
                    newdb_ref.document(id).set(json)
            else:
                msg = "Already Notified on this Subject"
                data = db.collection('newteacher').document(teacherid).get().to_dict()
                return render_template("adminnotifyteacher1.html", data=data, msg=msg, 
                                       depts=depts, classnames=classnames,
                                       class1subjects=class1subjects, class2subjects=class2subjects,
                                       class3subjects=class3subjects, class4subjects=class4subjects,
                                       class5subjects=class5subjects, class6subjects=class6subjects)

            print("Teacher Notified Successfully")
            return redirect(url_for('adminviewquestions'))  # Correct redirect path
    except Exception as e:
        return str(e)

@app.route('/adminaddteacher', methods=['POST','GET'])
def adminaddteacher():
    try:
        msg=""
        print("Add New Tecaher page")
        if request.method == 'POST':
            fname = request.form['fname']
            lname = request.form['lname']
            uname = request.form['uname']
            pwd = request.form['pwd']
            email = request.form['email']
            phnum = request.form['phnum']
            dept = request.form['dept']
            address = request.form['address']
            classname = request.form['classname']
            subjectname = request.form['subjectname']
            id = str(random.randint(1000, 9999))
            encode = base64.b64encode(pwd.encode("utf-8"))
            print("str-byte : ", encode)
            print("Class Name : ", classname)
            print("Subject Name : ", subjectname)
            json = {'id': id, 'FirstName': fname, 'LastName': lname,
                        'UserName': uname, 'Password': encode,
                        'EmailId': email, 'PhoneNumber': phnum,
                        'Address': address, 'Department':dept,
                    'ClassName':classname, 'SubjectName':subjectname}
            db = firestore.client()
            newuser_ref = db.collection('newteacher')
            newuser_ref.document(id).set(json)
            print("Teacher Inserted Success")
            msg = "New Teacher Added Success"
        return render_template("adminaddteacher.html", msg=msg,depts=depts,
               classnames=classnames, class1subjects = class1subjects,
               class2subjects = class2subjects, class3subjects = class3subjects,
               class4subjects = class4subjects, class5subjects = class5subjects,
               class6subjects = class6subjects)
    except Exception as e:
        return str(e)


@app.route('/teacheraddstudent', methods=['POST','GET'])
def teacheraddstudent():
    try:
        msg=""
        cnt=getNotificationCnt()
        print("Add New User page")
        # dept = session['dept']
        dept = session.get('dept', None)  
        if request.method == 'POST':
            fname = request.form['fname']
            lname = request.form['lname']
            uname = request.form['uname']
            pwd = request.form['pwd']
            email = request.form['email']
            phnum = request.form['phnum']
            address = request.form['address']
            classname = request.form['classname']
            dept = request.form.get('department', dept)
            if not dept:
                return "Error: Department selection is required"
            id = str(random.randint(1000, 9999))
            #encMessage = fernet.encrypt(pwd.encode())
            encode = base64.b64encode(pwd.encode("utf-8"))
            print("str-byte : ", encode)
            json = {'id': id, 'FirstName': fname, 'LastName': lname,
                        'UserName': uname, 'Password': encode,
                        'EmailId': email, 'PhoneNumber': phnum,
                        'Address': address,'Department':dept,
                    'ClassName':classname}
            db = firestore.client()
            newuser_ref = db.collection('newuser')
            newuser_ref.document(id).set(json)
            print("User Inserted Success")
            # msg = "New User Added Success"
        return render_template("teacheraddstudent.html",  dept=dept,cnt=cnt)
    except Exception as e:
        return str(e)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/contact', methods=['POST','GET'])
def contactpage():
    try:
        msg=""
        if request.method == 'POST':
            cname = str(request.form['cname'])# + " " + str(request.form['lname'])
            subject = request.form['subject']
            message = request.form['message']
            phnum = request.form['phnum']
            email = request.form['email']
            id = str(random.randint(1000, 9999))
            json = {'id': id,
                    'ContactName': cname, 'Subject': subject,
                    'Message': message,'PhoneNumber': phnum,
                    'EmailId': email}
            db = firestore.client()
            newdb_ref = db.collection('newcontact')
            id = json['id']
            newdb_ref.document(id).set(json)
            body = "Thank you for contacting us, " + str(cname) + " We will keep in touch with in 24 Hrs"
            receipients = [email]
            send_email(subject,body,recipients=receipients)
            msg = "New Contact Added Success"
        return render_template("contact.html", msg=msg)
    except Exception as e:
        return str(e)

@app.route('/teacheraddquestion', methods=['POST','GET'])
def teacheraddquestion():
    try:
        userid = session['userid']
        db = firestore.client()
        newdata_ref = db.collection('newquestion')
        newdata = newdata_ref.get()
        data=[]
        cnt=getNotificationCnt()
        classnames=[]
        for x in newdata:
            temp = x.to_dict()
            #if (str(temp['TeacherId']) == str(userid) and str(temp['Status']) == 'NotUpdated' and
            #    str(temp['ClassName']) not in classnames):
            if (str(temp['TeacherId']) == str(userid) and str(temp['Status']) == 'NotUpdated'):
                classnames.append(str(temp['ClassName']))
                data.append(temp)
        print("Users Data " , data)
        print("Count ", cnt)
        return render_template("teacheraddquestion.html", data=data, cnt=cnt, id=userid)
    except Exception as e:
        return str(e)

@app.route('/adminviewusers', methods=['POST','GET'])
def adminviewusers():
    try:
        db = firestore.client()
        newdata_ref = db.collection('newuser')
        newdata = newdata_ref.get()
        data=[]
        for doc in newdata:
            data.append(doc.to_dict())
        print("Users Data " , data)
        return render_template("adminviewusers.html", data=data)
    except Exception as e:
        return str(e)

@app.route('/teacherviewstudents', methods=['POST','GET'])
def teacherviewstudents():
    try:
        cnt = getNotificationCnt()
        db = firestore.client()
        newdata_ref = db.collection('newuser')
        newdata = newdata_ref.get()
        data=[]
        for doc in newdata:
            data.append(doc.to_dict())
        print("Students Data " , data)
        return render_template("teacherviewstudents.html", data=data,cnt=cnt)
    except Exception as e:
        return str(e)

@app.route('/teacherupdateanswers', methods=['POST','GET'])
def teacherupdateanswers():
    try:
        cnt = getNotificationCnt()
        db = firestore.client()
        newdata_ref = db.collection('newuser')
        newdata = newdata_ref.get()
        data=[]
        for doc in newdata:
            data.append(doc.to_dict())
        print("Students Data " , data)
        return render_template("teacherupdateanswers.html", data=data,cnt=cnt)
    except Exception as e:
        return str(e)

@app.route('/adminnotifyteacher', methods=['POST','GET'])
def adminnotifyteacher():
    try:
        db = firestore.client()
        newdata_ref = db.collection('newteacher')
        newdata = newdata_ref.get()
        data = []
        for doc in newdata:
            data.append(doc.to_dict())
        print("Teacher Data: ", data)
        return render_template("adminnotifyteacher.html", data=data)
    except Exception as e:
        return str(e)

@app.route('/adminnotifyteacher1', methods=['POST','GET'])
def adminnotifyteacher1():
    try:
        id = request.args.get('id')  # Use get() to avoid errors if 'id' is missing
        db = firestore.client()
        data = db.collection('newteacher').document(id).get().to_dict()

        print("Teacher Data: ", data)
        return render_template("adminnotifyteacher1.html", data=data, depts=depts, 
                               classnames=classnames, class1subjects=class1subjects,
                               class2subjects=class2subjects, class3subjects=class3subjects,
                               class4subjects=class4subjects, class5subjects=class5subjects,
                               class6subjects=class6subjects)
    except Exception as e:
        return str(e)

@app.route('/adminviewteachers', methods=['POST','GET'])
def adminviewteachers():
    try:
        db = firestore.client()
        newdata_ref = db.collection('newteacher')
        newdata = newdata_ref.get()
        data=[]
        for doc in newdata:
            data.append(doc.to_dict())
        print("Teacher Data " , data)
        return render_template("adminviewteachers.html", data=data)
    except Exception as e:
        return str(e)

@app.route('/adminviewquestions', methods=['POST','GET'])
def adminviewquestions():
    try:
        db = firestore.client()
        newdata_ref = db.collection('newquestion')
        newdata = newdata_ref.order_by("DateTime").get()
        data=[]
        for doc in newdata:
            data.append(doc.to_dict())
        print("Question Data " , data)
        return render_template("adminviewquestions.html", data=data)
    except Exception as e:
        return str(e)

@app.route('/teacherviewquestions', methods=['POST','GET'])
def teacherviewquestions():
    try:
        cnt = getNotificationCnt()
        db = firestore.client()
        newdata_ref = db.collection('newquestion')
        newdata = newdata_ref.get()
        data=[]
        for doc in newdata:
            data.append(doc.to_dict())
        print("Question Data " , data)
        return render_template("teacherviewquestions.html", data=data,cnt=cnt)
    except Exception as e:
        return str(e)

@app.route('/adminviewcontacts', methods=['POST','GET'])
def adminviewcontacts():
    try:
        db = firestore.client()
        newdata_ref = db.collection('newcontact')
        newdata = newdata_ref.get()
        data=[]
        for doc in newdata:
            data.append(doc.to_dict())
        print("Contact Data " , data)
        return render_template("adminviewcontacts.html", data=data)
    except Exception as e:
        return str(e)


@app.route('/adminviewreports', methods=['POST','GET'])
def adminviewreports():
    try:
        db = firestore.client()
        newdata_ref = db.collection('newuser')
        newdata = newdata_ref.get()
        data=[]
        for doc in newdata:
            temp = doc.to_dict()
            data.append(temp)
        """
        passcount, failcount = 0, 0
        for doc in newdata:
            temp = doc.to_dict()
            data.append(temp)
            if (float(temp['ObtainedPercentage']) > 50.00):
                passcount += 1
            else:
                failcount += 1
        print("Report Data ", data)
        graph_data = [
            {"label": "Pass", "y": passcount},
            {"label": "Fail", "y": failcount}
        ]
        """
        print("Report Data " , data)
        return render_template("adminviewreports.html", data=data)
    except Exception as e:
        return str(e)

@app.route('/teacherviewreports', methods=['POST','GET'])
def teacherviewreports():
    try:
        db = firestore.client()
        newdata_ref = db.collection('newuser')
        newdata = newdata_ref.get()
        data=[]
        for doc in newdata:
            temp = doc.to_dict()
            data.append(temp)
        print("Report Data " , data)
        return render_template("teacherviewreports.html", data=data)
    except Exception as e:
        return str(e)

@app.route('/teachermainpage')
def teachermainpage():
    try:
        cnt=getNotificationCnt()
        return render_template("teachermainpage.html",cnt=cnt)
    except Exception as e:
        return str(e)

def getNotificationCnt():
    userid = session['userid']
    db = firestore.client()
    newdata_ref = db.collection('newquestion')
    newdata = newdata_ref.get()
    cnt,subjectnames = 0,[]
    for x in newdata:
        temp = x.to_dict()
        if (str(temp['TeacherId']) == str(userid) and str(temp['Status']) == 'NotUpdated' and
                str(temp['SubjectName']) not in subjectnames):
            subjectnames.append(str(temp['SubjectName']))
            cnt += 1
    return cnt
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.debug = True
    app.run()