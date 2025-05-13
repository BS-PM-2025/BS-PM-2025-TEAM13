// פונקציה שתרוץ כאשר הדף נטען במלואו
document.addEventListener('DOMContentLoaded', function() {
    // יצירת הוידג'ט והוספתו לדף
    createChatWidget();
});

function createChatWidget() {
    // יצירת הכפתור הצף
    const chatButton = document.createElement('div');
    chatButton.className = 'chat-widget-button';
    chatButton.innerHTML = '<span class="chat-widget-icon">💬</span>';
    document.body.appendChild(chatButton);

    // יצירת מיכל הצ'אט
    const chatContainer = document.createElement('div');
    chatContainer.className = 'chat-widget-container';
    chatContainer.id = 'chat-widget';
    chatContainer.innerHTML = `
        <div class="chat-widget-header">
            <h3 class="chat-widget-title">עוזר וירטואלי לבקשות סטודנטים</h3>
            <span class="chat-widget-close">&times;</span>
        </div>
        <div class="chat-widget-body" id="chat-widget-body">
            <div class="chat-widget-message chat-widget-bot">
                שלום! אני העוזר הווירטואלי של מערכת בקשות הסטודנטים. איך אוכל לעזור לך היום?
                
                <div class="options-container">
                    <button class="option-button" onclick="selectWidgetOption('הגשת ערעור על ציון')">הגשת ערעור על ציון</button>
                    <button class="option-button" onclick="selectWidgetOption('בקשה למועד מיוחד')">בקשה למועד מיוחד</button>
                    <button class="option-button" onclick="selectWidgetOption('שקלול עבודה בית בציון הסופי')">שקלול עבודה בית בציון הסופי</button>
                    <button class="option-button" onclick="selectWidgetOption('דחיית הגשת עבודה')">דחיית הגשת עבודה</button>
                    <button class="option-button" onclick="selectWidgetOption('שחרור מחובת הרשמה')">שחרור מחובת הרשמה</button>
                    <button class="option-button" onclick="selectWidgetOption('בקשה לפטור מקורס')">בקשה לפטור מקורס</button>
                    <button class="option-button" onclick="selectWidgetOption('ערעור על ציון')">ערעור על ציון</button>
                    <button class="option-button" onclick="selectWidgetOption('בקשה לפטור מעבודת הגשה')">בקשה לפטור מעבודת הגשה</button>
                    <button class="option-button" onclick="selectWidgetOption('בקשה לפטור מדרישת קדם')">בקשה לפטור מדרישת קדם</button>
                    <button class="option-button" onclick="selectWidgetOption('בקשה לחריגה מיוחדת - דיקאנט')">בקשה לחריגה מיוחדת - דיקאנט</button>
                    <button class="option-button" onclick="selectWidgetOption('מידע על סטטוס בקשות')">מידע על סטטוס בקשות</button>
                    <button class="option-button" onclick="selectWidgetOption('עזרה בניסוח בקשות')">עזרה בניסוח בקשות</button>
                    <button class="option-button" onclick="selectWidgetOption('מידע על תהליך הגשת בקשות')">מידע על תהליך הגשת בקשות</button>
                </div>
            </div>
        </div>
        <div class="chat-widget-input">
            <input type="text" id="chat-widget-input" placeholder="הקלד את שאלתך כאן...">
            <button id="chat-widget-send">שלח</button>
        </div>
    `;
    document.body.appendChild(chatContainer);

    // הוספת אירועים לכפתורים
    chatButton.addEventListener('click', function() {
        chatContainer.classList.toggle('open');
    });

    const closeButton = document.querySelector('.chat-widget-close');
    closeButton.addEventListener('click', function() {
        chatContainer.classList.remove('open');
    });

    const sendButton = document.getElementById('chat-widget-send');
    const chatInput = document.getElementById('chat-widget-input');

    sendButton.addEventListener('click', function() {
        sendWidgetMessage();
    });

    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendWidgetMessage();
        }
    });
}

