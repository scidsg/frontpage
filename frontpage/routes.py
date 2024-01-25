import os
import re
from collections import Counter
from datetime import datetime
from itertools import groupby

import markdown
import pycountry
from flask import flash, redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_required, login_user, logout_user
from slugify import slugify
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from . import app, inject_scopes, format_size, parse_size
from .db import db
from .forms import (
    AvatarForm,
    BioForm,
    CustomUrlForm,
    DisplayNameForm,
    PasswordForm,
    RegistrationForm,
    TeamPageForm,
)
from .models import Article, ArticleType, Category, InvitationCode, User


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        invite_code = InvitationCode.query.filter_by(code=form.invite_code.data, used=False).first()
        if not invite_code:
            flash("⛔️ Invalid or expired invite code.", "danger")
            return render_template("register.html", title="Register", form=form)

        user = User(username=form.username.data)
        user.set_password(form.password.data)
        user.requires_approval = True  # Set new users to require approval
        db.session.add(user)

        # Mark invite code as used
        invite_code.used = True
        db.session.commit()

        flash("👍 Your account has been created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("home"))
        flash("⛔️ Invalid username or password")

    return render_template("login.html", title="Login")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/")
def home():
    max_articles = 10

    # Only fetch articles that are not pending approval
    main_articles = (
        Article.query.filter_by(pending_approval=False)
        .order_by(Article.publish_date.desc())
        .limit(max_articles)
        .all()
    )

    main_articles_total = Article.query.count()

    recently_edited_articles = (
        Article.query.filter(Article.last_edited.isnot(None))
        .order_by(Article.last_edited.desc())
        .limit(max_articles)
        .all()
    )
    recently_edited_articles_total = Article.query.filter(Article.last_edited.isnot(None)).count()

    external_collaboration_articles = (
        Article.query.filter(Article.external_collaboration.isnot(None))
        .filter(Article.external_collaboration != "")
        .order_by(Article.publish_date.desc())
        .limit(max_articles)
        .all()
    )
    external_collaboration_articles_total = (
        Article.query.filter(Article.external_collaboration.isnot(None))
        .filter(Article.external_collaboration != "")
        .count()
    )

    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "home.html",
        title="Home",
        main_articles=main_articles,
        main_articles_total=main_articles_total,
        main_articles_more=main_articles_total > max_articles,
        recently_edited_articles=recently_edited_articles,
        recently_edited_articles_total=recently_edited_articles_total,
        recently_edited_articles_more=recently_edited_articles_total > max_articles,
        external_collaboration_articles=external_collaboration_articles,
        external_collaboration_articles_total=external_collaboration_articles_total,
        external_collaboration_articles_more=external_collaboration_articles_total > max_articles,
        show_team_link=show_team_link,
    )


