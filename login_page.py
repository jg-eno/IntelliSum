import streamlit as st
import sqlite3

st.set_page_config(page_title="IntelliSum - Email Summarizer", page_icon="✉️")

def add_custom_css():
    st.markdown("""
        <style>
        .stButton > button {
            background-color: #263238;
            color: white;
            border-radius: 5px;
            font-size: 18px;
            padding: 10px;
        }
        .stTextInput > div > input {
            border: 2px solid #ccc;
            border-radius: 5px;
            padding: 10px;
        }
        .title-text {
            font-family: 'Arial', sans-serif;
            text-align: center;
            margin-top: 20px;
            color: orange;
        }
        .subheader-text {
            text-align: center;
            font-size: 20px;
            color: #7f8c8d;
            margin-top: -10px;
            margin-bottom: 20px;
        }
        .custom-form-container input {
            width: 100%;
            padding: 12px;
            border-radius: 5px;
            border: 1px solid #ccc;
            margin-bottom: 20px;
            font-size: 16px;
        }
        .custom-form-container button {
            color: white;
            padding: 12px;
            border-radius: 5px;
            border: none;
            font-size: 16px;
            cursor: pointer;
        }
        .custom-form-container button:hover {
            background-color: #2980b9;
        }
        [data-testid="stForm"] {
            background: #202020;
        }
        [data-testid="stMain"] {
            background: black;
        }
        [data-testid="stHeader"] {
            background: black;
        }
        [data-testid="stBaseButton-secondaryFormSubmit"] {
            background-color: #263238;
            color: white;
            border-radius: 5px;
            font-size: 18px;
            padding: 10px;
        }
        h3 {
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

add_custom_css()

st.markdown("<h1 class='title-text'>Welcome to IntelliSum</h1>", unsafe_allow_html=True)
st.markdown("<h4 class='subheader-text'>Summarize your emails instantly</h4>", unsafe_allow_html=True)


def login(email, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

def login_page():
    st.markdown("<div class='custom-form-container'>", unsafe_allow_html=True)
    st.write("### Login")

    with st.form(key='login_form'):
        email = st.text_input("Email", placeholder="Enter your email", key="email_input")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="password_input")
        submit_button = st.form_submit_button(label="Login")

    if submit_button:
        if login(email, password):
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.success("Login successful!")
        else:
            st.error("Invalid email or password. Please try again.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        landingPage(st.session_state.user_email)
    else:
        login_page()

if __name__ == "__main__":
    main()
