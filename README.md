# AI Circuit Builder (Llama 3 with Ollama)

This is a Streamlit app that allows you to describe a circuit or upload a BOM (Bill of Materials) and get:

- Clarifying questions and suggestions from Llama 3 (Ollama)
- A preliminary block diagram
- Downloadable BOM (Excel/CSV)
- Pin-to-pin connection details (JSON/CSV)
- Clone the repository:
  ```bash
   git clone <your-repo-url>
   cd llama_circuit_app

---

## **Setup Instructions**

Create a virtual environment (recommended):
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

Install dependencies:
pip install -r requirements.txt


Run the Streamlit app:
streamlit run app.py


