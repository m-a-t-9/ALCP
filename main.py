from flask import Flask, render_template, request, redirect, url_for
from core.Model import Model

model = Model()

app = Flask(__name__)


@app.route("/")
def index():
    return redirect(url_for("admin_databases"))

@app.route("/<database>/listview", methods=['POST', 'GET'])
def listview(database):
    if request.method == "POST":
        model.create_record(request.form.to_dict(), database)
    return render_template('listview.html', data=model.get_all_records(database),
                           layout=model.get_layout_for(database))

@app.route("/<database>/<id>")
def details_view(database, id):
    return render_template('record.html', data=model.get_record_by_id(id),
                           layout=model.get_layout_for(database))

@app.route("/admin/databases", methods=['GET', 'POST'])
def admin_databases():
    if request.method == "POST":
        model.create_database(request.form.to_dict())
    return render_template('database.html', data=model.get_list_of_databases())

@app.route("/admin/database/layout/<id>", methods=['GET', 'POST'])
def admin_database_layout(id):
    if request.method == 'POST':
        print(request.form.to_dict(flat=False))
        model.update_layout_by_id(request.form.to_dict(flat=False), id)
    print(model.get_layout_by_id(id))
    return render_template('database.html', layout=model.get_layout_by_id(id),
                           id=id)

@app.route("/admin/database/layout/<id>/delete")
def admin_database_layout_field_delete(id):
    print(request.args.get('name'))
    model.remove_field_from_layout(id, request.args.get('name'))
    return redirect(url_for('admin_database_layout', id=id))

@app.route("/admin/database/<id>/delete")
def admin_database_delete(id):
    model.remove_database_and_layout(id)
    return redirect(url_for('admin_databases'))

@app.route("/api/databases")
def api_databases():
    print("API", str(model.get_list_of_databases()))
    return model.get_list_of_databases()

@app.route("/api/<database>")
def api_database(database):
    result = model.search_records(database, request.args.to_dict(flat=True)['query'])
    print(result)
    return result