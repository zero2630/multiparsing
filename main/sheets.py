import gspread
from  google.oauth2.service_account import Credentials


scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("../credentials.json", scopes=scopes)
spreadsheet_id = "14dTF2sTdXjzEEE-2YUhd-Ye26iRA4KWh8yz7vxGd0Hs"

## Класс для работы с google sheets
class SheetsManager:
    def __init__(self):
        self.rows = [] # список, в котором хранятся данные о новых товарах

        self.client = gspread.authorize(creds) # клиент для работы с google sheets
        self.spreadsheet = self.client.open_by_key(spreadsheet_id) # таблица, в которую записываются данные
        self.sheet = self.spreadsheet.worksheet("Лист1") # лист для записи данных

    # добавление данных в список rows
    def add_row(self, row):
        self.rows.append(row)

    # добавление новых строк из rows в google sheets
    def push_rows(self):
        if self.rows: # проверка, что в списке что-то есть
            self.sheet.append_rows(self.rows) # добавляем в таблицу новые строки после последней
            self.rows = [] # обнуляем список
