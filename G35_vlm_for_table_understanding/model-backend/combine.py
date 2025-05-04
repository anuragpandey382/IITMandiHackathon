from google import genai
import os
from csv2html import csv2html

client = genai.Client(api_key="")

def combine_tables():
    input_dir = './'
    output_dir = './'
    csv_contents = []
    for filename in sorted(os.listdir(input_dir)):
        if not filename.endswith('.csv'):
            continue

        path = f'{input_dir}{filename}'

        csv_content = ''
        with open(path, 'r') as file:
            csv_content = file.read()
        if not csv_content:
            print(f"⚠️ Skipping empty file: {filename}")
            continue

        csv_contents.append(csv_content)
        print(f"→ Processing {filename}")

    prompt = f"""
    Consider yourself an expert in undesrtanding tables and dataframes.
    I will provide you multiple csv content extracted from the pdf, and want you to see and analyze it and based on your understanding,
    combine the csv contents that you think are from the same table and create a new csv file for each group of tables.
    In the end, you will return the csv contents of all the new csv files you created.
    The csv contents are as follows: {str(csv_contents)}
    Please return the csv contents of all the new csv files you created.
    Points to consider: 
        1. You have to return the csv contents of all the new csv files you created.'
        2. You have to return the csv contents in a list format.'
        Example output:
            csv_contents = [csv_content1, csv_content2, csv_content3]'
        4. Remember to return only the csv contents like mentioned in the example, nothing else.
        5. Do not return any explanation or any other text.
        6. Do not return any csv file, only the csv contents.
        7. Do not return any other text, only the csv contents.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents = prompt
    )
    csv_contents = response.text.split('\n')
    csv_contents = [csv_content for csv_content in csv_contents if csv_content.strip() != '']
    num = 0
    for i, csv_content in enumerate(csv_contents, start=1):
        csv_content = csv_content.replace("'", "").replace('"', '')
        if ',' not in csv_content:
            print(f"⚠️ Skipping invalid csv content: {csv_content}")
            continue
        with open(f'{output_dir}combined_group_{num}.csv', 'w') as file:
            csv_content = csv_content.replace('\\n', '\n')
            file.write(csv_content)
            with open(f'{output_dir}combined_group_html_{num}.html', 'w') as file:
                file.write(csv2html(csv_content))
        print(f"→ Created combined_table_{num}.csv")
        num += 1
    
    return num


        