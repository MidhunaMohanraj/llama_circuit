import streamlit as st
import requests
import pandas as pd
import schemdraw
import schemdraw.elements as elm
import io

# -------------------------
# 🧠 OLLAMA CONFIG
# -------------------------
OLLAMA_API_URL = "http://localhost:11434/api/generate"
LLAMA3_MODEL = "llama3"

st.set_page_config(page_title="AI Circuit Builder", layout="wide")
st.title("⚙️ AI Circuit Builder with Llama 3 (Ollama)")

st.markdown("""
Describe your circuit or upload a BOM (optional).  
Llama 3 will ask clarifying questions first, generate a block diagram,  
and once you're happy, you can download the final BOM file.
""")

# -------------------------
# 🔹 INPUTS
# -------------------------
# -------------------------
# 🔹 INPUTS
# -------------------------
uploaded_file = st.file_uploader("📄 Upload BOM Excel/CSV (optional)", type=["xlsx", "csv"])
user_input = st.text_area("🧠 Describe your circuit requirements:")

# -------------------------
# 🔗 MULTIPLE LCSC LINKS
# -------------------------
st.markdown("### 🔗 LCSC Component Links (Optional)")

# Initialize list in session state
if "lcsc_links" not in st.session_state:
    st.session_state.lcsc_links = [""]

# Render text inputs
for i, link in enumerate(st.session_state.lcsc_links):
    st.session_state.lcsc_links[i] = st.text_input(
        f"LCSC Link {i+1}",
        value=link,
        key=f"lcsc_link_{i}"
    )

# Add button
if st.button("➕ Add LCSC Link"):
    st.session_state.lcsc_links.append("")

# Show valid links
valid_links = [l for l in st.session_state.lcsc_links if l.strip()]
if valid_links:
    st.markdown("#### 📄 Current LCSC Links")
    st.json(valid_links)


# Load BOM if provided
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.write("**Uploaded BOM preview:**")
        st.dataframe(df)
        bom_parts = df.get('Name', df.columns[0]).tolist()
    except Exception as e:
        st.error(f"Error reading BOM: {e}")
        bom_parts = []
else:
    bom_parts = []

# -------------------------
# 💬 LLM Query Function
# -------------------------
def query_ollama(prompt):
    """Send prompt to local Ollama (Llama 3)."""
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": LLAMA3_MODEL, "prompt": prompt, "stream": False},
            timeout=90
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("response") or data.get("results", [{}])[0].get("text", "")
        else:
            return f"❌ Ollama error: {response.text}"
    except Exception as e:
        return f"⚠️ Connection error: {str(e)}"

# -------------------------
# ⚙️ COMPONENT SETTINGS
# -------------------------
st.markdown("### 🧩 Components List")

default_components = [
    {"type": "Resistor", "value": "10kΩ"},
    {"type": "Capacitor", "value": "100nF"},
    {"type": "LED", "value": "Green"},
]

if "components" not in st.session_state:
    st.session_state["components"] = default_components

for i, comp in enumerate(st.session_state["components"]):
    col1, col2 = st.columns([2, 1])
    with col1:
        comp["type"] = st.text_input(f"Component {i+1} Type", comp["type"], key=f"type_{i}")
    with col2:
        comp["value"] = st.text_input(f"Value", comp["value"], key=f"value_{i}")

if st.button("➕ Add Component"):
    st.session_state["components"].append({"type": "", "value": ""})

# -------------------------
# ⚡ SCHEMATIC GENERATION (Block Diagram)
# -------------------------
def generate_block_diagram(components):
    """Generate a visible block diagram with properly spaced boxes."""
    import schemdraw
    import schemdraw.flow as flow

    d = schemdraw.Drawing(show=False)
    d.config(unit=3)

    x_offset = 0  # starting position

    for i, comp in enumerate(components):

        # Draw the box at a specific location
        box = d.add(
            flow.Box(w=4, h=2)
            .label(f"{comp['type']}\n{comp['value']}", fontsize=12)
            .at((x_offset, 0))
        )

        # Add arrow to next block
        if i < len(components) - 1:
            d.add(flow.Arrow().right().at(box.E))
            x_offset += 6  # move next block to the right

    # Convert to SVG
    svg_data = d.get_imagedata("svg")
    if isinstance(svg_data, bytes):
        svg_data = svg_data.decode("utf-8")

    svg_data = svg_data.replace("<svg ", '<svg style="background-color:white;" ')
    return svg_data


