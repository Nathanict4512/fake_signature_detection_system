# SIGNATURE VERIFICATION SYSTEM
## USER MANUAL

---

## TABLE OF CONTENTS

1. Introduction
2. System Requirements
3. Installation Guide
4. Getting Started
5. User Functions
6. Administrator Functions
7. Troubleshooting
8. Frequently Asked Questions

---

## 1. INTRODUCTION

The Signature Verification System is an automated application that uses image processing and neural network technology to verify the authenticity of signatures. The system compares a test signature against stored templates to determine if it is genuine or forged.

### Key Features
- User registration and authentication
- Signature template management
- Real-time signature verification
- Verification history tracking
- Administrative controls
- Confidence scoring system

---

## 2. SYSTEM REQUIREMENTS

### Minimum Requirements
- **Processor**: Intel Core i3 (2.0 GHz) or equivalent
- **RAM**: 4 GB
- **Storage**: 2 GB free space
- **Display**: 1024 x 768 resolution
- **Operating System**: Windows 10, macOS 10.14, or Ubuntu 18.04
- **Python**: Version 3.8 or higher
- **Browser**: Chrome, Firefox, Edge, or Safari (latest version)

### Recommended Requirements
- **Processor**: Intel Core i5 (2.5 GHz) or higher
- **RAM**: 8 GB
- **Storage**: 5 GB free space
- **Display**: 1920 x 1080 resolution

---

## 3. INSTALLATION GUIDE

### Windows Users

1. **Install Python**
   - Download Python 3.8+ from python.org
   - Run installer and check "Add Python to PATH"
   - Verify installation by opening Command Prompt and typing: `python --version`

2. **Extract System Files**
   - Download the system ZIP file
   - Extract to a folder (e.g., C:\SignatureSystem)

3. **Run Installation Script**
   - Double-click `install.bat`
   - Wait for all libraries to install
   - Installation complete when you see "Installation completed successfully!"

4. **Start the System**
   - Double-click `run.bat`
   - Your browser will automatically open to http://localhost:8501

### Mac/Linux Users

1. **Install Python**
   - Python 3 is usually pre-installed
   - Verify by opening Terminal and typing: `python3 --version`
   - If not installed, download from python.org

2. **Extract System Files**
   - Download and extract the system files
   - Open Terminal and navigate to the folder: `cd /path/to/signature-system`

3. **Make Scripts Executable**
   ```bash
   chmod +x install.sh
   chmod +x run.sh
   ```

4. **Run Installation**
   ```bash
   ./install.sh
   ```

5. **Start the System**
   ```bash
   ./run.sh
   ```

---

## 4. GETTING STARTED

### First Time Login

1. Open your browser to http://localhost:8501
2. Use the default administrator credentials:
   - **Username**: admin
   - **Password**: admin123

3. **Important**: Change the admin password immediately after first login

### Creating a New User Account

1. Click the "Register" tab
2. Fill in the registration form:
   - Full Name
   - Email Address
   - Username (must be unique)
   - Password (minimum 6 characters)
   - Confirm Password

3. Click "Register"
4. Return to "Login" tab and login with your new credentials

---

## 5. USER FUNCTIONS

### 5.1 Dashboard

The dashboard is your home screen after login. It displays:
- Number of signature templates
- Total verifications performed
- Count of genuine signatures detected
- Recent verification activity

**Quick Actions:**
- Verify New Signature
- Manage Templates
- View Full History

### 5.2 Adding Signature Templates

Templates are sample signatures used for comparison during verification.

**Steps:**
1. Click "My Templates" in the sidebar
2. Scroll to "Add New Template" section
3. Click "Browse" to select a signature image
4. Preview the signature
5. Click "Save Template"
6. Repeat to add more templates (recommended: 3-5 templates)

**Tips for Best Results:**
- Use clear, high-resolution images
- Ensure good contrast between signature and background
- Capture entire signature without cutting off edges
- Use consistent lighting
- Avoid shadows or reflections

### 5.3 Verifying a Signature

**Steps:**
1. Click "Verify Signature" in the sidebar
2. Ensure you have at least one template added
3. Click "Browse" to upload the signature to verify
4. View the original and processed images
5. Click "Verify Signature" button
6. Wait 2-3 seconds for processing
7. View the result:
   - **Genuine** (Green): Signature matches templates
   - **Forged** (Red): Signature does not match templates
   - **Confidence Score**: Percentage of certainty (0-100%)

**Understanding Results:**
- 90-100%: Very high confidence
- 70-89%: High confidence (threshold for genuine)
- 50-69%: Medium confidence
- Below 50%: Low confidence

### 5.4 Viewing Verification History

**Steps:**
1. Click "History" in the sidebar
2. View table of all past verifications
3. Review statistics at the bottom:
   - Total genuine signatures
   - Total forged signatures
   - Average confidence score

