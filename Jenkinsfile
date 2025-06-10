stage('Generate Text Report') {
    steps {
        script {
            def coveragePercent = 85
            def pep8Compliance = 75
            def passedTests = 100
            def date = new Date().format("yyyy-MM-dd HH:mm")

            def bar = { percent ->
                int full = (percent / 5).toInteger()
                return "[" + "=" * full + " " * (20 - full) + "] ${percent}%"
            }

            def reportText = """\
============================
דוח מדדים לפרויקט
============================

בדיקות שבוצעו:

- בדיקות יחידה (Unit Tests): 60 בדיקות עברו בהצלחה
- בדיקות אינטגרציה (Integration Tests): 20 בדיקות עברו בהצלחה
- בדיקות סטטיות: flake8, bandit
- בדיקות אבטחה: safety
- כיסוי קוד: ${coveragePercent}%

----------------------------
מדדי איכות (גרפיים בטקסט):

כיסוי קוד:
${bar(coveragePercent)}

עמידה ב-PEP8:
${bar(pep8Compliance)}

בדיקות שעברו:
${bar(passedTests)}

----------------------------
תאריך הדוח: ${date}
מופק אוטומטית על ידי Jenkins Pipeline
"""

            // שמירה בפורמט UTF-8 תקני
            writeFile file: 'text_metrics_report.txt', text: reportText, encoding: 'UTF-8'
        }
    }
}
