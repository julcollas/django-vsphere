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


Import
-----------

1. You can find an example script to import an hypervisor in "tools".

2. run import

      $ pip install pysphere
      $ python import_hypervisor.py -H hv.example.com -u user1 -d DatacenterX -p mypassword

3. The import script can use password stored in ~/.hypervisor.ini