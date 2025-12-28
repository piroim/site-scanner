from module.imports import * 

#JSON 데이터를 JSON 파일로 저장하는 함수
def save_json(data):
    data_all = data.get('Output', {})
    with open("aaa.json", 'a', encoding='utf-8') as f:
        f.write(json.dumps(data_all, ensure_ascii=False) + '\n')

#CSV 파일 저장 함수 (헤더 중복방지 코드만 추가)
def save_csv():
    csv_file = ""
    fieldnames = []
    data_list = []
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, 'a', newline='', encoding='utf-8-sig') as csvfile:
        writer=csv.DictWriter(csvfile, fieldnames=fieldnames)

    if not file_exists:
        writer.writeheader()

    for user in data_list:
        filtered_user = {
            key: ('null' if (value == '' or value is None) else str(value))
            for key, value in user.items()
        }
        writer.writerow(filtered_user)

#JSON 데이터를 CSV로 저장
def save_json():
    data_list = []
    #여기는 JSON 데이터 또는 JSON 파일 지정
    with open('bbb.json', mode='r', encoding='utf-8') as f:
        data = json.load(f)
    
    user_all = data.get('aa')
    for i in user_all:
        data_list.append(i)
        
    #제외할 필드 값을 설정해서 필요한 필드만 저장
    exclude_fields = {'a','b','c'}
    csv_file = "aaa.csv"
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = [key for key in data_list[0].keys() if key not in exclude_fields]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if not file_exists:
            writer.writeheader()

        for user in data_list:
            filtered_user = {
                key: ('null' if (value == '' or value is None) else value)
                for key, value in user.items()
                if key not in exclude_fields
            }
            writer.writerow(filtered_user)
