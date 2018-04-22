from __future__ import absolute_import

from dependencies import this
from django.views.generic import FormView, View


def view(injector):
    """Create Django class-based view from injector class."""

    handler = create_handler(View)
    apply_http_methods(handler, injector)
    return injector.let(as_view=handler.as_view)


def form_view(injector):
    """Create Django form processing class-based view from injector class."""

    handler = create_handler(FormView)
    apply_form_methods(handler, injector)
    return injector.let(as_view=handler.as_view)


def create_handler(from_class):

    class Handler(from_class):
        pass

    return Handler


def apply_http_methods(handler, injector):

    for method in ["get", "post", "put", "patch", "delete", "head", "options", "trace"]:
        if method in injector:

            def __view(self, request, *args, **kwargs):
                ns = injector.let(
                    view=self,
                    request=request,
                    args=args,
                    kwargs=kwargs,
                    user=this.request.user,
                )
                return getattr(ns, __view.method)()

            __view.method = method
            setattr(handler, method, __view)


# TODO: allow to override http_method_not_allowed?


def apply_form_methods(handler, injector):

    handler.form_class = injector.form_cls
    handler.template_name = injector.template_name
    handler.success_url = injector.success_url

    for method in ["form_valid", "form_invalid"]:
        if method in injector:

            def __method(self, form):
                ns = injector.let(
                    view=self,
                    form=form,
                    request=this.view.request,
                    args=this.view.args,
                    kwargs=this.view.kwargs,
                    user=this.request.user,
                )
                return getattr(ns, __method.method)()

            __method.method = method
            setattr(handler, method, __method)


# TODO:
#
# TemplateResponseMixin.template_name
# TemplateResponseMixin.template_engine
# TemplateResponseMixin.response_class
# TemplateResponseMixin.content_type
#
# FormMixin.initial
# FormMixin.form_class
# FormMixin.success_url
# FormMixin.prefix
#
# ContextMixin.extra_context
