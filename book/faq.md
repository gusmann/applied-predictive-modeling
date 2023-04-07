
# Frequently Asked Questions (FAQ)

I'll admit, this FAQ was started before any questions were actually submitted, so they're definitely not frequently asked but will hopefully answer questions people will have about the project.

## Why this book?

TODO

## Why Python?

TODO


## Why Rust?

TODO

## How to create/build docs?  

```bash
poetry run python book/make-chapters.py
poetry run jupyter-book build book
poetry run python -m http.server --directory book/_build/html
```
