from . import download, auth, users, documents, logs, audit

router = download.router
# expose audit router via import side-effect (app.main imports routes)