# Protect the publish route
@app.route("/publish", methods=["GET", "POST"])
@login_required
def publish():
    categories = Category.query.all()
    countries = [country.name for country in pycountry.countries]
    article_types = ArticleType.query.all()  # Fetch article types from the database

    if request.method == "POST":
        article_title = request.form["title"]
        article_content = request.form["content"]
        article_countries = request.form.getlist("countries")
        article_country = ", ".join(article_countries)
        selected_article_type_ids = request.form.getlist("article_types")
        selected_article_types = ArticleType.query.filter(
            ArticleType.id.in_(selected_article_type_ids)
        ).all()
        article_download_link = request.form["download_link"]
        article_download_link2 = request.form["download_link2"]
        article_download_link3 = request.form["download_link3"]
        article_magnet_link = request.form["magnet_link"]
        article_magnet_link2 = request.form["magnet_link2"]
        article_magnet_link3 = request.form["magnet_link3"]
        article_torrent_link = request.form["torrent_link"]
        article_torrent_link2 = request.form["torrent_link2"]
        article_torrent_link3 = request.form["torrent_link3"]
        article_ipfs_link = request.form["ipfs_link"]
        article_ipfs_link2 = request.form["ipfs_link2"]
        article_ipfs_link3 = request.form["ipfs_link3"]
        article_download_size = request.form["download_size"]
        article_external_collaboration = request.form.get("external_collaboration")
        article_external_collaboration2 = request.form.get("external_collaboration2")
        article_external_collaboration3 = request.form.get("external_collaboration3")
        article_source = request.form["source"]
        requires_approval = current_user.requires_approval

        article_download_size_bytes = None  # Default to None if no size is provided

        # Only attempt conversion if a size is provided
        if article_download_size.strip():  # Check if the string is not just whitespace
            try:
                article_download_size_bytes = parse_size(article_download_size)
            except ValueError:
                flash(
                    "Invalid download size format. Please use formats like 1 MB, 2.4GB, etc.",
                    "danger",
                )
                return redirect(url_for("publish"))

        new_article = Article(
            title=article_title,
            content=article_content,
            author=current_user.username,
            country=article_country,
            download_link=article_download_link,
            download_link2=article_download_link2,
            download_link3=article_download_link3,
            article_types=selected_article_types,
            magnet_link=article_magnet_link,
            magnet_link2=article_magnet_link2,
            magnet_link3=article_magnet_link3,
            torrent_link=article_torrent_link,
            torrent_link2=article_torrent_link2,
            torrent_link3=article_torrent_link3,
            ipfs_link=article_ipfs_link,
            ipfs_link2=article_ipfs_link2,
            ipfs_link3=article_ipfs_link3,
            download_size=article_download_size_bytes,  # Use the converted size in bytes or None
            external_collaboration=article_external_collaboration,
            external_collaboration2=article_external_collaboration2,
            external_collaboration3=article_external_collaboration3,
            source=article_source,
            pending_approval=requires_approval,
        )

        # Extract and handle the publication date
        publish_date_str = request.form.get("publish_date")
        if publish_date_str:
            publish_date = datetime.strptime(publish_date_str, "%Y-%m-%dT%H:%M")
            new_article.publish_date = publish_date
        else:
            new_article.publish_date = datetime.utcnow()  # default to current time

        # Set slug for the new article
        new_article.set_slug()

        # Handle the last_edited date
        last_edited_str = request.form.get("last_edited")
        if last_edited_str:
            last_edited = datetime.strptime(last_edited_str, "%Y-%m-%dT%H:%M")
            new_article.last_edited = last_edited

        # Handle article categories
        selected_category_ids = request.form.getlist("categories")
        selected_categories = Category.query.filter(Category.id.in_(selected_category_ids)).all()
        new_article.categories = selected_categories

        try:
            db.session.add(new_article)
            db.session.commit()

            flash_message = (
                "⏱️ Your article has been submitted for approval."
                if requires_approval
                else "👍 Article published successfully."
            )
            flash(flash_message, "success")
        except IntegrityError:
            db.session.rollback()
            flash(
                "An error occurred: The article slug must be unique. Please try a different title.",
                "danger",
            )
            app.logger.error(
                "IntegrityError: Duplicate slug found while trying to publish an article."
            )
            return redirect(url_for("publish"))

        return redirect(url_for("home"))

    return render_template(
        "publish.html",
        title="Publish Article",
        categories=categories,
        countries=countries,
        article_types=article_types,  # Pass article types to the template
    )


@app.route("/approve_articles")
@login_required
def approve_articles():
    if not current_user.is_admin:
        flash("⛔️ Unauthorized access.", "danger")
        return redirect(url_for("home"))

    # Fetch only articles that are pending approval
    articles_to_approve = Article.query.filter_by(pending_approval=True).all()
    article_count = len(articles_to_approve)  # Get the count of articles pending approval

    return render_template(
        "approve_articles.html",
        title="Approve Articles",
        articles=articles_to_approve,
        article_count=article_count,
    )


@app.route("/approve_article/<slug>", methods=["POST"])
@login_required
def approve_article(slug):
    if not current_user.is_admin:
        flash("⛔️ Unauthorized access.", "danger")
        return redirect(url_for("home"))

    article = Article.query.filter_by(slug=slug).first_or_404()
    if current_user.is_admin:
        article.pending_approval = False  # Mark as approved
        db.session.commit()
        flash("🎉 Article approved.", "success")
    else:
        flash("⛔️ Unauthorized access.", "danger")

    return redirect(url_for("approve_articles"))


@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if not current_user.is_admin:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        if "delete_user" in request.form:
            user_id_to_delete = request.form.get("delete_user")
            if int(user_id_to_delete) != current_user.id:
                user_to_delete = User.query.get(user_id_to_delete)
                if user_to_delete:
                    db.session.delete(user_to_delete)
                    db.session.commit()
                    flash("🗑️ User deleted successfully.", "success")
                else:
                    flash("🤔 User not found.", "danger")
            else:
                flash("😱 You cannot delete your own account.", "warning")
            return redirect(url_for("users"))
        else:
            all_users = User.query.all()
            for user in all_users:
                user.requires_approval = f"approval_{user.id}" in request.form
                user.is_admin = f"admin_{user.id}" in request.form
            db.session.commit()
            flash("👍 Users updated successfully.", "success")

    all_users = User.query.all()
    user_count = len(all_users)
    return render_template("users.html", title="Users", users=all_users, user_count=user_count)


