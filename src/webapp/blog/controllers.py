from sqlalchemy import desc, func
from flask import (
    render_template, Blueprint, 
    flash, redirect, url_for, 
    jsonify, request, current_app
)
from .models import db, Post, Tag, Comment, User, tags
from .forms import CommentForm


blog_blueprint = Blueprint(
    'blog',
    __name__,
    template_folder='../templates/blog',
    url_prefix="/blog"
)


def sidebar_data():
    recent = Post.query.order_by(Post.publish_date.desc()).limit(5).all()
    top_tags = db.session.query(
        Tag, func.count(tags.c.post_id).label('total')
    ).join(tags).group_by(Tag).order_by(desc('total')).limit(5).all()

    return recent, top_tags


@blog_blueprint.route('/')
@blog_blueprint.route('/<int:page>')
def home(page=1):
    posts = Post.query.order_by(Post.publish_date.desc()).paginate(page=page, per_page=current_app.config.get('POSTS_PER_PAGE', 10), error_out=False)
    recent, top_tags = sidebar_data()

    return render_template(
        'home.html',
        posts=posts,
        recent=recent,
        top_tags=top_tags
    )


@blog_blueprint.route('/post/<int:post_id>', methods=('GET', 'POST'))
def post(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        new_comment = Comment()
        new_comment.name = form.name.data
        new_comment.text = form.text.data
        new_comment.post_id = post_id
        try:
            db.session.add(new_comment)
            db.session.commit()
        except Exception as e:
            flash('Error adding your comment: %s' % str(e), 'error')
            db.session.rollback()
        else:
            flash('Comment added', 'info')
        return redirect(url_for('blog.post', post_id=post_id))

    post = Post.query.get_or_404(post_id)
    tags = post.tags
    comments = post.comments.order_by(Comment.date.desc()).all()
    recent, top_tags = sidebar_data()

    return render_template(
        'post.html',
        post=post,
        tags=tags,
        comments=comments,
        recent=recent,
        top_tags=top_tags,
        form=form
    )


@blog_blueprint.route('/posts_by_tag/<string:tag_name>')
def posts_by_tag(tag_name):
    tag = Tag.query.filter_by(title=tag_name).first_or_404()
    posts = tag.posts.order_by(Post.publish_date.desc()).all()
    recent, top_tags = sidebar_data()

    return render_template(
        'tag.html',
        tag=tag,
        posts=posts,
        recent=recent,
        top_tags=top_tags
    )


@blog_blueprint.route('/posts_by_user/<string:username>')
def posts_by_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.publish_date.desc()).all()
    recent, top_tags = sidebar_data()

    return render_template(
        'user.html',
        user=user,
        posts=posts,
        recent=recent,
        top_tags=top_tags
    )


@blog_blueprint.route("/users", methods=['GET'])
def list_users():
    # Get the page number from the request, default to 1 if not provided
    page = request.args.get('page', default=1, type=int)

    # Paginate the users
    users_pagination = User.query.paginate(page=page, per_page=10, error_out=False)

    # Extract data from pagination object
    users = users_pagination.items
    total_pages = users_pagination.pages
    current_page = users_pagination.page

    # Prepare the response
    response = {
        'users': [{
            'id': user.id, 
            'username': user.username,
            "full_name": user.full_name,
        } for user in users],
        'total_pages': total_pages,
        'current_page': current_page,
    }
    return jsonify(response)


@blog_blueprint.route('/users', methods=['POST'])
def add_user():
    # Get user data from the request body
    data = request.get_json()
    # Create a new user
    new_user = User(**data)

    # Add the user to the database
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User added successfully'}), 201