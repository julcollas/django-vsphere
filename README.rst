django-vsphere is an app for `Django <https://www.djangoproject.com/>`_ to have a centralized dashboard for all your VMWare vSphere ESXi.

Dependencies
-----------

- django-tasypie
- python-mimeparse (un-resolved tastypie dependencie)

Quick start
-----------

1. Add "vsphere" to your INSTALLED_APPS setting like this::

      INSTALLED_APPS = (
          ...
          'vsphere',
      )

2. Include the polls URLconf in your project urls.py like this::

      url(r'^', include('vsphere.urls')),

4. Run syncdb to create the vsphere models::

      python manage.py syncdb

5. Start the development server and visit http://127.0.0.1:8000/admin/ ::

      python manage.py runserver

6. Visit http://127.0.0.1:8000/ to display the dashboard.

7. Visit the guest API at http://127.0.0.1:8000/api/guest/?name=vm1
