let userState = '';

const escapeHtml = (text) => {
    return $('<div>').text(text || '').html();
};

const userDiv = (senderId, receiverId, name, online) => {
    const isCurrentActive = (typeof sender_id !== 'undefined' && String(sender_id) === String(receiverId));
    const activeStyle = isCurrentActive ? 'background-color: #e3f2fd; border-left: 4px solid #1976d2;' : '';

    return (`<a href="/chat/${senderId}/${receiverId}" id="user${receiverId}" class="collection-item" style="display: flex; align-items: center; padding: 12px 14px; border-bottom: 1px solid #eceff1; text-decoration: none; transition: background 0.2s ease; ${activeStyle}">
        <div style="margin-right: 12px; position: relative; flex-shrink: 0; width: 38px; height: 38px;">
            <div style="width: 38px; height: 38px; border-radius: 50%; background: #bbdefb; color: #0d47a1; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 16px;">
                <i class="material-icons" style="font-size: 22px;">account_circle</i>
            </div>
            <span style="position: absolute; bottom: 0; right: 0; width: 10px; height: 10px; border-radius: 50%; background-color: ${online ? '#4caf50' : '#bdbdbd'}; border: 2px solid #ffffff;"></span>
        </div>
        <div style="flex-grow: 1; min-width: 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="title" style="font-weight: 600; color: #263238; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(name)}</span>
                <span style="font-size: 11px; font-weight: 500; color: ${online ? '#2e7d32' : '#9e9e9e'};">${online ? 'Online' : 'Offline'}</span>
            </div>
        </div>
    </a>`);
};

function scrolltoend() {
    const board = $('#board');
    if (board.length > 0) {
        board.stop().animate({
            scrollTop: board[0].scrollHeight
        }, 400);
    }
}

function send(sender, receiver, message) {
    if (!receiver || receiver.trim() === '') {
        console.warn('No active receiver selected to send message to.');
        return;
    }

    $.ajax({
        url: '/api/messages',
        type: 'POST',
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify({
            sender: sender,
            receiver: receiver,
            message: message
        }),
        success: function (data) {
            $('#no-messages-placeholder').remove();
            const now = new Date();
            const timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
            const safeMsg = escapeHtml(message);

            const box = `<div class="card-panel blue darken-1 white-text right" style="max-width: 75%; min-width: 140px; border-radius: 12px 12px 2px 12px; margin: 8px 0; padding: 10px 14px; position: relative; clear: both; float: right; box-shadow: 0 1px 4px rgba(0,0,0,0.12);">
                <div style="font-size: 11px; opacity: 0.85; margin-bottom: 3px; font-weight: 600;">You</div>
                <div style="font-size: 14px; word-break: break-word;">${safeMsg}</div>
                <div style="font-size: 10px; opacity: 0.75; text-align: right; margin-top: 4px;">${timeStr}</div>
            </div>`;

            $('#board').append(box);
            scrolltoend();
        },
        error: function (xhr, status, error) {
            console.error('Failed to send message:', error, xhr.responseText);
        }
    });
}

function receive() {
    if (typeof sender_id === 'undefined' || typeof receiver_id === 'undefined' || !sender_id || !receiver_id) {
        return;
    }

    $.get('/api/messages/' + sender_id + '/' + receiver_id, function (data) {
        if (data && data.length > 0) {
            $('#no-messages-placeholder').remove();
            for (let i = 0; i < data.length; i++) {
                const item = data[i];
                let timeStr = '';
                if (item.timestamp) {
                    const d = new Date(item.timestamp);
                    timeStr = d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
                }
                const safeSender = escapeHtml(item.sender);
                const safeMsg = escapeHtml(item.message);

                const box = `<div class="card-panel white grey-text text-darken-3 left" style="max-width: 75%; min-width: 140px; border-radius: 12px 12px 12px 2px; margin: 8px 0; padding: 10px 14px; position: relative; clear: both; float: left; border: 1px solid #e0e0e0; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
                    <div style="font-size: 11px; color: #1565c0; margin-bottom: 3px; font-weight: 600;">${safeSender}</div>
                    <div style="font-size: 14px; word-break: break-word;">${safeMsg}</div>
                    <div style="font-size: 10px; color: #9e9e9e; text-align: right; margin-top: 4px;">${timeStr}</div>
                </div>`;

                $('#board').append(box);
                scrolltoend();
            }
        }
    });
}

function getUsers(senderId, callback) {
    return $.get('/api/users', function (data) {
        if (userState !== JSON.stringify(data)) {
            userState = JSON.stringify(data);
            const doc = data.reduce((res, user) => {
                if (user.id === senderId) {
                    return res;
                } else {
                    return [userDiv(senderId, user.id, user.username, user.online), ...res];
                }
            }, []);
            callback(doc);
        }
    });
}

function register(username, password) {
    $.ajax({
        url: '/api/users',
        type: 'POST',
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify({
            username: username,
            password: password
        }),
        success: function (data) {
            window.location = '/';
        },
        error: function (response) {
            $('#id_username').addClass('invalid');
        }
    });
}

