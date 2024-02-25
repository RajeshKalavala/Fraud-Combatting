import streamlit as st
import pickle
import string
from nltk.corpus import stopwords
import nltk
from nltk.stem.porter import PorterStemmer
import pandas as pd
import re
from twilio.rest import Client

account_sid = "AC8b6ee4efcb96f82aa4f2c0fbe40714f1"
auth_token = "7864b2ecf43b55a3c61d1f16edc4c5d8"
verify_sid = "VAf898b308bdafddd6365c2dd89e283fba"
verified_number = "+19139919000"

client = Client(account_sid, auth_token)

def send_sms_verification(number):
    verification = client.verify.v2.services(verify_sid) \
        .verifications \
        .create(to=number, channel="sms")
    return verification

def check_sms_verification(number, code):
    verification_check = client.verify.v2.services(verify_sid) \
        .verification_checks \
        .create(to=number, code=code)
    return verification_check

combined = pd.read_csv('combined.csv')
st.markdown("""
<style>
/* Add your CSS styles here */
h1 { color: blue; }
/* Example to change the background color */
body { background-color: #f0f2f6; }
/* Adjust the text area */
textarea { background-color: #fff; }
</style>
""", unsafe_allow_html=True)
ps = PorterStemmer()

@st.cache_data
def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)

    y = []
    for i in text:
        if i.isalnum():
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        if i not in stopwords.words('english') and i not in string.punctuation:
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        y.append(ps.stem(i))

    return " ".join(y)

@st.cache_data
def load_model():
    tfidf = pickle.load(open('vectorizer.pkl', 'rb'))
    model = pickle.load(open('model.pkl', 'rb'))
    return tfidf, model

st.title("Welcome to my app of Fraud Combatting- Open Banking Safety and Fraud mitigation")
st.subheader("We will start with Email/SMS Spam Classifier")

st.title("Email/SMS Spam Classifier")

input_sms = st.text_area("Enter the message")
predict_button = st.button('Predict')

if 'spam_result' not in st.session_state:
    st.session_state.spam_result = None

if predict_button:
    tfidf, model = load_model()
    transformed_sms = transform_text(input_sms)
    vector_input = tfidf.transform([transformed_sms])
    result = model.predict(vector_input)[0]
    st.session_state.spam_result = result

    message = input_sms
    url_pattern = r'https?://([a-zA-Z0-9.-]+)'
    matched_links = re.findall(url_pattern, message)
    if matched_links in combined['domains'].values:
        st.markdown("<h1 style='color:red;'>THIS IS SPAM LINK FOUND IN OUR DATABASE. VERIFICATION Failed</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='color:green;'>THIS LINK IS NOT PRESENT IN OUR DATABASE. VERIFICATION Passed</h1>", unsafe_allow_html=True)

if st.session_state.spam_result == 1:
    st.markdown("<h1 style='color:red;'>THIS MESSAGE IS SPAM AS PER OUR MODEL. VERIFICATION Failed</h1>", unsafe_allow_html=True)
    st.subheader("WARNING ⚠ - This link may be dangerous")
    st.subheader("You have to proceed to MFA for continuing this transaction.")

    name = st.text_area("Name")
    mobile = st.text_area("Mobile Number:")
    otp_button = st.button("Get OTP")

    if 'entered_otp' not in st.session_state:
        st.session_state.entered_otp = None

    if 'otp_verified' not in st.session_state:
        st.session_state.otp_verified = False

    if otp_button:
        verification = send_sms_verification(verified_number)
        st.session_state.verification_sid = verification.sid
        st.subheader("OTP has been sent to your mobile.")


        
    if st.session_state.entered_otp is None and not st.session_state.otp_verified:
        entered_otp = st.text_input("Enter OTP")
        check_otp_button = st.button("Validate OTP")

        if check_otp_button:
            st.subheader("Please wait while we load")
            if entered_otp:
                verification_check = check_sms_verification(verified_number, entered_otp)

                if verification_check.status == 'approved':
                    st.session_state.otp_verified = True
                    st.markdown("<h1 style='color:green;'>OTP ENTERED IS CORRECT. VERIFICATION Passed.</h1>", unsafe_allow_html=True)
                else:
                    st.session_state.otp_verified = False
                    st.markdown("<h1 style='color:red;'>OTP ENTERED IS INCORRECT. VERIFICATION Failed.</h1>", unsafe_allow_html=True)
            else:
                st.warning("Please enter the OTP before validating.")

elif st.session_state.spam_result == 0:
    st.markdown("<h1 style='color:green;'>THIS MESSAGE IS NOT SPAM AS PER OUR MODEL. VERIFICATION Passed</h1>", unsafe_allow_html=True)
    st.subheader("This step requires further inspection. Wait while we confirm your transaction")
