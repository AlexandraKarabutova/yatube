from django.core.paginator import Paginator

POST_LIMIT: int = 10


def paginator(post_list, request):
    paginator = Paginator(post_list, POST_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
