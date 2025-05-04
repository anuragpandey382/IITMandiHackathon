import os
import pandas as pd
from google import genai

client = genai.Client(api_key="")

CSV_DIR = "./"
output_dir = "./"

def ask_structure(file_path):
    """
    Use LLM to determine if CSV has a header.
    Returns:
      '0' => has header (start new group)
      '1' => no header (append to previous group)
    """
    try:
        df = pd.read_csv(file_path, nrows=5)
        preview = df.to_csv(index=False)
    except Exception:
        with open(file_path, 'r', errors='ignore') as f:
            lines = [next(f) for _ in range(5)]
            preview = ''.join(lines)

    prompt = f"""
        You are a data processing assistant specializing in understanding CSV file formats.

        You will be shown the **first few lines of a CSV file**. Your job is to decide whether it contains a **header row** (a row that defines the field names or column titles) or if it only contains **data rows** (actual content/records, without any column names).

        Below is the preview of the CSV file you need to analyze:

        --- CSV Preview ---
        {preview}
        -------------------

        Your task:

        Respond with only a single character:
        - 0 — if the first row is a header (column names like `Name, Age, Salary, Department`)
        - 1 — if the first row is not a header (just plain data like `Alice, 30, Engineering, 70000`
        Do **not** include any explanation, description, or extra characters. Only respond with `0` or `1`.

        -------------------
        ✅ Examples to guide you:

        Example 1:
        Name,Age,Department,Salary  
        Alice,30,Engineering,70000  
        Bob,25,Marketing,50000  
        → Output: 0 (The first row is a header)

        Example 2:
        Alice,30,Engineering,70000  
        Bob,25,Marketing,50000  
        Charlie,35,Finance,80000  
        → Output: 1 (No header, just data)

        Example 3:
        Invoice ID, Order Date, Customer, Total Amount  
        1001,2024-12-01,Acme Corp,500.75  
        1002,2024-12-02,XYZ Ltd,1030.00  
        → Output: 0 (First row defines fields)

        Example 4:
        1001,2024-12-01,Acme Corp,500.75  
        1002,2024-12-02,XYZ Ltd,1030.00  
        → Output: 1 (All rows are data)

        Example 5:
        Column1,Column2,Column3  
        Value1,Value2,Value3  
        → Output: 0 (Even generic names like Column1 can be headers
        -------------------

        Now, based on the above instructions and examples, reply with only `0` or `1` indicating whether the CSV preview includes a header row or not.
        """

    
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents = prompt
    )

    return response.text

import uuid

def is_redundant_header(row, base_cols):
    return all(str(cell).strip() == str(header).strip() for cell, header in zip(row, base_cols))

def handle_unnamed_columns(df, base_cols=None):
    if base_cols is not None:
        if len(df.columns) == len(base_cols):
            df.columns = base_cols
        else:
            raise ValueError("Column count mismatch with base columns")
    return df

def combine(input_dir=CSV_DIR, output_dir=output_dir):
    groups = []  # List of (base_columns, dataframe)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    for filename in sorted(os.listdir(input_dir)):
        if not filename.endswith('.csv'):
            continue

        path = os.path.join(input_dir, filename)

        if os.path.getsize(path) == 0:
            print(f"⚠️ Skipping empty file: {filename}")
            continue

        print(f"→ Processing {filename}")

        try:
            flag = str(ask_structure(path)).strip()
            print(f"  LLM says: {'HEADER' if flag == '0' else 'NO HEADER'}")

            if flag == '0' or not groups:
                # Ensure all rows in the CSV have the same number of columns
                with open(path, 'r') as file:
                    lines = file.readlines()

                max_columns = max(len(line.split(',')) for line in lines)
                with open(path, 'w') as file:
                    for line in lines:
                        columns = line.strip().split(',')
                        file.write(','.join(columns + [''] * (max_columns - len(columns))) + '\n')
                df = pd.read_csv(path, on_bad_lines='skip', dtype=str, keep_default_na=False)
                if df.empty:
                    print(f"⚠️ Skipping empty dataframe from file: {filename}")
                    continue

                base_cols = list(df.columns)

                df = df[~df.apply(lambda row: is_redundant_header(row, base_cols), axis=1)]

                groups.append((base_cols, df))

            else:  
                df = pd.read_csv(path, header=None, on_bad_lines='skip', dtype=str, keep_default_na=False)
                if df.empty:
                    print(f"⚠️ Skipping empty dataframe from file: {filename}")
                    continue

                if not groups:
                    
                    default_columns = [f"Column{i+1}" for i in range(df.shape[1])]
                    df.columns = default_columns
                    groups.append((default_columns, df))
                    print("⚠️ No previous group — created new group with default headers.")
                else:
                    base_cols, last_df = groups[-1]

                    if len(base_cols) != df.shape[1]:
                        print(f"❌ Column count mismatch: skipping file {filename}")
                        continue

                    df = handle_unnamed_columns(df, base_cols)

                    df = df[~df.apply(lambda row: is_redundant_header(row, base_cols), axis=1)]

                    groups[-1] = (base_cols, pd.concat([last_df, df], ignore_index=True))

        except pd.errors.EmptyDataError:
            print(f"❌ pandas EmptyDataError — skipping file: {filename}")
        except Exception as e:
            print(f"❌ Unexpected error while processing {filename}: {e}")

    for idx, (cols, df) in enumerate(groups, start=1):
        out_path = f"combined_group_{idx}.csv"
        df.to_csv(out_path, index=False)
        print(f"✅ Group {idx}: {len(df)} rows → {out_path}")
    
    return idx