@app.route("/article/<slug>")
def article(slug):
    article = Article.query.filter_by(slug=slug).first_or_404()

    # Convert the download size to a human-readable format for the template
    download_size_formatted = (
        format_size(int(article.download_size)) if article.download_size is not None else None
    )

    content_html = markdown.markdown(article.content)

    # Fetch related articles by type
    related_by_type = (
        Article.query.join(Article.article_types)
        .filter(
            ArticleType.id.in_([atype.id for atype in article.article_types]),
            Article.id != article.id,
        )
        .all()
    )

    related_by_type_grouped = {
        atype.name: [art for art in related_by_type if atype in art.article_types]
        for atype in article.article_types
    }

    # Fetch related articles by source
    related_by_source = Article.query.filter(
        Article.source == article.source, Article.id != article.id
    ).all()
    related_by_source_grouped = {
        k: list(g)
        for k, g in groupby(
            sorted(related_by_source, key=lambda x: x.source), key=lambda x: x.source
        )
    }

    # Related articles by country with handling for multiple countries
    related_by_country_dict = {}
    if article.country:
        countries = article.country.split(", ")
        for country in countries:
            related_articles = Article.query.filter(
                Article.country.like(f"%{country}%"), Article.id != article.id
            ).all()
            if country not in related_by_country_dict:
                related_by_country_dict[country] = []
            related_by_country_dict[country].extend(related_articles)

    # Collect all articles to determine top scopes
    all_articles = Article.query.all()
    counter = Counter()
    for a in all_articles:
        if a.article_types:
            for atype in a.article_types:
                counter[("type", atype.name)] += 1
        if a.country:
            for c in a.country.split(", "):
                counter[("country", c)] += 1
        if a.source:
            counter[("source", a.source)] += 1

    # Check if the article is pending approval
    if article.pending_approval:
        # If the article is pending, only allow access to admins
        if not current_user.is_authenticated or not current_user.is_admin:
            flash(
                "⛔️ Nuh uh uh, you didn't say the magic word...",
                "warning",
            )
            return redirect(url_for("home"))

    # Get the top 5 scopes
    top_scopes = counter.most_common(5)
    all_scopes = [{"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes]

    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "article.html",
        title=article.title,
        article=article,
        download_size_formatted=download_size_formatted,
        content_html=content_html,
        related_by_type_grouped=related_by_type_grouped,
        related_by_source_grouped=related_by_source_grouped,
        related_by_country_grouped=related_by_country_dict,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/edit/<slug>", methods=["GET", "POST"])
@login_required
def edit_article(slug):
    app.logger.info(f"Editing article with slug: {slug}")

    article = Article.query.filter_by(slug=slug).first_or_404()
    if not article:
        app.logger.warning(f"Article with slug {slug} not found")
        flash("Article not found.")
        return redirect(url_for("home"))

    if article.pending_approval and not current_user.is_admin:
        flash("⛔️ This article is pending approval and cannot be edited.", "warning")
        return redirect(url_for("home"))

    if not (current_user.username == article.author or current_user.is_admin):
        app.logger.warning(
            f"Unauthorized edit attempt by user {current_user.username} on article {slug}"
        )
        flash("⛔️ You do not have permission to edit this article.")
        return redirect(url_for("home"))

    categories = Category.query.all()
    countries = [country.name for country in pycountry.countries]
    article_types = ArticleType.query.all()

    # Convert the download size from bytes for the edit form using format_size
    if article.download_size is not None:
        try:
            size_in_bytes = int(article.download_size)
            article.download_size_for_edit = format_size(size_in_bytes)
        except ValueError:
            article.download_size_for_edit = "Invalid size"
    else:
        article.download_size_for_edit = ""

    if request.method == "POST":
        app.logger.info(f"Processing POST request for editing article {slug}")

        try:
            original_title = article.title
            article.title = request.form["title"]
            article.content = request.form["content"]
            article.country = ", ".join(request.form.getlist("countries"))

            # Handle article types
            selected_article_type_ids = request.form.getlist("article_types")
            selected_article_types = ArticleType.query.filter(
                ArticleType.id.in_(selected_article_type_ids)
            ).all()
            article.article_types = selected_article_types

            # Update DL links
            article.download_link = request.form["download_link"]
            article.download_link2 = request.form.get("download_link2")
            article.download_link3 = request.form.get("download_link3")

            # Update magnet links
            article.magnet_link = request.form.get("magnet_link")
            article.magnet_link2 = request.form.get("magnet_link2")
            article.magnet_link3 = request.form.get("magnet_link3")

            # Update torrent links
            article.torrent_link = request.form.get("torrent_link")
            article.torrent_link2 = request.form.get("torrent_link2")
            article.torrent_link3 = request.form.get("torrent_link3")

            # Update IPFS links
            article.ipfs_link = request.form.get("ipfs_link")
            article.ipfs_link2 = request.form.get("ipfs_link2")
            article.ipfs_link3 = request.form.get("ipfs_link3")

            # Update external collaboration links
            article.external_collaboration = request.form.get("external_collaboration")
            article.external_collaboration2 = request.form.get("external_collaboration2")
            article.external_collaboration3 = request.form.get("external_collaboration3")

            # Convert download size
            article_download_size = request.form["download_size"]
            try:
                article.download_size = parse_size(article_download_size)
            except ValueError:
                flash(
                    "Invalid download size format. Please use formats like 1 MB, 2.4GB, etc.",
                    "danger",
                )
                return redirect(url_for("edit_article", slug=slug))

            article.source = request.form.get("source", "")

            # Extract and handle the publication and last edited dates
            publish_date_str = request.form.get("publish_date")
            if publish_date_str:
                article.publish_date = datetime.strptime(publish_date_str, "%Y-%m-%dT%H:%M")

            last_edited_str = request.form.get("last_edited")
            if last_edited_str:
                article.last_edited = datetime.strptime(last_edited_str, "%Y-%m-%dT%H:%M")

            if original_title != article.title:
                article.slug = slugify(article.title)
                # Ensure unique slug
                original_slug = article.slug
                count = 1
                while Article.query.filter(
                    Article.slug == article.slug, Article.id != article.id
                ).first():
                    article.slug = f"{original_slug}-{count}"
                    count += 1

            # Handle categories
            selected_category_ids = request.form.getlist("categories")
            selected_categories = Category.query.filter(
                Category.id.in_(selected_category_ids)
            ).all()
            article.categories = selected_categories

            db.session.commit()
            app.logger.info(f"Article {slug} updated successfully")
            flash("👍 Article updated successfully.")
            return redirect(url_for("article", slug=article.slug))

        except Exception as e:
            app.logger.error(f"Error updating article {slug}: {e}", exc_info=True)
            flash("Error updating article.")
            return redirect(url_for("edit_article", slug=slug))

    else:
        selected_countries = article.country.split(", ") if article.country else []
        selected_categories = [category.id for category in article.categories]
        selected_article_type_ids = [atype.id for atype in article.article_types]

        return render_template(
            "edit_article.html",
            title="Edit Article",
            article=article,
            categories=categories,
            countries=countries,
            selected_countries=selected_countries,
            article_types=article_types,
            selected_article_type_ids=selected_article_type_ids,
            selected_categories=selected_categories,
            download_size_for_edit=article.download_size_for_edit,
        )


@app.route("/source/<source>")
def articles_by_source(source):
    articles = Article.query.filter_by(source=source).all()
    article_count = len(articles)  # Get the count of articles

    # Use inject_scopes function to get the top scopes
    scope_data = inject_scopes()
    all_scopes = scope_data["all_scopes"]

    # Check if the team link should be shown
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    # Create a dynamic title based on the source
    title = f"Articles from {source}"

    return render_template(
        "source_articles.html",
        title=title,
        articles=articles,
        source=source,
        article_count=article_count,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/country/<country>")
def articles_by_country(country):
    articles = Article.query.filter(Article.country.like(f"%{country}%")).all()
    article_count = len(articles)  # Get the count of articles

    # Use inject_scopes function to get the top scopes
    scope_data = inject_scopes()
    all_scopes = scope_data["all_scopes"]

    # Check if the team link should be shown
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    # Create a dynamic title based on the country
    title = f"Articles from {country}"

    return render_template(
        "country_articles.html",
        title=title,
        articles=articles,
        country=country,
        article_count=article_count,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/author/<author>")
def articles_by_author(author):
    articles = Article.query.filter_by(author=author).all()
    article_count = len(articles)  # Get the count of articles

    # Use inject_scopes function to get the top scopes
    scope_data = inject_scopes()
    all_scopes = scope_data["all_scopes"]

    # Check if the team link should be shown
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    # Create a dynamic title based on the author's name
    title = f"Articles by {author}"

    return render_template(
        "author_articles.html",
        title=title,
        articles=articles,
        author=author,
        article_count=article_count,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/type/<article_type>")
def articles_by_type(article_type):
    articles = []

    if article_type.lower() == "all":
        articles = Article.query.all()
        title = "All Articles"  # Title for 'all' types
    else:
        type_obj = ArticleType.query.filter_by(name=article_type).first()
        if type_obj:
            articles = (
                Article.query.join(Article.article_types)
                .filter(ArticleType.name == article_type)
                .all()
            )
        title = f"Articles of Type: {article_type}"  # Dynamic title for specific type

    article_count = len(articles)

    # Use inject_scopes function to get the top scopes
    scope_data = inject_scopes()
    all_scopes = scope_data["all_scopes"]

    # Check if the team link should be shown
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "type_articles.html",
        title=title,
        articles=articles,
        article_type=article_type,
        article_count=article_count,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/all_categories")
def all_categories():
    # Fetch all article types that have at least one article
    article_types = (
        ArticleType.query.filter(ArticleType.articles.any()).order_by(ArticleType.name).all()
    )

    # Fetch countries and sources from articles
    articles = Article.query.all()
    countries = sorted(
        set(
            country
            for article in articles
            for country in article.country.split(", ")
            if article.country
        )
    )
    sources = sorted(set(article.source for article in articles if article.source))

    # Use inject_scopes function to get the top scopes
    scope_data = inject_scopes()
    all_scopes = scope_data["all_scopes"]

    # Check if the team link should be shown
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "all_categories.html",
        title="All Categories",
        article_types=article_types,
        countries=countries,
        sources=sources,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/delete_article/<int:article_id>", methods=["POST"])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)

    # Check if the current user is the author or an admin
    if not (current_user.username == article.author or current_user.is_admin):
        flash("⛔️ You do not have permission to delete this article.")
        return redirect(url_for("home"))

    db.session.delete(article)
    db.session.commit()
    flash("🗑️ Article deleted successfully.")
    return redirect(url_for("home"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def user_settings():
    bio_form = BioForm(obj=current_user)
    password_form = PasswordForm()
    team_page_form = TeamPageForm(obj=current_user)
    display_name_form = DisplayNameForm(obj=current_user)
    custom_url_form = CustomUrlForm(obj=current_user)
    avatar_form = AvatarForm()

    if "submit_bio" in request.form and bio_form.validate_on_submit():
        current_user.bio = bio_form.bio.data
        db.session.commit()
        flash("Your bio has been updated.", "success")

    elif "submit_password" in request.form and password_form.validate_on_submit():
        if current_user.check_password(password_form.current_password.data):
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash("Your password has been updated. Please log in again.", "success")
            logout_user()
            return redirect(url_for("login"))
        else:
            flash("Current password is incorrect.", "danger")

    elif "submit_team" in request.form and team_page_form.validate_on_submit():
        current_user.include_in_team_page = team_page_form.include_in_team_page.data
        db.session.commit()
        flash("Team page settings updated", "success")

    elif "submit_display_name" in request.form and display_name_form.validate_on_submit():
        current_user.display_name = display_name_form.display_name.data
        db.session.commit()
        flash("Your display name has been updated.", "success")

    elif "submit_custom_url" in request.form and custom_url_form.validate_on_submit():
        current_user.custom_url = custom_url_form.custom_url.data
        db.session.commit()
        flash("Your custom URL has been updated.", "success")

    elif avatar_form.validate_on_submit() and "avatar" in request.files:
        file = avatar_form.avatar.data
        filename = secure_filename(file.filename)
        if filename != "":
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            current_user.avatar = filename
            db.session.commit()
            flash("Your avatar has been updated.", "success")
        else:
            flash("No file selected.", "warning")

    return render_template(
        "settings.html",
        title="Settings",
        bio_form=bio_form,
        password_form=password_form,
        team_page_form=team_page_form,
        display_name_form=display_name_form,
        custom_url_form=custom_url_form,
        avatar_form=avatar_form,
    )


@app.route("/update_bio", methods=["POST"])
@login_required
def update_bio():
    form = BioForm()
    user = current_user

    if form.validate_on_submit():
        user.bio = form.bio.data
        db.session.commit()
        flash("👍 Your bio has been updated.", "success")
    else:
        flash("Error updating bio.", "danger")

    return redirect(url_for("user_settings"))


@app.route("/change_password", methods=["POST"])
@login_required
def change_password():
    form = PasswordForm()
    user = current_user

    if form.validate_on_submit():
        if user.check_password(form.current_password.data):
            # Set new password using Passlib
            user.set_password(form.new_password.data)
            db.session.commit()
            flash("👍 Your password has been updated.", "success")
            logout_user()
            return redirect(url_for("login"))
        else:
            flash("⛔️ Current password is incorrect.", "danger")

    return redirect(url_for("user_settings"))


@app.route("/all_articles/<category>")
def all_articles(category):
    articles = []

    if category == "recent":
        articles = (
            Article.query.filter_by(pending_approval=False)
            .order_by(Article.publish_date.desc())
            .all()
        )
        title = "All Recently Published Articles"
    elif category == "edited":
        articles = (
            Article.query.filter(
                Article.pending_approval.is_(False), Article.last_edited.isnot(None)
            )
            .order_by(Article.last_edited.desc())
            .all()
        )
        title = "All Recently Edited Articles"
    elif category == "external":
        articles = (
            Article.query.filter(
                Article.pending_approval.is_(False),
                Article.external_collaboration.isnot(None),
                Article.external_collaboration != "",
            )
            .order_by(Article.publish_date.desc())
            .all()
        )
        title = "All External Collaboration Articles"

    article_count = len(articles)

    # Use inject_scopes function to get the top scopes
    scope_data = inject_scopes()
    all_scopes = scope_data["all_scopes"]

    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "all_articles.html",
        title=title,
        articles=articles,
        article_count=article_count,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/team")
def team():
    users = User.query.filter(User.include_in_team_page).all()
    return render_template("team.html", title="Our Team", users=users)


@app.route("/all_articles/a-z")
def all_articles_alphabetized():
    # Fetch all articles that do not require approval and sort by title
    articles = Article.query.filter_by(pending_approval=False).order_by(Article.title).all()
    article_count = len(articles)  # Get the count of articles

    # Render the template with the filtered articles
    return render_template(
        "all_articles_alphabetized.html",
        title="All Approved Articles (A-Z)",
        articles=articles,
        article_count=article_count,
    )


@app.route("/impact")
def impact():
    # Calculate total number of articles
    total_articles_count = Article.query.count()

    # Get the "Limited Distribution" article type
    limited_dist_type = ArticleType.query.filter_by(name="Limited Distribution").first()

    # Calculate total number of limited distribution articles
    if limited_dist_type:
        limited_dist_articles_count = len(limited_dist_type.articles)
        limited_dist_percentage = (
            (limited_dist_articles_count / total_articles_count) * 100
            if total_articles_count > 0
            else 0
        )
    else:
        limited_dist_articles_count = 0
        limited_dist_percentage = 0

    # Top Source
    top_source = (
        db.session.query(Article.source, db.func.count(Article.id))
        .group_by(Article.source)
        .order_by(db.func.count(Article.id).desc())
        .first()
    )

    # Top Country
    top_country = (
        db.session.query(Article.country, db.func.count(Article.id))
        .group_by(Article.country)
        .order_by(db.func.count(Article.id).desc())
        .first()
    )

    # Top Type
    top_type = (
        db.session.query(ArticleType.name, db.func.count(Article.id))
        .join(Article.article_types)
        .group_by(ArticleType.name)
        .order_by(db.func.count(Article.id).desc())
        .first()
    )

    # Render the template with the calculated metrics
    return render_template(
        "impact.html",
        title="Impact Metrics",
        total_articles_count=total_articles_count,
        limited_dist_percentage=limited_dist_percentage,
        top_source=top_source,
        top_country=top_country,
        top_type=top_type,
    )


@app.route("/submit")
def submit():
    return render_template("submit.html", title="Submit")


@app.route("/api/article_count")
def article_count():
    count = Article.query.count()
    return jsonify({"count": count})
