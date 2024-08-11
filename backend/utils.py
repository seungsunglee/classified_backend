from rest_framework.renderers import BrowsableAPIRenderer


class BrowsableAPIRendererWithoutHTMLForms(BrowsableAPIRenderer):
    def get_rendered_html_form(self, data, view, method, request):
        return ""

    def render_form_for_serializer(self, serializer):
        return ""

    def get_raw_data_form(self, data, view, method, request):
        return None