# -------------------------
# 🚀 SMART FLOW: Clarify → Review → Generate BOM
# -------------------------
if st.button("🤖 Generate Block Diagram"):
    if not user_input:
        st.warning("Please enter a description first.")
    else:
        prompt = f"""
You are an expert electronics engineer.

User request: "{user_input}"
Uploaded BOM parts: {bom_parts}

1️⃣ If the description is unclear, ask 3–5 clarifying questions.
2️⃣ If enough information is available, summarize the circuit idea and list key components.
3️⃣ Provide a preliminary block diagram description.

Return the output clearly with sections:
'Questions', 'Block Diagram Summary', and 'Key Components'.
"""
        ai_response = query_ollama(prompt)
        st.session_state["ai_response"] = ai_response

        st.markdown("### 🤖 Llama 3 Response:")
        st.write(ai_response if ai_response else "No response received from model.")

        # Generate preliminary block diagram for visual review
        try:
            schematic_svg = generate_block_diagram(st.session_state["components"])
            st.markdown("### 🧭 Preliminary Block Diagram:")
            st.components.v1.html(schematic_svg, height=500, scrolling=True)
        except Exception as e:
            st.error(f"Error generating block diagram: {e}")

# -------------------------
# ✅ Generate BOM after confirmation
# -------------------------
st.markdown("### 💾 Generate BOM File")

if st.button("Generate BOM Excel/CSV"):
    if st.session_state.get("ai_response") is None:
        st.warning("Please generate block diagram and confirm components first.")
    else:
        try:
            import xlsxwriter  # ensures the module is available
        except ImportError:
            st.error("⚠️ Please install xlsxwriter: run `pip install xlsxwriter` in your terminal.")
        else:
            # Create BOM DataFrame
            bom_df = pd.DataFrame(st.session_state["components"])

            # Provide download as Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                bom_df.to_excel(writer, index=False, sheet_name='BOM')

            st.download_button(
                label="📥 Download BOM File",
                data=output.getvalue(),
                file_name="circuit_BOM.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
# -------------------------
# 🔌 Generate Connection Details
# -------------------------
st.markdown("### 🔗 Generate Connection Details")

if st.button("🔍 Generate Connection Table"):
    if st.session_state.get("ai_response") is None:
        st.warning("Please generate the block diagram and confirm components first.")
    else:
        connection_prompt = f"""
You are an expert electronics circuit designer.

Given the following circuit description and components:
{user_input}

Components list:
{st.session_state['components']}

Task:
1️⃣ Generate a table of pin-to-pin connections between these components.
2️⃣ Include connection type (signal, power, ground, etc.).
3️⃣ If unsure, make reasonable engineering assumptions.

Format strictly as JSON array with fields:
[
  {{
    "From_Component": "Resistor R1",
    "From_Pin": "Pin 1",
    "To_Component": "LED D1",
    "To_Pin": "Anode",
    "Connection_Type": "Signal"
  }},
  ...
]
"""

        connection_response = query_ollama(connection_prompt)

        # Try to display as JSON table
        try:
            import json
            connection_data = json.loads(connection_response)
            conn_df = pd.DataFrame(connection_data)
            st.markdown("### 📊 Connection Details Table:")
            st.dataframe(conn_df)

            # Offer download as JSON or CSV
            json_output = io.BytesIO(json.dumps(connection_data, indent=2).encode("utf-8"))
            csv_output = io.BytesIO(conn_df.to_csv(index=False).encode("utf-8"))

            st.download_button(
                label="📥 Download Connection Details (JSON)",
                data=json_output,
                file_name="connection_details.json",
                mime="application/json"
            )

            st.download_button(
                label="📥 Download Connection Details (CSV)",
                data=csv_output,
                file_name="connection_details.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.text(connection_response)

# -------------------------
# 🌐 LCSC Placeholder
# -------------------------
# -------------------------
# 🌐 LCSC Links Placeholder
# -------------------------
if "lcsc_links" in st.session_state:
    valid_links = [l for l in st.session_state.lcsc_links if l.strip()]
    if valid_links:
        st.info(f"{len(valid_links)} LCSC link(s) added.\n(Future: fetch specs via LCSC API)")
