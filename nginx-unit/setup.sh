sleep 3
channel-tasks-admin migrate --noinput
channel-tasks-admin create_task_admin taskadmin d.farre.m@gmail.com
channel-tasks-admin collectstatic --noinput
