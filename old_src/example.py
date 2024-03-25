import os

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fasthx import Jinja

basedir = os.path.abspath(os.path.dirname(__file__))

# Create the app instance.
app = FastAPI()
# Create a FastAPI Jinja2Templates instance. This will be used in FastHX Jinja instance.
templates = Jinja2Templates(directory=os.path.join(basedir, "templates"))
# FastHX Jinja instance is initialized with the Jinja2Templates instance.
jinja = Jinja(templates)


@app.get("/user-list")
@jinja("user-list.html")  # Render the response with the user-list.html template.
def htmx_or_data() -> dict[str, list[dict[str, str]]]:
    """This route can serve both JSON and HTML, depending on if the request is an HTMX request or not."""
    return {
        "users": [
            {"first_name": "Peter", "last_name": "Volf"},
            {"first_name": "Hasan", "last_name": "Tasan"},
        ],
    }


@app.get("/admin-list")
@jinja.template(
    "user-list.html", no_data=True,
)  # Render the response with the user-list.html template.
def htmx_only() -> dict[str, list[dict[str, str]]]:
    """This route can only serve HTML, because the no_data parameter is set to True."""
    return {"users": [{"first_name": "John", "last_name": "Doe"}]}


@app.get("/")
def index(request: Request) -> HTMLResponse:
    """This route serves the index.html template."""
    return templates.TemplateResponse("index.html", context={"request": request})
