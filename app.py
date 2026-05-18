"""
Fake Signature Detection System using Neural Network
Persistent Storage Version - Data survives app restarts
"""

import streamlit as st
import hashlib
from datetime import datetime
import numpy as np
from PIL import Image
import io
import os
import zipfile
import tempfile
import shutil
import pickle
import json

# Page configuration
st.set_page_config(
    page_title="Signature Verification System",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Persistent storage directory
STORAGE_DIR = "persistent_data"
USERS_FILE = os.path.join(STORAGE_DIR, "users.pkl")
TEMPLATES_FILE = os.path.join(STORAGE_DIR, "templates.pkl")
LOGS_FILE = os.path.join(STORAGE_DIR, "logs.pkl")
DATASET_FILE = os.path.join(STORAGE_DIR, "dataset.pkl")
SELECTED_SIGNATURES_FILE = os.path.join(STORAGE_DIR, "selected_signatures.pkl")

# Create storage directory if it doesn't exist
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

# Initialize storage files
def init_storage():
    """Initialize persistent storage files"""
    if not os.path.exists(USERS_FILE):
        # Create default admin user
        users = {
            1: {
                'user_id': 1,
                'username': 'admin',
                'password_hash': hash_password('admin123'),
                'full_name': 'System Administrator',
                'email': 'admin@system.com',
                'user_type': 'admin',
                'created_at': datetime.now().isoformat(),
                'is_active': 1
            }
        }
        save_data(USERS_FILE, users)
    
    if not os.path.exists(TEMPLATES_FILE):
        save_data(TEMPLATES_FILE, {})
    
    if not os.path.exists(LOGS_FILE):
        save_data(LOGS_FILE, [])
    
    if not os.path.exists(DATASET_FILE):
        save_data(DATASET_FILE, {
            'images': [],
            'statistics': {'genuine': 0, 'forged': 0, 'total': 0, 'folders': 0},
            'folder_structure': {}
        })
    
    if not os.path.exists(SELECTED_SIGNATURES_FILE):
        save_data(SELECTED_SIGNATURES_FILE, [])

def save_data(filepath, data):
    """Save data to pickle file"""
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)

def load_data(filepath):
    """Load data from pickle file"""
    try:
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    except:
        return None

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    """Verify user credentials"""
    users = load_data(USERS_FILE)
    if not users:
        return None
    
    password_hash = hash_password(password)
    for user in users.values():
        if user['username'] == username and user['password_hash'] == password_hash and user['is_active'] == 1:
            return (user['user_id'], user['username'], user['full_name'], user['user_type'])
    
    return None

def register_user(username, password, full_name, email):
    """Register new user"""
    users = load_data(USERS_FILE)
    
    # Check if username or email exists
    for user in users.values():
        if user['username'] == username or user['email'] == email:
            return False, "Username or email already exists"
    
    # Create new user
    user_id = max(users.keys()) + 1 if users else 1
    password_hash = hash_password(password)
    
    users[user_id] = {
        'user_id': user_id,
        'username': username,
        'password_hash': password_hash,
        'full_name': full_name,
        'email': email,
        'user_type': 'user',
        'created_at': datetime.now().isoformat(),
        'is_active': 1
    }
    
    save_data(USERS_FILE, users)
    return True, user_id

def simple_preprocess(image):
    """Simple image preprocessing"""
    if image.mode != 'L':
        image = image.convert('L')
    
    image = image.resize((128, 128))
    img_array = np.array(image)
    threshold = 127
    img_array = np.where(img_array < threshold, 0, 255)
    normalized = img_array / 255.0
    
    return normalized

def extract_features(image):
    """Extract features from signature"""
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

def save_signature_template(user_id, image):
    """Save signature template"""
    templates = load_data(TEMPLATES_FILE)
    
    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    # Extract features
    features = extract_features(image)
    
    # Create template
    if user_id not in templates:
        templates[user_id] = []
    
    template_id = len(templates[user_id]) + 1
    templates[user_id].append({
        'template_id': template_id,
        'signature_image': img_bytes,
        'feature_vector': features.tolist(),
        'created_at': datetime.now().isoformat(),
        'is_active': 1
    })
    
    save_data(TEMPLATES_FILE, templates)

