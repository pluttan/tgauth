from flask import *


# --- Web Server (Flask) ---
@app.route('/auth', methods=['GET', 'POST'])
def auth():
    """Обрабатывает запрос аутентификации."""
    if request.method == 'POST':
        code = request.form['code']
        is_valid, user_id = is_code_valid(code)

        if is_valid:
            user_resources = get_user_resources(user_id)
            if not user_resources:
               return render_template('failure.html', message="У вас нет доступа ни к одному ресурсу.")

            # Помечаем код как использованный
            used_codes.add(code)
            del user_codes[user_id]

            # Добавьте логику выбора ресурса, если у пользователя есть доступ к нескольким.
            # Сейчас просто перенаправляет на первый доступный.
            resource = user_resources[0] #Выбираем первый доступный ресурс

            # Перенаправление на страницу ресурса
            return redirect(f"/{resource}")  #  Редирект на страницу ресурса
        else:
            return render_template('failure.html')

    return render_template('auth.html')

#Создаем отдельные роуты для каждого ресурса
@app.route('/<resource>')
def resource_page(resource):
    #Здесь должна быть проверка, имеет ли пользователь доступ к этому ресурсу
    #Иначе - показывать страницу с ошибкой доступа
    return f"Страница ресурса: {resource}" #Заглушка

@app.route('/')
def index():
    return "Сервер аутентификации работает."