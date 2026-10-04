import os
import re
import uuid
import bcrypt
from flask import (Flask, render_template, request, redirect, url_for, 
                   flash, jsonify, send_from_directory, abort)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
from config import Config
from models import db, Category, Project, ProjectImage, AdminUser, SiteSetting, slugify

BASE_DIR = Config.BASE_DIR
BACKEND_DIR = Config.BACKEND_DIR

app = Flask(
    __name__,
    template_folder=os.path.join(BACKEND_DIR, 'templates'),
    static_folder=BASE_DIR,
    static_url_path='/static'
)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)

import shutil
from collections import defaultdict

LAST_SYNC_TIME = 0

def sync_images_folder():
    global LAST_SYNC_TIME
    images_dir = app.config['UPLOAD_FOLDER']
    upload_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(images_dir):
        return

    try:
        current_mtime = os.path.getmtime(images_dir)
    except Exception:
        return

    if current_mtime <= LAST_SYNC_TIME:
        return

    LAST_SYNC_TIME = current_mtime

    files = os.listdir(images_dir)
    img_pattern = re.compile(r'^(.*?)\s*\(\s*(\d+)\s*\)\.[a-zA-Z0-9]+$')
    projects_dict = defaultdict(list)

    for f in files:
        match = img_pattern.match(f)
        if match:
            proj_name = match.group(1).strip()
            key = proj_name.lower()
            projects_dict[key].append((int(match.group(2)), f, proj_name))

    if not projects_dict:
        return

    category = Category.query.first()
    cat_id = category.id if category else None

    for key, items in projects_dict.items():
        items.sort(key=lambda x: x[0])
        proj_display_name = items[0][2]
        slug = slugify(proj_display_name)

        project = Project.query.filter_by(slug=slug).first()
        if not project:
            # Only create brand-new projects — NEVER modify existing ones
            project = Project(
                title=proj_display_name,
                slug=slug,
                description=f"Project details for {proj_display_name}",
                is_featured=False,
                category_id=cat_id,
                status='published'
            )
            db.session.add(project)
            db.session.flush()

        # Get filenames already saved for this project in DB
        existing_filenames = {img.filename for img in project.images}
        has_cover = any(img.is_cover for img in project.images)

        for num, filename, _ in items:
            src_path = os.path.join(images_dir, filename)
            dest_path = os.path.join(upload_dir, filename)

            # Copy file to uploads folder if not already there and paths differ
            if src_path != dest_path:
                if not os.path.exists(dest_path):
                    shutil.copy2(src_path, dest_path)
                elif os.path.getmtime(src_path) > os.path.getmtime(dest_path):
                    shutil.copy2(src_path, dest_path)

            # ONLY add images not already in DB — NEVER modify existing DB records
            if filename not in existing_filenames:
                assign_cover = (num == 1) and not has_cover
                if assign_cover:
                    has_cover = True
                pi = ProjectImage(
                    project_id=project.id,
                    filename=filename,
                    is_cover=assign_cover,
                    sort_order=num
                )
                db.session.add(pi)

    db.session.commit()

@app.before_request
def auto_sync():
    sync_images_folder()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access the admin panel.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

