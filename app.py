"""
Fake Signature Detection System using Neural Network
Enhanced version with ZIP dataset upload
"""

import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import numpy as np
from PIL import Image
import io
import os
import zipfile
import tempfile
import shutil

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
    
    # Training data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_data (
        data_id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_name TEXT NOT NULL,
        signature_image BLOB NOT NULL,
        is_genuine INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def simple_preprocess(image):
    """Simple image preprocessing using PIL only"""
    if image.mode != 'L':
        image = image.convert('L')
    
    image = image.resize((128, 128))
    img_array = np.array(image)
    threshold = 127
    img_array = np.where(img_array < threshold, 0, 255)
    normalized = img_array / 255.0
    
    return normalized

def extract_features(image):
    """Extract simple features from signature"""
    processed = simple_preprocess(image)
    features = []
    
    features.append(np.mean(processed))
    features.append(np.std(processed))
    
    non_zero_count = np.count_nonzero(processed)
    features.append(non_zero_count / (128 * 128))
    
    left_half = processed[:, :64]
    right_half = processed[:, 64:]
    features.append(np.mean(np.abs(left_half - np.fliplr(right_half))))
    
    top_half = processed[:64, :]
    bottom_half = processed[64:, :]
    features.append(np.mean(np.abs(top_half - np.flipud(bottom_half))))
    
    edges = 0
    for i in range(127):
        for j in range(127):
            if abs(processed[i, j] - processed[i+1, j]) > 0.5:
                edges += 1
            if abs(processed[i, j] - processed[i, j+1]) > 0.5:
                edges += 1
    features.append(edges / (128 * 128))
    
    return np.array(features)

def compare_signatures(template_features, test_features):
    """Compare signature features"""
    distance = np.linalg.norm(template_features - test_features)
    max_distance = 2.0
    similarity = max(0, (1 - min(distance, max_distance) / max_distance)) * 100
    return similarity

def load_dataset_from_zip(zip_file):
    """Load dataset from uploaded ZIP file"""
    dataset = []
    genuine_count = 0
    forged_count = 0
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract ZIP file
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find all folders
        for root, dirs, files in os.walk(temp_dir):
            # Skip the root temp directory itself
            if root == temp_dir:
                continue
            
            # Get folder name
            folder_name = os.path.basename(root)
            
            # Skip hidden folders and __MACOSX
            if folder_name.startswith('.') or folder_name == '__MACOSX':
                continue
            
            # Determine if genuine or forged
            is_genuine = not folder_name.endswith('_forg')
            label = 1 if is_genuine else 0
            
            # Process images in this folder
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.PNG', '.JPG', '.JPEG', '.BMP')
            
            for filename in files:
                if filename.endswith(image_extensions) and not filename.startswith('.'):
                    img_path = os.path.join(root, filename)
                    
                    try:
                        image = Image.open(img_path)
                        dataset.append({
                            'folder': folder_name,
                            'filename': filename,
                            'image': image.copy(),  # Make a copy
                            'label': label,
                            'label_text': 'Genuine' if is_genuine else 'Forged'
                        })
                        
                        if is_genuine:
                            genuine_count += 1
                        else:
                            forged_count += 1
                    except Exception as e:
                        st.warning(f"Could not load {filename}: {str(e)}")
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
        if len(dataset) == 0:
            return dataset, "No valid images found in ZIP file"
        
        return dataset, f"Loaded {len(dataset)} images ({genuine_count} genuine, {forged_count} forged)"
        
    except Exception as e:
        shutil.rmtree(temp_dir)
        return [], f"Error processing ZIP file: {str(e)}"

def save_training_data(dataset):
    """Save loaded dataset to database"""
    conn = sqlite3.connect('signature_system.db')
    cursor = conn.cursor()
    
    # Clear existing training data
    cursor.execute('DELETE FROM training_data')
    
    saved_count = 0
    for data in dataset:
        try:
            img_byte_arr = io.BytesIO()
            data['image'].save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            cursor.execute('''
            INSERT INTO training_data (folder_name, signature_image, is_genuine)
            VALUES (?, ?, ?)
            ''', (data['folder'], img_bytes, data['label']))
            
            saved_count += 1
        except Exception as e:
            st.error(f"Error saving {data['folder']}/{data['filename']}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    return saved_count

def get_training_statistics():
    """Get statistics about training data"""
    conn = sqlite3.connect('signature_system.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM training_data WHERE is_genuine = 1')
    genuine_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM training_data WHERE is_genuine = 0')
    forged_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT folder_name) FROM training_data')
    folder_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'genuine': genuine_count,
        'forged': forged_count,
        'total': genuine_count + forged_count,
        'folders': folder_count
    }

