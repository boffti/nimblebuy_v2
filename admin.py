from flask_admin.contrib.sqla import ModelView
from flask import session, redirect, url_for, request, flash


class AdminView(ModelView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.static_folder = 'static'

    def is_accessible(self):
        if 'permissions' in session:
            return 'get:admin_dashboard' in session.get('permissions')
        else:
            False

    def inaccessible_callback(self, name, **kwargs):
        if not self.is_accessible():
            flash('Unauthorized')
            return redirect(url_for('home', next=request.url))