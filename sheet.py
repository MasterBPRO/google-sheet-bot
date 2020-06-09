import httplib2
import src
import pickle
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

credentials = ServiceAccountCredentials.from_json_keyfile_name(src.credentials, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


def writeTable(user_id, username, name, year, vacancy, experience, phone):
    try:
        with open("data.pickle", 'rb') as file:
            res = pickle.load(file)
            row = res['row']
            tableID = res['spreadsheetId']

        service.spreadsheets().values().batchUpdate(spreadsheetId=tableID, body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"Сотрудники!A{row}:G{row}",
                 "majorDimension": "ROWS",
                 "values": [
                            [user_id, username, name, year, vacancy, experience, phone]
                           ]}
            ]}).execute()

        with open('data.pickle', 'wb') as file:
            res['row'] += 1
            pickle.dump(res, file)
        return True

    except Exception as writeTableError:
        print(f"writeTableError: {writeTableError}")
        return False


if __name__ == "__main__":
    # Создания документа
    spreadsheet = service.spreadsheets().create(body={
        'properties': {'title': 'Заявки с телграмм бота', 'locale': 'ru_RU'},
        'sheets': [{'properties': {'sheetType': 'GRID',
                                   'sheetId': 0,
                                   'title': 'Сотрудники',
                                   'gridProperties': {'rowCount': 100, 'columnCount': 15}}}]}).execute()
    spreadsheetId = spreadsheet['spreadsheetId']  # сохраняем идентификатор файла
    # Настройка доступа
    driveService = apiclient.discovery.build('drive', 'v3', http=httpAuth)
    access = driveService.permissions().create(
        fileId=spreadsheetId,
        body={'type': 'user', 'role': 'writer', 'emailAddress': src.email},
        fields='id').execute()
    # Сохранения данных о номере строки и идентификатора таблицы
    data = {'row': 1, 'spreadsheetId': spreadsheetId}
    with open('data.pickle', 'wb') as _file:
        pickle.dump(data, _file)

    print(f"======  Успех!  ======\n"
          f"Скопируйте эти данные для дальнейшего контрооля за таблицой:\n"
          f"Идентификатор таблицы: {spreadsheetId}\n"
          f"Ссылка для просмотра таблицы: https://docs.google.com/spreadsheets/d/{spreadsheetId}/edit#gid=0\n"
          f"======  Конец даных!  ======\n")

    writeTable('ID', 'Username', 'Name', 'Year', 'Work', 'Experience', 'Phone')  # Тестирования таблицы