@app.context_processor
def inject_site_settings():
    settings = {}
    try:
        for s in SiteSetting.query.all():
            settings[s.key] = s.value
    except Exception:
        pass

    def get_setting(key, default=None):
        return settings.get(key, getattr(Config, key, default))

    return dict(settings=settings, get_setting=get_setting)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Helper Functions
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def allowed_file(filename):
    return ('.' in filename and 
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'])

def save_image(file, subfolder='projects'):
    """Save uploaded image, optionally resize for web."""
    if not file or not allowed_file(file.filename):
        return None
    
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    
    # Save and optimize with PIL
    img = Image.open(file)
    img = img.convert('RGB')
    
    # Resize if too large (max 2400px width for web)
    max_width = 2400
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    
    img.save(filepath, 'JPEG', quality=85, optimize=True)
    
    return f"{subfolder}/{filename}"


def unique_slug(base_slug, model, exclude_id=None):
    """Ensure slug is unique, appending counter if needed."""
    slug = base_slug
    counter = 1
    while True:
        query = model.query.filter_by(slug=slug)
        if exclude_id:
            query = query.filter(model.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Public Routes
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/')
def index():
    featured_projects = Project.query.filter_by(is_featured=True, status='published').limit(6).all()
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('index.html', 
                           featured_projects=featured_projects,
                           categories=categories)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/sitemap.xml')
def sitemap():
    from flask import Response
    base = request.host_url.rstrip('/')
    projects = Project.query.filter_by(status='published').all()
    pages = [
        (base + '/', 'weekly', '1.0'),
        (base + '/about', 'monthly', '0.8'),
        (base + '/projects', 'weekly', '0.9'),
        (base + '/services', 'monthly', '0.8'),
        (base + '/team', 'monthly', '0.7'),
        (base + '/contact', 'monthly', '0.8'),
    ]
    for p in projects:
        pages.append((base + '/projects/' + p.slug, 'monthly', '0.7'))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, freq, pri in pages:
        xml.append(f'  <url><loc>{loc}</loc><changefreq>{freq}</changefreq><priority>{pri}</priority></url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    from flask import send_from_directory
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/projects')
def projects():
    category_slug = request.args.get('category', 'all')
    categories = Category.query.order_by(Category.sort_order).all()
    
    query = Project.query.filter_by(status='published')
    if category_slug and category_slug != 'all':
        cat = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category_id=cat.id)
    
    all_projects = query.order_by(Project.created_at.desc()).all()
    return render_template('projects.html', 
                           projects=all_projects, 
                           categories=categories,
                           active_category=category_slug)

@app.route('/projects/<slug>')
def project_detail(slug):
    project = Project.query.filter_by(slug=slug, status='published').first_or_404()
    related = Project.query.filter(
        Project.category_id == project.category_id,
        Project.id != project.id,
        Project.status == 'published'
    ).limit(3).all()
    return render_template('project_detail.html', project=project, related=related)

@app.route('/contact/submit', methods=['POST'])
def contact_submit():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    project_type = request.form.get('project_type', '').strip()
    message = request.form.get('message', '').strip()
    
    if not name or not phone or not message:
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('contact'))
    
    # In production, send email here
    flash('Thank you for your enquiry! We will get back to you within 24 hours.', 'success')
    return redirect(url_for('contact'))

# Serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Admin Routes
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').encode('utf-8')
        
        user = AdminUser.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password, user.password_hash.encode('utf-8')):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))
        
        flash('Invalid username or password.', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    total_projects = Project.query.count()
    published_projects = Project.query.filter_by(status='published').count()
    featured_projects = Project.query.filter_by(is_featured=True).count()
    categories = Category.query.count()
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           total_projects=total_projects,
                           published_projects=published_projects,
                           featured_projects=featured_projects,
                           categories=categories,
                           recent_projects=recent_projects)

@app.route('/admin/projects')
@login_required
def admin_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('admin/projects.html', projects=projects)

@app.route('/admin/projects/new', methods=['GET', 'POST'])
@login_required
def admin_project_new():
    categories = Category.query.order_by(Category.sort_order).all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        year = request.form.get('year', '').strip()
        area = request.form.get('area', '').strip()
        category_id = request.form.get('category_id')
        is_featured = 'is_featured' in request.form
        status = request.form.get('status', 'published')
        
        if not title:
            flash('Project title is required.', 'error')
            return render_template('admin/project_form.html', categories=categories, project=None)
        
        base_slug = slugify(title)
        slug = unique_slug(base_slug, Project)
        
        project = Project(
            title=title,
            slug=slug,
            description=description,
            location=location,
            year=int(year) if year.isdigit() else None,
            area=area,
            category_id=int(category_id) if category_id else None,
            is_featured=is_featured,
            status=status
        )
        db.session.add(project)
        db.session.flush()  # Get project.id before images
        
        # Handle image uploads
        files = request.files.getlist('images')
        cover_index = int(request.form.get('cover_index', 0))
        
        for i, file in enumerate(files):
            if file and file.filename:
                saved_path = save_image(file)
                if saved_path:
                    img = ProjectImage(
                        project_id=project.id,
                        filename=saved_path,
                        is_cover=(i == cover_index),
                        sort_order=i
                    )
                    db.session.add(img)
        
        db.session.commit()
        flash(f'Project "{title}" has been created successfully!', 'success')
        return redirect(url_for('admin_projects'))
    
    return render_template('admin/project_form.html', categories=categories, project=None)

