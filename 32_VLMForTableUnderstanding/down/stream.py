import os
import re
import sys
import time
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.llms import ChatMessage
from streamlit_autorefresh import st_autorefresh

# === Configure LLaMA 3 + Embeddings ===
Settings.llm = Ollama(model="llama3")
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

# === Streamlit UI ===
st.set_page_config(layout="wide")
st.title("🧪 Natural Language Query for Any CSV Table")
st.write(
    "Upload a CSV file or send it from the frontend. Then ask questions in plain language. "
    "The app will generate and execute Python code, and provide analysis based on the results."
)

# Autorefresh every 5 seconds (5000 ms), max 100 times
st_autorefresh(interval=5000, limit=100, key="polling")

# Sidebar history
st.sidebar.title("💬 Past Queries")
if 'history' not in st.session_state:
    st.session_state.history = []

for entry in st.session_state.history:
    st.sidebar.markdown(
        f"**Q:** {entry['user']}  \n"
        f"**A:** {entry.get('scalar_display', '') or ''}"
    )

# Handle CSV: from upload or injected file
uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])

csv_folder_path = "csv_final"

def get_newest_csv_file(folder):
    csv_files = [f for f in os.listdir(folder) if f.endswith('.csv')]
    if not csv_files:
        return None
    full_paths = [os.path.join(folder, f) for f in csv_files]
    return max(full_paths, key=os.path.getmtime)

if uploaded_file:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.session_state.source = "upload"
    st.session_state.current_csv_path = None  # clear any prior auto-loaded file
else:
    newest_csv = get_newest_csv_file(csv_folder_path)
    if newest_csv:
        if 'current_csv_path' not in st.session_state or st.session_state.current_csv_path != newest_csv:
            st.session_state.df = pd.read_csv(newest_csv)
            st.session_state.source = "folder_poll"
            st.session_state.current_csv_path = newest_csv
            st.success(f"✅ Loaded new CSV file: `{os.path.basename(newest_csv)}`")

# Display data if loaded
if 'df' in st.session_state:
    st.write("### 📊 Data Preview")
    st.dataframe(st.session_state.df.head())

    query = st.text_input("💬 Ask a question about the data:")
    if query:
        with st.spinner("🤖 Thinking..."):
            history_entry = {'user': query, 'assistant_code': None, 'scalar_display': None, 'analysis': None}

            # Build system prompt
            col_list = ", ".join(st.session_state.df.columns)
            desc = st.session_state.df.describe(include='all').fillna("").to_string()
            system_prompt = f"""
You are a smart data science assistant. Your job is to answer questions about a pandas DataFrame named `df`.
Always work with the full DataFrame (df), not just a sample.

Here are the column names: {col_list}

Here is a full description of the data:
{desc}

Instructions:
- Understand vague or natural questions.
- Generate Python code in a block like ```python ... ``` to answer the question.
- Use matplotlib/seaborn for visualizations if needed.
- Provide concise and clear code that can be executed to produce the answer.
- Do not include analysis or interpretation in this response; only provide the code to compute the answer.
"""
            messages = [ChatMessage(role="system", content=system_prompt), ChatMessage(role="user", content=query)]

            # Get code from LLM
            response = Settings.llm.chat(messages).message.content
            history_entry['assistant_code'] = response

            # Extract and execute Python code
            code_match = re.search(r"```python(.*?)```", response, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                with st.expander("Show generated code"):
                    st.code(code, language='python')

                # Capture print output
                stdout_buffer = StringIO()
                old_stdout = sys.stdout
                sys.stdout = stdout_buffer
                try:
                    local_env = {"df": st.session_state.df.copy(), "pd": pd, "plt": plt, "sns": sns}
                    exec(code, {}, local_env)
                except Exception as e:
                    sys.stdout = old_stdout
                    st.error(str(e))
                    local_env = {}
                finally:
                    sys.stdout = old_stdout

                printed = stdout_buffer.getvalue().strip()

                # Show output
                dfs = [val for val in local_env.values() if isinstance(val, pd.DataFrame) and not val.equals(st.session_state.df)]
                if dfs:
                    output_df = dfs[-1]
                    st.dataframe(output_df)
                    csv = output_df.to_csv(index=False)
                    st.download_button("Download filtered CSV", data=csv, file_name="filtered_data.csv", mime="text/csv")
                    history_entry['scalar_display'] = f"Displayed DataFrame ({len(output_df)} rows)"
                else:
                    fig = local_env.get('fig') or plt.gcf()
                    if fig and fig.get_axes():
                        st.pyplot(fig)
                        plt.clf()
                    elif printed:
                        try:
                            val = int(printed)
                            st.metric(label="Result", value=val)
                            history_entry['scalar_display'] = val
                        except ValueError:
                            st.text(printed)
                            history_entry['scalar_display'] = printed
                    else:
                        output = None
                        for val in local_env.values():
                            if isinstance(val, (int, float, str)):
                                output = val
                                break
                        if output is not None:
                            st.metric(label="Result", value=output)
                            history_entry['scalar_display'] = output

            # Ask for analysis
            analysis_in = f"The code has run and output displayed for: {query}. Please provide analysis of the result."
            messages.append(ChatMessage(role="user", content=analysis_in))
            analysis = Settings.llm.chat(messages).message.content
            history_entry['analysis'] = analysis
            st.expander("Show analysis").markdown(analysis)
            st.session_state.history.append(history_entry)
else:
    st.info("Please upload a CSV or send one from the frontend.")