def save_signature_template(user_id, image):
    """Save signature template"""
    conn = sqlite3.connect('signature_system.db')
    cursor = conn.cursor()
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    features = extract_features(image)
    feature_bytes = features.tobytes()
    
    cursor.execute('''
    INSERT INTO signature_templates (user_id, signature_image, feature_vector)
    VALUES (?, ?, ?)
    ''', (user_id, img_bytes, feature_bytes))
    
    conn.commit()
    conn.close()

def get_user_templates(user_id):
    """Get all templates for user"""
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
    """Verify signature"""
    templates = get_user_templates(user_id)
    
    if not templates:
        return "No Template", 0.0
    
    test_features = extract_features(test_image)
    
    similarities = []
    for template in templates:
        template_features = np.frombuffer(template[2], dtype=np.float64)
        similarity = compare_signatures(template_features, test_features)
        similarities.append(similarity)
    
    avg_similarity = np.mean(similarities)
    
    threshold = 70.0
    result = "Genuine" if avg_similarity >= threshold else "Forged"
    
    return result, avg_similarity

def log_verification(user_id, test_image, result, confidence):
    """Log verification"""
    conn = sqlite3.connect('signature_system.db')
    cursor = conn.cursor()
    
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
    """Get verification history"""
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

# Session state
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

# Login Page
if not st.session_state.logged_in:
    st.title("✍️ Signature Verification System")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        
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
                st.error("Password must be at least 6 characters")
            else:
                success, message = register_user(reg_username, reg_password, reg_full_name, reg_email)
                if success:
                    st.success("Registration successful! Please login.")
                else:
                    st.error(message)