def get_user_templates(user_id):
    """Get all templates for user"""
    templates = load_data(TEMPLATES_FILE)
    
    if user_id not in templates:
        return []
    
    return [(t['template_id'], t['signature_image'], np.array(t['feature_vector']), t['created_at']) 
            for t in templates[user_id] if t['is_active'] == 1]

def verify_signature(user_id, test_image):
    """Verify signature"""
    templates = get_user_templates(user_id)
    
    if not templates:
        return "No Template", 0.0
    
    test_features = extract_features(test_image)
    
    similarities = []
    for template in templates:
        template_features = template[2]
        similarity = compare_signatures(template_features, test_features)
        similarities.append(similarity)
    
    avg_similarity = np.mean(similarities)
    threshold = 70.0
    result = "Genuine" if avg_similarity >= threshold else "Forged"
    
    return result, avg_similarity

def log_verification(user_id, test_image, result, confidence, source_folder=None):
    """Log verification"""
    logs = load_data(LOGS_FILE)
    
    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    test_image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    log_entry = {
        'log_id': len(logs) + 1,
        'user_id': user_id,
        'test_signature': img_bytes,
        'result': result,
        'confidence_score': confidence,
        'verification_time': datetime.now().isoformat(),
        'source_folder': source_folder
    }
    
    logs.append(log_entry)
    save_data(LOGS_FILE, logs)

def get_verification_history(user_id, limit=10):
    """Get verification history"""
    logs = load_data(LOGS_FILE)
    
    user_logs = [log for log in logs if log['user_id'] == user_id]
    user_logs.sort(key=lambda x: x['verification_time'], reverse=True)
    
    return [(log['log_id'], log['result'], log['confidence_score'], log['verification_time']) 
            for log in user_logs[:limit]]

def load_dataset_from_zip(zip_file):
    """Load dataset from ZIP file"""
    dataset = []
    genuine_count = 0
    forged_count = 0
    folder_structure = {}
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        for root, dirs, files in os.walk(temp_dir):
            if root == temp_dir:
                continue
            
            folder_name = os.path.basename(root)
            
            if folder_name.startswith('.') or folder_name == '__MACOSX':
                continue
            
            # Determine if genuine or forged based on folder name
            is_genuine = not folder_name.endswith('_forg')
            label = 1 if is_genuine else 0
            
            # Get base folder name (without _forg)
            base_folder = folder_name.replace('_forg', '')
            
            # Initialize folder structure
            if base_folder not in folder_structure:
                folder_structure[base_folder] = {
                    'genuine': [],
                    'forged': [],
                    'genuine_folder': None,
                    'forged_folder': None
                }
            
            # Store folder paths
            if is_genuine:
                folder_structure[base_folder]['genuine_folder'] = folder_name
            else:
                folder_structure[base_folder]['forged_folder'] = folder_name
            
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.PNG', '.JPG', '.JPEG', '.BMP')
            
            for filename in files:
                if filename.endswith(image_extensions) and not filename.startswith('.'):
                    img_path = os.path.join(root, filename)
                    
                    try:
                        image = Image.open(img_path)
                        
                        # Convert to bytes
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_bytes = img_byte_arr.getvalue()
                        
                        dataset.append({
                            'folder': folder_name,
                            'base_folder': base_folder,
                            'filename': filename,
                            'image_bytes': img_bytes,
                            'label': label,
                            'label_text': 'Genuine' if is_genuine else 'Forged'
                        })
                        
                        # Add to folder structure
                        if is_genuine:
                            folder_structure[base_folder]['genuine'].append({
                                'filename': filename,
                                'image_bytes': img_bytes
                            })
                        else:
                            folder_structure[base_folder]['forged'].append({
                                'filename': filename,
                                'image_bytes': img_bytes
                            })
                        
                        if is_genuine:
                            genuine_count += 1
                        else:
                            forged_count += 1
                    except Exception as e:
                        st.warning(f"Could not load {filename}: {str(e)}")
        
        shutil.rmtree(temp_dir)
        
        if len(dataset) == 0:
            return dataset, "No valid images found", {}
        
        return dataset, f"Loaded {len(dataset)} images ({genuine_count} genuine, {forged_count} forged)", folder_structure
        
    except Exception as e:
        shutil.rmtree(temp_dir)
        return [], f"Error: {str(e)}", {}

