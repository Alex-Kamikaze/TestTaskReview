def add_numeric_filter(queryset, param_name, value):
    """Работа с фильтрами для чисел в эндпоинте GET /hero"""
    if value is not None:
        try:
            value = int(value)
            if param_name.endswith("_gte"):
                return queryset.filter(**{param_name[:-4] + "__gte": value})
            elif param_name.endswith("_lte"):
                return queryset.filter(**{param_name[:-4] + "__lte": value})
            else:
                return queryset.filter(**{param_name: value})
        except ValueError:
            return queryset
    return queryset
