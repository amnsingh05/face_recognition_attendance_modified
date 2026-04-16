🧠 Face Recognition Attendance System

An intelligent AI-powered attendance system that uses Face Recognition to automate attendance marking in real-time.

This project eliminates manual attendance, reduces fraud, and provides a modern solution using Computer Vision + Machine Learning + Streamlit Web App.


✨ Real-time face recognition
🔐 Secure admin authentication
📸 Face registration via camera
🧠 ML model training (LBPH)
📊 Attendance tracking & export
🌐 Full Streamlit web dashboard


🏗️ Project Architecture
User Face → Camera → Face Detection → Face Recognition → Attendance Logged → Dashboard
🧩 Tech Stack
Category	Technology
Language	Python
Computer Vision	OpenCV
ML Model	LBPH Face Recognizer
Data Handling	Pandas, NumPy
GUI	Tkinter
Web App	Streamlit


Dependencies:
📂 Project Structure
├── streamlit_app.py        # Web app
├── streamlit_core.py       # Core logic
├── login_gui.py            # Login UI
├── main_gui.py             # Dashboard
├── register_face.py        # Face capture
├── train_model.py          # Model training
├── take_attendance.py      # Attendance system
├── view_attendance.py      # Reports & export
├── admin_utils.py          # Authentication system
├── requirements.txt
├── faces/
├── trainer/
├── attendance/


⚙️ Installation
git clone https://github.com/your-username/face-attendance-system.git
cd face-attendance-system
pip install -r requirements.txt
▶️ Run the Project
🖥️ Desktop Version
python login_gui.py
🌐 Web Version
streamlit run streamlit_app.py

Open 👉 http://localhost:8501

🔑 Default Credentials
Username: admin
Password: admin123

⚠️ Change after first login (security best practice)

🔄 Workflow
1. Login
2. Register Face
3. Train Model
4. Take Attendance
5. View Reports
🔐 Security Features
SHA-256 password hashing
Secure login verification
Security question-based reset
📊 Output Example
Name       Date        Time
Aman       2026-04-16  10:32:45
Rahul      2026-04-16  10:34:12

🎯 Use Cases
🏫 Schools & Colleges
🏢 Offices
📚 Coaching Centers
🧠 Smart AI Systems
⚠️ Best Practices
Use good lighting
Capture 20–30 samples per person
Retrain model after adding users
Keep camera stable
🌟 Future Improvements
☁️ Cloud database (Firebase / MongoDB)
📱 Mobile app integration
😷 Mask detection
📡 Multi-camera system
🤖 AI analytics dashboard

👨‍💻 Author
Aman Singh


⭐ Support
If you like this project:
👉 Star the repo
👉 Fork it
👉 Share it

📜 License
This project is licensed under the MIT License