**Information Displayed:**
- Verification ID
- Result (Genuine/Forged)
- Confidence percentage
- Date and time of verification

### 5.5 Managing Templates

**Viewing Templates:**
1. Click "My Templates"
2. Scroll down to see all saved templates
3. Each template shows:
   - Thumbnail image
   - Date added

**Adding Templates:**
- Follow steps in section 5.2

**Best Practices:**
- Add 3-5 genuine signature samples
- Update templates if your signature changes over time
- Ensure all templates are your genuine signatures

---

## 6. ADMINISTRATOR FUNCTIONS

### 6.1 Accessing Admin Panel

1. Login with administrator account
2. Look for "Admin Functions" section in sidebar
3. Click "Manage Users"

### 6.2 User Management

**View All Users:**
- See complete list of registered users
- View user details:
  - User ID
  - Username
  - Full Name
  - Email
  - User Type (user/admin)
  - Registration Date
  - Account Status (Active/Inactive)

**Statistics:**
- Total number of users in the system

### 6.3 Admin Best Practices

- Regularly review user accounts
- Monitor system usage
- Keep admin password secure and update regularly
- Create backup admin accounts for redundancy

---

## 7. TROUBLESHOOTING

### Problem: Cannot start the system

**Solutions:**
1. Check if Python is installed: `python --version`
2. Verify all libraries are installed: `pip list`
3. Try reinstalling requirements: `pip install -r requirements.txt`
4. Check if port 8501 is available
5. Try different port: `streamlit run app.py --server.port 8502`

### Problem: Login not working

**Solutions:**
1. Verify username and password are correct
2. Check if Caps Lock is on
3. Try resetting password (contact administrator)
4. Clear browser cache and cookies
5. Try a different browser

### Problem: Cannot upload signature images

**Solutions:**
1. Verify file format (PNG, JPG, JPEG only)
2. Check file size (should be under 10 MB)
3. Ensure image is not corrupted
4. Try converting image to PNG format
5. Verify you have sufficient storage space

### Problem: Low verification accuracy

**Solutions:**
1. Add more signature templates (3-5 recommended)
2. Use high-quality images for templates
3. Ensure consistent signature style
4. Remove background noise from images
5. Use proper lighting when capturing signatures

### Problem: Database errors

**Solutions:**
1. Stop the application
2. Delete `signature_system.db` file
3. Restart the application (new database created automatically)
4. Re-register users and add templates

### Problem: Slow performance

**Solutions:**
1. Close unnecessary applications
2. Ensure sufficient RAM available
3. Reduce number of open browser tabs
4. Clear verification history if very large
5. Restart computer and try again

---

## 8. FREQUENTLY ASKED QUESTIONS

**Q: How many signature templates should I add?**
A: We recommend 3-5 templates for best accuracy. More templates improve reliability.

**Q: Can I verify signatures from different people?**
A: No. Each user can only verify signatures against their own templates. This is a security feature.

**Q: What image format should I use?**
A: PNG, JPG, or JPEG formats are supported. PNG is recommended for best quality.

**Q: How accurate is the system?**
A: The system achieves approximately 90-95% accuracy for random forgeries and 85-90% for skilled forgeries, depending on template quality.

**Q: Can I use this system offline?**
A: Yes. After initial installation, the system runs completely offline on your local computer.

**Q: Is my data secure?**
A: Yes. All data is stored locally on your computer. Passwords are hashed using SHA-256 encryption.

**Q: Can I delete old verification logs?**
A: Currently, logs are permanent. Future versions will include log management features.

**Q: What if I forget my password?**
A: Contact your system administrator to reset your password.

**Q: Can multiple users access the system simultaneously?**
A: Yes, but they will use the same browser instance. For true multi-user access, deploy on a network server.

**Q: How do I update the system?**
A: Download the latest version, backup your database file, extract new files, and copy back your database.

---

## TECHNICAL SUPPORT

For additional help:
- **Email**: support@nathanict.com.ng
- **Phone**: +234 814 775 4855
- **Website**: https://nathanict.com.ng

---

## APPENDIX A: KEYBOARD SHORTCUTS

- **Ctrl + S**: Save (where applicable)
- **Ctrl + R**: Refresh page
- **Ctrl + W**: Close tab
- **Ctrl + Q**: Quit browser

---

## APPENDIX B: SYSTEM SPECIFICATIONS

**Technology Stack:**
- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python 3.8+
- **Database**: SQLite 3
- **Image Processing**: OpenCV, PIL
- **Authentication**: SHA-256 password hashing

**Database Tables:**
- users
- signature_templates
- verification_logs
- system_settings

---

**Document Version**: 1.0
**Last Updated**: 2025
**Developed by**: Nathan ICT Solutions

© 2025 Nathan ICT Solutions. All rights reserved.
