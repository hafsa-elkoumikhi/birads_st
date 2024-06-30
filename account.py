import streamlit as st
from tensorflow.keras.models import load_model
from streamlit_gsheets import GSheetsConnection
from PIL import Image
import numpy as np
import pandas as pd
import pydicom
import os
from datetime import datetime
import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account


def app():
    # Load your trained model
    model = load_model('model_bi_aTL.h5')

    # Establish Google Sheets connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Fetch existing data from the Google Sheets
    existing_data = conn.read(worksheet="birads", usecols=list(range(5)), ttl=5)
    


    def preprocess_image(image):
        image = image.resize((150, 150))  # Resize the image to match the input size of your model
        image = np.array(image)
        
        # Normalize the image
        image = image / 255.0  
        
        # Ensure RGB format (remove alpha channel if present)
        if image.shape[2] == 4:  # Check if image has alpha channel (PNG)
            image = image[:, :, :3]  # Keep only RGB channels
        
        image = np.expand_dims(image, axis=0)  # Add batch dimension
        return image

    # Function to convert DICOM to PNG and return PIL Image
    def dicom_to_png(dicom_file):
        dicom = pydicom.dcmread(dicom_file)
        if 'ModalityLUTSequence' in dicom:
            modality_lut = dicom.ModalityLUTSequence[0].LUTDescriptor
            pixel_array = dicom.pixel_array * modality_lut.RescaleSlope + modality_lut.RescaleIntercept
        else:
            pixel_array = dicom.pixel_array
        
        # Normalize pixel values to 8-bit depth
        pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array)) * 255
        pixel_array = pixel_array.astype(np.uint8)
        
        # Convert pixel array to image
        image = Image.fromarray(pixel_array)
        
        return image

    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'service_account.json'
    PARENT_FOLDER_ID = '1jL1K5KiFInIN6wxlmEtCxZgR0_RcLy2J'


    def authenticate():
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return creds

    # Function to upload photo to Google Drive
    def upload_photo(file_path):
        creds = authenticate()
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [PARENT_FOLDER_ID]  # Replace with your parent folder ID
        }


        try:
            file = service.files().create(
                body=file_metadata,
                media_body=file_path
            ).execute()

            return f"Uploaded Image File ID: {file.get('id')}"
        except Exception as e:
            return f"An error occurred: {e}"



    # BIRADS category mapping
    birads_mapping = {
        0: "BIRADS 1",
        1: "BIRADS 2",
        2: "BIRADS 3",
        3: "BIRADS 4",
        4: "BIRADS 5"
    }

    # Create a folder to save uploads if it doesn't exist
    UPLOAD_FOLDER = 'uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Function to save feedback data
    def save_feedback(image_filename, birads_category, feedback_text, correct_class=None):
        feedback_data = pd.DataFrame({
            'Image Filename': [image_filename],
            'Predicted BIRADS': [birads_category],
            'Feedback': [feedback_text],
            'Correct BIRADS': [birads_mapping[correct_class] if correct_class is not None else ''],
            'Timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        # Add the new vendor data to the existing data
        updated_df = pd.concat([existing_data, feedback_data], ignore_index=True)

        # Update Google Sheets with the new vendor data
        conn.update(worksheet="birads", data=updated_df)

        st.success("Vendor details successfully submitted!")

        # Upload image to Google Drive
        try:
            upload_result = upload_photo(os.path.join(UPLOAD_FOLDER, image_filename))
            st.success(upload_result)
        except Exception as e:
            st.error(f"Error uploading image to Google Drive: {e}")


    # Define the function to predict the BIRADS category
    def predict_birads(image):
        processed_image = preprocess_image(image)
        prediction = model.predict(processed_image)
        birads_category_index = np.argmax(prediction)
        return birads_mapping[birads_category_index]

    # Streamlit app interface
    st.title("BIRADS Classification")
    st.write("Upload a mammogram image (JPEG, PNG, DICOM) to classify its BIRADS category")

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "dcm"])

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()

        if file_extension == 'dcm':
            image = dicom_to_png(uploaded_file)
        else:
            image = Image.open(uploaded_file)
        
        st.image(image, caption='Uploaded Image', use_column_width=True)
        st.write("Classifying...")
        birads_category = predict_birads(image)
        st.write(f"The predicted BIRADS category is: {birads_category}")

        # Ask for feedback
        st.write("Please provide your feedback:")
        feedback = st.radio("Is the predicted BIRADS category correct?", ('', 'Yes', 'No'), index=0)

        if feedback == 'No':
            st.write("Please select the correct BIRADS category:")
            correct_class = st.selectbox("Select the correct BIRADS category:", list(birads_mapping.values()))
            
            # Show the Submit Feedback button only when the correct class is selected
            if st.button("Submit Feedback"):
                image_filename = f"uploaded_image_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"    
                image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                if uploaded_file.type == 'application/dicom':
                    image.save(image_path)  # Save the DICOM converted to PNG to uploads folder
                else:
                    image.save(image_path)  # Save the uploaded image to uploads folder
                save_feedback(image_filename, birads_category, feedback, list(birads_mapping.keys())[list(birads_mapping.values()).index(correct_class)])
                st.write("Thank you for your feedback!")

        elif feedback == 'Yes':
            # Directly save the feedback if the predicted category is correct
            if st.button("Submit Feedback"):
                image_filename = f"uploaded_image_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                if uploaded_file.type == 'application/dicom':
                    image.save(image_path)  # Save the DICOM converted to PNG to uploads folder
                else:
                    image.save(image_path)
                save_feedback(image_filename, birads_category, feedback)
                st.write("Thank you for your feedback!")