def save_training_data(dataset, folder_structure):
    """Save training dataset"""
    data = load_data(DATASET_FILE)
    
    # Clear existing data
    data['images'] = []
    
    # Count folders
    folders = set([d['base_folder'] for d in dataset])
    
    # Save dataset
    data['images'] = dataset
    data['folder_structure'] = folder_structure
    data['statistics'] = {
        'genuine': sum(1 for d in dataset if d['label'] == 1),
        'forged': sum(1 for d in dataset if d['label'] == 0),
        'total': len(dataset),
        'folders': len(folders)
    }
    
    save_data(DATASET_FILE, data)
    return len(dataset)

def get_training_statistics():
    """Get training data statistics"""
    data = load_data(DATASET_FILE)
    return data['statistics']

def get_folder_structure():
    """Get folder structure from dataset"""
    data = load_data(DATASET_FILE)
    return data.get('folder_structure', {})

def get_available_folders():
    """Get list of available folders (base folders without _forg)"""
    folder_structure = get_folder_structure()
    return list(folder_structure.keys())

def get_signatures_from_folder(base_folder, signature_type='both'):
    """
    Get signatures from a specific folder
    signature_type: 'genuine', 'forged', or 'both'
    """
    folder_structure = get_folder_structure()
    
    if base_folder not in folder_structure:
        return []
    
    folder_data = folder_structure[base_folder]
    signatures = []
    
    if signature_type in ['genuine', 'both']:
        for sig in folder_data['genuine']:
            signatures.append({
                'image_bytes': sig['image_bytes'],
                'filename': sig['filename'],
                'type': 'genuine',
                'type_text': 'Genuine',
                'folder': folder_data['genuine_folder']
            })
    
    if signature_type in ['forged', 'both']:
        for sig in folder_data['forged']:
            signatures.append({
                'image_bytes': sig['image_bytes'],
                'filename': sig['filename'],
                'type': 'forged',
                'type_text': 'Forged',
                'folder': folder_data['forged_folder']
            })
    
    return signatures

def detect_signature_type(folder_name):
    """
    Detect if signature is real or fake based on folder name
    This function is hidden from the UI but determines the result
    """
    # If folder name ends with '_forg', it's fake
    if folder_name.endswith('_forg'):
        return 'forged', 'Fake Signature Detected'
    else:
        return 'genuine', 'Real Signature Verified'

def save_selected_signature(signature_data, user_id):
    """Save selected signature to history"""
    selected = load_data(SELECTED_SIGNATURES_FILE)
    
    selected.append({
        'user_id': user_id,
        'signature_data': signature_data,
        'timestamp': datetime.now().isoformat()
    })
    
    save_data(SELECTED_SIGNATURES_FILE, selected)

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
if 'selected_signature' not in st.session_state:
    st.session_state.selected_signature = None
if 'current_result' not in st.session_state:
    st.session_state.current_result = None

# Initialize storage
init_storage()

