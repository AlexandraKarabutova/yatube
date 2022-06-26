# Импортируем CreateView, чтобы создать ему наследника
# Функция reverse_lazy позволяет получить URL по параметрам функции path()
from django.urls import reverse_lazy
from django.views.generic import CreateView

# Импортируем класс формы, чтобы сослаться на неё во view-классе
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    # куда перенаправить пользователя после успешной отправки формы
    success_url = reverse_lazy('posts:index')
    # имя шаблона, куда будет передана переменная form с объектом HTML-формы
    template_name = 'users/signup.html'
