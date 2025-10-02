(function($) {
    function getAlertData() {
        sessionStorage.getItem('alerts') || sessionStorage.setItem('alerts', '{}');
        const session_alerts = JSON.parse(sessionStorage.getItem('alerts'));
        var cached_alerts = JSON.parse($('#cached_alerts').text());
        return {...cached_alerts, ...session_alerts}
    }

    function pushAlert(alertData) {
        const alerts = getAlertData();
        if (!alerts.hasOwnProperty(alertData.task_id)) { alerts[alertData.task_id] = []; }
        alerts[alertData.task_id].push(alertData);
        sessionStorage.setItem('alerts', JSON.stringify(alerts));
    }

    function dropAlerts(taskID) {
        const alerts = getAlertData();
        delete alerts[taskID];
        sessionStorage.setItem('alerts', JSON.stringify(alerts));
        if (Object.keys(alerts).length === 0) {
            $('#socket-notifications-module').attr('hidden', true);
        }
    }

    // WebSocket bound, mixed-in methods
    function dismissAlerts(taskID) {
        if (this.readyState === WebSocket.OPEN) {
            this.send(JSON.stringify({'task_id': taskID}));
        } else {
            console.warn('Coud not open websocket in order to clear backend-cached alerts:', this);
        }
        dropAlerts(taskID);
    }

    function dismissAllAlerts() {
        console.log('Dismissing all alerts:', this);
        if (this.readyState === WebSocket.OPEN) {
            this.send(JSON.stringify({'task_id': null}));
        } else {
            console.warn('Coud not open websocket in order to clear backend-cached alerts:', this);
        }
        sessionStorage.setItem('alerts', '{}');
    }

    function createAlertGroup(alertData) {
        const alert_group = $('#alert-group-template').find('div').first().clone();
        alert_group.attr('id', alertData.task_id);
        alert_group.find('div.alert').on('closed.bs.alert', () => this.dismissAlerts(alertData.task_id));
        alert_group.find('span.task-name').html(`${alertData.detail.registered_task}_${alertData.task_id}`);
        return alert_group;
    }

    function createAlert(alertData) {
        const msg_type = alertData.detail.status.toLowerCase();
        const alert = $(`#${msg_type}-alert-template`).find('div').first().clone();
        if (msg_type == 'success') {
            alert.find('code').html(alertData.detail.output);
        }
        if (msg_type == 'error') {
            alert.find('pre').html(alertData.detail['exception-repr']);
        }
        return alert;
    }

    function addTaskAlerts(alertsData) {
        alert_group = this.createAlertGroup(alertsData[0]);

        for (const alertData of alertsData) {
            const alert = this.createAlert(alertData);
            alert_group.find('div.task-alerts').first().append(alert);
        }

        $('#socket-notifications-module').find('#task-alert-groups').append(alert_group);
    }

    function showTaskAlerts() {
        const notifications_module = $('#socket-notifications-module');
        notifications_module.find('#task-alert-groups').find('div.alert').remove();

        let alert_group_count = 0;
        for (const taskAlertGroup of Object.values(getAlertData())) {
            this.addTaskAlerts(taskAlertGroup);
            alert_group_count++;
        }
        if (alert_group_count > 0) {
            notifications_module.attr('hidden', false);
            notifications_module.find('.alert').first().on('closed.bs.alert', () => this.dismissAllAlerts());
        }
    }

    function wsOnOpen(event) {
        console.log('WebSocket connection opened:', event);
        this.showTaskAlerts();
    };

    function wsOnClose(event) {
        console.log('WebSocket connection closed:', event);
    };

    function wsOnError(event) {
        console.error('WebSocket error:', event);
    };

    function wsOnMessage(msg_event) {
        console.log('WebSocket message received:', msg_event.data);
        const parsed_data = JSON.parse(msg_event.data);
        if (this.isTaskStatusMessage(parsed_data)) { pushAlert(parsed_data.content); }
        this.showTaskAlerts();
    };

    function isTaskStatusMessage(parsed_data) {
        return (parsed_data.type && [
            'task.started', 'task.success', 'task.error', 'task.cancelled'
        ].indexOf(parsed_data.type) >= 0)
    };

    // Overriden WebSocket instance factory
    function newChannelTasksWebSocket() {
        const socket_port = JSON.parse($('#socket_port').text())
        const socket_uri = JSON.parse($('#socket_uri').text())
        const ws = new WebSocket(
            `${(location.protocol === 'https:') ? 'wss' : 'ws'}://${window.location.hostname}:${socket_port}${socket_uri}`
        );
        ws.onopen = wsOnOpen; wsOnOpen.bind(ws);
        ws.onclose = wsOnClose; wsOnClose.bind(ws);
        ws.onerror = wsOnError; wsOnError.bind(ws);
        ws.onmessage = wsOnMessage; wsOnMessage.bind(ws);
        ws.addTaskAlerts = addTaskAlerts; addTaskAlerts.bind(ws);
        ws.createAlertGroup = createAlertGroup; createAlertGroup.bind(ws);
        ws.createAlert = createAlert; createAlert.bind(ws);
        ws.isTaskStatusMessage = isTaskStatusMessage; isTaskStatusMessage.bind(ws);
        ws.dismissAlerts = dismissAlerts; dismissAlerts.bind(ws);
        ws.dismissAllAlerts = dismissAllAlerts; dismissAllAlerts.bind(ws);
        ws.showTaskAlerts = showTaskAlerts; showTaskAlerts.bind(ws);
        return ws
    };

    $(document).ready(function () {
        const authenticated = $('#user_is_authenticated')
        if (authenticated.length > 0 && JSON.parse(authenticated.first().text()) === true) {
            var websocket = websocket || newChannelTasksWebSocket();
        }
    });

})(jQuery);