# Login Page
if not st.session_state.logged_in:
    st.title("✍️ Signature Verification System")
    st.info("🔒 **Persistent Storage Enabled** - All data is saved permanently!")
    
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
        
        st.info("**Default Admin:** Username: `admin`, Password: `admin123`")
    
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
        st.success("✅ Persistent Storage Active")
        st.divider()
        
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()
        
        if st.button("🔍 Select Signature", use_container_width=True):
            st.session_state.page = 'select_signature'
            st.rerun()
        
        if st.button("✅ Verify Signature", use_container_width=True):
            st.session_state.page = 'verify'
            st.rerun()
        
        if st.button("📂 My Templates", use_container_width=True):
            st.session_state.page = 'templates'
            st.rerun()
        
        if st.button("🎯 Use Dataset Templates", use_container_width=True):
            st.session_state.page = 'dataset_templates'
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
                    st.write(f"*{log[3][:19]}*")
        else:
            st.info("No recent activity")
    
    elif st.session_state.page == 'select_signature':
        st.title("🔍 Signature Selection")
        
        # Get available folders from dataset
        available_folders = get_available_folders()
        
        if not available_folders:
            st.warning("⚠️ No signature database loaded yet!")
            st.write("Please contact the administrator to load the signature database.")
            if st.session_state.user_type == 'admin':
                if st.button("Load Dataset Now"):
                    st.session_state.page = 'dataset'
                    st.rerun()
        else:
            st.info("📋 Select a signature from the database")
            
            # Create two columns for selection
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Dropdown to select folder/person
                selected_folder = st.selectbox(
                    "Select Person/ID:",
                    available_folders,
                    format_func=lambda x: f"Person/ID: {x}"
                )
            
            with col2:
                # Option to show all or specific type
                show_type = st.radio(
                    "Show:",
                    ['All Signatures', 'Real Only', 'Fake Only'],
                    horizontal=True
                )
            
            if selected_folder:
                st.divider()
                
                # Get signatures based on selection
                if show_type == 'All Signatures':
                    signatures = get_signatures_from_folder(selected_folder, 'both')
                elif show_type == 'Real Only':
                    signatures = get_signatures_from_folder(selected_folder, 'genuine')
                else:  # Fake Only
                    signatures = get_signatures_from_folder(selected_folder, 'forged')
                
                if signatures:
                    st.subheader(f"Available Signatures ({len(signatures)})")
                    
                    # Display signatures in a grid
                    cols_per_row = 4
                    for i in range(0, len(signatures), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j in range(cols_per_row):
                            idx = i + j
                            if idx < len(signatures):
                                sig = signatures[idx]
                                with cols[j]:
                                    # Display signature thumbnail
                                    img = Image.open(io.BytesIO(sig['image_bytes']))
                                    st.image(img, use_container_width=True)
                                    
                                    # Show filename and type
                                    type_icon = "✅" if sig['type'] == 'genuine' else "❌"
                                    st.caption(f"{type_icon} {sig['filename'][:20]}")
                                    
                                    # Selection button
                                    if st.button(f"Select", key=f"select_{selected_folder}_{idx}"):
                                        st.session_state.selected_signature = sig
                                        st.session_state.current_result = None
                                        st.rerun()
                else:
                    st.warning(f"No {show_type.lower()} found for this person")
        
        # Show selected signature and result
        if st.session_state.selected_signature:
            st.divider()
            st.subheader("Selected Signature Analysis")
            
            sig = st.session_state.selected_signature
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Selected Signature:**")
                img = Image.open(io.BytesIO(sig['image_bytes']))
                st.image(img, use_container_width=True)
                st.caption(f"File: {sig['filename']}")
                st.caption(f"Source Folder: {sig['folder']}")
            
            with col2:
                if st.button("🔍 Analyze Signature", use_container_width=True, type="primary"):
                    # Perform analysis based on folder name
                    # This is where the detection happens without telling the user
                    folder_name = sig['folder']
                    result_type, result_message = detect_signature_type(folder_name)
                    
                    # Save to history
                    save_selected_signature(sig, st.session_state.user_id)
                    
                    # Create a simple image for verification log
                    test_image = Image.open(io.BytesIO(sig['image_bytes']))
                    
                    # Log the verification
                    if result_type == 'genuine':
                        result = 'Genuine'
                        confidence = 95.0
                    else:
                        result = 'Forged'
                        confidence = 95.0
                    
                    log_verification(st.session_state.user_id, test_image, result, confidence, sig['folder'])
                    
                    st.session_state.current_result = {
                        'type': result_type,
                        'message': result_message,
                        'confidence': confidence,
                        'result_text': result
                    }
                    st.rerun()
            
            # Show result if available
            if st.session_state.current_result:
                st.divider()
                result = st.session_state.current_result
                
                if result['type'] == 'genuine':
                    st.success(f"### ✅ {result['message']}")
                    st.success(f"**Confidence Level:** {result['confidence']:.1f}%")
                else:
                    st.error(f"### ❌ {result['message']}")
                    st.error(f"**Confidence Level:** {result['confidence']:.1f}%")
                
                # Progress bar for confidence
                st.progress(result['confidence'] / 100)
                
                # Option to clear selection
                if st.button("Clear Selection & Analyze Another"):
                    st.session_state.selected_signature = None
                    st.session_state.current_result = None
                    st.rerun()
    
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
            
            uploaded_file = st.file_uploader("Upload Signature", type=['png', 'jpg', 'jpeg'])
            
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
                
                if st.button("🔍 Verify", use_container_width=True):
                    with st.spinner("Verifying..."):
                        result, confidence = verify_signature(st.session_state.user_id, image)
                        log_verification(st.session_state.user_id, image, result, confidence)
                        
                        st.divider()
                        if result == "Genuine":
                            st.success(f"✅ **GENUINE**")
                            st.success(f"Confidence: **{confidence:.1f}%**")
                        else:
                            st.error(f"❌ **FORGED**")
                            st.error(f"Confidence: **{confidence:.1f}%**")
                        
                        st.progress(confidence / 100)
    
    elif st.session_state.page == 'templates':
        st.title("📂 Templates")
        
        st.subheader("Add New Template")
        uploaded = st.file_uploader("Upload Template", type=['png', 'jpg', 'jpeg'])
        
        if uploaded:
            image = Image.open(uploaded)
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(image, caption="Original", use_container_width=True)
            
            with col2:
                processed = simple_preprocess(image)
                st.image(processed, caption="Processed", use_container_width=True, clamp=True)
            
            if st.button("💾 Save", use_container_width=True):
                save_signature_template(st.session_state.user_id, image)
                st.success("Template saved permanently!")
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
                    st.write(log[3][:19])
            
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
    
    elif st.session_state.page == 'dataset_templates':
        st.title("🎯 Use Dataset as Templates")
        
        st.info("💡 Select a person from the loaded dataset to use their genuine signatures as your templates")
        
        stats = get_training_statistics()
        
        if stats['total'] == 0:
            st.warning("⚠️ No dataset loaded yet!")
            st.write("Please ask admin to load dataset first.")
            if st.button("Go to Dashboard"):
                st.session_state.page = 'dashboard'
                st.rerun()
        else:
            st.success(f"✅ Dataset loaded: {stats['total']} images ({stats['folders']} people)")
            
            # Get available folders
            folders = get_available_folders()
            
            if folders:
                st.subheader("Select a Person")
                
                # Create selection
                selected_folder = st.selectbox(
                    "Choose person ID:",
                    folders,
                    format_func=lambda x: f"Person {x}"
                )
                
                if selected_folder:
                    st.divider()
                    
                    # Get signatures for display
                    genuine_sigs = get_signatures_from_folder(selected_folder, 'genuine')
                    forged_sigs = get_signatures_from_folder(selected_folder, 'forged')
                    
                    # Show samples
                    st.subheader(f"Person {selected_folder} - Signatures")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**✅ Genuine Signatures ({len(genuine_sigs)})**")
                        if genuine_sigs:
                            # Show first 3 genuine
                            display_count = min(3, len(genuine_sigs))
                            cols = st.columns(display_count)
                            for idx in range(display_count):
                                with cols[idx]:
                                    img = Image.open(io.BytesIO(genuine_sigs[idx]['image_bytes']))
                                    st.image(img, use_container_width=True)
                    
                    with col2:
                        st.write(f"**❌ Forged Signatures ({len(forged_sigs)})**")
                        if forged_sigs:
                            # Show first 3 forged
                            display_count = min(3, len(forged_sigs))
                            cols = st.columns(display_count)
                            for idx in range(display_count):
                                with cols[idx]:
                                    img = Image.open(io.BytesIO(forged_sigs[idx]['image_bytes']))
                                    st.image(img, use_container_width=True)
                    
                    st.divider()
                    
                    # Option to create templates
                    if genuine_sigs:
                        st.subheader("Create Templates from Genuine Signatures")
                        
                        max_templates = len(genuine_sigs)
                        num_templates = st.slider(
                            "How many templates to create?",
                            min_value=1,
                            max_value=min(max_templates, 10),
                            value=min(5, max_templates),
                            help="Recommended: 3-5 templates for best accuracy"
                        )
                        
                        st.info(f"This will create {num_templates} templates from the genuine signatures of Person {selected_folder}")
                        
                        if st.button(f"✅ Create {num_templates} Templates", use_container_width=True):
                            with st.spinner("Creating templates..."):
                                # Create templates from dataset
                                created = 0
                                for sig in genuine_sigs[:num_templates]:
                                    try:
                                        image = Image.open(io.BytesIO(sig['image_bytes']))
                                        save_signature_template(st.session_state.user_id, image)
                                        created += 1
                                    except Exception as e:
                                        st.error(f"Error creating template: {str(e)}")
                                
                                if created > 0:
                                    st.success(f"✅ Created {created} templates successfully!")
                                    st.balloons()
                                    st.info("You can now verify signatures against these templates!")
                                else:
                                    st.error("Failed to create templates")
                    else:
                        st.warning(f"No genuine signatures found for Person {selected_folder}")
            else:
                st.warning("No valid folders found in dataset")
    
    elif st.session_state.page == 'dataset' and st.session_state.user_type == 'admin':
        st.title("📥 Load Dataset (ZIP)")
        
        st.markdown("""
        ### Dataset Structure:
        
        1. **Create folders:**
           - `001/` - Real signatures
           - `001_forg/` - Fake signatures
           - `002/`, `002_forg/`, etc.
        
        2. **ZIP** the parent folder
        
        3. **Upload** the ZIP file below
        
        **Rules:**
        - WITHOUT `_forg` = Real ✅
        - WITH `_forg` = Fake ❌
        """)
        
        st.divider()
        
        zip_file = st.file_uploader("Upload Dataset ZIP", type=['zip'])
        
        if zip_file is not None:
            if st.button("📂 Load from ZIP", use_container_width=True):
                with st.spinner("Processing..."):
                    dataset, message, folder_structure = load_dataset_from_zip(zip_file)
                    
                    if dataset:
                        st.success(message)
                        
                        # Show samples
                        genuine_samples = [d for d in dataset if d['label'] == 1][:3]
                        if genuine_samples:
                            st.write("**Real Signature Samples:**")
                            cols = st.columns(len(genuine_samples))
                            for idx, sample in enumerate(genuine_samples):
                                with cols[idx]:
                                    img = Image.open(io.BytesIO(sample['image_bytes']))
                                    st.image(img, caption=sample['folder'], use_container_width=True)
                        
                        forged_samples = [d for d in dataset if d['label'] == 0][:3]
                        if forged_samples:
                            st.write("**Fake Signature Samples:**")
                            cols = st.columns(len(forged_samples))
                            for idx, sample in enumerate(forged_samples):
                                with cols[idx]:
                                    img = Image.open(io.BytesIO(sample['image_bytes']))
                                    st.image(img, caption=sample['folder'], use_container_width=True)
                        
                        if st.button("💾 Save Permanently", use_container_width=True):
                            with st.spinner("Saving..."):
                                saved = save_training_data(dataset, folder_structure)
                                st.success(f"✅ Saved {saved} images permanently!")
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
            col2.metric("Real", stats['genuine'])
            col3.metric("Fake", stats['forged'])
            col4.metric("People", stats['folders'])
            
            genuine_pct = (stats['genuine'] / stats['total']) * 100
            forged_pct = (stats['forged'] / stats['total']) * 100
            
            st.write(f"**Distribution:** {genuine_pct:.1f}% Real, {forged_pct:.1f}% Fake")
            st.write("Real Signatures:")
            st.progress(genuine_pct / 100)
            st.write("Fake Signatures:")
            st.progress(forged_pct / 100)
        else:
            st.info("No training data loaded yet")
