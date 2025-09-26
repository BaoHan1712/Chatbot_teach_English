from flask import Flask, request, jsonify, render_template_string
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Cấu hình database
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "hoang123@"
DB_NAME = "aichat"

# ----------------- HÀM XỬ LÝ -----------------
def run_query(query):
    """Thực hiện query SQL và trả về kết quả."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)

        if query.strip().lower().startswith("select"):
            result = cursor.fetchall()
        else:
            connection.commit()
            result = f"Thực thi thành công, {cursor.rowcount} hàng bị ảnh hưởng."

        return True, result
    except Error as e:
        return False, str(e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_all_tables_data():
    """Lấy dữ liệu tất cả bảng trong database."""
    success, tables = run_query("SHOW TABLES")
    if not success:
        return []

    all_data = []
    for table in tables:
        table_name = list(table.values())[0]
        success, rows = run_query(f"SELECT * FROM {table_name}")
        if success:
            all_data.append((table_name, rows))
    return all_data

# ----------------- TEMPLATE HTML -----------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Query Interface</title>
<style>
body { font-family: Arial; background:#fff; color:#333; padding:20px;}
h1 { text-align:center; color:#333;}
.query-container { max-width:800px; margin:20px auto; padding:20px; border:1px solid #ddd; border-radius:8px; background:#f9f9f9; }
.query-container input[type="text"] { width:100%; padding:10px; font-size:16px; margin-bottom:10px; border-radius:5px; border:1px solid #ccc; }
.query-container button { padding:10px 20px; background:#007bff; color:white; border:none; border-radius:5px; cursor:pointer; }
.query-container button:hover { background:#0056b3; }
.result { margin-top:20px; padding:10px; border:1px solid #ddd; border-radius:5px; background:#fff; min-height:50px;}
table { border-collapse:collapse; width:100%; margin-top:10px;}
th, td { border:1px solid #ccc; padding:5px; text-align:left;}
th { background:#007bff; color:white;}
tr:nth-child(even){background:#f2f2f2;}
</style>
</head>
<body>
<h1>Query Interface</h1>
<div class="query-container">
    <input type="text" id="queryInput" placeholder="Nhập lệnh SQL...">
    <button onclick="sendQuery()">Gửi</button>
    <button onclick="showAll()">Show toàn bộ database</button>
    <div class="result" id="result">Kết quả sẽ hiển thị ở đây</div>
</div>

<script>
async function sendQuery() {
    const query = document.getElementById('queryInput').value.trim();
    const resultDiv = document.getElementById('result');
    if (!query) { resultDiv.textContent = "❌ Vui lòng nhập lệnh!"; return; }

    try {
        const response = await fetch("/run_query", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ query })
        });
        const data = await response.json();
        if (data.status === "success") {
            displayResult(data.result);
        } else {
            resultDiv.textContent = data.result;
        }
    } catch (err) { resultDiv.textContent = "❌ Lỗi: " + err.message; }
    document.getElementById('queryInput').value = "";
}

async function showAll() {
    const resultDiv = document.getElementById('result');
    try {
        const response = await fetch("/show_all");
        const data = await response.json();
        if (data.status === "success") {
            resultDiv.innerHTML = "";
            data.result.forEach(table => {
                const [name, rows] = table;
                resultDiv.innerHTML += `<h3>Bảng: ${name}</h3>`;
                if(rows.length > 0){
                    const cols = Object.keys(rows[0]);
                    let tableHTML = "<table><thead><tr>";
                    cols.forEach(c => tableHTML += `<th>${c}</th>`);
                    tableHTML += "</tr></thead><tbody>";
                    rows.forEach(r => {
                        tableHTML += "<tr>";
                        cols.forEach(c => tableHTML += `<td>${r[c]}</td>`);
                        tableHTML += "</tr>";
                    });
                    tableHTML += "</tbody></table>";
                    resultDiv.innerHTML += tableHTML;
                } else {
                    resultDiv.innerHTML += "<p>Không có dữ liệu</p>";
                }
            });
        }
    } catch(err){ resultDiv.textContent = "❌ Lỗi: " + err.message; }
}

function displayResult(res){
    const resultDiv = document.getElementById('result');
    if(typeof res === "string"){ resultDiv.textContent = res; return; }
    if(Array.isArray(res) && res.length>0){
        const cols = Object.keys(res[0]);
        let tableHTML = "<table><thead><tr>";
        cols.forEach(c => tableHTML += `<th>${c}</th>`);
        tableHTML += "</tr></thead><tbody>";
        res.forEach(r => { tableHTML += "<tr>"; cols.forEach(c => tableHTML += `<td>${r[c]}</td>`); tableHTML += "</tr>"; });
        tableHTML += "</tbody></table>";
        resultDiv.innerHTML = tableHTML;
    } else { resultDiv.textContent = "❌ Không có kết quả"; }
}
</script>
</body>
</html>
"""

# ----------------- ROUTES -----------------
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/run_query", methods=["POST"])
def api_run_query():
    data = request.get_json()
    query = data.get("query")
    success, result = run_query(query)
    return jsonify({"status": "success" if success else "error", "result": result})

@app.route("/show_all")
def api_show_all():
    all_data = get_all_tables_data()
    return jsonify({"status": "success", "result": all_data})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
