"""
Fake Signature Detection System using Neural Network
Main Application File - Streamlit Interface
"""

import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime
import numpy as np
from PIL import Image
import cv2
import io
import base64

# Page configuration
st.set_page_config(
    page_title="Signature Verification System",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database initialization
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('signature_system.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        user_type TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )
    ''')
    
    # Signature templates table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS signature_templates (
        template_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        signature_image BLOB NOT NULL,
        feature_vector BLOB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # Verification logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS verification_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        test_signature BLOB NOT NULL,
        result TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        verification_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # System settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_settings (
        setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_name TEXT UNIQUE NOT NULL,
        setting_value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create default admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_password = hash_password('admin123')
        cursor.execute('''
        INSERT INTO users (username, password_hash, full_name, email, user_type)
        VALUES (?, ?, ?, ?, ?)
        ''', ('admin', admin_password, 'System Administrator', 'admin@system.com', 'admin'))
    
    conn.commit()
    conn.close()

# Helper functions
def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    """Verify user credentials"""
    conn = sqlite3.connect('signature_system.db')
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute('''
    SELECT user_id, username, full_name, user_type 
    FROM users 
    WHERE username = ? AND password_hash = ? AND is_active = 1
    ''', (username, password_hash))
    
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(username, password, full_name, email):
    """Register new user"""
    try:
        conn = sqlite3.connect('signature_system.db')
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute('''
        INSERT INTO users (username, password_hash, full_name, email)
        VALUES (?, ?, ?, ?)
        ''', (username, password_hash, full_name, email))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return True, user_id
    except sqlite3.IntegrityError:
        return False, "Username or email already exists"

def preprocess_signature(image):
    """Preprocess signature image for neural network"""
    # Convert PIL image to numpy array
    img_array = np.array(image)
    
    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply threshold to remove background
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Remove noise
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Resize to standard size (128x128)
    resized = cv2.resize(processed, (128, 128))
    
    # Normalize pixel values
    normalized = resized / 255.0
    
    return normalized

def extract_simple_features(image):
    """Extract simple features from signature image (simplified version)"""
    processed = preprocess_signature(image)
    
    # Simple feature extraction
    features = []
    
    # Pixel density
    features.append(np.mean(processed))
    
    # Aspect ratio (height to width ratio of non-zero pixels)
    non_zero = np.argwhere(processed > 0.5)
    if len(non_zero) > 0:
        h_range = non_zero[:, 0].max() - non_zero[:, 0].min()
        w_range = non_zero[:, 1].max() - non_zero[:, 1].min()
        features.append(h_range / (w_range + 1))
    else:
        features.append(0)
    
    # Horizontal projection
    h_proj = np.sum(processed, axis=1)
    features.append(np.std(h_proj))
    
    # Vertical projection
    v_proj = np.sum(processed, axis=0)
    features.append(np.std(v_proj))
    
    # Number of transitions (black to white)
    transitions = 0
    for row in processed:
        for i in range(len(row) - 1):
            if (row[i] > 0.5 and row[i+1] <= 0.5) or (row[i] <= 0.5 and row[i+1] > 0.5):
                transitions += 1
    features.append(transitions / 1000.0)  # Normalize
    
    return np.array(features)

def simple_signature_comparison(template_features, test_features):
    """Simple signature comparison using Euclidean distance"""
    # Calculate Euclidean distance
    distance = np.linalg.norm(template_features - test_features)
    
    # Convert distance to similarity score (0-100%)
    # Lower distance = higher similarity
    max_distance = 10.0  # Arbitrary maximum for normalization
    similarity = max(0, (1 - min(distance, max_distance) / max_distance)) * 100
    
    return similarity

def save_signature_template(user_id, image):
    """Save signature template to database"""
    conn = sqlite3.connect('signature_system.db')
    cursor = conn.cursor()
    
    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    # Extract features
    features = extract_simple_features(image)
    feature_bytes = features.tobytes()
    
    cursor.execute('''
    INSERT INTO signature_templates (user_id, signature_image, feature_vector)
    VALUES (?, ?, ?)
    ''', (user_id, img_bytes, feature_bytes))
    
    conn.commit()
    conn.close()

def get_user_templates(user_id):
    """Get all templates for a user"""
    conn = sqlite3.connect('signature_system.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT template_id, signature_image, feature_vector, created_at
    FROM signature_templates
    WHERE user_id = ? AND is_active = 1
    ORDER BY created_at DESC
    ''', (user_id,))
    
    templates = cursor.fetchall()
    conn.close()
    return templates

def verify_signature(user_id, test_image):
    """Verify signature against user templates"""
    templates = get_user_templates(user_id)
    
    if not templates:
        return "No Template", 0.0
    
    # Extract features from test signature
    test_features = extract_simple_features(test_image)
    
    # Compare with all templates and get average similarity
    similarities = []
    for template in templates:
        template_features = np.frombuffer(template[2], dtype=np.float64)
        similarity = simple_signature_comparison(template_features, test_features)
        similarities.append(similarity)
    
    avg_similarity = np.mean(similarities)
    
    # Determine result based on threshold
    threshold = 70.0  # 70% similarity threshold
    if avg_similarity >= threshold:
        result = "Genuine"
    else:
        result = "Forged"
    
    return result, avg_similarity

def log_verification(user_id, test_image, result, confidence):
    """Log verification to database"""
    conn = sqlite3.connect('signature_system.db')
    cursor = conn.cursor()
    
    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    test_image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    cursor.execute('''
    INSERT INTO verification_logs (user_id, test_signature, result, confidence_score)
    VALUES (?, ?, ?, ?)
    ''', (user_id, img_bytes, result, confidence))
    
    conn.commit()
    conn.close()

def get_verification_history(user_id, limit=10):
    """Get verification history for user"""
    conn = sqlite3.connect('signature_system.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT log_id, result, confidence_score, verification_time
    FROM verification_logs
    WHERE user_id = ?
    ORDER BY verification_time DESC
    LIMIT ?
    ''', (user_id, limit))
    
    history = cursor.fetchall()
    conn.close()
    return history

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'full_name' not in st.session_state:
    st.session_state.full_name = None
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# Initialize database
init_database()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.25rem;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# Login/Registration Page
if not st.session_state.logged_in:
    st.markdown('<h1 class="main-header">✍️ Signature Verification System</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Login", use_container_width=True):
                if login_username and login_password:
                    user = verify_user(login_username, login_password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.full_name = user[2]
                        st.session_state.user_type = user[3]
                        st.session_state.page = 'dashboard'
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
        
        st.info("**Default Admin Login:** Username: `admin`, Password: `admin123`")
    
    with tab2:
        st.subheader("Create New Account")
        
        reg_full_name = st.text_input("Full Name")
        reg_email = st.text_input("Email Address")
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_password_confirm = st.text_input("Confirm Password", type="password")
        
        if st.button("Register", use_container_width=True):
            if not all([reg_full_name, reg_email, reg_username, reg_password, reg_password_confirm]):
                st.warning("Please fill in all fields")
            elif reg_password != reg_password_confirm:
                st.error("Passwords do not match")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                success, message = register_user(reg_username, reg_password, reg_full_name, reg_email)
                if success:
                    st.success("Registration successful! Please login with your credentials.")
                else:
                    st.error(message)

# Main Application (After Login)
else:
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        st.write(f"**Welcome, {st.session_state.full_name}!**")
        st.write(f"*{st.session_state.user_type.title()}*")
        st.divider()
        
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()
        
        if st.button("✅ Verify Signature", use_container_width=True):
            st.session_state.page = 'verify'
            st.rerun()
        
        if st.button("📂 My Templates", use_container_width=True):
            st.session_state.page = 'templates'
            st.rerun()
        
        if st.button("📊 History", use_container_width=True):
            st.session_state.page = 'history'
            st.rerun()
        
        if st.session_state.user_type == 'admin':
            st.divider()
            st.write("**Admin Functions**")
            if st.button("👥 Manage Users", use_container_width=True):
                st.session_state.page = 'admin_users'
                st.rerun()
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.full_name = None
            st.session_state.user_type = None
            st.session_state.page = 'login'
            st.rerun()
    
    # Dashboard Page
    if st.session_state.page == 'dashboard':
        st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)
        
        # Statistics
        templates = get_user_templates(st.session_state.user_id)
        history = get_verification_history(st.session_state.user_id, limit=100)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Signature Templates", len(templates))
        
        with col2:
            st.metric("Total Verifications", len(history))
        
        with col3:
            genuine_count = sum(1 for h in history if h[1] == 'Genuine')
            st.metric("Genuine Signatures", genuine_count)
        
        st.divider()
        
        # Quick Actions
        st.subheader("Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Verify New Signature", use_container_width=True):
                st.session_state.page = 'verify'
                st.rerun()
        
        with col2:
            if st.button("📂 Manage Templates", use_container_width=True):
                st.session_state.page = 'templates'
                st.rerun()
        
        with col3:
            if st.button("📊 View Full History", use_container_width=True):
                st.session_state.page = 'history'
                st.rerun()
        
        # Recent Activity
        st.divider()
        st.subheader("Recent Verification Activity")
        
        recent_history = get_verification_history(st.session_state.user_id, limit=5)
        
        if recent_history:
            for log in recent_history:
                col1, col2, col3 = st.columns([2, 2, 3])
                
                with col1:
                    if log[1] == 'Genuine':
                        st.success(f"✓ {log[1]}")
                    else:
                        st.error(f"✗ {log[1]}")
                
                with col2:
                    st.write(f"**{log[2]:.1f}%** confidence")
                
                with col3:
                    st.write(f"*{log[3]}*")
                
                st.divider()
        else:
            st.info("No verification history yet. Start by verifying a signature!")
    
    # Verify Signature Page
    elif st.session_state.page == 'verify':
        st.markdown('<h1 class="main-header">✅ Verify Signature</h1>', unsafe_allow_html=True)
        
        # Check if user has templates
        templates = get_user_templates(st.session_state.user_id)
        
        if not templates:
            st.warning("⚠️ You don't have any signature templates yet. Please add at least one template before verifying signatures.")
            if st.button("Go to Templates"):
                st.session_state.page = 'templates'
                st.rerun()
        else:
            st.info(f"You have {len(templates)} signature template(s) in the system.")
            
            uploaded_file = st.file_uploader("Upload Signature to Verify", type=['png', 'jpg', 'jpeg'])
            
            if uploaded_file is not None:
                # Display uploaded image
                image = Image.open(uploaded_file)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Original Signature")
                    st.image(image, use_container_width=True)
                
                with col2:
                    st.subheader("Processed Signature")
                    processed = preprocess_signature(image)
                    st.image(processed, use_container_width=True, clamp=True)
                
                st.divider()
                
                if st.button("🔍 Verify Signature", use_container_width=True):
                    with st.spinner("Verifying signature..."):
                        result, confidence = verify_signature(st.session_state.user_id, image)
                        
                        # Log verification
                        log_verification(st.session_state.user_id, image, result, confidence)
                        
                        # Display result
                        st.subheader("Verification Result")
                        
                        if result == "Genuine":
                            st.markdown(f'<div class="success-box"><h2>✅ GENUINE SIGNATURE</h2><p>Confidence Score: <strong>{confidence:.1f}%</strong></p></div>', unsafe_allow_html=True)
                        elif result == "Forged":
                            st.markdown(f'<div class="error-box"><h2>❌ FORGED SIGNATURE</h2><p>Confidence Score: <strong>{confidence:.1f}%</strong></p></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="info-box"><h2>ℹ️ NO TEMPLATE</h2><p>Please add signature templates first.</p></div>', unsafe_allow_html=True)
                        
                        # Confidence meter
                        st.progress(confidence / 100)
                        
                        st.info("This verification has been saved to your history.")
    
    # Templates Page
    elif st.session_state.page == 'templates':
        st.markdown('<h1 class="main-header">📂 Signature Templates</h1>', unsafe_allow_html=True)
        
        templates = get_user_templates(st.session_state.user_id)
        
        st.subheader("Add New Template")
        
        uploaded_template = st.file_uploader("Upload Signature Template", type=['png', 'jpg', 'jpeg'], key="template_upload")
        
        if uploaded_template is not None:
            image = Image.open(uploaded_template)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(image, caption="Template Preview", use_container_width=True)
            
            with col2:
                st.write("**Template Information**")
                st.write(f"Image Size: {image.size}")
                st.write(f"Format: {image.format}")
                
                if st.button("💾 Save Template", use_container_width=True):
                    save_signature_template(st.session_state.user_id, image)
                    st.success("Template saved successfully!")
                    st.rerun()
        
        st.divider()
        
        st.subheader(f"Your Templates ({len(templates)})")
        
        if templates:
            cols = st.columns(3)
            
            for idx, template in enumerate(templates):
                with cols[idx % 3]:
                    # Convert bytes to image
                    img = Image.open(io.BytesIO(template[1]))
                    st.image(img, use_container_width=True)
                    st.caption(f"Added: {template[3][:10]}")
        else:
            st.info("No templates yet. Upload your first signature template above!")
    
    # History Page
    elif st.session_state.page == 'history':
        st.markdown('<h1 class="main-header">📊 Verification History</h1>', unsafe_allow_html=True)
        
        history = get_verification_history(st.session_state.user_id, limit=50)
        
        if history:
            st.write(f"Showing last {len(history)} verifications")
            
            # Create table
            st.dataframe(
                {
                    'ID': [h[0] for h in history],
                    'Result': [h[1] for h in history],
                    'Confidence': [f"{h[2]:.1f}%" for h in history],
                    'Date & Time': [h[3] for h in history]
                },
                use_container_width=True
            )
            
            # Statistics
            st.divider()
            st.subheader("Statistics")
            
            genuine_count = sum(1 for h in history if h[1] == 'Genuine')
            forged_count = sum(1 for h in history if h[1] == 'Forged')
            avg_confidence = np.mean([h[2] for h in history])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Genuine", genuine_count)
            
            with col2:
                st.metric("Forged", forged_count)
            
            with col3:
                st.metric("Avg Confidence", f"{avg_confidence:.1f}%")
        else:
            st.info("No verification history yet.")
    
    # Admin Users Page
    elif st.session_state.page == 'admin_users' and st.session_state.user_type == 'admin':
        st.markdown('<h1 class="main-header">👥 User Management</h1>', unsafe_allow_html=True)
        
        conn = sqlite3.connect('signature_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT user_id, username, full_name, email, user_type, created_at, is_active
        FROM users
        ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        st.dataframe(
            {
                'ID': [u[0] for u in users],
                'Username': [u[1] for u in users],
                'Full Name': [u[2] for u in users],
                'Email': [u[3] for u in users],
                'Type': [u[4] for u in users],
                'Created': [u[5][:10] for u in users],
                'Active': ['Yes' if u[6] else 'No' for u in users]
            },
            use_container_width=True
        )
        
        st.metric("Total Users", len(users))