# Main Application
else:
    with st.sidebar:
        st.title("Navigation")
        st.write(f"**Welcome, {st.session_state.full_name}!**")
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
            if st.button("📥 Load Dataset", use_container_width=True):
                st.session_state.page = 'dataset'
                st.rerun()
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    
    if st.session_state.page == 'dashboard':
        st.title("📊 Dashboard")
        
        templates = get_user_templates(st.session_state.user_id)
        history = get_verification_history(st.session_state.user_id, 100)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Templates", len(templates))
        col2.metric("Verifications", len(history))
        col3.metric("Genuine", sum(1 for h in history if h[1] == 'Genuine'))
        
        if st.session_state.user_type == 'admin':
            st.divider()
            st.subheader("Training Dataset")
            stats = get_training_statistics()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Images", stats['total'])
            col2.metric("Genuine", stats['genuine'])
            col3.metric("Forged", stats['forged'])
            col4.metric("Folders", stats['folders'])
        
        st.divider()
        st.subheader("Recent Activity")
        
        recent = get_verification_history(st.session_state.user_id, 5)
        if recent:
            for log in recent:
                col1, col2, col3 = st.columns([2, 2, 3])
                with col1:
                    if log[1] == 'Genuine':
                        st.success(f"✓ {log[1]}")
                    else:
                        st.error(f"✗ {log[1]}")
                with col2:
                    st.write(f"**{log[2]:.1f}%**")
                with col3:
                    st.write(f"*{log[3]}*")
        else:
            st.info("No recent activity")
    
    elif st.session_state.page == 'verify':
        st.title("✅ Verify Signature")
        
        templates = get_user_templates(st.session_state.user_id)
        
        if not templates:
            st.warning("⚠️ Add templates first!")
            if st.button("Go to Templates"):
                st.session_state.page = 'templates'
                st.rerun()
        else:
            st.info(f"You have {len(templates)} template(s)")
            
            uploaded_file = st.file_uploader("Upload Signature to Verify", type=['png', 'jpg', 'jpeg'])
            
            if uploaded_file:
                image = Image.open(uploaded_file)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Original")
                    st.image(image, use_container_width=True)
                
                with col2:
                    st.subheader("Processed")
                    processed = simple_preprocess(image)
                    st.image(processed, use_container_width=True, clamp=True)
                
                if st.button("🔍 Verify Signature", use_container_width=True):
                    with st.spinner("Verifying..."):
                        result, confidence = verify_signature(st.session_state.user_id, image)
                        log_verification(st.session_state.user_id, image, result, confidence)
                        
                        st.divider()
                        if result == "Genuine":
                            st.success(f"✅ **GENUINE SIGNATURE**")
                            st.success(f"Confidence: **{confidence:.1f}%**")
                        else:
                            st.error(f"❌ **FORGED SIGNATURE**")
                            st.error(f"Confidence: **{confidence:.1f}%**")
                        
                        st.progress(confidence / 100)
    
    elif st.session_state.page == 'templates':
        st.title("📂 Signature Templates")
        
        st.subheader("Add New Template")
        uploaded = st.file_uploader("Upload Signature Template", type=['png', 'jpg', 'jpeg'])
        
        if uploaded:
            image = Image.open(uploaded)
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(image, caption="Original", use_container_width=True)
            
            with col2:
                processed = simple_preprocess(image)
                st.image(processed, caption="Processed", use_container_width=True, clamp=True)
            
            if st.button("💾 Save Template", use_container_width=True):
                save_signature_template(st.session_state.user_id, image)
                st.success("Template saved!")
                st.rerun()
        
        st.divider()
        templates = get_user_templates(st.session_state.user_id)
        st.subheader(f"Your Templates ({len(templates)})")
        
        if templates:
            cols = st.columns(3)
            for idx, template in enumerate(templates):
                with cols[idx % 3]:
                    img = Image.open(io.BytesIO(template[1]))
                    st.image(img, use_container_width=True)
                    st.caption(f"Added: {template[3][:10]}")
        else:
            st.info("No templates yet")
    
    elif st.session_state.page == 'history':
        st.title("📊 History")
        
        history = get_verification_history(st.session_state.user_id, 50)
        
        if history:
            for log in history:
                col1, col2, col3, col4 = st.columns([1, 2, 2, 3])
                with col1:
                    st.write(f"#{log[0]}")
                with col2:
                    if log[1] == 'Genuine':
                        st.success(log[1])
                    else:
                        st.error(log[1])
                with col3:
                    st.write(f"**{log[2]:.1f}%**")
                with col4:
                    st.write(log[3])
            
            st.divider()
            genuine = sum(1 for h in history if h[1] == 'Genuine')
            forged = sum(1 for h in history if h[1] == 'Forged')
            avg_conf = np.mean([h[2] for h in history])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Genuine", genuine)
            col2.metric("Forged", forged)
            col3.metric("Avg Confidence", f"{avg_conf:.1f}%")
        else:
            st.info("No history yet")
    
    elif st.session_state.page == 'dataset' and st.session_state.user_type == 'admin':
        st.title("📥 Load Training Dataset (ZIP Upload)")
        
        st.markdown("""
        ### How to Prepare Your Dataset ZIP File:
        
        1. **Create folders with this structure:**
           - `001/` - Genuine signatures (person 1)
           - `001_forg/` - Forged signatures (person 1)
           - `002/` - Genuine signatures (person 2)
           - `002_forg/` - Forged signatures (person 2)
           - Continue this pattern...
        
        2. **ZIP the parent folder** containing all these subfolders
        
        3. **Upload the ZIP file** below
        
        **Rules:**
        - Folders WITHOUT `_forg` = Genuine signatures ✅
        - Folders WITH `_forg` = Forged signatures ❌
        - Supported: PNG, JPG, JPEG, BMP
        """)
        
        st.divider()
        
        zip_file = st.file_uploader(
            "Upload Dataset ZIP File",
            type=['zip'],
            help="Upload a ZIP file containing your signature dataset folders"
        )
        
        if zip_file is not None:
            if st.button("📂 Load Dataset from ZIP", use_container_width=True):
                with st.spinner("Processing ZIP file..."):
                    dataset, message = load_dataset_from_zip(zip_file)
                    
                    if dataset:
                        st.success(message)
                        
                        # Show samples
                        st.subheader("Sample Images")
                        
                        genuine_samples = [d for d in dataset if d['label'] == 1][:3]
                        forged_samples = [d for d in dataset if d['label'] == 0][:3]
                        
                        if genuine_samples:
                            st.write("**Genuine:**")
                            cols = st.columns(len(genuine_samples))
                            for idx, sample in enumerate(genuine_samples):
                                with cols[idx]:
                                    st.image(sample['image'], caption=sample['folder'], use_container_width=True)
                        
                        if forged_samples:
                            st.write("**Forged:**")
                            cols = st.columns(len(forged_samples))
                            for idx, sample in enumerate(forged_samples):
                                with cols[idx]:
                                    st.image(sample['image'], caption=sample['folder'], use_container_width=True)
                        
                        if st.button("💾 Save to Database", use_container_width=True):
                            with st.spinner("Saving..."):
                                saved = save_training_data(dataset)
                                st.success(f"Saved {saved} images!")
                                st.balloons()
                                st.rerun()
                    else:
                        st.error(message)
        
        st.divider()
        st.subheader("Current Dataset")
        stats = get_training_statistics()
        
        if stats['total'] > 0:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", stats['total'])
            col2.metric("Genuine", stats['genuine'])
            col3.metric("Forged", stats['forged'])
            col4.metric("Folders", stats['folders'])
            
            genuine_pct = (stats['genuine'] / stats['total']) * 100
            forged_pct = (stats['forged'] / stats['total']) * 100
            
            st.write(f"**Distribution:** {genuine_pct:.1f}% Genuine, {forged_pct:.1f}% Forged")
            st.write("Genuine:")
            st.progress(genuine_pct / 100)
            st.write("Forged:")
            st.progress(forged_pct / 100)
        else:
            st.info("No training data loaded yet")
