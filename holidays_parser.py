import csv
import requests
import time
from io import StringIO
from bs4 import BeautifulSoup


FILE_LIST = "currs.txt"         # Имя файла со списком валют
RESULT_FILE = 'holidays'        # Имя результируещего файл со списком праздников
SEARCH_YEAR = 2023              # Год поиска
IGNORE_LIST = ["RUB", "KZT"]    # Список валют с отдельным парсингом


dict_of_valute = {}
URL_LINK = "https://fxreporting.trading.refinitiv.net/dx/dxnrequest.aspx?RequestName=TadiPost"
international_months = dict(zip(['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                                        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
                                        'January', 'February', 'March', 'April', 'May', 'June',
                                        'July', 'August', 'September', 'October', 'November', 'December',
                                        'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT',
                                        'NOV', 'DEC'],
                                        [f"{i:02}" for i in range(1, 13)] * 3))


def parse_valute_to_csv(valute, year=SEARCH_YEAR):
    payload = {'TadiServer': 'TPASS',
                        'TadiUrl': '/testdx/curr_hols.call',
                        'in_CUR_CODE': valute,
                        'in_holiday_year': year,
                        'in_output_fmt': 'CSV'}
    
    try:
        send_message = requests.post(url=URL_LINK, data=payload)
    except Exception as err:
        print(f"Error {err}")
    else:
        text = send_message.text
        if len(text) > 70:
            csv_data_lines = text[63:].strip().split('\n')
            csv_file = StringIO('\n'.join(csv_data_lines))
            csvreader = csv.reader(csv_file)
            return csvreader
        
        print(f"{valute} is not found!")
        return None

def save_csv_to_dict(csvreader, valute):
    if csvreader:
        for row in csvreader:
            year, month, day, _ = row
            try:
                dict_of_valute[valute]
            except KeyError:
                dict_of_valute[valute] = []
            dict_of_valute[valute].append(f"{year}/{month.replace(month, international_months[month])}/{day} 1")
    

def get_valutes(filename=FILE_LIST):
    my_valutes = []
    with open(filename, "r", encoding="utf-8") as fread:
        for line in fread:
            my_valutes.append(line.strip())
    return my_valutes

def parse_ruble(year=SEARCH_YEAR, valute = "RUB"):
    rub_url = f"http://www.consultant.ru/law/ref/calendar/proizvodstvennye/{year}"

    try:
        r = requests.get(rub_url)
    except Exception as err:
        print(f"Error {err}")
    else:
        result = r.text

        soup = BeautifulSoup(result, 'html.parser')
        holidays = soup.findAll('table', class_='cal')
        try:
            dict_of_valute[valute]
        except KeyError:
            dict_of_valute[valute] = []
        for element in holidays:
            month = element.find('th', class_='month').get_text()
            month = international_months[month]
            holidays = element.findAll('td', class_='holiday weekend')
            list_holidays = [f"{year}/{month}/{int(day.text):02} 1" for day in holidays]
            if len(list_holidays) >= 1: dict_of_valute[valute].extend(list_holidays)

def parse_tenge(year=SEARCH_YEAR, valute = "KZT"):
    tenge_url = f"https://kase.kz/en/reglament/"
    
    try:
        r = requests.get(tenge_url)
    except Exception as err:
        print(f"Error {err}")
    else:
        result = r.text

        soup = BeautifulSoup(result, 'html.parser')
        holidays = soup.findAll('div', class_='calendar')
        tmp_months = []
        
        try:
            dict_of_valute[valute]
        except KeyError:
            dict_of_valute[valute] = []
        
        for element in holidays:
            month = element.find('span', class_='mounth-name').get_text()
            month = month.strip()
            if month not in tmp_months:
                tmp_months.append(month)
                month = international_months[month]
                holidays = element.findAll('td', class_='trading-day')
                list_holidays = [f"{year}/{month}/{int(day.text):02} 1" for day in holidays]
                if len(list_holidays) >= 1: dict_of_valute[valute].extend(list_holidays)

        

def write_to_txt_file():
    write_file = f'{RESULT_FILE} - {time.strftime("%d-%m-%Y %H_%M")}.txt'
    with open(write_file, 'w') as fwrite:
        for key, values in dict_of_valute.items():
            fwrite.write(f"""{key}\n{{\n""")
            fwrite.write('\tHolidays\n')
            fwrite.write('\t{\n')
            for i in values:
                fwrite.write(f'\t\t{i}\n')
            fwrite.write('\t}\n')
            fwrite.write('}\n')
            print(f"Праздники для {key} записаны")



def main():
    result_list = get_valutes() 
    for el in result_list:
        if el not in IGNORE_LIST:
            csv_result = parse_valute_to_csv(el)
            save_csv_to_dict(csv_result, el)
        else:
            if el == "RUB":
                parse_ruble()
            elif el == "KZT":
                parse_tenge()
    write_to_txt_file()

main()
