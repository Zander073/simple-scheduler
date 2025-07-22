# simple-scheduler

## First-time setup
* Run `brew bundle` to install brew packages
* Run `uv sync` to create a virtual environment and install dependencies
* Run `source .venv/bin/activate` to activate the virtual environment
  * Note: The exact command may change depending on which shell you use

## Running the app
* Recommended: add the following function definition to your shell config:
```
function dpy() {
  python manage.py "$@"
  return $?
}
```
* Start server: `dpy runserver`
* Open a console: `dpy shell`
* Generate migrations: `dpy makemigrations`
* Run migrations: `dpy migrate`
* Seed data: `dpy seed_data`