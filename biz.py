import streamlit as st
import os
from easyocr import Reader
import re
from PIL import Image
import pandas as pd
from pymysql import connect
import cv2
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt

st.set_page_config(layout='wide')
st.markdown("<h1 style=color:violet><center>Bizcard capstone project</center></h1>",unsafe_allow_html=True)
#st.header(":violet[Bizcard capstone project]")
selected=option_menu(default_index=0,
                     menu_title=None,
                     options=["Overview","Upload","Modify"],
                     icons=["house","cloud-upload-fill","database"],
                     orientation="horizontal")

reader=Reader(['en'])

conn=connect(host='127.0.0.1',user='root',password='yusuff@12345',port=3306,database='bizcard')
cursor=conn.cursor()
create_table='''CREATE TABLE IF NOT EXISTS card_data
                   (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10),
                    image LONGBLOB
                    )'''
cursor.execute(create_table)
conn.commit()

if selected == "Overview":
    
    col1,col2 = st.columns(2)
    with col1:
        st.image("card.png", width = 550)
        st.markdown("#### :green[**Technologies Used :**] Python, easy OCR, Streamlit, SQL, Pandas.")
    with col2:
        st.write("#### :green[**Overview :**] In this streamlit web app you can upload an image of a business card and extract relevant information from it using easyOCR. You can view, modify or delete the extracted data in this app. This app would also allow users to save the extracted information into a database along with the uploaded business card image. The database would be able to store multiple entries, each with its own business card image and extracted information.")

if selected=="Upload":
    st.markdown("<h3>Upload your card</h3>",unsafe_allow_html=True)
    uploaded_image=st.file_uploader(label="Upload",type=['png','jpeg','jpg'],label_visibility="collapsed")
    if uploaded_image is not None:
        def save_card(image):
            with open(os.path.join("uploaded_cards",image.name), "wb") as f:
                f.write(uploaded_image.getbuffer())
        save_card(uploaded_image)
        def img_show(image,res):
            for (bbox, text, prob) in res:
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 255), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (15,15)
            plt.axis('off')
            plt.imshow(image)
        col1,col2=st.columns(2)
        with col1:
            st.markdown("#     ")
            st.markdown("#     ")
            st.write("You have uploaded the card")
            st.image(uploaded_image)
        with col2:
            st.header("  ")
            st.header("  ")
            with st.spinner("Processing your card, Please wait"):
                st.set_option('deprecation.showPyplotGlobalUse', False)
                saved_image=os.getcwd()+"\\"+"uploaded_cards"+"\\" + uploaded_image.name
                st.write(saved_image)
                img=cv2.imread(saved_image)
                res=reader.readtext(img)
                st.write("Image processed and extracted")
                st.pyplot(img_show(img,res))
        saved_img=os.getcwd()+ "\\"+"uploaded_cards"+"\\" + uploaded_image.name
        result = reader.readtext(saved_img,detail = 0,paragraph=False)

        def img_to_binary(file):
            with open(file,'rb') as file:
                binaryData=file.read()
            return binaryData
        data={'company_name':[],
                'card_holder':[],
                'designation':[],
                'mobile_number':[],
                'email':[],
                'website':[],
                'area':[],
                'city':[],
                'state':[],
                'pin_code':[],
                'image':img_to_binary(saved_img)}
        def get_data(res):
            for ind,i in enumerate(res):
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)
                elif "WWW" in i:
                    data["website"] = res[4] +"." + res[5]
                elif "@" in i:
                    data["email"].append(i)
                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) ==2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])
                elif ind == len(res)-1:
                    data["company_name"].append(i)
                elif ind == 0:
                    data["card_holder"].append(i)
                elif ind == 1:
                    data["designation"].append(i)
                if re.findall('^[0-9].+, [a-zA-Z]+',i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+',i):
                    data["area"].append(i)
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*',i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])
                state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
                if state_match:
                     data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
                    data["state"].append(i.split()[-1])
                if len(data["state"])== 2:
                    data["state"].pop(0)        
                if len(i)>=6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]',i):
                    data["pin_code"].append(i[10:])
        get_data(result)
        def create_df(data):
            df = pd.DataFrame(data)
            return df
        df = create_df(data)
        st.success("### Data Extracted!")
        st.write(df)
    if st.button("Store in database"):
        for i,row in df.iterrows():
            sql = """INSERT INTO card_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(sql, tuple(row))
            conn.commit()
        st.success("Stored in database")
if selected=="Modify":
    col1,col2,col3=st.columns([3,3,2])
    st.write("Here you can modify the stored data")
    column1,column2=st.columns(2,gap='large')
    try:
        with column1:
            cursor.execute("select card_holder from card_data")
            result=cursor.fetchall()
            business_cards={}
            for row in result:
                business_cards[row[0]]=row[0]
            card_select=st.selectbox("Select a card holder name to update", list(business_cards.keys()))
            st.markdown("#### Update or modify any data below")
            cursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data WHERE card_holder=%s",
                            (card_select))
            output=cursor.fetchone()
            company_name = st.text_input("Company_Name", output[0])
            card_holder = st.text_input("Card_Holder", output[1])
            designation = st.text_input("Designation", output[2])
            mobile_number = st.text_input("Mobile_Number", output[3])
            email = st.text_input("Email", output[4])
            website = st.text_input("Website", output[5])
            area = st.text_input("Area", output[6])
            city = st.text_input("City", output[7])
            state = st.text_input("State", output[8])
            pin_code = st.text_input("Pin_Code", output[9])
            if st.button("Commit changes to DB"):
                # Update the information for the selected business card in the database
                cursor.execute("""UPDATE card_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                    WHERE card_holder=%s""", (company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,card_select))
                conn.commit()
                st.success("Information updated in database successfully.")
            with column2:
                cursor.execute("SELECT card_holder FROM card_data")
                result = cursor.fetchall()
                business_cards = {}
                for row in result:
                    business_cards[row[0]] = row[0]
                card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))
                st.write(f"### You have selected :green[**{card}'s**] card to delete")
                st.write("#### Proceed to delete this card?")
                if st.button("Yes Delete Business Card"):
                    cursor.execute(f"DELETE FROM card_data WHERE card_holder='{card}'")
                    conn.commit()
                    st.success("Business card information deleted from database.")
    except:
        st.write("There is no data available in database for this selected business card")
    if st.button("View updated data"):
        cursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data")
        updated_df = pd.DataFrame(cursor.fetchall(),columns=["Company_Name","Card_Holder","Designation","Mobile_Number","Email","Website","Area","City","State","Pin_Code"])
        st.write(updated_df)