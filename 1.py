from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus

app = Flask(__name__)

# Функция для очистки данных (оставляем только буквы и цифры)
def clean_data(data):
    return ''.join(re.findall(r'\w+', data))  # Оставляем только буквы и цифры

# Функция для получения ссылок с сайта
def get_links(query):
    query_encoded = quote_plus(query)  # Кодируем запрос для URL
    url = f'https://reveng.ee/search?q={query_encoded}&per_page=100'  # Запрос с параметром per_page
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим все ссылки нужного формата
    links = []
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        if 'entity' in link:
            links.append('https://reveng.ee' + link)
    
    # Применяем фильтрацию, исключая повторяющиеся ссылки
    links = list(set(links))
    
    return links

# Функция для парсинга всей информации с каждой страницы
def parse_info_from_links(links):
    data_list = []  # Список для хранения данных, которые будут отображены на веб-странице
    for link in links:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Парсим блок с данными
        entity_info = soup.find('div', class_='bg-body rounded shadow-sm p-3 mb-2 entity-info')
        if entity_info:
            data = []

            # Парсим имя (если оно есть)
            name_element = entity_info.find('span', class_='entity-prop-value')
            if name_element:
                data.append(['ФИО', name_element.get_text(strip=True)])

            # Парсим данные из таблицы, исключая ID и длинные строки
            for row in entity_info.find_all('tr', class_='property-row'):
                property_name = row.find('td', class_='property-name').get_text(strip=True)
                property_value = row.find('td', class_='property-values').get_text(strip=True)

                # Пропускаем строки, содержащие ID и длинные строки (например, хеши или зашифрованные данные)
                if 'id' in property_name.lower() or len(property_value) > 50:
                    continue

                # Добавляем данные в список, делая различие по названию свойства
                if property_name.lower() in ["телефон", "номер телефона", "тел.", "mobile"]:
                    data.append(['Телефон', property_value])
                elif property_name.lower() in ["номер паспорта", "паспорт", "passport"]:
                    data.append(['Номер паспорта', property_value])
                elif property_name.lower() in ["адрес", "address"]:
                    data.append(['Адрес', property_value])
                else:
                    # Добавляем любое другое свойство
                    data.append([property_name, property_value])

            # Если данные есть, добавляем их в список для вывода
            if data:
                data_list.append(data)
        else:
            data_list.append([["Ошибка", "Не удалось найти информацию на странице."]])

    return data_list


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        query = request.form["query"]
        cleaned_data = clean_data(query)

        links = get_links(query)
        data_list = parse_info_from_links(links)

        return render_template("index.html", cleaned_data=cleaned_data, data_list=data_list, links=links)
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