function sendWidgetMessage() {
    const chatInput = document.getElementById('chat-widget-input');
    const message = chatInput.value.trim();

    if (message === '') return;

    // הוספת הודעת המשתמש לצ'אט
    addWidgetMessage(message, 'user');

    // ניקוי תיבת הקלט
    chatInput.value = '';

    // הצגת "חושב..."
    const thinkingId = addWidgetMessage("חושב...", 'bot', 'thinking-message');

    // שליחת הבקשה לשרת
    fetch('/chat-response/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'message': message
        })
    })
    .then(response => response.json())
    .then(data => {
        // הסרת הודעת "חושב..."
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) {
            thinkingElement.remove();
        }

        // הוספת תשובת הבוט
        let responseText = data.response || "אירעה שגיאה. אנא נסה שוב.";
        addWidgetMessage(responseText, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);

        // הסרת הודעת "חושב..."
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) {
            thinkingElement.remove();
        }

        // הוספת הודעת שגיאה
        addWidgetMessage("אירעה שגיאה בתקשורת. נא לנסות שוב.", 'bot');
    });
}

function selectWidgetOption(option) {
    // הוספת האפשרות שנבחרה כהודעת משתמש
    addWidgetMessage(option, 'user');

    // הצגת "חושב..."
    const thinkingId = addWidgetMessage("חושב...", 'bot', 'thinking-message');

    // טיפול באפשרות "עזרה בניסוח בקשות" באופן מיוחד
    if (option === 'עזרה בניסוח בקשות') {
        // הסרת הודעת "חושב..."
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) {
            thinkingElement.remove();
        }

        // הצגת אפשרויות ניסוח
        const response = `באיזה סוג של בקשה אתה צריך עזרה בניסוח?
        <div class="options-container">
            <button class="option-button" onclick="selectWidgetOption('ניסוח ערעור על ציון')">ערעור על ציון</button>
            <button class="option-button" onclick="selectWidgetOption('ניסוח בקשה להארכת זמן')">בקשה להארכת זמן</button>
            <button class="option-button" onclick="selectWidgetOption('ניסוח בקשה לקבלת מלגה')">בקשה לקבלת מלגה</button>
        </div>`;

        addWidgetMessage(response, 'bot');
        return;
    }

    // שליחת הבקשה לשרת
    fetch('/student_chat/get-response/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'message': option
        })
    })
    .then(response => response.json())
    .then(data => {
        // הסרת הודעת "חושב..."
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) {
            thinkingElement.remove();
        }

        // הוספת תשובת הבוט
        let responseText = data.response || "אירעה שגיאה. אנא נסה שוב.";
        addWidgetMessage(responseText, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);

        // הסרת הודעת "חושב..."
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) {
            thinkingElement.remove();
        }

        // הוספת הודעת שגיאה
        addWidgetMessage("אירעה שגיאה בתקשורת. נא לנסות שוב.", 'bot');
    });
}

function addWidgetMessage(message, sender, id = null) {
    const chatBody = document.getElementById('chat-widget-body');
    const messageElement = document.createElement('div');
    messageElement.className = `chat-widget-message chat-widget-${sender}`;

    if (id) {
        messageElement.id = id;
    } else {
        // יצירת מזהה ייחודי לכל הודעה
        messageElement.id = 'msg-' + Date.now();
    }

    // בדיקה אם ההודעה היא מחרוזת ויש צורך להחליף ירידות שורה
    if (typeof message === 'string') {
        messageElement.innerHTML = message.replace(/\n/g, '<br>');
    } else {
        messageElement.textContent = message;
    }

    chatBody.appendChild(messageElement);

    // גלילה לתחתית הצ'אט
    chatBody.scrollTop = chatBody.scrollHeight;

    return messageElement.id;
}

// פונקציית עזר לקבלת ערך העוגייה
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}