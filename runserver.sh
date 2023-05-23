sleep 3
django-admin migrate --noinput
django-admin create_task_admin taskadmin d.farre.m@gmail.com
django-admin collectstatic --noinput
django-admin runserver 0.0.0.0:8001
