from django.shortcuts import render
from django.http import JsonResponse
import json
from openai import OpenAI


def chat_view(request):
    return render(request, 'student_chat/chat.html')


def get_response(request):
    if request.method == 'POST':
        try:
            print("התקבלה בקשת POST")
            data = json.loads(request.body)
            user_message = data.get('message', '')
            print(f"הודעת המשתמש: {user_message}")

            # קבלת תשובה מ-ChatGPT
            bot_response = get_openai_response(user_message)
            print(f"תשובת הבוט (התחלה): {bot_response[:50]}...")

            return JsonResponse({
                'response': bot_response
            })
        except Exception as e:
            print(f"שגיאה בטיפול בבקשה: {str(e)}")
            return JsonResponse({
                'response': f"אירעה שגיאה: {str(e)}"
            })
    return JsonResponse({'error': 'שיטה לא נתמכת'}, status=405)


def get_openai_response(message):
    """
    מקבל תשובה ממודל שפה של OpenAI
    """
    try:
        print("מתחבר ל-OpenAI API...")
        # יצירת קליינט OpenAI
        client = OpenAI(
            api_key="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")

        # בניית הפרומפט והקשר עם הגבלות נוקשות
        system_prompt = """
        אתה עוזר וירטואלי באתר בקשות סטודנטים, שמטרתו היחידה היא לספק מידע ועזרה בנושאים הקשורים לבקשות סטודנטים בלבד.

        אתה מוגבל אך ורק לנושאים הבאים:
        1. הגשת ערעור על ציון
        2. בקשה למועד מיוחד
        3. שקלול עבודה בית בציון הסופי
        4. דחיית הגשת עבודה
        5. שחרור מחובת הרשמה
        6. בקשה לפטור מקורס
        7. בקשה לפטור מעבודת הגשה
        8. בקשה לפטור מדרישת קדם
        9. בקשה לחריגה מיוחדת - דיקאנט
        10. מידע על סטטוס בקשות
        11. עזרה בניסוח בקשות אקדמיות
        12. מידע על תהליך הגשת בקשות

        חשוב מאוד: אינך מורשה לענות על שאלות שאינן קשורות לרשימת הנושאים הללו. 
        אם נשאלת שאלה שאינה קשורה לנושאים הללו (כמו מתכונים, תחביבים, חדשות, מזג אוויר, וכדומה):
        1. סרב בנימוס לענות
        2. הסבר שאתה מתמחה רק בנושאי בקשות סטודנטים
        3. הצע לדבר על אחד מהנושאים המותרים ברשימה

        עבור כל אחת מהבקשות המותרות, עליך להסביר:
        1. מהו הנתיב במערכת להגשת הבקשה (איפה צריך ללחוץ)
        2. למי הבקשה מוגשת (מרצה, יועץ, דיקנט וכו')
        3. איזה מסמכים נדרשים לרוב להגשת הבקשה
        4. מהו זמן הטיפול המשוער בבקשה

        כאשר המשתמש בוחר באפשרות "מידע על סטטוס בקשות", עליך להסביר את הנתיב במערכת לצפייה בסטטוס הבקשות.

        כאשר המשתמש בוחר באפשרות "עזרה בניסוח בקשות", עליך לשאול אותו איזה סוג בקשה הוא רוצה לנסח ואז לספק לו תבנית מפורטת לניסוח הבקשה המבוקשת.

        תשובותיך צריכות להיות מפורטות, מקצועיות אך ידידותיות, ולהכיל את כל המידע הדרוש לסטודנט כדי להבין איך להגיש את הבקשה ומה לצפות בהמשך התהליך.

        הערה חשובה: אתה לא יודע את הנתיבים המדויקים במערכת, למי בדיוק מוגשת כל בקשה, או את המסמכים הספציפיים הנדרשים - לכן הצג מידע כללי ומסוגנן שיכול להתאים למערכות בקשות סטודנטים טיפוסיות. הדגש שמדובר במידע כללי וכי הנתיבים המדויקים עשויים להשתנות בהתאם למערכת הספציפית של המוסד האקדמי.
        """

        print("שולח בקשה ל-OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=1000
        )

        print("התקבלה תשובה מ-OpenAI API")
        # החזרת התשובה
        return response.choices[0].message.content
    except Exception as e:
        print(f"שגיאה בחיבור ל-OpenAI: {str(e)}")
        return f"אירעה שגיאה בתקשורת עם מערכת ה-AI. נא לנסות שוב מאוחר יותר. (שגיאה: {str(e)})"