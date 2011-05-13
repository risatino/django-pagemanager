from django.contrib import admin
from django.contrib.admin.util import unquote
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _

from reversion.admin import VersionAdmin

from pagemanager.models import Page
from pagemanager.sites import StaticPageSite, static_page_site


def autodiscover():
    """
    Auto-discover registered subclasses of PageLayout living in models.py files
    in any application in settings.INSTALLED_APPS by attempting to import and
    failing silently if need be.
    """
    import copy
    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        try:
            before_import_registry = copy.copy(static_page_site._registry)
            import_module('%s.models' % app)
        except:
            static_page_site._registry = before_import_registry
            if module_has_submodule(mod, 'models'):
                raise


class PageAdmin(admin.ModelAdmin):

    fieldsets = (
        ('Basics', {
            'fields': ('title', 'slug',)
        }),
        ('Publish', {
            'fields': ('status', 'visibility',)
        }),
        ('Attributes', {
            'fields': ('parent',)
        }),
    )
    change_form_template = 'pagemanager/admin/change_form.html'
    prepopulated_fields = {'slug': ('title',)}

    def get_urls(self):
        from django.conf.urls.defaults import *
        urls = super(PageAdmin, self).get_urls()
        more = patterns('',
            (r'^parentsorders/$', self.admin_site.admin_view(self.parents_orders))
        )
        return more + urls

    def parents_orders(self, request):
        if request.method == 'POST':
            for page_id, values in request.POST.iteritems():
                parent, order = values.split(',')
                page = Page.objects.get(pk=int(page_id))
                try:
                    page.parent = Page.objects.get(pk=parent)
                except ValueError:
                    page.parent = None
                page.order = order
                page.save()
            return HttpResponse()
        raise Http404

    def render_change_form(self, request, context, add=False, change=False, \
        form_url='', obj=None):
        """
        Function to render the change_form, used in both the add_view and
        change_view.

        Modified to include a list of all PageLayout subclasses in the context
        of Page's add_view.
        """
        if add:
            context.update({'page_layouts': static_page_site})
        return super(PageAdmin, self).render_change_form(request, context, \
            add, change, form_url, obj)

    def changelist_view(self, request, extra_context=None):
        """
        Redirect the fake Page changelist_view to the real Page changelist_view.
        """
        return HttpResponseRedirect(reverse('admin:index'))

    def change_view(self, request, object_id, extra_context=None):
        """
        The 'change' admin view for this model.

        Modified to redirect to the respective PageLayout object's change_view,
        instead of the Page's. This is necessary as it's impossible to create a
        GenericInlineModelAdmin with a variable model. However, the Page model
        will always be the same, so a relation in the opposite direction is
        safe.
        """
        obj = self.get_object(request, unquote(object_id))
        layout = obj.page_layout
        layout_class_meta = layout.__class__._meta
        return HttpResponseRedirect(reverse('admin:%s_%s_change' % (
            layout_class_meta.app_label,
            layout_class_meta.module_name,
        ), args=[layout.pk]))

    def save_model(self, request, obj, form, change):
        """
        Given a model instance, saves it to the database.

        Modified to create associations between the Page object and the chosen
        PageLayout object on the initial save.
        """

        if not obj.pk:

            # Create new instance of PostLayout subclass
            layout_model = static_page_site.get_by_name(request.POST['layout'])
            layout = layout_model()
            layout.save()

            # Associate PostLayout subclass instance with Page
            obj.layout_type = ContentType.objects.get_for_model(layout_model)
            obj.object_id = layout.pk

        obj.save()