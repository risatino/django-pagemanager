from django.db import models
from django.utils import unittest

import pagemanager
from pagemanager.exceptions import AlreadyRegistered, NotRegistered
from pagemanager.models import PageLayout


class HomepageLayout(PageLayout):
    name = 'Homepage'
    thumbnail = 'pagemanager/homepage.jpg'
    template_file = 'pagemanager/homepage.html'
    context = {'foo': 'bar'}
    components = ['blog', 'news']
    body = models.TextField()


class ListingPageLayout(PageLayout):
    name = 'Landing Page'
    base = 'listing'

    def get_thumbnail(self, instance=None):
        return '%s.jpg' % self.base

    def get_template_file(self, instance=None):
        return '%s.html' % self.base

    def get_context_data(self, instance=None):
        return {'foo': '%s' % self.base}

    def get_components(self, instance=None):
        return [self.base]


class PageManagerSiteTest(unittest.TestCase):
    def setUp(self):
        self.site = pagemanager.sites.PageManagerSite()

    def test_initilization(self):
        self.assertTrue(self.site._registry == [])

    def test_dependency_check(self):
        self.site.check_dependencies()
        self.assertTrue(True)


class PageLayoutModelTest(unittest.TestCase):
    def setUp(self):
        self.page_layout_instance = PageLayout()
        self.test_layout = HomepageLayout
        self.test_layout_instance = self.test_layout()
        self.test_layout_instance_get = ListingPageLayout()

    def test_initialization(self):
        self.assertTrue(isinstance(
            pagemanager.pagemanager_site,
            pagemanager.sites.PageManagerSite
        ))

    def test_get_thumbnail(self):
        self.assertTrue(self.page_layout_instance.get_thumbnail() == None)
        self.assertTrue(self.test_layout_instance.get_thumbnail() == \
            'pagemanager/homepage.jpg')
        self.assertTrue(self.test_layout_instance_get.get_thumbnail() == \
            'listing.jpg')

    def test_get_template_file(self):
        self.assertTrue(self.page_layout_instance.get_template_file() == None)
        self.assertTrue(self.test_layout_instance.get_template_file() == \
            'pagemanager/homepage.html')
        self.assertTrue(self.test_layout_instance_get.get_template_file() == \
            'listing.html')

    def test_get_context_data(self):
        self.assertTrue(self.page_layout_instance.get_context_data() == None)
        self.assertTrue(self.test_layout_instance.get_context_data() == \
            {'foo': 'bar'})
        self.assertTrue(self.test_layout_instance_get.get_context_data() == \
            {'foo': 'listing'})

    def test_get_components(self):
        self.assertTrue(self.page_layout_instance.get_components() == None)
        self.assertTrue(self.test_layout_instance.get_components() == \
            ['blog', 'news'])
        self.assertTrue(self.test_layout_instance_get.get_components() == \
            ['listing'])


class RegistrationTest(unittest.TestCase):
    def setUp(self):
        self.site = pagemanager.sites.PageManagerSite()
        self.test_layout = HomepageLayout

    def test_registration(self):
        self.site.register(self.test_layout)
        self.assertTrue(self.test_layout in self.site._registry)

    def test_unregistration(self):
        self.site.register(self.test_layout)
        self.site.unregister(self.test_layout)
        self.assertFalse(self.test_layout in self.site._registry)

    def test_prevent_reregistration(self):
        self.site.register(self.test_layout)
        self.assertRaises(
            pagemanager.sites.AlreadyRegistered,
            self.site.register,
            self.test_layout
        )

    def test_prevent_abstract_registration(self):
        self.assertRaises(
            pagemanager.sites.ImproperlyConfigured,
            self.site.register,
            PageLayout
        )

    def test_prevent_unregistration_of_unregistered(self):
        self.assertRaises(
            pagemanager.sites.NotRegistered,
            self.site.unregister,
            self.test_layout
        )