@app.route('/admin/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_project_edit(project_id):
    project = Project.query.get_or_404(project_id)
    categories = Category.query.order_by(Category.sort_order).all()
    
    if request.method == 'POST':
        project.title = request.form.get('title', '').strip()
        project.description = request.form.get('description', '').strip()
        project.location = request.form.get('location', '').strip()
        year = request.form.get('year', '').strip()
        project.year = int(year) if year.isdigit() else None
        project.area = request.form.get('area', '').strip()
        category_id = request.form.get('category_id')
        project.category_id = int(category_id) if category_id else None
        project.is_featured = 'is_featured' in request.form
        project.status = request.form.get('status', 'published')
        
        # Update slug if title changed
        new_slug = slugify(project.title)
        project.slug = unique_slug(new_slug, Project, exclude_id=project.id)
        
        # Handle new image uploads
        files = request.files.getlist('images')
        current_count = len(project.images)
        for i, file in enumerate(files):
            if file and file.filename:
                saved_path = save_image(file)
                if saved_path:
                    img = ProjectImage(
                        project_id=project.id,
                        filename=saved_path,
                        is_cover=False,
                        sort_order=current_count + i
                    )
                    db.session.add(img)
        
        # Set cover image
        cover_image_id = request.form.get('cover_image_id')
        if cover_image_id:
            for img in project.images:
                img.is_cover = (str(img.id) == cover_image_id)
        
        db.session.commit()
        flash(f'Project "{project.title}" has been updated!', 'success')
        return redirect(url_for('admin_projects'))
    
    return render_template('admin/project_form.html', categories=categories, project=project)

@app.route('/admin/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def admin_project_delete(project_id):
    project = Project.query.get_or_404(project_id)
    title = project.title
    
    # Delete image files
    for img in project.images:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    db.session.delete(project)
    db.session.commit()
    flash(f'Project "{title}" has been deleted.', 'success')
    return redirect(url_for('admin_projects'))

@app.route('/admin/projects/<int:project_id>/toggle-featured', methods=['POST'])
@login_required
def admin_toggle_featured(project_id):
    project = Project.query.get_or_404(project_id)
    project.is_featured = not project.is_featured
    db.session.commit()
    return jsonify({'featured': project.is_featured})

@app.route('/admin/projects/<int:project_id>/toggle-status', methods=['POST'])
@login_required
def admin_toggle_status(project_id):
    project = Project.query.get_or_404(project_id)
    project.status = 'draft' if project.status == 'published' else 'published'
    db.session.commit()
    return jsonify({'status': project.status})

@app.route('/admin/images/<int:image_id>/delete', methods=['POST'])
@login_required
def admin_image_delete(image_id):
    img = ProjectImage.query.get_or_404(image_id)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(img)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/categories')
@login_required
def admin_categories():
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/new', methods=['POST'])
@login_required
def admin_category_new():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('admin_categories'))
    
    slug = unique_slug(slugify(name), Category)
    category = Category(name=name, slug=slug, description=description)
    db.session.add(category)
    db.session.commit()
    flash(f'Category "{name}" created.', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
def admin_category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    # Un-assign projects from this category
    Project.query.filter_by(category_id=cat.id).update({'category_id': None})
    db.session.delete(cat)
    db.session.commit()
    flash(f'Category "{cat.name}" deleted.', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    keys = [
        'BUSINESS_NAME', 'BUSINESS_PHONE', 'BUSINESS_PHONE2',
        'BUSINESS_EMAIL', 'BUSINESS_WHATSAPP', 'BUSINESS_WHATSAPP2',
        'BUSINESS_ADDRESS', 'BUSINESS_INSTAGRAM', 'BUSINESS_FACEBOOK'
    ]
    if request.method == 'POST':
        for key in keys:
            val = request.form.get(key.lower(), '').strip()
            setting = SiteSetting.query.filter_by(key=key).first()
            if not setting:
                setting = SiteSetting(key=key, value=val)
                db.session.add(setting)
            else:
                setting.value = val
        db.session.commit()
        flash('Site settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    current_settings = {}
    try:
        for s in SiteSetting.query.all():
            current_settings[s.key] = s.value
    except Exception:
        pass
    return render_template('admin/settings.html', settings=current_settings)

@app.route('/admin/change-password', methods=['GET', 'POST'])
@login_required
def admin_change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').encode('utf-8')
        new_password = request.form.get('new_password', '').encode('utf-8')
        confirm_password = request.form.get('confirm_password', '').encode('utf-8')
        
        user = AdminUser.query.get(current_user.id)
        if not user or not bcrypt.checkpw(current_password, user.password_hash.encode('utf-8')):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('admin_change_password'))
            
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('admin_change_password'))
            
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('admin_change_password'))
            
        hashed = bcrypt.hashpw(new_password, bcrypt.gensalt()).decode('utf-8')
        user.password_hash = hashed
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/change_password.html')


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Database Initialization
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def init_db():
    """Create tables and seed default data."""
    db.create_all()
    
    # Create admin user if none exists
    if not AdminUser.query.first():
        password = app.config['ADMIN_PASSWORD'].encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
        admin = AdminUser(username=app.config['ADMIN_USERNAME'], password_hash=hashed)
        db.session.add(admin)
    
    # Create default categories if none exist
    if not Category.query.first():
        default_categories = [
            ('Residential Construction', 'residential-construction', 'Complete home construction and renovation.', 1),
            ('Commercial Construction', 'commercial-construction', 'Professional office and commercial building projects.', 2),
            ('Renovation Works', 'renovation-works', 'Complete structural and interior renovations.', 3),
            ('Civil Works', 'civil-works', 'Foundation, structural, and general civil contracting.', 4),
            ('Interior Contracting', 'interior-contracting', 'Turnkey interior execution and finishing works.', 5),
            ('Project Management', 'project-management', 'End-to-end project execution and management.', 6),
        ]
        for name, slug, desc, order in default_categories:
            cat = Category(name=name, slug=slug, description=desc, sort_order=order)
            db.session.add(cat)
    
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    # Create upload directories
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'projects'), exist_ok=True)
    
    print("\n" + "="*60)
    print("  SHARMA CONTRACTORS â€” Website Running")
    print("="*60)
    print(f"  URL: http://127.0.0.1:5000")
    print(f"  Admin: http://127.0.0.1:5000/admin")
    print(f"  Username: {app.config['ADMIN_USERNAME']}")
    print(f"  Password: {app.config['ADMIN_PASSWORD']}")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)
