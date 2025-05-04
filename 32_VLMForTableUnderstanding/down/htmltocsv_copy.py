#!/usr/bin/env python3
import os
import time
import shutil
import csv
import pandas as pd
from bs4 import BeautifulSoup
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from csv import Sniffer

HTML_DIR = "html"
CSV_DIR = "csv"
PAIR_DIR = "pair"
CSV_FINAL = "csv_final"
HTML_FINAL = "html_final"

# Ensure final directories exist on startup
os.makedirs(CSV_FINAL, exist_ok=True)
os.makedirs(HTML_FINAL, exist_ok=True)

# In-memory storage for last processed pairs
global_pairs = []

def read_and_merge_csv(file1, file2, output_file):
    with open(file1, 'r') as f1:
        sniffer = Sniffer()
        sample = f1.read(1024)
        f1.seek(0)
        has_header = sniffer.has_header(sample)
        dialect = sniffer.sniff(sample)
        reader = csv.reader(f1, dialect)
        rows = list(reader)
        if has_header and rows:
            headers = rows[0]
            main_data = rows[1:]
        else:
            headers = [f'Column{i+1}' for i in range(len(rows[0]))] if rows else []
            main_data = rows
    with open(file2, 'r') as f2:
        reader2 = csv.reader(f2, dialect)
        cont = list(reader2)
    if main_data and cont and not cont[0][0].strip():
        main_data[-1] += cont[0][1:]
        cont = cont[1:]
    final = main_data + cont
    with open(output_file, 'w', newline='') as out:
        writer = csv.writer(out)
        if has_header:
            writer.writerow(headers)
        writer.writerows(final)
    return headers, final

def convert_csv_to_html(headers, data, html_path):
    with open(html_path, 'w') as h:
        h.write("<table border='1'>\n")
        if headers:
            h.write("<tr>" + "".join(f"<th>{col}</th>" for col in headers) + "</tr>\n")
        for row in data:
            h.write("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>\n")
        h.write("</table>")

def html_table_to_csv(html_file, output_dir, table_index=None):
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(html_file))[0]
    soup = BeautifulSoup(open(html_file, encoding='utf-8'), 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        print(f"No tables in {html_file}")
        return []
    paths = []
    indices = [table_index] if table_index is not None else range(len(tables))
    for i in indices:
        df = pd.read_html(str(tables[i]))[0]
        name = f"{base}.csv" if table_index is not None else f"{base}_table{i}.csv"
        out = os.path.join(CSV_DIR, name)
        df.to_csv(out, index=False)
        print(f"Saved CSV: {out}")
        paths.append(out)
    return paths

class HTMLHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.html'):
            print("New HTML detected:", event.src_path)
            csvs = html_table_to_csv(event.src_path, CSV_DIR)
            if is_pair_file_empty():
                transfer_to_final(csvs, event.src_path)
    def on_modified(self, event):
        if event.src_path.endswith('.html'):
            print("HTML modified:", event.src_path)
            csvs = html_table_to_csv(event.src_path, CSV_DIR)
            if is_pair_file_empty():
                transfer_to_final(csvs, event.src_path)

def is_pair_file_empty():
    pair_file = os.path.join(PAIR_DIR, 'paired.txt')
    return not os.path.exists(pair_file) or os.path.getsize(pair_file) == 0

def transfer_to_final(csv_paths, html_file=None):
    for c in csv_paths:
        dest_csv = os.path.join(CSV_FINAL, os.path.basename(c))
        shutil.copy(c, dest_csv)
        print(f"Copied CSV to final: {dest_csv}")
    if html_file:
        dest_html = os.path.join(HTML_FINAL, os.path.basename(html_file))
        shutil.copy(html_file, dest_html)
        print(f"Copied HTML to final: {dest_html}")

def process_pairs_and_cleanup():
    global global_pairs
    pair_file = os.path.join(PAIR_DIR, 'paired.txt')
    if not os.path.exists(pair_file):
        return
    # Read and parse pairs
    content = open(pair_file).read()
    lines = [l for l in content.splitlines() if l.strip()]
    # store exact filenames (with .csv) if provided, else append .csv
    global_pairs = []
    for line in lines:
        parts = line.split()
        global_pairs.append([p if p.lower().endswith('.csv') else p + '.csv' for p in parts])
    os.remove(pair_file)
    print(f"Processing {len(global_pairs)} pairs:", global_pairs)

    if not global_pairs:
        # no pairs: do nothing
        print("paired.txt was empty, nothing to merge.")
        return

    paired_set = set()
    # Merge each pair
    for p1_name, p2_name in global_pairs:
        p1 = os.path.join(CSV_DIR, p1_name)
        p2 = os.path.join(CSV_DIR, p2_name)
        if not os.path.exists(p1) or not os.path.exists(p2):
            print(f"Skipping missing pair files: {p1_name}, {p2_name}")
            continue
        out_csv = os.path.join(CSV_FINAL, f"{os.path.splitext(p1_name)[0]}_{os.path.splitext(p2_name)[0]}.csv")
        headers, data = read_and_merge_csv(p1, p2, out_csv)
        # generate HTML
        html_out = os.path.join(HTML_FINAL, os.path.splitext(os.path.basename(out_csv))[0] + '.html')
        convert_csv_to_html(headers, data, html_out)
        print(f"Merged and saved: {out_csv} & {html_out}")
        paired_set.update({p1, p2})

    # Copy any unpaired CSVs
    for fname in os.listdir(CSV_DIR):
        src = os.path.join(CSV_DIR, fname)
        if fname.endswith('.csv') and src not in paired_set:
            dest = os.path.join(CSV_FINAL, fname)
            shutil.copy(src, dest)
            print(f"Copied unpaired CSV: {fname}")

    print("Pair processing complete.")

if __name__ == '__main__':
    os.makedirs(HTML_DIR, exist_ok=True)
    os.makedirs(CSV_DIR, exist_ok=True)
    # Bootstrap any existing HTML
    for f in os.listdir(HTML_DIR):
        if f.endswith('.html'):
            csvs = html_table_to_csv(os.path.join(HTML_DIR,f), CSV_DIR)
            if is_pair_file_empty():
                transfer_to_final(csvs, os.path.join(HTML_DIR,f))
    # Start watcher
    handler = HTMLHandler()
    obs = Observer()
    obs.schedule(handler, HTML_DIR, recursive=False)
    obs.start()
    try:
        while True:
            time.sleep(5)
            process_pairs_and_cleanup()
    except KeyboardInterrupt:
        obs.stop()
        obs.join()
