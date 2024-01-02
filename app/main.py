import random
from flask import (
    Flask, 
    render_template, 
    request, 
    jsonify, 
    session, 
    g, 
    flash,
    redirect, 
    url_for,
    Blueprint
)
from config import DevConfig
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm as Form
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length
from flask_migrate import Migrate
from sqlalchemy import func, desc

app = Flask(__name__)
app.config.from_object(DevConfig)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


blog_blueprint = Blueprint(
    'blog',
    __name__,
    template_folder='templates/blog',
    url_prefix="/blog"
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255))
    full_name = db.Column(db.String(255))
    posts = db.relationship('Post', backref='user', lazy='dynamic')


tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
)

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255))
    text = db.Column(db.Text())
    publish_date = db.Column(db.DateTime())
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    tags = db.relationship('Tag', secondary=tags, backref=db.backref('posts', lazy='dynamic'))

    def __init__(self, title):
        self.title = title
    
    def __repr__(self):
        return "<Post '{}'>".format(self.title)


class Comment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    text = db.Column(db.Text())
    date = db.Column(db.DateTime())
    post_id = db.Column(db.Integer(), db.ForeignKey('posts.id'))
    
    def __repr__(self):
        return "<Comment '{}'>".format(self.text[:15])


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255))
    
    def __init__(self, title):
        self.title = title
    
    def __repr__(self):
        return "<Tag '{}'>".format(self.title)


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


@app.before_request
def before_request():
    session['page_loads'] = session.get('page_loads', 0) + 1
    g.random_key = random.randrange(1, 10)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


def sidebar_data():
    recent = Post.query.order_by(Post.publish_date.desc()).limit(5).all()
    top_tags = db.session.query(
        Tag, func.count(tags.c.post_id).label('total')
    ).join(tags).group_by(Tag).order_by(desc('total')).limit(5).all()

    return recent, top_tags


@blog_blueprint.route('/')
@blog_blueprint.route('/<int:page>')
def home(page=1):
    posts = Post.query.order_by(Post.publish_date.desc()).paginate(page=page, per_page=app.config.get('POSTS_PER_PAGE', 10), error_out=False)
    recent, top_tags = sidebar_data()

    return render_template(
        'home.html',
        posts=posts,
        recent=recent,
        top_tags=top_tags
    )


class CommentForm(Form):
    name = StringField(
        'Name',
        validators=[DataRequired(), Length(max=255)]
    )
    text = TextAreaField(u'Comment', validators=[DataRequired()])


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

app.register_blueprint(blog_blueprint)


from flask.views import View

class GenericListView(View):

    def __init__(self, model, list_template='generic_list.html'):
        self.model = model
        self.list_template = list_template
        self.columns = self.model.__mapper__.columns.keys()
        # Call super python3 style
        super(GenericListView, self).__init__()

    def render_template(self, context):
        return render_template(self.list_template, **context)

    def get_objects(self):
        return self.model.query.all()

    def dispatch_request(self):
        context = {'objects': self.get_objects(),
                   'columns': self.columns}
        return self.render_template(context)


app.add_url_rule(
    '/generic_posts', view_func=GenericListView.as_view(
        'generic_posts', model=Post)
    )

app.add_url_rule(
    '/generic_users', view_func=GenericListView.as_view(
        'generic_users', model=User)
)

app.add_url_rule(
    '/generic_comments', view_func=GenericListView.as_view(
        'generic_comments', model=Comment)
)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config['PORT'])