from rest_framework.pagination import PageNumberPagination
from .responses import custom_response

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(
        self, 
        data,
        message
        ):
        return custom_response(
            status_code= 200,
            message= message,
            data = {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "results": data,
            }
        )
