# SPECTRA-AI  
**AI-Based Identity Verification & Fake Content Detection Platform**

SPECTRA-AI is a computer vision–driven system designed to verify the identity of public figures and detect impersonation, fake images, and manipulated media.  
The platform extracts faces from images, encodes identity into numerical embeddings, and compares them to determine whether two images belong to the same person.

---

## 🚀 Project Vision

In the digital age, celebrities and public figures are frequently targeted with:
- Fake images
- AI-generated content
- Identity impersonation
- Misinformation campaigns

**SPECTRA-AI** provides a technical foundation to:
- Verify whether an image truly belongs to a person
- Detect identity mismatches
- Support future deepfake detection and social media monitoring

---

## 🧠 System Pipeline

Input Image (Group Photo / Online Image)
↓
[Step 2] Face Detection & Alignment
↓
Aligned Individual Faces
↓
[Step 3] Face Embedding (Identity Encoding)
↓
Numerical Face Vectors
↓
[Step 4] Face Matching (Similarity Check)
↓
Verified / Not Verified

---

## ✅ Current Implementation Status

| Step | Module | Status |
|------|--------|--------|
Step 1 | Input Handling | ✔ Completed |
Step 2 | Face Detection & Alignment | ✔ Completed |
Step 3 | Face Embedding (FaceNet / DeepFace) | ✔ Completed |
Step 4 | Face Matching (Cosine Similarity) | ✔ Completed |
Step 5 | Deepfake / Morph Detection | ⏳ Planned |
Step 6 | Social Media Monitoring Platform | ⏳ Planned |

---

## 🧩 Core Features

### 🔍 Face Detection & Alignment
- Detects multiple faces in a group image
- Crops and aligns each face
- Stores individual face images for further processing

### 🧬 Face Embedding
- Converts each aligned face into a **128-dimensional numerical vector**
- Uses **FaceNet via DeepFace**
- Embeddings are consistent and identity-based

### 🔐 Face Matching (Verification)
- Compares two face embeddings using **cosine similarity**
- Determines:
  - **Same person** (verified)
  - **Different person** (possible impersonation)

---

## 📁 Project Structure

SPECTRA-AI/
│
├── ai_models/
│ └── face_recognition/
│ ├── detector.py # Face detection
│ ├── align.py # Face alignment
│ ├── embedder.py # Face embedding
│ └── matcher.py # Face matching
│
├── data/
│ ├── extracted-faces/ # Output from Step 2
│ └── embeddings/ # Saved embeddings (.npy files)
│
├── tests/
│ ├── test_retinaface.py # Step 2 test
│ ├── test_embedding.py # Step 3 test
│ └── test_matching.py # Step 4 test
│
├── requirements.txt
└── README.md

---

## ⚙️ Setup Instructions

### 1️⃣ Create Virtual Environment
```bash
    python -m venv venv
    venv\Scripts\activate

2️⃣ Install Dependencies
    pip install -r requirements.txt
▶ How to Run

🔹 Step 2 — Face Detection & Alignment
    python -m tests.test_retinaface
Output:
Aligned face images stored in:
data/extracted-faces/aligned/

🔹 Step 3 — Face Embedding

    python -m tests.test_embedding
Output:
Numerical embeddings stored in:
data/embeddings/*.npy

🔹 Step 4 — Face Matching
    python -m tests.test_matching
Output Example:
Similarity Score: 0.73
✅ Same person
or
Similarity Score: 0.32
❌ Different person

🧠 Technical Details
Face Detection: RetinaFace / OpenCV
Embedding Model: FaceNet (via DeepFace)
Matching Metric: Cosine Similarity
Embedding Size: 128-Dimensional
Language: Python

🧪 Example Use Case :
A celebrity registers their authentic images in the system.
The system extracts faces and stores identity embeddings.
A new image appears online.
The system:
Extracts the face
Generates a new embedding
Compares it with stored embeddings
If similarity is high → Verified
If similarity is low → Possible Fake / Impersonation

⚠️ Current Limitations :
Does not yet detect AI-generated or morphed images directly.
Matching accuracy may decrease for:
Extremely low-quality images
Heavy occlusion (masks, sunglasses)
Extreme face angles
Social media monitoring is not yet automated.

🔮 Future Work :
🔍 Deepfake & Morph Detection
🌐 Automated Social Media Monitoring
🗄️ Database for registered public figures
⚡ Large-scale face search using vector databases (FAISS)
📊 Web dashboard for verification results

📜 License
This project is for academic and research purposes.

---

# 🧠 WHAT I ADDED / IMPROVED

✔ Removed duplicates  
✔ Fixed Markdown formatting  
✔ Added **Use Case section**  
✔ Added **Limitations section** (important for academic projects)  
✔ Cleaned command blocks  
✔ Improved professional tone  

---
