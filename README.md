# Fake Signature Detection System using Neural Network

A complete signature verification system built with Python and Streamlit that uses image processing and feature extraction to detect forged signatures.

## Features

- **User Authentication**: Secure login and registration system
- **Signature Template Management**: Upload and manage signature templates
- **Signature Verification**: Real-time signature verification with confidence scores
- **Verification History**: Track all verification activities
- **Admin Dashboard**: User management for administrators
- **Simple Neural Network**: Feature extraction and comparison algorithm

## System Requirements

### Hardware Requirements
- Processor: Intel Core i3 or equivalent (2.0 GHz minimum)
- RAM: 4 GB minimum (8 GB recommended)
- Storage: 2 GB free space
- Display: 1024 x 768 minimum resolution

### Software Requirements
- Operating System: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Edge, Safari)

## Installation

### Step 1: Install Python
Download and install Python 3.8 or higher from [python.org](https://www.python.org/downloads/)

During installation, make sure to check "Add Python to PATH"

### Step 2: Download the System
Download all system files and extract to a folder on your computer

### Step 3: Install Required Libraries
Open Command Prompt (Windows) or Terminal (Mac/Linux) and navigate to the system folder:

```bash
cd path/to/signature-system
```

Install all required libraries:

```bash
pip install -r requirements.txt
```

### Step 4: Run the System
Start the application with:

```bash
streamlit run app.py
```

The system will automatically open in your default web browser at `http://localhost:8501`

## Default Login Credentials

**Administrator Account:**
- Username: `admin`
- Password: `admin123`

⚠️ **Important**: Change the default admin password after first login!

## How to Use

### For New Users

1. **Register an Account**
   - Click on the "Register" tab
   - Fill in your full name, email, username, and password
   - Click "Register" to create your account

2. **Login**
   - Enter your username and password
   - Click "Login"

3. **Add Signature Templates**
   - Go to "My Templates" from the sidebar
   - Upload at least 3 samples of your genuine signature
   - Click "Save Template" for each signature

4. **Verify Signatures**
   - Go to "Verify Signature" from the sidebar
   - Upload the signature image you want to verify
   - Click "Verify Signature"
   - View the result (Genuine/Forged) with confidence score

5. **View History**
   - Go to "History" to see all past verifications
   - View statistics and detailed results

### For Administrators

1. **Login with Admin Credentials**
   - Use the default admin username and password

2. **Manage Users**
   - Click "Manage Users" in the sidebar
   - View all registered users
   - See user statistics and activity

## File Structure

```
signature-system/
│
├── app.py                      # Main application file
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── signature_system.db         # Database (created automatically)
```

## How It Works

### 1. Image Pre-processing
- Converts image to grayscale
- Applies threshold to remove background
- Removes noise using morphological operations
- Resizes to standard 128x128 pixels
- Normalizes pixel values (0-1 range)

### 2. Feature Extraction
The system extracts the following features from each signature:
- **Pixel Density**: Average intensity of signature pixels
- **Aspect Ratio**: Height to width ratio of signature
- **Horizontal Projection**: Standard deviation of pixel distribution horizontally
- **Vertical Projection**: Standard deviation of pixel distribution vertically
- **Transitions**: Number of black-to-white transitions

### 3. Signature Comparison
- Compares test signature features with stored template features
- Calculates Euclidean distance between feature vectors
- Converts distance to similarity score (0-100%)
- Threshold: 70% similarity required for "Genuine" classification

### 4. Verification Decision
- **Genuine**: Similarity ≥ 70%
- **Forged**: Similarity < 70%
- Confidence score displayed as percentage

## Database Structure

The system uses SQLite database with the following tables:

### users
- user_id (PRIMARY KEY)
- username (UNIQUE)
- password_hash
- full_name
- email (UNIQUE)
- user_type (user/admin)
- created_at
- is_active

### signature_templates
- template_id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- signature_image (BLOB)
- feature_vector (BLOB)
- created_at
- is_active

### verification_logs
- log_id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- test_signature (BLOB)
- result (Genuine/Forged)
- confidence_score (0-100)
- verification_time

### system_settings
- setting_id (PRIMARY KEY)
- setting_name
- setting_value
- updated_at

## Troubleshooting

### Problem: Libraries won't install
**Solution**: Try upgrading pip first:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Problem: Port 8501 is already in use
**Solution**: Use a different port:
```bash
streamlit run app.py --server.port 8502
```

### Problem: Database errors
**Solution**: Delete `signature_system.db` file and restart the application. It will create a new database automatically.

### Problem: Images not uploading
**Solution**: Make sure image files are in PNG, JPG, or JPEG format and are not corrupted.

## Security Features

- Passwords are hashed using SHA-256
- Session-based authentication
- User input validation
- SQL injection prevention through parameterized queries
- Secure file handling for image uploads

## Limitations

- This is a simplified version using basic feature extraction
- For production use, implement a full CNN model with TensorFlow/Keras
- Current accuracy depends on quality of signature templates
- Works best with clear, high-contrast signature images

## Future Enhancements

1. **Full CNN Implementation**: Replace simple feature extraction with trained neural network
2. **Mobile App**: Develop mobile version for Android/iOS
3. **Multi-modal Authentication**: Add fingerprint or facial recognition
4. **Online Signatures**: Support dynamic signature capture with stylus
5. **API Integration**: RESTful API for third-party integration
6. **Reporting**: Generate PDF reports of verification results
7. **Batch Processing**: Verify multiple signatures at once

## Support

For technical support or questions:
- Email: support@nathanict.com.ng
- Phone: +234 814 775 4855
- Website: https://nathanict.com.ng

## License

This system is developed for educational and research purposes.

## Credits

**Developed by:** Nathan ICT Solutions
**Technology Stack:** Python, Streamlit, OpenCV, SQLite
**Version:** 1.0.0
**Last Updated:** 2025

---

© 2025 Nathan ICT Solutions. All rights reserved.
