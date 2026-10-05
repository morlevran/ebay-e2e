eBay E2E Automation – Playwright + Python

אוטומציית End-to-End לאתר eBay: התחברות, חיפוש פריטים מתחת למחיר מקסימלי, הוספה אקראית לסל ובדיקה שסכום הסל לא חורג מהתקציב.

מה נבדק (ארבע הפונקציות)
פונקציה	מחלקה	תיאור
login()	ShoppingFlow	התחברות עם EBAY_USER / EBAY_PASS. אם לא הוגדרו – ממשיכים כאורח (ראו הנחות)
search_items_by_name_under_price(query, max_price, limit)	ShoppingFlow	חיפוש, סינון מחיר (_udhi), מעבר בין עמודים, איסוף עד limit כתובות פריטים. הכרטיסים נאספים ב-XPath
add_items_to_cart(urls)	ShoppingFlow	כניסה לכל פריט, בחירה אקראית של וריאנטים (מידה/צבע וכו'), הוספה לסל וצילום מסך לכל פריט שנוסף
assert_cart_total_not_exceeds(budget_per_item, items_count)	ShoppingFlow	בדיקה שסכום הסל ≤ budget_per_item × items_count וצילום מסך של הסל
מבנה הפרויקט
ebay-e2e/
├── config/        # הגדרות (כתובות, timeouts, תיקיות פלט)
├── data/          # scenarios.json – נתוני הבדיקות (data-driven)
├── pages/         # Page Objects: BasePage, HomePage, SearchResultsPage, ItemPage, CartPage
├── flows/         # ShoppingFlow – מתזמר את ארבע הפונקציות מעל ה-Pages
├── utils/         # עזרים (טעינת JSON, פרסור מחירים)
├── tests/         # test_e2e_cart.py
├── reports/       # junit.xml, report.html (נוצרים בכל ריצה)
├── artifacts/     # צילומי מסך, traces (נוצרים בכל ריצה)
└── run_report/    # דוגמת דוח מריצה מוצלחת (נשמרת בגיט)
ארכיטקטורה
POM + OOP: כל עמוד הוא מחלקה שיורשת מ-BasePage. הלוקייטורים והפעולות על העמוד נמצאים רק ב-Page, והבדיקות לא מכירות selectors.
Flow: ShoppingFlow מחבר בין העמודים ומממש את הפונקציות הנדרשות. הבדיקה קוראת רק ל-Flow.
Data-driven: התרחישים ב-data/scenarios.json, והבדיקה מורצת עם pytest.mark.parametrize על כל תרחיש. להוספת תרחיש מוסיפים אובייקט ל-JSON, בלי לגעת בקוד.
json
{ "name": "shoes_under_220", "query": "shoes", "max_price": 220, "limit": 5 }
התקנה והרצה

דרישות: Python 3.10 ומעלה.

bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

הרצה (מומלץ עם דפדפן גלוי, ראו הערה בהמשך):

bash
pytest tests/test_e2e_cart.py --headed

התחברות עם משתמש אמיתי (אופציונלי):

bash
export EBAY_USER="your_user"
export EBAY_PASS="your_password"

הרצת תרחיש בודד: pytest tests/test_e2e_cart.py --headed -k backpack

דוחות

הריצה מייצרת אוטומטית (מוגדר ב-pytest.ini):

reports/junit.xml – JUnit XML
reports/report.html – דוח HTML עצמאי (pytest-html)
artifacts/ – צילום מסך לכל פריט שנוסף, צילום מסך של הסל (cart_page), וצילום add_failed_<id> לכל פריט שלא ניתן היה להוסיף
תוצאות Allure (allure-results) נוצרות גם הן; להצגה נדרש Allure CLI מותקן (allure serve allure-results)

דוגמת דוח מריצה מוצלחת נמצאת בתיקייה run_report/.

הנחות ומגבלות
התחברות / אורח: לא נעשה שימוש בחשבון אמיתי כברירת מחדל. eBay חוסמת התחברות אוטומטית (CAPTCHA ואימות נוסף), לכן ללא EBAY_USER/EBAY_PASS הבדיקה ממשיכה כאורח. הפונקציה login() מוכנה להתחברות כשמוגדרים פרטי משתמש.
מטבע: האתר מציג מחירים במטבע לפי המיקום (₪ בסביבת ההרצה). הסף והתקציב מושווים במטבע שהאתר מציג, ללא המרת מטבע.
סכום הסל: ה-Subtotal של eBay כולל משלוח, ולכן לא משמש להשוואה. הבדיקה משווה את שורת Items (N) (סכום הפריטים בלבד) ל-budget_per_item × N. ניתן להשוות לפי Subtotal עם include_shipping=True.
N הוא מספר הפריטים שנוספו בפועל: פריט שלא ניתן להוסיף (למשל וריאנט שלא נבחר, או פריט שאזל) מדולג, מתועד באזהרה ובצילום מסך, והסף מחושב לפי מה שנוסף. אם לא נוסף אף פריט – הבדיקה נכשלת.
בחירת וריאנטים: מנגנון best-effort. תפריטי select רגילים נתמכים, ותפריטים מותאמים (listbox) נתמכים ברמת ניסיון. מבנה העמוד של eBay משתנה בין פריטים.
חוסר יציבות של eBay: האתר מחזיר לסירוגין "Error Page | eBay" או מפנה לדף הבית. הקוד מזהה זאת, מנסה שוב עד 3 פעמים עם המתנה גדלה, ובמקרה כשל חוזר טוען ישירות את כתובת התוצאות. אם עדיין אין תוצאות נרשם צילום מסך results_unavailable.
הרצה עם --headed: מומלץ, כי ב-headless eBay מזהה אוטומציה בתדירות גבוהה יותר.
פריט placeholder: כרטיס נסתר עם הכתובת /itm/123456 מוחרג מהאיסוף.
אקראיות: בחירת הווריאנטים אקראית. ניתן לקבע seed ב-config לשחזור ריצה.
פתרון תקלות מהיר
0 תוצאות / דף שגיאה: להריץ שוב עם --headed, ולוודא חיבור יציב. זו בעיה בצד האתר ולא בקוד.
python: command not found: להשתמש ב-python3.
TargetClosedError: אין לסגור את חלון הדפדפן בזמן ריצה.