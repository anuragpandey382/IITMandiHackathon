import os

for file in os.listdir('./public/uploads/'):
        file_path = os.path.join('./public/uploads', file)
        if os.path.isfile(file_path):
            print(f"Removing file: {file_path}")
            os.remove(file_path)

for file in os.listdir('./public/preprocess_results/'):
    file_path = os.path.join('./public/preprocess_results', file)
    if os.path.isfile(file_path):
        print(f"Removing file: {file_path}")
        os.remove(file_path)

for file in os.listdir('./public/results/'):
    file_path = os.path.join('./public/results', file)
    if os.path.isfile(file_path):
        print(f"Removing file: {file_path}")
        os.remove(file_path)
 
if(os.path.exists('./public/results.json')):
    os.remove('./public/results.json')
    print("results.json removed")

if(os.path.exists('./public/results.html')):
    os.remove('./public/results.html')
    print("results.html removed")
