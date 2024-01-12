from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
db = SQLAlchemy(app)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False)
    publish_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<Article %r>" % self.title


@app.before_first_request
def create_tables():
    db.create_all()


@app.route("/")
def home():
    articles = Article.query.order_by(Article.publish_date.desc()).all()
    return render_template("home.html", articles=articles)


@app.route("/publish", methods=["GET", "POST"])
def publish():
    if request.method == "POST":
        article_title = request.form["title"]
        article_content = request.form["content"]
        article_author = request.form["author"]

        new_article = Article(
            title=article_title, content=article_content, author=article_author
        )
        db.session.add(new_article)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("publish.html")


@app.route("/article/<int:article_id>")
def article(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template("article.html", article=article)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
