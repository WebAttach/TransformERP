from flask import Flask, request, render_template_string
import os
import pdfplumber
import json

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
STATIC_UPLOADS = "static/uploads"
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>ERP Console</title>
<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/simple-datatables@latest/dist/style.css\">
<script src=\"https://cdn.jsdelivr.net/npm/simple-datatables@latest\" defer></script>
<link rel=\"stylesheet\" href=\"https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css\">
<link rel=\"stylesheet\" href=\"https://cdn.datatables.net/buttons/2.4.1/css/buttons.dataTables.min.css\">
<script src=\"https://code.jquery.com/jquery-3.7.1.min.js\"></script>
<script src=\"https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js\"></script>
<script src=\"https://cdn.datatables.net/buttons/2.4.1/js/dataTables.buttons.min.js\"></script>
<script src=\"https://cdn.datatables.net/buttons/2.4.1/js/buttons.html5.min.js\"></script>
<script src=\"https://cdn.datatables.net/buttons/2.4.1/js/buttons.print.min.js\"></script>
<script src=\"https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js\"></script>
<script src=\"https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/pdfmake.min.js\"></script>
<script src=\"https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/vfs_fonts.js\"></script>
<style>
body { font-family: sans-serif; background: #f4f6f8; margin: 0; }
.top-bar, .bottom-bar {
  background: #4f6273; color: white; padding: 12px; text-align: center; position: fixed; width: 100%; z-index: 1000;
}
.top-bar { top: 0; } .bottom-bar { bottom: 0; background: #4f6273; }
.main { padding: 120px 20px 60px; max-width: 1000px; margin: auto; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
.card {
  background: #4f6273; color: white; border-radius: 10px; padding: 20px; text-align: center; font-size: 22px;
  font-weight: 500; cursor: pointer; transition: 0.2s; border: 3px solid transparent; position: relative;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.card:hover { transform: scale(1.03); }
.card.selected { border: 3px solid white; box-shadow: 0 0 12px rgba(255,255,255,0.7); }
.card.selected::after {
  content: \"✓\"; position: absolute; top: 10px; right: 12px; font-size: 22px; font-weight: bold; color: orange;
}
.proceed-button {
  margin: 20px auto; display: block; padding: 12px 24px; font-size: 16px;
  background: #1c2733; color: white; border: none; border-radius: 8px; cursor: pointer;
}
.result-box { background: white; padding: 20px; border-radius: 10px; margin-top: 20px; }
</style>
<script>
let modalShownAt = null;

function selectCard(id) {
  document.querySelectorAll('.card').forEach(el => el.classList.remove('selected'));
  document.getElementById(id).classList.add('selected');
  document.getElementById('selected_folder').value = id;
}

function runWithProgress(form) {
  const modal = document.getElementById('progressModal');
  const details = document.getElementById('progressDetails');
  modal.style.display = 'block';
  modalShownAt = Date.now();
  details.innerHTML = "Scanning and processing files";

  setTimeout(() => {
    form.submit();
  }, 2000);
}

window.addEventListener('load', () => {
  const modal = document.getElementById('progressModal');
  if (modal) {
    const now = Date.now();
    const elapsed = now - (modalShownAt || now);
    const remaining = Math.max(2000, 2000 - elapsed);
    setTimeout(() => {
      modal.style.display = 'none';
    }, remaining);
  }
});
</script>
<script>

function openPlan(){
  const url = "https://docs.google.com/spreadsheets/d/1WGJFgJrhoyBrMENQhIB6U6BUZ1ukj_tq5FzEzULs6AI/edit?usp=sharing";
  const width = 1000;
  const height = 600;
  const left = (screen.width - width) / 2;
  const top = (screen.height - height) / 3;
  window.open(url, "_blank", `width=${width},height=${height},top=${top},left=${left},resizable=yes`);
}

function openSlides() {
  const url = "https://docs.google.com/presentation/d/e/2PACX-1vR_ZDbltFP3g0lop4lYwBGpRgfL93NJaN85PP2LN4K5KG6nzfGqOVVbpHg-zYh2ajDsrfbehSZ9ySXY/pub?start=false&loop=true&delayms=10000";
  const width = 1000;
  const height = 600;
  const left = (screen.width - width) / 2;
  const top = (screen.height - height) / 3;
  window.open(url, "_blank", `width=${width},height=${height},top=${top},left=${left},resizable=yes`);
}
</script>
</head><body>
<div class='top-bar' onclick="openSlides()">ERP Transformation Console</div>
<div class='main'>
  <form method='POST' onsubmit="event.preventDefault(); runWithProgress(this);">
    <input type='hidden' name='selected_folder' id='selected_folder'>
        <div class='card-grid' id="panelGrid">
          {% for btn in buttons %}
          <div class='card panel-card' id="{{ btn }}" onclick="selectCard('{{ btn }}')"
               style="{% if loop.index > 4 %}display:none;{% endif %}">
            {{ btn }}<br>📁 {{ counts[btn] }} 
          </div>
          {% endfor %}
        </div>
    <label><input type="checkbox" name="show_curation" {% if show_curation %}checked{% endif %}>Solve</label>&nbsp;|&nbsp;<span onclick="togglePanels(this)">Expand</span>&nbsp;|&nbsp;<span onclick="openPlan()">Plan</span>
    <button class='proceed-button' type='submit'>Proceed</button>
  </form>

  <div id="progressModal" style="display:none; position:fixed;top:30%;left:50%;transform:translateX(-50%);background:white;padding:30px;border-radius:10px;box-shadow:0 8px 18px rgba(0,0,0,0.2);text-align:center;z-index:2000;width:400px;">
    <h3>Processing Files...</h3>
    <div id="progressDetails" style="margin-top:12px; text-align:left; font-size:14px; color:#444;"></div>
  </div>

  {% if not show_curation and final_output %}
  <div class='result-box'>
   
    <h3>Final Output</h3>
    {% for row in final_output %}
      {% if row.type == 'html' %}
        {{ row.content | safe }}
      {% else %}
      <table id="finalTable">
        <thead><tr><th>Type</th><th>Content</th></tr></thead>
        <tbody>
          <tr>
            <td>{{ row.type }}</td>
            <td>
              {% if row.type == 'image' %}
                <img src="/static/uploads/{{ selected_folder }}/{{ row.content }}" style="max-height:80px;">
              {% else %}
                <pre style="white-space:pre-wrap;">{{ row.content }}</pre>
              {% endif %}
            </td>
          </tr>
        </tbody>
      </table>
      {% endif %}
    {% endfor %}
  </div>
  {% endif %}

  {% if show_curation %}
    {% if extracted_text %}
    <div class='result-box'>
      <h3>Extracted Text{% if "CDD" in selected_folder.upper() %} (Filtered for C0 rows){% endif %}</h3>
      <textarea style="width:100%; height:300px; font-family:monospace; font-size:14px;">{{ extracted_text }}</textarea>
    </div>
    {% endif %}

    {% if json_outputs %}
    <div class='result-box'>
      <h3>JSON Files</h3>
      {% for fname, content in json_outputs %}
      <h4>{{ fname }}</h4>
      <pre style="background:#eee; padding:12px; border-radius:8px; white-space:pre-wrap;">{{ content }}</pre>
      {% endfor %}
    </div>
    {% endif %}

    {% if image_paths %}
    <div class='result-box'>
      <h3>Images</h3>
      {% for img in image_paths %}
        <div style="margin:10px 0;">
          <p>{{ img }}</p>
          <img src="/static/uploads/{{ selected_folder }}/{{ img }}" style="max-width:100%; border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,0.1);">
        </div>
      {% endfor %}
    </div>
    {% endif %}
  {% endif %}
</div>
<div class='bottom-bar'>McElroy Technology &nbsp;|&nbsp; (530) 591-3052</div>
<script>
document.addEventListener("DOMContentLoaded", function () {
  $('table.display').DataTable({
    dom: 'Bfrtip',
    buttons: ['copy', 'csv', 'excel', 'pdf', 'print'],
    pageLength: 10,
    responsive: true
  });
});
</script>
<script>
function openFinalOutput() {
  const outputBox = document.querySelector('.result-box');
  const win = window.open('', '_blank');
  win.document.write(`<html><head><title>Final Output</title></head><body>${outputBox.innerHTML}</body></html>`);
  win.document.close();
}
</script>
<script>
let panelsExpanded = false;

function togglePanels(button) {
  const cards = document.querySelectorAll('.panel-card');
  panelsExpanded = !panelsExpanded;

  cards.forEach((card, index) => {
    if (panelsExpanded || index < 4) {
      card.style.display = 'block';
    } else {
      card.style.display = 'none';
    }
  });

  button.textContent = panelsExpanded ? 'Collapse' : 'Expand';
}
</script>
</body></html>
"""

def gather_folder_content(folder):
    full_text = []
    json_outputs = []
    image_paths = []
    final_output = []


    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        if file.lower().endswith(".pdf"):
            try:
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text.append(f"\n--- {file} | Page {page.page_number} ---\n{text}")
                            final_output.append({"type": "text", "content": text})
            except Exception as e:
                full_text.append(f"[Error reading {file}]: {e}")
                final_output.append({"type": "text", "content": f"[Error reading {file}]: {e}"})
        elif file.lower().endswith(".json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pretty = json.dumps(data, indent=2)
                    json_outputs.append((file, pretty))
                    final_output.append({"type": "text", "content": pretty})
            except Exception as e:
                json_outputs.append((file, f"[Error reading {file}]: {e}"))
                final_output.append({"type": "text", "content": f"[Error reading {file}]: {e}"})
        elif file.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            image_paths.append(file)
            final_output.append({"type": "image", "content": file})
        elif file.lower().endswith((".html")):
             sample_html = """
             <table class='display'>
              <thead><tr><th>Client ID</th><th>Name</th><th>Region</th><th>Outstanding Balance</th></tr></thead>
              <tbody>
                <tr><td>C00001</td><td>Veronica Cobos</td><td>California</td><td>$6,240.00</td></tr>
                <tr><td>C00002</td><td>Jorge Velazco</td><td>Texas</td><td>$300.00</td></tr>
                <tr><td>C00003</td><td>Kubota Tractor</td><td>Nevada</td><td>$2,453,929.22</td></tr>
              </tbody>
             </table>
             """
             final_output.append({"type": "html", "content": sample_html})

 
    extracted_text = "\n".join(full_text)
    if "CDD" in folder.upper():
        extracted_text = "\n".join(line for line in extracted_text.splitlines() if line.strip().startswith("C0"))

    return extracted_text, json_outputs, image_paths, final_output

@app.route("/", methods=["GET", "POST"])
def index():
    folders = [f for f in sorted(os.listdir(UPLOAD_FOLDER)) if os.path.isdir(os.path.join(UPLOAD_FOLDER, f))]
    result, files = None, []
    extracted_text, json_outputs, image_paths, final_output = "", [], [], []
    show_curation = False

    if request.method == "POST":
        selected = request.form.get("selected_folder")
        show_curation = bool(request.form.get("show_curation"))
        folder_path = os.path.join(UPLOAD_FOLDER, selected)
        extracted_text, json_outputs, image_paths, final_output = gather_folder_content(folder_path)
        result = selected

    counts = {
        f: len([x for x in os.listdir(os.path.join(UPLOAD_FOLDER, f)) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f, x))])
        for f in folders
    }

    return render_template_string(HTML_TEMPLATE,
        buttons=folders,
        counts=counts,
        selected_folder=result,
        extracted_text=extracted_text,
        json_outputs=json_outputs,
        image_paths=image_paths,
        final_output=final_output,
        show_curation=show_curation
    )

if __name__ == "__main__":
    app.run(debug=True)
