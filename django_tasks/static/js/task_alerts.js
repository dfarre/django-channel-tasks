function getAlertData() {
    sessionStorage.getItem('alerts') || sessionStorage.setItem('alerts', '{}');
    const session_alerts = JSON.parse(sessionStorage.getItem('alerts'));
    var cached_alerts = JSON.parse(document.getElementById('cached_alerts').textContent);
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
}

function formatTimestamp(timestamp) {
    var today = new Date(timestamp * 1000);
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var yyyy = today.getFullYear();
    var hh = String(today.getHours()).padStart(2, '0');
    var minutes = String(today.getMinutes()).padStart(2, '0');
    var secs = String(today.getSeconds()).padStart(2, '0');
    return `${yyyy}/${mm}/${dd} ${hh}:${minutes}:${secs}`
};

// WebSocket bound methods
function dismissAlerts(taskID) {
    if (this.readyState === WebSocket.OPEN) {
        this.send(JSON.stringify({'task_id': taskID}));
    } else {
        console.warn('Coud not open websocket in order to clear backend-cached alerts:', this);
    }
    dropAlerts(taskID);
}

function addTaskAlert(alertData) {
    var alert_group = document.getElementById(alertData.task_id);

    if (!alert_group) {
        var alert_group = document.getElementById('alert-group-template').cloneNode(true).firstElementChild;
        alert_group.setAttribute('id', alertData.task_id);
        alert_group.addEventListener('closed.bs.alert', () => this.dismissAlerts(alertData.task_id));
        alert_group.getElementsByClassName('task-name')[0].innerHTML = `${alertData.detail.registered_task}_${alertData.task_id}`;
        alertData.detail['registered_task'];
        document.getElementById('task-alerts-display').appendChild(alert_group);
    }

    var msg_type = alertData.detail.status.toLowerCase();
    var alert = document.getElementById(`${msg_type}-alert-template`).cloneNode(true).firstElementChild;

    if (msg_type == 'success') {
        alert.getElementsByTagName('code')[0].innerHTML = alertData.detail.output;
    }
    if (msg_type == 'error') {
        alert.getElementsByTagName('pre')[0].innerHTML = alertData.detail['exception-repr'];
    }

    alert_group.getElementsByClassName('task-alerts')[0].appendChild(alert);
};

function showTaskAlerts() {
    for (const taskAlerts of Object.values(getAlertData())) {
        taskAlerts.forEach((alertData) => this.addTaskAlert(alertData));
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
    const socket_port = JSON.parse(document.getElementById('socket_port').textContent);
    const socket_uri = JSON.parse(document.getElementById('socket_uri').textContent);
    const ws = new WebSocket(
        `${(location.protocol === 'https:') ? 'wss' : 'ws'}://${window.location.hostname}:${socket_port}${socket_uri}`
    );
    ws.onopen = wsOnOpen; wsOnOpen.bind(ws);
    ws.onclose = wsOnClose; wsOnClose.bind(ws);
    ws.onerror = wsOnError; wsOnError.bind(ws);
    ws.onmessage = wsOnMessage; wsOnMessage.bind(ws);
    ws.addTaskAlert = addTaskAlert; addTaskAlert.bind(ws);
    ws.isTaskStatusMessage = isTaskStatusMessage; isTaskStatusMessage.bind(ws);
    ws.dismissAlerts = dismissAlerts; dismissAlerts.bind(ws);
    ws.showTaskAlerts = showTaskAlerts; showTaskAlerts.bind(ws);
    return ws
};
